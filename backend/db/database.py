"""
Database Configuration — SQLite with SQLAlchemy.

- Single DB file: superbowl_pulse.db
- Auto-initialization on import
- Session management for FastAPI dependency injection
"""
from pathlib import Path
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session

from .models import Base

# Database file in project root
DB_PATH = Path(__file__).resolve().parent.parent.parent / "superbowl_pulse.db"
DATABASE_URL = f"sqlite:///{DB_PATH}"

# Create engine with SQLite-specific settings
engine = create_engine(
    DATABASE_URL,
    connect_args={"check_same_thread": False},  # Required for SQLite + FastAPI
    echo=False,  # Set to True for SQL debugging
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)


def init_db():
    """
    Initialize database tables.
    Called automatically on first import, idempotent.
    """
    Base.metadata.create_all(bind=engine)


def get_db():
    """
    FastAPI dependency: yields a database session.
    Automatically closes session after request.
    
    Usage in routes:
        @app.get("/events")
        def get_events(db: Session = Depends(get_db)):
            ...
    """
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


@contextmanager
def get_db_context():
    """
    Context manager for scripts and non-FastAPI usage.
    
    Usage:
        with get_db_context() as db:
            db.query(Event).all()
    """
    db = SessionLocal()
    try:
        yield db
        db.commit()
    except Exception:
        db.rollback()
        raise
    finally:
        db.close()


def reset_db():
    """
    Drop all tables and recreate. USE WITH CAUTION.
    """
    Base.metadata.drop_all(bind=engine)
    Base.metadata.create_all(bind=engine)


# Auto-initialize on import
init_db()
