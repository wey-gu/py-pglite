"""SQLAlchemy integration for py-pglite.

This module provides SQLAlchemy-specific fixtures and utilities for py-pglite.
"""

# Import fixtures and utilities
from py_pglite.sqlalchemy.fixtures import pglite_engine
from py_pglite.sqlalchemy.fixtures import pglite_session
from py_pglite.sqlalchemy.fixtures import pglite_sqlalchemy_engine
from py_pglite.sqlalchemy.fixtures import pglite_sqlalchemy_session
from py_pglite.sqlalchemy.manager import SQLAlchemyPGliteManager
from py_pglite.sqlalchemy.utils import create_all_tables
from py_pglite.sqlalchemy.utils import drop_all_tables
from py_pglite.sqlalchemy.utils import get_session_class


__all__ = [
    # Manager
    "SQLAlchemyPGliteManager",
    # Utilities
    "create_all_tables",
    "drop_all_tables",
    "get_session_class",
    # Fixtures
    "pglite_engine",
    "pglite_session",
    "pglite_sqlalchemy_engine",
    "pglite_sqlalchemy_session",
]
