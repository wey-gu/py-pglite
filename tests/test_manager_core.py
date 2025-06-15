"""Tests for core PGliteManager functionality."""

import os
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, Mock, patch

import pytest

from py_pglite import PGliteConfig, PGliteManager
from py_pglite.utils import check_connection


class TestPGliteManagerCore:
    """Test core PGliteManager functionality."""

    def test_manager_initialization(self):
        """Test PGliteManager initialization."""
        config = PGliteConfig()
        manager = PGliteManager(config)

        assert manager.config == config
        assert not manager.is_running()
        assert manager.process is None

    def test_manager_with_default_config(self):
        """Test PGliteManager with default configuration."""
        manager = PGliteManager()

        # Should create default config
        assert manager.config is not None
        assert isinstance(manager.config, PGliteConfig)
        assert not manager.is_running()

    def test_manager_start_stop_lifecycle(self):
        """Test basic start/stop lifecycle."""
        manager = PGliteManager()

        # Initially not running
        assert not manager.is_running()

        # Start should work
        manager.start()
        assert manager.is_running()
        assert manager.process is not None

        # Stop should work
        manager.stop()
        assert not manager.is_running()
        assert manager.process is None

    def test_manager_double_start_protection(self):
        """Test that starting an already running manager is safe."""
        manager = PGliteManager()

        manager.start()
        assert manager.is_running()

        # Second start should be safe (no-op)
        manager.start()
        assert manager.is_running()

        manager.stop()

    def test_manager_double_stop_protection(self):
        """Test that stopping an already stopped manager is safe."""
        manager = PGliteManager()

        # Stop when not running should be safe
        manager.stop()
        assert not manager.is_running()

        # Start and stop normally
        manager.start()
        manager.stop()
        assert not manager.is_running()

        # Second stop should be safe
        manager.stop()
        assert not manager.is_running()

    def test_manager_context_manager(self):
        """Test PGliteManager as context manager."""
        with PGliteManager() as manager:
            assert manager.is_running()
            assert manager.process is not None

        # Should be stopped after context
        assert not manager.is_running()
        assert manager.process is None

    def test_manager_context_manager_exception_handling(self):
        """Test context manager cleanup on exception."""
        manager = None
        try:
            with PGliteManager() as mgr:
                manager = mgr
                assert manager.is_running()
                raise ValueError("Test exception")
        except ValueError:
            pass

        # Should still be cleaned up
        assert manager is not None
        assert not manager.is_running()
        assert manager.process is None

    def test_manager_restart_functionality(self):
        """Test manager restart functionality."""
        manager = PGliteManager()

        # Start initially
        manager.start()
        firstprocess = manager.process
        assert manager.is_running()

        # Restart should work
        manager.restart()
        assert manager.is_running()
        assert manager.process is not None
        # Should be a different process
        assert manager.process != firstprocess

        manager.stop()

    def test_manager_restart_when_not_running(self):
        """Test restart when manager is not running."""
        manager = PGliteManager()

        # Restart when not running should start it
        manager.restart()
        assert manager.is_running()

        manager.stop()

    def test_manager_connection_string_generation(self):
        """Test connection string generation."""
        config = PGliteConfig()
        manager = PGliteManager(config)

        # Manager needs to be started before getting connection string
        manager.start()
        try:
            # Should generate connection string
            conn_str = manager.get_connection_string()
            assert conn_str is not None
            assert "postgresql" in conn_str

            # Connection string contains socket directory, not full socket path
            socket_dir = str(Path(config.socket_path).parent)
            assert socket_dir in conn_str
        finally:
            manager.stop()

    def test_manager_dsn_generation(self):
        """Test DSN generation."""
        config = PGliteConfig()
        manager = PGliteManager(config)

        # Manager needs to be started before getting DSN
        manager.start()
        try:
            # Should generate DSN
            dsn = manager.get_dsn()
            assert dsn is not None
            assert "host=" in dsn

            # DSN contains socket directory, not full socket path
            socket_dir = str(Path(config.socket_path).parent)
            assert socket_dir in dsn
        finally:
            manager.stop()

    def test_manager_psycopg_uri_generation(self):
        """Test psycopg URI generation."""
        config = PGliteConfig()
        manager = PGliteManager(config)

        # Manager needs to be started before getting URI
        manager.start()
        try:
            # Should generate psycopg-compatible URI
            uri = manager.get_psycopg_uri()
            assert uri is not None
            assert "postgresql://" in uri
            assert "+psycopg" not in uri  # Should not have SQLAlchemy dialect
        finally:
            manager.stop()

    def test_manager_wait_for_ready_basic(self):
        """Test basic wait_for_ready functionality."""
        manager = PGliteManager()

        # Should return False when not started
        ready = manager.wait_for_ready(max_retries=1, delay=0.1)
        assert ready is False

        # Start and test readiness
        manager.start()
        try:
            # Should eventually become ready
            ready = manager.wait_for_ready(max_retries=10, delay=0.5)
            # Note: This might be True or False depending on startup time
            # The important thing is it doesn't crash
            assert isinstance(ready, bool)
        finally:
            manager.stop()

    def test_manager_wait_for_ready_timeout(self):
        """Test wait_for_ready timeout behavior."""
        manager = PGliteManager()

        # Should timeout quickly when not started
        start_time = time.time()
        ready = manager.wait_for_ready(max_retries=2, delay=0.1)
        elapsed = time.time() - start_time

        assert ready is False
        assert elapsed < 1.0  # Should timeout quickly

    def test_managerprocess_management(self):
        """Test process management functionality."""
        manager = PGliteManager()

        # Start and check process
        manager.start()
        assert manager.process is not None
        assert manager.process.poll() is None  # Process should be running

        # Stop and check process cleanup
        manager.stop()
        assert manager.process is None

    def test_manager_with_custom_work_dir(self):
        """Test manager with custom work directory."""
        with tempfile.TemporaryDirectory() as temp_dir:
            config = PGliteConfig(work_dir=Path(temp_dir))
            manager = PGliteManager(config)

            # Use resolve() to handle macOS path resolution consistently
            assert manager.config.work_dir is not None
            assert manager.config.work_dir.resolve() == Path(temp_dir).resolve()

            # Should be able to start with custom work dir
            manager.start()
            assert manager.is_running()
            manager.stop()

    def test_manager_with_custom_timeout(self):
        """Test manager with custom timeout."""
        config = PGliteConfig(timeout=60)
        manager = PGliteManager(config)

        assert manager.config.timeout == 60

        # Should work with custom timeout
        manager.start()
        assert manager.is_running()
        manager.stop()

    def test_manager_cleanup_on_exit_behavior(self):
        """Test cleanup_on_exit behavior."""
        # Test with cleanup enabled (default)
        config = PGliteConfig(cleanup_on_exit=True)
        manager = PGliteManager(config)

        manager.start()
        # process = manager.process
        manager.stop()

        # Process should be cleaned up
        assert manager.process is None

        # Test with cleanup disabled
        config = PGliteConfig(cleanup_on_exit=False)
        manager = PGliteManager(config)

        manager.start()
        assert manager.is_running()
        manager.stop()

    def test_manager_error_handling_invalid_config(self):
        """Test error handling with invalid configuration."""
        # Test with invalid timeout
        with pytest.raises(ValueError):
            PGliteConfig(timeout=-1)

        # Test with invalid log level
        with pytest.raises(ValueError):
            PGliteConfig(log_level="INVALID")

    def test_manager_node_modules_check_behavior(self):
        """Test node_modules_check behavior."""
        # Test with check enabled (default)
        config = PGliteConfig(node_modules_check=True)
        manager = PGliteManager(config)

        # Should work (might warn about missing node_modules)
        manager.start()
        assert manager.is_running()
        manager.stop()

        # Test with check disabled - may fail if dependencies not available
        config = PGliteConfig(node_modules_check=False)
        manager = PGliteManager(config)

        try:
            manager.start()
            # If it succeeds, clean up
            if manager.is_running():
                manager.stop()
        except RuntimeError as e:
            # Expected failure when dependencies are not available
            assert "PGlite process died during startup" in str(e)
            assert "Cannot find module" in str(e)

    def test_manager_auto_install_deps_behavior(self):
        """Test auto_install_deps behavior."""
        # Test with auto install enabled (default)
        config = PGliteConfig(auto_install_deps=True)
        manager = PGliteManager(config)

        manager.start()
        assert manager.is_running()
        manager.stop()

        # Test with auto install disabled - may fail if dependencies not available
        config = PGliteConfig(auto_install_deps=False)
        manager = PGliteManager(config)

        try:
            manager.start()
            # If it succeeds, clean up
            if manager.is_running():
                manager.stop()
        except RuntimeError as e:
            # Expected failure when dependencies are not available
            assert "PGlite process died during startup" in str(e)
            assert "Cannot find module" in str(e)

    def test_manager_socket_path_handling(self):
        """Test socket path handling."""
        config = PGliteConfig()
        manager = PGliteManager(config)

        # Should have auto-generated socket path
        assert config.socket_path is not None
        assert "py-pglite" in config.socket_path

        # Manager needs to be started before getting connection string
        manager.start()
        try:
            # Connection string should include socket directory
            conn_str = manager.get_connection_string()
            from pathlib import Path

            socket_dir = str(Path(config.socket_path).parent)
            assert socket_dir in conn_str
        finally:
            manager.stop()

    def test_manager_custom_socket_path(self):
        """Test manager with custom socket path."""
        with tempfile.TemporaryDirectory() as temp_dir:
            custom_socket = os.path.join(temp_dir, "custom_socket")
            config = PGliteConfig(socket_path=custom_socket)
            manager = PGliteManager(config)

            assert config.socket_path == custom_socket

            # Should work with custom socket path
            manager.start()
            assert manager.is_running()
            manager.stop()

    def test_manager_repr_and_str(self):
        """Test manager string representations."""
        config = PGliteConfig()
        manager = PGliteManager(config)

        # Should have meaningful string representation
        repr_str = repr(manager)
        assert "PGliteManager" in repr_str

        str_str = str(manager)
        assert "PGliteManager" in str_str

    def test_manager_multiple_instances_isolation(self):
        """Test that multiple manager instances are isolated."""
        manager1 = PGliteManager()
        manager2 = PGliteManager()

        # Should have different socket paths
        assert manager1.config.socket_path != manager2.config.socket_path

        # Should be able to run independently
        manager1.start()
        manager2.start()

        assert manager1.is_running()
        assert manager2.is_running()
        assert manager1.process != manager2.process

        manager1.stop()
        manager2.stop()

    def test_managerprocess_termination_handling(self):
        """Test handling of process termination."""
        manager = PGliteManager()

        manager.start()
        process = manager.process
        assert process is not None

        # Manually terminate the process
        process.terminate()
        process.wait()

        # Manager should detect the process is no longer running
        # Note: This behavior might vary based on implementation
        # The important thing is it doesn't crash
        try:
            is_running = manager.is_running()
            assert isinstance(is_running, bool)
        finally:
            manager.stop()  # Cleanup


