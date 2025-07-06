"""SQLAlchemy utilities for py-pglite."""

from typing import Any

from sqlalchemy import MetaData, text
from sqlalchemy.engine import Engine
from sqlalchemy.orm import DeclarativeBase
from sqlalchemy.orm import Session as SQLAlchemySession

# Try to import SQLAlchemy Session types
try:
    HAS_SQLALCHEMY_ORM = True
except ImportError:
    SQLAlchemySession = None  # type: ignore
    HAS_SQLALCHEMY_ORM = False


def _ensure_sqlalchemy() -> None:
    """Ensure SQLAlchemy is available."""
    if not HAS_SQLALCHEMY_ORM or SQLAlchemySession is None:
        raise ImportError(
            "SQLAlchemy is required for these utilities. "
            "Install with: pip install 'py-pglite[sqlalchemy]'"
        )


# Try to import SQLModel
try:
    from sqlmodel import Session as SQLModelSession
    from sqlmodel import SQLModel

    HAS_SQLMODEL = True
except ImportError:
    SQLModelSession = None  # type: ignore
    SQLModel = None  # type: ignore
    HAS_SQLMODEL = False

__all__ = [
    "create_all_tables",
    "drop_all_tables",
    "get_session_class",
    "reflect_tables",
    "clear_all_data",
    "get_table_names",
    # Database maintenance utilities
    "clean_database_data",
    "reset_sequences",
    "get_table_row_counts",
    "verify_database_empty",
    "create_test_schema",
    "drop_test_schema",
    "execute_sql_file",
]


def create_all_tables(engine: Engine, base: DeclarativeBase | None = None) -> None:
    """Create all tables for the given declarative base.

    Args:
        engine: SQLAlchemy engine
        base: Declarative base class. If None and SQLModel is available, uses SQLModel.
    """
    if base is not None:
        base.metadata.create_all(engine)
    elif HAS_SQLMODEL and SQLModel is not None:
        SQLModel.metadata.create_all(engine)
    else:
        raise ValueError(
            "Either provide a declarative base or install SQLModel: "
            "pip install 'py-pglite[sqlmodel]'"
        )


def drop_all_tables(engine: Engine, base: DeclarativeBase | None = None) -> None:
    """Drop all tables for the given declarative base.

    Args:
        engine: SQLAlchemy engine
        base: Declarative base class. If None and SQLModel is available, uses SQLModel.
    """
    if base is not None:
        base.metadata.drop_all(engine)
    elif HAS_SQLMODEL and SQLModel is not None:
        SQLModel.metadata.drop_all(engine)
    else:
        raise ValueError(
            "Either provide a declarative base or install SQLModel: "
            "pip install 'py-pglite[sqlmodel]'"
        )


def get_session_class() -> type[Any]:
    """Get the best available session class.

    Returns:
        Session class (SQLModel Session if available, otherwise SQLAlchemy Session)
    """
    if HAS_SQLMODEL and SQLModelSession is not None:
        return SQLModelSession
    elif HAS_SQLALCHEMY_ORM and SQLAlchemySession is not None:
        return SQLAlchemySession
    else:
        raise ImportError(
            "Neither SQLModel nor SQLAlchemy ORM Session found. "
            "Install with: pip install 'py-pglite[sqlmodel]' or 'py-pglite[sqlalchemy]'"
        )


def reflect_tables(engine: Engine) -> MetaData:
    """Reflect existing tables from the database.

    Args:
        engine: SQLAlchemy engine

    Returns:
        MetaData object with reflected tables
    """
    metadata = MetaData()
    metadata.reflect(bind=engine)
    return metadata


def clear_all_data(engine: Engine, base: DeclarativeBase | None = None) -> None:
    """Clear all data from tables without dropping them.

    Args:
        engine: SQLAlchemy engine
        base: Declarative base class. If None and SQLModel is available, uses SQLModel.
    """
    if base is not None:
        metadata = base.metadata
    elif HAS_SQLMODEL and SQLModel is not None:
        metadata = SQLModel.metadata
    else:
        # Reflect tables if no base provided
        metadata = reflect_tables(engine)

    with engine.begin() as conn:
        # Disable foreign key constraints temporarily for PostgreSQL
        conn.execute(text("SET session_replication_role = replica"))

        # Clear all tables
        for table in reversed(metadata.sorted_tables):
            conn.execute(table.delete())

        # Re-enable foreign key constraints
        conn.execute(text("SET session_replication_role = DEFAULT"))


