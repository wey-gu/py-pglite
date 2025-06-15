"""Comprehensive Django backend coverage tests.

Tests Django backend database operations, connection handling, and integration
to significantly improve coverage from 22% to 50%+.
"""

import tempfile
import threading
import time
import uuid
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from py_pglite.config import PGliteConfig
from py_pglite.manager import PGliteManager
from py_pglite.utils import execute_sql


class TestPGliteDatabaseCreation:
    """Test PGlite database creation functionality."""

    def test_import_without_django(self):
        """Test importing backend without Django available."""
        # Mock Django as unavailable
        with patch.dict(
            "sys.modules",
            {
                "django.conf": None,
                "django.core.management": None,
                "django.db": None,
                "django.db.backends.postgresql": None,
                "django.db.backends.postgresql.creation": None,
            },
        ):
            # Import should still work but HAS_DJANGO should be False
            with patch("py_pglite.django.backend.base.HAS_DJANGO", False):
                from py_pglite.django.backend.base import PGliteDatabaseWrapper

                # Should raise ImportError when trying to instantiate
                with pytest.raises(ImportError, match="Django is required"):
                    PGliteDatabaseWrapper({}, "default")

    def test_pglite_database_wrapper_initialization(self):
        """Test PGliteDatabaseWrapper initialization."""
        # Mock Django components
        with patch("py_pglite.django.backend.base.HAS_DJANGO", True):
            with patch(
                "py_pglite.django.backend.base.base.DatabaseWrapper"
            ) as mock_base:
                # Mock parent class
                mock_parent = Mock()
                mock_base.return_value = mock_parent

                # Import after mocking
                from py_pglite.django.backend.base import (
                    PGliteDatabaseCreation,
                    PGliteDatabaseWrapper,
                )

                # Create wrapper with settings
                settings_dict = {
                    "NAME": "test_db",
                    "USER": "test_user",
                    "OPTIONS": {},  # Django requires this
                }

                # Create wrapper
                wrapper = PGliteDatabaseWrapper(settings_dict, "test_alias")

                # Should set creation class
                assert isinstance(wrapper.creation, PGliteDatabaseCreation)

                # Should have settings_dict set
                assert wrapper.settings_dict == settings_dict

    def test_get_database_version(self):
        """Test get_database_version returns PostgreSQL 15.0."""
        with patch("py_pglite.django.backend.base.HAS_DJANGO", True):
            with patch(
                "py_pglite.django.backend.base.base.DatabaseWrapper"
            ) as mock_base:  # noqa: F841
                from py_pglite.django.backend.base import PGliteDatabaseWrapper

                # Create wrapper
                wrapper = PGliteDatabaseWrapper({}, "default")

                # Should return PostgreSQL 15.0 tuple
                version = wrapper.get_database_version()
                assert version == (15, 0)

    def test_create_test_db_basic_flow(self):
        """Test _create_test_db basic flow."""
        with patch("py_pglite.django.backend.base.HAS_DJANGO", True):
            with patch("py_pglite.django.backend.base.base.DatabaseWrapper"):
                from py_pglite.django.backend.base import PGliteDatabaseCreation

                # Mock connection
                mock_connection = Mock()
                mock_connection.settings_dict = {}
                mock_connection.alias = "test_alias"
                mock_connection._test_database_name = None

                creation = PGliteDatabaseCreation(mock_connection)  # type: ignore

                # Mock methods
                with patch.object(
                    creation, "_get_test_db_name", return_value="test_schema"
                ):
                    with patch.object(
                        creation, "_get_pglite_manager"
                    ) as mock_get_manager:
                        with patch.object(creation, "_update_connection_settings"):
                            with patch.object(creation, "_create_test_schema"):
                                with patch.object(creation, "_run_migrations"):
                                    # Mock manager
                                    mock_manager = Mock()
                                    mock_manager.is_running.return_value = False
                                    mock_get_manager.return_value = mock_manager

                                    # Call method
                                    result = creation._create_test_db(verbosity=0)

                                    # Verify flow
                                    assert result == "test_schema"
                                    mock_manager.start.assert_called_once()
                                    assert hasattr(
                                        mock_connection, "_test_database_name"
                                    )

    def test_create_test_db_already_running(self):
        """Test _create_test_db when manager is already running."""
        with patch("py_pglite.django.backend.base.HAS_DJANGO", True):
            with patch("py_pglite.django.backend.base.base.DatabaseWrapper"):
                from py_pglite.django.backend.base import PGliteDatabaseCreation

                mock_connection = Mock()
                creation = PGliteDatabaseCreation(mock_connection)  # type: ignore

                with patch.object(
                    creation, "_get_test_db_name", return_value="test_schema"
                ):
                    with patch.object(
                        creation, "_get_pglite_manager"
                    ) as mock_get_manager:
                        with patch.object(creation, "_update_connection_settings"):
                            with patch.object(creation, "_create_test_schema"):
                                with patch.object(creation, "_run_migrations"):
                                    # Mock manager already running
                                    mock_manager = Mock()
                                    mock_manager.is_running.return_value = True
                                    mock_get_manager.return_value = mock_manager

                                    # Call method
                                    result = creation._create_test_db(verbosity=0)

                                    # Should not call start()
                                    mock_manager.start.assert_not_called()
                                    assert result == "test_schema"

    def test_get_pglite_manager_creates_new(self):
        """Test _get_pglite_manager creates new manager."""
        with patch("py_pglite.django.backend.base.HAS_DJANGO", True):
            with patch("py_pglite.django.backend.base.base.DatabaseWrapper"):
                from py_pglite.django.backend.base import (
                    PGliteDatabaseCreation,
                    _pglite_managers,
                )

                # Clear managers dict
                _pglite_managers.clear()

                mock_connection = Mock()
                mock_connection.settings_dict = {}
                mock_connection.alias = "test_alias"

                creation = PGliteDatabaseCreation(mock_connection)  # type: ignore

                # Mock PGliteManager and config
                with patch(
                    "py_pglite.django.backend.base.PGliteManager"
                ) as mock_manager_class:
                    with patch(
                        "py_pglite.django.backend.base.PGliteConfig"
                    ) as mock_config_class:
                        with patch("tempfile.gettempdir", return_value="/tmp"):
                            with patch("uuid.uuid4") as mock_uuid:
                                mock_uuid.return_value.hex = "abcdef123456"
                                mock_config = Mock()
                                mock_config_class.return_value = mock_config
                                mock_manager = Mock()
                                mock_manager_class.return_value = mock_manager

                                # Call method
                                result = creation._get_pglite_manager("test_db")

                                # Should create new manager
                                assert result == mock_manager
                                assert "test_db" in _pglite_managers
                                mock_config_class.assert_called_once()
                                mock_manager_class.assert_called_once_with(mock_config)

    def test_get_pglite_manager_returns_existing(self):
        """Test _get_pglite_manager returns existing manager."""
        with patch("py_pglite.django.backend.base.HAS_DJANGO", True):
            with patch("py_pglite.django.backend.base.base.DatabaseWrapper"):
                from py_pglite.django.backend.base import (
                    PGliteDatabaseCreation,
                    _pglite_managers,
                )

                # Pre-populate managers dict
                mock_manager = Mock()
                _pglite_managers["existing_db"] = mock_manager

                mock_connection = Mock()
                mock_connection.settings_dict = {}
                mock_connection.alias = "test_alias"

                creation = PGliteDatabaseCreation(mock_connection)  # type: ignore

                # Call method
                result = creation._get_pglite_manager("existing_db")

                # Should return existing manager
                assert result == mock_manager

    def test_update_connection_settings(self):
        """Test _update_connection_settings updates Django connection."""
        with patch("py_pglite.django.backend.base.HAS_DJANGO", True):
            with patch("py_pglite.django.backend.base.base.DatabaseWrapper"):
                from py_pglite.django.backend.base import PGliteDatabaseCreation

                # Mock connection with settings_dict
                mock_connection = Mock()
                mock_connection.settings_dict = {
                    "NAME": "original_db",
                    "USER": "original_user",
                }

                creation = PGliteDatabaseCreation(mock_connection)  # type: ignore

                # Mock manager with connection string
                mock_manager = Mock()
                mock_config = Mock()
                mock_config.get_connection_string.return_value = "postgresql+psycopg://postgres:postgres@/postgres?host=/tmp/socket-dir"
                mock_manager.config = mock_config

                # Call method
                creation._update_connection_settings("test_schema", mock_manager)

                # Verify connection settings were updated
                updated_settings = mock_connection.settings_dict
                assert updated_settings["HOST"] == "/tmp/socket-dir"
                assert updated_settings["PORT"] == ""
                assert updated_settings["NAME"] == "postgres"
                assert updated_settings["USER"] == "postgres"
                assert updated_settings["PASSWORD"] == "postgres"
                assert (
                    updated_settings["OPTIONS"]["options"]
                    == "-c search_path=test_schema,public"
                )

                # Should close connection to force reconnect
                mock_connection.close.assert_called_once()

    def test_create_test_schema_success(self):
        """Test _create_test_schema successful execution."""
        with patch("py_pglite.django.backend.base.HAS_DJANGO", True):
            with patch("py_pglite.django.backend.base.base.DatabaseWrapper"):
                from py_pglite.django.backend.base import (
                    PGliteDatabaseCreation,
                    _pglite_managers,
                )

                # Mock manager
                mock_manager = Mock()
                mock_config = Mock()
                mock_config.get_connection_string.return_value = (
                    "postgresql://connection/string"
                )
                mock_manager.config = mock_config
                _pglite_managers["test_schema"] = mock_manager

                mock_connection = Mock()
                mock_connection.settings_dict = {}
                mock_connection.alias = "test_alias"

                creation = PGliteDatabaseCreation(mock_connection)  # type: ignore

                # Mock execute_sql to return success
                with patch("py_pglite.utils.execute_sql") as mock_execute:
                    mock_execute.return_value = True  # Success

                    # Call method
                    creation._create_test_schema("test_schema", verbosity=1)

                    # Should execute CREATE SCHEMA
                    mock_execute.assert_called_once()
                    args = mock_execute.call_args[0]
                    assert "CREATE SCHEMA IF NOT EXISTS" in args[1]
                    assert "test_schema" in args[1]

    def test_create_test_schema_failure(self):
        """Test _create_test_schema handles failure gracefully."""
        with patch("py_pglite.django.backend.base.HAS_DJANGO", True):
            with patch("py_pglite.django.backend.base.base.DatabaseWrapper"):
                from py_pglite.django.backend.base import (
                    PGliteDatabaseCreation,
                    _pglite_managers,
                )

                # Mock manager
                mock_manager = Mock()
                _pglite_managers["test_schema"] = mock_manager

                mock_connection = Mock()
                mock_connection.settings_dict = {}
                mock_connection.alias = "test_alias"

                creation = PGliteDatabaseCreation(mock_connection)  # type: ignore

                # Mock execute_sql to raise exception
                with patch(
                    "py_pglite.utils.execute_sql", side_effect=Exception("SQL error")
                ):
                    # Should not raise exception
                    creation._create_test_schema("test_schema", verbosity=0)

    def test_destroy_test_db(self):
        """Test _destroy_test_db cleanup."""
        with patch("py_pglite.django.backend.base.HAS_DJANGO", True):
            with patch("py_pglite.django.backend.base.base.DatabaseWrapper"):
                from py_pglite.django.backend.base import (
                    PGliteDatabaseCreation,
                    _pglite_managers,
                )

                # Pre-populate manager
                mock_manager = Mock()
                _pglite_managers["test_db"] = mock_manager

                mock_connection = Mock()
                mock_connection.settings_dict = {}
                mock_connection.alias = "test_alias"

                creation = PGliteDatabaseCreation(mock_connection)  # type: ignore

                with patch.object(
                    creation, "_destroy_test_schema"
                ) as mock_destroy_schema:
                    # Call method
                    creation._destroy_test_db("test_db", verbosity=0)

                    # Should destroy schema and cleanup manager
                    mock_destroy_schema.assert_called_once_with("test_db", 0)
                    mock_manager.stop.assert_called_once()
                    assert "test_db" not in _pglite_managers

    def test_destroy_test_schema_success(self):
        """Test _destroy_test_schema successful execution."""
        with patch("py_pglite.django.backend.base.HAS_DJANGO", True):
            with patch("py_pglite.django.backend.base.base.DatabaseWrapper"):
                from py_pglite.django.backend.base import (
                    PGliteDatabaseCreation,
                    _pglite_managers,
                )

                # Mock manager
                mock_manager = Mock()
                mock_config = Mock()
                mock_config.get_connection_string.return_value = (
                    "postgresql://connection/string"
                )
                mock_manager.config = mock_config
                _pglite_managers["test_schema"] = mock_manager

                mock_connection = Mock()
                mock_connection.settings_dict = {}
                mock_connection.alias = "test_alias"

                creation = PGliteDatabaseCreation(mock_connection)  # type: ignore

                # Mock execute_sql to return success
                with patch("py_pglite.utils.execute_sql") as mock_execute:
                    mock_execute.return_value = True  # Success

                    # Call method
                    creation._destroy_test_schema("test_schema", verbosity=1)

                    # Should execute DROP SCHEMA
                    mock_execute.assert_called_once()
                    args = mock_execute.call_args[0]
                    assert "DROP SCHEMA IF EXISTS" in args[1]
                    assert "test_schema" in args[1]
                    assert "CASCADE" in args[1]

    def test_run_migrations_success(self):
        """Test _run_migrations calls Django migrate command."""
        with patch("py_pglite.django.backend.base.HAS_DJANGO", True):
            with patch("py_pglite.django.backend.base.base.DatabaseWrapper"):
                from py_pglite.django.backend.base import PGliteDatabaseCreation

                mock_connection = Mock()
                mock_connection.settings_dict = {}
                mock_connection.alias = "test_alias"
                creation = PGliteDatabaseCreation(mock_connection)  # type: ignore

                # Mock call_command
                with patch("py_pglite.django.backend.base.call_command") as mock_call:
                    # Call method
                    creation._run_migrations(verbosity=1)

                    # Should call migrate command
                    mock_call.assert_called_once_with(
                        "migrate",
                        verbosity=1,
                        interactive=False,
                        database="test_alias",
                        run_syncdb=True,
                    )

    def test_run_migrations_handles_exception(self):
        """Test _run_migrations handles exceptions gracefully."""
        with patch("py_pglite.django.backend.base.HAS_DJANGO", True):
            with patch("py_pglite.django.backend.base.base.DatabaseWrapper"):
                from py_pglite.django.backend.base import PGliteDatabaseCreation

                mock_connection = Mock()
                mock_connection.settings_dict = {}
                mock_connection.alias = "test_alias"
                creation = PGliteDatabaseCreation(mock_connection)  # type: ignore

                # Mock call_command to raise exception
                with patch(
                    "py_pglite.django.backend.base.call_command",
                    side_effect=Exception("Migration error"),
                ):
                    # Should not raise exception
                    creation._run_migrations(verbosity=0)


