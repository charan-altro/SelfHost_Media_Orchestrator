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
        
        legacy_db_data = os.path.join(self.DATABASE_DIR, 'mediavault.db')
        legacy_db_config = os.path.join(self.CONFIG_DIR, 'mediavault.db')
        new_db = os.path.join(self.DATABASE_DIR, 'orchestrator.db')
        
        db_path = new_db
        # Priority 1: Use new db if it already exists
        if os.path.exists(new_db):
            db_path = new_db
        # Priority 2: Use legacy db if it exists in data/
        elif os.path.exists(legacy_db_data):
            db_path = legacy_db_data
        # Priority 3: Migration! If it exists in config/ but not in data/, move it to data/
        elif os.path.exists(legacy_db_config):
            import shutil
            try:
                print(f"[Migration] Legacy database found at {legacy_db_config}. Migrating to {new_db}...")
                shutil.copy2(legacy_db_config, new_db)
                print(f"[Migration] Successfully migrated database to {new_db}. Using new location.")
                db_path = new_db
                # Optionally rename the old one so we don't try to migrate it again if something fails
                # os.rename(legacy_db_config, legacy_db_config + ".migrated")
            except Exception as e:
                print(f"[Migration] CRITICAL: Failed to migrate legacy database: {e}. Falling back to old location.")
                db_path = legacy_db_config

        # Ensure we have an absolute path for SQLAlchemy
        abs_db_path = os.path.abspath(db_path)
        
        # Check for directory writability to prevent "readonly database" errors in Docker
        db_dir = os.path.dirname(abs_db_path)
        if not os.access(db_dir, os.W_OK):
            print(f"WARNING: Database directory {db_dir} is NOT writable! SQLite may fail.")
        
        self.DATABASE_URL = f"sqlite:///{abs_db_path}"

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
