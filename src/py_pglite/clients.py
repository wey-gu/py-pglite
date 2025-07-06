"""Database client abstraction for py-pglite.

Provides unified interface for both psycopg and asyncpg clients,
allowing users to choose their preferred PostgreSQL driver.
"""

import logging
from abc import ABC, abstractmethod
from typing import Any

logger = logging.getLogger(__name__)


class DatabaseClient(ABC):
    """Abstract database client interface."""

    @abstractmethod
    def connect(self, connection_string: str) -> Any:
        """Create a connection to the database."""
        pass

    @abstractmethod
    def execute_query(
        self, connection: Any, query: str, params: Any = None
    ) -> list[tuple]:
        """Execute a query and return results."""
        pass

    @abstractmethod
    def test_connection(self, connection_string: str) -> bool:
        """Test if database connection is working."""
        pass

    @abstractmethod
    def get_database_version(self, connection_string: str) -> str | None:
        """Get PostgreSQL version string."""
        pass

    @abstractmethod
    def close_connection(self, connection: Any) -> None:
        """Close a database connection."""
        pass


class PsycopgClient(DatabaseClient):
    """psycopg-based database client."""

    def __init__(self):
        try:
            import psycopg

            self._psycopg = psycopg
        except ImportError as e:
            raise ImportError(
                "psycopg is required for PsycopgClient. "
                "Install with: pip install psycopg[binary]"
            ) from e

    def connect(self, connection_string: str) -> Any:
        """Create a psycopg connection."""
        return self._psycopg.connect(connection_string)

    def execute_query(
        self, connection: Any, query: str, params: Any = None
    ) -> list[tuple]:
        """Execute query using psycopg."""
        with connection.cursor() as cur:
            if params:
                cur.execute(query, params)
            else:
                cur.execute(query)

            try:
                return cur.fetchall()
            except self._psycopg.ProgrammingError:
                # Not a SELECT query, return empty list to indicate success
                return []

    def test_connection(self, connection_string: str) -> bool:
        """Test psycopg connection."""
        try:
            with self.connect(connection_string) as conn:
                result = self.execute_query(conn, "SELECT 1")
                return len(result) > 0 and result[0][0] == 1
        except Exception as e:
            logger.warning(f"psycopg connection test failed: {e}")
            return False

    def get_database_version(self, connection_string: str) -> str | None:
        """Get PostgreSQL version using psycopg."""
        try:
            with self.connect(connection_string) as conn:
                result = self.execute_query(conn, "SELECT version()")
                return result[0][0] if result else None
        except Exception as e:
            logger.warning(f"Failed to get database version via psycopg: {e}")
            return None

    def close_connection(self, connection: Any) -> None:
        """Close psycopg connection."""
        if connection and not connection.closed:
            connection.close()


