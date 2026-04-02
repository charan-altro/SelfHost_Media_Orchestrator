import os
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException
from fastapi.responses import Response
from sqlalchemy.orm import Session
from backend.core.db import get_db
from backend.models.media import Movie
from backend.services.nfo import NFOGenerator

router = APIRouter(prefix="/api/nfo", tags=["NFO"])

def _movie_to_metadata(movie: Movie) -> dict:
    file_info = movie.files[0] if movie.files else None
    return {
        "title": movie.title,
        "original_title": movie.original_title,
        "sort_title": movie.sort_title,
        "year": movie.year,
        "plot": movie.plot,
        "tagline": movie.tagline,
        "tmdb_id": movie.tmdb_id,
        "imdb_id": movie.imdb_id,
        "tmdb_rating": movie.tmdb_rating,
        "imdb_rating": movie.imdb_rating,
        "genres": movie.genres.split(",") if movie.genres else [],
        "resolution": file_info.resolution if file_info else None,
        "video_codec": file_info.video_codec if file_info else None,
        "audio_codec": file_info.audio_codec if file_info else None,
        "audio_channels": file_info.audio_channels if file_info else None,
    }

@router.get("/movies/{movie_id}")
def get_movie_nfo(movie_id: int, db: Session = Depends(get_db)):
    """Return the raw contents of the NFO file for a movie."""
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    if not movie.files:
        raise HTTPException(status_code=400, detail="No file associated with this movie")

    file_path = movie.files[0].file_path
    nfo_path = str(Path(file_path).with_suffix(".nfo"))

    if not os.path.exists(nfo_path):
        raise HTTPException(status_code=404, detail="NFO file not found on disk")

    with open(nfo_path, "r", encoding="utf-8") as f:
        contents = f.read()

    return Response(content=contents, media_type="application/xml")

@router.post("/movies/{movie_id}/generate")
def generate_movie_nfo(movie_id: int, db: Session = Depends(get_db)):
    """(Re)generate NFO on disk from current database metadata."""
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    if not movie.files:
        raise HTTPException(status_code=400, detail="No file associated")
    if movie.status != "matched":
        raise HTTPException(status_code=400, detail="Movie must be scraped before generating NFO")

    metadata = _movie_to_metadata(movie)
    gen = NFOGenerator()
    nfo_path, success = gen.generate_movie_nfo(metadata, movie.files[0].file_path)
    if not success:
        from fastapi import HTTPException
        raise HTTPException(status_code=500, detail="Permission denied writing NFO file. Check folder permissions.")
    return {"status": "generated", "nfo_path": nfo_path}
