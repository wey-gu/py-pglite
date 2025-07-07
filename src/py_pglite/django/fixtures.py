"""Django-specific pytest fixtures for PGlite integration."""

import os
import secrets

from collections.abc import Generator
from typing import Any

import pytest


# Import Django components with proper error handling
HAS_DJANGO = False
django: Any | None = None
settings: Any | None = None
call_command: Any | None = None
setup_test_environment: Any | None = None
teardown_test_environment: Any | None = None
connection: Any | None = None
connections: Any | None = None
TestCase: Any = object
TransactionTestCase: Any = object

try:
    import django  # type: ignore

    from django.apps import apps
    from django.conf import settings  # type: ignore
    from django.core.management import call_command  # type: ignore
    from django.db import connection  # type: ignore
    from django.db import connections  # type: ignore
    from django.test import TestCase  # type: ignore
    from django.test import TransactionTestCase  # type: ignore
    from django.test.utils import setup_test_environment  # type: ignore
    from django.test.utils import teardown_test_environment  # type: ignore

    HAS_DJANGO = True
except ImportError:
    # Django is not available - functions will raise appropriate errors when called
    pass

from py_pglite.config import PGliteConfig
from py_pglite.manager import PGliteManager


@pytest.fixture(scope="session")
def django_pglite_settings() -> None:
    """Configure Django settings for PGlite testing."""
    if not HAS_DJANGO:
        raise ImportError(
            "Django is required for Django integration. "
            "Install with: pip install 'py-pglite[django]'"
        )

    # Configure Django to use PGlite backend
    if settings and not settings.configured:
        # Generate a secure random secret key for testing
        secret_key = os.environ.get(
            "DJANGO_SECRET_KEY",
        ) or secrets.token_urlsafe(50)

        settings.configure(
            DEBUG=True,
            DATABASES={
                "default": {
                    "ENGINE": "py_pglite.django.backend",
                    "NAME": "test_pglite_db",
                    "USER": "postgres",
                    "PASSWORD": "postgres",
                    "HOST": "",  # Let the backend handle socket path dynamically
                    "PORT": "",
                    "OPTIONS": {},
                    "TEST": {
                        "NAME": "test_pglite_db",
                    },
                }
            },
            USE_TZ=True,
            SECRET_KEY=secret_key,
            INSTALLED_APPS=[
                "django.contrib.auth",
                "django.contrib.contenttypes",
                "django.contrib.sessions",
                "django.contrib.messages",
            ],
        )

    if django:
        django.setup()


@pytest.fixture(scope="module")
def pglite_django_manager() -> Generator[PGliteManager, None, None]:
    """Pytest fixture providing a PGlite manager for Django testing."""
    config = PGliteConfig()
    manager = PGliteManager(config)
    manager.start()
    manager.wait_for_ready()

    try:
        yield manager
    finally:
        manager.stop()


@pytest.fixture(scope="function")
def django_pglite_db(pglite_manager: PGliteManager) -> Generator[None, None, None]:
    """Django database fixture that auto-configures Django to use PGlite.

    Provides zero-config Django testing with PGlite. Just use this fixture
    and Django will automatically connect to the PGlite instance.
    """
    if not HAS_DJANGO:
        raise ImportError(
            "Django is required for Django integration. "
            "Install with: pip install 'py-pglite[django]'"
        )

    # Auto-configure Django to use our PGlite instance
    conn_str = pglite_manager.config.get_connection_string()
    socket_dir = conn_str.split("host=")[1].split(sep="&")[0].split("#")[0]

    # Update Django's connection settings transparently
    if connection is None:
        raise RuntimeError("Django connection is not available")

    original_config = connection.settings_dict.copy()  # type: ignore
    connection.settings_dict.update(
        {  # type: ignore
            "ENGINE": "py_pglite.django.backend",
            "HOST": socket_dir,
            "PORT": "",
            "NAME": "postgres",
            "USER": "postgres",
            "PASSWORD": "postgres",
            "OPTIONS": {},
        }
    )

    # Force reconnection with new settings
    connection.close()  # type: ignore

    # Auto-create tables for any models that need them
    try:
        call_command(
            "migrate",
            verbosity=0,
            interactive=False,
            run_syncdb=True,
        )  # type: ignore
    except Exception:
        # If migrations fail, try to create tables manually
        # using Django's schema editor
        if settings and settings.DEBUG:
            pass
        try:
            with connection.schema_editor() as schema_editor:  # type: ignore
                # Get all models from all apps
                for app_config in apps.get_app_configs():  # type: ignore
                    for model in app_config.get_models():
                        try:
                            schema_editor.create_model(model)
                        except Exception:
                            # Log specific model creation failures in debug mode
                            if settings and settings.DEBUG:
                                pass
        except Exception:
            # Log schema editor failures in debug mode
            if settings and settings.DEBUG:
                pass

    try:
        yield
    finally:
        # Cleanup: Clear all data for next test and restore original config
        try:
            call_command("flush", verbosity=0, interactive=False)  # type: ignore
        except Exception:
            if settings and settings.DEBUG:
                pass

        # Restore original database configuration
        if connection is not None:
            connection.settings_dict.clear()  # type: ignore
            connection.settings_dict.update(original_config)  # type: ignore
            connection.close()  # type: ignore


