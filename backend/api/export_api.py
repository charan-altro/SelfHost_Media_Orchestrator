from fastapi import APIRouter, Depends
from fastapi.responses import StreamingResponse
from sqlalchemy.orm import Session
from backend.core.db import get_db
from backend.services.exporter import export_csv, export_html, backup_library_to_json

router = APIRouter(prefix="/api/export", tags=["Export"])

@router.get("/library/{library_id}/backup")
def download_library_backup(library_id: int, db: Session = Depends(get_db)):
    """Download a full metadata backup of a specific library as JSON."""
    json_content = backup_library_to_json(db, library_id)
    return StreamingResponse(
        iter([json_content]),
        media_type="application/json",
        headers={"Content-Disposition": f"attachment; filename=orchestrator_lib_{library_id}_backup.json"},
    )

@router.get("/csv")
def download_csv(db: Session = Depends(get_db)):
    """Download the full movie library as a CSV file."""
    csv_content = export_csv(db)
    return StreamingResponse(
        iter([csv_content]),
        media_type="text/csv",
        headers={"Content-Disposition": "attachment; filename=orchestrator_library.csv"},
    )

@router.get("/html")
def download_html(db: Session = Depends(get_db)):
    """Download the full movie library as a styled HTML report."""
    html_content = export_html(db)
    return StreamingResponse(
        iter([html_content]),
        media_type="text/html",
        headers={"Content-Disposition": "attachment; filename=orchestrator_library.html"},
    )
