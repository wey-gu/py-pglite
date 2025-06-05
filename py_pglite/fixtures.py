"""Pytest fixtures for PGlite integration."""

import time
from collections.abc import Generator
from typing import Any

import pytest
from sqlalchemy import text
from sqlalchemy.engine import Engine

from .config import PGliteConfig
from .manager import PGliteManager

# Try to import SQLAlchemy Session types
try:
    from sqlalchemy.orm import Session as SQLAlchemySession

    HAS_SQLALCHEMY_ORM = True
except ImportError:
    SQLAlchemySession = None  # type: ignore
    HAS_SQLALCHEMY_ORM = False

# Try to import SQLModel
try:
    from sqlmodel import Session as SQLModelSession
    from sqlmodel import SQLModel

    HAS_SQLMODEL = True
except ImportError:
    SQLModelSession = None  # type: ignore
    SQLModel = None  # type: ignore
    HAS_SQLMODEL = False


@pytest.fixture(scope="module")
def pglite_manager() -> Generator[PGliteManager, None, None]:
    """Pytest fixture providing a PGlite manager for the test module.

    Yields:
        PGliteManager: Active PGlite manager instance
    """
    manager = PGliteManager()
    manager.start()

    try:
        yield manager
    finally:
        manager.stop()


@pytest.fixture(scope="module")
def pglite_engine(pglite_manager: PGliteManager) -> Engine:
    """Pytest fixture providing SQLAlchemy engine connected to PGlite.

    Args:
        pglite_manager: PGlite manager instance

    Returns:
        Engine: SQLAlchemy engine connected to PGlite
    """
    # Get the engine
    engine = pglite_manager.get_engine()

    # Wait for database to be ready like the working version
    max_retries = 15
    for attempt in range(max_retries):
        try:
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1 as test"))
                row = result.fetchone()
                if row is not None and row[0] == 1:
                    break
        except Exception:
            if attempt < max_retries - 1:
                time.sleep(1.0)
            else:
                raise

    return engine


@pytest.fixture(scope="function")
def pglite_session(pglite_engine: Engine) -> Generator[Any, None, None]:
    """Pytest fixture providing a database session with automatic cleanup.

    Creates tables, provides a session, and cleans up after each test.
    Works with both SQLAlchemy ORM and SQLModel.

    Args:
        pglite_engine: SQLAlchemy engine

    Yields:
        Session: Database session (SQLAlchemy or SQLModel)
    """
    # Type hint for session variable
    session: Any | None = None
    is_sqlmodel = False

    # Create all tables if SQLModel is available
    if HAS_SQLMODEL and SQLModel is not None and SQLModelSession is not None:
        SQLModel.metadata.create_all(pglite_engine)
        session = SQLModelSession(pglite_engine)
        is_sqlmodel = True
    elif HAS_SQLALCHEMY_ORM and SQLAlchemySession is not None:
        # For pure SQLAlchemy, user needs to create tables manually
        session = SQLAlchemySession(pglite_engine)
        is_sqlmodel = False
    else:
        raise ImportError(
            "Neither SQLModel nor SQLAlchemy ORM Session found. "
            "Install with: pip install 'py-pglite[sqlmodel]' or sqlalchemy"
        )

    try:
        yield session
    finally:
        if session is not None:
            session.close()

        # Clean up tables for next test
        if is_sqlmodel and SQLModel is not None:
            # Drop and recreate for clean state
            SQLModel.metadata.drop_all(pglite_engine)
            SQLModel.metadata.create_all(pglite_engine)


# Additional configuration fixtures
@pytest.fixture(scope="session")
def pglite_config() -> PGliteConfig:
    """Pytest fixture providing PGlite configuration.

    Override this fixture in your conftest.py to customize PGlite settings.

    Returns:
        PGliteConfig: Configuration for PGlite
    """
    return PGliteConfig()


@pytest.fixture(scope="module")
def pglite_manager_custom(
    pglite_config: PGliteConfig,
) -> Generator[PGliteManager, None, None]:
    """Pytest fixture providing a PGlite manager with custom configuration.

    Args:
        pglite_config: Custom configuration

    Yields:
        PGliteManager: Active PGlite manager instance
    """
    manager = PGliteManager(pglite_config)
    manager.start()
    manager.wait_for_ready()

    try:
        yield manager
    finally:
        manager.stop()