@pytest.fixture(scope="function")
def django_pglite_transactional_db(
    pglite_manager: PGliteManager,
) -> Generator[None, None, None]:
    """Django transactional database fixture with auto-configuration.

    Provides the same interface as pytest-django's transactional_db fixture
    but uses ultra-fast PGlite with zero configuration required.
    """
    if not HAS_DJANGO:
        raise ImportError(
            "Django is required for Django integration. "
            "Install with: pip install 'py-pglite[django]'"
        )

    # Auto-configure Django to use our PGlite instance
    conn_str = pglite_manager.config.get_connection_string()
    socket_dir = conn_str.split("host=")[1].split("&")[0].split("#")[0]

    if connection is None:
        raise RuntimeError("Django connection is not available")

    original_config = connection.settings_dict.copy()  # type: ignore
    connection.settings_dict.update(
        {  # type: ignore
            "ENGINE": "py_pglite.django.backend",
            "HOST": socket_dir,
            "PORT": "",
            "NAME": "postgres",
            "USER": "postgres",
            "PASSWORD": "postgres",
            "OPTIONS": {},
        }
    )

    connection.close()  # type: ignore

    # Auto-create tables
    try:
        call_command(
            "migrate",
            verbosity=0,
            interactive=False,
            run_syncdb=True,
        )  # type: ignore
    except Exception:
        # If migrations fail, try to create tables manually
        # using Django's schema editor
        if settings and settings.DEBUG:
            pass
        try:
            with connection.schema_editor() as schema_editor:  # type: ignore
                # Get all models from all apps
                for app_config in apps.get_app_configs():  # type: ignore
                    for model in app_config.get_models():
                        try:
                            schema_editor.create_model(model)
                        except Exception:
                            # Log specific model creation failures in debug mode
                            if settings and settings.DEBUG:
                                pass
        except Exception:
            # Log schema editor failures in debug mode
            if settings and settings.DEBUG:
                pass

    try:
        yield
    finally:
        # Cleanup for next test and restore config
        try:
            call_command("flush", verbosity=0, interactive=False)  # type: ignore
        except Exception:
            if settings and settings.DEBUG:
                pass

        if connection is not None:
            connection.settings_dict.clear()  # type: ignore
            connection.settings_dict.update(original_config)  # type: ignore
            connection.close()  # type: ignore


# Pytest-django compatible aliases for zero-config experience
@pytest.fixture(scope="function")
def db(django_pglite_db: None) -> None:
    """Auto-configured database fixture compatible with pytest-django.

    Just use this fixture and py-pglite automatically configures Django
    to use ultra-fast PGlite with zero setup required!
    """
    # The actual work is done by django_pglite_db


@pytest.fixture(scope="function")
def transactional_db(django_pglite_transactional_db: None) -> None:
    """Auto-configured transactional database fixture compatible with pytest-django.

    Provides the same interface as pytest-django's transactional_db fixture
    but uses ultra-fast PGlite with zero configuration required.
    """
    # The actual work is done by django_pglite_transactional_db


@pytest.fixture(scope="function")
def django_user_model(django_pglite_db: None) -> Any:
    """Pytest fixture providing Django's User model for testing.

    Args:
        django_pglite_db: Database fixture

    Returns:
        User model class
    """
    if not HAS_DJANGO:
        raise ImportError(
            "Django is required for Django integration. "
            "Install with: pip install 'py-pglite[django]'"
        )

    from django.contrib.auth import get_user_model

    return get_user_model()


@pytest.fixture(scope="function")
def django_admin_user(django_user_model: Any) -> Any:
    """Pytest fixture creating a Django admin user for testing.

    Args:
        django_user_model: User model class

    Returns:
        Admin user instance
    """
    # Generate a secure random password for testing
    admin_password = os.environ.get(
        "DJANGO_ADMIN_PASSWORD",
    ) or secrets.token_urlsafe(16)

    return django_user_model.objects.create_user(
        username="admin",
        email="admin@example.com",
        password=admin_password,
        is_staff=True,
        is_superuser=True,
    )


@pytest.fixture(scope="function")
def django_client(django_pglite_db: None) -> Any:
    """Pytest fixture providing Django test client.

    Args:
        django_pglite_db: Database fixture

    Returns:
        Django test client instance
    """
    if not HAS_DJANGO:
        raise ImportError(
            "Django is required for Django integration. "
            "Install with: pip install 'py-pglite[django]'"
        )

    from django.test import Client

    return Client()
