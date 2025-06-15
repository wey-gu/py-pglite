"""Test coverage for import statements and module exports.

This file tests all the 0% coverage __init__.py files and extensions
to boost overall coverage with simple import tests.
"""

import pytest


def test_main_package_imports():
    """Test main package imports work correctly."""
    # Test all imports from py_pglite/__init__.py (lines 7-16)
    from py_pglite import (
        AsyncpgClient,
        PGliteConfig,
        PGliteManager,
        PsycopgClient,
        get_client,
        get_default_client,
    )

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
    from py_pglite.django import (
        configure_django_for_pglite,
        create_django_superuser,
        db,
        django_pglite_db,
        django_pglite_transactional_db,
        transactional_db,
    )

    # Verify these are callable/importable
    assert callable(configure_django_for_pglite)
    assert callable(create_django_superuser)
    # Note: fixture functions will be pytest fixtures, not directly callable


def test_sqlalchemy_package_imports():
    """Test SQLAlchemy package imports work correctly."""
    # Test all imports from py_pglite/sqlalchemy/__init__.py (lines 7-20)
    from py_pglite.sqlalchemy import (
        SQLAlchemyPGliteManager,
        create_all_tables,
        drop_all_tables,
        get_session_class,
        pglite_engine,
        pglite_session,
        pglite_sqlalchemy_engine,
        pglite_sqlalchemy_session,
    )

    # Verify manager class can be imported
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
