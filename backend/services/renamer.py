import os
import shutil
import re
from pathlib import Path

class RenamerService:
    def __init__(self, templates: dict):
        self.movie_folder_template = templates.get("movie_folder", "${title} (${year})")
        self.movie_file_template = templates.get("movie_file", "${title} (${year}) [${resolution} ${videoCodec} ${audioCodec}]")

    def _sanitize(self, name: str) -> str:
        """Removes illegal OS characters from string."""
        if not name: return ""
        return re.sub(r'[\\/*?:"<>|]', "", str(name)).strip()

    def generate_movie_paths(self, metadata: dict, original_file_path: str) -> tuple[str, str]:
        """Returns the new folder name and new file name based on templates and metadata."""
        variables = {
            "${title}": self._sanitize(metadata.get("title", "Unknown Title")),
            "${year}": str(metadata.get("year", "")) if metadata.get("year") else "",
            "${resolution}": metadata.get("resolution", ""),
            "${videoCodec}": metadata.get("video_codec", ""),
            "${audioCodec}": metadata.get("audio_codec", ""),
            "${audioChannels}": metadata.get("audio_channels", ""),
        }
        
        folder_name = self.movie_folder_template
        file_name = self.movie_file_template
        
        for key, val in variables.items():
            # If val is missing, we might want to clean up surrounding brackets/spaces. Simple replace for now.
            if not val:
                # remove the placeholder and try to clean up orphaned brackets if needed
                folder_name = folder_name.replace(key, "")
                file_name = file_name.replace(key, "")
            else:
                folder_name = folder_name.replace(key, val)
                file_name = file_name.replace(key, val)
                
        # Clean up double spaces or empty brackets
        # Replace [ ] with any amount of whitespace inside with nothing
        folder_name = re.sub(r'\[\s*\]', '', folder_name)
        folder_name = re.sub(r'\(\s*\)', '', folder_name)
        folder_name = re.sub(r'\s+', ' ', folder_name).strip()
        
        file_name = re.sub(r'\[\s*\]', '', file_name)
        file_name = re.sub(r'\(\s*\)', '', file_name)
        file_name = re.sub(r'\s+', ' ', file_name).strip()
        
        ext = Path(original_file_path).suffix
        file_name = f"{file_name}{ext}"
        
        return folder_name, file_name

    def rename_movie(self, metadata: dict, current_file_path: str, root_library_path: str) -> str:
        """Moves and renames a movie file and its companion files (NFO, art) into the proper folder structure."""
        if not os.path.exists(current_file_path):
            raise FileNotFoundError(f"File not found: {current_file_path}")
            
        folder_name, file_name = self.generate_movie_paths(metadata, current_file_path)
        
        dest_folder = os.path.join(root_library_path, folder_name)
        dest_file = os.path.join(dest_folder, file_name)
        
        if current_file_path == dest_file:
            return dest_file # Already correctly named
            
        os.makedirs(dest_folder, exist_ok=True)
        
        old_dir = os.path.dirname(current_file_path)
        old_stem = Path(current_file_path).stem
        new_stem = Path(dest_file).stem
        
        # Move the main movie file
        shutil.move(current_file_path, dest_file)
        
        # Move companion files (NFO, images, etc.) that match the old stem
        if os.path.isdir(old_dir):
            for companion in os.listdir(old_dir):
                c_path = os.path.join(old_dir, companion)
                if not os.path.isfile(c_path): continue
                if c_path == dest_file or c_path == current_file_path: continue
                
                # If it starts with the old movie filename stem (e.g. "Movie (2021)-poster.jpg")
                if companion.startswith(old_stem):
                    new_companion_name = companion.replace(old_stem, new_stem, 1)
                    shutil.move(c_path, os.path.join(dest_folder, new_companion_name))
        
        # Clean up old directory if empty
        try:
            if old_dir != root_library_path and not os.listdir(old_dir):
                os.rmdir(old_dir)
        except OSError:
            pass
            
        return dest_file
