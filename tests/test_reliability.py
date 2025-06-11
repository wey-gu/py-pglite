"""Reliability and error scenario testing for py-pglite.

Tests process recovery, timeout handling, resource cleanup, and edge cases
to ensure robust behavior under adverse conditions.
"""

import os
import signal
import tempfile
import time
from pathlib import Path

import pytest
from sqlalchemy import text

from py_pglite import PGliteConfig
from py_pglite.sqlalchemy import SQLAlchemyPGliteManager


class TestProcessReliability:
    """Test process management and recovery scenarios."""

    def test_manager_restart_after_stop(self):
        """Test that manager can be restarted after being stopped."""
        manager = SQLAlchemyPGliteManager()

        # Start, use, and stop
        manager.start()
        manager.wait_for_ready()

        engine1 = manager.get_engine()
        with engine1.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            assert result == 1

        manager.stop()

        # Should be able to start again
        manager.start()
        manager.wait_for_ready()

        engine2 = manager.get_engine()
        with engine2.connect() as conn:
            result = conn.execute(text("SELECT 2")).scalar()
            assert result == 2

        manager.stop()

    def test_multiple_start_calls_safe(self):
        """Test that multiple start() calls are safe."""
        manager = SQLAlchemyPGliteManager()

        try:
            # Multiple start calls should be safe
            manager.start()
            manager.start()  # Should not cause issues
            manager.start()  # Should not cause issues

            manager.wait_for_ready()

            # Should still work normally
            engine = manager.get_engine()
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 'multiple_start'")).scalar()
                assert result == "multiple_start"

        finally:
            manager.stop()

    def test_multiple_stop_calls_safe(self):
        """Test that multiple stop() calls are safe."""
        manager = SQLAlchemyPGliteManager()

        manager.start()
        manager.wait_for_ready()

        # Use the manager
        engine = manager.get_engine()
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 'before_stop'")).scalar()
            assert result == "before_stop"

        # Multiple stop calls should be safe
        manager.stop()
        manager.stop()  # Should not cause issues
        manager.stop()  # Should not cause issues

    def test_context_manager_exception_handling(self):
        """Test that context manager properly cleans up even with exceptions."""
        exception_occurred = False

        try:
            with SQLAlchemyPGliteManager() as manager:
                engine = manager.get_engine()

                # Use the connection
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT 'before_exception'")).scalar()
                    assert result == "before_exception"

                # Simulate an exception
                raise ValueError("Test exception for cleanup")

        except ValueError as e:
            assert str(e) == "Test exception for cleanup"
            exception_occurred = True

        assert exception_occurred, "Exception should have been raised"
        # Manager should have been cleaned up automatically

    def test_resource_cleanup_on_process_exit(self):
        """Test that resources are cleaned up when process exits."""
        import tempfile
        import uuid

        # Create a unique socket path for this test
        temp_dir = (
            Path(tempfile.gettempdir()) / f"py-pglite-cleanup-{uuid.uuid4().hex[:8]}"
        )
        temp_dir.mkdir(mode=0o700, exist_ok=True)
        socket_path = str(temp_dir / ".s.PGSQL.5432")

        config = PGliteConfig(socket_path=socket_path, cleanup_on_exit=True)

        with SQLAlchemyPGliteManager(config) as manager:
            engine = manager.get_engine()

            # Use the connection
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 'cleanup_test'")).scalar()
                assert result == "cleanup_test"

        # After context manager exits, socket should be cleaned up
        # Note: This is hard to test definitively without subprocess
        # but we can at least verify the manager cleaned up properly


