import httpx
from typing import Optional
from backend.core.config import settings

TMDB_API_URL = "https://api.tmdb.org/3"

class TMDBScraper:
    def __init__(self):
        self.api_key = settings.get_api_keys().get("tmdb")
        self.headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Accept": "application/json"
        }

    async def search_movies(self, title: str, year: Optional[int] = None) -> list[dict]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                params = {"query": title}
                if year:
                    params["primary_release_year"] = str(year)
                    
                resp = await client.get(f"{TMDB_API_URL}/search/movie", headers=self.headers, params=params)
                if resp.status_code == 200:
                    return resp.json().get("results", [])
                else:
                    print(f"TMDB search_movies HTTP {resp.status_code}: {resp.text}")
        except httpx.RequestError as e:
            print(f"Network error connecting to TMDB: {e}")
        return []

    async def search_movie(self, title: str, year: Optional[int] = None) -> Optional[dict]:
        results = await self.search_movies(title, year)
        return results[0] if results else None

    async def search_tv_shows(self, title: str, year: Optional[int] = None) -> list[dict]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                params = {"query": title}
                if year:
                    params["first_air_date_year"] = str(year)
                    
                resp = await client.get(f"{TMDB_API_URL}/search/tv", headers=self.headers, params=params)
                if resp.status_code == 200:
                    return resp.json().get("results", [])
        except httpx.RequestError as e:
            print(f"Network error connecting to TMDB: {e}")
        return []

    async def search_tv(self, title: str, year: Optional[int] = None) -> Optional[dict]:
        results = await self.search_tv_shows(title, year)
        return results[0] if results else None

    async def get_movie_details(self, tmdb_id: str) -> Optional[dict]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                # Append to get credits, releases, and extended images at the same time
                resp = await client.get(
                    f"{TMDB_API_URL}/movie/{tmdb_id}?append_to_response=credits,release_dates,images", 
                    headers=self.headers
                )
                if resp.status_code == 200:
                    return resp.json()
                else:
                    print(f"TMDB get_movie_details HTTP {resp.status_code}: {resp.text}")
        except httpx.RequestError as e:
            print(f"Network error connecting to TMDB: {e}")
            
        return None

    async def get_tv_details(self, tmdb_id: str) -> Optional[dict]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{TMDB_API_URL}/tv/{tmdb_id}?append_to_response=credits,external_ids,images", 
                    headers=self.headers
                )
                if resp.status_code == 200:
                    return resp.json()
        except httpx.RequestError as e:
            print(f"Network error connecting to TMDB: {e}")
        return None
        
    async def get_tv_season(self, tmdb_id: str, season_number: int) -> Optional[dict]:
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                resp = await client.get(
                    f"{TMDB_API_URL}/tv/{tmdb_id}/season/{season_number}", 
                    headers=self.headers
                )
                if resp.status_code == 200:
                    return resp.json()
        except httpx.RequestError as e:
            print(f"Network error connecting to TMDB: {e}")
        return None
