from fastapi import APIRouter
from pydantic import BaseModel
from typing import Any, Dict
from backend.core.config import settings

router = APIRouter(prefix="/api/settings", tags=["Settings"])

class SettingsPatch(BaseModel):
    api_keys: Dict[str, str] = {}
    rename_templates: Dict[str, str] = {}
    language: str = "en"

@router.get("/")
def get_settings():
    """Return the current persisted settings."""
    return settings.get_settings()

@router.patch("/")
def update_settings(patch: SettingsPatch):
    """Merge and persist settings updates."""
    data = patch.model_dump(exclude_none=True)
    settings.save_settings(data)
    return settings.get_settings()
