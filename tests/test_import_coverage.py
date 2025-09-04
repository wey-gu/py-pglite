"""Test coverage for import statements and module exports.

This file tests all the 0% coverage __init__.py files and extensions
to boost overall coverage with simple import tests.
"""

import pytest


def test_main_package_imports():
    """Test main package imports work correctly."""
    # Test all imports from py_pglite/__init__.py (lines 7-16)
    from py_pglite import AsyncpgClient
    from py_pglite import PGliteConfig
    from py_pglite import PGliteManager
    from py_pglite import PsycopgClient
    from py_pglite import get_client
    from py_pglite import get_default_client

    # Verify classes can be instantiated (basic smoke test)
    config = PGliteConfig()
    assert config.timeout == 30
    assert config.cleanup_on_exit is True

    manager = PGliteManager(config)
    assert manager.config == config

    # Test client getters work
    client = get_default_client()
    assert client is not None

    auto_client = get_client("auto")
    assert auto_client is not None


def test_django_package_imports():
    """Test Django package imports work correctly."""
    # Test all imports from py_pglite/django/__init__.py (lines 7-18)
    from py_pglite.django import configure_django_for_pglite
    from py_pglite.django import create_django_superuser
    from py_pglite.django import db
    from py_pglite.django import django_pglite_db
    from py_pglite.django import django_pglite_transactional_db
    from py_pglite.django import transactional_db

    # Verify these are callable/importable
    assert callable(configure_django_for_pglite)
    assert callable(create_django_superuser)
    # Note: fixture functions will be pytest fixtures, not directly callable


def test_sqlalchemy_package_imports():
    """Test SQLAlchemy package imports work correctly."""
    # Test all imports from py_pglite/sqlalchemy/__init__.py (lines 7-20)
    from py_pglite.sqlalchemy import SQLAlchemyAsyncPGliteManager
    from py_pglite.sqlalchemy import SQLAlchemyPGliteManager
    from py_pglite.sqlalchemy import create_all_tables
    from py_pglite.sqlalchemy import drop_all_tables
    from py_pglite.sqlalchemy import get_session_class
    from py_pglite.sqlalchemy import pglite_async_engine
    from py_pglite.sqlalchemy import pglite_async_session
    from py_pglite.sqlalchemy import pglite_engine
    from py_pglite.sqlalchemy import pglite_session
    from py_pglite.sqlalchemy import pglite_sqlalchemy_async_engine
    from py_pglite.sqlalchemy import pglite_sqlalchemy_engine
    from py_pglite.sqlalchemy import pglite_sqlalchemy_session

    # Verify manager classes can be imported
    assert SQLAlchemyAsyncPGliteManager is not None
    assert SQLAlchemyPGliteManager is not None

    # Verify utilities are callable
    assert callable(create_all_tables)
    assert callable(drop_all_tables)
    assert callable(get_session_class)


def test_extensions_registry():
    """Test extensions registry is accessible."""
    # Test py_pglite/extensions.py (line 7)
    from py_pglite.extensions import SUPPORTED_EXTENSIONS

    # Verify registry structure
    assert isinstance(SUPPORTED_EXTENSIONS, dict)
    assert "pgvector" in SUPPORTED_EXTENSIONS

    # Verify pgvector extension details
    pgvector = SUPPORTED_EXTENSIONS["pgvector"]
    assert pgvector["module"] == "@electric-sql/pglite/vector"
    assert pgvector["name"] == "vector"


def test_all_exports_available():
    """Test that all __all__ exports are available."""
    # Test main package __all__
    import py_pglite

    for name in py_pglite.__all__:
        assert hasattr(py_pglite, name), f"Missing export: {name}"

    # Test Django package __all__
    import py_pglite.django

    for name in py_pglite.django.__all__:
        assert hasattr(py_pglite.django, name), f"Missing Django export: {name}"

    # Test SQLAlchemy package __all__
    import py_pglite.sqlalchemy

    for name in py_pglite.sqlalchemy.__all__:
        assert hasattr(py_pglite.sqlalchemy, name), f"Missing SQLAlchemy export: {name}"


def test_package_metadata():
    """Test package metadata is accessible."""
    import py_pglite

    # Test __version__ is accessible (part of lines 7-16)
    assert hasattr(py_pglite, "__version__")
    assert isinstance(py_pglite.__version__, str)
    assert py_pglite.__version__ != ""
