"""py-pglite: Python testing library for PGlite integration.

Provides seamless integration between PGlite (in-memory PostgreSQL)
and Python test suites with support for SQLAlchemy, SQLModel, and Django.
"""

import importlib.metadata


__version__ = importlib.metadata.version(__name__)

# Core exports (always available)
# Database client exports (choose your preferred client)
from py_pglite.clients import AsyncpgClient
from py_pglite.clients import PsycopgClient
from py_pglite.clients import get_client
from py_pglite.clients import get_default_client
from py_pglite.config import PGliteConfig
from py_pglite.manager import PGliteManager


# Core public API - framework agnostic
__all__ = [
    "AsyncpgClient",
    "PGliteConfig",
    "PGliteManager",
    "PsycopgClient",
    # Database clients
    "get_client",
    "get_default_client",
]

# Framework integrations are imported separately:
# from py_pglite.sqlalchemy import pglite_session, pglite_engine
# from py_pglite.django import db, transactional_db
# Or use the pytest plugin which auto-discovers fixtures
