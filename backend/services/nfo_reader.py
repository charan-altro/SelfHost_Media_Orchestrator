import os
import xml.etree.ElementTree as ET
from pathlib import Path

class NFOReader:
    @staticmethod
    def parse_movie_nfo(video_file_path: str) -> dict:
        """
        Looks for an NFO file next to the video file and parses metadata.
        Also detects local images (poster.jpg, backdrop.jpg).
        """
        target_dir = os.path.dirname(video_file_path)
        base_name = Path(video_file_path).stem
        
        nfo_paths = [
            os.path.join(target_dir, f"{base_name}.nfo"),
            os.path.join(target_dir, "movie.nfo")
        ]
        
        nfo_file = None
        for path in nfo_paths:
            if os.path.exists(path):
                nfo_file = path
                break
                
        # Initialize metadata with local image detection
        metadata = {
            "poster_path": None,
            "fanart_path": None,
            "cast": []
        }
        
        # 1. Local Image Detection (Identity)
        poster_candidates = ["poster.jpg", "poster.png", f"{base_name}-poster.jpg", "folder.jpg"]
        fanart_candidates = ["fanart.jpg", "backdrop.jpg", f"{base_name}-fanart.jpg"]
        
        for cand in poster_candidates:
            full_cand = os.path.join(target_dir, cand)
            if os.path.exists(full_cand):
                metadata["poster_path"] = f"local://{full_cand}"
                break
        
        for cand in fanart_candidates:
            full_cand = os.path.join(target_dir, cand)
            if os.path.exists(full_cand):
                metadata["fanart_path"] = f"local://{full_cand}"
                break

        if not nfo_file and not metadata["poster_path"]:
            return None
            
        if nfo_file:
            try:
                tree = ET.parse(nfo_file)
                root = tree.getroot()
                if root.tag == 'movie':
                    for el in root:
                        if el.tag == 'title' and el.text: metadata['title'] = el.text
                        elif el.tag == 'sorttitle' and el.text: metadata['sort_title'] = el.text
                        elif el.tag == 'tmdbid' and el.text: metadata['tmdb_id'] = el.text
                        elif el.tag == 'imdbid' and el.text: metadata['imdb_id'] = el.text
                        elif el.tag == 'uniqueid' and el.text:
                            uid_type = el.get("type", "").lower()
                            if uid_type == "tmdb": metadata['tmdb_id'] = el.text
                            elif uid_type == "imdb": metadata['imdb_id'] = el.text
                        elif el.tag == 'year' and el.text:
                            try: metadata['year'] = int(el.text)
                            except: pass
                        elif el.tag == 'plot' and el.text: metadata['plot'] = el.text
                        elif el.tag == 'runtime' and el.text:
                            try: metadata['runtime'] = int(el.text)
                            except: pass
                        elif el.tag == 'actor':
                            actor = {"name": "", "role": "", "thumb": ""}
                            for sub in el:
                                if sub.tag == 'name': actor['name'] = sub.text
                                elif sub.tag == 'role': actor['role'] = sub.text
                                elif sub.tag == 'thumb': actor['thumb'] = sub.text
                            metadata['cast'].append(actor)
            except Exception as e:
                print(f"Failed to parse NFO {nfo_file}: {e}")
                        
        return metadata

    @staticmethod
    def parse_tvshow_nfo(video_file_path: str) -> dict:
        """
        Looks for a 'tvshow.nfo' file and local images.
        """
        current_dir = os.path.dirname(video_file_path)
        # Handle "Season X" folders
        if "season" in os.path.basename(current_dir).lower():
            current_dir = os.path.dirname(current_dir)
            
        nfo_file = os.path.join(current_dir, "tvshow.nfo")
        if not os.path.exists(nfo_file):
            nfo_file = None
            
        metadata = {
            "poster_path": None,
            "fanart_path": None,
            "cast": []
        }
        
        # Local images
        if os.path.exists(os.path.join(current_dir, "poster.jpg")):
            metadata["poster_path"] = f"local://{os.path.join(current_dir, 'poster.jpg')}"
        if os.path.exists(os.path.join(current_dir, "fanart.jpg")):
            metadata["fanart_path"] = f"local://{os.path.join(current_dir, 'fanart.jpg')}"
        elif os.path.exists(os.path.join(current_dir, "backdrop.jpg")):
            metadata["fanart_path"] = f"local://{os.path.join(current_dir, 'backdrop.jpg')}"

        if nfo_file:
            try:
                tree = ET.parse(nfo_file)
                root = tree.getroot()
                if root.tag == 'tvshow':
                    for el in root:
                        if el.tag == 'title' and el.text: metadata['title'] = el.text
                        elif el.tag == 'tmdbid' and el.text: metadata['tmdb_id'] = el.text
                        elif el.tag == 'imdbid' and el.text: metadata['imdb_id'] = el.text
                        elif el.tag == 'uniqueid' and el.text:
                            uid_type = el.get("type", "").lower()
                            if uid_type == "tmdb": metadata['tmdb_id'] = el.text
                            elif uid_type == "imdb": metadata['imdb_id'] = el.text
                        elif el.tag == 'plot' and el.text: metadata['plot'] = el.text
                        elif el.tag == 'year' and el.text:
                            try: metadata['year'] = int(el.text)
                            except: pass
                        elif el.tag == 'actor':
                            actor = {"name": "", "role": "", "thumb": ""}
                            for sub in el:
                                if sub.tag == 'name': actor['name'] = sub.text
                                elif sub.tag == 'role': actor['role'] = sub.text
                                elif sub.tag == 'thumb': actor['thumb'] = sub.text
                            metadata['cast'].append(actor)
            except Exception as e:
                print(f"Failed to parse NFO {nfo_file}: {e}")
                        
        return metadata

