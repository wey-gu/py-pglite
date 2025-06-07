"""
SQLAlchemy Testing Configuration for py-pglite
==============================================

Provides SQLAlchemy-specific fixtures with proper isolation.
All fixtures are module-scoped to avoid conflicts with other test modules.
"""

from collections.abc import Generator

import pytest
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, sessionmaker
from sqlalchemy.pool import StaticPool

from py_pglite import PGliteConfig, PGliteManager


@pytest.fixture(scope="module")
def sqlalchemy_pglite_engine() -> Generator[Engine, None, None]:
    """Module-scoped PGlite engine for SQLAlchemy tests."""
    manager = PGliteManager(PGliteConfig())
    manager.start()

    try:
        engine = manager.get_engine(
            poolclass=StaticPool, pool_pre_ping=True, echo=False
        )
        yield engine
    finally:
        manager.stop()


@pytest.fixture(scope="function")
def sqlalchemy_session(
    sqlalchemy_pglite_engine: Engine,
) -> Generator[Session, None, None]:  # type: ignore
    """Function-scoped session for clean test isolation."""
    SessionLocal = sessionmaker(bind=sqlalchemy_pglite_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture(scope="function")
def sqlalchemy_transaction(
    sqlalchemy_pglite_engine: Engine,
) -> Generator[Session, None, None]:  # type: ignore
    """Transactional session that rolls back after each test."""
    connection = sqlalchemy_pglite_engine.connect()
    transaction = connection.begin()

    SessionLocal = sessionmaker(bind=connection)
    session = SessionLocal()

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()
