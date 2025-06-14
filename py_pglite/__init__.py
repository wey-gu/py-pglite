"""py-pglite: Python testing library for PGlite integration.

Provides seamless integration between PGlite (in-memory PostgreSQL)
and Python test suites with support for SQLAlchemy, SQLModel, and Django.
"""

__version__ = "0.4.0"

# Core exports (always available)
# Database client exports (choose your preferred client)
from .clients import AsyncpgClient, PsycopgClient, get_client, get_default_client
from .config import PGliteConfig
from .manager import PGliteManager

# Core public API - framework agnostic
__all__ = [
    "PGliteConfig",
    "PGliteManager",
    # Database clients
    "get_client",
    "get_default_client",
    "PsycopgClient",
    "AsyncpgClient",
]

# Framework integrations are imported separately:
# from py_pglite.sqlalchemy import pglite_session, pglite_engine
# from py_pglite.django import db, transactional_db
# Or use the pytest plugin which auto-discovers fixtures
