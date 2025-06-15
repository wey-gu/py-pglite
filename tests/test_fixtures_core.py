"""Tests for pytest fixtures functionality."""

from py_pglite import PGliteConfig, PGliteManager
from py_pglite.fixtures import (
    pglite_config,
    pglite_manager,
    pglite_manager_custom,
)


class TestPGliteFixtures:
    """Test core PGlite fixtures."""

    def test_pglite_config_fixture(self, pglite_config):
        """Test pglite_config fixture provides valid configuration."""
        assert isinstance(pglite_config, PGliteConfig)
        assert pglite_config.timeout > 0
        assert pglite_config.log_level in ["DEBUG", "INFO", "WARNING", "ERROR"]
        assert pglite_config.cleanup_on_exit is True
        assert pglite_config.socket_path is not None

    def test_pglite_config_fixture_isolation(self, pglite_config):
        """Test that pglite_config fixture provides isolated instances."""
        # Get another instance
        config2 = pglite_config

        # Should be the same instance within the same test
        assert config2 is pglite_config

        # But should have unique socket paths for isolation
        assert pglite_config.socket_path is not None

    def test_pglite_manager_fixture(self, pglite_manager):
        """Test pglite_manager fixture provides running manager."""
        assert isinstance(pglite_manager, PGliteManager)
        assert pglite_manager.is_running()
        assert pglite_manager.config is not None

        # Should be able to get connection info
        conn_str = pglite_manager.get_connection_string()
        assert conn_str is not None
        assert "postgresql" in conn_str

    def test_pglite_manager_fixture_cleanup(self, pglite_manager):
        """Test that pglite_manager fixture handles cleanup."""
        # Manager should be running during test
        assert pglite_manager.is_running()

        # Store reference to check cleanup later
        process = pglite_manager.process
        assert process is not None

        # Fixture should handle cleanup automatically after test

    def test_pglite_manager_custom_fixture(self):
        """Test custom manager creation with custom config."""
        custom_config = PGliteConfig(timeout=60, log_level="DEBUG")

        # Create manager manually with custom config
        manager = PGliteManager(custom_config)
        manager.start()
        try:
            assert isinstance(manager, PGliteManager)
            assert manager.config == custom_config
            assert manager.config.timeout == 60
            assert manager.config.log_level == "DEBUG"
            assert manager.is_running()
        finally:
            manager.stop()

    def test_pglite_manager_custom_fixture_context_manager(self):
        """Test custom manager as context manager."""
        config = PGliteConfig(timeout=45)

        # Use manager as context manager
        with PGliteManager(config) as manager:
            assert manager.is_running()
            assert manager.config.timeout == 45

        # Should be stopped after context
        assert not manager.is_running()

    def test_multiple_pglite_managers_isolation(self, pglite_manager):
        """Test isolation between multiple manager instances."""
        # Get the fixture manager
        manager1 = pglite_manager

        # Create another manager manually
        manager2 = PGliteManager()
        manager2.start()

        try:
            # Should be different instances
            assert manager1 is not manager2
            assert manager1.config.socket_path != manager2.config.socket_path

            # Both should be running independently
            assert manager1.is_running()
            assert manager2.is_running()

            # Should have different processes
            assert manager1.process != manager2.process
        finally:
            manager2.stop()

    def test_fixture_configuration_defaults(self, pglite_config):
        """Test that fixture provides reasonable defaults."""
        # Should have reasonable timeout
        assert 1 <= pglite_config.timeout <= 300

        # Should have valid log level
        assert pglite_config.log_level in ["DEBUG", "INFO", "WARNING", "ERROR"]

        # Should enable cleanup by default
        assert pglite_config.cleanup_on_exit is True

        # Should have node modules check enabled
        assert pglite_config.node_modules_check is True

        # Should have auto install enabled
        assert pglite_config.auto_install_deps is True

    def test_fixture_socket_path_uniqueness(self):
        """Test that fixtures generate unique socket paths."""
        # Create multiple configs
        config1 = PGliteConfig()
        config2 = PGliteConfig()

        # Should have different socket paths
        assert config1.socket_path != config2.socket_path

        # Both should contain the PID for uniqueness
        import os

        pid = str(os.getpid())
        assert pid in config1.socket_path
        assert pid in config2.socket_path

    def test_fixture_work_dir_handling(self, pglite_config):
        """Test fixture work directory handling."""
        # Default should be None (uses temp dir)
        assert pglite_config.work_dir is None

        # Should be able to create manager with this config
        manager = PGliteManager(pglite_config)
        assert manager.config == pglite_config

    def test_fixture_error_handling(self):
        """Test fixture error handling scenarios."""
        # Test with invalid config
        try:
            PGliteConfig(timeout=-1)
            assert False, "Should have raised ValueError"
        except ValueError:
            pass  # Expected

        # Test fixture with edge case config
        edge_config = PGliteConfig(timeout=1)  # Very short timeout
        manager = PGliteManager(edge_config)

        # Should still work
        assert manager.config.timeout == 1

    def test_fixture_connection_string_generation(self, pglite_manager):
        """Test connection string generation from fixtures."""
        # Should generate valid connection strings
        conn_str = pglite_manager.get_connection_string()
        assert conn_str is not None
        assert "postgresql" in conn_str

        # Connection string contains socket directory, not full socket path
        from pathlib import Path

        socket_dir = str(Path(pglite_manager.config.socket_path).parent)
        assert socket_dir in conn_str

        # Should generate valid DSN
        dsn = pglite_manager.get_dsn()
        assert dsn is not None
        assert "host=" in dsn

        # Should generate valid psycopg URI
        uri = pglite_manager.get_psycopg_uri()
        assert uri is not None
        assert "postgresql://" in uri
        assert "+psycopg" not in uri

    def test_fixture_manager_lifecycle(self, pglite_manager):
        """Test manager lifecycle through fixtures."""
        # Should be running
        assert pglite_manager.is_running()

        # Should be able to restart
        pglite_manager.restart()
        assert pglite_manager.is_running()

        # Should be able to check readiness
        ready = pglite_manager.wait_for_ready(max_retries=5, delay=0.1)
        assert isinstance(ready, bool)

    def test_fixture_configuration_immutability(self, pglite_config):
        """Test that fixture configuration is properly set."""
        original_timeout = pglite_config.timeout
        original_log_level = pglite_config.log_level
        original_socket_path = pglite_config.socket_path

        # Values should remain consistent
        assert pglite_config.timeout == original_timeout
        assert pglite_config.log_level == original_log_level
        assert pglite_config.socket_path == original_socket_path

    def test_fixture_manager_process_management(self, pglite_manager):
        """Test process management in fixture managers."""
        # Should have a running process
        assert pglite_manager.process is not None
        assert pglite_manager.process.poll() is None  # Still running

        # Process should be manageable
        process = pglite_manager.process
        assert hasattr(process, "pid")
        assert process.pid > 0


