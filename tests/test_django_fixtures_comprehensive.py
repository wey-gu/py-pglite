"""Comprehensive tests for Django fixtures module."""

from unittest.mock import Mock
from unittest.mock import patch

import pytest


class TestDjangoImports:
    """Test Django import handling and error cases."""

    def test_has_django_flag_with_django_available(self):
        """Test that HAS_DJANGO is True when Django is available."""
        from py_pglite.django.fixtures import HAS_DJANGO

        # Since Django is available in the test environment, this should be True
        assert HAS_DJANGO is True

    def test_import_constants_are_set(self):
        """Test that Django components are properly imported when available."""
        from py_pglite.django import fixtures

        # When Django is available, these should be set
        assert fixtures.django is not None
        assert fixtures.settings is not None
        assert fixtures.call_command is not None
        assert fixtures.connection is not None


class TestDjangoInitImports:
    """Test Django __init__.py imports."""

    def test_django_init_imports(self):
        """Test that Django __init__.py imports work."""
        from py_pglite.django import configure_django_for_pglite
        from py_pglite.django import create_django_superuser
        from py_pglite.django import db
        from py_pglite.django import django_pglite_db
        from py_pglite.django import django_pglite_transactional_db
        from py_pglite.django import transactional_db

        # These should be importable
        assert db is not None
        assert django_pglite_db is not None
        assert django_pglite_transactional_db is not None
        assert transactional_db is not None
        assert configure_django_for_pglite is not None
        assert create_django_superuser is not None


