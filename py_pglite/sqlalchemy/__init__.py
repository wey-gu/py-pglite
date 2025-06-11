"""SQLAlchemy integration for py-pglite.

This module provides SQLAlchemy-specific fixtures and utilities for py-pglite.
"""

# Import fixtures and utilities
from .fixtures import (
    pglite_engine,
    pglite_session,
    pglite_sqlalchemy_engine,
    pglite_sqlalchemy_session,
)
from .manager import SQLAlchemyPGliteManager
from .utils import (
    create_all_tables,
    drop_all_tables,
    get_session_class,
)

__all__ = [
    # Manager
    "SQLAlchemyPGliteManager",
    # Fixtures
    "pglite_engine",
    "pglite_session",
    "pglite_sqlalchemy_session",
    "pglite_sqlalchemy_engine",
    # Utilities
    "create_all_tables",
    "drop_all_tables",
    "get_session_class",
]
