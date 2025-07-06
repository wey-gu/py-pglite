"""Django database backend base module for PGlite integration."""
# mypy: disable-error-code=import-untyped,attr-defined,misc,no-any-return

import threading
import time
import uuid

from typing import Any

from py_pglite.config import PGliteConfig
from py_pglite.manager import PGliteManager


# Import Django components with error handling
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


# Global registry for PGlite managers
_pglite_managers: dict[str, PGliteManager] = {}
_manager_lock = threading.Lock()


class PGliteDatabaseCreation(DatabaseCreation):  # type: ignore
    """Database creation class for PGlite backend."""

    def _create_test_db(
        self, verbosity: int = 1, autoclobber: bool = False, keepdb: bool = False
    ) -> str:
        """Create a test database using PGlite.

        Note: PGlite doesn't support CREATE DATABASE, so we use schemas for isolation.
        """
        test_database_name = self._get_test_db_name()  # type: ignore

        if verbosity >= 1:
            print(f"Creating test schema '{test_database_name}' using PGlite...")

        # Get or create PGlite manager for this database
        manager = self._get_pglite_manager(test_database_name)

        # Start PGlite if not already running
        if not manager.is_running():
            manager.start()
            # Give the socket a moment to be fully ready
            time.sleep(1)

        # Update connection settings to use PGlite
        self._update_connection_settings(test_database_name, manager)

        # Store the test database name so other methods can access it
        self.connection._test_database_name = test_database_name  # type: ignore

        # Create a schema for test isolation instead of a database
        self._create_test_schema(test_database_name, verbosity)

        # Run migrations
        self._run_migrations(verbosity)

        return test_database_name

    def _create_test_schema(self, schema_name: str, verbosity: int = 1) -> None:
        """Create a test schema for isolation since PGlite doesn't support CREATE DATABASE."""
        try:
            # Get the PGlite manager
            with _manager_lock:
                manager = _pglite_managers.get(schema_name)
                if not manager:
                    return

            # Use framework-agnostic utilities instead of SQLAlchemy
            from ...utils import execute_sql

            conn_str = manager.config.get_connection_string()

            # Create schema for test isolation
            result = execute_sql(
                conn_str, f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'
            )
            if result is not None:
                if verbosity >= 1:
                    print(f"✅ Created test schema: {schema_name}")
            else:
                if verbosity >= 1:
                    print(f"Schema creation warning for {schema_name}")

        except Exception as e:
            if verbosity >= 1:
                print(f"Schema setup failed: {e}")
            # Continue anyway - we'll use the default schema

    def _destroy_test_db(
        self, test_database_name: str, verbosity: int = 1, keepdb: bool = False
    ) -> None:
        """Destroy the test database."""
        if verbosity >= 1:
            print(f"Destroying test schema '{test_database_name}'...")

        # Clean up the schema first
        self._destroy_test_schema(test_database_name, verbosity)

        # Stop and cleanup PGlite manager
        with _manager_lock:
            manager = _pglite_managers.pop(test_database_name, None)
            if manager:
                manager.stop()

    def _destroy_test_schema(self, schema_name: str, verbosity: int = 1) -> None:
        """Destroy the test schema."""
        try:
            # Get the PGlite manager
            with _manager_lock:
                manager = _pglite_managers.get(schema_name)
                if not manager:
                    return

            # Use framework-agnostic utilities instead of SQLAlchemy
            from ...utils import execute_sql

            conn_str = manager.config.get_connection_string()

            # Drop schema with cascade to remove all objects
            result = execute_sql(
                conn_str, f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'
            )
            if result is not None:
                if verbosity >= 1:
                    print(f"✅ Destroyed test schema: {schema_name}")
            else:
                if verbosity >= 1:
                    print(f"Schema cleanup warning for {schema_name}")

        except Exception as e:
            if verbosity >= 1:
                print(f"Schema cleanup failed: {e}")
            # Continue anyway

    def _get_pglite_manager(self, db_name: str) -> PGliteManager:
        """Get or create a PGlite manager for the given database name."""
        with _manager_lock:
            if db_name not in _pglite_managers:
                # Create unique socket directory for this database
                config = PGliteConfig()
                import tempfile

                from pathlib import Path

                # Create unique socket directory but use standard socket name
                socket_dir = (
                    Path(tempfile.gettempdir())
                    / f"py-pglite-{db_name}-{uuid.uuid4().hex[:8]}"
                )
                socket_dir.mkdir(mode=0o700, exist_ok=True)
                config.socket_path = str(socket_dir / ".s.PGSQL.5432")

                _pglite_managers[db_name] = PGliteManager(config)

            return _pglite_managers[db_name]

    def _update_connection_settings(self, db_name: str, manager: PGliteManager) -> None:
        """Update Django connection settings to use PGlite."""
        # Get the connection settings
        db_settings = self.connection.settings_dict.copy()  # type: ignore

        # Parse PGlite connection string
        conn_str = manager.config.get_connection_string()
        # postgresql+psycopg://postgres:postgres@/postgres?host=/tmp/py-pglite-test-abc123

        # Extract socket directory from connection string
        if "host=" in conn_str:
            # Split by 'host=' and get the socket directory
            socket_dir = conn_str.split("host=")[1].split("&")[0].split("#")[0]

            # Update Django database settings to use Unix socket directory
            # psycopg will automatically look for .s.PGSQL.5432 in this directory
            # Always use 'postgres' database since PGlite only supports that
            db_settings.update(
                {
                    "HOST": socket_dir,
                    "PORT": "",
                    "NAME": "postgres",  # PGlite only has 'postgres' database
                    "USER": "postgres",
                    "PASSWORD": "postgres",
                    "OPTIONS": {
                        "options": f"-c search_path={db_name},public"  # Use schema for isolation
                    },
                }
            )

            # Update the connection's settings_dict directly
            self.connection.settings_dict.update(db_settings)  # type: ignore

            # Force connection to close and reconnect with new settings
            self.connection.close()  # type: ignore

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


class PGliteDatabaseWrapper(base.DatabaseWrapper):  # type: ignore
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

        # Set up parent class
        self.settings_dict = settings_dict
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
                        socket_dir = (
                            conn_str.split("host=")[1].split("&")[0].split("#")[0]
                        )
                        # Map any Django database name to PGlite's 'postgres' database
                        # but use schema for isolation
                        conn_params.update(
                            {
                                "host": socket_dir,  # psycopg will look for .s.PGSQL.5432 here
                                "port": None,
                                "dbname": "postgres",  # Always use 'postgres' in PGlite
                                "user": "postgres",
                                "password": "postgres",
                                "options": f"-c search_path={db_name},public",  # Schema isolation
                            }
                        )

        # Call parent class's method using super()
        return super().get_new_connection(conn_params)  # type: ignore

    def get_database_version(self):
        """
        Return the database version as a tuple.
        PGlite is compatible with PostgreSQL 15.0.
        """
        return (15, 0)  # Report as PostgreSQL 15.0 for Django compatibility


# Registry function for easy access
def get_pglite_manager(alias: str = "default") -> PGliteManager | None:
    """Get the PGlite manager for a given database alias."""
    with _manager_lock:
        # Find manager by database alias or name
        for db_name, manager in _pglite_managers.items():
            if alias in db_name or db_name == alias:
                return manager
    return None


# For Django compatibility, expose DatabaseWrapper as the main class
DatabaseWrapper = PGliteDatabaseWrapper
