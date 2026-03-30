import os
from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from pydantic import BaseModel
from backend.core.db import get_db
from backend.models.media import Movie, Library, MovieFile
from backend.services.scraper.chain import ScraperChain
from backend.services.nfo import NFOGenerator
from backend.services.renamer import RenamerService
from backend.services.artwork import ArtworkDownloader
from backend.services.cleanup import CleanupService
from backend.core.config import settings

router = APIRouter(prefix="/api/movies", tags=["Movies"])

class MovieUpdate(BaseModel):
    title: str | None = None
    year: int | None = None
    plot: str | None = None
    tagline: str | None = None
    tmdb_rating: float | None = None
    imdb_rating: float | None = None
    runtime: int | None = None
    director: str | None = None
    genres: list[str] | None = None
    content_rating: str | None = None

@router.patch("/{movie_id}")
def update_movie(movie_id: int, update: MovieUpdate, db: Session = Depends(get_db)):
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    update_data = update.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(movie, key, value)
    
    db.commit()
    db.refresh(movie)
    return movie

@router.get("/")
def list_movies(db: Session = Depends(get_db), limit: int = 10000, offset: int = 0):
    movies = db.query(Movie).offset(offset).limit(limit).all()
    # Simple serialization for MVP
    result = []
    for m in movies:
        m_dict = {c.name: getattr(m, c.name) for c in m.__table__.columns}
        m_dict["files"] = [
            {c.name: getattr(f, c.name) for c in f.__table__.columns} 
            for f in m.files
        ]
        result.append(m_dict)
    return result

@router.get("/{movie_id}")
def get_movie(movie_id: int, db: Session = Depends(get_db)):
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
        
    m_dict = {c.name: getattr(movie, c.name) for c in movie.__table__.columns}
    m_dict["files"] = [
        {c.name: getattr(f, c.name) for c in f.__table__.columns} 
        for f in movie.files
    ]
    return m_dict

@router.get("/search/external")
async def search_external_movies(query: str, year: int = None):
    scraper = ScraperChain()
    results = await scraper.tmdb.search_movies(query, year)
    return results

async def _background_scrape_and_rename(movie_id: int, tmdb_id: int = None):
    # This is a basic background job MVP
    # In M3, this moves to Celery
    from backend.core.db import SessionLocal
    from backend.core.task_manager import create_task, update_task
    db = SessionLocal()
    task_id = None
    try:
        movie = db.query(Movie).filter(Movie.id == movie_id).first()
        if not movie:
            return
            
        task_id = create_task(f"Scraping Movie: {movie.title}", total=1)
        update_task(task_id, status="running", progress=0, message="Searching TMDB...")
        
        scraper = ScraperChain()
        if tmdb_id:
            metadata = await scraper.scrape_movie_by_id(tmdb_id)
        else:
            metadata = await scraper.scrape_movie(movie.title, movie.year)
        
        if metadata:
            update_task(task_id, message="Updating database...")
            # Update DB
            for key, val in metadata.items():
                if hasattr(movie, key) and val is not None:
                    setattr(movie, key, val)
            movie.status = "matched"
            db.commit()
            
            # If we have a file, attempt NFO and Rename
            if movie.files:
                original_path = movie.files[0].file_path
                lib = db.query(Library).filter(Library.id == movie.library_id).first()
                if lib:
                    update_task(task_id, message="Generating NFO & Artwork...")
                    renamer = RenamerService(settings.get_settings().get("preferences", {}).get("rename_templates", {}))
                    # Add file specs to metadata for renaming
                    metadata["resolution"] = movie.files[0].resolution
                    metadata["video_codec"] = movie.files[0].video_codec
                    metadata["audio_codec"] = movie.files[0].audio_codec
                    
                    new_path = renamer.rename_movie(metadata, original_path, lib.path)
                    
                    movie.files[0].file_path = new_path
                    movie.file_renamed = True
                    
                    nfo_gen = NFOGenerator()
                    nfo_gen.generate_movie_nfo(metadata, new_path)
                    movie.nfo_generated = True
                    
                    artwork_dl = ArtworkDownloader()
                    await artwork_dl.download_movie_artwork(metadata, new_path)
                    
                    db.commit()
            
            update_task(task_id, status="done", progress=1, message="Completed successfully")
        else:
            update_task(task_id, status="error", message="No metadata found")
            
    except Exception as e:
        import traceback
        print("Error in background scrape pipeline:")
        traceback.print_exc()
        if task_id:
            update_task(task_id, status="error", message=str(e))
    finally:
        db.close()

@router.post("/{movie_id}/match")
def manual_match_movie(movie_id: int, tmdb_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    background_tasks.add_task(_background_scrape_and_rename, movie_id, tmdb_id)
    return {"status": "Manual match task queued"}

@router.post("/{movie_id}/scrape")
def trigger_scrape(movie_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    
    background_tasks.add_task(_background_scrape_and_rename, movie_id)
    return {"status": "Task queued"}

class BulkScrapeRequest(BaseModel):
    movie_ids: list[int]

def _bulk_scrape_task(movie_ids: list[int]):
    import asyncio
    
    # We create a new event loop for this thread to run async functions sequentially
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        for mid in movie_ids:
            # Reusing the existing scraper function sequentially
            loop.run_until_complete(_background_scrape_and_rename(mid))
    finally:
        loop.close()

@router.post("/scrape/bulk")
def trigger_bulk_scrape(req: BulkScrapeRequest, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    if not req.movie_ids:
        raise HTTPException(status_code=400, detail="No movie IDs provided")
        
    background_tasks.add_task(_bulk_scrape_task, req.movie_ids)
    return {"status": f"Queued {len(req.movie_ids)} movies for scraping"}

@router.post("/{movie_id}/rename")
def rename_movie_to_title(movie_id: int, db: Session = Depends(get_db)):
    """
    Renames a movie's folder and file to match its scraped metadata title.
    All companion files (NFO, artwork) in the same directory are migrated automatically.
    """
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    if not movie.files:
        raise HTTPException(status_code=400, detail="No file associated with this movie")
    if movie.status != "matched":
        raise HTTPException(status_code=400, detail="Movie must be scraped/matched before renaming")
    
    lib = db.query(Library).filter(Library.id == movie.library_id).first()
    if not lib:
        raise HTTPException(status_code=400, detail="Library not found for this movie")
    
    current_path = movie.files[0].file_path
    if not current_path or not os.path.exists(current_path):
        raise HTTPException(status_code=400, detail="Movie file not found on disk")
    
    try:
        new_path = CleanupService.rename_to_title(
            current_file_path=current_path,
            title=movie.title,
            year=movie.year,
            library_root=lib.path,
            resolution=movie.files[0].resolution or "",
            video_codec=movie.files[0].video_codec or "",
            audio_codec=movie.files[0].audio_codec or "",
        )
        # Update DB
        movie.files[0].file_path = new_path
        movie.file_renamed = True
        db.commit()
        return {"status": "renamed", "new_path": new_path}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Rename failed: {e}")
