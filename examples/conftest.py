"""Isolated pytest configuration for examples.

This ensures examples have their own PGlite instances and don't interfere
with the main test suite or each other when running all tests together.
"""

import logging
import os
import tempfile
import time
import uuid

from collections.abc import Generator
from pathlib import Path
from typing import Any

import pytest

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import StaticPool

from py_pglite.config import PGliteConfig
from py_pglite.sqlalchemy import SQLAlchemyPGliteManager


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


@pytest.fixture(scope="module")
def pglite_manager() -> Generator[SQLAlchemyPGliteManager, None, None]:
    """Isolated PGlite manager for examples - one per test module.

    This overrides the session-scoped fixture from the main package
    to provide better isolation when running all tests together.
    """
    # Create unique configuration to prevent socket conflicts
    config = PGliteConfig()

    # Create a unique socket directory for this example module
    # PGlite expects socket_path to be the full path including .s.PGSQL.5432
    socket_dir = (
        Path(tempfile.gettempdir()) / f"py-pglite-example-{uuid.uuid4().hex[:8]}"
    )
    socket_dir.mkdir(mode=0o700, exist_ok=True)  # Restrict to user only
    config.socket_path = str(socket_dir / ".s.PGSQL.5432")

    manager = SQLAlchemyPGliteManager(config)
    manager.start()
    manager.wait_for_ready()

    try:
        yield manager
    finally:
        manager.stop()


@pytest.fixture(scope="module")
def pglite_engine(pglite_manager: SQLAlchemyPGliteManager) -> Engine:
    """Isolated SQLAlchemy engine for examples."""
    # Use the shared engine from manager (no custom parameters to avoid conflicts)
    return pglite_manager.get_engine()


@pytest.fixture(scope="function")
def pglite_session(pglite_engine: Engine) -> Generator[Any, None, None]:
    """Isolated SQLAlchemy/SQLModel session for examples with proper cleanup."""
    # Clean up data before test starts with retry logic
    logger.info("Starting database cleanup before example test...")
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
                                "RESTART IDENTITY CASCADE;"
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
