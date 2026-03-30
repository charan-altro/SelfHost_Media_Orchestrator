from sqlalchemy import Column, Integer, String, Boolean, Float, Text, ForeignKey, JSON, DateTime
from sqlalchemy.orm import relationship
from datetime import datetime
from backend.core.db import Base

class Library(Base):
    __tablename__ = "libraries"
    
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String, index=True)
    path = Column(String, unique=True, index=True)
    type = Column(String) # 'movie' or 'tv'
    language = Column(String, default='en')

class Movie(Base):
    __tablename__ = "movies"

    id = Column(Integer, primary_key=True, index=True)
    library_id = Column(Integer, ForeignKey("libraries.id"))
    title = Column(String, index=True)
    sort_title = Column(String)
    original_title = Column(String)
    year = Column(Integer, index=True)
    
    # IDs
    tmdb_id = Column(String, index=True, nullable=True)
    imdb_id = Column(String, index=True, nullable=True)
    
    # Metadata
    plot = Column(Text, nullable=True)
    tagline = Column(String, nullable=True)
    genres = Column(JSON, nullable=True)
    cast = Column(JSON, nullable=True)
    director = Column(String, nullable=True)
    content_rating = Column(String, nullable=True) # e.g. PG-13, R
    runtime = Column(Integer, nullable=True) # minutes
    
    # Ratings
    tmdb_rating = Column(Float, nullable=True)
    imdb_rating = Column(Float, nullable=True)
    imdb_votes = Column(Integer, nullable=True)
    metascore = Column(Integer, nullable=True)
    
    # Images
    poster_path = Column(String, nullable=True)
    fanart_path = Column(String, nullable=True)
    
    # Status
    status = Column(String, default="unmatched") # unmatched, matched
    nfo_generated = Column(Boolean, default=False)
    file_renamed = Column(Boolean, default=False)
    trailer_url = Column(String, nullable=True)  # YouTube URL
    
    # Relationships
    files = relationship("MovieFile", back_populates="movie", cascade="all, delete-orphan")

class MovieFile(Base):
    __tablename__ = "movie_files"
    
    id = Column(Integer, primary_key=True, index=True)
    movie_id = Column(Integer, ForeignKey("movies.id"))
    file_path = Column(String, unique=True, index=True)
    original_filename = Column(String)
    size_bytes = Column(Integer)
    
    # Media Info Specs
    resolution = Column(String, nullable=True) # 1080p, 4K
    hdr_type = Column(String, nullable=True) # HDR10, DV
    video_codec = Column(String, nullable=True) # x264, x265
    audio_codec = Column(String, nullable=True) # TrueHD, DTS
    audio_channels = Column(String, nullable=True) # 5.1, 7.1
    part_number = Column(Integer, nullable=True) # For cd1, cd2
    subtitle_path = Column(String, nullable=True)  # Path to downloaded .srt
    
    movie = relationship("Movie", back_populates="files")

class TVShow(Base):
    __tablename__ = "tv_shows"
    
    id = Column(Integer, primary_key=True, index=True)
    library_id = Column(Integer, ForeignKey("libraries.id"))
    title = Column(String, index=True)
    year = Column(Integer, index=True)
    
    # IDs
    tmdb_id = Column(String, index=True, nullable=True)
    tvdb_id = Column(String, index=True, nullable=True)
    imdb_id = Column(String, index=True, nullable=True)
    
    # Metadata
    plot = Column(Text, nullable=True)
    genres = Column(JSON, nullable=True)
    cast = Column(JSON, nullable=True)
    director = Column(String, nullable=True)
    runtime = Column(Integer, nullable=True)
    content_rating = Column(String, nullable=True)
    imdb_rating = Column(Float, nullable=True)
    
    # Images
    poster_path = Column(String, nullable=True)
    fanart_path = Column(String, nullable=True)
    
    status = Column(String, default="unmatched")
    episode_ordering = Column(String, default="aired") # aired, dvd, absolute
    trailer_url = Column(String, nullable=True)
    
    seasons = relationship("Season", back_populates="show", cascade="all, delete-orphan")

class Season(Base):
    __tablename__ = "seasons"
    
    id = Column(Integer, primary_key=True, index=True)
    show_id = Column(Integer, ForeignKey("tv_shows.id"))
    season_number = Column(Integer, index=True)
    episode_count = Column(Integer, default=0)
    poster_path = Column(String, nullable=True)
    
    show = relationship("TVShow", back_populates="seasons")
    episodes = relationship("Episode", back_populates="season", cascade="all, delete-orphan")

class Episode(Base):
    __tablename__ = "episodes"
    
    id = Column(Integer, primary_key=True, index=True)
    season_id = Column(Integer, ForeignKey("seasons.id"))
    episode_number = Column(Integer, index=True)
    title = Column(String)
    plot = Column(Text, nullable=True)
    air_date = Column(String, nullable=True)
    
    file_path = Column(String, nullable=True, unique=True)
    original_filename = Column(String, nullable=True)
    thumbnail_path = Column(String, nullable=True)
    
    # Media Info Specs
    resolution = Column(String, nullable=True)
    video_codec = Column(String, nullable=True)
    audio_codec = Column(String, nullable=True)
    
    missing = Column(Boolean, default=False)
    
    season = relationship("Season", back_populates="episodes")

class BackgroundTask(Base):
    __tablename__ = "background_tasks"
    
    id = Column(String, primary_key=True, index=True)
    name = Column(String)
    status = Column(String, default="queued") # queued, running, done, error
    progress = Column(Integer, default=0)
    total = Column(Integer, default=100)
    message = Column(String, nullable=True)
    duration = Column(Float, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
