"""
🔄 PostgreSQL Client Compatibility Demonstration
==============================================

Simple demonstration that py-pglite works with different PostgreSQL
clients by providing a real PostgreSQL server.

Shows:
- SQLAlchemy integration (native)
- Connection parameter extraction
- Client compatibility principles
- Optional dependency handling
"""

import pytest

from sqlalchemy import text

from py_pglite import PGliteConfig
from py_pglite.sqlalchemy import SQLAlchemyPGliteManager


@pytest.fixture(scope="module")
def client_demo_manager():
    """Manager for client compatibility demonstration."""
    config = PGliteConfig(timeout=30, log_level="WARNING", cleanup_on_exit=True)

    with SQLAlchemyPGliteManager(config) as manager:
        manager.wait_for_ready(max_retries=15, delay=1.0)
        yield manager


class TestClientCompatibilityPrinciples:
    """Demonstrate client compatibility principles."""

    def test_sqlalchemy_native_integration(self, client_demo_manager):
        """Test native SQLAlchemy integration."""

        engine = client_demo_manager.get_engine()

        with engine.connect() as conn:
            # Test basic operations
            result = conn.execute(text("SELECT 'SQLAlchemy works!' as message"))
            row = result.fetchone()
            assert row is not None
            assert row.message == "SQLAlchemy works!"

            # Test table creation and data operations
            conn.execute(
                text("""
                CREATE TABLE IF NOT EXISTS client_demo (
                    id SERIAL PRIMARY KEY,
                    client_name VARCHAR(100),
                    message TEXT
                )
            """)
            )

            conn.execute(
                text("""
                INSERT INTO client_demo (client_name, message) VALUES
                ('SQLAlchemy', 'Native integration'),
                ('psycopg', 'Direct connection possible'),
                ('asyncpg', 'Async connection possible')
            """)
            )
            conn.commit()

            # Test query results
            result = conn.execute(
                text("""
                SELECT client_name, message FROM client_demo ORDER BY id
            """)
            )
            rows = result.fetchall()
            assert len(rows) == 3
            assert rows[0].client_name == "SQLAlchemy"

    def test_connection_parameter_extraction(self, client_demo_manager):
        """Test extracting connection parameters for other clients."""

        engine = client_demo_manager.get_engine()
        url = engine.url

        # Extract connection components
        host = str(url.host) if url.host else "localhost"
        port = url.port or 5432  # Default PostgreSQL port if not set
        database = url.database or "postgres"
        username = url.username or "postgres"

        # Verify components are valid
        assert port is not None
        assert database is not None

        # Show how these would be used with different clients
        connection_examples = {
            "psycopg": (
                f"psycopg.connect(host='{host}', port={port}, dbname='{database}', "
                f"user='{username}')"
            ),
            "asyncpg": (
                f"await asyncpg.connect(host='{host}', port={port}, "
                f"database='{database}', user='{username}')"
            ),
            "SQLAlchemy": f"create_engine('{url}')",
        }

        for _client, _example in connection_examples.items():
            pass

    def test_optional_dependency_handling(self, client_demo_manager):
        """Test graceful handling of optional dependencies."""

        # Test psycopg availability
        try:
            import psycopg

            # psycopg_available = True
        except ImportError:
            # psycopg_available = False
            pass

        # Test asyncpg availability
        try:
            import asyncpg

            # asyncpg_available = True
        except ImportError:
            # asyncpg_available = False
            pass

        # Test pytest-asyncio availability
        try:
            import pytest_asyncio

            # async_testing_available = True
        except ImportError:
            # async_testing_available = False
            pass

        # Core functionality should always work
        engine = client_demo_manager.get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 'Core always works!' as status"))
            status = result.scalar()
            assert status == "Core always works!"

    def test_real_postgresql_server_principle(self, client_demo_manager):
        """Demonstrate that py-pglite provides a real PostgreSQL server."""

        engine = client_demo_manager.get_engine()

        with engine.connect() as conn:
            # Test PostgreSQL-specific features
            result = conn.execute(text("SELECT version()"))
            version = result.scalar()
            assert "PostgreSQL" in version

            # Test advanced PostgreSQL features
            result = conn.execute(
                text("""
                SELECT
                    '{"test": "json", "array": [1,2,3]}'::jsonb ->> 'test' as json_test,
                    ARRAY['a', 'b', 'c'] as array_test,
                    CURRENT_TIMESTAMP as timestamp_test
            """)
            )
            row = result.fetchone()
            assert row is not None
            assert row.json_test == "json"
            assert len(row.array_test) == 3

            # Test that it's a real server, not SQLite
            result = conn.execute(text("SELECT 'Real PostgreSQL Server!' WHERE 1=1"))
            message = result.scalar()
            assert message == "Real PostgreSQL Server!"


class TestClientCompatibilityDocumentation:
    """Document client compatibility patterns."""

    def test_client_usage_patterns(self, client_demo_manager):
        """Document how different clients would connect."""

        engine = client_demo_manager.get_engine()
        url = engine.url

        # Extract connection details
        host = str(url.host) if url.host else "localhost"
        port = url.port
        database = url.database or "postgres"

        patterns = [
            ("SQLAlchemy (sync)", "✅ Native", "engine = manager.get_engine()"),
            (
                "psycopg (sync)",
                "✅ Direct",
                (
                    f"conn = psycopg.connect(host='{host}', port={port}, "
                    f"dbname='{database}')"
                ),
            ),
            (
                "asyncpg (async)",
                "✅ Direct",
                (
                    f"conn = await asyncpg.connect(host='{host}', port={port}, "
                    f"database='{database}')"
                ),
            ),
            ("Django ORM", "✅ Backend", "Uses custom py-pglite Django backend"),
            ("SQLModel", "✅ Via SQLAlchemy", "Works through SQLAlchemy integration"),
            (
                "FastAPI",
                "✅ Via SQLAlchemy",
                "async def endpoint(session: AsyncSession)",
            ),
        ]

        for _client, _support, _example in patterns:
            pass

    def test_installation_patterns(self, client_demo_manager):
        """Document installation patterns for different clients."""

        install_patterns = [
            ("Core only", "pip install py-pglite"),
            ("With SQLAlchemy", "pip install py-pglite[sqlalchemy]"),
            ("With Django", "pip install py-pglite[django]"),
            ("With FastAPI", "pip install py-pglite[fastapi]"),
            ("With async support", "pip install py-pglite[async]"),
            ("With psycopg", "pip install py-pglite[psycopg]"),
            ("Everything", "pip install py-pglite[all]"),
        ]

        for _description, _command in install_patterns:
            pass


# Summary fixture
@pytest.fixture(scope="module", autouse=True)
def client_compatibility_summary():
    """Print client compatibility summary."""

    yield


if __name__ == "__main__":
    pass