class TestPGliteDatabaseWrapperConnection:
    """Test PGliteDatabaseWrapper connection handling."""

    def test_get_new_connection_without_test_database(self):
        """Test get_new_connection without test database."""
        # Mock Django components before importing our module
        with patch("py_pglite.django.backend.base.HAS_DJANGO", True):
            # Mock psycopg at module level
            mock_psycopg = Mock()
            mock_psycopg.connect = Mock(return_value="mock_connection")

            # Mock base class at module level
            mock_base = Mock()
            mock_base.DatabaseWrapper = Mock()

            with (
                patch("py_pglite.django.backend.base.base", mock_base),
                patch("psycopg.connect", mock_psycopg.connect),
            ):
                # Import after mocking
                from py_pglite.django.backend.base import PGliteDatabaseWrapper

                # Create wrapper
                settings_dict = {
                    "NAME": "test_db",
                    "USER": "test_user",
                    "PASSWORD": "test_pass",  # Add password
                    "OPTIONS": {},  # Django requires this
                }
                wrapper = PGliteDatabaseWrapper(settings_dict, "default")

                # Call method with connection params
                conn_params = {
                    "host": "localhost",
                    "dbname": "test",
                    "password": "test_pass",  # Add password
                }
                result = wrapper.get_new_connection(conn_params)

                # Should call parent method unchanged
                assert result == "mock_connection"
                mock_psycopg.connect.assert_called_once_with(**conn_params)

    def test_get_new_connection_with_test_database(self):
        """Test get_new_connection with test database and PGlite manager."""
        # Mock Django components before importing our module
        with patch("py_pglite.django.backend.base.HAS_DJANGO", True):
            # Mock psycopg at module level
            mock_psycopg = Mock()
            mock_psycopg.connect = Mock(return_value="mock_connection")

            # Mock base class at module level
            mock_base = Mock()
            mock_base.DatabaseWrapper = Mock()

            with (
                patch("py_pglite.django.backend.base.base", mock_base),
                patch("psycopg.connect", mock_psycopg.connect),
            ):
                # Import after mocking
                from py_pglite.django.backend.base import (
                    PGliteDatabaseWrapper,
                    _pglite_managers,
                )

                # Create wrapper
                settings_dict = {
                    "NAME": "test_db",
                    "USER": "test_user",
                    "PASSWORD": "test_pass",  # Add password
                    "OPTIONS": {},  # Django requires this
                }
                wrapper = PGliteDatabaseWrapper(settings_dict, "default")

                # Set test database name
                wrapper._test_database_name = "test_db"  # type: ignore

                # Mock manager
                mock_manager = Mock()
                mock_config = Mock()
                mock_config.get_connection_string.return_value = "postgresql+psycopg://postgres:postgres@/postgres?host=/tmp/socket-dir"
                mock_manager.config = mock_config
                _pglite_managers["test_db"] = mock_manager

                # Call method with connection params
                conn_params = {
                    "host": "localhost",
                    "dbname": "original_db",
                    "password": "test_pass",  # Add password
                }
                result = wrapper.get_new_connection(conn_params)

                # Should update connection params for PGlite
                expected_params = {
                    "host": "/tmp/socket-dir",
                    "port": None,
                    "dbname": "postgres",
                    "user": "postgres",
                    "password": "postgres",
                    "options": "-c search_path=test_db,public",
                }

                # Should call parent method with updated params
                assert result == "mock_connection"

                # Verify connection params were updated
                for key, value in expected_params.items():
                    assert conn_params[key] == value

                # Verify psycopg.connect was called with updated params
                mock_psycopg.connect.assert_called_once_with(**conn_params)

    def test_get_new_connection_no_host_in_connection_string(self):
        """Test get_new_connection when connection string has no host."""
        # Mock Django components before importing our module
        with patch("py_pglite.django.backend.base.HAS_DJANGO", True):
            # Mock psycopg at module level
            mock_psycopg = Mock()
            mock_psycopg.connect = Mock(return_value="mock_connection")

            # Mock base class at module level
            mock_base = Mock()
            mock_base.DatabaseWrapper = Mock()

            with (
                patch("py_pglite.django.backend.base.base", mock_base),
                patch("psycopg.connect", mock_psycopg.connect),
            ):
                # Import after mocking
                from py_pglite.django.backend.base import (
                    PGliteDatabaseWrapper,
                    _pglite_managers,
                )

                # Create wrapper
                settings_dict = {
                    "NAME": "test_db",
                    "USER": "test_user",
                    "PASSWORD": "test_pass",  # Add password
                    "OPTIONS": {},  # Django requires this
                }
                wrapper = PGliteDatabaseWrapper(settings_dict, "default")

                wrapper._test_database_name = "test_db"  # type: ignore

                # Mock manager with connection string without host
                mock_manager = Mock()
                mock_config = Mock()
                mock_config.get_connection_string.return_value = (
                    "postgresql+psycopg://postgres:postgres@/postgres"
                )
                mock_manager.config = mock_config
                _pglite_managers["test_db"] = mock_manager

                # Call method
                conn_params = {
                    "host": "localhost",
                    "password": "test_pass",  # Add password
                }
                result = wrapper.get_new_connection(conn_params)

                # Should call parent with original params (no update)
                assert result == "mock_connection"
                assert conn_params["host"] == "localhost"  # Should not be modified

                # Verify psycopg.connect was called with original params
                mock_psycopg.connect.assert_called_once_with(**conn_params)


