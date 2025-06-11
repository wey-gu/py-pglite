"""Comprehensive configuration testing for py-pglite.

Tests configuration validation, edge cases, and boundary conditions
to ensure robust configuration handling.
"""

import os
import tempfile
from pathlib import Path

import pytest

from py_pglite import PGliteConfig, PGliteManager


class TestPGliteConfigValidation:
    """Test configuration validation and edge cases."""

    def test_default_configuration(self):
        """Test that default configuration is valid and reasonable."""
        config = PGliteConfig()

        # Default values should be reasonable
        assert config.timeout == 30
        assert config.log_level == "INFO"
        assert config.cleanup_on_exit is True
        assert config.socket_path is not None  # Auto-generated
        assert config.work_dir is None
        assert config.node_modules_check is True
        assert config.auto_install_deps is True

    def test_timeout_validation(self):
        """Test timeout validation and boundary conditions."""
        # Valid timeouts
        config = PGliteConfig(timeout=5)
        assert config.timeout == 5

        config = PGliteConfig(timeout=120)
        assert config.timeout == 120

        # Edge case: very short timeout
        config = PGliteConfig(timeout=1)
        assert config.timeout == 1

        # Invalid: negative timeout
        with pytest.raises(ValueError, match="timeout must be positive"):
            PGliteConfig(timeout=-1)

        # Invalid: zero timeout
        with pytest.raises(ValueError, match="timeout must be positive"):
            PGliteConfig(timeout=0)

    def test_log_level_validation(self):
        """Test log level validation."""
        # Valid log levels
        valid_levels = ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
        for level in valid_levels:
            config = PGliteConfig(log_level=level)
            assert config.log_level == level

        # Invalid log level
        with pytest.raises(ValueError, match="Invalid log_level"):
            PGliteConfig(log_level="INVALID")

    def test_socket_path_handling(self):
        """Test socket path handling."""
        # Default socket path should be auto-generated
        config = PGliteConfig()
        assert config.socket_path is not None
        assert ".s.PGSQL.5432" in config.socket_path

        # Valid custom socket path
        with tempfile.TemporaryDirectory() as temp_dir:
            socket_path = os.path.join(temp_dir, ".s.PGSQL.5432")
            config = PGliteConfig(socket_path=socket_path)
            assert config.socket_path == socket_path

    def test_work_dir_handling(self):
        """Test work directory handling."""
        # Default work_dir is None
        config = PGliteConfig()
        assert config.work_dir is None

        # Valid custom work directory
        with tempfile.TemporaryDirectory() as temp_dir:
            config = PGliteConfig(work_dir=Path(temp_dir))
            assert config.work_dir == Path(temp_dir).resolve()

    def test_cleanup_on_exit_validation(self):
        """Test cleanup_on_exit validation."""
        # Valid boolean values
        config = PGliteConfig(cleanup_on_exit=True)
        assert config.cleanup_on_exit is True

        config = PGliteConfig(cleanup_on_exit=False)
        assert config.cleanup_on_exit is False

    def test_node_modules_check_validation(self):
        """Test node_modules_check validation."""
        config = PGliteConfig(node_modules_check=True)
        assert config.node_modules_check is True

        config = PGliteConfig(node_modules_check=False)
        assert config.node_modules_check is False

    def test_auto_install_deps_validation(self):
        """Test auto_install_deps validation."""
        config = PGliteConfig(auto_install_deps=True)
        assert config.auto_install_deps is True

        config = PGliteConfig(auto_install_deps=False)
        assert config.auto_install_deps is False

    def test_log_level_int_property(self):
        """Test log_level_int property."""
        import logging

        config = PGliteConfig(log_level="DEBUG")
        assert config.log_level_int == logging.DEBUG

        config = PGliteConfig(log_level="INFO")
        assert config.log_level_int == logging.INFO

        config = PGliteConfig(log_level="WARNING")
        assert config.log_level_int == logging.WARNING

    def test_connection_string_generation(self):
        """Test connection string generation."""
        config = PGliteConfig()
        conn_str = config.get_connection_string()

        # Should be a valid PostgreSQL connection string
        assert conn_str.startswith("postgresql+psycopg://")
        assert "postgres:postgres@/postgres" in conn_str
        assert "host=" in conn_str


class TestPGliteConfigUsage:
    """Test configuration usage in real scenarios."""

    def test_config_with_manager_startup(self):
        """Test configuration properly affects manager behavior."""
        # Test with custom timeout
        config = PGliteConfig(timeout=15, log_level="DEBUG")
        manager = PGliteManager(config)

        assert manager.config.timeout == 15
        assert manager.config.log_level == "DEBUG"

    def test_multiple_configs_isolation(self):
        """Test that multiple configurations don't interfere."""
        config1 = PGliteConfig(timeout=5, log_level="INFO")
        config2 = PGliteConfig(timeout=20, log_level="DEBUG")

        # Configs should be independent
        assert config1.timeout == 5
        assert config1.log_level == "INFO"
        assert config2.timeout == 20
        assert config2.log_level == "DEBUG"

    def test_config_serialization(self):
        """Test configuration can be represented and debugged."""
        config = PGliteConfig(timeout=30, log_level="DEBUG", cleanup_on_exit=False)

        # Should have reasonable string representation
        config_str = str(config)
        assert "30" in config_str
        assert "DEBUG" in config_str
        assert "False" in config_str

    def test_config_with_custom_work_dir(self):
        """Test configuration with custom work directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = PGliteConfig(work_dir=Path(temp_dir))
            manager = PGliteManager(config)

            assert manager.config.work_dir == Path(temp_dir).resolve()

    def test_config_without_node_modules_check(self):
        """Test configuration with node_modules_check disabled."""
        config = PGliteConfig(node_modules_check=False)
        manager = PGliteManager(config)

        assert manager.config.node_modules_check is False

    def test_config_without_auto_install(self):
        """Test configuration with auto_install_deps disabled."""
        config = PGliteConfig(auto_install_deps=False)
        manager = PGliteManager(config)

        assert manager.config.auto_install_deps is False


class TestConfigurationPerformance:
    """Test configuration performance and efficiency."""

    def test_config_creation_speed(self):
        """Test that configuration creation is fast."""
        import time

        start_time = time.time()

        # Create many configurations quickly
        configs = [PGliteConfig(timeout=i, log_level="INFO") for i in range(1, 51)]

        creation_time = time.time() - start_time

        # Should create 50 configs very quickly
        assert creation_time < 0.1  # Should be much faster than 100ms
        assert len(configs) == 50

        # Each config should be independent
        assert configs[0].timeout == 1
        assert configs[49].timeout == 50

    def test_config_memory_efficiency(self):
        """Test that configurations don't consume excessive memory."""
        # Create many configurations
        configs = [
            PGliteConfig(timeout=10 + i, log_level="INFO", cleanup_on_exit=(i % 2 == 0))
            for i in range(100)
        ]

        # Should all be valid and independent
        assert len(configs) == 100
        assert configs[0].timeout == 10
        assert configs[99].timeout == 109
        assert configs[0].cleanup_on_exit is True
        assert configs[1].cleanup_on_exit is False

    def test_connection_string_consistency(self):
        """Test that connection strings are consistent and valid."""
        # Multiple configs should generate valid connection strings
        configs = [PGliteConfig() for _ in range(10)]

        for config in configs:
            conn_str = config.get_connection_string()
            assert conn_str.startswith("postgresql+psycopg://")
            assert "postgres:postgres@/postgres" in conn_str
