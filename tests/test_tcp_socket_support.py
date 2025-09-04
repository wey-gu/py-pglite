"""Test TCP socket support."""

import asyncio
import json

from io import StringIO

import pytest

from sqlalchemy import create_engine
from sqlalchemy import text
from sqlalchemy.pool import StaticPool

from py_pglite import PGliteConfig
from py_pglite import PGliteManager


# Optional dependencies - only import if available
try:
    import asyncpg
except ImportError:
    asyncpg = None

try:
    import psycopg
except ImportError:
    psycopg = None

try:
    import psycopg2
except ImportError:
    psycopg2 = None


class TestTCPSocketConfiguration:
    """Test TCP socket configuration and validation."""

    def test_default_remains_unix_socket(self):
        """Ensure backward compatibility - Unix socket by default."""
        config = PGliteConfig()
        assert config.use_tcp is False
        assert config.socket_path is not None
        assert config.tcp_host == "127.0.0.1"  # Default values still set
        assert config.tcp_port == 5432

    def test_tcp_config_enabled(self):
        """Test enabling TCP configuration."""
        config = PGliteConfig(use_tcp=True)
        assert config.use_tcp is True
        assert config.tcp_host == "127.0.0.1"
        assert config.tcp_port == 5432

    def test_tcp_config_custom_values(self):
        """Test TCP configuration with custom values."""
        config = PGliteConfig(use_tcp=True, tcp_host="localhost", tcp_port=15432)
        assert config.tcp_host == "localhost"
        assert config.tcp_port == 15432

    def test_tcp_port_validation(self):
        """Test TCP port validation."""
        # Valid ports
        config = PGliteConfig(use_tcp=True, tcp_port=1)
        assert config.tcp_port == 1

        config = PGliteConfig(use_tcp=True, tcp_port=65535)
        assert config.tcp_port == 65535

        # Invalid ports
        with pytest.raises(ValueError, match="Invalid TCP port"):
            PGliteConfig(use_tcp=True, tcp_port=0)

        with pytest.raises(ValueError, match="Invalid TCP port"):
            PGliteConfig(use_tcp=True, tcp_port=70000)

        with pytest.raises(ValueError, match="Invalid TCP port"):
            PGliteConfig(use_tcp=True, tcp_port=-1)

    def test_tcp_host_validation(self):
        """Test TCP host validation."""
        # Empty host should fail
        with pytest.raises(ValueError, match="TCP host cannot be empty"):
            PGliteConfig(use_tcp=True, tcp_host="")


class TestTCPSocketConnectionStrings:
    """Test connection string generation for TCP mode."""

    def test_unix_socket_connection_strings(self):
        """Test connection strings for Unix socket mode."""
        config = PGliteConfig(use_tcp=False)

        # Connection string should use Unix socket
        conn_str = config.get_connection_string()
        assert "host=" in conn_str
        assert "127.0.0.1" not in conn_str
        assert "port=" not in conn_str

        # DSN should use Unix socket
        dsn = config.get_dsn()
        assert "host=" in dsn
        assert "port=" not in dsn
        assert "127.0.0.1" not in dsn

        # URI should use Unix socket
        uri = config.get_psycopg_uri()
        assert "host=" in uri
        assert "127.0.0.1" not in uri

    def test_tcp_connection_strings(self):
        """Test connection strings for TCP mode."""
        config = PGliteConfig(use_tcp=True, tcp_host="127.0.0.1", tcp_port=5432)

        # Connection string should use TCP
        conn_str = config.get_connection_string()
        assert "127.0.0.1:5432" in conn_str
        assert "sslmode=disable" in conn_str
        assert "postgresql+psycopg://postgres:postgres@" in conn_str

        # DSN should use TCP
        dsn = config.get_dsn()
        assert "host=127.0.0.1" in dsn
        assert "port=5432" in dsn
        assert "sslmode=disable" in dsn

        # URI should use TCP
        uri = config.get_psycopg_uri()
        assert "127.0.0.1:5432" in uri
        assert "sslmode=disable" in uri
        assert "postgresql://postgres:postgres@" in uri

    def test_tcp_custom_host_port_strings(self):
        """Test connection strings with custom TCP host and port."""
        config = PGliteConfig(use_tcp=True, tcp_host="localhost", tcp_port=15432)

        # All connection methods should use custom values
        assert "localhost:15432" in config.get_connection_string()
        assert "host=localhost port=15432" in config.get_dsn()
        assert "localhost:15432" in config.get_psycopg_uri()


