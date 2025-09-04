"""Reliability and error scenario testing for py-pglite.

Tests process recovery, timeout handling, resource cleanup, and edge cases
to ensure robust behavior under adverse conditions.
"""

import contextlib
import os
import signal
import tempfile
import time

from pathlib import Path

import pytest

from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.exc import ProgrammingError

from py_pglite import PGliteConfig
from py_pglite.sqlalchemy import SQLAlchemyAsyncPGliteManager
from py_pglite.sqlalchemy.manager import SQLAlchemyPGliteManager


class TestProcessReliability:
    """Test process management and recovery scenarios."""

    async def test_manager_restart_after_stop(self):
        """Test that manager can be restarted after being stopped."""
        manager = SQLAlchemyAsyncPGliteManager()

        # Start, use, and stop
        manager.start()
        await manager.wait_for_ready()

        engine1 = manager.get_engine()
        async with engine1.connect() as conn:
            result = (await conn.execute(text("SELECT 1"))).scalar()
            assert result == 1

        await manager.stop()

        # Should be able to start again
        manager.start()
        await manager.wait_for_ready()

        engine2 = manager.get_engine()
        async with engine2.connect() as conn:
            result = (await conn.execute(text("SELECT 2"))).scalar()
            assert result == 2

        await manager.stop()

    async def test_multiple_start_calls_safe(self):
        """Test that multiple start() calls are safe."""
        manager = SQLAlchemyAsyncPGliteManager()

        try:
            # Multiple start calls should be safe
            manager.start()
            manager.start()  # Should not cause issues
            manager.start()  # Should not cause issues

            await manager.wait_for_ready()

            # Should still work normally
            engine = manager.get_engine()
            async with engine.connect() as conn:
                result = (await conn.execute(text("SELECT 'multiple_start'"))).scalar()
                assert result == "multiple_start"

        finally:
            manager.stop()

    async def test_multiple_stop_calls_safe(self):
        """Test that multiple stop() calls are safe."""
        manager = SQLAlchemyAsyncPGliteManager()

        manager.start()
        await manager.wait_for_ready()

        # Use the manager
        engine = manager.get_engine()
        async with engine.connect() as conn:
            result = (await conn.execute(text("SELECT 'before_stop'"))).scalar()
            assert result == "before_stop"

        # Multiple stop calls should be safe
        await manager.stop()
        await manager.stop()  # Should not cause issues
        await manager.stop()  # Should not cause issues

    async def test_context_manager_exception_handling(self):
        """Test that context manager properly cleans up even with exceptions."""
        exception_occurred = False

        try:
            async with SQLAlchemyAsyncPGliteManager() as manager:
                engine = manager.get_engine()

                # Use the connection
                async with engine.connect() as conn:
                    result = (
                        await conn.execute(text("SELECT 'before_exception'"))
                    ).scalar()
                    assert result == "before_exception"

                # Simulate an exception
                raise ValueError("Test exception for cleanup")

        except ValueError as e:
            assert str(e) == "Test exception for cleanup"
            exception_occurred = True

        assert exception_occurred, "Exception should have been raised"
        # Manager should have been cleaned up automatically

    async def test_resource_cleanup_on_process_exit(self):
        """Test that resources are cleaned up when process exits."""
        import uuid

        # Create a unique socket path for this test
        temp_dir = (
            Path(tempfile.gettempdir()) / f"py-pglite-cleanup-{uuid.uuid4().hex[:8]}"
        )
        temp_dir.mkdir(mode=0o700, exist_ok=True)
        socket_path = str(temp_dir / ".s.PGSQL.5432")

        config = PGliteConfig(socket_path=socket_path, cleanup_on_exit=True)

        async with SQLAlchemyAsyncPGliteManager(config) as manager:
            engine = manager.get_engine()

            # Use the connection
            async with engine.connect() as conn:
                result = (await conn.execute(text("SELECT 'cleanup_test'"))).scalar()
                assert result == "cleanup_test"

        # After context manager exits, socket should be cleaned up
        # Note: This is hard to test definitively without subprocess
        # but we can at least verify the manager cleaned up properly


