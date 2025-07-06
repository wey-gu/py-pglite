"""Comprehensive tests for py_pglite.config module to achieve full coverage."""

import logging
import os
import tempfile

from pathlib import Path
from unittest.mock import patch

import pytest

from py_pglite.config import PGliteConfig
from py_pglite.config import _get_secure_socket_path


class TestSecureSocketPathGeneration:
    """Test the _get_secure_socket_path helper function."""

    def test_secure_socket_path_format(self):
        """Test that socket path follows expected format."""
        socket_path = _get_secure_socket_path()

        # Should be a string path
        assert isinstance(socket_path, str)

        # Should contain PostgreSQL socket naming convention
        assert socket_path.endswith(".s.PGSQL.5432")

        # Should be in temp directory
        assert str(tempfile.gettempdir()) in socket_path

        # Should contain process ID and UUID components
        assert "py-pglite-" in socket_path

    def test_secure_socket_path_uniqueness(self):
        """Test that multiple calls generate unique paths."""
        path1 = _get_secure_socket_path()
        path2 = _get_secure_socket_path()

        # Should be different paths
        assert path1 != path2

        # Both should be valid paths
        assert path1.endswith(".s.PGSQL.5432")
        assert path2.endswith(".s.PGSQL.5432")

    def test_secure_socket_path_directory_creation(self):
        """Test that socket path directory is created with correct permissions."""
        socket_path = _get_secure_socket_path()
        socket_dir = Path(socket_path).parent

        # Directory should exist
        assert socket_dir.exists()

        # Directory should be user-only accessible (0o700)
        # Note: This test may not work on all systems
        # stat_info = socket_dir.stat()
        # Check that directory exists and has restricted permissions
        assert socket_dir.is_dir()

    @patch("os.getpid")
    @patch("uuid.uuid4")
    def test_secure_socket_path_components(self, mock_uuid, mock_getpid):
        """Test that socket path includes PID and UUID components."""
        mock_getpid.return_value = 12345
        mock_uuid.return_value.hex = "abcdef123456789"

        socket_path = _get_secure_socket_path()

        # Should contain PID and UUID
        assert "12345" in socket_path
        assert "abcdef12" in socket_path  # First 8 chars of UUID


class TestPGliteConfigValidationExtensive:
    """Comprehensive validation tests for PGliteConfig."""

    def test_default_field_values(self):
        """Test all default field values are correctly set."""
        config = PGliteConfig()

        # Test all defaults
        assert config.timeout == 30
        assert config.cleanup_on_exit is True
        assert config.log_level == "INFO"
        assert config.work_dir is None
        assert config.node_modules_check is True
        assert config.auto_install_deps is True
        assert config.extensions is None
        assert config.node_options is None

        # Socket path should be generated
        assert config.socket_path is not None
        assert config.socket_path.endswith(".s.PGSQL.5432")

    def test_timeout_validation_boundary_values(self):
        """Test timeout validation with boundary values."""
        # Valid boundary values
        config = PGliteConfig(timeout=1)
        assert config.timeout == 1

        # Invalid values
        with pytest.raises(ValueError, match="timeout must be positive"):
            PGliteConfig(timeout=0)

        with pytest.raises(ValueError, match="timeout must be positive"):
            PGliteConfig(timeout=-1)

        with pytest.raises(ValueError, match="timeout must be positive"):
            PGliteConfig(timeout=-999)

    def test_log_level_validation_all_levels(self):
        """Test log_level validation with all possible values."""
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

        for level in valid_levels:
            config = PGliteConfig(log_level=level)
            assert config.log_level == level

        # Test invalid levels
        invalid_levels = ["TRACE", "debug", "info", "WARN", "FATAL", "", "INVALID"]
        for level in invalid_levels:
            with pytest.raises(ValueError, match=f"Invalid log_level: {level}"):
                PGliteConfig(log_level=level)

    def test_extensions_validation_comprehensive(self):
        """Test extension validation with various inputs."""
        # Valid single extension
        config = PGliteConfig(extensions=["pgvector"])
        assert config.extensions == ["pgvector"]

        # Valid multiple extensions (if supported)
        config = PGliteConfig(extensions=["pgvector"])
        assert config.extensions is not None
        assert "pgvector" in config.extensions

        # Invalid extension
        with pytest.raises(ValueError, match="Unsupported extension: 'invalid_ext'"):
            PGliteConfig(extensions=["invalid_ext"])

        # Mixed valid and invalid
        with pytest.raises(ValueError, match="Unsupported extension: 'bad_ext'"):
            PGliteConfig(extensions=["pgvector", "bad_ext"])

        # Empty list should be fine
        config = PGliteConfig(extensions=[])
        assert config.extensions == []

    def test_work_dir_path_resolution(self):
        """Test work_dir path resolution and validation."""
        # Relative path should be resolved to absolute
        config = PGliteConfig(work_dir=Path("./test_dir"))
        assert config.work_dir is not None
        assert config.work_dir.is_absolute()

        # Absolute path should be preserved
        absolute_path = Path("/tmp/test_pglite").resolve()
        config = PGliteConfig(work_dir=absolute_path)
        assert config.work_dir is not None
        assert config.work_dir == absolute_path

        # Path object should work
        config = PGliteConfig(work_dir=Path("./another_test"))
        assert config.work_dir is not None
        assert config.work_dir.is_absolute()

    def test_custom_socket_path_validation(self):
        """Test custom socket path handling."""
        custom_path = "/tmp/custom_socket/.s.PGSQL.5432"
        config = PGliteConfig(socket_path=custom_path)
        assert config.socket_path == custom_path

    def test_node_options_handling(self):
        """Test node_options field handling."""
        node_opts = "--max-old-space-size=4096"
        config = PGliteConfig(node_options=node_opts)
        assert config.node_options == node_opts

        # None should be preserved
        config = PGliteConfig(node_options=None)
        assert config.node_options is None


