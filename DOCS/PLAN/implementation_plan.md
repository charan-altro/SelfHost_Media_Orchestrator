# SelfHost Media Orchestrator – Master Technical Architecture & Specification

SelfHost Media Orchestrator is a full-stack, Docker-native media management application designed for large-scale movie and TV show libraries (10,000+ items). It provides automated metadata scraping, artwork management, NFO generation, file renaming, and a cinematic, Netflix-style browser UI.

---

## Technical Architecture Overview

### Component 1 – Project Structure
The project is organized as a mono-repo for streamlined development and deployment:

```
SelfHost_Media_Orchestrator/
├── backend/           # FastAPI (Python 3.11+)
│   ├── api/           # RESTful endpoints & routers
│   ├── core/          # Configuration, DB engine, and Task Manager
│   ├── models/        # SQLAlchemy ORM models (SQLite/Alembic)
│   ├── services/      # Core business logic (Scanner, Scraper, etc.)
│   └── tests/         # Pytest suite
├── frontend/          # React + Vite (Typescript)
│   ├── src/           # Components, Pages, and Zustand Store
│   └── vite.config.ts # Build configuration
└── docker/            # Multi-stage Dockerfile & Compose
```

---

### Component 2 – Data Models & Schema
The system uses **SQLAlchemy 2.0** with **Alembic** migrations. Key models include:

| Model | Purpose |
|---|---|
| **Library** | Defines a media type (Movie/TV) and its physical storage path. |
| **Movie** | Core metadata (Title, Year, TMDB ID, Plot, Rating, etc.). |
| **MovieFile** | Physical file metrics mapping (Resolution, Codec, File Path). |
| **TVShow** | Top-level metadata for series (IMDb Rating, Studio, Status). |
| **Season** | Hierarchical link between a TV show and its episodes. |
| **Episode** | Specific metadata for a single television episode. |
| **Person** | Global registry for Cast and Crew (Actor images, Roles). |
| **Task** | Persistent registry of background operations (Scans, Scrapes). |

---

### Component 3 – Core Service Logic

#### 1. Scanner Service (`scanner.py`)
- **Dual-Phase Sync**: Performs a fast preliminary "discovery" scan to sync filenames to the database, followed by a background "enrichment" phase for MediaInfo and NFO parsing.
- **Normalization**: Automatically handles cross-platform path issues (Windows backslashes to Linux slashes).

#### 2. Parser Engine (`parser.py`)
- Uses complex regex patterns to untangle scene-release filenames into structured `ParsedMedia` objects (Title, Year, SXXEXX).

#### 3. Scraper Chain (`scraper/chain.py`)
- **Priority Logic**: Orchestrates a fallback chain: **TMDB** (Primary) → **OMDb/IMDb** (Ratings/Votes) → **Cinemagoer** (Global Fallback).
- **Metadata Merging**: Intelligently merges data from multiple providers to ensure the most complete profile possible.

#### 4. NFO Generator/Reader (`nfo.py`)
- Produces and reads Kodi/Jellyfin-compatible XML files (`movie.nfo`, `tvshow.nfo`). Ensures local metadata is prioritized over internet scraping for faster library rebuilds.

#### 5. Variable-based Renamer (`renamer.py`)
- Allows users to define templates like `${title} (${year}) [${resolution}]`. Handles companion file migration (matching `.nfo` and subtitles move with the video file).

---

### Component 4 – REST API Specification

| Endpoint | Method | Description |
|---|---|---|
| `/api/libraries` | GET/POST/PATCH | Manage media directory mappings and paths. |
| `/api/movies` | GET | List movies with filters (10,000+ item capacity). |
| `/api/tvshows` | GET | List TV shows and nested seasons/episodes. |
| `/api/scan` | POST | Trigger a two-phase library scan. |
| `/api/scrape/bulk`| POST | Queue background metadata scraping tasks. |
| `/api/tasks` | GET/DELETE | Monitor and clear background task history. |
| `/api/export` | GET | Export library data to JSON, CSV, or HTML. |

---

## Recent Iterations & Improvements

### Phase 7: Live Scaling & Progress (March 2026)
- **SSE Streaming**: Implemented Server-Sent Events to push real-time task updates from the Backend Task Manager directly to the Frontend Store.
- **Scanner Optimization**: Refactored the scan loop to be "Lazy". Fast sync happens instantly; slow MediaInfo extraction happens in a managed background thread to prevent UI freezing.
- **Self-Healing Cleanup**: Added automatic orphaned record purging and "ghost" folder removal to keep the database and file system synchronized.

### Phase 9: Netflix-Style UI Overhaul (March 2026)
- **Premium Aesthetics**: Implemented hero banners, hover-scale animations, and detailed fullscreen modals.
- **Dynamic Store**: Integrated Zustand for persistent, high-performance state management of 10,000+ library records.

### Phase 10: Advanced Maintenance & Performance (March 30, 2026)
- **Eligibility-Based Cleanup**: Implemented a "Fast-Scan" duplicate detection algorithm. It groups files by exact byte-size first, skipping expensive MD5 hashing unless a size collision is detected.
- **UI Update Throttling**: Optimized the Task Manager to throttle database commits and UI updates to a maximum of once every 2 seconds, significantly reducing overhead for high-frequency operations.
- **Metadata Repair (NFO)**: Added automatic NFO regeneration to the cleanup cycle. This retroactively fixes incomplete NFO files (e.g., missing actor data) using the rich metadata stored in the database.
- **Safe Orphan Removal**: Enhanced the empty folder cleanup with a "Safety Filter" that preserves any folder containing files larger than 20MB or unrecognized file extensions.
