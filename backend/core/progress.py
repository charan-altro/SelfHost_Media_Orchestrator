"""
In-memory progress tracker for long-running background tasks.
Since the application runs locally (often primarily single-worker), 
this global dictionary is sufficient and avoids heavy bulk resources 
like Redis.
"""

from typing import Dict, Any

# Structure: { library_id: {"total": int, "current": int, "file": str, "status": str} }
active_scans: Dict[int, Dict[str, Any]] = {}