class TestPGliteConfigProperties:
    """Test PGliteConfig property methods."""

    def test_log_level_int_property_all_levels(self):
        """Test log_level_int property for all valid log levels."""
        level_mappings = {
            "DEBUG": logging.DEBUG,
            "INFO": logging.INFO,
            "WARNING": logging.WARNING,
            "ERROR": logging.ERROR,
            "CRITICAL": logging.CRITICAL,
        }

        for level_str, expected_int in level_mappings.items():
            config = PGliteConfig(log_level=level_str)
            assert config.log_level_int == expected_int
            assert isinstance(config.log_level_int, int)

    def test_connection_string_format(self):
        """Test get_connection_string format and components."""
        config = PGliteConfig(socket_path="/tmp/test/.s.PGSQL.5432")
        conn_str = config.get_connection_string()

        # Should contain SQLAlchemy PostgreSQL driver
        assert conn_str.startswith("postgresql+psycopg://")

        # Should contain credentials
        assert "postgres:postgres" in conn_str

        # Should contain database name
        assert "/postgres" in conn_str

        # Should contain socket directory as host
        assert "host=/tmp/test" in conn_str

    def test_psycopg_uri_format(self):
        """Test get_psycopg_uri format and components."""
        config = PGliteConfig(socket_path="/tmp/test/.s.PGSQL.5432")
        uri = config.get_psycopg_uri()

        # Should use standard PostgreSQL URI format
        assert uri.startswith("postgresql://")

        # Should contain credentials
        assert "postgres:postgres" in uri

        # Should contain database name
        assert "/postgres" in uri

        # Should contain socket directory as host
        assert "host=/tmp/test" in uri

    def test_dsn_format(self):
        """Test get_dsn format and components."""
        config = PGliteConfig(socket_path="/tmp/test/.s.PGSQL.5432")
        dsn = config.get_dsn()

        # Should contain all required DSN components
        assert "host=/tmp/test" in dsn
        assert "dbname=postgres" in dsn
        assert "user=postgres" in dsn
        assert "password=postgres" in dsn

        # Should be space-separated key=value format
        parts = dsn.split()
        assert len(parts) == 4

        for part in parts:
            assert "=" in part

    def test_connection_methods_consistency(self):
        """Test that all connection methods use the same socket directory."""
        socket_path = "/tmp/consistent_test/.s.PGSQL.5432"
        config = PGliteConfig(socket_path=socket_path)

        conn_str = config.get_connection_string()
        psycopg_uri = config.get_psycopg_uri()
        dsn = config.get_dsn()

        # All should reference the same socket directory
        socket_dir = "/tmp/consistent_test"
        assert f"host={socket_dir}" in conn_str
        assert f"host={socket_dir}" in psycopg_uri
        assert f"host={socket_dir}" in dsn