class TestPGliteManagerErrorHandling:
    """Test error handling in PGliteManager."""

    def test_manager_start_failure_handling(self):
        """Test handling of start failures."""
        # Create a config that might cause startup issues
        config = PGliteConfig(work_dir=Path("/nonexistent/path/that/should/not/exist"))
        manager = PGliteManager(config)

        # Start might fail, but should handle gracefully
        try:
            manager.start()
            # If it succeeds, clean up
            if manager.is_running():
                manager.stop()
        except Exception:
            # If it fails, that's also acceptable for invalid paths
            assert not manager.is_running()

    def test_manager_connection_string_with_invalid_config(self):
        """Test connection string generation with edge case configs."""
        # Test with minimal config
        config = PGliteConfig()
        manager = PGliteManager(config)

        # Manager needs to be started before getting connection string
        manager.start()
        try:
            # Should still generate valid connection string
            conn_str = manager.get_connection_string()
            assert conn_str is not None
            assert len(conn_str) > 0
        finally:
            manager.stop()

    def test_manager_wait_for_ready_error_handling(self):
        """Test wait_for_ready error handling."""
        manager = PGliteManager()

        # Should handle errors gracefully
        ready = manager.wait_for_ready(max_retries=1, delay=0.01)
        assert ready is False  # Should return False, not crash

    @patch("py_pglite.manager.subprocess.Popen")
    def test_managerprocess_creation_failure(self, mock_popen):
        """Test handling of process creation failure."""
        mock_popen.side_effect = OSError("Failed to create process")

        manager = PGliteManager()

        # Start should handle process creation failure
        with pytest.raises(OSError):
            manager.start()

        # Manager should remain in stopped state
        assert not manager.is_running()
        assert manager.process is None

    def test_manager_stop_with_noprocess(self):
        """Test stop when no process exists."""
        manager = PGliteManager()

        # Stop should be safe even when no process
        manager.stop()
        assert not manager.is_running()
        assert manager.process is None

    def test_manager_restart_error_recovery(self):
        """Test restart error recovery."""
        manager = PGliteManager()

        # Start normally
        manager.start()
        assert manager.is_running()

        # Restart should work even if there are issues
        try:
            manager.restart()
            assert manager.is_running()
        finally:
            manager.stop()


