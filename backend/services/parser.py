import re
from dataclasses import dataclass
from typing import Optional, List

@dataclass
class ParsedMedia:
    title: str
    year: Optional[int] = None
    season: Optional[int] = None
    episode: Optional[int] = None
    extra_tags: List[str] = None
    is_tv: bool = False

# Regexes based on plan specifications
MOVIE_RE = re.compile(r'^(.*?)(?:[. (\[]+((?:19|20)\d{2}))[. )\]]*(.*)$', re.IGNORECASE)
EPISODE_RE = re.compile(r'^(.*?)[\. _-]*S(\d{2})E(\d{2})[\. _-]?(.*)$', re.IGNORECASE)

def parse_filename(filename: str) -> ParsedMedia:
    """Extracts title, year, season, episode, and tags from media filenames."""
    # Cleanup extension
    name = filename.rsplit('.', 1)[0] if '.' in filename else filename
    
    # Try episode first
    ep_match = EPISODE_RE.match(name)
    if ep_match:
        title, season, episode, tags = ep_match.groups()
        return ParsedMedia(
            title=title.replace('.', ' ').strip(),
            season=int(season),
            episode=int(episode),
            extra_tags=[t for t in re.split(r'[\. \-\[\]()]+', tags) if t],
            is_tv=True
        )
        
    # Try movie
    mov_match = MOVIE_RE.match(name)
    if mov_match:
        title, year, tags = mov_match.groups()
        return ParsedMedia(
            title=title.replace('.', ' ').strip(),
            year=int(year),
            extra_tags=[t for t in re.split(r'[\. \-\[\]()]+', tags) if t],
            is_tv=False
        )
        
    # Fallback to plain name
    return ParsedMedia(title=name.replace('.', ' ').strip())
