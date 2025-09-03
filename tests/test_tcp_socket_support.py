"""Test TCP socket support for ADBC compatibility."""

import psycopg
import pytest

from py_pglite import PGliteConfig
from py_pglite import PGliteManager


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
                    cur.execute("CREATE TABLE test_tcp (id SERIAL PRIMARY KEY, name TEXT)")
                    cur.execute("INSERT INTO test_tcp (name) VALUES (%s)", ("TCP Test",))
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
                    cur.execute("CREATE TABLE test_unix (id SERIAL PRIMARY KEY, name TEXT)")
                    cur.execute("INSERT INTO test_unix (name) VALUES (%s)", ("Unix Test",))
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
                    cur.execute("SELECT extname FROM pg_extension WHERE extname = 'vector'")
                    result = cur.fetchone()
                    assert result is not None

        # Test with TCP socket
        config_tcp = PGliteConfig(use_tcp=True, tcp_port=15437, extensions=["pgvector"])
        with PGliteManager(config_tcp) as manager:
            with psycopg.connect(manager.get_dsn()) as conn:
                with conn.cursor() as cur:
                    cur.execute("CREATE EXTENSION IF NOT EXISTS vector")
                    cur.execute("SELECT extname FROM pg_extension WHERE extname = 'vector'")
                    result = cur.fetchone()
                    assert result is not None