"""Pytest fixtures for PGlite integration - Framework Agnostic Core."""

import os
import tempfile
import uuid
from collections.abc import Generator
from pathlib import Path

import pytest

from .config import PGliteConfig
from .manager import PGliteManager


@pytest.fixture(scope="session")
def pglite_manager() -> Generator[PGliteManager, None, None]:
    """Pytest fixture providing a PGlite manager for the test session.

    This is the core, framework-agnostic fixture. Framework-specific
    fixtures build on top of this.

    Yields:
        PGliteManager: Active PGlite manager instance
    """
    # Create unique configuration to prevent socket conflicts
    config = PGliteConfig()

    # Create a unique socket directory for this test session
    # PGlite expects socket_path to be the full path including .s.PGSQL.5432
    socket_dir = Path(tempfile.gettempdir()) / f"py-pglite-test-{uuid.uuid4().hex[:8]}"
    socket_dir.mkdir(mode=0o700, exist_ok=True)  # Restrict to user only
    config.socket_path = str(socket_dir / ".s.PGSQL.5432")

    manager = PGliteManager(config)
    manager.start()
    manager.wait_for_ready()

    try:
        yield manager
    finally:
        manager.stop()


@pytest.fixture(scope="module")
def pglite_manager_isolated() -> Generator[PGliteManager, None, None]:
    """Pytest fixture providing an isolated PGlite manager per test module.

    Use this fixture when you need stronger isolation between test modules
    to prevent cross-test interference.

    Yields:
        PGliteManager: Active PGlite manager instance
    """
    # Create unique configuration to prevent socket conflicts
    config = PGliteConfig()

    # Create a unique socket directory for this test module
    # PGlite expects socket_path to be the full path including .s.PGSQL.5432
    socket_dir = (
        Path(tempfile.gettempdir()) / f"py-pglite-module-{uuid.uuid4().hex[:8]}"
    )
    socket_dir.mkdir(mode=0o700, exist_ok=True)  # Restrict to user only
    config.socket_path = str(socket_dir / ".s.PGSQL.5432")

    manager = PGliteManager(config)
    manager.start()
    manager.wait_for_ready()

    try:
        yield manager
    finally:
        manager.stop()


# Additional configuration fixtures
@pytest.fixture(scope="session")
def pglite_config() -> PGliteConfig:
    """Pytest fixture providing PGlite configuration.

    Override this fixture in your conftest.py to customize PGlite settings.

    Returns:
        PGliteConfig: Configuration for PGlite
    """
    return PGliteConfig()


@pytest.fixture(scope="session")
def pglite_manager_custom(
    pglite_config: PGliteConfig,
) -> Generator[PGliteManager, None, None]:
    """Pytest fixture providing a PGlite manager with custom configuration.

    Args:
        pglite_config: Custom configuration

    Yields:
        PGliteManager: Active PGlite manager instance
    """
    # Ensure unique socket path even with custom config
    if not hasattr(pglite_config, "socket_path") or not pglite_config.socket_path:
        socket_dir = (
            Path(tempfile.gettempdir()) / f"py-pglite-custom-{uuid.uuid4().hex[:8]}"
        )
        socket_dir.mkdir(mode=0o700, exist_ok=True)  # Restrict to user only
        pglite_config.socket_path = str(socket_dir / ".s.PGSQL.5432")

    manager = PGliteManager(pglite_config)
    manager.start()
    manager.wait_for_ready()

    try:
        yield manager
    finally:
        manager.stop()
