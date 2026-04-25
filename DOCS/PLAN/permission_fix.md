# Plan: Fix Permission Denied Errors and Improve Robustness

This plan addresses the "Permission denied" errors reported by the user when running "Bulk Scrape" and "Cleanup" operations. These errors typically occur when the application (running as a non-root user in Docker) tries to overwrite existing NFO files on a host-mounted NTFS volume (external HDD) where permissions are restricted or files are marked read-only.

## Objective
- Resolve "Permission denied" when writing NFO files.
- Improve error handling and diagnostics for file I/O operations.
- Add PUID/PGID support to the Docker container for better permission management.

## Key Files & Context
- `backend/services/nfo.py`: The primary source of the error.
- `backend/services/cleanup.py`: Uses NFO generation during cleanup.
- `docker/Dockerfile`: Defines the container user and environment.
- `docker-compose.yml`: Defines volume mounts and environment variables.

## Implementation Steps

### 0. Documentation Update
- Save this implementation plan to `DOCS/PLAN/permission_fix.md` for project history, ensuring no existing files in that directory are deleted or overwritten.

### 1. Enhance `NFOGenerator` with Robust File Writing
Modify `backend/services/nfo.py` to use a more resilient writing strategy:
- Attempt to `os.remove()` the existing NFO file before writing a new one. On many filesystems (including NTFS via Docker Desktop), deleting an existing file and creating a new one is more reliable than overwriting if the file has restricted permissions.
- If `os.remove()` fails, attempt to `os.chmod()` it to a writable state before trying again.
- Provide clearer error messages indicating *why* it failed (e.g., if the file exists and couldn't be removed).

### 2. Improve Cleanup Service Logging
Modify `backend/services/cleanup.py`:
- Ensure that NFO regeneration failures are logged with more context to help users identify specific problematic files.

### 3. Support PUID/PGID in Docker (Optional but Recommended)
Standardize the container to handle host permissions better:
- Update `docker/Dockerfile` to allow changing the `appuser` UID/GID at runtime via `PUID` and `PGID` environment variables.
- Add a `docker/entrypoint.sh` script to perform the `usermod`/`groupmod` operations.
- This is a common pattern for self-hosted media apps to avoid permission headaches on Linux and WSL2.

## Verification & Testing
1. **Manual Verification**: Run the "Bulk Scrape" operation and check if the "Permission denied" errors persist in the logs.
2. **Cleanup Verification**: Run the "Cleanup" operation and verify the output log for NFO regeneration.
3. **Log Review**: Ensure the new, more detailed logs appear when a file cannot be written.
