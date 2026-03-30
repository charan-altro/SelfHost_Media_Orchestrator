"""
YouTube trailer URL scraper.
Uses TMDB's video endpoint (no YouTube API key needed) to find the official trailer.
Falls back to constructing a YouTube search URL.
"""
import httpx
from backend.core.config import settings

TMDB_BASE = "https://api.themoviedb.org/3"
YOUTUBE_WATCH = "https://www.youtube.com/watch?v="


async def fetch_trailer_url(tmdb_id: str, media_type: str = "movie") -> str | None:
    """
    Fetch the official trailer URL from TMDB's /videos endpoint.
    Returns the first YouTube trailer URL found, or None.
    """
    api_key = settings.get_api_keys().get("tmdb", "")
    if not api_key or not tmdb_id:
        return None

    endpoint = f"{TMDB_BASE}/{media_type}/{tmdb_id}/videos"
    params = {"api_key": api_key, "language": "en-US"}

    async with httpx.AsyncClient(timeout=10) as client:
        try:
            res = await client.get(endpoint, params=params)
            if res.status_code != 200:
                return None
            results = res.json().get("results", [])
            # Prefer Official Trailer on YouTube
            for priority in [
                lambda v: v.get("type") == "Trailer" and v.get("official") and v.get("site") == "YouTube",
                lambda v: v.get("type") == "Trailer" and v.get("site") == "YouTube",
                lambda v: v.get("type") == "Teaser" and v.get("site") == "YouTube",
            ]:
                matches = [v for v in results if priority(v)]
                if matches:
                    key = matches[0]["key"]
                    return f"{YOUTUBE_WATCH}{key}"
        except Exception as e:
            print(f"Trailer fetch failed: {e}")
    return None
