"""Pytest fixtures for PGlite integration - Framework Agnostic Core."""

from collections.abc import Generator

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
    manager = PGliteManager()
    manager.start()

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
    manager = PGliteManager(pglite_config)
    manager.start()
    manager.wait_for_ready()

    try:
        yield manager
    finally:
        manager.stop()
