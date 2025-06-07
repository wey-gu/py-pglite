"""py-pglite: Python testing library for PGlite integration.

Provides seamless integration between PGlite (in-memory PostgreSQL)
and Python test suites with support for SQLAlchemy, SQLModel, and Django.
"""

__version__ = "0.2.0"

# Core exports (always available)
from .config import PGliteConfig
from .manager import PGliteManager

# Core public API - framework agnostic
__all__ = [
    "PGliteConfig",
    "PGliteManager",
]

# Framework integrations are imported separately:
# from py_pglite.sqlalchemy import pglite_session, pglite_engine
# from py_pglite.django import db, transactional_db
# Or use the pytest plugin which auto-discovers fixtures
