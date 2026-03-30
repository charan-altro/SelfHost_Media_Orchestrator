from pymediainfo import MediaInfo
import os

def extract_media_info(file_path: str) -> dict:
    """Wrapper for MediaInfo to extract core technical specs."""
    if not os.path.exists(file_path):
        return {}
    
    data = {
        "resolution": None,
        "hdr_type": None,
        "video_codec": None,
        "audio_codec": None,
        "audio_channels": None,
        "size_bytes": os.path.getsize(file_path)
    }
    
    try:
        media_info = MediaInfo.parse(file_path)
        for track in media_info.tracks:
            if track.track_type == "Video":
                width = track.width
                if width:
                    if width >= 3800: data["resolution"] = "4K"
                    elif width >= 1900: data["resolution"] = "1080p"
                    elif width >= 1200: data["resolution"] = "720p"
                    else: data["resolution"] = "SD"
                data["video_codec"] = track.format
                data["hdr_type"] = track.hdr_format
                
            elif track.track_type == "Audio":
                # Priority: take the first audio track specs
                if not data["audio_codec"]:
                    data["audio_codec"] = track.format
                    channels = track.channel_s
                    if channels:
                        if channels == 8: data["audio_channels"] = "7.1"
                        elif channels == 6: data["audio_channels"] = "5.1"
                        elif channels == 2: data["audio_channels"] = "2.0"
                        else: data["audio_channels"] = str(channels)
    except Exception as e:
        # Graceful fallback if pymediainfo fails (e.g. missing binary)
        print(f"[MediaInfo] Failed to read {file_path}: {e}")
        
    return data
