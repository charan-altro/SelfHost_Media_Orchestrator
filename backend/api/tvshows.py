from fastapi import APIRouter, Depends, BackgroundTasks, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy import asc
from pydantic import BaseModel
from backend.core.db import get_db
from backend.models.media import TVShow, Season, Episode, Library

router = APIRouter(prefix="/api/tvshows", tags=["TV Shows"])

class TVShowUpdate(BaseModel):
    title: str | None = None
    year: int | None = None
    plot: str | None = None
    tmdb_rating: float | None = None
    imdb_rating: float | None = None
    runtime: int | None = None
    director: str | None = None
    genres: list[str] | None = None
    content_rating: str | None = None

@router.patch("/{show_id}")
def update_tvshow(show_id: int, update: TVShowUpdate, db: Session = Depends(get_db)):
    show = db.query(TVShow).filter(TVShow.id == show_id).first()
    if not show:
        raise HTTPException(status_code=404, detail="TV Show not found")
    
    update_data = update.model_dump(exclude_none=True)
    for key, value in update_data.items():
        setattr(show, key, value)
    
    db.commit()
    db.refresh(show)
    return show

@router.get("/")
def list_tvshows(db: Session = Depends(get_db), limit: int = 10000, offset: int = 0):
    shows = db.query(TVShow).offset(offset).limit(limit).all()
    # Simple serialization for MVP
    result = []
    for s in shows:
        s_dict = {c.name: getattr(s, c.name) for c in s.__table__.columns}
        # Include episode counts or basic stats if needed
        result.append(s_dict)
    return result

@router.get("/{show_id}")
def get_tvshow(show_id: int, db: Session = Depends(get_db)):
    show = db.query(TVShow).filter(TVShow.id == show_id).first()
    if not show:
        raise HTTPException(status_code=404, detail="TV Show not found")
        
    s_dict = {c.name: getattr(show, c.name) for c in show.__table__.columns}
    
    # Serialize seasons and episodes
    seasons_data = []
    for season in sorted(show.seasons, key=lambda x: x.season_number):
        season_dict = {c.name: getattr(season, c.name) for c in season.__table__.columns}
        episodes_data = []
        for ep in sorted(season.episodes, key=lambda x: x.episode_number):
            ep_dict = {c.name: getattr(ep, c.name) for c in ep.__table__.columns}
            episodes_data.append(ep_dict)
        season_dict["episodes"] = episodes_data
        seasons_data.append(season_dict)
        
    s_dict["seasons"] = seasons_data
    return s_dict

@router.get("/search/external")
async def search_external_tv(query: str, year: int = None):
    from backend.services.scraper.chain import ScraperChain
    scraper = ScraperChain()
    results = await scraper.tmdb.search_tv_shows(query, year)
    return results

