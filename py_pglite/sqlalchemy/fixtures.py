"""SQLAlchemy-specific pytest fixtures for PGlite integration."""

import logging
from collections.abc import Generator
from typing import Any

import pytest
from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from ..config import PGliteConfig
from ..manager import PGliteManager

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
def pglite_engine(pglite_manager: PGliteManager) -> Engine:
    """Pytest fixture providing a SQLAlchemy engine connected to PGlite.

    Uses the core pglite_manager fixture to ensure all integrations
    share the same PGlite instance.
    """
    return pglite_manager.get_engine(
        poolclass=StaticPool, pool_pre_ping=True, echo=False
    )


@pytest.fixture(scope="session")
def pglite_sqlalchemy_engine(pglite_manager: PGliteManager) -> Engine:
    """Pytest fixture providing an optimized SQLAlchemy engine connected to PGlite."""
    return pglite_manager.get_engine(
        poolclass=StaticPool, pool_pre_ping=True, echo=False
    )


@pytest.fixture(scope="function")
def pglite_session(pglite_engine: Engine) -> Generator[Any, None, None]:
    """Pytest fixture providing a SQLAlchemy/SQLModel session with proper isolation.

    This fixture ensures database isolation between tests by cleaning all data
    at the start of each test.
    """
    # Clean up data before test starts
    logger.info("Starting database cleanup before test...")
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
                # Truncate all tables
                for table_name in table_names:
                    logger.info(f"Truncating table: {table_name}")
                    conn.execute(
                        text(f'TRUNCATE TABLE "{table_name}" RESTART IDENTITY CASCADE;')
                    )

                # Commit the cleanup
                conn.commit()
                logger.info("Database cleanup completed successfully")
            else:
                logger.info("No tables found to clean")
    except Exception as e:
        logger.info(f"Database cleanup failed (might be first run): {e}")
        # Continue anyway - tables might not exist yet
        pass

    # Create session - prefer SQLModel if available
    if HAS_SQLMODEL and SQLModelSession is not None:
        session = SQLModelSession(pglite_engine)
        # Create tables if using SQLModel
        if SQLModel is not None:
            SQLModel.metadata.create_all(pglite_engine)
    else:
        SessionLocal = sessionmaker(bind=pglite_engine)
        session = SessionLocal()  # type: ignore[assignment]

    try:
        yield session
    finally:
        # Just close the session, cleanup is done at start of next test
        session.close()


@pytest.fixture(scope="function")
def pglite_sqlalchemy_session(pglite_session: Session) -> Session:
    """Legacy fixture name for backwards compatibility."""
    return pglite_session