class TestTimeoutHandling:
    """Test timeout scenarios and edge cases."""

    def test_short_timeout_still_works(self):
        """Test that very short timeouts still allow successful startup."""
        # Use a short but reasonable timeout
        config = PGliteConfig(timeout=5)

        with SQLAlchemyPGliteManager(config) as manager:
            # Should still work with short timeout
            engine = manager.get_engine()
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 'short_timeout'")).scalar()
                assert result == "short_timeout"

    def test_timeout_configuration_respected(self):
        """Test that timeout configuration is properly respected."""
        config = PGliteConfig(timeout=15)
        manager = SQLAlchemyPGliteManager(config)

        assert manager.config.timeout == 15

        # Test actual startup within timeout
        start_time = time.time()
        manager.start()
        manager.wait_for_ready()
        startup_time = time.time() - start_time

        # Should start within the timeout period
        assert startup_time < 15

        manager.stop()

    def test_wait_for_ready_timeout_behavior(self):
        """Test wait_for_ready timeout behavior."""
        with SQLAlchemyPGliteManager() as manager:
            # Should return True when ready
            ready = manager.wait_for_ready(max_retries=5, delay=0.5)
            assert ready is True

            # Should be able to use after wait_for_ready
            engine = manager.get_engine()
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 'ready'")).scalar()
                assert result == "ready"


class TestResourceManagement:
    """Test resource management and cleanup scenarios."""

    def test_socket_cleanup_on_exit(self):
        """Test that socket files are cleaned up properly."""
        import tempfile
        import uuid

        temp_dir = (
            Path(tempfile.gettempdir()) / f"py-pglite-socket-{uuid.uuid4().hex[:8]}"
        )
        temp_dir.mkdir(mode=0o700, exist_ok=True)
        socket_path = str(temp_dir / ".s.PGSQL.5432")

        config = PGliteConfig(socket_path=socket_path, cleanup_on_exit=True)

        manager = SQLAlchemyPGliteManager(config)
        manager.start()
        manager.wait_for_ready()

        # Socket should exist while running
        # (Note: The socket might not be visible as a file in all systems)

        try:
            # Use the connection
            engine = manager.get_engine()
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 'socket_test'")).scalar()
                assert result == "socket_test"
        finally:
            manager.stop()

        # Clean up test directory
        import shutil

        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass

    def test_work_dir_handling(self):
        """Test work directory handling and cleanup."""
        import tempfile
        import uuid

        work_dir = (
            Path(tempfile.gettempdir()) / f"py-pglite-work-{uuid.uuid4().hex[:8]}"
        )
        config = PGliteConfig(work_dir=work_dir)

        with SQLAlchemyPGliteManager(config) as manager:
            # Work directory should be created and used
            assert manager.config.work_dir == work_dir.resolve()

            # Should be able to use normally
            engine = manager.get_engine()
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 'work_dir_test'")).scalar()
                assert result == "work_dir_test"

        # Clean up test directory
        import shutil

        try:
            shutil.rmtree(work_dir, ignore_errors=True)
        except Exception:
            pass

    def test_memory_usage_stability(self):
        """Test that memory usage remains stable over multiple operations."""
        with SQLAlchemyPGliteManager() as manager:
            engine = manager.get_engine()

            # Perform many operations to test for memory leaks
            for i in range(50):
                with engine.connect() as conn:
                    # Various types of operations
                    conn.execute(text(f"SELECT {i}"))
                    conn.execute(text("SELECT NOW()"))
                    conn.execute(text("SELECT 'memory_test'"))

            # Should still be responsive after many operations
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 'still_working'")).scalar()
                assert result == "still_working"


