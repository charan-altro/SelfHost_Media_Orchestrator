"""
Database export service.
Supports CSV and styled HTML exports of the movie library.
"""
import csv
import io
from datetime import datetime
from sqlalchemy.orm import Session
from backend.models.media import Movie

HTML_TEMPLATE = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>SelfHost Media Orchestrator Library Export</title>
<style>
  * {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body {{ font-family: 'Segoe UI', Arial, sans-serif; background: #1a1a2e; color: #e0e0e0; padding: 2rem; }}
  h1 {{ font-size: 2rem; font-weight: 700; color: #6c63ff; margin-bottom: 0.25rem; }}
  .meta {{ color: #888; margin-bottom: 2rem; font-size: 0.9rem; }}
  table {{ width: 100%; border-collapse: collapse; background: #16213e; border-radius: 12px; overflow: hidden; box-shadow: 0 4px 24px rgba(0,0,0,0.4); }}
  thead {{ background: #6c63ff; color: #fff; }}
  th, td {{ padding: 0.75rem 1rem; text-align: left; border-bottom: 1px solid #0f3460; }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td {{ background: #0f3460; }}
  .badge {{ padding: 0.2rem 0.6rem; border-radius: 999px; font-size: 0.75rem; font-weight: 600; }}
  .matched {{ background: #155724; color: #d4edda; }}
  .unmatched {{ background: #721c24; color: #f8d7da; }}
</style>
</head>
<body>
<h1>🎬 SelfHost Media Orchestrator Library</h1>
<p class="meta">Exported {count} movies &nbsp;•&nbsp; {date}</p>
<table>
<thead><tr>
  <th>#</th><th>Title</th><th>Year</th><th>IMDB Rating</th><th>TMDB Rating</th><th>Status</th><th>File</th>
</tr></thead>
<tbody>
{rows}
</tbody>
</table>
</body>
</html>"""

ROW_TEMPLATE = """<tr>
  <td>{idx}</td>
  <td><strong>{title}</strong></td>
  <td>{year}</td>
  <td>{imdb}</td>
  <td>{tmdb}</td>
  <td><span class="badge {status_cls}">{status}</span></td>
  <td><small>{file}</small></td>
</tr>"""


import json
from backend.models.media import Movie, Library, TVShow

def backup_library_to_json(db: Session, library_id: int) -> str:
    """Export all metadata for a specific library to a JSON string."""
    lib = db.query(Library).filter(Library.id == library_id).first()
    if not lib:
        return json.dumps({"error": "Library not found"})

    data = {
        "library": {
            "name": lib.name,
            "path": lib.path,
            "type": lib.type,
            "language": lib.language
        },
        "movies": [],
        "tv_shows": []
    }

    if lib.type == 'movie':
        movies = db.query(Movie).filter(Movie.library_id == library_id).all()
        for m in movies:
            m_dict = {c.name: getattr(m, c.name) for c in m.__table__.columns}
            m_dict["files"] = [{c.name: getattr(f, c.name) for f in f.__table__.columns} for f in m.files]
            data["movies"].append(m_dict)
    else:
        shows = db.query(TVShow).filter(TVShow.library_id == library_id).all()
        for s in shows:
            s_dict = {c.name: getattr(s, c.name) for c in s.__table__.columns}
            s_dict["seasons"] = []
            for season in s.seasons:
                season_dict = {c.name: getattr(season, c.name) for c in season.__table__.columns}
                season_dict["episodes"] = [{c.name: getattr(ep, c.name) for ep in ep.__table__.columns} for ep in season.episodes]
                s_dict["seasons"].append(season_dict)
            data["tv_shows"].append(s_dict)

    return json.dumps(data, indent=2, default=str)

def export_csv(db: Session) -> str:
    """Return library as CSV string."""
    movies = db.query(Movie).order_by(Movie.title).all()
    output = io.StringIO()
    writer = csv.writer(output)
    writer.writerow(["ID", "Title", "Year", "Status", "IMDB ID", "TMDB ID",
                     "IMDB Rating", "TMDB Rating", "Genres", "Plot", "File Path"])
    for m in movies:
        file_path = m.files[0].file_path if m.files else ""
        genres = ", ".join(m.genres) if isinstance(m.genres, list) else (m.genres or "")
        writer.writerow([
            m.id, m.title, m.year or "", m.status,
            m.imdb_id or "", m.tmdb_id or "",
            m.imdb_rating or "", m.tmdb_rating or "",
            genres, (m.plot or "").replace("\n", " "), file_path,
        ])
    return output.getvalue()


def export_html(db: Session) -> str:
    """Return library as styled HTML string."""
    movies = db.query(Movie).order_by(Movie.title).all()
    rows_html = ""
    for idx, m in enumerate(movies, 1):
        file_path = m.files[0].file_path if m.files else "—"
        rows_html += ROW_TEMPLATE.format(
            idx=idx,
            title=m.title,
            year=m.year or "—",
            imdb=m.imdb_rating or "—",
            tmdb=m.tmdb_rating or "—",
            status=m.status,
            status_cls="matched" if m.status == "matched" else "unmatched",
            file=file_path,
        )
    return HTML_TEMPLATE.format(
        count=len(movies),
        date=datetime.utcnow().strftime("%Y-%m-%d %H:%M UTC"),
        rows=rows_html,
    )
