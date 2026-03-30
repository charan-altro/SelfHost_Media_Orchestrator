# SelfHost Media Orchestrator – Task Checklist

## Phase 0: Planning
- [x] Review all user requirements and write implementation_plan.md
- [x] Get user approval on implementation plan

## Phase 1: Project Scaffold
- [x] Create mono-repo directory structure
- [x] Initialize backend (Python/FastAPI/SQLAlchemy)
- [x] Initialize frontend (React/Vite)
- [x] Set up Docker & Docker Compose
- [ ] 🆕 Setup CLI Entrypoint: Command-line parser for headless automation (⚡ optional/future)

## Phase 2: Backend Core
- [x] Database models (Movie, TVShow, Season, Episode, Person)
- [x] Config management (settings, API keys)
- [x] File scanner service (Expanded extensions, robust error handling, strict type enforcement)
- [x] Filename parser (regex engine)
- [x] Media info extractor (MediaInfo wrapper)
- [ ] 🆕 FFmpeg Integration: Deep video analysis for real aspect ratio (⚡ optional/future)

## Phase 3: Metadata Engine
- [x] TMDB scraper (primary – movie + TV)
- [x] OMDb scraper (IMDb ratings, votes, Metascore, awards)
- [x] Cinemagoer fallback (no API key; pip install cinemagoer)
- [x] Scraper chain / fallback logic
- [x] Universal Scraper Combiner (Custom field merging)
- [x] TMDB scraper for TV Shows (search + series details + season/episode details)
- [x] Extract expanded metadata (Cast, Director, Runtime)
- [ ] TVDB scraper (⚡ optional/future)
- [ ] Fanart.tv scraper (⚡ optional/future)
- [ ] 🆕 Anime Scraper: AniDB API integration (⚡ optional/future)
- [ ] 🆕 Additional Scrapers: TVmaze, Trakt.tv, regional scrapers (⚡ optional/future)
- [ ] 🆕 Kodi XML Scraper: Parse local Kodi XML files (⚡ optional/future)
- [ ] Movie Sets/Collections support (⚡ optional/future)

## Phase 4: Artwork & Asset Manager
- [x] Artwork downloader (poster, fanart, banner, logo, discart, clearart)
- [x] Extrafanart / extrathumbs support
- [x] Actor image (.actors folder) support
- [x] Manual artwork override API (GET list, POST upload, DELETE per type)
- [ ] 🆕 FFmpeg Thumbnail Generator (⚡ optional/future)

## Phase 5: NFO & File Management
- [x] NFO generator (Kodi/Jellyfin-compatible XML) for Movies
- [x] NFO generator for TV Shows (tvshow.nfo) and Episodes
- [x] NFO reader/importer
- [x] Renaming template engine
- [x] Safe file move/rename (shutil)
- [x] Junk/orphan file cleanup (CleanupService)
- [x] Duplicate artwork cleanup (hash-based deduplication)
- [x] Empty folder cleanup (bottom-up traversal + Metadata-only safety logic)
- [x] Proper title renaming (folder + file + companion migration + Empty bracket fix)

## Phase 6: Subtitles & Trailers
- [x] Trailer URL scraper (TMDB /videos → YouTube URL stored in DB) for Movies & TV
- [x] OpenSubtitles v3 integration (search + download .srt by IMDB ID) for Movies & Episodes
- [x] Subtitle renamer (saved beside video as `{stem}.{lang}.srt`)
- [x] API endpoints: `POST /api/media/{type}/{id}/subtitles`, `POST /api/media/{type}/{id}/trailer`

