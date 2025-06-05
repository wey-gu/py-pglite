"""Utility functions for PGlite testing."""

from sqlalchemy import text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session


def clean_database_data(
    engine: Engine, exclude_tables: list[str] | None = None
) -> None:
    """Clean all data from database tables while preserving schema.

    Args:
        engine: SQLAlchemy engine
        exclude_tables: List of table names to exclude from cleaning
    """
    exclude_tables = exclude_tables or []

    with Session(engine) as session:
        with session.connection() as conn:
            # Disable foreign key checks temporarily
            conn.execute(text("SET session_replication_role = replica"))

            # Get all user tables
            result = conn.execute(
                text(
                    """
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename
            """
                )
            )

            tables = [
                row[0] for row in result.fetchall() if row[0] not in exclude_tables
            ]

            # Delete data from all tables
            for table in tables:
                conn.execute(text(f'DELETE FROM "{table}"'))

            # Re-enable foreign key checks
            conn.execute(text("SET session_replication_role = DEFAULT"))

            session.commit()


def reset_sequences(engine: Engine) -> None:
    """Reset all sequences to start from 1.

    Args:
        engine: SQLAlchemy engine
    """
    with Session(engine) as session:
        with session.connection() as conn:
            # Get all sequences
            result = conn.execute(
                text(
                    """
                SELECT sequence_name
                FROM information_schema.sequences
                WHERE sequence_schema = 'public'
            """
                )
            )

            sequences = [row[0] for row in result.fetchall()]

            # Reset each sequence
            for seq in sequences:
                conn.execute(text(f'ALTER SEQUENCE "{seq}" RESTART WITH 1'))

            session.commit()


def get_table_row_counts(engine: Engine) -> dict[str, int]:
    """Get row counts for all tables.

    Args:
        engine: SQLAlchemy engine

    Returns:
        Dictionary mapping table names to row counts
    """
    counts = {}

    with Session(engine) as session:
        with session.connection() as conn:
            # Get all table names
            result = conn.execute(
                text("""
                SELECT tablename
                FROM pg_tables
                WHERE schemaname = 'public'
                ORDER BY tablename
            """)
            )

            tables = [row[0] for row in result.fetchall()]

            # Count rows in each table
            for table in tables:
                count_result = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"'))
                row = count_result.fetchone()
                counts[table] = row[0] if row is not None else 0

    return counts


def verify_database_empty(
    engine: Engine, exclude_tables: list[str] | None = None
) -> bool:
    """Verify that database tables are empty.

    Args:
        engine: SQLAlchemy engine
        exclude_tables: List of table names to exclude from check

    Returns:
        True if all tables are empty, False otherwise
    """
    exclude_tables = exclude_tables or []
    counts = get_table_row_counts(engine)

    for table, count in counts.items():
        if table not in exclude_tables and count > 0:
            return False

    return True


def create_test_schema(engine: Engine, schema_name: str = "test_schema") -> None:
    """Create a test schema for isolated testing.

    Args:
        engine: SQLAlchemy engine
        schema_name: Name of schema to create
    """
    with Session(engine) as session:
        with session.connection() as conn:
            conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))
            session.commit()


def drop_test_schema(engine: Engine, schema_name: str = "test_schema") -> None:
    """Drop a test schema.

    Args:
        engine: SQLAlchemy engine
        schema_name: Name of schema to drop
    """
    with Session(engine) as session:
        with session.connection() as conn:
            conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))
            session.commit()


def execute_sql_file(engine: Engine, file_path: str) -> None:
    """Execute SQL commands from a file.

    Args:
        engine: SQLAlchemy engine
        file_path: Path to SQL file
    """
    with open(file_path) as f:
        sql_content = f.read()

    with Session(engine) as session:
        with session.connection() as conn:
            # Split on semicolons and execute each statement
            statements = [
                stmt.strip() for stmt in sql_content.split(";") if stmt.strip()
            ]

            for statement in statements:
                conn.execute(text(statement))

            session.commit()