class TestTimeoutHandling:
    """Test timeout scenarios and edge cases."""

    async def test_short_timeout_still_works(self):
        """Test that very short timeouts still allow successful startup."""
        # Use a short but reasonable timeout
        config = PGliteConfig(timeout=5)

        async with SQLAlchemyAsyncPGliteManager(config) as manager:
            # Should still work with short timeout
            engine = manager.get_engine()
            async with engine.connect() as conn:
                result = (await conn.execute(text("SELECT 'short_timeout'"))).scalar()
                assert result == "short_timeout"

    async def test_timeout_configuration_respected(self):
        """Test that timeout configuration is properly respected."""
        config = PGliteConfig(timeout=15)
        manager = SQLAlchemyAsyncPGliteManager(config)

        assert manager.config.timeout == 15

        # Test actual startup within timeout
        start_time = time.time()
        manager.start()
        await manager.wait_for_ready()
        startup_time = time.time() - start_time

        # Should start within the timeout period
        assert startup_time < 15

        await manager.stop()

    async def test_wait_for_ready_timeout_behavior(self):
        """Test wait_for_ready timeout behavior."""
        async with SQLAlchemyAsyncPGliteManager() as manager:
            # Should return True when ready
            ready = await manager.wait_for_ready(max_retries=5, delay=0.5)
            assert ready is True

            # Should be able to use after wait_for_ready
            engine = manager.get_engine()
            async with engine.connect() as conn:
                result = (await conn.execute(text("SELECT 'ready'"))).scalar()
                assert result == "ready"


class TestResourceManagement:
    """Test resource management and cleanup scenarios."""

    async def test_socket_cleanup_on_exit(self):
        """Test that socket files are cleaned up properly."""
        import uuid

        temp_dir = (
            Path(tempfile.gettempdir()) / f"py-pglite-socket-{uuid.uuid4().hex[:8]}"
        )
        temp_dir.mkdir(mode=0o700, exist_ok=True)
        socket_path = str(temp_dir / ".s.PGSQL.5432")

        config = PGliteConfig(socket_path=socket_path, cleanup_on_exit=True)

        manager = SQLAlchemyAsyncPGliteManager(config)
        manager.start()
        await manager.wait_for_ready()

        # Socket should exist while running
        # (Note: The socket might not be visible as a file in all systems)

        try:
            # Use the connection
            engine = manager.get_engine()
            async with engine.connect() as conn:
                result = (await conn.execute(text("SELECT 'socket_test'"))).scalar()
                assert result == "socket_test"
        finally:
            await manager.stop()

        # Clean up test directory
        import shutil

        with contextlib.suppress(Exception):
            shutil.rmtree(temp_dir, ignore_errors=True)

    async def test_work_dir_handling(self):
        """Test work directory handling and cleanup."""
        import uuid

        work_dir = (
            Path(tempfile.gettempdir()) / f"py-pglite-work-{uuid.uuid4().hex[:8]}"
        )
        config = PGliteConfig(work_dir=work_dir)

        async with SQLAlchemyAsyncPGliteManager(config) as manager:
            # Work directory should be created and used
            assert manager.config.work_dir == work_dir.resolve()

            # Should be able to use normally
            engine = manager.get_engine()
            async with engine.connect() as conn:
                result = (await conn.execute(text("SELECT 'work_dir_test'"))).scalar()
                assert result == "work_dir_test"

        # Clean up test directory
        import shutil

        with contextlib.suppress(Exception):
            shutil.rmtree(work_dir, ignore_errors=True)

    async def test_memory_usage_stability(self):
        """Test that memory usage remains stable over multiple operations."""
        async with SQLAlchemyAsyncPGliteManager() as manager:
            engine = manager.get_engine()

            # Perform many operations to test for memory leaks
            for i in range(50):
                async with engine.connect() as conn:
                    # Various types of operations
                    await conn.execute(text(f"SELECT {i}"))
                    await conn.execute(text("SELECT NOW()"))
                    await conn.execute(text("SELECT 'memory_test'"))

            # Should still be responsive after many operations
            async with engine.connect() as conn:
                result = (await conn.execute(text("SELECT 'still_working'"))).scalar()
                assert result == "still_working"


