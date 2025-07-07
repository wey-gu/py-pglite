"""Tests for configuration edge cases and validation."""

import logging
import os
import tempfile

from pathlib import Path

import pytest

from py_pglite.config import PGliteConfig
from py_pglite.config import _get_secure_socket_path


def test_default_config_values():
    """Test that default configuration values are sensible."""
    config = PGliteConfig()

    assert config.timeout == 30
    assert config.cleanup_on_exit is True
    assert config.log_level == "INFO"
    assert config.socket_path is not None
    assert config.work_dir is None
    assert config.node_modules_check is True
    assert config.auto_install_deps is True
    assert config.extensions is None
    assert config.node_options is None


def test_config_timeout_validation():
    """Test timeout validation."""
    # Valid timeout
    config = PGliteConfig(timeout=60)
    assert config.timeout == 60

    # Zero timeout should raise error
    with pytest.raises(ValueError, match="timeout must be positive"):
        PGliteConfig(timeout=0)

    # Negative timeout should raise error
    with pytest.raises(ValueError, match="timeout must be positive"):
        PGliteConfig(timeout=-1)


def test_config_log_level_validation():
    """Test log level validation."""
    # Valid log levels
    valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    for level in valid_levels:
        config = PGliteConfig(log_level=level)
        assert config.log_level == level

    # Invalid log level should raise error
    with pytest.raises(ValueError, match="Invalid log_level: INVALID"):
        PGliteConfig(log_level="INVALID")

    # Case sensitivity check
    with pytest.raises(ValueError, match="Invalid log_level: info"):
        PGliteConfig(log_level="info")


def test_log_level_int_property():
    """Test log_level_int property returns correct integer values."""
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


def test_work_dir_resolution():
    """Test work_dir path resolution."""
    # Test with relative path
    config = PGliteConfig(work_dir=Path("./test_dir"))
    assert config.work_dir == Path("./test_dir").resolve()

    # Test with absolute path
    abs_path = Path.cwd() / "test_absolute"
    config = PGliteConfig(work_dir=abs_path)
    assert config.work_dir == abs_path

    # Test with Path object
    config = PGliteConfig(work_dir=Path("./test_path"))
    assert config.work_dir == Path("./test_path").resolve()


def test_secure_socket_path_generation():
    """Test secure socket path generation."""
    # Test the function directly
    socket_path1 = _get_secure_socket_path()
    socket_path2 = _get_secure_socket_path()

    # Should be different each time (due to PID)
    assert socket_path1 != socket_path2 or str(os.getpid()) in socket_path1

    # Should contain PostgreSQL socket naming convention
    assert ".s.PGSQL.5432" in socket_path1

    # Should be in temp directory
    assert str(Path(tempfile.gettempdir())) in socket_path1


def test_socket_path_customization():
    """Test custom socket path configuration."""
    custom_path = "/tmp/custom_pglite_socket/.s.PGSQL.5432"
    config = PGliteConfig(socket_path=custom_path)
    assert config.socket_path == custom_path


def test_connection_string_generation():
    """Test PostgreSQL connection string generation."""
    config = PGliteConfig()
    conn_str = config.get_connection_string()

    assert conn_str.startswith("postgresql+psycopg://")
    assert "postgres:postgres@" in conn_str
    assert "/postgres" in conn_str
    assert "host=" in conn_str


def test_dsn_generation():
    """Test PostgreSQL DSN generation."""
    config = PGliteConfig()
    dsn = config.get_dsn()

    assert "host=" in dsn
    assert "dbname=postgres" in dsn
    assert "user=postgres" in dsn
    assert "password=postgres" in dsn


def test_socket_path_consistency():
    """Test that socket path is consistent between connection methods."""
    config = PGliteConfig()

    # Extract socket directory from connection string
    conn_str = config.get_connection_string()
    dsn = config.get_dsn()

    # Both should reference the same socket directory
    socket_dir = str(Path(config.socket_path).parent)
    assert socket_dir in conn_str
    assert socket_dir in dsn


def test_config_immutability_after_init():
    """Test that configuration behaves correctly after initialization."""
    config = PGliteConfig(timeout=45)

    # Should maintain the configured value
    assert config.timeout == 45

    # Post-init validation should have run
    assert hasattr(config, "log_level_int")


