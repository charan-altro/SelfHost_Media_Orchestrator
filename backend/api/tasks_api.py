from fastapi import APIRouter, HTTPException
from backend.core.task_manager import list_tasks, get_task, clear_all_tasks

router = APIRouter(prefix="/api/tasks", tags=["Tasks"])

@router.get("/")
def get_all_tasks():
    """List all background tasks with their current status and progress."""
    return list_tasks()

@router.delete("/")
def clear_tasks():
    """Delete all recorded tasks from the database."""
    try:
        clear_all_tasks()
        return {"status": "ok", "message": "All tasks cleared."}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/{task_id}")
def get_task_status(task_id: str):
    """Get the status of a single background task."""
    task = get_task(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task
