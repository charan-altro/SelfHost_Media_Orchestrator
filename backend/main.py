from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.gzip import GZipMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import FileResponse
from backend.core.db import engine, Base, run_migrations, SessionLocal
from backend.api import movies, libraries, tvshows
from backend.api import (
    settings_api,
    nfo_api,
    media_extras,
    tasks_api,
    export_api,
    artwork_api,
)
import os
import threading
from backend.services.cleanup import CleanupService
from backend.core.task_manager import sanitize_tasks_on_startup

# Create tables for MVP
Base.metadata.create_all(bind=engine)
# Run incremental column migrations on existing DB
run_migrations()
# Sanitize any stuck tasks from a previous crash/reload
sanitize_tasks_on_startup()

app = FastAPI(title="SelfHost Media Orchestrator API", version="1.0.0", strict_slashes=False)

@app.on_event("startup")
async def startup_event():
    # Run a one-time orphan purge in the background when server starts
    def run_purge():
        db = SessionLocal()
        try:
            print("[Startup] Running one-time database self-healing...")
            stats = CleanupService.purge_orphans(db)
            print(f"[Startup] Self-healing complete: {stats}")
        finally:
            db.close()
            
    threading.Thread(target=run_purge, daemon=True).start()

app.add_middleware(GZipMiddleware, minimum_size=1000)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"], # Allow Vite dev server
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(movies.router)
app.include_router(tvshows.router)
app.include_router(libraries.router)
app.include_router(settings_api.router)
app.include_router(nfo_api.router)
app.include_router(media_extras.router)
app.include_router(tasks_api.router)
app.include_router(export_api.router)
app.include_router(artwork_api.router)

@app.get("/api/health")
async def health_check():
    return {"status": "ok", "message": "SelfHost Media Orchestrator API is running"}

# Serve static files from the React build
if os.path.exists("frontend/dist"):
    # Ensure assets directory exists to prevent crash if Vite didn't output any assets (e.g. empty app)
    os.makedirs("frontend/dist/assets", exist_ok=True)
    app.mount("/assets", StaticFiles(directory="frontend/dist/assets"), name="assets")
    
    @app.get("/{full_path:path}")
    async def serve_frontend(full_path: str):
        # Prevent API routes from falling through to the frontend index.html parser if they 404
        if full_path.startswith("api/"):
            return {"error": "Not Found"}
            
        # Serve specific file if it exists, else serve index.html for SPA routing
        target_path = os.path.join("frontend/dist", full_path)
        if os.path.exists(target_path) and os.path.isfile(target_path):
            return FileResponse(target_path)
            
        return FileResponse("frontend/dist/index.html")
