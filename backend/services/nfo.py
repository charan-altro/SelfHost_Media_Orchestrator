import xml.etree.ElementTree as ET
from xml.dom import minidom
import os
import stat

class NFOGenerator:
    @staticmethod
    def _create_text_element(parent, tag, text):
        if text:
            elem = ET.SubElement(parent, tag)
            elem.text = str(text)

    def _write_nfo_to_disk(self, nfo_path: str, xmlstr: str) -> bool:
        """
        Robustly writes an NFO file to disk. 
        Attempts to handle permission issues common on host-mounted volumes.
        Uses a temp file to ensure the original isn't lost if writing fails.
        """
        
        # 1. Ensure directory exists
        os.makedirs(os.path.dirname(nfo_path), exist_ok=True)
        
        temp_path = nfo_path + ".tmp"
        
        # 2. Write to temp file
        try:
            with open(temp_path, "w", encoding="utf-8") as f:
                f.write(xmlstr)
        except PermissionError:
            # If we can't even write a temp file, the directory is likely read-only
            print(f"[NFO] Permission denied in directory: {os.path.dirname(nfo_path)}")
            return False
        except Exception as e:
            print(f"[NFO] Error writing temp NFO {temp_path}: {e}")
            return False

        # 3. Replace the original file
        try:
            if os.path.exists(nfo_path):
                # Try to make original writable just in case it's marked read-only
                try:
                    os.chmod(nfo_path, stat.S_IWRITE | stat.S_IREAD)
                except:
                    pass
            
            # Use os.replace for atomic-ish replacement
            os.replace(temp_path, nfo_path)
            return True
        except PermissionError:
            # If replace fails, try the delete-and-move fallback (more aggressive)
            try:
                os.remove(nfo_path)
                os.rename(temp_path, nfo_path)
                return True
            except Exception as e:
                print(f"[NFO] Permission denied replacing {nfo_path}: {e}")
                if os.path.exists(temp_path):
                    try: os.remove(temp_path)
                    except: pass
                return False
        except Exception as e:
            print(f"[NFO] Error replacing {nfo_path}: {e}")
            if os.path.exists(temp_path):
                try: os.remove(temp_path)
                except: pass
            return False

    def generate_movie_nfo(self, metadata: dict, file_path: str) -> tuple[str, bool]:
        """Generates a Kodi-compatible movie.nfo. Returns (path, success)."""
        root = ET.Element('movie')
        
        self._create_text_element(root, 'title', metadata.get("title"))
        self._create_text_element(root, 'originaltitle', metadata.get("original_title"))
        self._create_text_element(root, 'sorttitle', metadata.get("sort_title"))
        self._create_text_element(root, 'year', metadata.get("year"))
        self._create_text_element(root, 'plot', metadata.get("plot"))
        self._create_text_element(root, 'tagline', metadata.get("tagline"))
        self._create_text_element(root, 'runtime', metadata.get("runtime"))
        self._create_text_element(root, 'mpaa', metadata.get("content_rating"))
        
        # IDs
        if metadata.get("tmdb_id"):
            self._create_text_element(root, 'tmdbid', metadata.get("tmdb_id"))
            uniqueid = ET.SubElement(root, 'uniqueid', type="tmdb")
            uniqueid.text = str(metadata.get("tmdb_id"))
            if not metadata.get("imdb_id"):
                uniqueid.set('default', 'true')
                
        if metadata.get("imdb_id"):
            self._create_text_element(root, 'imdbid', metadata.get("imdb_id"))
            uniqueid = ET.SubElement(root, 'uniqueid', type="imdb", default="true")
            uniqueid.text = metadata.get("imdb_id")

        # Ratings
        if metadata.get("imdb_rating"):
            rating = ET.SubElement(root, 'rating', name="imdb", max="10")
            ET.SubElement(rating, 'value').text = str(metadata.get("imdb_rating"))
            ET.SubElement(rating, 'votes').text = str(metadata.get("imdb_votes", 0))

        if metadata.get("tmdb_rating"):
            rating = ET.SubElement(root, 'rating', name="tmdb", max="10")
            ET.SubElement(rating, 'value').text = str(metadata.get("tmdb_rating"))

        # Genres
        for genre in metadata.get("genres", []):
            self._create_text_element(root, 'genre', genre)

        # Cast
        for actor in metadata.get("cast", []):
            actor_elem = ET.SubElement(root, 'actor')
            self._create_text_element(actor_elem, 'name', actor.get("name"))
            self._create_text_element(actor_elem, 'role', actor.get("character") or actor.get("role"))
            thumb_path = actor.get('profile_path') or actor.get('thumb')
            if thumb_path and not thumb_path.startswith('http'):
                thumb_path = f"https://image.tmdb.org/t/p/original{thumb_path}"
            self._create_text_element(actor_elem, 'thumb', thumb_path)

        # File Info section
        fileinfo = ET.SubElement(root, 'fileinfo')
        streamdetails = ET.SubElement(fileinfo, 'streamdetails')
        
        if metadata.get("resolution") or metadata.get("video_codec"):
            video = ET.SubElement(streamdetails, 'video')
            self._create_text_element(video, 'codec', metadata.get("video_codec"))
            self._create_text_element(video, 'width', "3840" if metadata.get("resolution") == "4K" else "1920") # approximation if exact not kept
            
        if metadata.get("audio_codec"):
            audio = ET.SubElement(streamdetails, 'audio')
            self._create_text_element(audio, 'codec', metadata.get("audio_codec"))
            self._create_text_element(audio, 'channels', metadata.get("audio_channels"))
            
        # Write to disk
        xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
        # Remove standard XML declaration for better Kodi compatibility
        xmlstr = '\n'.join(xmlstr.split('\n')[1:])
        
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        nfo_path = os.path.join(os.path.dirname(file_path), f"{base_name}.nfo")
        success = self._write_nfo_to_disk(nfo_path, xmlstr)
            
        return nfo_path, success

    def generate_tvshow_nfo(self, metadata: dict, folder_path: str) -> tuple[str, bool]:
        """Generates a tvshow.nfo in the show folder. Returns (path, success)."""
        root = ET.Element('tvshow')
        
        self._create_text_element(root, 'title', metadata.get("title"))
        self._create_text_element(root, 'year', metadata.get("year"))
        self._create_text_element(root, 'plot', metadata.get("plot"))
        self._create_text_element(root, 'mpaa', metadata.get("content_rating"))
        self._create_text_element(root, 'runtime', metadata.get("runtime"))
        
        if metadata.get("tmdb_id"):
            self._create_text_element(root, 'tmdbid', metadata.get("tmdb_id"))
            uniqueid = ET.SubElement(root, 'uniqueid', type="tmdb")
            uniqueid.text = str(metadata.get("tmdb_id"))
            
        if metadata.get("imdb_id"):
            self._create_text_element(root, 'imdbid', metadata.get("imdb_id"))
            uniqueid = ET.SubElement(root, 'uniqueid', type="imdb", default="true")
            uniqueid.text = metadata.get("imdb_id")

        for genre in metadata.get("genres", []):
            self._create_text_element(root, 'genre', genre)

        # Cast
        for actor in metadata.get("cast", []):
            actor_elem = ET.SubElement(root, 'actor')
            self._create_text_element(actor_elem, 'name', actor.get("name"))
            self._create_text_element(actor_elem, 'role', actor.get("character"))
            self._create_text_element(actor_elem, 'thumb', f"https://image.tmdb.org/t/p/original{actor.get('profile_path')}" if actor.get('profile_path') else None)

        xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
        xmlstr = '\n'.join(xmlstr.split('\n')[1:])
        
        nfo_path = os.path.join(folder_path, "tvshow.nfo")
        success = self._write_nfo_to_disk(nfo_path, xmlstr)
        return nfo_path, success

    def generate_episode_nfo(self, ep_metadata: dict, series_metadata: dict, file_path: str) -> tuple[str, bool]:
        """Generates a Kodi-compatible episode.nfo. Returns (path, success)."""
        root = ET.Element('episodedetails')
        
        self._create_text_element(root, 'title', ep_metadata.get("name"))
        self._create_text_element(root, 'season', ep_metadata.get("season_number"))
        self._create_text_element(root, 'episode', ep_metadata.get("episode_number"))
        self._create_text_element(root, 'plot', ep_metadata.get("overview"))
        self._create_text_element(root, 'aired', ep_metadata.get("air_date"))
        
        # Ratings
        if ep_metadata.get("vote_average"):
            rating = ET.SubElement(root, 'rating', name="tmdb", max="10")
            ET.SubElement(rating, 'value').text = str(ep_metadata.get("vote_average"))

        xmlstr = minidom.parseString(ET.tostring(root)).toprettyxml(indent="  ")
        xmlstr = '\n'.join(xmlstr.split('\n')[1:])
        
        base_name = os.path.splitext(os.path.basename(file_path))[0]
        nfo_path = os.path.join(os.path.dirname(file_path), f"{base_name}.nfo")
        success = self._write_nfo_to_disk(nfo_path, xmlstr)
        return nfo_path, success
