# Live Server-Sent Events (SSE) Progress Tracker

- [x] Create lightweight in-memory tracker `backend/core/progress.py`
- [x] Integrate global state counting and tracking into `backend/services/scanner.py`
- [x] Expose `GET /api/libraries/{library_id}/scan/progress` streaming endpoint
- [x] Setup `Zustand` store definitions and `EventSource` connection handling
- [x] Create floating global `<ScanProgressToast />` in `Layout.tsx`

Ready for user testing!


time : 29/03/2026 20:08 ist
Lazy Metadata Loading & NFO Parsing
- [x] Modify scanner.py to implement "Fast Scan" approach, decoupling slow metadata tasks.
- [x] Implement lazy extract_media_info() and NFO reading in a separate background thread `_background_metadata_task`.
- [x] Enhance _process_movie to fast-register files to bypass UI display limits.
- [x] Enhance nfo_reader.py with parse_tvshow_nfo() functionality
- [x] Handle UI limit rendering blocks to seamlessly show 10,000+ items.
- [x] Replace intrusive window.prompt and window.alert calls with seamless UI Modals and Toast notifications.
- [x] Add tasks manager tracking for background metadata extraction progress.

---
time : 30/03/2026 15:30 ist
Task Management & Advanced Cleanup
- [x] Implement Task History clearing (Backend + UI button).
- [x] Fix empty brackets `[ ]` bug in movie renaming logic.
- [x] Implement full companion file migration (NFO/Art) in RenamerService.
- [x] Enhance Library Cleanup with safe "Ghost Folder" removal (metadata-only folders).
- [x] Implement detailed Cleanup Reporting (`cleanup_report.txt` generation).
- [x] Optimize background task performance via UI Throttling.
- [x] Add real-time folder scanning feedback to Cleanup task UI.
- [x] Fix missing actor data in Movie NFO generation logic.
- [x] Implement automated NFO metadata repair (actor data) during cleanup cycle.
- [x] Optimize Duplicate Artwork scanner with size-collision fast-filtering.