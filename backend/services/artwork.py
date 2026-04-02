import os
import httpx
from pathlib import Path

TMDB_IMAGE_BASE = "https://image.tmdb.org/t/p/original"

class ArtworkDownloader:
    """
    Downloads artwork for movies and TV shows from API providers.
    """
    def __init__(self):
        # We can implement a rate limiter or shared client here in the future
        pass

    async def download_movie_artwork(self, metadata: dict, video_file_path: str):
        """
        Downloads the poster and fanart for a movie.
        Saves them in the same directory as the video file.
        """
        target_dir = os.path.dirname(video_file_path)
        base_name = Path(video_file_path).stem
        
        poster_path = metadata.get("poster_path")
        fanart_path = metadata.get("fanart_path")

        # Async download helper using a shared client pool
        async def _download_img(client, url, dest_path):
            if os.path.exists(dest_path):
                return # Already downloaded
                
            try:
                resp = await client.get(url, follow_redirects=True)
                if resp.status_code == 200:
                    with open(dest_path, "wb") as f:
                        f.write(resp.content)
            except PermissionError:
                # Silently fail for individual images if the folder is locked
                pass
            except Exception as e:
                # Log other network/io errors briefly
                print(f"[Artwork] Failed {Path(dest_path).name}: {e}")

        import asyncio
        tasks = []
        
        async with httpx.AsyncClient(timeout=30.0, limits=httpx.Limits(max_connections=20)) as client:
            # 1. Poster
            if poster_path:
                poster_url = f"{TMDB_IMAGE_BASE}{poster_path}"
                poster_dest = os.path.join(target_dir, f"{base_name}-poster.jpg")
                tasks.append(_download_img(client, poster_url, poster_dest))

            # 2. Fanart (Backdrop)
            if fanart_path:
                fanart_url = f"{TMDB_IMAGE_BASE}{fanart_path}"
                fanart_dest = os.path.join(target_dir, f"{base_name}-fanart.jpg")
                tasks.append(_download_img(client, fanart_url, fanart_dest))
                
            # 3. Logos
            images = metadata.get("images", {})
            logos = images.get("logos", [])
            if logos:
                # Try English first, then fallback
                en_logos = [l for l in logos if l.get("iso_639_1") == "en"]
                best_logo = en_logos[0] if en_logos else logos[0]
                if best_logo.get("file_path"):
                    logo_url = f"{TMDB_IMAGE_BASE}{best_logo['file_path']}"
                    logo_dest = os.path.join(target_dir, f"{base_name}-logo.png")
                    tasks.append(_download_img(client, logo_url, logo_dest))
                
            # 4. Extrafanart
            backdrops = images.get("backdrops", [])
            if len(backdrops) > 1:
                # Take up to 5 extra backdrops, skipping the primary fanart
                for idx, bg in enumerate(backdrops[1:6], 1):
                    if bg.get("file_path"):
                        bg_url = f"{TMDB_IMAGE_BASE}{bg['file_path']}"
                        bg_dest = os.path.join(target_dir, f"{base_name}-fanart{idx}.jpg")
                        tasks.append(_download_img(client, bg_url, bg_dest))
                        
            # 5. Actors
            cast = metadata.get("cast", [])
            if cast:
                # Limit to top 15 actors to save API bandwidth / disk space
                for actor in cast[:15]:
                    profile_path = actor.get("profile_path")
                    name = actor.get("name")
                    if profile_path and name:
                        safe_name = name.replace(" ", "_").replace("/", "-")
                        actor_url = f"{TMDB_IMAGE_BASE}{profile_path}"
                        actor_dest = os.path.join(target_dir, f"{base_name}-{safe_name}.jpg")
                        tasks.append(_download_img(client, actor_url, actor_dest))

            if tasks:
                await asyncio.gather(*tasks)
