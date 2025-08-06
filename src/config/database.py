"""
Database configuration and session management for Quote Master Pro
"""

from sqlalchemy import create_engine, MetaData
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, Session
from sqlalchemy.pool import StaticPool
from contextlib import asynccontextmanager
from typing import Generator
import logging

from src.config.settings import get_settings

logger = logging.getLogger(__name__)
settings = get_settings()

# Database engine
engine = create_engine(
    settings.DATABASE_URL,
    poolclass=StaticPool if settings.DATABASE_URL.startswith("sqlite") else None,
    connect_args={"check_same_thread": False} if settings.DATABASE_URL.startswith("sqlite") else {},
    echo=settings.DEBUG
)

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()

def get_db_session() -> Generator[Session, None, None]:
    """
    Database session dependency for FastAPI routes
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

@asynccontextmanager
async def get_async_db_session():
    """
    Async database session context manager
    """
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Async database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()

async def init_db():
    """
    Initialize database and create tables
    """
    try:
        logger.info("Initializing database...")
        
        # Import all models to ensure they're registered
        from src.models.user import User
        from src.models.quote import Quote
        from src.models.voice_recording import VoiceRecording
        from src.models.analytics import AnalyticsEvent
        
        # Create all tables
        Base.metadata.create_all(bind=engine)
        logger.info("Database initialized successfully")
        
    except Exception as e:
        logger.error(f"Database initialization failed: {e}")
        raise

async def close_db():
    """
    Close database connections
    """
    try:
        engine.dispose()
        logger.info("Database connections closed")
    except Exception as e:
        logger.error(f"Error closing database: {e}")

def test_db_connection() -> bool:
    """
    Test database connectivity
    """
    try:
        with engine.connect() as connection:
            connection.execute("SELECT 1")
        logger.info("Database connection test successful")
        return True
    except Exception as e:
        logger.error(f"Database connection test failed: {e}")
        return False