## Phase 7: Background Task System & Sync
- [x] Task registry (in-memory: create/update/get/list with cleanup)
- [x] Progress/status reporting to UI (GET /api/tasks, GET /api/tasks/{id})
- [x] Task History Clearing (DELETE /api/tasks and "Clear All" UI button)
- [x] Performance Optimized Progress (UI Throttling for high-frequency tasks)
- [x] Live SSE Progress updates for Library Scanning
- [x] Integration of Scrape, Trailer, and Subtitle tasks into TaskManager
- [x] **Fast Scan & Background Metadata Extraction** (Decoupled ffprobe/NFO reading from initial DB sync)
- [x] Detailed Cleanup Reporting (Auto-generation of `cleanup_report.txt`)
- [ ] 🆕 Trakt.tv Integration (⚡ optional/future)
- [ ] 🆕 App Update Checker (⚡ optional/future)

## Phase 8: REST API Layer
- [x] /api/movies – CRUD (Updated to 10,000 limit)
- [x] /api/tvshows – CRUD (Updated to 10,000 limit)
- [x] /api/scan – trigger scanner
- [x] /api/scrape – trigger scraper (movie + TV)
- [x] /api/rename – trigger rename
- [x] /api/nfo – NFO read/generate
- [x] /api/settings – GET + PATCH configuration
- [x] /api/tasks – task status/progress
- [x] /api/export – CSV, HTML, and JSON Library Backup exports
- [ ] 🆕 /api/sync/trakt (⚡ optional/future)

## Phase 9: Frontend UI
- [x] **Netflix-Style UI Redesign** (Dark theme, Hero banners, Hover scaling, Top Nav)
- [x] Library grid/table view (Handling 10,000+ items without 50-item cap)
- [x] Status badges & real-time search filtering
- [x] Bulk operations panel (Movies & TV Shows separated)
- [x] Fix-Match / Manual search dialog
- [x] Library Path Management (Add, Delete, **Edit Path with Auto-Migration via Modal**)
- [x] Detailed Metadata Modal (Netflix-style, Cast List, Episode Browser)
- [x] **Manual Metadata Editing** (Edit Title, Year, Plot, Director, etc. directly in UI)
- [x] **Non-intrusive UI Notifications** (Replaced browser alerts/prompts with Toast Overlay & Custom Modals)
- [x] Task progress monitor (TasksPage – live polling)
- [x] Export Module (CSV, HTML, JSON Database backup)

## Phase 10: Dockerization
- [x] Multi-stage Dockerfile (Optimized for production)
- [x] docker-compose.yml with volume mounts
- [x] Production build pipeline (Static hosting via FastAPI)

## Phase 11: Testing & Verification
- [x] Unit tests (scanner, parser, scraper, NFO)
- [x] Integration tests (API endpoints)
- [x] End-to-end browser smoke test
- [x] Docker smoke test

## Phase 12: Professional Distribution (Open Source Ready)
- [x] MIT License integration
- [x] Professional README with Badges and Docker Hub links
- [x] Automated GitHub Actions (CI/CD) for Docker Hub
- [x] Codebase sanitization (No hardcoded secrets or personal paths)
- [x] `docker-compose.release.yml` for end-users
- [x] Universal Drive Mapping (.env strategy)

## Phase 13: Hybrid Playback & Streaming (Future)
- [ ] Backend: Environment detection (Native Windows vs. Docker)
- [ ] Backend: Native "One-Click" playback engine (`os.startfile`)
- [ ] Backend: High-performance streaming engine (seekable)
- [ ] Frontend: "Play" button integration in Movie/Episode details
- [ ] Frontend: In-browser Video.js player integration
- [ ] Frontend: "Open in External Player" (.m3u generation)

## Phase 14: Native Windows Packaging (Future)
- [ ] Backend: Update path management for `%APPDATA%` persistence
- [ ] Backend: Bundle `ffmpeg`/`ffprobe` binaries for portable use
- [ ] Frontend: Build static React assets for Python embedding
- [ ] Packaging: PyInstaller configuration for single `.exe` distribution
- [ ] UI: PyWebView integration for native window "Desktop App" feel
- [ ] Installer: Inno Setup / NSIS script for professional Windows installation
