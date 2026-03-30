"""
OpenSubtitles v3 REST API integration.
API docs: https://opensubtitles.stoplight.io/docs/opensubtitles-api
Requires OPENSUBTITLES_API_KEY in settings.json
"""
import os
import httpx
from pathlib import Path
from backend.core.config import settings

OPENSUBTITLES_BASE = "https://api.opensubtitles.com/api/v1"

async def search_subtitles(imdb_id: str, language: str = "en") -> list[dict]:
    """Search OpenSubtitles for matching subtitles by IMDB ID."""
    api_key = settings.get_api_keys().get("opensubtitles", "")
    if not api_key:
        return []

    headers = {
        "Api-Key": api_key,
        "Content-Type": "application/json",
    }
    params = {
        "imdb_id": imdb_id.lstrip("tt"),
        "languages": language,
        "type": "movie",
    }
    async with httpx.AsyncClient(timeout=15) as client:
        try:
            res = await client.get(f"{OPENSUBTITLES_BASE}/subtitles", headers=headers, params=params)
            if res.status_code == 200:
                data = res.json()
                return data.get("data", [])
        except Exception as e:
            print(f"OpenSubtitles search failed: {e}")
    return []


async def download_subtitle(file_id: int, dest_path: str, language: str = "en") -> str | None:
    """Download a subtitle file by file_id and save to dest_path."""
    api_key = settings.get_api_keys().get("opensubtitles", "")
    if not api_key:
        return None

    headers = {
        "Api-Key": api_key,
        "Content-Type": "application/json",
    }
    payload = {"file_id": file_id}

    async with httpx.AsyncClient(timeout=30) as client:
        try:
            # Step 1: Get download link
            res = await client.post(f"{OPENSUBTITLES_BASE}/download", headers=headers, json=payload)
            if res.status_code != 200:
                return None
            link = res.json().get("link")
            if not link:
                return None

            # Step 2: Follow download link
            dl = await client.get(link, follow_redirects=True)
            if dl.status_code != 200:
                return None

            # Save the file
            srt_path = f"{dest_path}.{language}.srt"
            with open(srt_path, "wb") as f:
                f.write(dl.content)
            return srt_path
        except Exception as e:
            print(f"Subtitle download failed: {e}")
    return None


async def fetch_best_subtitle(imdb_id: str, video_file_path: str, language: str = "en") -> str | None:
    """
    High-level helper: search for the best subtitle match and download it
    beside the video file. Returns path to downloaded .srt or None.
    """
    results = await search_subtitles(imdb_id, language)
    if not results:
        return None

    # Take highest download count (most trusted)
    results.sort(key=lambda r: r.get("attributes", {}).get("download_count", 0), reverse=True)
    best = results[0]
    files = best.get("attributes", {}).get("files", [])
    if not files:
        return None

    file_id = files[0]["file_id"]
    dest_base = str(Path(video_file_path).with_suffix(""))
    return await download_subtitle(file_id, dest_base, language)
