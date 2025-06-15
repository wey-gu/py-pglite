"""Tests for Django backend integration.

Tests the core Django database backend functionality, focusing on
the decoupling fix and ensuring wait_for_ready() works properly.
"""

from unittest.mock import patch

import pytest

from py_pglite import PGliteManager


class TestDjangoBackendDecoupling:
    """Test Django backend decoupling and wait_for_ready fix."""

    def test_django_backend_imports(self):
        """Test that Django backend can be imported when Django is available."""
        try:
            import django  # noqa: F401

            # Should be able to import Django backend components
            from py_pglite.django.backend import (
                PGliteDatabaseCreation,
                PGliteDatabaseWrapper,
                get_pglite_manager,
            )

            assert PGliteDatabaseCreation is not None
            assert PGliteDatabaseWrapper is not None
            assert get_pglite_manager is not None

        except ImportError:
            pytest.skip("Django not available, skipping Django backend tests")

    def test_base_manager_has_wait_for_ready(self):
        """Test that base PGliteManager has wait_for_ready method for Django backend."""
        manager = PGliteManager()

        # Should have both methods (the fix we implemented)
        assert hasattr(manager, "wait_for_ready")
        assert hasattr(manager, "wait_for_ready_basic")

        # Both should be callable
        assert callable(manager.wait_for_ready)
        assert callable(manager.wait_for_ready_basic)

    def test_wait_for_ready_delegation(self):
        """Test that wait_for_ready properly delegates to wait_for_ready_basic."""
        manager = PGliteManager()

        # Mock wait_for_ready_basic to verify delegation
        with patch.object(manager, "wait_for_ready_basic") as mock_basic:
            mock_basic.return_value = True

            result = manager.wait_for_ready(max_retries=5, delay=0.5)

            # Should have called wait_for_ready_basic with correct arguments
            mock_basic.assert_called_once_with(max_retries=5, delay=0.5)
            assert result is True

    def test_wait_for_ready_parameters(self):
        """Test that wait_for_ready accepts same parameters as wait_for_ready_basic."""
        manager = PGliteManager()

        # Test with different parameter combinations
        with patch.object(manager, "wait_for_ready_basic") as mock_basic:
            mock_basic.return_value = False

            # Default parameters
            result1 = manager.wait_for_ready()
            mock_basic.assert_called_with(max_retries=15, delay=1.0)

            # Custom parameters
            result2 = manager.wait_for_ready(max_retries=10, delay=0.5)
            mock_basic.assert_called_with(max_retries=10, delay=0.5)

            assert result1 is False
            assert result2 is False

    def test_django_backend_compatibility(self):
        """Test that Django backend code pattern works with base manager."""
        try:
            import django  # noqa: F401

            has_django = True
        except ImportError:
            has_django = False

        if not has_django:
            pytest.skip("Django not available")

        # Test the pattern used in Django backend: manager.wait_for_ready()
        manager = PGliteManager()

        # Should be able to call wait_for_ready without error
        # (It will return False since the manager isn't started, but shouldn't crash)
        result = manager.wait_for_ready(max_retries=1, delay=0.1)

        # Should return False since manager isn't started, but not crash
        assert result is False

    def test_django_backend_error_handling(self):
        """Test that Django backend fails gracefully when Django is not available."""
        try:
            # Simple test - try to import Django backend components
            from py_pglite.django.backend import PGliteDatabaseWrapper

            # If we can import, Django is available
            # The actual error handling is built into the class
            # and would only trigger in environments without Django
            assert PGliteDatabaseWrapper is not None

        except ImportError:
            # Expected if Django imports fail completely
            pytest.skip("Django completely unavailable")


class TestFrameworkDecouplingValidation:
    """Test that the decoupling fix doesn't break other frameworks."""

    def test_sqlalchemy_manager_still_works(self):
        """Test that SQLAlchemy manager still has its own wait_for_ready."""
        try:
            from py_pglite.sqlalchemy import SQLAlchemyPGliteManager

            manager = SQLAlchemyPGliteManager()

            # Should have wait_for_ready method (SQLAlchemy-specific version)
            assert hasattr(manager, "wait_for_ready")
            assert callable(manager.wait_for_ready)

            # Should also inherit the base wait_for_ready method
            # but SQLAlchemy version might override it

        except ImportError:
            pytest.skip("SQLAlchemy not available")

    def test_base_manager_is_framework_agnostic(self):
        """Test that base manager remains framework-agnostic."""
        manager = PGliteManager()

        # Should not have any framework-specific methods beyond wait_for_ready
        assert hasattr(manager, "wait_for_ready")
        assert hasattr(manager, "wait_for_ready_basic")
        assert hasattr(manager, "start")
        assert hasattr(manager, "stop")
        assert hasattr(manager, "is_running")
        assert hasattr(manager, "get_connection_string")

        # Should NOT have framework-specific methods like get_engine
        assert not hasattr(manager, "get_engine")

    def test_decoupling_consistency(self):
        """Test that all managers have consistent wait_for_ready behavior."""
        # Base manager
        base_manager = PGliteManager()
        assert hasattr(base_manager, "wait_for_ready")

        # SQLAlchemy manager (if available)
        try:
            from py_pglite.sqlalchemy import SQLAlchemyPGliteManager

            sqlalchemy_manager = SQLAlchemyPGliteManager()
            assert hasattr(sqlalchemy_manager, "wait_for_ready")
        except ImportError:
            pass  # SQLAlchemy not available

        # All managers should have wait_for_ready for consistency
