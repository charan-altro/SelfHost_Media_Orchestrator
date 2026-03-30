import os
import hashlib
import re
import shutil
from pathlib import Path
from collections import defaultdict
from sqlalchemy.orm import Session
from sqlalchemy import func
from backend.models.media import Movie, MovieFile, Library

# Artwork file patterns that have a canonical base name
ARTWORK_PATTERNS = (
    "-poster.jpg",
    "-fanart.jpg",
    "-logo.png",
    "-logo.jpg",
    "-banner.jpg",
    "-thumb.jpg",
)

def _file_hash(path: str, chunk_size: int = 65536) -> str:
    """Return a quick MD5 hash of a file's first 64KB."""
    h = hashlib.md5()
    try:
        with open(path, "rb") as f:
            h.update(f.read(chunk_size))
        return h.hexdigest()
    except Exception:
        return ""


class CleanupService:
    """
    Handles three kinds of cleanup inside a library root:
      1. Duplicate artwork – same hash files saved under different names.
      2. Empty folders – directories with no media or artwork left.
      3. Orphaned DB records – merges duplicates and removes missing files.
    """

    def __init__(self, library_path: str):
        self.root = library_path

    # ------------------------------------------------------------------
    # 1.  Duplicate artwork cleanup (Physical)
    # ------------------------------------------------------------------
    def remove_duplicate_artwork(self, progress_callback=None) -> dict:
        removed = []
        kept = []
        print(f"[Cleanup] Fast-scanning for duplicate artwork in {self.root}...")
        for dirpath, _, files in os.walk(self.root):
            images = [f for f in files if Path(f).suffix.lower() in {".jpg", ".jpeg", ".png", ".webp"}]
            if len(images) < 2:
                continue

            if progress_callback:
                progress_callback(f"Analyzing images: {os.path.basename(dirpath)}")

            # OPTIMIZATION: Group by size first.
            # Two files can only be duplicates if they have the EXACT same byte size.
            size_groups = defaultdict(list)
            for img in images:
                full = os.path.join(dirpath, img)
                try:
                    size = os.path.getsize(full)
                    size_groups[size].append(full)
                except: continue

            # Only hash files that share the same size
            for size, paths in size_groups.items():
                if len(paths) < 2:
                    continue
                
                # Group by hash within this size group
                hash_groups = defaultdict(list)
                for full in paths:
                    h = _file_hash(full)
                    if h:
                        hash_groups[h].append(full)

                for h, hashed_paths in hash_groups.items():
                    if len(hashed_paths) < 2:
                        continue
                    
                    # Keep the file with the canonical suffix pattern, or shortest name
                    canonical = min(
                        hashed_paths,
                        key=lambda p: (
                            0 if any(p.endswith(sfx) for sfx in ARTWORK_PATTERNS) else 1,
                            len(os.path.basename(p))
                        )
                    )
                    
                    for dupe in hashed_paths:
                        if dupe != canonical:
                            try:
                                os.remove(dupe)
                                print(f"[Cleanup] Removed duplicate artwork: {os.path.basename(dupe)}")
                                removed.append(dupe)
                            except Exception as e:
                                print(f"CleanupService: failed to remove {dupe}: {e}")

        return {"removed_duplicates": removed, "kept": kept}

    # ------------------------------------------------------------------
    # 2.  Empty folder cleanup (Physical)
    # ------------------------------------------------------------------
    def remove_empty_folders(self, progress_callback=None) -> list[str]:
        """
        Removes folders that contain no media files and only metadata.
        SAFETY: If any file > 20MB exists, or any non-metadata file exists, we KEEP the folder.
        """
        # Common metadata/image extensions that are safe to delete if no video is present
        METADATA_EXTS = {
            '.jpg', '.jpeg', '.png', '.webp', '.nfo', '.txt', '.xml', '.json', 
            '.url', '.tbn', '.info', '.log', '.pjf', '.thumb'
        }
        
        removed_dirs = []
        print(f"[Cleanup] Safely scanning for orphaned folders in {self.root}...")

        # walk topdown=False so we clean leaf nodes (subfolders) first
        for dirpath, dirs, files in os.walk(self.root, topdown=False):
            if dirpath == self.root:
                continue
            
            if progress_callback:
                progress_callback(f"Checking folder: {os.path.basename(dirpath)}")

            # SAFETY CHECKS
            keep_folder = False
            
            # 1. If it has subdirectories that we haven't deleted, keep it
            current_subdirs = [d for d in os.listdir(dirpath) if os.path.isdir(os.path.join(dirpath, d))]
            if current_subdirs:
                keep_folder = True
                
            # 2. Check every file in the folder
            if not keep_folder:
                for f in files:
                    f_path = os.path.join(dirpath, f)
                    ext = Path(f).suffix.lower()
                    
                    # If any file is > 20MB, it's likely a video or important data. KEEP IT.
                    try:
                        if os.path.getsize(f_path) > 20 * 1024 * 1024:
                            keep_folder = True
                            break
                    except: pass
                    
                    # If any file is NOT a known metadata type, keep the folder to be safe.
                    if ext not in METADATA_EXTS:
                        keep_folder = True
                        break
            
            if not keep_folder:
                # This folder ONLY contains small metadata files and no subfolders.
                try:
                    print(f"[Cleanup] Safely removing orphaned metadata folder: {dirpath}")
                    shutil.rmtree(dirpath)
                    removed_dirs.append(dirpath)
                except Exception as e:
                    print(f"[Cleanup] Failed to remove orphaned folder {dirpath}: {e}")
                    
        return removed_dirs

    # ------------------------------------------------------------------
    # 3.  Database Cleanup: Merge Duplicates & Remove Orphans
    # ------------------------------------------------------------------
    @staticmethod
    def merge_duplicate_movies(db: Session, library_id: int) -> dict:
        """
        Finds movies in the same library with the same title/year (case-insensitive).
        Merges files into one canonical record.
        """
        duplicates = db.query(
            func.lower(Movie.title).label('l_title'), 
            Movie.year, 
            func.count(Movie.id).label('m_count')
        ).filter(Movie.library_id == library_id)\
         .group_by(func.lower(Movie.title), Movie.year)\
         .having(func.count(Movie.id) > 1).all()
        
        merged_groups = 0
        freed = 0
        
        for dup in duplicates:
            m_list = db.query(Movie).filter(
                func.lower(Movie.title) == dup.l_title,
                Movie.year == dup.year,
                Movie.library_id == library_id
            ).order_by(Movie.id.asc()).all()
            
            canonical = m_list[0]
            others = m_list[1:]
            
            for other in others:
                for mfile in other.files:
                    mfile.movie_id = canonical.id
                
                if not canonical.plot and other.plot: canonical.plot = other.plot
                if not canonical.poster_path and other.poster_path: canonical.poster_path = other.poster_path
                
                db.delete(other)
                freed += 1
            merged_groups += 1
        
        db.commit()
        return {"merged_groups": merged_groups, "deleted_records": freed}

    @staticmethod
    def remove_orphans(db: Session, library_id: int) -> dict:
        """Removes DB records for files that no longer exist on disk."""
        mfiles = db.query(MovieFile).join(Movie).filter(Movie.library_id == library_id).all()
        removed_files = 0
        for mf in mfiles:
            if not os.path.exists(mf.file_path):
                db.delete(mf)
                removed_files += 1
        db.commit()

        # Remove movies with no files
        empty_movies = db.query(Movie).filter(Movie.library_id == library_id, ~Movie.files.any()).all()
        removed_movies = len(empty_movies)
        for m in empty_movies:
            db.delete(m)
        db.commit()
        
        return {"removed_files": removed_files, "removed_movies": removed_movies}

    @staticmethod
    def purge_orphans(db: Session) -> dict:
        """
        Force-removes ANY movies or TV shows that reference a library ID 
        which no longer exists in the libraries table.
        """
        from backend.models.media import Movie, TVShow, Library
        
        valid_lib_ids = [l.id for l in db.query(Library.id).all()]
        
        orphaned_movies = db.query(Movie).filter(~Movie.library_id.in_(valid_lib_ids)).all()
        m_count = len(orphaned_movies)
        for m in orphaned_movies:
            db.delete(m)
            
        orphaned_shows = db.query(TVShow).filter(~TVShow.library_id.in_(valid_lib_ids)).all()
        s_count = len(orphaned_shows)
        for s in orphaned_shows:
            db.delete(s)
            
        db.commit()
        return {"orphaned_movies_removed": m_count, "orphaned_shows_removed": s_count}

    @staticmethod
    def fix_all_movie_filenames(db: Session, library_id: int) -> dict:
        """
        Iterates through all movies in a library and re-applies renaming logic
        if their current filename contains empty brackets like '[]' or '[ ]'.
        """
        lib = db.query(Library).filter(Library.id == library_id).first()
        if not lib:
            return {"error": "Library not found"}

        movies = db.query(Movie).filter(Movie.library_id == library_id).all()
        fixed_count = 0
        errors = 0
        details = []
        
        print(f"[Cleanup] Checking filenames for {len(movies)} movies...")

        for movie in movies:
            if not movie.files:
                continue
            
            mfile = movie.files[0]
            current_path = mfile.file_path
            filename = os.path.basename(current_path)

            # Check if filename has the problematic pattern
            if "[]" in filename or "[ ]" in filename or "()" in filename or "( )" in filename:
                try:
                    new_path = CleanupService.rename_to_title(
                        current_file_path=current_path,
                        title=movie.title,
                        year=movie.year,
                        library_root=lib.path,
                        resolution=mfile.resolution or "",
                        video_codec=mfile.video_codec or "",
                        audio_codec=mfile.audio_codec or "",
                    )
                    
                    if new_path != current_path:
                        change_msg = f"{filename} -> {os.path.basename(new_path)}"
                        print(f"[Cleanup] Fixed: {change_msg}")
                        details.append(change_msg)
                        mfile.file_path = new_path
                        fixed_count += 1
                except Exception as e:
                    print(f"[CleanupService] Failed to fix {current_path}: {e}")
                    errors += 1
        
        db.commit()
        return {"fixed_filenames": fixed_count, "errors": errors, "details": details}

    @staticmethod
    def regenerate_nfos(db: Session, library_id: int) -> dict:
        """
        Regenerates NFO files for all matched movies to ensure they have the latest 
        metadata structure (like actors/cast).
        """
        from backend.services.nfo import NFOGenerator
        from backend.models.media import Movie
        movies = db.query(Movie).filter(Movie.library_id == library_id, Movie.status == "matched").all()
        nfo_gen = NFOGenerator()
        count = 0
        for movie in movies:
            if not movie.files: continue
            
            # Reconstruct metadata dict from DB for NFO gen
            m_dict = {c.name: getattr(movie, c.name) for c in movie.__table__.columns}
            # Add cast (JSON column is a list of dicts)
            m_dict["cast"] = movie.cast or []
            # Add genres (JSON column is a list of strings)
            m_dict["genres"] = movie.genres or []
            # Add file info
            m_dict["resolution"] = movie.files[0].resolution
            m_dict["video_codec"] = movie.files[0].video_codec
            m_dict["audio_codec"] = movie.files[0].audio_codec
            m_dict["audio_channels"] = movie.files[0].audio_channels

            try:
                nfo_gen.generate_movie_nfo(m_dict, movie.files[0].file_path)
                count += 1
            except: pass
            
        return {"regenerated_nfos": count}

    # ------------------------------------------------------------------
    # 4.  Rename movie folder + file
    # ------------------------------------------------------------------
    @staticmethod
    def rename_to_title(
        current_file_path: str,
        title: str,
        year: int | None,
        library_root: str,
        resolution: str = "",
        video_codec: str = "",
        audio_codec: str = "",
    ) -> str:
        def sanitize(s: str) -> str:
            return re.sub(r'[\\/*?:"<>|]', "", str(s)).strip()

        safe_title = sanitize(title)
        folder_name = f"{safe_title} ({year})" if year else safe_title
        
        tags = " ".join(x for x in [resolution, video_codec, audio_codec] if x)
        file_stem = f"{folder_name} [{tags}]" if tags else folder_name
        
        # Clean up empty brackets and double spaces
        file_stem = re.sub(r'\[\s*\]', '', file_stem)
        file_stem = re.sub(r'\(\s*\)', '', file_stem)
        file_stem = re.sub(r'\s+', ' ', file_stem).strip()
        
        ext = Path(current_file_path).suffix
        new_filename = f"{file_stem}{ext}"

        dest_folder = os.path.join(library_root, folder_name)
        dest_file = os.path.join(dest_folder, new_filename)

        if current_file_path == dest_file:
            return dest_file

        os.makedirs(dest_folder, exist_ok=True)
        shutil.move(current_file_path, dest_file)

        old_dir = os.path.dirname(current_file_path)
        old_stem = Path(current_file_path).stem
        new_stem = Path(dest_file).stem

        for companion in os.listdir(old_dir):
            c_path = os.path.join(old_dir, companion)
            if c_path == dest_file: continue
            if companion.startswith(old_stem):
                new_companion_name = companion.replace(old_stem, new_stem, 1)
                shutil.move(c_path, os.path.join(dest_folder, new_companion_name))

        try:
            if not os.listdir(old_dir):
                os.rmdir(old_dir)
        except OSError:
            pass

        return dest_file
