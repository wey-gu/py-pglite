"""SQLAlchemy integration for py-pglite.

This module provides SQLAlchemy-specific fixtures and utilities for py-pglite.
"""

# Import fixtures and utilities
from py_pglite.sqlalchemy.fixtures import pglite_async_engine
from py_pglite.sqlalchemy.fixtures import pglite_async_session
from py_pglite.sqlalchemy.fixtures import pglite_async_sqlalchemy_manager
from py_pglite.sqlalchemy.fixtures import pglite_engine
from py_pglite.sqlalchemy.fixtures import pglite_session
from py_pglite.sqlalchemy.fixtures import pglite_sqlalchemy_async_engine
from py_pglite.sqlalchemy.fixtures import pglite_sqlalchemy_engine
from py_pglite.sqlalchemy.fixtures import pglite_sqlalchemy_session
from py_pglite.sqlalchemy.manager import SQLAlchemyPGliteManager
from py_pglite.sqlalchemy.manager_async import SQLAlchemyAsyncPGliteManager
from py_pglite.sqlalchemy.utils import create_all_tables
from py_pglite.sqlalchemy.utils import drop_all_tables
from py_pglite.sqlalchemy.utils import get_session_class


__all__ = [
    # Manager
    "SQLAlchemyAsyncPGliteManager",
    "SQLAlchemyPGliteManager",
    # Utilities
    "create_all_tables",
    "drop_all_tables",
    "get_session_class",
    # Fixtures
    "pglite_async_engine",
    "pglite_async_session",
    "pglite_async_sqlalchemy_manager",
    "pglite_engine",
    "pglite_session",
    "pglite_sqlalchemy_async_engine",
    "pglite_sqlalchemy_engine",
    "pglite_sqlalchemy_session",
]
