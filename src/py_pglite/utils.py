"""Framework-agnostic utility functions for PGlite testing."""

import logging

from pathlib import Path
from typing import Any

from py_pglite.clients import DatabaseClient
from py_pglite.clients import get_default_client


logger = logging.getLogger(__name__)


def get_connection_from_string(
    connection_string: str, client: DatabaseClient | None = None
) -> Any:
    """Get a raw database connection from connection string.

    Args:
        connection_string: PostgreSQL connection string
        client: Database client to use (defaults to auto-detected)

    Returns:
        Database connection object
    """
    if client is None:
        client = get_default_client()
    return client.connect(connection_string)


def check_connection(
    connection_string: str, client: DatabaseClient | None = None
) -> bool:
    """Test if database connection is working.

    Args:
        connection_string: PostgreSQL connection string (DSN format preferred)
        client: Database client to use (defaults to auto-detected)

    Returns:
        True if connection successful, False otherwise
    """
    if client is None:
        client = get_default_client()
    return client.test_connection(connection_string)


# Backward compatibility alias
test_connection = check_connection


def get_database_version(
    connection_string: str, client: DatabaseClient | None = None
) -> str | None:
    """Get PostgreSQL version string.

    Args:
        connection_string: PostgreSQL connection string
        client: Database client to use (defaults to auto-detected)

    Returns:
        Version string or None if failed
    """
    if client is None:
        client = get_default_client()
    return client.get_database_version(connection_string)


def get_table_names(
    connection_string: str,
    schema: str = "public",
    client: DatabaseClient | None = None,
) -> list[str]:
    """Get list of table names in a schema.

    Args:
        connection_string: PostgreSQL connection string
        schema: Schema name (default: public)
        client: Database client to use (defaults to auto-detected)

    Returns:
        List of table names
    """
    if client is None:
        client = get_default_client()

    try:
        conn = client.connect(connection_string)
        try:
            result = client.execute_query(
                conn,
                """
                SELECT table_name
                FROM information_schema.tables
                WHERE table_schema = %s
                AND table_type = 'BASE TABLE'
                ORDER BY table_name
                """,
                (schema,),
            )
            return [row[0] for row in result]
        finally:
            client.close_connection(conn)
    except Exception as e:
        logger.warning(f"Failed to get table names: {e}")
        return []


def table_exists(
    connection_string: str,
    table_name: str,
    schema: str = "public",
    client: DatabaseClient | None = None,
) -> bool:
    """Check if a table exists in the database.

    Args:
        connection_string: PostgreSQL connection string
        table_name: Name of table to check
        schema: Schema name (default: public)
        client: Database client to use (defaults to auto-detected)

    Returns:
        True if table exists, False otherwise
    """
    if client is None:
        client = get_default_client()

    try:
        conn = client.connect(connection_string)
        try:
            result = client.execute_query(
                conn,
                """
                SELECT EXISTS (
                    SELECT FROM information_schema.tables
                    WHERE table_schema = %s
                    AND table_name = %s
                )
                """,
                (schema, table_name),
            )
            return result[0][0] if result else False
        finally:
            client.close_connection(conn)
    except Exception as e:
        logger.warning(f"Failed to check table existence: {e}")
        return False


def execute_sql(
    connection_string: str,
    query: str,
    params: Any | None = None,
    client: DatabaseClient | None = None,
) -> list[tuple] | None:
    """Execute SQL and return results.

    Args:
        connection_string: PostgreSQL connection string
        query: SQL query to execute
        params: Query parameters (optional)
        client: Database client to use (defaults to auto-detected)

    Returns:
        List of result tuples, or None if failed
    """
    if client is None:
        client = get_default_client()

    try:
        conn = client.connect(connection_string)
        try:
            return client.execute_query(conn, query, params)
        finally:
            client.close_connection(conn)
    except Exception as e:
        logger.warning(f"Failed to execute SQL: {e}")
        return None


def get_major_version(version: str) -> int:
    """Get the major version number from a version string."""
    return int(version.split(".")[0])


def find_pglite_modules(start_path: Path) -> Path | None:
    """Find the node_modules directory containing @electric-sql/pglite."""
    current_path = start_path.resolve()
    while current_path != current_path.parent:
        node_modules = current_path / "node_modules"
        if (node_modules / "@electric-sql/pglite").exists():
            return node_modules
        current_path = current_path.parent
    return None
