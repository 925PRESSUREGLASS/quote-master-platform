"""Database configuration and session management."""

import logging
from typing import Generator, Optional

from sqlalchemy import MetaData, create_engine, event, inspect, text
from sqlalchemy.exc import DisconnectionError
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import Pool

from .config import get_settings

# Get settings
settings = get_settings()

# Configure logging
logger = logging.getLogger(__name__)

# Database engine
if settings.database_url.startswith("sqlite"):
    # SQLite configuration
    engine = create_engine(
        settings.database_url,
        echo=settings.debug,
        pool_pre_ping=True,  # Verify connections before use
    )
else:
    # PostgreSQL/other database configuration
    engine = create_engine(
        settings.database_url,
        pool_size=settings.db_pool_size,
        pool_overflow=settings.db_pool_overflow,
        echo=settings.debug,
        pool_pre_ping=True,  # Verify connections before use
    )

# Session factory
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=engine)

# Base class for models
Base = declarative_base()

# Metadata for migrations
metadata = MetaData()


def get_db() -> Generator[Session, None, None]:
    """Get database session dependency."""
    db = SessionLocal()
    try:
        yield db
    except Exception as e:
        logger.error(f"Database session error: {e}")
        db.rollback()
        raise
    finally:
        db.close()


def get_db_session() -> Session:
    """Get database session (for background tasks)."""
    return SessionLocal()


def init_db() -> None:
    """Initialize database tables."""
    try:
        # Import all models to register them
        import src.models  # noqa - import models to register them

        # Create tables only if they don't exist
        Base.metadata.create_all(bind=engine, checkfirst=True)
        logger.info("Database tables created successfully")

    except Exception as e:
        logger.error(f"Failed to initialize database: {e}")
        raise


def check_db_health() -> bool:
    """Check database connection health."""
    try:
        with engine.connect() as connection:
            connection.execute(text("SELECT 1"))
        return True
    except Exception as e:
        logger.error(f"Database health check failed: {e}")
        return False


class DatabaseManager:
    """Database management utilities."""

    @staticmethod
    def create_session() -> Session:
        """Create a new database session."""
        return SessionLocal()

    @staticmethod
    def close_session(session: Session) -> None:
        """Safely close a database session."""
        try:
            session.close()
        except Exception as e:
            logger.error(f"Error closing session: {e}")

    @staticmethod
    def rollback_session(session: Session) -> None:
        """Safely rollback a database session."""
        try:
            session.rollback()
        except Exception as e:
            logger.error(f"Error rolling back session: {e}")

    @staticmethod
    def commit_session(session: Session) -> bool:
        """Safely commit a database session."""
        try:
            session.commit()
            return True
        except Exception as e:
            logger.error(f"Error committing session: {e}")
            session.rollback()
            return False


# Connection event handlers
@event.listens_for(Pool, "connect")
def set_sqlite_pragma(dbapi_connection, connection_record):
    """Set SQLite pragmas for better performance (if using SQLite)."""
    if "sqlite" in str(dbapi_connection):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.execute("PRAGMA journal_mode=WAL")
        cursor.execute("PRAGMA synchronous=NORMAL")
        cursor.close()


@event.listens_for(Pool, "checkout")
def ping_connection(dbapi_connection, connection_record, connection_proxy):
    """Ping connection on checkout to ensure it's alive."""
    cursor = dbapi_connection.cursor()
    try:
        cursor.execute("SELECT 1")
    except Exception:
        # Connection is invalid, raise DisconnectionError
        raise DisconnectionError()
    finally:
        cursor.close()


# Transaction context manager
class TransactionManager:
    """Context manager for database transactions."""

    def __init__(self, session: Optional[Session] = None):
        self.session = session or SessionLocal()
        self.should_close = session is None

    def __enter__(self) -> Session:
        return self.session

    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.session.rollback()
        else:
            try:
                self.session.commit()
            except Exception:
                self.session.rollback()
                raise

        if self.should_close:
            self.session.close()


# Database utilities
class DatabaseUtils:
    """Database utility functions."""

    @staticmethod
    def execute_raw_sql(query: str, params: Optional[dict] = None):
        """Execute raw SQL query."""
        with engine.connect() as connection:
            result = connection.execute(text(query), params or {})
            return result.fetchall()

    @staticmethod
    def table_exists(table_name: str) -> bool:
        """Check if table exists in database."""
        inspector = inspect(engine)
        return table_name in inspector.get_table_names()

    @staticmethod
    def get_table_columns(table_name: str) -> list:
        """Get table column information."""
        inspector = inspect(engine)
        return inspector.get_columns(table_name)


# Database connection manager
db_manager = DatabaseManager()
