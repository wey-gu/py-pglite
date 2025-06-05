"""py-pglite: Python testing library for PGlite integration.

Provides seamless integration between PGlite (in-memory PostgreSQL)
and Python test suites.
"""

__version__ = "0.1.0"

# Main exports
from .config import PGliteConfig
from .manager import PGliteManager

# Import fixtures for pytest plugin discovery
try:
    from .fixtures import (  # noqa: F401
        pglite_engine,
        pglite_manager,
        pglite_session,
    )

    HAS_PYTEST = True
except ImportError:
    HAS_PYTEST = False

__all__ = [
    "PGliteConfig",
    "PGliteManager",
]

# Add pytest fixtures to __all__ if available
if HAS_PYTEST:
    __all__.extend(["pglite_engine", "pglite_manager", "pglite_session"])
