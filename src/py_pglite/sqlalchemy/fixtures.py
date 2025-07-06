"""SQLAlchemy-specific pytest fixtures for PGlite integration."""

import logging
import time
from collections.abc import Generator
from typing import Any

import pytest
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker

from ..config import PGliteConfig
from .manager import SQLAlchemyPGliteManager

# Try to import SQLModel
try:
    from sqlmodel import Session as SQLModelSession
    from sqlmodel import SQLModel

    HAS_SQLMODEL = True
except ImportError:
    SQLModelSession = None  # type: ignore
    SQLModel = None  # type: ignore
    HAS_SQLMODEL = False

logger = logging.getLogger(__name__)


@pytest.fixture(scope="session")
def pglite_config() -> PGliteConfig:
    """Pytest fixture providing PGlite configuration."""
    return PGliteConfig()


@pytest.fixture(scope="session")
def pglite_sqlalchemy_manager(
    pglite_config: PGliteConfig,
) -> Generator[SQLAlchemyPGliteManager, None, None]:
    """Pytest fixture providing an SQLAlchemy-enabled PGlite manager."""
    manager = SQLAlchemyPGliteManager(pglite_config)
    manager.start()

    # Wait for database to be ready
    if not manager.wait_for_ready():
        raise RuntimeError("Failed to start PGlite database")

    try:
        yield manager
    finally:
        manager.stop()


@pytest.fixture(scope="session")
def pglite_engine(pglite_sqlalchemy_manager: SQLAlchemyPGliteManager) -> Engine:
    """Pytest fixture providing a SQLAlchemy engine connected to PGlite.

    Uses the SQLAlchemy-enabled manager to ensure proper SQLAlchemy integration.
    """
    # Use the shared engine from manager (no custom parameters to avoid conflicts)
    return pglite_sqlalchemy_manager.get_engine()


@pytest.fixture(scope="session")
def pglite_sqlalchemy_engine(
    pglite_sqlalchemy_manager: SQLAlchemyPGliteManager,
) -> Engine:
    """Pytest fixture providing an optimized SQLAlchemy engine connected to PGlite."""
    # Use the shared engine from manager (no custom parameters to avoid conflicts)
    return pglite_sqlalchemy_manager.get_engine()


@pytest.fixture(scope="function")
def pglite_session(pglite_engine: Engine) -> Generator[Any, None, None]:
    """Pytest fixture providing a SQLAlchemy/SQLModel session with proper isolation.

    This fixture ensures database isolation between tests by cleaning all data
    at the start of each test.
    """
    # Clean up data before test starts
    logger.info("Starting database cleanup before test...")
    retry_count = 3
    for attempt in range(retry_count):
        try:
            with pglite_engine.connect() as conn:
                # Get all table names from information_schema
                result = conn.execute(
                    text("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_type = 'BASE TABLE'
                """)
                )

                table_names = [row[0] for row in result]
                logger.info(f"Found tables to clean: {table_names}")

                if table_names:
                    # Disable foreign key checks for faster cleanup
                    conn.execute(text("SET session_replication_role = replica;"))

                    # Truncate all tables
                    for table_name in table_names:
                        logger.info(f"Truncating table: {table_name}")
                        conn.execute(
                            text(
                                f'TRUNCATE TABLE "{table_name}" '
                                f"RESTART IDENTITY CASCADE;"
                            )
                        )

                    # Re-enable foreign key checks
                    conn.execute(text("SET session_replication_role = DEFAULT;"))

                    # Commit the cleanup
                    conn.commit()
                    logger.info("Database cleanup completed successfully")
                else:
                    logger.info("No tables found to clean")
                break  # Success, exit retry loop

        except Exception as e:
            logger.info(f"Database cleanup attempt {attempt + 1} failed: {e}")
            if attempt == retry_count - 1:
                logger.warning(
                    "Database cleanup failed after all retries, continuing anyway"
                )
            else:
                time.sleep(0.5)  # Brief pause before retry

    # Create session - prefer SQLModel if available
    if HAS_SQLMODEL and SQLModelSession is not None:
        session = SQLModelSession(pglite_engine)
        # Create tables if using SQLModel with retry logic
        if SQLModel is not None:
            for attempt in range(3):
                try:
                    SQLModel.metadata.create_all(pglite_engine)
                    break
                except Exception as e:
                    logger.warning(f"Table creation attempt {attempt + 1} failed: {e}")
                    if attempt == 2:
                        raise
                    time.sleep(0.5)
    else:
        SessionLocal = sessionmaker(bind=pglite_engine)
        session = SessionLocal()  # type: ignore[assignment]

    try:
        yield session
    finally:
        # Close the session safely
        try:
            session.close()
        except Exception as e:
            logger.warning(f"Error closing session: {e}")


@pytest.fixture(scope="function")
def pglite_sqlalchemy_session(pglite_session: Session) -> Session:
    """Legacy fixture name for backwards compatibility."""
    return pglite_session
