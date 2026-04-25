import os
import time
import threading
from pathlib import Path
from concurrent.futures import ThreadPoolExecutor, as_completed
from sqlalchemy.orm import Session
from backend.core.db import SessionLocal
from backend.models.media import Library, Movie, MovieFile, TVShow, Season, Episode
from backend.services.parser import parse_filename
from backend.services.mediainfo import extract_media_info
from backend.services.nfo_reader import NFOReader
from backend.core.progress import active_scans
from backend.core.task_manager import update_task

SUPPORTED_EXTS = {
    # Common
    '.mkv', '.mp4', '.avi', '.mov', '.wmv', '.m4v', '.ts', '.m2ts', '.mts',
    # Legacy & DVD
    '.mpg', '.mpeg', '.m1v', '.m2v', '.vob', '.divx', '.xvid',
    # Web & Other
    '.webm', '.flv', '.f4v', '.ogv', '.ogm', '.3gp', '.3g2',
    # Disc Images
    '.iso'
}

class ScannerService:
    def __init__(self, db: Session):
        self.db = db
        self.db_lock = threading.Lock()
        self.max_workers = 4  # Safe default for mixed HDD/SSD/NAS environments

    def scan_library(self, library_id: int, task_id: str = None):
        lib = self.db.query(Library).filter(Library.id == library_id).first()
        if not lib:
            active_scans[library_id] = {"status": "error"}
            return {"status": "error", "message": "Library not found"}
            
        normalized_path = lib.path.replace("\\", "/")
        print(f"[Scanner] Starting multi-threaded scan of library {lib.id} at: {normalized_path}")
        
        if not os.path.exists(normalized_path):
            active_scans[library_id] = {"status": "error", "message": f"Path not found: {normalized_path}"}
            if task_id: update_task(task_id, status="error", message=f"Path not found: {normalized_path}")
            return {"status": "error", "message": f"Path not found: {normalized_path}"}
            
        # 1. Pre-fetch Caches
        existing_movies_paths = {}
        existing_episodes_paths = {}
        title_to_movie = {}
        title_to_show = {}
        
        if lib.type == 'movie' or lib.type is None:
            m_files = self.db.query(MovieFile.file_path, MovieFile.movie_id).join(Movie).filter(Movie.library_id == library_id).all()
            existing_movies_paths = {f.file_path: f.movie_id for f in m_files}
            movies = self.db.query(Movie).filter(Movie.library_id == library_id).all()
            title_to_movie = {m.title.lower(): m for m in movies}
            
        if lib.type == 'tv' or lib.type is None:
            e_files = self.db.query(Episode.file_path, Season.show_id).join(Season).join(TVShow).filter(TVShow.library_id == library_id).all()
            existing_episodes_paths = {f.file_path: f.show_id for f in e_files}
            shows = self.db.query(TVShow).filter(TVShow.library_id == library_id).all()
            title_to_show = {s.title.lower(): s for s in shows}

        # 2. Discovery Phase
        files_to_process = []
        SKIP_DIRS = {'.git', 'node_modules', '.actors', '@eaDir', '#recycle'}
        
        if task_id: update_task(task_id, message="Walking folders...")
        
        processed_movie_ids = set()
        processed_show_ids = set()

        for root, dirs, files in os.walk(normalized_path):
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in SKIP_DIRS]
            for file in files:
                ext = Path(file).suffix.lower()
                if ext in SUPPORTED_EXTS:
                    file_path = os.path.join(root, file).replace("\\", "/")
                    if file_path in existing_movies_paths:
                        processed_movie_ids.add(existing_movies_paths[file_path])
                    elif file_path in existing_episodes_paths:
                        processed_show_ids.add(existing_episodes_paths[file_path])
                    else:
                        files_to_process.append((file_path, file))

        total_new = len(files_to_process)
        if total_new == 0:
            print("[Scanner] No new files found.")
            if task_id: update_task(task_id, status="completed", message="Scan complete (no new files)")
            return {"status": "success", "files_processed": 0, "movie_ids": list(processed_movie_ids), "show_ids": list(processed_show_ids)}

        active_scans[library_id] = {"total": total_new, "current": 0, "status": "processing"}
        print(f"[Scanner] Found {total_new} new files. Gathering metadata in parallel...")

        # 3. Phase 1: Gather Metadata (Parallel)
        gathered_data = []
        with ThreadPoolExecutor(max_workers=self.max_workers) as executor:
            futures = [executor.submit(self._gather_metadata_worker, f_path, f_name) for f_path, f_name in files_to_process]
            for future in as_completed(futures):
                gathered_data.append(future.result())
                if len(gathered_data) % 50 == 0:
                    print(f"[Scanner] Gathered {len(gathered_data)}/{total_new}...")

        # 4. Phase 2: Batch Registration (Sequential & Atomic)
        print(f"[Scanner] Registering {total_new} items to database in batches of 50...")
        for i, item in enumerate(gathered_data):
            f_path, f_name, parsed, size_bytes = item
            
            if lib.type == 'tv' or (lib.type != 'movie' and parsed.is_tv):
                sid = self._register_tv_sequential(lib, f_path, f_name, parsed, size_bytes, title_to_show)
                processed_show_ids.add(sid)
            else:
                mid = self._register_movie_sequential(lib, f_path, f_name, parsed, size_bytes, title_to_movie)
                processed_movie_ids.add(mid)
            
            # Commit in smaller batches (e.g. 50 items) to "breathe" the DB
            # and let the Task Manager update the persistent status table.
            if (i + 1) % 50 == 0 or (i + 1) == total_new:
                active_scans[library_id]["current"] = i + 1
                if task_id:
                    # Pass self.db to update_task so it uses the same transaction
                    update_task(task_id, progress=i + 1, total=total_new, 
                                message=f"Registering: {i + 1}/{total_new}...", db=self.db)
                else:
                    self.db.commit()
                print(f"[Scanner] Registered {i + 1}/{total_new}...")

        # Final commit happens inside the last batch check
        print("[Scanner] Registration phase complete.")

        active_scans[library_id]["status"] = "done"
        if task_id: 
            update_task(task_id, status="completed", message="Scan complete", db=self.db)
        
        return {
            "status": "success", 
            "files_processed": total_new,
            "movie_ids": list(processed_movie_ids),
            "show_ids": list(processed_show_ids)
        }

    def _gather_metadata_worker(self, file_path: str, filename: str):
        parsed = parse_filename(filename)
        size_bytes = os.path.getsize(file_path) if os.path.exists(file_path) else 0
        return (file_path, filename, parsed, size_bytes)

    def _register_movie_sequential(self, lib: Library, file_path: str, filename: str, parsed, size_bytes: int, cache: dict):
        clean_title = parsed.title.strip()
        lower_title = clean_title.lower()
        
        if lower_title in cache:
            movie = cache[lower_title]
        else:
            movie = Movie(library_id=lib.id, title=clean_title, year=parsed.year, status="unmatched")
            self.db.add(movie)
            # Flush assigns an ID without committing to disk (very fast)
            self.db.flush()
            cache[lower_title] = movie

        mfile = MovieFile(file_path=file_path, original_filename=filename, size_bytes=size_bytes)
        movie.files.append(mfile)
        return movie.id

    def _register_tv_sequential(self, lib: Library, file_path: str, filename: str, parsed, size_bytes: int, cache: dict):
        clean_title = parsed.title.strip()
        lower_title = clean_title.lower()
        
        if lower_title in cache:
            show = cache[lower_title]
        else:
            show = TVShow(library_id=lib.id, title=clean_title, status="unmatched")
            self.db.add(show)
            self.db.flush()
            cache[lower_title] = show

        season_num = parsed.season or 1
        season_key = f"{show.id}_{season_num}"
        if not hasattr(self, '_season_cache'): self._season_cache = {}
        
        season = self._season_cache.get(season_key)
        if not season:
            season = self.db.query(Season).filter(Season.show_id == show.id, Season.season_number == season_num).first()
            if not season:
                season = Season(season_number=season_num)
                show.seasons.append(season)
                self.db.flush() # Ensure season gets ID for episodes
            self._season_cache[season_key] = season

        ep = Episode(
            episode_number=parsed.episode or 1,
            title=f"Episode {parsed.episode or 1}",
            file_path=file_path,
            original_filename=filename
        )
        season.episodes.append(ep)
        return show.id
