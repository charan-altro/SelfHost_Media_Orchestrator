import os
import string
import asyncio
import json
import threading
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException, Query
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.core.db import get_db
from backend.models.media import Library
from backend.services.scanner import ScannerService
from backend.services.cleanup import CleanupService
from backend.core.progress import active_scans

router = APIRouter(prefix="/api/libraries", tags=["Libraries"])

# ────────────────── Drive detection ──────────────────

def _get_windows_drive_mounts() -> list[dict]:
    """
    Detect Windows drive letters mounted inside Docker.
    Convention: D:\ is mounted at /d_drive, E:\ at /e_drive, etc.
    Returns list of {label, path} dicts for drives that exist.
    """
    drives = []
    for letter in string.ascii_lowercase:
        mount = f"/{letter}_drive"
        if os.path.isdir(mount):
            drives.append({
                "label": f"{letter.upper()}:\\",
                "path": mount,
            })
    # Also always include /media (local mapped folder) and /
    if os.path.isdir("/media"):
        drives.append({"label": "Local /media", "path": "/media"})
    return drives


@router.get("/drives")
def list_drives():
    """
    Return all Windows drive letters mounted inside this Docker container,
    plus the /media volume. Use these paths in the folder browser.
    """
    drives = _get_windows_drive_mounts()
    if not drives:
        return {"drives": [{"label": "/ (root)", "path": "/"}]}
    return {"drives": drives}

class LibraryCreate(BaseModel):
    name: str
    path: str
    type: str # 'movie' or 'tv'
    language: str = 'en'

class LibraryUpdate(BaseModel):
    name: str | None = None
    path: str | None = None

class BulkAnalyzeRequest(BaseModel):
    movie_ids: list[int] | None = []
    show_ids: list[int] | None = []

@router.post("/analyze/bulk")
def bulk_analyze(req: BulkAnalyzeRequest, background_tasks: BackgroundTasks):
    """Trigger deep analysis for a specific set of items."""
    if not req.movie_ids and not req.show_ids:
        raise HTTPException(status_code=400, detail="No IDs provided")
    
    background_tasks.add_task(_background_deep_analysis_task, req.movie_ids or [], req.show_ids or [])
    return {"status": "Bulk analysis queued", "items": len(req.movie_ids or []) + len(req.show_ids or [])}

@router.get("/browse")
def browse_filesystem(path: str = Query("/", description="Path to browse")):
    # Normalize for Linux
    path = path.replace("\\", "/")
    if not os.path.exists(path) or not os.path.isdir(path):
        raise HTTPException(status_code=404, detail=f"Path not found or is not a directory: {path}")
    
    dirs = []
    try:
        for entry in os.scandir(path):
            if entry.is_dir() and not entry.name.startswith('.'):
                dirs.append({
                    "name": entry.name,
                    "path": entry.path.replace("\\", "/") 
                })
    except PermissionError:
        pass
        
    dirs.sort(key=lambda x: x["name"].lower())
    
    parent_path = os.path.dirname(path) if path != "/" else "/"
    if parent_path.endswith("/") and len(parent_path) > 1:
        parent_path = parent_path[:-1]
        
    return {
        "current_path": path.replace("\\", "/"),
        "parent_path": parent_path.replace("\\", "/"),
        "directories": dirs
    }

@router.get("/")
def list_libraries(db: Session = Depends(get_db)):
    return db.query(Library).all()