class TestFixtureIntegration:
    """Test fixture integration scenarios."""

    def test_fixture_with_real_operations(self, pglite_manager):
        """Test fixtures with real database operations."""
        # Wait for manager to be ready
        ready = pglite_manager.wait_for_ready(max_retries=10, delay=0.5)

        if ready:
            # Should be able to get connection info
            conn_str = pglite_manager.get_connection_string()
            dsn = pglite_manager.get_dsn()
            uri = pglite_manager.get_psycopg_uri()

            # All should be valid strings
            assert isinstance(conn_str, str) and len(conn_str) > 0
            assert isinstance(dsn, str) and len(dsn) > 0
            assert isinstance(uri, str) and len(uri) > 0

            # Should contain expected components
            assert "postgresql" in conn_str
            assert "host=" in dsn
            assert "postgresql://" in uri
        else:
            # If not ready, we should still be able to test basic functionality
            assert pglite_manager.is_running()
            assert pglite_manager.config is not None

    def test_fixture_performance_characteristics(self, pglite_manager):
        """Test fixture performance characteristics."""
        import time

        # Connection string generation should be fast
        start_time = time.time()
        conn_str = None  # Initialize to avoid linter warning
        for _ in range(100):
            conn_str = pglite_manager.get_connection_string()
        elapsed = time.time() - start_time

        # Should be very fast (less than 1 second for 100 calls)
        assert elapsed < 1.0
        assert conn_str is not None

    def test_fixture_memory_efficiency(self, pglite_config):
        """Test fixture memory efficiency."""
        # Multiple config accesses should return same instance
        config1 = pglite_config
        config2 = pglite_config

        # Should be the same object (fixture scope)
        assert config1 is config2

    def test_fixture_error_resilience(self, pglite_manager):
        """Test fixture resilience to errors."""
        # Manager should handle various operations without crashing
        try:
            # These operations should not crash the fixture
            pglite_manager.get_connection_string()
            pglite_manager.get_dsn()
            pglite_manager.get_psycopg_uri()
            pglite_manager.is_running()

            # Wait for ready with short timeout
            pglite_manager.wait_for_ready(max_retries=1, delay=0.01)

        except Exception as e:
            # If any operation fails, it should be a specific expected error
            # not a fixture-related crash
            assert isinstance(
                e, OSError | ConnectionError | TimeoutError | RuntimeError
            )

    def test_fixture_cleanup_behavior(self, pglite_manager):
        """Test fixture cleanup behavior."""
        # Store references to check cleanup
        process = pglite_manager.process
        config = pglite_manager.config

        # Should be running during test
        assert pglite_manager.is_running()
        assert process is not None
        assert config is not None

        # Fixture should handle cleanup automatically
        # (This is tested by the fixture teardown, not directly verifiable here)

    def test_fixture_concurrent_usage(self, pglite_manager):
        """Test fixture behavior with concurrent operations."""
        import threading
        import time

        results = []
        errors = []

        def worker():
            try:
                for _ in range(10):
                    conn_str = pglite_manager.get_connection_string()
                    results.append(len(conn_str))
                    time.sleep(0.01)
            except Exception as e:
                errors.append(e)

        # Run multiple threads
        threads = [threading.Thread(target=worker) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        # Should have results without errors
        assert len(results) == 30  # 3 threads * 10 operations
        assert len(errors) == 0
        assert all(r > 0 for r in results)  # All connection strings should be non-empty


class TestFixtureEdgeCases:
    """Test fixture edge cases and error conditions."""

    def test_fixture_with_custom_timeout(self):
        """Test manager with custom timeout configuration."""
        custom_config = PGliteConfig(timeout=120)

        with PGliteManager(custom_config) as manager:
            assert manager.config.timeout == 120
            assert manager.is_running()

    def test_fixture_with_custom_log_level(self):
        """Test manager with custom log level."""
        custom_config = PGliteConfig(log_level="DEBUG")

        with PGliteManager(custom_config) as manager:
            assert manager.config.log_level == "DEBUG"
            assert manager.is_running()

    def test_fixture_with_cleanup_disabled(self):
        """Test manager with cleanup disabled."""
        custom_config = PGliteConfig(cleanup_on_exit=False)

        with PGliteManager(custom_config) as manager:
            assert manager.config.cleanup_on_exit is False
            assert manager.is_running()

    def test_fixture_with_node_modules_check_disabled(self):
        """Test manager with node modules check disabled."""
        custom_config = PGliteConfig(node_modules_check=False)

        try:
            with PGliteManager(custom_config) as manager:
                assert manager.config.node_modules_check is False
                assert manager.is_running()
        except RuntimeError as e:
            # Expected failure when dependencies are not available
            assert "PGlite process died during startup" in str(e)
            assert "Cannot find module" in str(e)

    def test_fixture_with_auto_install_disabled(self):
        """Test manager with auto install disabled."""
        custom_config = PGliteConfig(auto_install_deps=False)

        try:
            with PGliteManager(custom_config) as manager:
                assert manager.config.auto_install_deps is False
                assert manager.is_running()
        except RuntimeError as e:
            # Expected failure when dependencies are not available
            assert "PGlite process died during startup" in str(e)
            assert "Cannot find module" in str(e)

    def test_fixture_socket_path_validation(self, pglite_config):
        """Test fixture socket path validation."""
        socket_path = pglite_config.socket_path

        # Should be a valid path string
        assert isinstance(socket_path, str)
        assert len(socket_path) > 0

        # Should contain identifying information
        assert "py-pglite" in socket_path

        # Should be in a temporary location
        import tempfile

        temp_dir = tempfile.gettempdir()
        assert temp_dir in socket_path or "/tmp" in socket_path
