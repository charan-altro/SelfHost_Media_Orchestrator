import xml.etree.ElementTree as ET
from xml.dom import minidom
import os

class NFOGenerator:
    @staticmethod
    def _create_text_element(parent, tag, text):
        if text:
            elem = ET.SubElement(parent, tag)
            elem.text = str(text)

    def generate_movie_nfo(self, metadata: dict, file_path: str) -> str:
        """Generates a Kodi-compatible movie.nfo."""
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
        with open(nfo_path, "w", encoding="utf-8") as f:
            f.write(xmlstr)
            
        return nfo_path

    def generate_tvshow_nfo(self, metadata: dict, folder_path: str) -> str:
        """Generates a tvshow.nfo in the show folder."""
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
        with open(nfo_path, "w", encoding="utf-8") as f:
            f.write(xmlstr)
        return nfo_path

    def generate_episode_nfo(self, ep_metadata: dict, series_metadata: dict, file_path: str) -> str:
        """Generates a Kodi-compatible episode.nfo."""
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
        with open(nfo_path, "w", encoding="utf-8") as f:
            f.write(xmlstr)
        return nfo_path
