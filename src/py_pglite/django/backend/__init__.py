"""Django backend package for py-pglite integration."""

from .base import (
    DatabaseWrapper,
    PGliteDatabaseCreation,
    PGliteDatabaseWrapper,
    get_pglite_manager,
)

# Expose both names for compatibility
__all__ = [
    "DatabaseWrapper",
    "PGliteDatabaseWrapper",
    "PGliteDatabaseCreation",
    "get_pglite_manager",
]
