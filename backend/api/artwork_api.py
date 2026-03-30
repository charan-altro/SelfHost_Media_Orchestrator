import os
import shutil
from pathlib import Path
from fastapi import APIRouter, Depends, HTTPException, UploadFile, File, Query
from fastapi.responses import FileResponse
from sqlalchemy.orm import Session
from backend.core.db import get_db
from backend.models.media import Movie

router = APIRouter(prefix="/api/artwork", tags=["Artwork"])

IMAGE_EXTS = {".jpg", ".jpeg", ".png", ".webp"}
ARTWORK_TYPES = {"poster", "fanart", "logo", "banner", "thumb", "discart", "clearart"}

@router.get("/local")
def serve_local_artwork(path: str = Query(..., description="Absolute path to the local image")):
    """Serves a local image file from the disk."""
    if not os.path.exists(path):
        raise HTTPException(status_code=404, detail="Image not found")
    
    ext = Path(path).suffix.lower()
    if ext not in IMAGE_EXTS:
        raise HTTPException(status_code=400, detail="Invalid image format")
        
    return FileResponse(path)


def _find_artwork(movie: Movie) -> list[dict]:
    """Scan the movie's folder and return all image file info."""
    if not movie.files:
        return []
    folder = os.path.dirname(movie.files[0].file_path)
    if not os.path.exists(folder):
        return []
    results = []
    for f in os.listdir(folder):
        if Path(f).suffix.lower() in IMAGE_EXTS:
            full = os.path.join(folder, f)
            results.append({
                "filename": f,
                "path": full,
                "size_bytes": os.path.getsize(full),
            })
    return results


@router.get("/movies/{movie_id}")
def list_artwork(movie_id: int, db: Session = Depends(get_db)):
    """List all artwork image files currently on disk for a movie."""
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    return {"movie_id": movie_id, "artwork": _find_artwork(movie)}


@router.post("/movies/{movie_id}/upload")
async def upload_artwork(
    movie_id: int,
    artwork_type: str = "poster",
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    """
    Upload a custom image file to replace a specific artwork type.
    The file is saved as `MovieTitle (Year)-{artwork_type}.ext` in the movie folder.
    """
    if artwork_type not in ARTWORK_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid artwork_type. Choose from: {ARTWORK_TYPES}")
    
    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    if not movie.files:
        raise HTTPException(status_code=400, detail="No video file associated with this movie")

    folder = os.path.dirname(movie.files[0].file_path)
    base_name = Path(movie.files[0].file_path).stem
    ext = Path(file.filename or "image.jpg").suffix.lower() or ".jpg"

    dest_path = os.path.join(folder, f"{base_name}-{artwork_type}{ext}")

    content = await file.read()
    with open(dest_path, "wb") as f_out:
        f_out.write(content)

    return {"status": "uploaded", "path": dest_path}


@router.delete("/movies/{movie_id}/{artwork_type}")
def delete_artwork(movie_id: int, artwork_type: str, db: Session = Depends(get_db)):
    """Delete a specific artwork type file for a movie."""
    if artwork_type not in ARTWORK_TYPES:
        raise HTTPException(status_code=400, detail=f"Invalid artwork_type. Choose from: {ARTWORK_TYPES}")

    movie = db.query(Movie).filter(Movie.id == movie_id).first()
    if not movie:
        raise HTTPException(status_code=404, detail="Movie not found")
    if not movie.files:
        raise HTTPException(status_code=400, detail="No file associated")

    folder = os.path.dirname(movie.files[0].file_path)
    base_name = Path(movie.files[0].file_path).stem

    deleted = []
    for ext in IMAGE_EXTS:
        candidate = os.path.join(folder, f"{base_name}-{artwork_type}{ext}")
        if os.path.exists(candidate):
            os.remove(candidate)
            deleted.append(candidate)

    if not deleted:
        raise HTTPException(status_code=404, detail=f"No {artwork_type} file found for this movie")

    return {"status": "deleted", "files": deleted}
