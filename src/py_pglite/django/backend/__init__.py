"""Django backend package for py-pglite integration."""

from .base import DatabaseWrapper
from .base import PGliteDatabaseCreation
from .base import PGliteDatabaseWrapper
from .base import get_pglite_manager


# Expose both names for compatibility
__all__ = [
    "DatabaseWrapper",
    "PGliteDatabaseWrapper",
    "PGliteDatabaseCreation",
    "get_pglite_manager",
]