class TestDjangoUtilsFunctionality:
    """Test Django utils module functionality."""

    def test_django_utils_has_django_flag(self):
        """Test that utils module correctly detects Django availability."""
        from py_pglite.django.utils import HAS_DJANGO

        assert HAS_DJANGO is True  # Django is available in test environment

    def test_create_django_test_database_without_django(self):
        """Test create_django_test_database raises error when Django unavailable."""
        from py_pglite.django.utils import create_django_test_database

        mock_manager = Mock()

        with patch("py_pglite.django.utils.HAS_DJANGO", False):
            with pytest.raises(ImportError, match="Django is required"):
                create_django_test_database(mock_manager)

    def test_create_django_test_database_success(self):
        """Test create_django_test_database functionality."""
        from py_pglite.django.utils import create_django_test_database

        mock_manager = Mock()
        mock_manager.is_running.return_value = False

        with (
            patch("py_pglite.django.utils.HAS_DJANGO", True),
            patch("py_pglite.django.utils.migrate_django_database") as mock_migrate,
        ):
            result = create_django_test_database(mock_manager, verbosity=0)

            assert result == "test_pglite_db"
            mock_manager.start.assert_called_once()
            mock_manager.wait_for_ready.assert_called_once()
            mock_migrate.assert_called_once_with(verbosity=0)

    def test_create_django_test_database_already_running(self):
        """Test create_django_test_database when manager already running."""
        from py_pglite.django.utils import create_django_test_database

        mock_manager = Mock()
        mock_manager.is_running.return_value = True

        with (
            patch("py_pglite.django.utils.HAS_DJANGO", True),
            patch("py_pglite.django.utils.migrate_django_database") as mock_migrate,
        ):
            create_django_test_database(mock_manager, verbosity=0)

            # Should not start if already running
            mock_manager.start.assert_not_called()
            mock_manager.wait_for_ready.assert_not_called()
            mock_migrate.assert_called_once()

    def test_destroy_django_test_database(self):
        """Test destroy_django_test_database functionality."""
        from py_pglite.django.utils import destroy_django_test_database

        mock_manager = Mock()

        destroy_django_test_database(mock_manager, verbosity=0)

        mock_manager.stop.assert_called_once()

    def test_migrate_django_database_without_django(self):
        """Test migrate_django_database raises error when Django unavailable."""
        from py_pglite.django.utils import migrate_django_database

        with patch("py_pglite.django.utils.HAS_DJANGO", False):
            with pytest.raises(ImportError, match="Django is required"):
                migrate_django_database()

    def test_migrate_django_database_success(self):
        """Test migrate_django_database functionality."""
        from py_pglite.django.utils import migrate_django_database

        mock_call_command = Mock()

        with (
            patch("py_pglite.django.utils.HAS_DJANGO", True),
            patch("py_pglite.django.utils.call_command", mock_call_command),
        ):
            migrate_django_database(verbosity=0)

            mock_call_command.assert_called_once_with(
                "migrate",
                verbosity=0,
                interactive=False,
                run_syncdb=True,
            )

    def test_migrate_django_database_handles_errors(self):
        """Test migrate_django_database handles migration errors gracefully."""
        from py_pglite.django.utils import migrate_django_database

        mock_call_command = Mock(side_effect=Exception("Migration failed"))

        with (
            patch("py_pglite.django.utils.HAS_DJANGO", True),
            patch("py_pglite.django.utils.call_command", mock_call_command),
        ):
            # Should not raise exception
            migrate_django_database(verbosity=0)

            mock_call_command.assert_called_once()

    def test_flush_django_database_without_django(self):
        """Test flush_django_database raises error when Django unavailable."""
        from py_pglite.django.utils import flush_django_database

        with patch("py_pglite.django.utils.HAS_DJANGO", False):
            with pytest.raises(ImportError, match="Django is required"):
                flush_django_database()

    def test_flush_django_database_success(self):
        """Test flush_django_database functionality."""
        from py_pglite.django.utils import flush_django_database

        mock_call_command = Mock()

        with (
            patch("py_pglite.django.utils.HAS_DJANGO", True),
            patch("py_pglite.django.utils.call_command", mock_call_command),
        ):
            flush_django_database(verbosity=0)

            mock_call_command.assert_called_once_with(
                "flush",
                verbosity=0,
                interactive=False,
            )

    def test_flush_django_database_handles_errors(self):
        """Test flush_django_database handles errors gracefully."""
        from py_pglite.django.utils import flush_django_database

        mock_call_command = Mock(side_effect=Exception("Flush failed"))

        with (
            patch("py_pglite.django.utils.HAS_DJANGO", True),
            patch("py_pglite.django.utils.call_command", mock_call_command),
        ):
            # Should not raise exception
            flush_django_database(verbosity=0)

            mock_call_command.assert_called_once()

    def test_configure_django_for_pglite_without_django(self):
        """Test configure_django_for_pglite raises error when Django unavailable."""
        from py_pglite.django.utils import configure_django_for_pglite

        with patch("py_pglite.django.utils.HAS_DJANGO", False):
            with pytest.raises(ImportError, match="Django is required"):
                configure_django_for_pglite()

    def test_configure_django_for_pglite_already_configured(self):
        """Test configure_django_for_pglite when Django already configured."""
        from py_pglite.django.utils import configure_django_for_pglite

        mock_settings = Mock()
        mock_settings.configured = True
        mock_django = Mock()

        with (
            patch("py_pglite.django.utils.HAS_DJANGO", True),
            patch("py_pglite.django.utils.settings", mock_settings),
            patch("py_pglite.django.utils.django", mock_django),
        ):
            configure_django_for_pglite()

            # Should return early if configured
            mock_settings.configure.assert_not_called()
            mock_django.setup.assert_not_called()

    def test_configure_django_for_pglite_success(self):
        """Test configure_django_for_pglite configuration."""
        from py_pglite.django.utils import configure_django_for_pglite

        mock_settings = Mock()
        mock_settings.configured = False
        mock_django = Mock()

        with (
            patch("py_pglite.django.utils.HAS_DJANGO", True),
            patch("py_pglite.django.utils.settings", mock_settings),
            patch("py_pglite.django.utils.django", mock_django),
            patch.dict("os.environ", {}, clear=True),
        ):
            configure_django_for_pglite(socket_path="/tmp/test_socket")

            mock_settings.configure.assert_called_once()
            mock_django.setup.assert_called_once()

            # Check configuration
            call_args = mock_settings.configure.call_args
            db_config = call_args[1]["DATABASES"]["default"]
            assert db_config["ENGINE"] == "py_pglite.django.backend"
            assert db_config["USER"] == "postgres"

    def test_configure_django_for_pglite_with_extra_settings(self):
        """Test configure_django_for_pglite with extra settings."""
        from py_pglite.django.utils import configure_django_for_pglite

        mock_settings = Mock()
        mock_settings.configured = False
        mock_django = Mock()

        with (
            patch("py_pglite.django.utils.HAS_DJANGO", True),
            patch("py_pglite.django.utils.settings", mock_settings),
            patch("py_pglite.django.utils.django", mock_django),
            patch.dict("os.environ", {}, clear=True),
        ):
            configure_django_for_pglite(CUSTOM_SETTING="test_value", DEBUG=False)

            call_args = mock_settings.configure.call_args
            assert call_args[1]["CUSTOM_SETTING"] == "test_value"
            assert call_args[1]["DEBUG"] is False

    def test_get_django_connection_params(self):
        """Test get_django_connection_params functionality."""
        from py_pglite.django.utils import get_django_connection_params

        mock_manager = Mock()
        mock_manager.config.get_connection_string.return_value = (
            "postgresql://user:pass@host=/tmp/test_socket&port=5432/db"
        )

        params = get_django_connection_params(mock_manager)

        assert params["ENGINE"] == "py_pglite.django.backend"
        assert params["NAME"] == "postgres"
        assert params["USER"] == "postgres"
        assert params["PASSWORD"] == "postgres"
        assert params["HOST"] == "/tmp/test_socket"

    def test_is_django_configured_without_django(self):
        """Test is_django_configured when Django unavailable."""
        from py_pglite.django.utils import is_django_configured

        with patch("py_pglite.django.utils.HAS_DJANGO", False):
            assert is_django_configured() is False

    def test_is_django_configured_success(self):
        """Test is_django_configured functionality."""
        from py_pglite.django.utils import is_django_configured

        mock_settings = Mock()
        mock_settings.configured = True

        with (
            patch("py_pglite.django.utils.HAS_DJANGO", True),
            patch("py_pglite.django.utils.settings", mock_settings),
        ):
            assert is_django_configured() is True

    def test_is_django_configured_not_configured(self):
        """Test is_django_configured when Django not configured."""
        from py_pglite.django.utils import is_django_configured

        mock_settings = Mock()
        mock_settings.configured = False

        with (
            patch("py_pglite.django.utils.HAS_DJANGO", True),
            patch("py_pglite.django.utils.settings", mock_settings),
        ):
            assert is_django_configured() is False

    def test_get_django_models_without_django(self):
        """Test get_django_models raises error when Django unavailable."""
        from py_pglite.django.utils import get_django_models

        with patch("py_pglite.django.utils.HAS_DJANGO", False):
            with pytest.raises(ImportError, match="Django is required"):
                get_django_models()

    def test_get_django_models_success(self):
        """Test get_django_models functionality."""
        from py_pglite.django.utils import get_django_models

        mock_model1 = Mock()
        mock_model2 = Mock()
        mock_app_config = Mock()
        mock_app_config.get_models.return_value = [mock_model1, mock_model2]
        mock_apps = Mock()
        mock_apps.get_app_configs.return_value = [mock_app_config]

        with (
            patch("py_pglite.django.utils.HAS_DJANGO", True),
            patch("django.apps.apps", mock_apps),
        ):
            models = get_django_models()

            assert models == [mock_model1, mock_model2]
            mock_apps.get_app_configs.assert_called_once()

    def test_create_django_superuser_without_django(self):
        """Test create_django_superuser raises error when Django unavailable."""
        from py_pglite.django.utils import create_django_superuser

        with patch("py_pglite.django.utils.HAS_DJANGO", False):
            with pytest.raises(ImportError, match="Django is required"):
                create_django_superuser()

    def test_create_django_superuser_new_user(self):
        """Test create_django_superuser creates new user."""
        from py_pglite.django.utils import create_django_superuser

        # Create a proper DoesNotExist exception class
        class DoesNotExist(Exception):
            pass

        mock_user_model = Mock()
        mock_user_model.DoesNotExist = DoesNotExist
        mock_user = Mock()
        mock_user_model.objects.get.side_effect = DoesNotExist()
        mock_user_model.objects.create_superuser.return_value = mock_user
        mock_get_user_model = Mock(return_value=mock_user_model)

        with (
            patch("py_pglite.django.utils.HAS_DJANGO", True),
            patch("django.contrib.auth.get_user_model", mock_get_user_model),
            patch.dict("os.environ", {}, clear=True),
        ):
            result = create_django_superuser(
                username="testadmin", email="test@example.com"
            )

            assert result is mock_user
            mock_user_model.objects.create_superuser.assert_called_once()

            # Verify the call arguments
            call_args = mock_user_model.objects.create_superuser.call_args
            assert call_args[1]["username"] == "testadmin"
            assert call_args[1]["email"] == "test@example.com"
            assert isinstance(
                call_args[1]["password"], str
            )  # Password should be generated

    def test_create_django_superuser_existing_user(self):
        """Test create_django_superuser with existing user."""
        from py_pglite.django.utils import create_django_superuser

        mock_user_model = Mock()
        mock_existing_user = Mock()
        mock_user_model.objects.get.return_value = mock_existing_user
        mock_get_user_model = Mock(return_value=mock_user_model)

        with (
            patch("py_pglite.django.utils.HAS_DJANGO", True),
            patch("django.contrib.auth.get_user_model", mock_get_user_model),
        ):
            result = create_django_superuser()

            assert result is mock_existing_user
            mock_user_model.objects.create_superuser.assert_not_called()

    def test_create_django_superuser_with_env_password(self):
        """Test create_django_superuser uses environment password."""
        from py_pglite.django.utils import create_django_superuser

        # Create a proper DoesNotExist exception class
        class DoesNotExist(Exception):
            pass

        mock_user_model = Mock()
        mock_user_model.DoesNotExist = DoesNotExist
        mock_user = Mock()
        mock_user_model.objects.get.side_effect = DoesNotExist()
        mock_user_model.objects.create_superuser.return_value = mock_user
        mock_get_user_model = Mock(return_value=mock_user_model)
        test_password = "env-admin-password"

        with (
            patch("py_pglite.django.utils.HAS_DJANGO", True),
            patch("django.contrib.auth.get_user_model", mock_get_user_model),
            patch.dict("os.environ", {"DJANGO_ADMIN_PASSWORD": test_password}),
        ):
            create_django_superuser()

            call_args = mock_user_model.objects.create_superuser.call_args
            assert call_args[1]["password"] == test_password