def get_table_names(engine: Engine) -> list[str]:
    """Get all table names in the database.

    Args:
        engine: SQLAlchemy engine

    Returns:
        List of table names
    """
    metadata = reflect_tables(engine)
    return list(metadata.tables.keys())


# Database maintenance utilities (consolidated from legacy)


def clean_database_data(
    engine: Engine, exclude_tables: list[str] | None = None
) -> None:
    """Clean all data from database tables while preserving schema.

    Args:
        engine: SQLAlchemy engine
        exclude_tables: List of table names to exclude from cleaning
    """
    _ensure_sqlalchemy()
    exclude_tables = exclude_tables or []

    with SQLAlchemySession(engine) as session:  # type: ignore
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
                # Table names from database metadata are safe, but use nosec for clarity
                conn.execute(text(f'DELETE FROM "{table}"'))  # nosec B608 - table name from metadata

            # Re-enable foreign key checks
            conn.execute(text("SET session_replication_role = DEFAULT"))

            session.commit()


def reset_sequences(engine: Engine) -> None:
    """Reset all sequences to start from 1.

    Args:
        engine: SQLAlchemy engine
    """
    _ensure_sqlalchemy()
    with SQLAlchemySession(engine) as session:  # type: ignore
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
                # Sequence names from database metadata are safe
                conn.execute(text(f'ALTER SEQUENCE "{seq}" RESTART WITH 1'))  # nosec B608 - sequence name from metadata

            session.commit()


def get_table_row_counts(engine: Engine) -> dict[str, int]:
    """Get row counts for all tables.

    Args:
        engine: SQLAlchemy engine

    Returns:
        Dictionary mapping table names to row counts
    """
    counts = {}

    _ensure_sqlalchemy()
    with SQLAlchemySession(engine) as session:  # type: ignore
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
                # Table names from database metadata are safe, but use nosec for clarity
                count_result = conn.execute(text(f'SELECT COUNT(*) FROM "{table}"'))  # nosec B608 - table name from metadata
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
    _ensure_sqlalchemy()
    with SQLAlchemySession(engine) as session:  # type: ignore
        with session.connection() as conn:
            # Schema name is passed as parameter, validate it's safe
            if not schema_name.replace("_", "").replace("-", "").isalnum():
                raise ValueError(f"Invalid schema name: {schema_name}")
            conn.execute(text(f'CREATE SCHEMA IF NOT EXISTS "{schema_name}"'))  # nosec B608 - validated schema name
            session.commit()


def drop_test_schema(engine: Engine, schema_name: str = "test_schema") -> None:
    """Drop a test schema.

    Args:
        engine: SQLAlchemy engine
        schema_name: Name of schema to drop
    """
    _ensure_sqlalchemy()
    with SQLAlchemySession(engine) as session:  # type: ignore
        with session.connection() as conn:
            # Schema name is passed as parameter, validate it's safe
            if not schema_name.replace("_", "").replace("-", "").isalnum():
                raise ValueError(f"Invalid schema name: {schema_name}")
            conn.execute(text(f'DROP SCHEMA IF EXISTS "{schema_name}" CASCADE'))  # nosec B608 - validated schema name
            session.commit()


def execute_sql_file(engine: Engine, file_path: str) -> None:
    """Execute SQL commands from a file.

    Args:
        engine: SQLAlchemy engine
        file_path: Path to SQL file
    """
    with open(file_path) as f:
        sql_content = f.read()

    _ensure_sqlalchemy()
    with SQLAlchemySession(engine) as session:  # type: ignore
        with session.connection() as conn:
            # Split on semicolons and execute each statement
            statements = [
                stmt.strip() for stmt in sql_content.split(";") if stmt.strip()
            ]

            for statement in statements:
                conn.execute(text(statement))

            session.commit()
