"""Django database backend for PGlite integration.

This module provides a Django database backend that uses PGlite for testing.
It should be used as: 'py_pglite.django.backend'
"""
# mypy: disable-error-code=import-untyped,attr-defined,misc,no-any-return

import os
import tempfile
import threading
import uuid
from pathlib import Path
from typing import Any

try:
    from django.conf import settings  # type: ignore
    from django.core.management import call_command  # type: ignore
    from django.db import connections  # type: ignore
    from django.db.backends.postgresql import base  # type: ignore
    from django.db.backends.postgresql.creation import DatabaseCreation  # type: ignore

    HAS_DJANGO = True
except ImportError:
    HAS_DJANGO = False

    # Create dummy classes for type hints when Django is not available
    class base:  # type: ignore
        DatabaseWrapper = object

    class DatabaseCreation:  # type: ignore
        pass


from ..config import PGliteConfig
from ..manager import PGliteManager

# Global registry for PGlite managers
_pglite_managers: dict[str, PGliteManager] = {}
_manager_lock = threading.Lock()


class PGliteDatabaseCreation(DatabaseCreation):  # type: ignore
    """Database creation class for PGlite backend."""

    def _create_test_db(
        self, verbosity: int = 1, autoclobber: bool = False, keepdb: bool = False
    ) -> str:
        """Create a test database using PGlite."""
        test_database_name = self._get_test_db_name()  # type: ignore

        if verbosity >= 1:
            print(f"Creating test database '{test_database_name}' using PGlite...")

        # Get or create PGlite manager for this database
        manager = self._get_pglite_manager(test_database_name)

        # Start PGlite if not already running
        if not manager.is_running():
            manager.start()
            manager.wait_for_ready()

        # Update connection settings to use PGlite
        self._update_connection_settings(test_database_name, manager)

        # Run migrations
        self._run_migrations(verbosity)

        return test_database_name

    def _destroy_test_db(
        self, test_database_name: str, verbosity: int = 1, keepdb: bool = False
    ) -> None:
        """Destroy the test database."""
        if verbosity >= 1:
            print(f"Destroying test database '{test_database_name}'...")

        # Stop and cleanup PGlite manager
        with _manager_lock:
            manager = _pglite_managers.pop(test_database_name, None)
            if manager:
                manager.stop()

    def _get_pglite_manager(self, db_name: str) -> PGliteManager:
        """Get or create a PGlite manager for the given database name."""
        with _manager_lock:
            if db_name not in _pglite_managers:
                # Create unique socket directory for this database
                config = PGliteConfig()
                socket_dir = (
                    Path(tempfile.gettempdir())
                    / f"py-pglite-django-{db_name}-{uuid.uuid4().hex[:8]}"
                )
                socket_dir.mkdir(mode=0o700, exist_ok=True)  # Restrict to user only
                config.socket_path = str(socket_dir / ".s.PGSQL.5432")
                _pglite_managers[db_name] = PGliteManager(config)

            return _pglite_managers[db_name]

    def _update_connection_settings(self, db_name: str, manager: PGliteManager) -> None:
        """Update Django connection settings to use PGlite."""
        # Get the connection settings
        db_settings = self.connection.settings_dict.copy()  # type: ignore

        # Parse PGlite connection string
        conn_str = manager.config.get_connection_string()
        # postgresql+psycopg://postgres:postgres@/postgres?host=/tmp/pglite_socket.sock

        # Extract socket path from connection string
        if "host=" in conn_str:
            socket_path = conn_str.split("host=")[1].split("&")[0]

            # Update Django database settings
            db_settings.update(
                {
                    "HOST": socket_path,
                    "PORT": "",
                    "NAME": "postgres",
                    "USER": "postgres",
                    "PASSWORD": "postgres",
                    "OPTIONS": {
                        "host": socket_path,
                    },
                }
            )

        # Update the connection
        from django.db import connections

        connections.databases[self.connection.alias] = db_settings  # type: ignore

        # Close and recreate connection
        self.connection.close()  # type: ignore
        connections[self.connection.alias] = self.connection.__class__(  # type: ignore
            db_settings,
            self.connection.alias,  # type: ignore
        )

    def _run_migrations(self, verbosity: int = 1) -> None:
        """Run Django migrations."""
        try:
            call_command(  # type: ignore
                "migrate",
                verbosity=verbosity,
                interactive=False,
                database=self.connection.alias,  # type: ignore
                run_syncdb=True,
            )
        except Exception as e:
            if verbosity >= 1:
                print(f"Migration warning: {e}")
            # Continue anyway - migrations might fail but tables might still be created


class PGliteDatabaseWrapper(base.DatabaseWrapper):
    """Database wrapper for PGlite integration."""

    def __init__(self, settings_dict: dict[str, Any], alias: str = "default"):
        """Initialize PGlite database wrapper."""
        if not HAS_DJANGO:
            raise ImportError(
                "Django is required for Django integration. "
                "Install with: pip install 'py-pglite[django]'"
            )

        # Ensure we use the PGlite creation class
        settings_dict = settings_dict.copy()

        super().__init__(settings_dict, alias)  # type: ignore
        self.creation = PGliteDatabaseCreation(self)  # type: ignore

    def get_new_connection(self, conn_params: dict[str, Any]) -> Any:
        """Get a new database connection."""
        # If we're in a test and using PGlite, adjust connection params
        if hasattr(self, "_test_database_name"):
            # Use PGlite manager's connection params
            db_name = getattr(self, "_test_database_name", "test_db")
            with _manager_lock:
                manager = _pglite_managers.get(db_name)
                if manager:
                    # Update connection params for PGlite
                    conn_str = manager.config.get_connection_string()
                    if "host=" in conn_str:
                        socket_path = conn_str.split("host=")[1].split("&")[0]
                        conn_params.update(
                            {
                                "host": socket_path,
                                "port": None,
                                "database": "postgres",
                                "user": "postgres",
                                "password": "postgres",
                            }
                        )

        return super().get_new_connection(conn_params)  # type: ignore


# Registry function for easy access
def get_pglite_manager(alias: str = "default") -> PGliteManager | None:
    """Get the PGlite manager for a given database alias."""
    with _manager_lock:
        # Find manager by database alias or name
        for db_name, manager in _pglite_managers.items():
            if alias in db_name or db_name == alias:
                return manager
    return None