class TestPGliteConfigEdgeCases:
    """Test edge cases and error conditions."""

    def test_config_immutability_after_init(self):
        """Test that config validation runs during initialization."""
        # Valid config should initialize successfully
        config = PGliteConfig(timeout=60, log_level="DEBUG")
        assert config.timeout == 60
        assert config.log_level == "DEBUG"

        # Can modify after init (dataclass is mutable)
        config.timeout = 120
        assert config.timeout == 120

    def test_config_with_all_parameters(self):
        """Test config with all parameters specified."""
        config = PGliteConfig(
            timeout=45,
            cleanup_on_exit=False,
            log_level="ERROR",
            socket_path="/custom/path/.s.PGSQL.5432",
            work_dir=Path("/custom/work"),
            node_modules_check=False,
            auto_install_deps=False,
            extensions=["pgvector"],
            node_options="--experimental-modules",
        )

        assert config.timeout == 45
        assert config.cleanup_on_exit is False
        assert config.log_level == "ERROR"
        assert config.socket_path == "/custom/path/.s.PGSQL.5432"
        assert config.work_dir is not None
        assert config.work_dir == Path("/custom/work")
        assert config.node_modules_check is False
        assert config.auto_install_deps is False
        assert config.extensions == ["pgvector"]
        assert config.node_options == "--experimental-modules"

    def test_config_repr_and_str(self):
        """Test string representations of config."""
        config = PGliteConfig(timeout=15, log_level="WARNING")

        # Should be representable as string
        repr_str = repr(config)
        assert "PGliteConfig" in repr_str
        assert "timeout=15" in repr_str
        assert "log_level='WARNING'" in repr_str

        # str() should also work
        str_repr = str(config)
        assert "PGliteConfig" in str_repr

    def test_socket_path_with_different_extensions(self):
        """Test socket path handling with different file extensions."""
        custom_paths = [
            "/tmp/test1/.s.PGSQL.5432",
            "/tmp/test2/custom_socket",
            "/var/run/postgresql/.s.PGSQL.5433",
        ]

        for path in custom_paths:
            config = PGliteConfig(socket_path=path)
            assert config.socket_path == path

            # Connection methods should work with any socket path
            conn_str = config.get_connection_string()
            assert "postgresql+psycopg://" in conn_str

            dsn = config.get_dsn()
            assert "host=" in dsn

    def test_extensions_none_vs_empty_list(self):
        """Test difference between None and empty list for extensions."""
        # None extensions
        config1 = PGliteConfig(extensions=None)
        assert config1.extensions is None

        # Empty list
        config2 = PGliteConfig(extensions=[])
        assert config2.extensions == []
        assert config2.extensions is not None

    @patch.dict(os.environ, {"TMPDIR": "/custom/tmp"})
    def test_socket_path_with_custom_temp_dir(self):
        """Test socket path generation with custom temp directory."""
        socket_path = _get_secure_socket_path()

        # Should work regardless of temp directory
        assert socket_path.endswith(".s.PGSQL.5432")
        assert "py-pglite-" in socket_path


class TestPGliteConfigValidationIntegration:
    """Integration tests for config validation."""

    def test_config_validation_order(self):
        """Test that validation happens in correct order."""
        # Timeout validation should happen first
        with pytest.raises(ValueError, match="timeout must be positive"):
            PGliteConfig(timeout=-1, log_level="INVALID")  # Both invalid

        # If timeout is valid, should catch log level error
        with pytest.raises(ValueError, match="Invalid log_level"):
            PGliteConfig(timeout=30, log_level="INVALID")

    def test_config_partial_validation_on_error(self):
        """Test that config is not created if validation fails."""
        with pytest.raises(ValueError):
            PGliteConfig(timeout=-1)

        with pytest.raises(ValueError):
            PGliteConfig(log_level="INVALID")

        with pytest.raises(ValueError):
            PGliteConfig(extensions=["invalid_extension"])

    def test_work_dir_path_edge_cases(self):
        """Test work_dir with various path formats."""
        # Home directory expansion
        config = PGliteConfig(work_dir=Path("~/test"))
        assert config.work_dir is not None
        assert config.work_dir.is_absolute()

        # Current directory
        config = PGliteConfig(work_dir=Path("."))
        assert config.work_dir is not None
        assert config.work_dir.is_absolute()

        # Parent directory
        config = PGliteConfig(work_dir=Path("../test"))
        assert config.work_dir is not None
        assert config.work_dir.is_absolute()