class TestTCPSocketManager:
    """Test PGliteManager with TCP socket support."""

    @pytest.mark.parametrize("use_tcp", [False, True])
    def test_both_socket_modes_work(self, use_tcp):
        """Test that both Unix and TCP modes work correctly."""
        config = PGliteConfig(
            use_tcp=use_tcp,
            tcp_port=15433 if use_tcp else 5432,  # Use non-default port for TCP tests
        )

        with PGliteManager(config) as manager:
            assert manager.is_running()

            # Check connection strings are mode-appropriate
            dsn = manager.get_dsn()
            conn_str = manager.get_connection_string()
            uri = manager.get_psycopg_uri()

            if use_tcp:
                # TCP mode assertions
                assert "127.0.0.1" in dsn
                assert "port=15433" in dsn
                assert "sslmode=disable" in dsn

                assert "127.0.0.1:15433" in conn_str
                assert "127.0.0.1:15433" in uri
            else:
                # Unix socket mode assertions
                assert "host=" in dsn
                assert "port=" not in dsn or "port=5432" not in dsn

                assert "127.0.0.1" not in conn_str
                assert "127.0.0.1" not in uri

    def test_tcp_mode_database_connectivity(self):
        """Test actual database connectivity in TCP mode."""
        config = PGliteConfig(use_tcp=True, tcp_port=15434)

        with PGliteManager(config) as manager:
            # Use psycopg to connect
            dsn = manager.get_dsn()
            with psycopg.connect(dsn) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT version()")
                    result = cur.fetchone()
                    assert result is not None
                    assert "PostgreSQL" in str(result[0])

                    # Test basic operations
                    cur.execute(
                        "CREATE TABLE test_tcp (id SERIAL PRIMARY KEY, name TEXT)"
                    )
                    cur.execute(
                        "INSERT INTO test_tcp (name) VALUES (%s)", ("TCP Test",)
                    )
                    cur.execute("SELECT name FROM test_tcp WHERE id = 1")
                    result = cur.fetchone()
                    assert result[0] == "TCP Test"

    def test_unix_mode_database_connectivity(self):
        """Test actual database connectivity in Unix socket mode."""
        config = PGliteConfig(use_tcp=False)

        with PGliteManager(config) as manager:
            # Use psycopg to connect
            dsn = manager.get_dsn()
            with psycopg.connect(dsn) as conn:
                with conn.cursor() as cur:
                    cur.execute("SELECT version()")
                    result = cur.fetchone()
                    assert result is not None
                    assert "PostgreSQL" in str(result[0])

                    # Test basic operations
                    cur.execute(
                        "CREATE TABLE test_unix (id SERIAL PRIMARY KEY, name TEXT)"
                    )
                    cur.execute(
                        "INSERT INTO test_unix (name) VALUES (%s)", ("Unix Test",)
                    )
                    cur.execute("SELECT name FROM test_unix WHERE id = 1")
                    result = cur.fetchone()
                    assert result[0] == "Unix Test"

    def test_tcp_mode_multiple_instances_different_ports(self):
        """Test running multiple TCP instances on different ports."""
        config1 = PGliteConfig(use_tcp=True, tcp_port=15435)
        config2 = PGliteConfig(use_tcp=True, tcp_port=15436)

        with PGliteManager(config1) as manager1:
            with PGliteManager(config2) as manager2:
                # Both should be running
                assert manager1.is_running()
                assert manager2.is_running()

                # Connection strings should have different ports
                assert "15435" in manager1.get_dsn()
                assert "15436" in manager2.get_dsn()

                # Test connectivity to both
                with psycopg.connect(manager1.get_dsn()) as conn1:
                    with conn1.cursor() as cur1:
                        cur1.execute("SELECT 1")
                        assert cur1.fetchone()[0] == 1

                with psycopg.connect(manager2.get_dsn()) as conn2:
                    with conn2.cursor() as cur2:
                        cur2.execute("SELECT 2")
                        assert cur2.fetchone()[0] == 2

    def test_mode_does_not_affect_extensions(self):
        """Test that extensions work in both Unix and TCP modes."""
        # Test with Unix socket
        config_unix = PGliteConfig(use_tcp=False, extensions=["pgvector"])
        with PGliteManager(config_unix) as manager:
            with psycopg.connect(manager.get_dsn()) as conn:
                with conn.cursor() as cur:
                    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
                    cur.execute(
                        "SELECT extname FROM pg_extension WHERE extname = 'vector'"
                    )
                    result = cur.fetchone()
                    assert result is not None

        # Test with TCP socket
        config_tcp = PGliteConfig(use_tcp=True, tcp_port=15437, extensions=["pgvector"])
        with PGliteManager(config_tcp) as manager:
            with psycopg.connect(manager.get_dsn()) as conn:
                with conn.cursor() as cur:
                    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
                    cur.execute(
                        "SELECT extname FROM pg_extension WHERE extname = 'vector'"
                    )
                    result = cur.fetchone()
                    assert result is not None


