"""Django backend package for py-pglite integration."""

from py_pglite.django.backend.base import DatabaseWrapper
from py_pglite.django.backend.base import PGliteDatabaseCreation
from py_pglite.django.backend.base import PGliteDatabaseWrapper
from py_pglite.django.backend.base import get_pglite_manager


# Expose both names for compatibility
__all__ = [
    "DatabaseWrapper",
    "PGliteDatabaseCreation",
    "PGliteDatabaseWrapper",
    "get_pglite_manager",
]
