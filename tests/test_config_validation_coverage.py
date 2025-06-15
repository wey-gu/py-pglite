"""Comprehensive config validation tests to boost coverage.

Tests all the missing config validation paths and error conditions
to significantly improve coverage from 48% to 80%+.
"""

import logging
import os
import tempfile
import uuid
from pathlib import Path
from unittest.mock import patch

import pytest

from py_pglite.config import PGliteConfig, _get_secure_socket_path


class TestSecureSocketPath:
    """Test _get_secure_socket_path function (lines 13-18 missing)."""

    def test_secure_socket_path_generation(self):
        """Test secure socket path generation."""
        path1 = _get_secure_socket_path()
        path2 = _get_secure_socket_path()

        # Should be different each time due to UUID
        assert path1 != path2

        # Should contain PID and UUID components
        assert "py-pglite-" in path1
        assert str(os.getpid()) in path1

        # Should end with PostgreSQL socket name
        assert path1.endswith(".s.PGSQL.5432")

        # Directory should be created with secure permissions
        socket_dir = Path(path1).parent
        assert socket_dir.exists()

        # Check permissions (0o700 = owner read/write/execute only)
        stat = socket_dir.stat()
        permissions = oct(stat.st_mode)[-3:]
        assert permissions == "700"


class TestPGliteConfigValidation:
    """Test config validation logic (lines 48-61 missing)."""

    def test_negative_timeout_validation(self):
        """Test validation of negative timeout."""
        with pytest.raises(ValueError, match="timeout must be positive"):
            PGliteConfig(timeout=-1)

    def test_zero_timeout_validation(self):
        """Test validation of zero timeout."""
        with pytest.raises(ValueError, match="timeout must be positive"):
            PGliteConfig(timeout=0)

    def test_invalid_log_level_validation(self):
        """Test validation of invalid log level."""
        with pytest.raises(ValueError, match="Invalid log_level"):
            PGliteConfig(log_level="INVALID")

    def test_valid_log_levels(self):
        """Test all valid log levels work."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in valid_levels:
            config = PGliteConfig(log_level=level)
            assert config.log_level == level

    def test_unsupported_extension_validation(self):
        """Test validation of unsupported extensions."""
        with pytest.raises(ValueError, match="Unsupported extension"):
            PGliteConfig(extensions=["invalid_extension"])

    def test_supported_extension_validation(self):
        """Test validation of supported extensions."""
        config = PGliteConfig(extensions=["pgvector"])
        assert config.extensions == ["pgvector"]

    def test_multiple_extensions_validation(self):
        """Test validation with multiple extensions."""
        config = PGliteConfig(extensions=["pgvector"])
        assert config.extensions == ["pgvector"]

        # Test mixed valid/invalid
        with pytest.raises(ValueError, match="Unsupported extension"):
            PGliteConfig(extensions=["pgvector", "invalid_extension"])

    def test_work_dir_path_resolution(self):
        """Test work_dir path resolution (line 61)."""
        with tempfile.TemporaryDirectory() as temp_dir:
            # Test relative path gets resolved
            config = PGliteConfig(work_dir=Path("."))
            assert config.work_dir == Path(".").resolve()

            # Test absolute path
            config = PGliteConfig(work_dir=Path(temp_dir))
            assert config.work_dir == Path(temp_dir).resolve()

    def test_work_dir_none_default(self):
        """Test work_dir defaults to None."""
        config = PGliteConfig()
        assert config.work_dir is None


class TestPGliteConfigProperties:
    """Test config properties (lines 68-69, 74, 87, 93 missing)."""

    def test_log_level_int_property(self):
        """Test log_level_int property converts correctly."""
        test_cases = [
            ("DEBUG", logging.DEBUG),
            ("INFO", logging.INFO),
            ("WARNING", logging.WARNING),
            ("ERROR", logging.ERROR),
            ("CRITICAL", logging.CRITICAL),
        ]

        for level_str, expected_int in test_cases:
            config = PGliteConfig(log_level=level_str)
            assert config.log_level_int == expected_int
            assert isinstance(config.log_level_int, int)

    def test_get_connection_string_property(self):
        """Test get_connection_string method."""
        config = PGliteConfig()
        conn_str = config.get_connection_string()

        # Should be SQLAlchemy PostgreSQL connection string
        assert conn_str.startswith("postgresql+psycopg://")
        assert "postgres:postgres@/postgres" in conn_str
        assert "host=" in conn_str

        # Should include socket directory
        socket_dir = str(Path(config.socket_path).parent)
        assert socket_dir in conn_str

    def test_get_psycopg_uri_property(self):
        """Test get_psycopg_uri method."""
        config = PGliteConfig()
        uri = config.get_psycopg_uri()

        # Should be standard PostgreSQL URI
        assert uri.startswith("postgresql://")
        assert "postgres:postgres@/postgres" in uri
        assert "host=" in uri

        # Should include socket directory
        socket_dir = str(Path(config.socket_path).parent)
        assert socket_dir in uri

    def test_get_dsn_property(self):
        """Test get_dsn method."""
        config = PGliteConfig()
        dsn = config.get_dsn()

        # Should be key-value DSN format
        assert "host=" in dsn
        assert "dbname=postgres" in dsn
        assert "user=postgres" in dsn
        assert "password=postgres" in dsn

        # Should include socket directory
        socket_dir = str(Path(config.socket_path).parent)
        assert socket_dir in dsn


class TestPGliteConfigDefaults:
    """Test config default values (lines 34-44 missing)."""

    def test_default_values(self):
        """Test all default configuration values."""
        config = PGliteConfig()

        # Test documented defaults
        assert config.timeout == 30
        assert config.cleanup_on_exit is True
        assert config.log_level == "INFO"
        assert config.work_dir is None
        assert config.node_modules_check is True
        assert config.auto_install_deps is True
        assert config.extensions is None
        assert config.node_options is None

        # Test socket_path is generated
        assert config.socket_path is not None
        assert isinstance(config.socket_path, str)
        assert config.socket_path.endswith(".s.PGSQL.5432")

    def test_custom_socket_path(self):
        """Test custom socket path."""
        custom_path = "/tmp/custom-socket/.s.PGSQL.5432"
        config = PGliteConfig(socket_path=custom_path)
        assert config.socket_path == custom_path

    def test_node_options_custom(self):
        """Test custom node options."""
        custom_options = "--max-old-space-size=4096"
        config = PGliteConfig(node_options=custom_options)
        assert config.node_options == custom_options


class TestPGliteConfigEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_extensions_list(self):
        """Test empty extensions list."""
        config = PGliteConfig(extensions=[])
        assert config.extensions == []

    def test_extensions_none_vs_empty(self):
        """Test None vs empty list for extensions."""
        config1 = PGliteConfig(extensions=None)
        config2 = PGliteConfig(extensions=[])

        assert config1.extensions is None
        assert config2.extensions == []

    def test_socket_path_parent_directory_creation(self):
        """Test socket path parent directory creation."""
        # The _get_secure_socket_path should create the directory
        path = _get_secure_socket_path()
        parent_dir = Path(path).parent

        assert parent_dir.exists()
        assert parent_dir.is_dir()

    @patch("py_pglite.config.Path.mkdir")
    @patch("py_pglite.config.tempfile.gettempdir")
    @patch("py_pglite.config.os.getpid")
    @patch("py_pglite.config.uuid.uuid4")
    def test_socket_path_generation_mocked(
        self, mock_uuid, mock_getpid, mock_tempdir, mock_mkdir
    ):
        """Test socket path generation with mocked components."""
        # Mock the components
        mock_tempdir.return_value = "/mock/tmp"
        mock_getpid.return_value = 12345
        mock_uuid.return_value.hex = "abcdef1234567890abcdef1234567890"

        path = _get_secure_socket_path()

        expected_dir = "/mock/tmp/py-pglite-12345-abcdef12"
        expected_path = f"{expected_dir}/.s.PGSQL.5432"

        assert path == expected_path
        # Verify mkdir was called with correct permissions
        mock_mkdir.assert_called_once_with(mode=0o700, exist_ok=True)

    def test_config_immutability_after_init(self):
        """Test config validation happens during __post_init__."""
        # This should work
        config = PGliteConfig(timeout=10)
        assert config.timeout == 10

        # But modifying after init should still be validated if __post_init__ runs again
        # (though normally you wouldn't call __post_init__ manually)
        config.timeout = -1
        with pytest.raises(ValueError):
            config.__post_init__()


class TestPGliteConfigIntegration:
    """Integration tests for config usage."""

    def test_config_with_all_options(self):
        """Test config with all options specified."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = PGliteConfig(
                timeout=60,
                cleanup_on_exit=False,
                log_level="DEBUG",
                socket_path="/tmp/test-socket/.s.PGSQL.5432",
                work_dir=Path(temp_dir),
                node_modules_check=False,
                auto_install_deps=False,
                extensions=["pgvector"],
                node_options="--max-old-space-size=2048",
            )

            # Verify all settings
            assert config.timeout == 60
            assert config.cleanup_on_exit is False
            assert config.log_level == "DEBUG"
            assert config.socket_path == "/tmp/test-socket/.s.PGSQL.5432"
            assert config.work_dir == Path(temp_dir).resolve()
            assert config.node_modules_check is False
            assert config.auto_install_deps is False
            assert config.extensions == ["pgvector"]
            assert config.node_options == "--max-old-space-size=2048"

            # Test derived properties
            assert config.log_level_int == logging.DEBUG
            assert "postgresql+psycopg://" in config.get_connection_string()
            assert "postgresql://" in config.get_psycopg_uri()
            assert "host=" in config.get_dsn()
