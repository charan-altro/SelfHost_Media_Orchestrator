import os
from pathlib import Path
from sqlalchemy.orm import Session
from sqlalchemy import func
from sqlalchemy.exc import IntegrityError
from backend.models.media import Library, Movie, MovieFile, TVShow, Season, Episode
from backend.services.parser import parse_filename
from backend.services.mediainfo import extract_media_info
from backend.services.nfo_reader import NFOReader

from backend.core.progress import active_scans

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

    def scan_library(self, library_id: int, task_id: str = None):
        import time
        from backend.core.task_manager import update_task
        lib = self.db.query(Library).filter(Library.id == library_id).first()
        if not lib:
            print(f"[Scanner] Library ID {library_id} not found in database.")
            active_scans[library_id] = {"status": "error"}
            return {"status": "error", "message": "Library not found"}
            
        normalized_path = lib.path.replace("\\", "/")
        print(f"[Scanner] Starting optimized single-pass scan of library {lib.id} at: {normalized_path}")
        
        if not os.path.exists(normalized_path):
            print(f"[Scanner] CRITICAL: Path does not exist on disk: {normalized_path}")
            active_scans[library_id] = {"status": "error", "message": f"Path not found: {normalized_path}"}
            if task_id:
                update_task(task_id, status="error", message=f"Path not found: {normalized_path}")
            return {"status": "error", "message": f"Path not found: {normalized_path}"}
            
        # 1. PRE-FETCH CACHE: Load everything into memory once to avoid session overhead
        print(f"[Scanner] Building caches for library {lib.id}...")
        existing_movies_paths = {}   # path -> movie_id
        existing_episodes_paths = {} # path -> show_id
        title_to_movie = {}    # lowered_title -> Movie object
        title_to_show = {}     # lowered_title -> TVShow object
        
        if lib.type == 'movie' or lib.type is None:
            m_files = self.db.query(MovieFile).join(Movie).filter(Movie.library_id == library_id).all()
            for f in m_files: existing_movies_paths[f.file_path] = f.movie_id
            
            movies = self.db.query(Movie).filter(Movie.library_id == library_id).all()
            for m in movies: title_to_movie[m.title.lower()] = m
            
        if lib.type == 'tv' or lib.type is None:
            e_files = self.db.query(Episode).join(Season).join(TVShow).filter(TVShow.library_id == library_id).all()
            for f in e_files: existing_episodes_paths[f.file_path] = f.show_id
            
            shows = self.db.query(TVShow).filter(TVShow.library_id == library_id).all()
            for s in shows: title_to_show[s.title.lower()] = s

        # Initial status
        active_scans[library_id] = {
            "total": 0,
            "current": 0,
            "file": "Walking folders...",
            "status": "scanning"
        }
        if task_id:
            update_task(task_id, message="Walking folders...")

        processed_movie_ids = set()
        processed_show_ids = set()
        count = 0
        last_ui_update = time.time()
        
        SKIP_DIRS = {'.git', 'node_modules', '.actors', '@eaDir', '#recycle'}

        # 2. SINGLE-PASS SCAN LOOP
        for root, dirs, files in os.walk(normalized_path):
            # Optimization: Skip hidden and junk directories
            dirs[:] = [d for d in dirs if not d.startswith('.') and d not in SKIP_DIRS]
            
            for file in files:
                ext = Path(file).suffix.lower()
                if ext in SUPPORTED_EXTS:
                    file_path = os.path.join(root, file).replace("\\", "/")
                    try:
                        # Optimization Check: If file path is already known, just record it
                        found_id = None
                        if file_path in existing_movies_paths:
                            found_id = existing_movies_paths[file_path]
                            processed_movie_ids.add(found_id)
                        elif file_path in existing_episodes_paths:
                            found_id = existing_episodes_paths[file_path]
                            processed_show_ids.add(found_id)
                        
                        # If not found, do registration pass using title cache
                        if not found_id:
                            parsed = parse_filename(file)
                            if lib.type == 'tv' or (lib.type != 'movie' and parsed.is_tv):
                                sid = self._process_tv_cached(lib, file_path, file, parsed, title_to_show)
                                if sid: processed_show_ids.add(sid)
                            else:
                                mid = self._process_movie_cached(lib, file_path, file, parsed, title_to_movie)
                                if mid: processed_movie_ids.add(mid)
                        
                        count += 1
                        
                        # Throttled UI update & DB "Breathing"
                        now = time.time()
                        if now - last_ui_update > 1.5:
                            # 1. Update status maps (in-memory)
                            active_scans[library_id]["current"] = count
                            active_scans[library_id]["total"] = count
                            active_scans[library_id]["file"] = file
                            
                            # 2. Update persistent Task Manager (using our CURRENT session)
                            if task_id:
                                update_task(task_id, progress=count, total=count, message=f"Registered {count} files...", db=self.db)
                            
                            # 3. Commit releases the lock
                            self.db.commit()
                            last_ui_update = now
                            
                    except Exception as e:
                        print(f"[Scanner] ERROR processing {file_path}: {e}")
                        continue
        
        # 3. FINAL COMMIT
        print(f"[Scanner] Finalizing database changes...")
        self.db.commit()
        
        active_scans[library_id]["current"] = count
        active_scans[library_id]["total"] = count
        active_scans[library_id]["status"] = "done"
        active_scans[library_id]["file"] = "Scan Complete"
        
        return {
            "status": "success", 
            "files_processed": count,
            "movie_ids": list(processed_movie_ids),
            "show_ids": list(processed_show_ids)
        }

    def _process_movie_cached(self, lib: Library, file_path: str, filename: str, parsed, cache: dict) -> int:
        clean_title = parsed.title.strip()
        lower_title = clean_title.lower()
        
        if lower_title in cache:
            movie = cache[lower_title]
        else:
            movie = Movie(
                library_id=lib.id,
                title=clean_title,
                year=parsed.year,
                status="unmatched"
            )
            self.db.add(movie)
            self.db.flush()
            cache[lower_title] = movie
        
        normalized_file_path = file_path.replace("\\", "/")
        mfile = MovieFile(
            movie_id=movie.id,
            file_path=normalized_file_path,
            original_filename=filename,
            size_bytes=os.path.getsize(file_path) if os.path.exists(file_path) else 0
        )
        self.db.add(mfile)
        return movie.id

    def _process_tv_cached(self, lib: Library, file_path: str, filename: str, parsed, cache: dict) -> int:
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
        # Quick lookup for season (less frequent than movies/shows)
        season = self.db.query(Season).filter(Season.show_id == show.id, Season.season_number == season_num).first()
        if not season:
            season = Season(show_id=show.id, season_number=season_num)
            self.db.add(season)
            self.db.flush()

        ep_num = parsed.episode or 1
        ep = Episode(
            season_id=season.id,
            episode_number=ep_num,
            title=f"Episode {ep_num}",
            file_path=file_path.replace("\\", "/"),
            original_filename=filename
        )
        self.db.add(ep)
        return show.id
