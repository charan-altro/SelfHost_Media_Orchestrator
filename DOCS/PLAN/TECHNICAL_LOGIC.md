# SelfHost Media Orchestrator – Technical Logic Deep-Dive

This document provides a detailed technical breakdown of the "How and Why" behind SelfHost Media Orchestrator's core services. It is designed for developers who want to understand the underlying logic of the system.

---

## 1. Scanner Logic: Two-Phase Enrichment
The SelfHost Media Orchestrator scanner is designed to prioritize UI responsiveness while handling extremely large libraries.

### Phase 1: Fast Directory Sync
- **Operation**: A non-blocking `os.walk` or recursive glob.
- **Logic**: It identifies files with supported extensions (`.mkv`, `.mp4`, etc.) and immediately adds them to the database with a `status='unmatched'`.
- **Primary Goal**: To make the media visible in the UI within seconds, even for libraries with 10,000+ files.

### Phase 2: Background Metadata Extraction (Enrichment)
- **Operation**: A managed background thread (`_background_metadata_task`).
- **Logic**:
    1. **MediaInfo**: It calls `ffprobe` or `pymediainfo` *only* if the resolution/codec metrics are missing.
    2. **Local NFO Parsing**: It checks for any existing `.nfo` file. If found, it parses the XML and updates the database immediately, marking the record as `matched`.
- **Throttling**: To prevent overloading the SQLite database, progress updates to the UI are throttled to once per second using `time.time()`.

---

## 2. Scraper Chain & Fallback Mechanism
The `ScraperChain` orchestrates a series of API calls to build a complete metadata profile.

```mermaid
graph TD
    A[Start Scraper Chain] --> B{Search TMDB}
    B -- Match Found --> C[Fetch TMDB Details]
    B -- No Match --> D[Log Unmatched]
    C --> E{Fetch IMDb ID}
    E -- Success --> F[Fetch OMDb Ratings/Votes]
    E -- Fail / OMDb Limit --> G[Fetch Cinemagoer Fallback]
    F --> H[Merge into Unified Payload]
    G --> H
    H --> I[Download Artwork & Cast Images]
    I --> J[Write NFO & Update DB]
```

### Key Logic:
- **Search Scoring**: TMDB results are scored based on Title similarity (Levenshtein distance) and Year matching.
- **Rate Limiting**: Uses a **Token Bucket** algorithm (40 requests / 10s for TMDB) to prevent API bans.
- **Concurrent Processing**: `asyncio.gather` is used to fetch posters, fanart, and cast images in parallel for maximum speed.

---

## 3. Filename Parsing (Regex Engine)
The parsing logic in `parser.py` is the most critical part of the ingestion process.

### Movie Parsing Pattern:
```python
MOVIE_RE = r'^(.*?)[. (\[]*(?:((?:19|20)\d{2}))[. )\]]*(.*)$'
```
- **Goal**: Separate the Title from the Year and any trailing "tags" (Resolution, Codec).
- **Cleanup**: It automatically strips illegal OS characters and removes empty brackets (`[]`) that often appear in scene releases.

### TV Show & Episode Pattern:
```python
EPISODE_RE = r'^(.*?)[\. _-]S(\d{2})E(\d{2})[\. _-]?(.*)$'
```
- **Goal**: Identify the Season (S) and Episode (E) numbers reliably across various naming formats (`Show.Name.S01E01`, `Show.Name.1x01`, etc.).

---

## 4. Real-Time State Management (SSE + Zustand)
SelfHost Media Orchestrator uses **Server-Sent Events (SSE)** for non-blocking UI updates.

### Backend Task Manager:
- Maintains an in-memory dictionary of `active_tasks`.
- Each task (Scan, Scrape, Subtitle) updates its `progress_pct` and `status` in the dictionary.

### Frontend Synchronization:
- The React app establishes a `GET /api/tasks/stream` stream (SSE).
- The `TaskManager` sends a JSON payload whenever a task status changes.
- The **Zustand Store** accepts these events and updates the global `activeTasks` state instantly, triggering re-renders of progress bars and notification toasts without polling.

---

## 5. Renaming & Migration Logic
When a file is renamed, the system doesn't just move the video file.

1. **Stem Identification**: It finds all companion files sharing the same filename "stem" (`movie.nfo`, `movie-poster.jpg`, `movie.en.srt`).
2. **Atomic Move**: It uses `shutil.move` to relocate the entire bundle to the new destination.
3. **Database Path Migration**: It performs a bulk UPDATE in SQLite to fix all `file_path` records for the moved items, ensuring the metadata remains linked to the new file location.
4. **Safety Check**: It only deletes the old directory if it is truly empty or only contains known "junk" files (e.g., `.DS_Store`, `Thumbs.db`).
