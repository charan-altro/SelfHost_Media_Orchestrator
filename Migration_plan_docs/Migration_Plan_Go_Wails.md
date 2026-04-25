# Migration Plan: SelfHost Media Orchestrator (Python -> Go + Wails)

This plan outlines the steps to convert the existing FastAPI (Python) backend and React/Vite frontend into a single native Windows desktop application using Go and Wails.

## Phase 1: Wails Project Initialization & Configuration
1. **Initialize Go Module:** Create a `go.mod` file for the new Go project.
2. **Create `wails.json`:** Define the Wails configuration to point to the existing `frontend` directory and set up Vite build commands (`npm run build`, `npm run dev`).
3. **Set up Go Entry Point:** Create `main.go` and `app.go`. The `app.go` file will contain the Go application state and methods that will be exposed to the React frontend. `main.go` will initialize the Wails application.

## Phase 2: Database Migration (SQLAlchemy -> GORM)
1. **Schema Definition:** Translate the SQLAlchemy models in `backend/models/media.py` to Go struct equivalents using GORM tags.
2. **Database Connection:** Implement SQLite initialization in Go using GORM, replicating the behavior of `backend/core/db.py`.
3. **Data Layer Interface:** Create a Go repository pattern or database access layer to replace the CRUD operations.

## Phase 3: Backend Logic Translation (Python -> Go)
The Python backend contains several services that need to be translated into Go packages:
1. **Media Scanner (`backend/services/scanner.py`):** Use Go's `path/filepath` and goroutines to scan directories. This will significantly improve performance over Python.
2. **Metadata Parsers (`nfo.py`, `nfo_reader.py`, `parser.py`):** Implement XML parsing using Go's `encoding/xml` for reading and writing Kodi-compatible NFO files.
3. **Scraper (`backend/services/scraper/` & `tmdb`):** Implement TMDB API integration using Go's `net/http` and `encoding/json`. Use goroutines for concurrent scraping.
4. **Artwork/Media Management (`artwork.py`, `cleanup.py`, `mediainfo.py`):** Translate the filesystem operations (downloading images, parsing file properties).
5. **Task Manager (`backend/core/task_manager.py`):** Implement a Go-based background worker pool and task queue to handle scraping, scanning, and cleanup asynchronously.

## Phase 4: API Translation to Wails Bindings
1. **Eliminate HTTP Overhead:** Instead of standard REST API endpoints (`backend/api/*.py`), we will bind Go methods directly to the frontend.
2. **Bind Methods:** Expose methods in `app.go` (or dedicated bound structs) for operations like `GetLibraries()`, `ScanLibrary()`, `GetMovies()`, `UpdateMovie()`, etc.
3. **Event Emitting:** Replace FastAPI websockets or SSE with Wails' native Event system (`runtime.EventsEmit`) to push progress updates and task statuses to the React UI.

## Phase 5: Frontend Integration
1. **Update API Calls:** Modify the React frontend (`frontend/src/`) to replace `fetch` or `axios` calls to the FastAPI backend with calls to the auto-generated Wails JavaScript bindings (`window.go.main.App...`).
2. **Event Listeners:** Update the frontend to listen to Wails events for progress bars and task updates.
3. **Build & Test:** Run `wails dev` to test the integration and ensure the frontend interacts seamlessly with the Go backend.

## Phase 6: Packaging & Deployment
1. **Build Windows Executable:** Run `wails build -platform windows/amd64` to compile the single `.exe`.
2. **Testing:** Test the standalone binary on a clean Windows environment to verify that no dependencies (Python, Node) are required.
