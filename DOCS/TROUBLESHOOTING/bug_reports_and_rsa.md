# Bug Reports & Root Cause Analysis (RSA)

This document serves as a historical log of critical, systemic bugs encountered during development. It details the Root Cause Analysis (RSA), the implemented solutions, and the rationale behind those changes to prevent regressions.

---

## Issue 1: Severe Pagination & Query Limits (Frontend Missing Files)
**Status**: Resolved

### The Bug
The backend multi-threaded scanner successfully discovered and processed 315 files within the media directory. However, the frontend dashboard only displayed a hard-capped maximum of 50 movies.

### Root Cause Analysis (RSA)
The issue was traced to the interaction between the FastAPI endpoint and the React frontend state.
1. The backend endpoint responsible for listing movies (`GET /api/media`) contained an unintentional default pagination parameter (`limit=50`).
2. The frontend Zustand store did not implement a "load more" recursive fetch or infinite scroll to request data beyond the first 50 items.
3. Therefore, while the backend database correctly saved all 315 items, the UI silently capped the payload response.

### Implemented Solution
- **Action**: Modified the API endpoint logic. The explicit hard-limit default in `backend/api.py` was removed or expanded for the `GET` request. 
- **Action**: Updated the React dashboard to correctly track total counts vs displayed counts to warn users if the payload is truncated.

---

## Issue 2: I/O Wait Bottleneck during Media Scanning
**Status**: Resolved

### The Bug
Early versions of the scanner took upwards of 10-15 minutes to process a moderate library (1000+ files), causing the application to feel unresponsive and sluggish, particularly on NAS drives.

### Root Cause Analysis (RSA)
The application was using a strictly sequential, single-threaded processing loop.
1. The system called `os.walk()`.
2. For each file found, it called `pymediainfo` (which reads the file header from disk).
3. Then it waited for a response from the TMDB API.
4. Then it inserted the row into SQLite.
5. Because steps 2 and 3 are severely I/O-bound (waiting on physical disk read speeds or network API latency), the CPU sat idle at 1% usage while the single thread blocked.

### Implemented Solution
- **Action**: Completely refactored `Scanner Engine` into a multi-threaded architecture using Python's `ThreadPoolExecutor`.
- **Logic**: Header extraction and API fetching now run concurrently across 4 to 8 workers using `asyncio.gather`.
- **Result**: Scan times dropped by over 70%, reducing a 9-minute task to ~2 minutes.

---

## Issue 3: SQLite "Read-Only Database" Locking
**Status**: Resolved

### The Bug
Users attempting to run the Docker container on a Windows Host, mapping the configuration drive directly to a physical Windows drive (e.g., `-v D:\config:/config`), encountered frequent 500 Server Errors declaring the SQLite database was "read-only" or locked.

### Root Cause Analysis (RSA)
Docker volume mapping between Windows (NTFS/SMB) and the internal Linux container environment creates filesystem permission mismatches.
1. When multiple threads inside the Linux container attempted to write to the `mediavault.db` file mapped to the Windows host, the Windows POSIX translation layer would aggressively lock the file.
2. The SQLAlchemy connection pool could not bypass this lock, causing a hard crash.

### Implemented Solution
- **Action**: Decentralized the volume mapping. User settings and legacy backups remain on the mapped `/config` volume, but the live `orchestrator.db` file was moved to an internal, native Docker named volume: `/data`.
- **Logic**: Built an automated Migration routine in the initialization script to detect existing Windows host databases and physically `shutil.copy` them into the native, high-speed Linux volume to guarantee write permissions.
