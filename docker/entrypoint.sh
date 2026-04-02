#!/bin/bash

# Default UID and GID if not provided
PUID=${PUID:-1000}
PGID=${PGID:-1000}

if [ "$PUID" -eq 0 ]; then
    echo "[Entrypoint] Running as root"
    # Ensure internal directories are owned by root (already are by default in Docker if not chowned)
    # But we want to be sure they are writable
    mkdir -p /app /config /data /media
    exec "$@"
else
    echo "[Entrypoint] Using PUID=$PUID and PGID=$PGID"

    # Update appuser UID/GID
    groupmod -o -g "$PGID" appuser 2>/dev/null || true
    usermod -o -u "$PUID" appuser 2>/dev/null || true

    # Ensure internal directories are owned by appuser
    # We do this on every startup to catch volume permission changes
    chown -R appuser:appuser /app /config /data /media

    # Switch to appuser and run the command
    exec gosu appuser "$@"
fi
