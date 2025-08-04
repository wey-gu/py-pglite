"""SQLAlchemy-specific pytest fixtures for PGlite integration."""

import logging
import time

from collections.abc import AsyncGenerator
from collections.abc import Generator
from typing import Any

import pytest

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.ext.asyncio import async_sessionmaker
from sqlalchemy.orm import Session
from sqlalchemy.orm import sessionmaker

from py_pglite.config import PGliteConfig
from py_pglite.sqlalchemy.manager import SQLAlchemyPGliteManager
from py_pglite.sqlalchemy.manager_async import SQLAlchemyAsyncPGliteManager


# Try to import SQLModel
try:
    from sqlmodel import Session as SQLModelSession
    from sqlmodel import SQLModel
    from sqlmodel.ext.asyncio.session import AsyncSession as SQLModelAsyncSession

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
async def pglite_async_sqlalchemy_manager(
    pglite_config: PGliteConfig,
) -> AsyncGenerator[SQLAlchemyAsyncPGliteManager, None, None]:
    """Pytest fixture providing an async SQLAlchemy-enabled PGlite manager."""
    manager = SQLAlchemyAsyncPGliteManager(pglite_config)
    manager.start()

    is_ready = await manager.wait_for_ready()
    # Wait for database to be ready
    if not is_ready:
        raise RuntimeError("Failed to start PGlite database")

    try:
        yield manager
    finally:
        await manager.stop()


@pytest.fixture(scope="session")
def pglite_engine(pglite_sqlalchemy_manager: SQLAlchemyPGliteManager) -> Engine:
    """Pytest fixture providing a SQLAlchemy engine connected to PGlite.

    Uses the SQLAlchemy-enabled manager to ensure proper SQLAlchemy integration.
    """
    # Use the shared engine from manager (no custom parameters to avoid conflicts)
    return pglite_sqlalchemy_manager.get_engine()


@pytest.fixture(scope="session")
def pglite_async_engine(
    pglite_async_sqlalchemy_manager: SQLAlchemyAsyncPGliteManager,
) -> AsyncEngine:
    """Pytest fixture providing a SQLAlchemy async engine connected to PGlite.

    Uses the SQLAlchemy-enabled manager to ensure proper SQLAlchemy integration.
    """
    # Use the shared engine from manager (no custom parameters to avoid conflicts)
    return pglite_async_sqlalchemy_manager.get_engine()


@pytest.fixture(scope="session")
def pglite_sqlalchemy_engine(
    pglite_sqlalchemy_manager: SQLAlchemyPGliteManager,
) -> Engine:
    """Pytest fixture providing an optimized SQLAlchemy engine connected to PGlite."""
    # Use the shared engine from manager (no custom parameters to avoid conflicts)
    return pglite_sqlalchemy_manager.get_engine()


@pytest.fixture(scope="session")
def pglite_sqlalchemy_async_engine(
    pglite_async_sqlalchemy_manager: SQLAlchemyAsyncPGliteManager,
) -> AsyncEngine:
    """Pytest fixture providing an optimized SQLAlchemy async engine connected to PGlite."""
    # Use the shared engine from manager (no custom parameters to avoid conflicts)
    return pglite_async_sqlalchemy_manager.get_engine()


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
        session_local = sessionmaker(bind=pglite_engine)
        session = session_local()  # type: ignore[assignment]

    try:
        yield session
    finally:
        # Close the session safely
        try:
            session.close()
        except Exception as e:
            logger.warning(f"Error closing session: {e}")


@pytest.fixture(scope="function")
async def pglite_async_session(
    pglite_async_engine: AsyncEngine,
) -> AsyncGenerator[Any, None, None]:
    """Pytest fixture providing a SQLAlchemy/SQLModel async session with proper isolation.

    This fixture ensures database isolation between tests by cleaning all data
    at the start of each test.
    """
    # Clean up data before test starts
    logger.info("Starting database cleanup before test...")
    retry_count = 3
    for attempt in range(retry_count):
        try:
            async with pglite_async_engine.connect() as conn:
                # Get all table names from information_schema
                result = await conn.execute(
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
                    await conn.execute(text("SET session_replication_role = replica;"))

                    # Truncate all tables
                    for table_name in table_names:
                        logger.info(f"Truncating table: {table_name}")
                        await conn.execute(
                            text(
                                f'TRUNCATE TABLE "{table_name}" '
                                f"RESTART IDENTITY CASCADE;"
                            )
                        )

                    # Re-enable foreign key checks
                    await conn.execute(text("SET session_replication_role = DEFAULT;"))

                    # Commit the cleanup
                    await conn.commit()
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
    if HAS_SQLMODEL and SQLModelAsyncSession is not None:
        session = SQLModelAsyncSession(pglite_async_engine)
        # Create tables if using SQLModel with retry logic
        if SQLModel is not None:
            for attempt in range(3):
                try:
                    async with pglite_async_engine.begin() as conn:
                        await conn.run_sync(SQLModel.metadata.create_all)
                    break
                except Exception as e:
                    logger.warning(f"Table creation attempt {attempt + 1} failed: {e}")
                    if attempt == 2:
                        raise
                    time.sleep(0.5)
    else:
        session_local = async_sessionmaker(bind=pglite_async_engine)
        session = session_local()  # type: ignore[assignment]

    try:
        yield session
    finally:
        # Close the session safely
        try:
            await session.close()
        except Exception as e:
            logger.warning(f"Error closing session: {e}")


@pytest.fixture(scope="function")
def pglite_sqlalchemy_session(pglite_session: Session) -> Session:
    """Legacy fixture name for backwards compatibility."""
    return pglite_session


@pytest.fixture(scope="function")
def pglite_sqlalchemy_async_session(pglite_async_session: AsyncSession) -> AsyncSession:
    """Legacy fixture name for backwards compatibility."""
    return pglite_session