class TestPGliteManagerRegistry:
    """Test PGlite manager registry functions."""

    def test_get_pglite_manager_by_alias(self):
        """Test get_pglite_manager finds manager by alias."""
        from py_pglite.django.backend.base import _pglite_managers, get_pglite_manager

        # Clear and populate managers dict
        _pglite_managers.clear()
        mock_manager = Mock()
        _pglite_managers["test_database_default"] = mock_manager

        # Should find by alias
        result = get_pglite_manager("default")
        assert result == mock_manager

    def test_get_pglite_manager_by_exact_name(self):
        """Test get_pglite_manager finds manager by exact name."""
        from py_pglite.django.backend.base import _pglite_managers, get_pglite_manager

        # Clear and populate managers dict
        _pglite_managers.clear()
        mock_manager = Mock()
        _pglite_managers["exact_name"] = mock_manager

        # Should find by exact name
        result = get_pglite_manager("exact_name")
        assert result == mock_manager

    def test_get_pglite_manager_not_found(self):
        """Test get_pglite_manager returns None when not found."""
        from py_pglite.django.backend.base import _pglite_managers, get_pglite_manager

        # Clear managers dict
        _pglite_managers.clear()

        # Should return None
        result = get_pglite_manager("nonexistent")
        assert result is None


class TestThreadingSafety:
    """Test threading safety of manager registry."""

    def test_manager_registry_thread_safety(self):
        """Test that manager registry operations are thread-safe."""
        from py_pglite.django.backend.base import _manager_lock, _pglite_managers

        _pglite_managers.clear()

        results = []

        def create_manager(name):
            """Thread function to create manager."""
            with _manager_lock:
                if name not in _pglite_managers:
                    # Create a real PGliteManager instead of a string
                    config = PGliteConfig()
                    _pglite_managers[name] = PGliteManager(config)
                results.append(_pglite_managers[name])

        # Create multiple threads
        threads = []
        for i in range(5):
            thread = threading.Thread(target=create_manager, args=(f"db_{i}",))
            threads.append(thread)

        # Start all threads
        for thread in threads:
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Should have 5 unique managers
        assert len(_pglite_managers) == 5
        assert len(results) == 5

        # Each manager should be unique
        for i in range(5):
            assert f"db_{i}" in _pglite_managers
            assert isinstance(_pglite_managers[f"db_{i}"], PGliteManager)
            # Verify each manager has a unique config
            assert _pglite_managers[f"db_{i}"].config is not None


