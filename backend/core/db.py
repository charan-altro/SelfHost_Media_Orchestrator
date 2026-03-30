from sqlalchemy import create_engine, event, text
from sqlalchemy.orm import sessionmaker, declarative_base
from backend.core.config import settings

engine = create_engine(
    settings.DATABASE_URL, 
    connect_args={
        "check_same_thread": False,
        "timeout": 30
    }
)

@event.listens_for(engine, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    cursor = dbapi_connection.cursor()
    cursor.execute("PRAGMA journal_mode=WAL")
    cursor.execute("PRAGMA synchronous=NORMAL")
    cursor.execute("PRAGMA busy_timeout=15000")
    cursor.close()

SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

Base = declarative_base()

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# ──────────────────────────────────────────────────────────────────
# Lightweight incremental migration.
# SQLite does not support ALTER TABLE ... ADD COLUMN IF NOT EXISTS,
# so we attempt each ALTER TABLE and silently swallow the "duplicate
# column" error. New columns must be listed here as the schema grows.
# ──────────────────────────────────────────────────────────────────
_MIGRATIONS = [
    "ALTER TABLE movies      ADD COLUMN trailer_url   TEXT",
    "ALTER TABLE movie_files ADD COLUMN subtitle_path TEXT",
    "ALTER TABLE movies      ADD COLUMN cast           JSON",
    "ALTER TABLE movies      ADD COLUMN director       TEXT",
    "ALTER TABLE tv_shows    ADD COLUMN cast           JSON",
    "ALTER TABLE tv_shows    ADD COLUMN director       TEXT",
    "ALTER TABLE tv_shows    ADD COLUMN runtime        INTEGER",
    "ALTER TABLE tv_shows    ADD COLUMN trailer_url    TEXT",
]

def run_migrations():
    # Initial table creations
    Base.metadata.create_all(bind=engine)
    
    with engine.connect() as conn:
        for stmt in _MIGRATIONS:
            try:
                conn.execute(text(stmt))
                conn.commit()
            except Exception:
                # Column already exists — safe to ignore
                conn.rollback()
