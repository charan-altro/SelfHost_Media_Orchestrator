from backend.services.scraper.tmdb import TMDBScraper
from backend.services.scraper.omdb import OMDbScraper
from backend.services.scraper.imdb_fallback import CinemagoerFallback
from backend.services.scraper.combiner import UniversalScraperCombiner
import asyncio
import traceback

class ScraperChain:
    def __init__(self):
        self.tmdb = TMDBScraper()
        self.omdb = OMDbScraper()
        self.cinemagoer = CinemagoerFallback()
        self.combiner = UniversalScraperCombiner()

    async def scrape_movie(self, title: str, year: int = None) -> dict:
        """
        Main orchestration entrypoint for single-movie metadata.
        TMDB (primary) -> OMDb (enrich) -> Cinemagoer (fallback).
        """
        # 1. Search TMDB
        tmdb_base = await self.tmdb.search_movie(title, year)
        if not tmdb_base:
            return {}

        return await self.scrape_movie_by_id(tmdb_base.get("id"))

    async def scrape_movie_by_id(self, tmdb_id: int) -> dict:
        """Fetch and combine metadata for a movie by its TMDB ID."""
        # 2. Get full TMDB details
        tmdb_details = await self.tmdb.get_movie_details(str(tmdb_id))
        if not tmdb_details:
            return {}

        imdb_id = tmdb_details.get("imdb_id")
        
        # Extract Director
        crew = tmdb_details.get("credits", {}).get("crew", [])
        director = next((m["name"] for m in crew if m["job"] == "Director"), None)

        # Basic TMDB extracted payload setup
        tmdb_metadata = {
            "tmdb_id": str(tmdb_id),
            "imdb_id": imdb_id,
            "title": tmdb_details.get("title"),
            "sort_title": tmdb_details.get("title"),
            "original_title": tmdb_details.get("original_title"),
            "year": int(tmdb_details.get("release_date", "0")[:4]) if tmdb_details.get("release_date") else None,
            "plot": tmdb_details.get("overview"),
            "tagline": tmdb_details.get("tagline"),
            "genres": [g["name"] for g in tmdb_details.get("genres", [])],
            "runtime": tmdb_details.get("runtime"),
            "director": director,
            "tmdb_rating": tmdb_details.get("vote_average"),
            "poster_path": tmdb_details.get("poster_path"),
            "fanart_path": tmdb_details.get("backdrop_path"),
            "cast": tmdb_details.get("credits", {}).get("cast", []),
            "images": tmdb_details.get("images", {})
        }

        # 3. Enrich with IMDb rating/votes
        omdb_metadata = {}
        if imdb_id:
            imdb_enrichment = await self.omdb.get_imdb_data(imdb_id=imdb_id)
            
            # Fallback to Cinemagoer if OMDb failed/empty
            if not imdb_enrichment:
                try:
                    loop = asyncio.get_event_loop()
                    imdb_enrichment = await loop.run_in_executor(
                        None, 
                        self.cinemagoer.get_imdb_data, 
                        imdb_id
                    )
                except Exception as e:
                    print(f"Fallback crash: {e}")

            if imdb_enrichment:
                omdb_metadata = {
                    "imdb_rating": imdb_enrichment.get("imdb_rating"),
                    "imdb_votes": imdb_enrichment.get("imdb_votes"),
                    "metascore": imdb_enrichment.get("metascore"),
                    "content_rating": imdb_enrichment.get("content_rating")
                }

        # 4. Use Combiner to merge intelligently
        scraper_payloads = {
            "tmdb": tmdb_metadata,
            "omdb": omdb_metadata
        }
        
        return self.combiner.combine(scraper_payloads)

    async def scrape_tvshow(self, title: str, year: int = None) -> dict:
        """
        Orchestration for TV Show metadata:
        Returns {"series": dict, "seasons": {1: dict, 2: dict...}}
        """
        # 1. Search TMDB TV
        tmdb_base = await self.tmdb.search_tv(title, year)
        if not tmdb_base:
            return {}

        return await self.scrape_tvshow_by_id(tmdb_base.get("id"))

    async def scrape_tvshow_by_id(self, tmdb_id: int) -> dict:
        """Fetch and combine metadata for a TV show by its TMDB ID."""
        # 2. Get full TMDB TV details
        tmdb_details = await self.tmdb.get_tv_details(str(tmdb_id))
        if not tmdb_details:
            return {}

        imdb_id = tmdb_details.get("external_ids", {}).get("imdb_id")
        
        # Extract Director/Creator
        created_by = tmdb_details.get("created_by", [])
        director = created_by[0]["name"] if created_by else None

        # Basic TMDB extracted payload setup
        tmdb_metadata = {
            "tmdb_id": str(tmdb_id),
            "imdb_id": imdb_id,
            "title": tmdb_details.get("name"),
            "year": int(tmdb_details.get("first_air_date", "0")[:4]) if tmdb_details.get("first_air_date") else None,
            "plot": tmdb_details.get("overview"),
            "genres": [g["name"] for g in tmdb_details.get("genres", [])],
            "director": director,
            "runtime": tmdb_details.get("episode_run_time", [None])[0],
            "tmdb_rating": tmdb_details.get("vote_average"),
            "poster_path": tmdb_details.get("poster_path"),
            "fanart_path": tmdb_details.get("backdrop_path"),
            "cast": tmdb_details.get("credits", {}).get("cast", []),
            "images": tmdb_details.get("images", {})
        }

        # 3. Enrich with IMDb rating/content rating
        omdb_metadata = {}
        if imdb_id:
            imdb_enrichment = await self.omdb.get_imdb_data(imdb_id=imdb_id)
            if imdb_enrichment:
                omdb_metadata = {
                    "imdb_rating": imdb_enrichment.get("imdb_rating"),
                    "content_rating": imdb_enrichment.get("content_rating")
                }

        # 4. Use Combiner
        scraper_payloads = {
            "tmdb": tmdb_metadata,
            "omdb": omdb_metadata
        }
        
        final_series_meta = self.combiner.combine(scraper_payloads)
        
        # 5. Fetch Seasons
        seasons_meta = {}
        for season in tmdb_details.get("seasons", []):
            s_num = season.get("season_number")
            s_data = await self.tmdb.get_tv_season(str(tmdb_id), s_num)
            if s_data:
                seasons_meta[s_num] = s_data
                
        return {
            "series": final_series_meta,
            "seasons": seasons_meta
        }