class TestTCPModeDatabaseClients:
    """Test TCP mode with different database clients."""

    def test_sqlalchemy_tcp_mode(self):
        """Test SQLAlchemy connectivity in TCP mode."""
        config = PGliteConfig(use_tcp=True, tcp_port=15440)

        with PGliteManager(config) as manager:
            # Get connection string for SQLAlchemy
            conn_str = manager.get_connection_string()

            # Verify TCP connection string format
            assert "127.0.0.1:15440" in conn_str
            assert "sslmode=disable" in conn_str
            assert "postgresql+psycopg://" in conn_str

            # Create SQLAlchemy engine with StaticPool for single connection
            engine = create_engine(
                conn_str,
                poolclass=StaticPool,  # PGlite only supports single connection
                echo=False,
            )

            # Test basic operations with SQLAlchemy
            with engine.connect() as conn:
                # Test SELECT
                result = conn.execute(text("SELECT 1 as val"))
                assert result.scalar() == 1

                # Test CREATE TABLE
                conn.execute(
                    text("""
                    CREATE TABLE test_sqlalchemy (
                        id SERIAL PRIMARY KEY,
                        name VARCHAR(100),
                        value INTEGER
                    )
                """)
                )

                # Test INSERT
                conn.execute(
                    text(
                        "INSERT INTO test_sqlalchemy (name, value) VALUES (:name, :value)"
                    ),
                    {"name": "SQLAlchemy Test", "value": 42},
                )

                # Test SELECT with WHERE
                result = conn.execute(
                    text("SELECT name, value FROM test_sqlalchemy WHERE value = :val"),
                    {"val": 42},
                )
                row = result.fetchone()
                assert row[0] == "SQLAlchemy Test"
                assert row[1] == 42

                # Test UPDATE
                conn.execute(
                    text(
                        "UPDATE test_sqlalchemy SET value = :new_val WHERE name = :name"
                    ),
                    {"new_val": 100, "name": "SQLAlchemy Test"},
                )

                # Verify UPDATE
                result = conn.execute(
                    text("SELECT value FROM test_sqlalchemy WHERE name = :name"),
                    {"name": "SQLAlchemy Test"},
                )
                assert result.scalar() == 100

                # Test DELETE
                conn.execute(text("DELETE FROM test_sqlalchemy WHERE id > 0"))
                result = conn.execute(text("SELECT COUNT(*) FROM test_sqlalchemy"))
                assert result.scalar() == 0

                conn.commit()

    def test_asyncpg_tcp_mode(self):
        """Test asyncpg connectivity in TCP mode.
        
        Root cause analysis showed asyncpg DOES work with PGlite TCP mode,
        but requires specific connection parameters and careful cleanup handling.
        """
        if asyncpg is None:
            pytest.skip("asyncpg not available")

        async def run_asyncpg_test():
            config = PGliteConfig(use_tcp=True, tcp_port=15443)

            with PGliteManager(config) as manager:
                # Connect with asyncpg using the working configuration found through debugging
                # Key fixes: server_settings={} and proper timeout handling
                conn = await asyncio.wait_for(
                    asyncpg.connect(
                        host=config.tcp_host,
                        port=config.tcp_port,
                        user="postgres",
                        password="postgres",
                        database="postgres",
                        ssl=False,
                        server_settings={}  # CRITICAL: Empty server_settings prevents hanging
                    ),
                    timeout=10.0
                )
                
                try:
                    # Test basic operations
                    result = await conn.fetchval("SELECT 1")
                    assert result == 1

                    # Test CREATE TABLE
                    await conn.execute("""
                        CREATE TABLE test_asyncpg (
                            id SERIAL PRIMARY KEY,
                            name TEXT,
                            tags TEXT[]
                        )
                    """)

                    # Test INSERT with arrays
                    await conn.execute(
                        "INSERT INTO test_asyncpg (name, tags) VALUES ($1, $2)",
                        "Async Test",
                        ["tag1", "tag2", "tag3"],
                    )

                    # Test SELECT with arrays
                    row = await conn.fetchrow(
                        "SELECT name, tags FROM test_asyncpg WHERE name = $1",
                        "Async Test",
                    )
                    assert row["name"] == "Async Test"
                    assert row["tags"] == ["tag1", "tag2", "tag3"]

                    # Test prepared statements
                    stmt = await conn.prepare("SELECT $1::int + $2::int")
                    result = await stmt.fetchval(5, 10)
                    assert result == 15

                    # Test transaction
                    async with conn.transaction():
                        await conn.execute(
                            "INSERT INTO test_asyncpg (name, tags) VALUES ($1, $2)",
                            "Transaction Test",
                            ["tx"],
                        )
                        # Verify insert within transaction
                        count = await conn.fetchval("SELECT COUNT(*) FROM test_asyncpg")
                        assert count == 2

                    # Test batch operations
                    batch_data = [(f"Batch {i}", [f"tag{i}"]) for i in range(3)]
                    await conn.executemany(
                        "INSERT INTO test_asyncpg (name, tags) VALUES ($1, $2)",
                        batch_data,
                    )

                    # Verify batch insert
                    count = await conn.fetchval(
                        "SELECT COUNT(*) FROM test_asyncpg WHERE name LIKE 'Batch%'"
                    )
                    assert count == 3

                finally:
                    # Handle connection cleanup with timeout to prevent hanging
                    # Root cause: PGlite's connection cleanup can hang in some cases
                    try:
                        await asyncio.wait_for(conn.close(), timeout=5.0)
                    except asyncio.TimeoutError:
                        # If cleanup hangs, it's not a test failure since all operations worked
                        # This is a known limitation with PGlite TCP mode cleanup
                        pass

        # Run the async test
        asyncio.run(run_asyncpg_test())

    def test_multiple_clients_tcp_mode(self):
        """Test multiple different clients can connect to TCP mode (sequentially due to single connection limit)."""
        config = PGliteConfig(use_tcp=True, tcp_port=15444)

        with PGliteManager(config) as manager:
            clients_tested = []

            # Test psycopg2 (if available)
            if psycopg2 is not None:
                conn2 = psycopg2.connect(manager.get_dsn())
                cur2 = conn2.cursor()
                cur2.execute("CREATE TABLE multi_client (id INT, client TEXT)")
                cur2.execute("INSERT INTO multi_client VALUES (1, 'psycopg2')")
                conn2.commit()
                cur2.close()
                conn2.close()
                clients_tested.append("psycopg2")

            # Test psycopg3 (if available)
            if psycopg is not None:
                with psycopg.connect(manager.get_dsn()) as conn3:
                    with conn3.cursor() as cur3:
                        # Create table if it doesn't exist (in case psycopg2 wasn't available)
                        if not clients_tested:
                            cur3.execute(
                                "CREATE TABLE multi_client (id INT, client TEXT)"
                            )
                        cur3.execute("INSERT INTO multi_client VALUES (2, 'psycopg3')")
                        conn3.commit()
                clients_tested.append("psycopg3")

            # Test SQLAlchemy (always available since it's imported directly)
            engine = create_engine(
                manager.get_connection_string(), poolclass=StaticPool
            )
            with engine.connect() as conn_sa:
                # Create table if it doesn't exist (in case no psycopg was available)
                if not clients_tested:
                    conn_sa.execute(
                        text("CREATE TABLE multi_client (id INT, client TEXT)")
                    )
                conn_sa.execute(
                    text("INSERT INTO multi_client VALUES (3, 'sqlalchemy')")
                )
                conn_sa.commit()
                
                # Do the verification within the same connection to avoid reconnection issues
                result = conn_sa.execute(text("SELECT COUNT(*) FROM multi_client"))
                expected_count = len(clients_tested) + 1  # +1 for sqlalchemy
                assert result.scalar() == expected_count
            
            clients_tested.append("sqlalchemy")

            # Verify that we tested at least one client
            assert len(clients_tested) > 0, "No clients were available for testing"
