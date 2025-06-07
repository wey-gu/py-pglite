"""Framework-agnostic utility functions for PGlite testing."""

import logging
from typing import Any

import psycopg

logger = logging.getLogger(__name__)


def get_connection_from_string(connection_string: str) -> psycopg.Connection:
    """Get a raw psycopg connection from connection string.

    Args:
        connection_string: PostgreSQL connection string

    Returns:
        psycopg Connection object
    """
    return psycopg.connect(connection_string)


def test_connection(connection_string: str) -> bool:
    """Test if database connection is working.

    Args:
        connection_string: PostgreSQL connection string

    Returns:
        True if connection successful, False otherwise
    """
    try:
        with get_connection_from_string(connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT 1")
                result = cur.fetchone()
                return result is not None and result[0] == 1
    except Exception as e:
        logger.warning(f"Connection test failed: {e}")
        return False


def get_database_version(connection_string: str) -> str | None:
    """Get PostgreSQL version string.

    Args:
        connection_string: PostgreSQL connection string

    Returns:
        Version string or None if failed
    """
    try:
        with get_connection_from_string(connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT version()")
                result = cur.fetchone()
                return result[0] if result else None
    except Exception as e:
        logger.warning(f"Failed to get database version: {e}")
        return None


def get_table_names(connection_string: str, schema: str = "public") -> list[str]:
    """Get list of table names in a schema.

    Args:
        connection_string: PostgreSQL connection string
        schema: Schema name (default: public)

    Returns:
        List of table names
    """
    try:
        with get_connection_from_string(connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = %s
                    AND table_type = 'BASE TABLE'
                    ORDER BY table_name
                """,
                    (schema,),
                )
                return [row[0] for row in cur.fetchall()]
    except Exception as e:
        logger.warning(f"Failed to get table names: {e}")
        return []


def table_exists(
    connection_string: str, table_name: str, schema: str = "public"
) -> bool:
    """Check if a table exists in the database.

    Args:
        connection_string: PostgreSQL connection string
        table_name: Name of table to check
        schema: Schema name (default: public)

    Returns:
        True if table exists, False otherwise
    """
    try:
        with get_connection_from_string(connection_string) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT EXISTS (
                        SELECT FROM information_schema.tables
                        WHERE table_schema = %s
                        AND table_name = %s
                    )
                """,
                    (schema, table_name),
                )
                result = cur.fetchone()
                return result[0] if result else False
    except Exception as e:
        logger.warning(f"Failed to check table existence: {e}")
        return False


def execute_sql(
    connection_string: str, query: str, params: Any | None = None
) -> list[tuple] | None:
    """Execute SQL and return results.

    Args:
        connection_string: PostgreSQL connection string
        query: SQL query to execute
        params: Query parameters (optional)

    Returns:
        List of result tuples, or None if failed
    """
    try:
        with get_connection_from_string(connection_string) as conn:
            with conn.cursor() as cur:
                if params:
                    cur.execute(query, params)  # type: ignore
                else:
                    cur.execute(query)  # type: ignore

                # Check if it's a SELECT query by trying to fetch
                try:
                    return cur.fetchall()
                except psycopg.ProgrammingError:
                    # Not a SELECT query, return empty list to indicate success
                    return []
    except Exception as e:
        logger.warning(f"Failed to execute SQL: {e}")
        return None
