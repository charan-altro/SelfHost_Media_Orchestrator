import os
import json
from pathlib import Path
from pydantic_settings import BaseSettings
from pydantic import Field
from typing import Dict, List, Any

class Settings(BaseSettings):
    CONFIG_DIR: str = Field(default=os.getenv("CONFIG_DIR", "./config"))
    MEDIA_DIR: str = Field(default=os.getenv("MEDIA_DIR", "./media"))
    DATABASE_DIR: str = Field(default=os.getenv("DATABASE_DIR", "./data"))
    DATABASE_URL: str = ""

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        os.makedirs(self.CONFIG_DIR, exist_ok=True)
        os.makedirs(self.MEDIA_DIR, exist_ok=True)
        os.makedirs(self.DATABASE_DIR, exist_ok=True)
        # Check for legacy db path first if user is migrating
        legacy_db = os.path.join(self.DATABASE_DIR, 'mediavault.db')
        new_db = os.path.join(self.DATABASE_DIR, 'orchestrator.db')
        
        db_path = new_db
        if os.path.exists(legacy_db) and not os.path.exists(new_db):
             db_path = legacy_db
             
        self.DATABASE_URL = f"sqlite:///{db_path}"

    def get_api_keys(self) -> Dict[str, str]:
        # Priority 1: Environment Variables (Good for Docker)
        env_keys = {
            "tmdb": os.getenv("TMDB_API_KEY"),
            "omdb": os.getenv("OMDB_API_KEY")
        }
        # Filter out None values
        env_keys = {k: v for k, v in env_keys.items() if v}
        
        # Priority 2: settings.json
        settings_path = Path(self.CONFIG_DIR) / "settings.json"
        json_keys = {}
        if settings_path.exists():
            with open(settings_path, "r") as f:
                try:
                    data = json.load(f)
                    json_keys = data.get("api_keys", {})
                except json.JSONDecodeError:
                    pass
        
        # Merge, environment variables take precedence
        return {**json_keys, **env_keys}

    def get_settings(self) -> Dict[str, Any]:
        settings_path = Path(self.CONFIG_DIR) / "settings.json"
        if not settings_path.exists():
            return {"api_keys": {}, "libraries": [], "general": {}}
        with open(settings_path, "r") as f:
            try:
                return json.load(f)
            except json.JSONDecodeError:
                return {"api_keys": {}, "libraries": [], "general": {}}

    def save_settings(self, data: Dict[str, Any]) -> None:
        settings_path = Path(self.CONFIG_DIR) / "settings.json"
        existing = self.get_settings()
        existing.update(data)
        with open(settings_path, "w") as f:
            json.dump(existing, f, indent=2)

settings = Settings()
