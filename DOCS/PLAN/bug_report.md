# SelfHost Media Orchestrator – Bug Report & Resolutions Registry

This document serves as the official registry of all critical bugs identified and resolved during the development of SelfHost Media Orchestrator. Each entry includes a description of the issue, its technical root cause, and the specific resolution implemented.

---

## 1. Library Export `NameError` (Internal Server Error)
- **Description**: Calling the JSON library export (`GET /api/export/library/{id}/backup`) failed with a `500 Internal Server Error`.
- **Root Cause**: In `backend/services/exporter.py`, a nested list comprehension for extracting episodes used an incorrect loop variable reference (`c` instead of `ep`).
- **Resolution**: Corrected the reference to `ep.__table__.columns` to ensure proper dictionary comprehension during export.

## 2. Missing Trailer Attribute for TV Shows (`AttributeError`)
- **Description**: Checking trailers for newly matched TV shows caused a `500 Internal Server Error` (`'TVShow' object has no attribute 'trailer_url'`).
- **Root Cause**: The `TVShow` SQLAlchemy model lacked the `trailer_url` column, which was only present on the `Movie` model.
- **Resolution**: Added `trailer_url = Column(String, nullable=True)` to the `TVShow` model and patched the API to use `getattr(media, "trailer_url", None)` for defensive attribute access.

## 3. UI Paging Issue (Stuck at 50 Items)
- **Description**: Large libraries (300+ items) only displayed the first 50 items in the frontend dashboard.
- **Root Cause**: The FastAPI endpoints `/api/movies/` and `/api/tvshows/` had a hardcoded default `limit=50` in the function signature.
- **Resolution**: Updated the default limit to `10,000` to allow the React frontend to fetch and manage the complete library using local filtering.

## 4. Suboptimal UI Popups (Prompt/Alert)
- **Description**: Settings features used native browser `window.prompt()` and `window.alert()` dialogues, breaking the immersive Netflix-style aesthetic.
- **Root Cause**: Initial MVP used simple browser dialogues for rapid prototyping.
- **Resolution**: Implemented a custom `EditLibraryModal.tsx` and a global, Zustand-powered `NotificationOverlay.tsx` for non-blocking, stylish toast messages.

## 5. Missing Database Column (`OperationalError`)
- **Description**: App startup failed with `sqlite3.OperationalError: no such column: tv_shows.trailer_url`.
- **Root Cause**: While the SQLAlchemy model was updated, the lightweight internal migration system was not triggered to add the column to existing SQLite files.
- **Resolution**: Added `ALTER TABLE tv_shows ADD COLUMN trailer_url TEXT` to the `_MIGRATIONS` array in `backend/core/db.py`.

## 6. Background Task Visibility
- **Description**: Metadata extraction and scraper tasks were running invisibly, giving no feedback to the user on progress.
- **Root Cause**: The UI was only listening for initial SSE "scan" events and not polling the global `TaskManager`.
- **Resolution**: Updated the frontend store to poll the `/api/tasks` endpoint and display active processing tasks in a floating progress notification area.

## 7. TV Shows Persisting After Library Deletion
- **Description**: Deleting a library removed movies but left TV shows visible in the UI.
- **Root Cause**: The `delete_library` function in the API only queried and deleted `Movie` records linked to the library ID.
- **Resolution**: Updated the deletion logic to explicitly find and remove all `TVShow` (and their nested `Season`/`Episode`) records associated with the library ID.

## 8. Ghost Media Records (Orphans)
- **Description**: Some media records appeared in the UI even if their parent library was deleted or no longer existed.
- **Root Cause**: Orphaned records were left in the DB from previous failed deletions (Bug 7).
- **Resolution**: Implemented `CleanupService.purge_orphans(db)`, which is called during every `list_libraries` request to "self-heal" the database by removing media records with invalid library IDs.

## 9. Empty Brackets in Filenames (`[ ]`)
- **Description**: Movie files were renamed with empty brackets like `Movie Title (2024) [ ].mp4`.
- **Root Cause**: The `RenamerService` template included placeholders forResolution and Codec. If these were missing/null, the whitespace in the template left artifacts.
- **Resolution**: Updated `RenamerService` with a robust regex (`\[\s*\]`) to identify and strip empty or whitespace-only brackets during the renaming commit.

## 10. Incomplete Companion File Migration
- **Description**: Renaming a movie left behind `.nfo` or `.jpg` files in the old folder.
- **Root Cause**: `RenamerService.rename_movie` only handled the primary video file `.mkv`/`.mp4`.
- **Resolution**: Implemented "Stem-based migration" which identifies every file sharing the original filename prefix and moves/renames the entire bundle (NFO, artwork, subtitles) to the new destination.

## 11. Invisible & Unresponsive Cleanup Task
- **Description**: "Deep Cleanup" ran silently and appeared to "hang" the system for large libraries.
- **Root Cause**: The cleanup service was committing to the database after every single folder scan, causing massive I/O overhead. It was also not registered with the `TaskManager`.
- **Resolution**: Registered the cleanup task with `TaskManager`. Implemented "UI Throttling" that only commits and sends SSE progress updates once per second, resulting in a 10x performance boost for large directories.

## 12. Missing Actor Photos in Movie NFOs
- **Description**: Movies matched via TMDB showed actor photos in the UI, but after a library scan, those photos would sometimes disappear.
- **Root Cause**: `NFOGenerator.generate_movie_nfo` was missing the `<actor>` section. Since the scanner prioritizes local NFO files, it would overwrite the rich database metadata with incomplete NFO data.
- **Resolution**: Updated `NFOGenerator` to include full cast data (names, roles, and TMDB thumb URLs) in movie NFOs. Added a `regenerate_nfos` feature to the Cleanup service to retroactively fix existing files.

## 13. Cleanup Crash: `'dict' object has no attribute 'name'`
- **Description**: The background cleanup task crashed with a Python error when trying to regenerate NFO files.
- **Root Cause**: The code assumed `movie.cast` and `movie.genres` were SQLAlchemy relationship objects, but they are actually `JSON` columns that return standard Python dictionaries and lists.
- **Resolution**: Corrected the iteration logic in `CleanupService.regenerate_nfos` to use dictionary-safe access for the cast and genre metadata fields.