class TestDatabaseWrapperExported:
    """Test DatabaseWrapper is properly exported."""

    def test_database_wrapper_export(self):
        """Test that DatabaseWrapper is exported as expected."""
        from py_pglite.django.backend.base import DatabaseWrapper, PGliteDatabaseWrapper

        # DatabaseWrapper should be an alias for PGliteDatabaseWrapper
        assert DatabaseWrapper is PGliteDatabaseWrapper

    def test_database_wrapper_with_django_unavailable(self):
        """Test DatabaseWrapper behavior when Django is unavailable."""
        # Mock HAS_DJANGO as False
        with patch("py_pglite.django.backend.base.HAS_DJANGO", False):
            from py_pglite.django.backend.base import DatabaseWrapper

            # Should still be the PGliteDatabaseWrapper class
            # but instantiation should fail
            with pytest.raises(ImportError, match="Django is required"):
                DatabaseWrapper({}, "default")


class TestConnectionStringParsing:
    """Test connection string parsing edge cases."""

    def test_connection_string_with_multiple_params(self):
        """Test parsing connection string with multiple URL parameters."""
        with patch("py_pglite.django.backend.base.HAS_DJANGO", True):
            with patch("py_pglite.django.backend.base.base.DatabaseWrapper"):
                from py_pglite.django.backend.base import (
                    PGliteDatabaseCreation,
                    _pglite_managers,
                )

                mock_connection = Mock()
                mock_connection.settings_dict = {}
                mock_connection.alias = "test_alias"

                creation = PGliteDatabaseCreation(mock_connection)  # type: ignore

                # Mock manager with complex connection string
                mock_manager = Mock()
                mock_config = Mock()
                mock_config.get_connection_string.return_value = "postgresql+psycopg://postgres:postgres@/postgres?host=/tmp/socket-dir&param2=value2#fragment"
                mock_manager.config = mock_config

                # Call method
                creation._update_connection_settings("test_schema", mock_manager)

                # Should extract just the socket directory
                assert mock_connection.settings_dict["HOST"] == "/tmp/socket-dir"

    def test_connection_string_with_ampersand_in_host(self):
        """Test parsing connection string, host parameter contains special chars."""
        with patch("py_pglite.django.backend.base.HAS_DJANGO", True):
            with patch("py_pglite.django.backend.base.base.DatabaseWrapper"):
                from py_pglite.django.backend.base import (
                    PGliteDatabaseCreation,
                    _pglite_managers,
                )

                mock_connection = Mock()
                mock_connection.settings_dict = {}
                mock_connection.alias = "test_alias"

                creation = PGliteDatabaseCreation(mock_connection)  # type: ignore

                # Mock manager with connection string containing special chars
                mock_manager = Mock()
                mock_config = Mock()
                mock_config.get_connection_string.return_value = "postgresql+psycopg://postgres:postgres@/postgres?host=/tmp/socket&dir"
                mock_manager.config = mock_config

                # Call method
                creation._update_connection_settings("test_schema", mock_manager)

                # Should handle special characters correctly
                assert mock_connection.settings_dict["HOST"] == "/tmp/socket"