async def _background_scrape_tvshow(show_id: int, tmdb_id: int = None):
    from backend.core.db import SessionLocal
    from backend.services.scraper.chain import ScraperChain
    from backend.services.artwork import ArtworkDownloader
    from backend.core.task_manager import create_task, update_task
    from backend.services.nfo import NFOGenerator
    db = SessionLocal()
    task_id = None
    try:
        show = db.query(TVShow).filter(TVShow.id == show_id).first()
        if not show:
            return
            
        task_id = create_task(f"Scraping TV Show: {show.title}", total=1)
        update_task(task_id, status="running", progress=0, message="Searching TMDB...")
        
        scraper = ScraperChain()
        if tmdb_id:
            metadata = await scraper.scrape_tvshow_by_id(tmdb_id)
        else:
            metadata = await scraper.scrape_tvshow(show.title, show.year)
        
        if not metadata or not metadata.get("series"):
            update_task(task_id, status="error", message="No metadata found")
            return
            
        series_meta = metadata["series"]
        seasons_meta = metadata.get("seasons", {})
        
        update_task(task_id, message="Updating series & episodes...")
        # Update Series DB
        for key, val in series_meta.items():
            if hasattr(show, key) and val is not None:
                setattr(show, key, val)
        show.status = "matched"
        db.commit()
        
        # Update Episodes
        for season_db in show.seasons:
            s_num = season_db.season_number
            if s_num in seasons_meta:
                tmdb_season = seasons_meta[s_num]
                season_db.poster_path = tmdb_season.get("poster_path")
                
                # Build dict of tmdb episodes
                tmdb_eps = {ep.get("episode_number"): ep for ep in tmdb_season.get("episodes", [])}
                
                for ep_db in season_db.episodes:
                    ep_num = ep_db.episode_number
                    if ep_num in tmdb_eps:
                        tmdb_ep = tmdb_eps[ep_num]
                        ep_db.title = tmdb_ep.get("name", f"Episode {ep_num}")
                        ep_db.plot = tmdb_ep.get("overview")
                        ep_db.air_date = tmdb_ep.get("air_date")
                        ep_db.thumbnail_path = tmdb_ep.get("still_path")
        db.commit()
        
        # Artwork Download
        if show.seasons and show.seasons[0].episodes:
            update_task(task_id, message="Downloading artwork...")
            first_ep_path = show.seasons[0].episodes[0].file_path
            if first_ep_path:
                import os
                # E.g. /tv/ShowName/Season 1/S01E01.mkv -> /tv/ShowName
                # Or /tv/ShowName/S01E01.mkv -> /tv/ShowName
                path_parts = first_ep_path.split(os.sep)
                # Just take the directory containing the file, unless it's a "Season 1" folder then go up one
                file_dir = os.path.dirname(first_ep_path)
                if "season" in os.path.basename(file_dir).lower() or "specials" in os.path.basename(file_dir).lower():
                    show_dir = os.path.dirname(file_dir)
                else:
                    show_dir = file_dir
                
                artwork_dl = ArtworkDownloader()
                mock_meta = {
                    "poster_path": series_meta.get("poster_path"),
                    "fanart_path": series_meta.get("fanart_path"),
                    "cast": series_meta.get("cast", []),
                    "images": series_meta.get("images", {})
                }
                # Create a mock file path explicitly using the Show Title so the artwork service saves correctly prefixed assets
                safe_title = show.title.replace(':', '').replace('/', '-')
                mock_file = os.path.join(show_dir, f"{safe_title}.mp4")
                await artwork_dl.download_movie_artwork(mock_meta, mock_file)
                
                # Generate NFOs
                nfo_gen = NFOGenerator()
                nfo_gen.generate_tvshow_nfo(series_meta, show_dir)
                for season_db in show.seasons:
                    if season_db.season_number in seasons_meta:
                        tmdb_season = seasons_meta[season_db.season_number]
                        tmdb_eps = {ep.get("episode_number"): ep for ep in tmdb_season.get("episodes", [])}
                        for ep_db in season_db.episodes:
                            if ep_db.episode_number in tmdb_eps:
                                nfo_gen.generate_episode_nfo(tmdb_eps[ep_db.episode_number], series_meta, ep_db.file_path)
        
        update_task(task_id, status="done", progress=1, message="Completed successfully")
                
    except Exception as e:
        import traceback
        print("Error in background tv scrape pipeline:")
        traceback.print_exc()
        if task_id:
            update_task(task_id, status="error", message=str(e))
    finally:
        db.close()

@router.post("/{show_id}/match")
def manual_match_tvshow(show_id: int, tmdb_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    show = db.query(TVShow).filter(TVShow.id == show_id).first()
    if not show:
        raise HTTPException(status_code=404, detail="TV Show not found")
    
    background_tasks.add_task(_background_scrape_tvshow, show_id, tmdb_id)
    return {"status": "Manual match task queued"}

@router.post("/{show_id}/scrape")
def trigger_scrape(show_id: int, background_tasks: BackgroundTasks, db: Session = Depends(get_db)):
    show = db.query(TVShow).filter(TVShow.id == show_id).first()
    if not show:
        raise HTTPException(status_code=404, detail="TV Show not found")
    
    background_tasks.add_task(_background_scrape_tvshow, show_id)
    return {"status": "Task queued"}

class BulkScrapeRequest(BaseModel):
    show_ids: list[int]

def _bulk_scrape_task(show_ids: list[int]):
    import asyncio
    loop = asyncio.new_event_loop()
    asyncio.set_event_loop(loop)
    try:
        for show_id in show_ids:
            loop.run_until_complete(_background_scrape_tvshow(show_id))
    finally:
        loop.close()

@router.post("/scrape/bulk")
def trigger_bulk_scrape(req: BulkScrapeRequest, background_tasks: BackgroundTasks):
    if not req.show_ids:
        raise HTTPException(status_code=400, detail="No show IDs provided")
        
    background_tasks.add_task(_bulk_scrape_task, req.show_ids)
    return {"status": f"Queued {len(req.show_ids)} TV shows for scraping"}
