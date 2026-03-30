from typing import Dict, Any

# Map specific metadata fields to their preferred scraper source.
# In M2, this dictionary can be loaded from the user's Settings DB.
DEFAULT_FIELD_SOURCES = {
    "tmdb_id": "tmdb",
    "title": "tmdb",
    "sort_title": "tmdb",
    "original_title": "tmdb",
    "year": "tmdb",
    "plot": "tmdb",
    "tagline": "tmdb",
    "genres": "tmdb",
    "runtime": "tmdb",
    "tmdb_rating": "tmdb",
    "poster_path": "tmdb",
    "fanart_path": "tmdb",
    
    # We prefer OMDB for IMDb specific ratings and metrics
    "imdb_id": "tmdb", # We still rely on TMDB to provide the primary ID linkage
    "imdb_rating": "omdb",
    "imdb_votes": "omdb",
    "metascore": "omdb",
    "content_rating": "omdb"
}

class UniversalScraperCombiner:
    """
    Combines metadata dictionaries from multiple API providers.
    Uses a priority mapping template (field -> preferred scraper module).
    If the preferred scraper doesn't have the field, it automatically falls back
    to any other scraper that provided it.
    """
    def __init__(self, field_sources: Dict[str, str] = None):
        self.field_sources = field_sources or DEFAULT_FIELD_SOURCES

    def combine(self, scraper_results: Dict[str, Dict[str, Any]]) -> Dict[str, Any]:
        """
        Takes a dict of scraper names mapped to their JSON results.
        Example: {"tmdb": {"title": "The Matrix"}, "omdb": {"imdb_rating": 8.7}}
        Returns the finalized unified metadata dict.
        """
        combined = {}
        
        # Identify superset of all fields provided by any scraper
        all_fields = set()
        for src, data in scraper_results.items():
            if data:
                all_fields.update(data.keys())

        # For every discovered field, resolve its final value
        for field in all_fields:
            preferred_source = self.field_sources.get(field)
            
            # Primary logic: Use preferred source if it exists and value is not None
            if preferred_source and preferred_source in scraper_results and scraper_results[preferred_source].get(field) is not None:
                combined[field] = scraper_results[preferred_source][field]
            else:
                # Fallback logic: iterate through all other sources and take the first non-null value
                for src in scraper_results:
                    if scraper_results[src] and scraper_results[src].get(field) is not None:
                        combined[field] = scraper_results[src][field]
                        break

        return combined
