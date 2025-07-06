"""Pytest configuration for advanced testing patterns."""

import pytest

from sqlmodel import SQLModel

from py_pglite import PGliteConfig
from py_pglite.sqlalchemy import SQLAlchemyPGliteManager


@pytest.fixture(scope="function")
def benchmark_engine():
    """High-performance engine configuration for benchmarking."""
    config = PGliteConfig(
        timeout=120,
        log_level="WARNING",
        cleanup_on_exit=True,
        node_options="--max-old-space-size=8192",
    )

    with SQLAlchemyPGliteManager(config) as manager:
        manager.wait_for_ready(max_retries=20, delay=1.0)

        engine = manager.get_engine(
            pool_pre_ping=False,
            echo=False,
            pool_recycle=3600,
        )

        SQLModel.metadata.create_all(engine)
        yield engine