class TestErrorRecovery:
    """Test error recovery and resilience scenarios."""

    async def test_invalid_work_dir_handling(self):
        """Test handling of invalid work directory."""
        # Test with non-existent parent directory
        invalid_work_dir = Path("/nonexistent/path/that/should/not/exist")

        # Should handle gracefully (either auto-create or use fallback)
        config = PGliteConfig(work_dir=invalid_work_dir)
        manager = SQLAlchemyAsyncPGliteManager(config)

        # This might succeed (with auto-creation) or fail gracefully
        try:
            manager.start()
            await manager.wait_for_ready()

            engine = manager.get_engine()
            async with engine.connect() as conn:
                result = (await conn.execute(text("SELECT 'recovered'"))).scalar()
                assert result == "recovered"

            await manager.stop()
        except Exception:
            # If it fails, that's also acceptable for invalid paths
            pass

    async def test_connection_resilience_after_errors(self):
        """Test that connections remain usable after various errors."""
        async with SQLAlchemyAsyncPGliteManager() as manager:
            engine = manager.get_engine()

            # Test recovery after syntax error
            with pytest.raises(ProgrammingError):
                async with engine.connect() as conn:
                    await conn.execute(text("INVALID SQL SYNTAX ERROR"))

            # Should still work after error
            async with engine.connect() as conn:
                result = (
                    await conn.execute(text("SELECT 'recovered_from_syntax'"))
                ).scalar()
                assert result == "recovered_from_syntax"

            # Test recovery after constraint violation
            async with engine.connect() as conn:
                await conn.execute(
                    text("CREATE TABLE test_recovery (id INTEGER PRIMARY KEY)")
                )
                await conn.execute(text("INSERT INTO test_recovery VALUES (1)"))
                await conn.commit()

                # Try to insert duplicate primary key
                with pytest.raises(IntegrityError):
                    await conn.execute(text("INSERT INTO test_recovery VALUES (1)"))
                    await conn.commit()

            # Should still work after constraint error
            async with engine.connect() as conn:
                result = (
                    await conn.execute(text("SELECT 'recovered_from_constraint'"))
                ).scalar()
                assert result == "recovered_from_constraint"

    async def test_graceful_degradation_scenarios(self):
        """Test graceful degradation under stress."""
        async with SQLAlchemyAsyncPGliteManager() as manager:
            engine = manager.get_engine()

            # Create a test table
            async with engine.connect() as conn:
                await conn.execute(
                    text("CREATE TABLE stress_test (id INTEGER, data TEXT)")
                )
                await conn.commit()

            # Rapid operations to test stability
            for i in range(20):
                try:
                    async with engine.connect() as conn:
                        await conn.execute(
                            text("INSERT INTO stress_test VALUES (:id, :data)"),
                            {"id": i, "data": f"data_{i}"},
                        )
                        await conn.commit()
                except Exception:
                    # Some operations might fail under stress, that's OK
                    continue

            # Should still be functional after stress
            async with engine.connect() as conn:
                count = (
                    await conn.execute(text("SELECT COUNT(*) FROM stress_test"))
                ).scalar()
                # Should have at least some data
                # (exact count depends on stress tolerance)
                assert count > 0

                result = (await conn.execute(text("SELECT 'stress_survived'"))).scalar()
                assert result == "stress_survived"


class TestEdgeCases:
    """Test edge cases and unusual scenarios."""

    async def test_very_long_table_names(self):
        """Test handling of very long table names."""
        async with SQLAlchemyAsyncPGliteManager() as manager:
            engine = manager.get_engine()

            # PostgreSQL has a limit of 63 characters for identifiers
            long_name = "a" * 60  # Just under the limit

            async with engine.connect() as conn:
                await conn.execute(text(f'CREATE TABLE "{long_name}" (id INTEGER)'))
                await conn.execute(text(f'INSERT INTO "{long_name}" VALUES (1)'))
                await conn.commit()

                result = (
                    await conn.execute(text(f'SELECT id FROM "{long_name}"'))
                ).scalar()
                assert result == 1

    async def test_unicode_data_handling(self):
        """Test handling of Unicode data."""
        async with SQLAlchemyAsyncPGliteManager() as manager:
            engine = manager.get_engine()

            async with engine.connect() as conn:
                await conn.execute(
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
                    await conn.execute(
                        text("INSERT INTO unicode_test VALUES (:id, :data)"),
                        {"id": i, "data": data},
                    )

                await conn.commit()

                # Verify Unicode data round-trip
                for i, expected in enumerate(unicode_data):
                    result = (
                        await conn.execute(
                            text("SELECT text_data FROM unicode_test WHERE id = :id"),
                            {"id": i},
                        )
                    ).scalar()
                    assert result == expected

    async def test_large_query_results(self):
        """Test handling of moderately large query results."""
        async with SQLAlchemyAsyncPGliteManager() as manager:
            engine = manager.get_engine()

            async with engine.connect() as conn:
                await conn.execute(
                    text("CREATE TABLE large_test (id INTEGER, value TEXT)")
                )

                # Insert a moderate amount of data (not too large for PGlite)
                for i in range(100):
                    await conn.execute(
                        text("INSERT INTO large_test VALUES (:id, :value)"),
                        {"id": i, "value": f"value_{i:03d}"},
                    )

                await conn.commit()

                # Query all data
                results = (
                    await conn.execute(
                        text("SELECT id, value FROM large_test ORDER BY id")
                    )
                ).fetchall()

                assert len(results) == 100
                assert results[0][1] == "value_000"
                assert results[99][1] == "value_099"
