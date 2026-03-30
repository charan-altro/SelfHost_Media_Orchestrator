import asyncio
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from sqlalchemy.orm import Session
from backend.core.db import get_db
from backend.models.media import Movie, MovieFile, TVShow, Episode
from backend.services.subtitles import fetch_best_subtitle
from backend.services.trailers import fetch_trailer_url

router = APIRouter(prefix="/api", tags=["Media Extras"])


# ──────────────────────────── Subtitles ────────────────────────────

def _subtitle_task(media_id: int, media_type: str, language: str):
    from backend.core.db import SessionLocal
    db = SessionLocal()
    try:
        imdb_id = None
        file_path = None
        file_record = None

        if media_type == "movie":
            movie = db.query(Movie).filter(Movie.id == media_id).first()
            if movie and movie.files and movie.imdb_id:
                imdb_id = movie.imdb_id
                file_record = movie.files[0]
                file_path = file_record.file_path
        else:
            ep = db.query(Episode).filter(Episode.id == media_id).first()
            if ep:
                from backend.models.media import Season
                show = db.query(TVShow).join(Season).filter(Season.id == ep.season_id).first()
                if show and show.imdb_id:
                    imdb_id = show.imdb_id
                    file_record = ep
                    file_path = ep.file_path
            
        if not imdb_id or not file_path:
            return

        loop = asyncio.new_event_loop()
        srt_path = loop.run_until_complete(
            fetch_best_subtitle(imdb_id, file_path, language)
        )
        loop.close()
        
        if srt_path and file_record:
            file_record.subtitle_path = srt_path
            db.commit()
    finally:
        db.close()

@router.post("/movies/{movie_id}/subtitles")
def download_movie_subtitle(movie_id: int, language: str = "en", background_tasks: BackgroundTasks = None, db: Session = Depends(get_db)):
    """Search and download the best matching subtitle for a movie."""
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    background_tasks.add_task(_subtitle_task, movie_id, "movie", language)
    return {"status": f"Subtitle search queued for language '{language}'"}

@router.post("/episodes/{ep_id}/subtitles")
def download_episode_subtitle(ep_id: int, language: str = "en", background_tasks: BackgroundTasks = None, db: Session = Depends(get_db)):
    """Search and download matching subtitle for an episode."""
    ep = db.query(Episode).filter(Episode.id == ep_id).first()
    if not ep:
        raise HTTPException(status_code=404, detail="Episode not found")
    background_tasks.add_task(_subtitle_task, ep_id, "tv", language)
    return {"status": f"Subtitle search queued for language '{language}'"}


# ──────────────────────────── Trailers ────────────────────────────

def _trailer_task(media_id: int, media_type: str):
    from backend.core.db import SessionLocal
    db = SessionLocal()
    try:
        if media_type == "movie":
            media = db.query(Movie).filter(Movie.id == media_id).first()
        else:
            media = db.query(TVShow).filter(TVShow.id == media_id).first()
            
        if not media or not media.tmdb_id:
            return
            
        loop = asyncio.new_event_loop()
        url = loop.run_until_complete(fetch_trailer_url(media.tmdb_id, media_type))
        loop.close()
        
        if url:
            media.trailer_url = url
            db.commit()
    finally:
        db.close()

@router.get("/media/{media_type}/{media_id}/trailer")
def get_trailer(media_type: str, media_id: int, db: Session = Depends(get_db)):
    if media_type == "movie":
        media = db.query(Movie).filter(Movie.id == media_id).first()
    else:
        media = db.query(TVShow).filter(TVShow.id == media_id).first()
    
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    
    # TVShow model might not have trailer_url yet if migration hasn't run
    url = getattr(media, "trailer_url", None)
    return {"trailer_url": url}

@router.post("/media/{media_type}/{media_id}/trailer")
def fetch_trailer(media_type: str, media_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    """Fetch and store the official YouTube trailer URL."""
    if media_type == "movie":
        media = db.query(Movie).filter(Movie.id == media_id).first()
    else:
        media = db.query(TVShow).filter(TVShow.id == media_id).first()
        
    if not media:
        raise HTTPException(status_code=404, detail="Media not found")
    if not media.tmdb_id:
        raise HTTPException(status_code=400, detail="No TMDB ID - scrape first")

    background_tasks.add_task(_trailer_task, media_id, media_type)
    return {"status": "Trailer fetch queued"}
