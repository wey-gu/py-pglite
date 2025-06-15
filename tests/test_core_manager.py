"""Core PGliteManager functionality tests."""

import os
import subprocess
import tempfile
from pathlib import Path

import psutil
import pytest
from sqlalchemy import text

from py_pglite import PGliteConfig, PGliteManager
from py_pglite.sqlalchemy import SQLAlchemyPGliteManager


class TestPGliteConfig:
    """Test PGliteConfig functionality."""

    def test_default_config(self):
        """Test default configuration values."""
        config = PGliteConfig()

        assert config.timeout == 30
        assert config.log_level == "INFO"
        assert config.cleanup_on_exit is True
        assert config.work_dir is None

    def test_custom_config(self):
        """Test custom configuration values."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = PGliteConfig(
                timeout=60,
                log_level="DEBUG",
                cleanup_on_exit=False,
                work_dir=Path(temp_dir),
            )

            assert config.timeout == 60
            assert config.log_level == "DEBUG"
            assert config.cleanup_on_exit is False
            # Path resolution may resolve symlinks, so check resolved paths
            assert config.work_dir is not None
            assert config.work_dir.resolve() == Path(temp_dir).resolve()


class TestPGliteManagerLifecycle:
    """Test PGliteManager lifecycle management."""

    def test_basic_start_stop(self):
        """Test basic start and stop functionality."""
        manager = PGliteManager()

        # Initially not running
        assert not manager.is_running()

        # Start
        manager.start()
        assert manager.is_running()

        # Stop
        manager.stop()
        assert not manager.is_running()

    def test_context_manager(self):
        """Test context manager functionality."""
        with PGliteManager() as manager:
            assert manager.is_running()

        # Should be stopped after context exit
        assert not manager.is_running()

    def test_double_start_is_safe(self):
        """Test that calling start() twice is safe."""
        manager = PGliteManager()

        try:
            manager.start()
            assert manager.is_running()

            # Second start should be safe
            manager.start()
            assert manager.is_running()
        finally:
            manager.stop()


class TestSQLAlchemyManagerEngineCreation:
    """Test SQLAlchemy engine creation and management."""

    def test_get_engine_requires_running_manager(self):
        """Test that get_engine() requires manager to be running."""
        manager = SQLAlchemyPGliteManager()

        with pytest.raises(RuntimeError, match="not running"):
            manager.get_engine()

    def test_get_engine_basic(self):
        """Test basic engine creation."""
        with SQLAlchemyPGliteManager() as manager:
            engine = manager.get_engine()

            # Should be able to connect and query
            with engine.connect() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()[0]
                assert "PostgreSQL" in version


class TestPGliteManagerErrorHandling:
    """Test the error handling capabilities of the PGliteManager."""

    def test_socket_cleanup_failure(self, mocker):
        """Test that the manager handles a failure to clean up the socket."""
        mocker.patch("pathlib.Path.unlink", side_effect=OSError("Permission denied"))
        with PGliteManager():
            # The context manager should still exit cleanly
            pass
        # The test passes if no unhandled exception is raised

    def test_kill_process_failure(self, mocker):
        """Test that the manager handles a failure to kill an existing process."""
        mocker.patch("psutil.Process.kill", side_effect=psutil.NoSuchProcess(pid=12345))
        # The test passes if the manager starts without raising an unhandled exception
        with PGliteManager():
            pass

    def test_npm_install_timeout(self, mocker):
        """Test that the manager handles a timeout during npm install."""
        mocker.patch(
            "subprocess.run",
            side_effect=subprocess.TimeoutExpired(cmd="npm install", timeout=1),
        )
        config = PGliteConfig(auto_install_deps=True, node_modules_check=True)

        # Create a dummy work_dir that is missing node_modules to trigger install
        with tempfile.TemporaryDirectory() as temp_dir:
            config.work_dir = Path(temp_dir)
            with pytest.raises(subprocess.TimeoutExpired):
                with PGliteManager(config=config):
                    pass
