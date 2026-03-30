import httpx
from typing import Optional
from backend.core.config import settings

class OMDbScraper:
    def __init__(self):
        self.api_key = settings.get_api_keys().get("omdb")

    async def get_imdb_data(self, imdb_id: Optional[str] = None, title: Optional[str] = None, year: Optional[int] = None) -> Optional[dict]:
        if not self.api_key:
            return None
            
        try:
            async with httpx.AsyncClient(timeout=10.0) as client:
                url = f"http://www.omdbapi.com/?apikey={self.api_key}"
                if imdb_id:
                    url += f"&i={imdb_id}"
                elif title:
                    url += f"&t={title}"
                    if year:
                        url += f"&y={year}"
                else:
                    return None
                    
                resp = await client.get(url)
                if resp.status_code == 200:
                    data = resp.json()
                    if data.get("Response") == "True":
                        return {
                            "imdb_rating": float(data.get("imdbRating", 0)) if data.get("imdbRating") != "N/A" else None,
                            "imdb_votes": int(data.get("imdbVotes", "0").replace(",", "")) if data.get("imdbVotes") != "N/A" else None,
                            "metascore": int(data.get("Metascore", 0)) if data.get("Metascore") != "N/A" else None,
                            "content_rating": data.get("Rated") if data.get("Rated") != "N/A" else None,
                        }
        except httpx.RequestError as e:
            print(f"Network error connecting to OMDb: {e}")
            
        return None
