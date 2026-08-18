from typing import Generator, Optional
import logging
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, Session
from app.core.config import settings

logger = logging.getLogger(__name__)

engine = None
SessionLocal = None

if settings.DATABASE_URL:
    try:
        # Standard PostgreSQL engine configuration
        engine = create_engine(
            settings.DATABASE_URL,
            pool_pre_ping=True,
            pool_size=10,
            max_overflow=20,
        )
        SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)
        logger.info("PostgreSQL database engine initialized successfully.")
    except Exception as e:
        logger.error(f"Failed to initialize PostgreSQL engine: {e}")


def get_db() -> Generator[Optional[Session], None, None]:
    """
    FastAPI dependency yielding a database session when PostgreSQL is available.
    """
    if SessionLocal is None:
        yield None
        return

    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


def is_database_connected() -> bool:
    """
    Utility check to verify if PostgreSQL connection is live.
    """
    if engine is None:
        return False
    try:
        with engine.connect() as conn:
            conn.execute("SELECT 1")
        return True
    except Exception:
        return False
