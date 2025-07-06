"""Django utilities for py-pglite."""

import os
import secrets
import tempfile

from pathlib import Path
from typing import Any


HAS_DJANGO = False
django: Any | None = None
settings: Any | None = None
call_command: Any | None = None
connection: Any | None = None

try:
    import django  # type: ignore

    from django.conf import settings  # type: ignore
    from django.core.management import call_command  # type: ignore
    from django.db import connection  # type: ignore

    HAS_DJANGO = True
except ImportError:
    # Django components will be None when Django is not available
    pass

from py_pglite.manager import PGliteManager


def create_django_test_database(manager: PGliteManager, verbosity: int = 1) -> str:
    """Create a Django test database using PGlite.

    Args:
        manager: PGlite manager instance
        verbosity: Verbosity level for output

    Returns:
        Test database name
    """
    if not HAS_DJANGO:
        raise ImportError(
            "Django is required for Django integration. "
            "Install with: pip install 'py-pglite[django]'"
        )

    if verbosity >= 1:
        pass

    # Start PGlite if not running
    if not manager.is_running():
        manager.start()
        manager.wait_for_ready()

    # Run migrations
    migrate_django_database(verbosity=verbosity)

    return "test_pglite_db"


def destroy_django_test_database(manager: PGliteManager, verbosity: int = 1) -> None:
    """Destroy the Django test database.

    Args:
        manager: PGlite manager instance
        verbosity: Verbosity level for output
    """
    if verbosity >= 1:
        pass

    # Stop PGlite
    manager.stop()


def migrate_django_database(verbosity: int = 1) -> None:
    """Run Django migrations on the PGlite database.

    Args:
        verbosity: Verbosity level for migration output
    """
    if not HAS_DJANGO:
        raise ImportError(
            "Django is required for Django integration. "
            "Install with: pip install 'py-pglite[django]'"
        )

    if call_command:
        try:
            call_command(
                "migrate",
                verbosity=verbosity,
                interactive=False,
                run_syncdb=True,
            )
        except Exception:
            if verbosity >= 1:
                pass


def flush_django_database(verbosity: int = 0) -> None:
    """Flush all data from Django database.

    Args:
        verbosity: Verbosity level for output
    """
    if not HAS_DJANGO:
        raise ImportError(
            "Django is required for Django integration. "
            "Install with: pip install 'py-pglite[django]'"
        )

    if call_command:
        try:
            call_command("flush", verbosity=verbosity, interactive=False)
        except Exception:
            if verbosity >= 1:
                pass


def configure_django_for_pglite(
    socket_path: str | None = None, **extra_settings: Any
) -> None:
    """Configure Django settings to use PGlite.

    Args:
        socket_path: Unix socket path for PGlite (auto-generated if None)
        **extra_settings: Additional Django settings
    """
    if not HAS_DJANGO:
        raise ImportError(
            "Django is required for Django integration. "
            "Install with: pip install 'py-pglite[django]'"
        )

    if settings and settings.configured:
        return

    # Generate secure socket path if not provided
    if socket_path is None:
        socket_dir = Path(tempfile.gettempdir()) / f"py-pglite-django-{os.getpid()}"
        socket_dir.mkdir(mode=0o700, exist_ok=True)  # Restrict to user only
        socket_path = str(socket_dir / ".s.PGSQL.5432")

    # Generate secure secret key
    secret_key = os.environ.get("DJANGO_SECRET_KEY") or secrets.token_urlsafe(50)

    default_settings = {
        "DEBUG": True,
        "DATABASES": {
            "default": {
                "ENGINE": "py_pglite.django.backend",
                "NAME": "postgres",
                "USER": "postgres",
                "PASSWORD": "postgres",
                "HOST": str(Path(socket_path).parent),  # Use socket directory as host
                "PORT": "",
                "OPTIONS": {
                    "host": str(Path(socket_path).parent),
                },
                "TEST": {
                    "NAME": "test_pglite_db",
                },
            }
        },
        "USE_TZ": True,
        "SECRET_KEY": secret_key,
        "INSTALLED_APPS": [
            "django.contrib.auth",
            "django.contrib.contenttypes",
            "django.contrib.sessions",
            "django.contrib.messages",
        ],
    }

    # Merge extra settings
    default_settings.update(extra_settings)

    if settings:
        settings.configure(**default_settings)
    if django:
        django.setup()


def get_django_connection_params(manager: PGliteManager) -> dict[str, Any]:
    """Get Django connection parameters for PGlite.

    Args:
        manager: PGlite manager instance

    Returns:
        Django database connection parameters
    """
    conn_str = manager.config.get_connection_string()

    # Extract socket directory from connection string
    socket_dir = (
        Path(tempfile.gettempdir()) / f"py-pglite-django-{os.getpid()}"
    )  # Default
    if "host=" in conn_str:
        socket_dir_str = conn_str.split("host=")[1].split("&")[0]
        socket_dir = Path(socket_dir_str)

    return {
        "ENGINE": "py_pglite.django.backend",
        "NAME": "postgres",
        "USER": "postgres",
        "PASSWORD": "postgres",
        "HOST": str(socket_dir),
        "PORT": "",
        "OPTIONS": {
            "host": str(socket_dir),
        },
        "TEST": {
            "NAME": "test_pglite_db",
        },
    }


def is_django_configured() -> bool:
    """Check if Django is configured.

    Returns:
        True if Django is configured, False otherwise
    """
    if not HAS_DJANGO or not settings:
        return False

    return settings.configured


def get_django_models() -> list[Any]:
    """Get all Django models from installed apps.

    Returns:
        List of Django model classes
    """
    if not HAS_DJANGO:
        raise ImportError(
            "Django is required for Django integration. "
            "Install with: pip install 'py-pglite[django]'"
        )

    from django.apps import apps  # type: ignore

    models = []
    for app_config in apps.get_app_configs():
        models.extend(app_config.get_models())

    return models


def create_django_superuser(
    username: str = "admin",
    email: str = "admin@example.com",
    password: str | None = None,
) -> Any:
    """Create a Django superuser for testing.

    Args:
        username: Username for the superuser
        email: Email for the superuser
        password: Password for the superuser (auto-generated if None)

    Returns:
        Created user instance
    """
    if not HAS_DJANGO:
        raise ImportError(
            "Django is required for Django integration. "
            "Install with: pip install 'py-pglite[django]'"
        )

    from django.contrib.auth import get_user_model

    User = get_user_model()  # noqa: N806

    # Generate secure password if not provided
    if password is None:
        password = os.environ.get("DJANGO_ADMIN_PASSWORD") or secrets.token_urlsafe(16)

    # Create superuser if it doesn't exist
    try:
        user = User.objects.get(username=username)
    except User.DoesNotExist:
        user = User.objects.create_superuser(
            username=username,
            email=email,
            password=password,
        )

    return user