class AsyncpgClient(DatabaseClient):
    """asyncpg-based database client."""

    def __init__(self):
        try:
            import asyncio

            import asyncpg

            self._asyncpg = asyncpg
            self._asyncio = asyncio
        except ImportError as e:
            raise ImportError(
                "asyncpg is required for AsyncpgClient. "
                "Install with: pip install asyncpg"
            ) from e

    def connect(self, connection_string: str) -> Any:
        """Create an asyncpg connection (sync wrapper)."""
        loop = self._get_event_loop()
        return loop.run_until_complete(self._asyncpg.connect(connection_string))

    def execute_query(
        self, connection: Any, query: str, params: Any = None
    ) -> list[tuple]:
        """Execute query using asyncpg (sync wrapper)."""
        loop = self._get_event_loop()
        try:
            # Check if we can use run_until_complete
            if loop.is_running():
                # If the loop is already running, we need to handle this differently
                # This can happen in testing environments like pytest
                import warnings

                warnings.warn(
                    "AsyncpgClient used in running event loop context. "
                    "Consider using PsycopgClient for synchronous operations.",
                    RuntimeWarning,
                    stacklevel=2,
                )
                # For now, we'll try to execute synchronously by creating a new loop
                # in a thread, but this is not ideal
                import concurrent.futures

                with concurrent.futures.ThreadPoolExecutor() as executor:
                    future = executor.submit(
                        self._asyncio.run,
                        self._async_execute_query(connection, query, params),
                    )
                    return future.result()
            else:
                return loop.run_until_complete(
                    self._async_execute_query(connection, query, params)
                )
        except Exception as e:
            # Ensure we don't leave any coroutines hanging
            logger.warning(f"AsyncpgClient execute_query failed: {e}")
            raise

    async def _async_execute_query(
        self, connection: Any, query: str, params: Any = None
    ) -> list[tuple]:
        """Execute query using asyncpg (async)."""
        try:
            if params:
                if isinstance(params, list | tuple) and len(params) == 1:
                    # Single parameter
                    result = await connection.fetch(query, params[0])
                else:
                    # Multiple parameters
                    result = await connection.fetch(query, *params)
            else:
                result = await connection.fetch(query)

            # Convert asyncpg Records to tuples
            return [tuple(row) for row in result]
        except Exception as e:
            logger.warning(f"AsyncpgClient async query execution failed: {e}")
            raise

    def test_connection(self, connection_string: str) -> bool:
        """Test asyncpg connection."""
        try:
            conn = self.connect(connection_string)
            try:
                result = self.execute_query(conn, "SELECT 1")
                return len(result) > 0 and result[0][0] == 1
            finally:
                self.close_connection(conn)
        except Exception as e:
            logger.warning(f"asyncpg connection test failed: {e}")
            return False

    def get_database_version(self, connection_string: str) -> str | None:
        """Get PostgreSQL version using asyncpg."""
        try:
            conn = self.connect(connection_string)
            try:
                result = self.execute_query(conn, "SELECT version()")
                return result[0][0] if result else None
            finally:
                self.close_connection(conn)
        except Exception as e:
            logger.warning(f"Failed to get database version via asyncpg: {e}")
            return None

    def close_connection(self, connection: Any) -> None:
        """Close asyncpg connection."""
        if connection and not connection.is_closed():
            loop = self._get_event_loop()
            loop.run_until_complete(connection.close())

    def _get_event_loop(self):
        """Get or create event loop."""
        try:
            # Try to get the current event loop
            loop = self._asyncio.get_event_loop()
            # Check if loop is running - if so, we need a new thread
            if loop.is_running():
                # If we're in a running loop (like in pytest), we can't use
                # run_until_complete
                # This is a potential source of the warning - let's handle it better
                logger.warning(
                    "AsyncpgClient: Event loop is already running. "
                    "Consider using psycopg client for synchronous usage."
                )
            return loop
        except RuntimeError:
            # No event loop in current thread, create a new one
            loop = self._asyncio.new_event_loop()
            self._asyncio.set_event_loop(loop)
            return loop


def get_default_client() -> DatabaseClient:
    """Get the default database client.

    Prefers psycopg if available, falls back to asyncpg.
    """
    try:
        return PsycopgClient()
    except ImportError:
        try:
            return AsyncpgClient()
        except ImportError:
            raise ImportError(
                "No supported database client found. "
                "Install either: pip install psycopg[binary] OR pip install asyncpg"
            ) from None


def get_client(client_type: str = "auto") -> DatabaseClient:
    """Get a database client by type.

    Args:
        client_type: "psycopg", "asyncpg", or "auto" (default)

    Returns:
        DatabaseClient instance
    """
    if client_type == "auto":
        return get_default_client()
    elif client_type == "psycopg":
        return PsycopgClient()
    elif client_type == "asyncpg":
        return AsyncpgClient()
    else:
        raise ValueError(f"Unknown client type: {client_type}")


__all__ = [
    "DatabaseClient",
    "PsycopgClient",
    "AsyncpgClient",
    "get_default_client",
    "get_client",
]