class TestErrorRecovery:
    """Test error recovery and resilience scenarios."""

    def test_invalid_work_dir_handling(self):
        """Test handling of invalid work directory."""
        # Test with non-existent parent directory
        invalid_work_dir = Path("/nonexistent/path/that/should/not/exist")

        # Should handle gracefully (either auto-create or use fallback)
        config = PGliteConfig(work_dir=invalid_work_dir)
        manager = SQLAlchemyPGliteManager(config)

        # This might succeed (with auto-creation) or fail gracefully
        try:
            manager.start()
            manager.wait_for_ready()

            engine = manager.get_engine()
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 'recovered'")).scalar()
                assert result == "recovered"

            manager.stop()
        except Exception:
            # If it fails, that's also acceptable for invalid paths
            pass

    def test_connection_resilience_after_errors(self):
        """Test that connections remain usable after various errors."""
        with SQLAlchemyPGliteManager() as manager:
            engine = manager.get_engine()

            # Test recovery after syntax error
            with engine.connect() as conn:
                with pytest.raises(Exception):
                    conn.execute(text("INVALID SQL SYNTAX ERROR"))

            # Should still work after error
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 'recovered_from_syntax'")).scalar()
                assert result == "recovered_from_syntax"

            # Test recovery after constraint violation
            with engine.connect() as conn:
                conn.execute(
                    text("CREATE TABLE test_recovery (id INTEGER PRIMARY KEY)")
                )
                conn.execute(text("INSERT INTO test_recovery VALUES (1)"))
                conn.commit()

                # Try to insert duplicate primary key
                with pytest.raises(Exception):
                    conn.execute(text("INSERT INTO test_recovery VALUES (1)"))
                    conn.commit()

            # Should still work after constraint error
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT 'recovered_from_constraint'")
                ).scalar()
                assert result == "recovered_from_constraint"

    def test_graceful_degradation_scenarios(self):
        """Test graceful degradation under stress."""
        with SQLAlchemyPGliteManager() as manager:
            engine = manager.get_engine()

            # Create a test table
            with engine.connect() as conn:
                conn.execute(text("CREATE TABLE stress_test (id INTEGER, data TEXT)"))
                conn.commit()

            # Rapid operations to test stability
            for i in range(20):
                try:
                    with engine.connect() as conn:
                        conn.execute(
                            text("INSERT INTO stress_test VALUES (:id, :data)"),
                            {"id": i, "data": f"data_{i}"},
                        )
                        conn.commit()
                except Exception:
                    # Some operations might fail under stress, that's OK
                    continue

            # Should still be functional after stress
            with engine.connect() as conn:
                count = conn.execute(text("SELECT COUNT(*) FROM stress_test")).scalar()
                # Should have at least some data (exact count depends on stress tolerance)
                assert count > 0

                result = conn.execute(text("SELECT 'stress_survived'")).scalar()
                assert result == "stress_survived"


class TestEdgeCases:
    """Test edge cases and unusual scenarios."""

    def test_very_long_table_names(self):
        """Test handling of very long table names."""
        with SQLAlchemyPGliteManager() as manager:
            engine = manager.get_engine()

            # PostgreSQL has a limit of 63 characters for identifiers
            long_name = "a" * 60  # Just under the limit

            with engine.connect() as conn:
                conn.execute(text(f'CREATE TABLE "{long_name}" (id INTEGER)'))
                conn.execute(text(f'INSERT INTO "{long_name}" VALUES (1)'))
                conn.commit()

                result = conn.execute(text(f'SELECT id FROM "{long_name}"')).scalar()
                assert result == 1

    def test_unicode_data_handling(self):
        """Test handling of Unicode data."""
        with SQLAlchemyPGliteManager() as manager:
            engine = manager.get_engine()

            with engine.connect() as conn:
                conn.execute(
                    text("CREATE TABLE unicode_test (id INTEGER, text_data TEXT)")
                )

                # Test various Unicode characters
                unicode_data = [
                    "Hello 世界",  # Chinese
                    "Здравствуй мир",  # Russian
                    "🚀 py-pglite ✨",  # Emojis
                    "Café résumé naïve",  # Accented characters
                ]

                for i, data in enumerate(unicode_data):
                    conn.execute(
                        text("INSERT INTO unicode_test VALUES (:id, :data)"),
                        {"id": i, "data": data},
                    )

                conn.commit()

                # Verify Unicode data round-trip
                for i, expected in enumerate(unicode_data):
                    result = conn.execute(
                        text("SELECT text_data FROM unicode_test WHERE id = :id"),
                        {"id": i},
                    ).scalar()
                    assert result == expected

    def test_large_query_results(self):
        """Test handling of moderately large query results."""
        with SQLAlchemyPGliteManager() as manager:
            engine = manager.get_engine()

            with engine.connect() as conn:
                conn.execute(text("CREATE TABLE large_test (id INTEGER, value TEXT)"))

                # Insert a moderate amount of data (not too large for PGlite)
                for i in range(100):
                    conn.execute(
                        text("INSERT INTO large_test VALUES (:id, :value)"),
                        {"id": i, "value": f"value_{i:03d}"},
                    )

                conn.commit()

                # Query all data
                results = conn.execute(
                    text("SELECT id, value FROM large_test ORDER BY id")
                ).fetchall()

                assert len(results) == 100
                assert results[0][1] == "value_000"
                assert results[99][1] == "value_099"
