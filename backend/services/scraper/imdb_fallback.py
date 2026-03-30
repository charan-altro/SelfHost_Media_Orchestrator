from imdb import Cinemagoer
from typing import Optional

class CinemagoerFallback:
    def __init__(self):
        self.ia = Cinemagoer()

    def get_imdb_data(self, imdb_id: Optional[str] = None, title: Optional[str] = None) -> Optional[dict]:
        try:
            if imdb_id:
                # Strip the 'tt' prefix if it exists as cinemagoer expects pure digits
                clean_id = imdb_id.replace("tt", "")
                movie = self.ia.get_movie(clean_id)
            elif title:
                results = self.ia.search_movie(title)
                if not results:
                    return None
                movie = results[0]
                self.ia.update(movie)
            else:
                return None
                
            return {
                "imdb_rating": movie.get('rating'),
                "imdb_votes": movie.get('votes'),
                "content_rating": movie.get('certificates', [''])[0] if movie.get('certificates') else None,
            }
        except Exception as e:
            print(f"[Cinemagoer Fallback Error]: {e}")
            return None
