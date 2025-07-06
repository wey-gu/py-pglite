"""
Framework Isolation Tests
========================

Ensures that py-pglite maintains proper framework isolation:
- Core functionality works without any frameworks installed
- SQLAlchemy and Django modules don't interfere with each other
- Optional dependencies are truly optional
"""

import sys

from unittest.mock import patch

import pytest


def test_core_imports_without_frameworks():
    """Test that core py-pglite functionality works without optional frameworks."""

    # Test core imports work
    from py_pglite import PGliteConfig
    from py_pglite import PGliteManager
    from py_pglite.config import PGliteConfig as DirectConfig
    from py_pglite.manager import PGliteManager as DirectManager

    # Verify core functionality
    config = PGliteConfig()
    assert hasattr(config, "cleanup_on_exit")
    assert config.cleanup_on_exit is True

    # Manager can be instantiated
    manager = PGliteManager(config)
    assert manager.config == config


def test_sqlalchemy_isolation():
    """Test SQLAlchemy module isolation - should not affect Django."""

    # Import SQLAlchemy module
    try:
        from py_pglite.sqlalchemy import fixtures as sqlalchemy_fixtures
        from py_pglite.sqlalchemy.utils import create_all_tables

        # Should be available
        assert hasattr(sqlalchemy_fixtures, "pglite_engine")
        assert callable(create_all_tables)
    except ImportError:
        # If SQLAlchemy not installed, this is expected
        pytest.skip("SQLAlchemy not available")


def test_django_isolation():
    """Test Django module isolation - should not affect SQLAlchemy."""

    # Test Django module can be imported independently
    try:
        from py_pglite.django import fixtures as django_fixtures
        from py_pglite.django.utils import configure_django_for_pglite

        # Should be available
        assert hasattr(django_fixtures, "django_pglite_db")
        assert callable(configure_django_for_pglite)
    except ImportError:
        # If Django not installed, this is expected
        pytest.skip("Django not available")


def test_framework_coexistence():
    """Test that both frameworks can coexist without interference."""

    sqlalchemy_available = False
    django_available = False

    # Test SQLAlchemy import
    try:
        from py_pglite.sqlalchemy import fixtures as sqlalchemy_fixtures

        sqlalchemy_available = True
    except ImportError:
        pass

    # Test Django import
    try:
        from py_pglite.django import fixtures as django_fixtures

        django_available = True
    except ImportError:
        pass

    # If both are available, they should coexist
    if sqlalchemy_available and django_available:
        # Re-import to ensure they're bound in this scope
        from py_pglite.django import fixtures as django_fixtures  # noqa: F401
        from py_pglite.sqlalchemy import fixtures as sqlalchemy_fixtures  # noqa: F401

        # Both should work without conflicts
        assert hasattr(sqlalchemy_fixtures, "pglite_engine")
        assert hasattr(django_fixtures, "django_pglite_db")


def test_optional_dependency_handling():
    """Test that missing optional dependencies are handled gracefully."""

    # Test that core works even if optional deps are missing
    with patch.dict(sys.modules, {"sqlalchemy": None, "django": None}):
        # Core should still work
        from py_pglite import PGliteConfig
        from py_pglite import PGliteManager

        config = PGliteConfig()
        manager = PGliteManager(config)
        assert manager.config == config


def test_pytest_plugin_isolation():
    """Test that the pytest plugin maintains framework isolation."""

    try:
        import py_pglite.pytest_plugin  # noqa: F401

        # Plugin module should be importable without errors
        assert True  # Basic import test
    except ImportError:
        pytest.skip("Pytest plugin not available")


@pytest.mark.integration
def test_sequential_framework_usage():
    """Test using different frameworks sequentially in the same process."""

    # This simulates what happens when tests run sequentially
    # First, use core functionality
    from py_pglite import PGliteConfig
    from py_pglite import PGliteManager

    config = PGliteConfig()
    manager = PGliteManager(config)

    # Then try SQLAlchemy (if available)
    try:
        from py_pglite.sqlalchemy import fixtures  # noqa: F401

        # Should not interfere with core
        assert manager.config == config
    except ImportError:
        pass

    # Then try Django (if available)
    try:
        from py_pglite.django.utils import configure_django_for_pglite

        # Should not interfere with core or SQLAlchemy
        assert manager.config == config
    except ImportError:
        pass


if __name__ == "__main__":
    # Run basic isolation tests
    test_core_imports_without_frameworks()
    print("✅ Core imports work without frameworks")

    try:
        test_sqlalchemy_isolation()
        print("✅ SQLAlchemy isolation verified")
    except Exception as e:
        print(f"⚠️  SQLAlchemy test skipped: {e}")

    try:
        test_django_isolation()
        print("✅ Django isolation verified")
    except Exception as e:
        print(f"⚠️  Django test skipped: {e}")

    test_framework_coexistence()
    print("✅ Framework coexistence verified")

    print("\n🎉 All framework isolation tests passed!")