def test_config_with_all_parameters():
    """Test configuration with all parameters specified."""
    custom_socket = "/tmp/test_pglite/.s.PGSQL.5432"
    custom_work_dir = Path("/tmp/test_work")

    config = PGliteConfig(
        timeout=120,
        cleanup_on_exit=False,
        log_level="DEBUG",
        socket_path=custom_socket,
        work_dir=custom_work_dir,
        node_modules_check=False,
        auto_install_deps=False,
        extensions=["pgvector"],
        node_options="--max-old-space-size=4096",
    )

    assert config.timeout == 120
    assert config.cleanup_on_exit is False
    assert config.log_level == "DEBUG"
    assert config.socket_path == custom_socket
    assert config.work_dir == custom_work_dir.resolve()
    assert config.node_modules_check is False
    assert config.auto_install_deps is False
    assert config.extensions == ["pgvector"]
    assert config.node_options == "--max-old-space-size=4096"


def test_config_boolean_parameters():
    """Test boolean parameter handling."""
    # Test cleanup_on_exit combinations
    config1 = PGliteConfig(cleanup_on_exit=True)
    assert config1.cleanup_on_exit is True

    config2 = PGliteConfig(cleanup_on_exit=False)
    assert config2.cleanup_on_exit is False

    # Test node_modules_check combinations
    config3 = PGliteConfig(node_modules_check=True)
    assert config3.node_modules_check is True

    config4 = PGliteConfig(node_modules_check=False)
    assert config4.node_modules_check is False

    # Test auto_install_deps combinations
    config5 = PGliteConfig(auto_install_deps=True)
    assert config5.auto_install_deps is True

    config6 = PGliteConfig(auto_install_deps=False)
    assert config6.auto_install_deps is False


def test_config_extension_none_vs_empty_list():
    """Test difference between None and empty list for extensions."""
    # None extensions
    config1 = PGliteConfig(extensions=None)
    assert config1.extensions is None

    # Empty list
    config2 = PGliteConfig(extensions=[])
    assert config2.extensions == []

    # They should be different
    assert config1.extensions != config2.extensions


def test_config_string_parameters():
    """Test string parameter validation and handling."""
    # Test node_options with various values
    node_options_tests = [
        None,
        "",
        "--max-old-space-size=2048",
        "--inspect --max-old-space-size=4096",
    ]

    for node_opt in node_options_tests:
        config = PGliteConfig(node_options=node_opt)
        assert config.node_options == node_opt


def test_config_path_edge_cases():
    """Test path handling edge cases."""
    # Test with home directory expansion
    if os.path.expanduser("~") != "~":  # Only if home exists
        config = PGliteConfig(work_dir=Path("~/test_pglite").expanduser())
        # work_dir should be resolved to absolute path
        assert config.work_dir is not None
        assert config.work_dir.is_absolute()

    # Test with current directory
    config = PGliteConfig(work_dir=Path("."))
    assert config.work_dir == Path.cwd()

    # Test with parent directory
    config = PGliteConfig(work_dir=Path(".."))
    assert config.work_dir == Path.cwd().parent


def test_config_repr_and_str():
    """Test string representation of configuration."""
    config = PGliteConfig(timeout=60, log_level="DEBUG")

    # Should be able to convert to string without errors
    str_repr = str(config)
    assert isinstance(str_repr, str)

    # Should contain some key information
    repr_str = repr(config)
    assert "PGliteConfig" in repr_str


@pytest.mark.parametrize("invalid_timeout", [-5, -1, 0])
def test_config_invalid_timeouts(invalid_timeout):
    """Test various invalid timeout values."""
    with pytest.raises(ValueError, match="timeout must be positive"):
        PGliteConfig(timeout=invalid_timeout)


@pytest.mark.parametrize("valid_timeout", [1, 30, 60, 300, 3600])
def test_config_valid_timeouts(valid_timeout):
    """Test various valid timeout values."""
    config = PGliteConfig(timeout=valid_timeout)
    assert config.timeout == valid_timeout
