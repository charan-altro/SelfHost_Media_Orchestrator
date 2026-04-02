"""
Database-backed task registry for tracking background job status.
Provides create_task(), update_task(), get_task(), list_tasks() helpers.
"""
import uuid
from datetime import datetime
from typing import Optional
from sqlalchemy.orm import Session
from backend.core.db import SessionLocal
from backend.models.media import BackgroundTask

TASK_STATUS = {"queued", "running", "done", "error"}

def create_task(name: str, total: int = 100) -> str:
    """Register a new background task in the database. Returns task_id."""
    import time
    max_retries = 5
    task_id = str(uuid.uuid4())[:8]

    for attempt in range(max_retries):
        db = SessionLocal()
        try:
            task = BackgroundTask(
                id=task_id,
                name=name,
                status="queued",
                progress=0,
                total=total,
                message="Queued",
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(task)
            db.commit()
            return task_id
        except Exception as e:
            db.rollback()
            err_msg = str(e).lower()
            if ("locked" in err_msg or "readonly" in err_msg) and attempt < max_retries - 1:
                time.sleep(0.2 * (attempt + 1))
                continue
            print(f"[TaskManager] Failed to create task '{name}': {e}")
            # If it truly fails (e.g. readonly and retries exhausted), we still return the ID 
            # so the caller doesn't necessarily crash, though updates will likely fail too.
            return task_id 
        finally:
            db.close()
    return task_id

def update_task(task_id: str, status: Optional[str] = None, progress: Optional[int] = None, total: Optional[int] = None, message: str = "", db: Session = None):
    """Update task progress and status in the database with retry logic for SQLite locks."""
    import time
    
    # If a session is provided, use it directly (no retries needed as we are part of the caller's transaction)
    if db:
        _update_task_record(db, task_id, status, progress, total, message)
        db.commit()
        return

    # Otherwise, open a new session with retries
    from backend.core.db import SessionLocal
    max_retries = 5
    for attempt in range(max_retries):
        new_db = SessionLocal()
        try:
            _update_task_record(new_db, task_id, status, progress, total, message)
            new_db.commit()
            new_db.close()
            break # Success
        except Exception as e:
            new_db.rollback()
            err_msg = str(e).lower()
            new_db.close()
            
            if "locked" in err_msg and attempt < max_retries - 1:
                time.sleep(0.2 * (attempt + 1)) # Backoff
                continue
            
            print(f"[TaskManager] Failed to update task {task_id}: {e}")
            break

def _update_task_record(db: Session, task_id: str, status: Optional[str], progress: Optional[int], total: Optional[int], message: str):
    task = db.query(BackgroundTask).filter(BackgroundTask.id == task_id).first()
    if not task:
        return
        
    if status:
        task.status = status
        if status in {"done", "error"}:
            duration = (datetime.utcnow() - task.created_at).total_seconds()
            task.duration = round(duration, 2)
            
    if total is not None:
        task.total = total
    if progress is not None:
        task.progress = min(progress, task.total if task.total > 0 else 1000000)
    if message:
        task.message = message
        
    task.updated_at = datetime.utcnow()

def get_task(task_id: str) -> Optional[dict]:
    db = SessionLocal()
    try:
        task = db.query(BackgroundTask).filter(BackgroundTask.id == task_id).first()
        if not task:
            return None
        return _serialize_task(task)
    finally:
        db.close()

def list_tasks() -> list[dict]:
    """Return all tasks sorted by creation time, newest first."""
    db = SessionLocal()
    try:
        tasks = db.query(BackgroundTask).order_by(BackgroundTask.created_at.desc()).all()
        return [_serialize_task(t) for t in tasks]
    finally:
        db.close()

def cleanup_old_tasks(max_done: int = 50):
    """Keep only the last max_done completed tasks to prevent database growth."""
    db = SessionLocal()
    try:
        done_tasks = db.query(BackgroundTask).filter(BackgroundTask.status.in_(["done", "error"])).order_by(BackgroundTask.updated_at.desc()).all()
        if len(done_tasks) > max_done:
            to_delete = done_tasks[max_done:]
            for t in to_delete:
                db.delete(t)
            db.commit()
    finally:
        db.close()

def sanitize_tasks_on_startup():
    """Find any tasks stuck in 'running' or 'queued' state from a previous session and mark them as error."""
    db = SessionLocal()
    try:
        stuck_tasks = db.query(BackgroundTask).filter(BackgroundTask.status.in_(["running", "queued"])).all()
        for t in stuck_tasks:
            t.status = "error"
            t.message = "Task interrupted (Server Restart)"
            t.updated_at = datetime.utcnow()
        db.commit()
        if stuck_tasks:
            print(f"[Startup] Sanitized {len(stuck_tasks)} stuck background tasks.")
    finally:
        db.close()

def clear_all_tasks():
    """Delete all background tasks from the database."""
    db = SessionLocal()
    try:
        db.query(BackgroundTask).delete()
        db.commit()
    finally:
        db.close()

def _serialize_task(task: BackgroundTask) -> dict:
    return {
        "id": task.id,
        "name": task.name,
        "status": task.status,
        "progress": task.progress,
        "total": task.total,
        "message": task.message,
        "duration": task.duration,
        "created_at": task.created_at.isoformat(),
        "updated_at": task.updated_at.isoformat(),
    }