@router.patch("/{library_id}")
def update_library(library_id: int, update: LibraryUpdate, db: Session = Depends(get_db)):
    lib = db.query(Library).filter(Library.id == library_id).first()
    if not lib:
        raise HTTPException(status_code=404, detail="Library not found")
    
    old_path = lib.path.replace("\\", "/")
    
    if update.name is not None:
        lib.name = update.name
    
    if update.path is not None:
        new_path = update.path.replace("\\", "/")
        if new_path != old_path:
            # Update all associated file paths
            if lib.type == 'movie':
                from backend.models.media import MovieFile, Movie
                files = db.query(MovieFile).join(Movie).filter(Movie.library_id == library_id).all()
                for f in files:
                    if f.file_path and f.file_path.startswith(old_path):
                        f.file_path = f.file_path.replace(old_path, new_path, 1)
            else:
                from backend.models.media import Episode, Season, TVShow
                episodes = db.query(Episode).join(Season).join(TVShow).filter(TVShow.library_id == library_id).all()
                for ep in episodes:
                    if ep.file_path and ep.file_path.startswith(old_path):
                        ep.file_path = ep.file_path.replace(old_path, new_path, 1)
            
            lib.path = new_path
            
    db.commit()
    db.refresh(lib)
    return lib

@router.post("/")
def add_library(lib: LibraryCreate, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    from sqlalchemy.exc import IntegrityError, OperationalError
    db_lib = Library(**lib.model_dump())
    db.add(db_lib)
    try:
        db.commit()
        db.refresh(db_lib)
    except IntegrityError:
        db.rollback()
        raise HTTPException(status_code=400, detail="This library path is already mapped.")
    except OperationalError as e:
        db.rollback()
        if "locked" in str(e).lower():
            raise HTTPException(status_code=503, detail="Database is busy scanning. Please try again in a few seconds.")
        raise e
    
    # Auto-trigger scan
    active_scans[db_lib.id] = {"status": "scanning", "file": "Queuing...", "current": 0, "total": 0}
    background_tasks.add_task(_background_scan, db_lib.id)
    
    return db_lib

def _background_metadata_task(movie_ids: list[int], show_ids: list[int]):
    """
    Background Enrichment (Identity Phase):
    Imports NFO data and detects local posters/backdrops.
    """
    from backend.core.db import SessionLocal
    from backend.core.task_manager import create_task, update_task
    from backend.services.nfo_reader import NFOReader
    from backend.models.media import Movie, TVShow, Episode, Season

    db = SessionLocal()
    total = len(movie_ids) + len(show_ids)
    if total == 0:
        db.close()
        return

    task_id = create_task(f"Identity Import ({total} items)", total=total)
    update_task(task_id, status="running", progress=0, message="Starting rapid NFO/Image import...")

    try:
        # 1. Process Movies in Batch
        movies = db.query(Movie).filter(Movie.id.in_(movie_ids)).all()
        processed = 0
        for movie in movies:
            if movie.files:
                update_task(task_id, message=f"Importing: {movie.title}")
                nfo = NFOReader.parse_movie_nfo(movie.files[0].file_path)
                if nfo:
                    movie.title = nfo.get("title") or movie.title
                    movie.year = nfo.get("year") or movie.year
                    movie.plot = nfo.get("plot") or movie.plot
                    movie.poster_path = nfo.get("poster_path") or movie.poster_path
                    movie.fanart_path = nfo.get("fanart_path") or movie.fanart_path
                    movie.cast = nfo.get("cast") or movie.cast
                    movie.runtime = nfo.get("runtime") or movie.runtime
                    movie.status = "matched"
            processed += 1
            if processed % 20 == 0:
                update_task(task_id, progress=processed)

        # 2. Process TV Shows in Batch
        shows = db.query(TVShow).filter(TVShow.id.in_(show_ids)).all()
        for show in shows:
            update_task(task_id, message=f"Importing TV: {show.title}")
            first_ep = db.query(Episode).join(Season).filter(Season.show_id == show.id).first()
            if first_ep:
                nfo = NFOReader.parse_tvshow_nfo(first_ep.file_path)
                if nfo:
                    show.title = nfo.get("title") or show.title
                    show.plot = nfo.get("plot") or show.plot
                    show.year = nfo.get("year") or show.year
                    show.poster_path = nfo.get("poster_path") or show.poster_path
                    show.fanart_path = nfo.get("fanart_path") or show.fanart_path
                    show.cast = nfo.get("cast") or show.cast
                    show.status = "matched"
            processed += 1
            if processed % 20 == 0:
                update_task(task_id, progress=processed)

        db.commit()
        # ENSURE FINAL COUNT IS ACCURATE
        update_task(task_id, status="done", progress=total, message=f"Identity import complete for {total} items.")
    except Exception as e:
        db.rollback()
        print(f"[IdentityTask] Error: {e}")
        update_task(task_id, status="error", message=str(e))
    finally:
        db.close()

def _background_deep_analysis_task(movie_ids: list[int], show_ids: list[int]):
    """
    Manual Phase 2.2: Deep MediaInfo Extraction (Technical Specs).
    Only runs when triggered by the user.
    """
    from backend.core.db import SessionLocal
    from backend.core.task_manager import create_task, update_task
    from backend.services.mediainfo import extract_media_info
    from backend.models.media import Movie, TVShow, Episode, Season

    db = SessionLocal()
    total = len(movie_ids) + len(show_ids)
    task_id = create_task(f"Deep Analysis ({total} items)", total=total)
    update_task(task_id, status="running", progress=0, message="Opening video files...")

    processed = 0
    try:
        if movie_ids:
            movies = db.query(Movie).filter(Movie.id.in_(movie_ids)).all()
            for movie in movies:
                update_task(task_id, progress=processed, message=f"Analyzing: {movie.title}")
                for mfile in movie.files:
                    info = extract_media_info(mfile.file_path)
                    if info:
                        mfile.resolution = info.get("resolution") or "Unknown"
                        mfile.video_codec = info.get("video_codec") or "Unknown"
                        mfile.audio_codec = info.get("audio_codec") or "Unknown"
                db.commit()
                processed += 1

        if show_ids:
            shows = db.query(TVShow).filter(TVShow.id.in_(show_ids)).all()
            for show in shows:
                update_task(task_id, progress=processed, message=f"Analyzing TV: {show.title}")
                episodes = db.query(Episode).join(Season).filter(Season.show_id == show.id).all()
                for ep in episodes:
                    info = extract_media_info(ep.file_path)
                    if info:
                        ep.resolution = info.get("resolution") or "Unknown"
                        ep.video_codec = info.get("video_codec") or "Unknown"
                        ep.audio_codec = info.get("audio_codec") or "Unknown"
                db.commit()
                processed += 1

        update_task(task_id, status="done", progress=total, message="Deep analysis complete.")
    except Exception as e:
        update_task(task_id, status="error", message=str(e))
    finally:
        db.close()

def _background_scan(library_id: int):
    from backend.core.db import SessionLocal
    from backend.core.task_manager import create_task, update_task
    db = SessionLocal()
    task_id = None
    try:
        lib = db.query(Library).filter(Library.id == library_id).first()
        lib_name = lib.name if lib else f"Library {library_id}"
        
        # Create persistent task for the "Fast Pass"
        task_id = create_task(f"Fast Scan: {lib_name}", total=0)
        update_task(task_id, status="running", message="Initializing folders...")
        
        scanner = ScannerService(db)
        result = scanner.scan_library(library_id, task_id=task_id)
        
        if result.get("status") == "success":
            final_count = result.get('files_processed', 0)
            update_task(task_id, status="done", progress=final_count, total=final_count, message=f"Registered {final_count} files.")
            
            # Trigger second-pass metadata extraction in another thread
            m_ids = result.get("movie_ids", [])
            s_ids = result.get("show_ids", [])
            if m_ids or s_ids:
                import threading
                t = threading.Thread(target=_background_metadata_task, args=(m_ids, s_ids))
                t.daemon = True
                t.start()
    except Exception as e:
        print(f"[Scanner] Fatal exception running _background_scan: {e}")
        if task_id:
            update_task(task_id, status="error", message=str(e))
        active_scans[library_id] = {"status": "error", "message": str(e)}
    finally:
        db.close()

@router.post("/{library_id}/scan")
def trigger_scan(library_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    from backend.models.media import BackgroundTask
    lib = db.query(Library).filter(Library.id == library_id).first()
    if not lib:
        raise HTTPException(status_code=404, detail="Library not found")

    # 1. Check in-memory Gatekeeper
    progress = active_scans.get(library_id)
    if progress and progress.get("status") == "scanning":
        return {"status": "already_scanning", "message": "Scan already in progress (memory)"}

    # 2. Check Database Gatekeeper (covers server restarts)
    active_db_task = db.query(BackgroundTask).filter(
        BackgroundTask.name.like(f"Fast Scan: {lib.name}%"),
        BackgroundTask.status == "running"
    ).first()
    if active_db_task:
        return {"status": "already_scanning", "message": "Scan already in progress (database)"}
        
    # Lock the scan immediately
    active_scans[library_id] = {"status": "scanning", "file": "Queuing...", "current": 0, "total": 0}
        
    background_tasks.add_task(_background_scan, library_id)
    return {"status": "Scan queued"}

@router.get("/{library_id}/scan/progress")
async def scan_progress_sse(library_id: int):
    async def event_generator():
        while True:
            progress = active_scans.get(library_id)
            if not progress:
                # Scan hasn't started or doesn't exist yet
                yield f"data: {json.dumps({'status': 'waiting'})}\n\n"
            else:
                yield f"data: {json.dumps(progress)}\n\n"
                
                # Close connection if done or error
                if progress.get("status") in ["done", "error"]:
                    # Small grace period to ensure delivery
                    await asyncio.sleep(1.0)
                    break
                    
            await asyncio.sleep(0.5)
            
    return StreamingResponse(event_generator(), media_type="text/event-stream")

@router.post("/{library_id}/analyze")
def trigger_deep_analysis(library_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Manually trigger deep MediaInfo extraction for a library."""
    from backend.models.media import Movie, TVShow
    lib = db.query(Library).filter(Library.id == library_id).first()
    if not lib:
        raise HTTPException(status_code=404, detail="Library not found")
        
    movie_ids = [m.id for m in db.query(Movie.id).filter(Movie.library_id == library_id).all()]
    show_ids = [s.id for s in db.query(TVShow.id).filter(TVShow.library_id == library_id).all()]
    
    if not movie_ids and not show_ids:
        return {"status": "skipped", "message": "Library is empty"}
        
    background_tasks.add_task(_background_deep_analysis_task, movie_ids, show_ids)
    return {"status": "Analysis queued", "items": len(movie_ids) + len(show_ids)}

@router.delete("/{library_id}")
def delete_library(library_id: int, db: Session = Depends(get_db)):
    lib = db.query(Library).filter(Library.id == library_id).first()
    if not lib:
        raise HTTPException(status_code=404, detail="Library not found")
        
    from backend.models.media import Movie, TVShow
    movies = db.query(Movie).filter(Movie.library_id == library_id).all()
    for m in movies:
        db.delete(m) # Delete movies and let cascade delete files
        
    shows = db.query(TVShow).filter(TVShow.library_id == library_id).all()
    for s in shows:
        db.delete(s) # Delete shows and let cascade delete seasons/episodes
        
    db.delete(lib)
    db.commit()
    
    # Final sweep to catch any edge cases
    CleanupService.purge_orphans(db)
    
    return {"status": "deleted"}

def _background_cleanup(library_id: int):
    from backend.core.db import SessionLocal
    from backend.core.task_manager import create_task, update_task
    db = SessionLocal()
    task_id = None
    try:
        lib = db.query(Library).filter(Library.id == library_id).first()
        if not lib: return
        
        task_id = create_task(f"Cleanup: {lib.name}", total=3)
        
        import time
        last_ui_update = [time.time()]

        def update_msg(msg: str):
            now = time.time()
            # Only update the database/UI at most once every 2 seconds to maximize speed
            if now - last_ui_update[0] > 2.0:
                update_task(task_id, message=msg)
                last_ui_update[0] = now

        update_task(task_id, status="running", progress=0, message="Cleaning duplicate artwork...")
        
        # 1. Physical Cleanup (Artwork duplicates, empty folders)
        svc = CleanupService(lib.path)
        dupes = svc.remove_duplicate_artwork(progress_callback=update_msg)
        
        update_task(task_id, message="Removing orphaned folders...")
        empty = svc.remove_empty_folders(progress_callback=update_msg)
        
        update_task(task_id, progress=1, message="Merging duplicate records...")
        
        # 2. Database Cleanup (Merge duplicates by title, remove orphans)
        merge_stats = CleanupService.merge_duplicate_movies(db, library_id)
        orphan_stats = CleanupService.remove_orphans(db, library_id)
        
        update_task(task_id, progress=2, message="Fixing filenames...")
        
        # 3. Filename Fixes (Clean brackets like '[]')
        fix_stats = CleanupService.fix_all_movie_filenames(db, library_id)
        
        update_task(task_id, message="Regenerating missing NFO data...")
        nfo_stats = CleanupService.regenerate_nfos(db, library_id)
        
        # 4. Generate Report
        try:
            from datetime import datetime
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            report_path = os.path.join(lib.path, f"cleanup_report_{timestamp}.txt")
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(f"Cleanup Report for {lib.name} - {datetime.now().isoformat()}\n")
                f.write("="*60 + "\n\n")
                
                f.write(f"SUMMARY:\n")
                f.write(f"- Fixed Filenames: {fix_stats['fixed_filenames']}\n")
                f.write(f"- Regenerated NFOs: {nfo_stats['regenerated_nfos']}\n")
                f.write(f"- Removed Artwork Duplicates: {len(dupes['removed_duplicates'])}\n")
                f.write(f"- Removed Empty Folders: {len(empty)}\n")
                f.write(f"- Merged DB Groups: {merge_stats['merged_groups']}\n")
                f.write(f"- Removed Orphan Records: {orphan_stats['removed_files']}\n\n")
                
                if fix_stats.get("details"):
                    f.write("FIXED FILENAMES:\n")
                    for d in fix_stats["details"]:
                        f.write(f"  [FIXED] {d}\n")
                    f.write("\n")
                
                if dupes.get("removed_duplicates"):
                    f.write("REMOVED DUPLICATE ARTWORK:\n")
                    for d in dupes["removed_duplicates"]:
                        f.write(f"  [REMOVED] {d}\n")
                    f.write("\n")
                
                if empty:
                    f.write("REMOVED EMPTY FOLDERS:\n")
                    for d in empty:
                        f.write(f"  [REMOVED] {d}\n")
                    f.write("\n")
            print(f"[Cleanup] Report generated: {report_path}")
        except Exception as report_err:
            print(f"[Cleanup] Failed to generate report: {report_err}")

        update_task(task_id, status="done", progress=3, message=f"Fixed {fix_stats['fixed_filenames']} filenames. Report saved to library folder.")
        
        print(f"Cleanup done for lib {library_id}:")
        print(f"  - Physical: {len(dupes['removed_duplicates'])} artwork dupes, {len(empty)} empty dirs removed")
        print(f"  - Database: {merge_stats['merged_groups']} groups merged, {orphan_stats['removed_files']} orphans removed")
        print(f"  - Filenames: {fix_stats['fixed_filenames']} fixed")
    except Exception as e:
        if task_id:
            update_task(task_id, status="error", message=str(e))
        print(f"[Cleanup] Error: {e}")
    finally:
        db.close()

@router.post("/{library_id}/cleanup")
def trigger_cleanup(library_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Removes duplicate artwork files, empty folders, and deduplicates database records."""
    lib = db.query(Library).filter(Library.id == library_id).first()
    if not lib:
        raise HTTPException(status_code=404, detail="Library not found")
        
    background_tasks.add_task(_background_cleanup, library_id)
    return {"status": "Cleanup queued", "library": lib.name}