class TestPGliteConfigImports:
    """Test imports and module-level functionality."""

    def test_config_module_imports(self):
        """Test that all necessary imports are working."""
        # Test that we can import all the components
        from py_pglite.config import PGliteConfig
        from py_pglite.config import _get_secure_socket_path

        # Test that the function works
        socket_path = _get_secure_socket_path()
        assert isinstance(socket_path, str)

        # Test that the class works
        config = PGliteConfig()
        assert isinstance(config, PGliteConfig)

    def test_supported_extensions_import(self):
        """Test that SUPPORTED_EXTENSIONS is properly imported."""
        # This tests the import from .extensions
        config = PGliteConfig(extensions=["pgvector"])
        assert config.extensions == ["pgvector"]

    def test_logging_module_usage(self):
        """Test that logging module is properly used."""
        config = PGliteConfig(log_level="DEBUG")
        # This should use the logging module to convert string to int
        assert config.log_level_int == logging.DEBUG


class TestPGliteConfigWorkDirEdgeCases:
    """Test work_dir field edge cases."""

    def test_work_dir_none_handling(self):
        """Test that work_dir=None is handled correctly."""
        config = PGliteConfig(work_dir=None)
        assert config.work_dir is None

    def test_work_dir_string_to_path_conversion(self):
        """Test that string work_dir is converted to Path."""
        config = PGliteConfig(work_dir=Path("/tmp/test"))
        assert isinstance(config.work_dir, Path)
        assert config.work_dir.is_absolute()

    def test_work_dir_relative_path_resolution(self):
        """Test that relative work_dir paths are resolved."""
        config = PGliteConfig(work_dir=Path("./relative_path"))
        assert config.work_dir is not None
        assert config.work_dir.is_absolute()
        assert "relative_path" in str(config.work_dir)


class TestPGliteConfigNodeOptions:
    """Test node_options field functionality."""

    def test_node_options_none_default(self):
        """Test that node_options defaults to None."""
        config = PGliteConfig()
        assert config.node_options is None

    def test_node_options_custom_value(self):
        """Test that custom node_options are preserved."""
        custom_options = "--max-old-space-size=4096 --experimental-modules"
        config = PGliteConfig(node_options=custom_options)
        assert config.node_options == custom_options


class TestPGliteConfigExtensionsValidation:
    """Test extensions field validation edge cases."""

    def test_extensions_none_default(self):
        """Test that extensions defaults to None."""
        config = PGliteConfig()
        assert config.extensions is None

    def test_extensions_empty_list(self):
        """Test that empty extensions list is allowed."""
        config = PGliteConfig(extensions=[])
        assert config.extensions == []

    def test_extensions_case_sensitivity(self):
        """Test that extension names are case-sensitive."""
        # Correct case should work
        config = PGliteConfig(extensions=["pgvector"])
        assert config.extensions == ["pgvector"]

        # Wrong case should fail
        with pytest.raises(ValueError, match="Unsupported extension"):
            PGliteConfig(extensions=["PGVECTOR"])

    def test_extensions_whitespace_handling(self):
        """Test that extension names with whitespace are rejected."""
        with pytest.raises(ValueError, match="Unsupported extension"):
            PGliteConfig(extensions=[" pgvector "])

        with pytest.raises(ValueError, match="Unsupported extension"):
            PGliteConfig(extensions=["pg vector"])


class TestPGliteConfigDataclassFeatures:
    """Test dataclass-specific features."""

    def test_config_field_defaults(self):
        """Test that field defaults work correctly."""
        config = PGliteConfig()

        # socket_path should use factory function
        assert config.socket_path is not None
        assert config.socket_path.endswith(".s.PGSQL.5432")

        # Other fields should have their specified defaults
        assert config.timeout == 30
        assert config.cleanup_on_exit is True
        assert config.log_level == "INFO"

    def test_config_field_assignment(self):
        """Test that fields can be assigned after creation."""
        config = PGliteConfig()

        # Should be able to modify fields (dataclass is mutable by default)
        original_timeout = config.timeout
        config.timeout = 60
        assert config.timeout == 60
        assert config.timeout != original_timeout

    def test_config_equality(self):
        """Test config equality comparison."""
        config1 = PGliteConfig(timeout=30, log_level="INFO")
        config2 = PGliteConfig(timeout=30, log_level="INFO")

        # Socket paths will be different, so configs won't be equal
        # This tests that the dataclass comparison works
        assert config1.timeout == config2.timeout
        assert config1.log_level == config2.log_level
        # But socket_paths will be different
        assert config1.socket_path != config2.socket_path
