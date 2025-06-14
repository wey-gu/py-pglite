"""Tests for connection resilience and format compatibility."""

import pytest

from py_pglite import PGliteManager
from py_pglite.config import PGliteConfig
from py_pglite.utils import test_connection


class TestConnectionStringFormats:
    """Test different connection string formats work correctly."""

    def test_sqlalchemy_connection_string_format(self):
        """Test SQLAlchemy connection string format."""
        config = PGliteConfig()
        conn_str = config.get_connection_string()

        # Should be SQLAlchemy format
        assert conn_str.startswith("postgresql+psycopg://")
        assert "postgres:postgres@" in conn_str
        assert "/postgres" in conn_str
        assert "host=" in conn_str

    def test_psycopg_uri_format(self):
        """Test direct psycopg URI format."""
        config = PGliteConfig()
        uri = config.get_psycopg_uri()

        # Should be standard PostgreSQL URI
        assert uri.startswith("postgresql://")
        assert "postgres:postgres@" in uri
        assert "/postgres" in uri
        assert "host=" in uri
        # Should NOT have +psycopg
        assert "+psycopg" not in uri

    def test_dsn_format(self):
        """Test DSN key-value format."""
        config = PGliteConfig()
        dsn = config.get_dsn()

        # Should be key-value format
        assert "host=" in dsn
        assert "dbname=postgres" in dsn
        assert "user=postgres" in dsn
        assert "password=postgres" in dsn
        # Should NOT have URI scheme
        assert "postgresql://" not in dsn

    def test_connection_format_consistency(self):
        """Test that all formats reference the same socket directory."""
        config = PGliteConfig()

        conn_str = config.get_connection_string()
        uri = config.get_psycopg_uri()
        dsn = config.get_dsn()

        # Extract socket directory from each format
        sqlalchemy_host = conn_str.split("host=")[1].split("&")[0].split("#")[0]
        uri_host = uri.split("host=")[1].split("&")[0].split("#")[0]
        dsn_host = dsn.split("host=")[1].split(" ")[0]

        # All should reference the same socket directory
        assert sqlalchemy_host == uri_host == dsn_host


class TestConnectionResilience:
    """Test connection resilience and error handling."""

    def test_connection_with_invalid_formats(self):
        """Test that invalid connection formats fail gracefully."""
        invalid_formats = [
            "",
            "not-a-connection-string",
            "postgresql+psycopg://invalid",
            "postgresql://",
            "host=nonexistent",
        ]

        for invalid_format in invalid_formats:
            # Should return False, not crash
            assert not test_connection(invalid_format)

    def test_manager_wait_for_ready_uses_correct_format(self):
        """Test that manager uses correct connection format for readiness check."""
        config = PGliteConfig()
        manager = PGliteManager(config)

        # Should not crash when checking readiness (even if not started)
        # Uses DSN format internally which is compatible with psycopg
        ready = manager.wait_for_ready(max_retries=1, delay=0.1)

        # Should return False since not started, but not crash
        assert ready is False

    def test_connection_format_error_messages(self):
        """Test that connection errors provide helpful messages."""
        from py_pglite.utils import get_database_version

        # Test with SQLAlchemy format (should fail for direct psycopg)
        sqlalchemy_format = (
            "postgresql+psycopg://postgres:postgres@/postgres?host=/tmp/nonexistent"
        )

        # Should handle gracefully and return None
        version = get_database_version(sqlalchemy_format)
        assert version is None


class TestSocketPathHandling:
    """Test socket path handling and uniqueness."""

    def test_socket_path_uniqueness(self):
        """Test that different configs get unique socket paths."""
        config1 = PGliteConfig()
        config2 = PGliteConfig()

        # Should have different socket paths
        assert config1.socket_path != config2.socket_path

    def test_socket_path_format(self):
        """Test socket path follows PostgreSQL conventions."""
        config = PGliteConfig()

        # Should end with .s.PGSQL.5432
        assert config.socket_path.endswith(".s.PGSQL.5432")

        # Should be in temp directory
        import tempfile

        temp_dir = tempfile.gettempdir()
        assert temp_dir in config.socket_path

    def test_custom_socket_path(self):
        """Test custom socket path configuration."""
        custom_path = "/tmp/custom_test/.s.PGSQL.5432"
        config = PGliteConfig(socket_path=custom_path)

        assert config.socket_path == custom_path

        # All connection formats should use the custom path
        conn_str = config.get_connection_string()
        dsn = config.get_dsn()

        assert "/tmp/custom_test" in conn_str
        assert "/tmp/custom_test" in dsn


class TestConnectionCompatibility:
    """Test compatibility with different PostgreSQL clients."""

    def test_psycopg_client_compatibility(self):
        """Test that connection formats work with psycopg client."""
        from py_pglite.clients import PsycopgClient

        config = PGliteConfig()
        client = PsycopgClient()

        # DSN format should be compatible
        dsn = config.get_dsn()
        # Should not crash (will fail to connect, but format should be valid)
        result = client.test_connection(dsn)
        assert result is False  # Expected since no server running

        # URI format should also be compatible
        uri = config.get_psycopg_uri()
        result = client.test_connection(uri)
        assert result is False  # Expected since no server running

    def test_connection_string_parsing(self):
        """Test that connection strings can be parsed correctly."""
        config = PGliteConfig()

        # Test SQLAlchemy format parsing
        conn_str = config.get_connection_string()
        assert "postgresql+psycopg://" in conn_str

        # Test URI format parsing
        uri = config.get_psycopg_uri()
        assert "postgresql://" in uri
        assert "+psycopg" not in uri

        # Test DSN format parsing
        dsn = config.get_dsn()
        parts = dsn.split()
        assert len(parts) >= 4  # Should have host, dbname, user, password