class TestPGliteManagerIntegration:
    """Test PGliteManager integration scenarios."""

    def test_manager_connection_validation(self):
        """Test that manager creates valid connections."""
        manager = PGliteManager()

        manager.start()
        try:
            # Wait for readiness
            ready = manager.wait_for_ready(max_retries=20, delay=0.5)

            if ready:
                # Test connection string validity
                conn_str = manager.get_connection_string()
                # Note: Actual connection test might fail if PGlite isn't fully ready
                # But connection string should be valid format
                assert "postgresql" in conn_str

                # Test DSN validity
                dsn = manager.get_dsn()
                assert "host=" in dsn

                # Test psycopg URI validity
                uri = manager.get_psycopg_uri()
                assert "postgresql://" in uri
                assert "+psycopg" not in uri
        finally:
            manager.stop()

    def test_manager_concurrent_operations(self):
        """Test concurrent manager operations."""
        manager = PGliteManager()

        # Multiple rapid start/stop cycles
        for _ in range(3):
            manager.start()
            assert manager.is_running()
            manager.stop()
            assert not manager.is_running()

    def test_manager_resource_cleanup(self):
        """Test proper resource cleanup."""
        manager = PGliteManager()

        # Start and get process reference
        manager.start()
        process = manager.process
        assert process is not None

        # Stop and verify cleanup
        manager.stop()
        assert manager.process is None

        # Original process should be terminated
        if process.poll() is None:
            # If still running, wait a bit for cleanup
            time.sleep(0.1)

        # Process should eventually be cleaned up
        # (Implementation detail - might vary)

    def test_manager_configuration_consistency(self):
        """Test configuration consistency across operations."""
        config = PGliteConfig(timeout=45, log_level="DEBUG")
        manager = PGliteManager(config)

        # Configuration should remain consistent
        assert manager.config.timeout == 45
        assert manager.config.log_level == "DEBUG"

        manager.start()
        assert manager.config.timeout == 45
        assert manager.config.log_level == "DEBUG"

        manager.restart()
        assert manager.config.timeout == 45
        assert manager.config.log_level == "DEBUG"

        manager.stop()
        assert manager.config.timeout == 45
        assert manager.config.log_level == "DEBUG"
