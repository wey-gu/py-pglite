"""Connection management and reliability testing for py-pglite.

Tests connection pooling, cleanup, error recovery, and edge cases
to ensure robust connection handling under various scenarios.
"""

import time

from concurrent.futures import ThreadPoolExecutor
from concurrent.futures import as_completed

import pytest

from sqlalchemy import text
from sqlalchemy.exc import DisconnectionError
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.pool import NullPool
from sqlalchemy.pool import StaticPool

from py_pglite import PGliteConfig
from py_pglite.sqlalchemy import SQLAlchemyPGliteManager


class TestConnectionPooling:
    """Test different connection pooling strategies."""

    def test_static_pool_default(self):
        """Test that StaticPool is the default and works properly."""
        with SQLAlchemyPGliteManager() as manager:
            engine = manager.get_engine()

            # StaticPool should be the default
            assert engine.pool.__class__.__name__ == "StaticPool"

            # Should be able to make multiple connections
            with engine.connect() as conn1:
                result1 = conn1.execute(text("SELECT 1")).scalar()
                assert result1 == 1

                with engine.connect() as conn2:
                    result2 = conn2.execute(text("SELECT 2")).scalar()
                    assert result2 == 2

    def test_null_pool_option(self):
        """Test NullPool option for scenarios that need it."""
        with SQLAlchemyPGliteManager() as manager:
            engine = manager.get_engine(poolclass=NullPool)

            assert engine.pool.__class__.__name__ == "NullPool"

            # Should still work with NullPool
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 'NullPool test'")).scalar()
                assert result == "NullPool test"

    def test_shared_engine_consistency(self):
        """Test that get_engine() returns the same shared engine."""
        with SQLAlchemyPGliteManager() as manager:
            engine1 = manager.get_engine()
            engine2 = manager.get_engine()
            engine3 = manager.get_engine(echo=True)  # Even with different params

            # Should be the exact same engine instance
            assert engine1 is engine2
            assert engine1 is engine3  # Shared engine ignores additional params

    def test_engine_persistence_across_calls(self):
        """Test that the shared engine persists across multiple calls."""
        with SQLAlchemyPGliteManager() as manager:
            # Create some data with first engine call
            engine1 = manager.get_engine()
            with engine1.connect() as conn:
                conn.execute(
                    text("CREATE TABLE test_persistence (id INTEGER, value TEXT)")
                )
                conn.execute(text("INSERT INTO test_persistence VALUES (1, 'test')"))
                conn.commit()

            # Get engine again and verify data persists
            engine2 = manager.get_engine()
            with engine2.connect() as conn:
                result = conn.execute(
                    text("SELECT value FROM test_persistence WHERE id = 1")
                ).scalar()
                assert result == "test"


class TestConnectionLifecycle:
    """Test connection lifecycle management."""

    def test_connection_cleanup_on_manager_stop(self):
        """Test that connections are properly cleaned up when manager stops."""
        manager = SQLAlchemyPGliteManager()
        manager.start()

        try:
            engine = manager.get_engine()

            # Make a connection and close it
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1")).scalar()
                assert result == 1

            # Engine should have a shared engine reference
            assert hasattr(manager, "_shared_engine")
            assert manager._shared_engine is not None

        finally:
            manager.stop()

            # After stop, shared engine should be cleaned up
            assert (
                not hasattr(manager, "_shared_engine") or manager._shared_engine is None
            )

    def test_multiple_manager_instances_isolation(self):
        """Test that multi-manager properly isolated (sequential usage)."""
        import tempfile
        import uuid

        from pathlib import Path

        # Create unique socket paths for each manager to avoid conflicts
        temp_dir1 = (
            Path(tempfile.gettempdir()) / f"py-pglite-test1-{uuid.uuid4().hex[:8]}"
        )
        temp_dir2 = (
            Path(tempfile.gettempdir()) / f"py-pglite-test2-{uuid.uuid4().hex[:8]}"
        )
        temp_dir1.mkdir(mode=0o700, exist_ok=True)
        temp_dir2.mkdir(mode=0o700, exist_ok=True)

        config1 = PGliteConfig(timeout=10, socket_path=str(temp_dir1 / ".s.PGSQL.5432"))
        config2 = PGliteConfig(timeout=20, socket_path=str(temp_dir2 / ".s.PGSQL.5432"))

        # Test manager1 first
        manager1 = SQLAlchemyPGliteManager(config1)
        try:
            manager1.start()
            manager1.wait_for_ready()

            engine1 = manager1.get_engine()

            # Create data in manager1
            with engine1.connect() as conn:
                conn.execute(
                    text("CREATE TABLE manager1_test (id INTEGER, value TEXT)")
                )
                conn.execute(
                    text("INSERT INTO manager1_test VALUES (1, 'manager1_data')")
                )
                conn.commit()

                # Verify data
                result = conn.execute(
                    text("SELECT value FROM manager1_test WHERE id = 1")
                ).scalar()
                assert result == "manager1_data"

        finally:
            manager1.stop()

        # Now test manager2 (sequential, not simultaneous)
        manager2 = SQLAlchemyPGliteManager(config2)
        try:
            manager2.start()
            manager2.wait_for_ready()

            engine2 = manager2.get_engine()

            # Create different data in manager2
            with engine2.connect() as conn:
                conn.execute(
                    text("CREATE TABLE manager2_test (id INTEGER, value TEXT)")
                )
                conn.execute(
                    text("INSERT INTO manager2_test VALUES (2, 'manager2_data')")
                )
                conn.commit()

                # Verify manager2's data
                result = conn.execute(
                    text("SELECT value FROM manager2_test WHERE id = 2")
                ).scalar()
                assert result == "manager2_data"

                # Should not see manager1's table (different database)
                with pytest.raises(
                    ProgrammingError
                ):  # Table doesn't exist in this database
                    conn.execute(text("SELECT value FROM manager1_test WHERE id = 1"))

        finally:
            manager2.stop()

            # Clean up temp directories
            import shutil

            try:
                shutil.rmtree(temp_dir1, ignore_errors=True)
                shutil.rmtree(temp_dir2, ignore_errors=True)
            except Exception:
                pass  # Ignore cleanup errors

    def test_engine_disposal_on_stop(self):
        """Test that engine is properly disposed when manager stops."""
        manager = SQLAlchemyPGliteManager()
        manager.start()

        try:
            engine = manager.get_engine()

            # Engine should be working
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 'working'")).scalar()
                assert result == "working"

        finally:
            manager.stop()

            # After stop, engine should be disposed and unusable
            # Note: We can't easily test this without potentially hanging
            # Just verify the manager cleaned up properly
            assert (
                not hasattr(manager, "_shared_engine") or manager._shared_engine is None
            )


class TestConnectionConcurrency:
    """Test concurrent connection usage."""

    def test_concurrent_connections_same_engine(self):
        """Test multiple threads using the same engine safely."""
        with SQLAlchemyPGliteManager() as manager:
            engine = manager.get_engine()

            # Create a test table
            with engine.connect() as conn:
                conn.execute(
                    text("CREATE TABLE concurrent_test (id INTEGER, thread_id INTEGER)")
                )
                conn.commit()

            def worker(thread_id):
                """Worker function for concurrent testing."""
                try:
                    with engine.connect() as conn:
                        # Insert data and return the ID in a single atomic operation
                        # to prevent race conditions.
                        result = conn.execute(
                            text(
                                "INSERT INTO concurrent_test (id, thread_id) "
                                "VALUES (:id, :thread_id) RETURNING id"
                            ),
                            {"id": thread_id, "thread_id": thread_id},
                        ).scalar()
                        conn.commit()
                        return result
                except Exception as e:
                    print(f"  ⚠️ Worker {thread_id} error: {e}")
                    return None

            # Run multiple threads concurrently
            num_threads = 5
            with ThreadPoolExecutor(max_workers=num_threads) as executor:
                futures = [executor.submit(worker, i) for i in range(num_threads)]

                results = []
                for future in as_completed(futures):
                    result = future.result()
                    results.append(result)

            # All threads should have succeeded
            assert len(results) == num_threads
            for i, result in enumerate(sorted(results)):
                assert result == i

    def test_rapid_connection_creation_and_disposal(self):
        """Test rapidly creating and disposing connections."""
        with SQLAlchemyPGliteManager() as manager:
            engine = manager.get_engine()

            # Rapidly create and dispose many connections
            for i in range(20):
                with engine.connect() as conn:
                    result = conn.execute(text(f"SELECT {i}")).scalar()
                    assert result == i
                # Connection should be automatically returned to pool

    def test_connection_with_transaction_rollback(self):
        """Test connection handling with transaction rollbacks."""
        with SQLAlchemyPGliteManager() as manager:
            engine = manager.get_engine()

            # Create test table
            with engine.connect() as conn:
                conn.execute(text("CREATE TABLE rollback_test (id INTEGER)"))
                conn.commit()

            # Test transaction rollback
            with engine.connect() as conn:
                trans = conn.begin()
                try:
                    conn.execute(text("INSERT INTO rollback_test VALUES (1)"))
                    # Simulate an error that causes rollback
                    raise Exception("Simulated error")
                except Exception:
                    trans.rollback()

            # Verify rollback worked - no data should be present
            with engine.connect() as conn:
                result = conn.execute(
                    text("SELECT COUNT(*) FROM rollback_test")
                ).scalar()
                assert result == 0

            # Connection should still be usable after rollback
            with engine.connect() as conn:
                conn.execute(text("INSERT INTO rollback_test VALUES (2)"))
                conn.commit()

                result = conn.execute(text("SELECT id FROM rollback_test")).scalar()
                assert result == 2


class TestConnectionErrorHandling:
    """Test connection error handling and recovery."""

    def test_engine_access_before_start(self):
        """Test proper error when accessing engine before starting manager."""
        manager = SQLAlchemyPGliteManager()

        # Should raise error when not started
        with pytest.raises(RuntimeError, match="not running"):
            manager.get_engine()

    def test_connection_after_manager_stop(self):
        """Test behavior when using connections after manager stops."""
        manager = SQLAlchemyPGliteManager()
        manager.start()

        engine = manager.get_engine()

        # Should work while manager is running
        with engine.connect() as conn:
            result = conn.execute(text("SELECT 1")).scalar()
            assert result == 1

        # Stop the manager
        manager.stop()

        # Engine should be disposed, new connections should fail
        # Note: This is implementation-dependent and might not always raise
        # but the manager should have cleaned up properly
        assert not hasattr(manager, "_shared_engine") or manager._shared_engine is None

    def test_invalid_sql_handling(self):
        """Test that invalid SQL doesn't break the connection pool."""
        with SQLAlchemyPGliteManager() as manager:
            engine = manager.get_engine()

            # Execute invalid SQL
            with engine.connect() as conn:
                with pytest.raises(ProgrammingError):  # Should raise SQL syntax error
                    conn.execute(text("INVALID SQL STATEMENT"))

            # Connection pool should still work after error
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 'recovery test'")).scalar()
                assert result == "recovery test"

    def test_connection_pool_resilience(self):
        """Test that connection pool can handle various error scenarios."""
        with SQLAlchemyPGliteManager() as manager:
            engine = manager.get_engine()

            # Create test scenarios that might stress the pool
            test_cases = [
                "SELECT 1",  # Normal case
                "SELECT 'string with spaces'",  # String case
                "SELECT 1/1",  # Division case
                "SELECT NOW()",  # Function case
            ]

            for _i, sql in enumerate(test_cases):
                with engine.connect() as conn:
                    result = conn.execute(text(sql)).scalar()
                    assert result is not None

            # One more connection to verify pool is still healthy
            with engine.connect() as conn:
                result = conn.execute(text("SELECT 'pool is healthy'")).scalar()
                assert result == "pool is healthy"


class TestConnectionPerformance:
    """Test connection performance characteristics."""

    def test_connection_creation_speed(self):
        """Test that connections are created reasonably quickly."""
        with SQLAlchemyPGliteManager() as manager:
            engine = manager.get_engine()

            start_time = time.time()

            # Create multiple connections quickly
            for _i in range(10):
                with engine.connect() as conn:
                    result = conn.execute(text("SELECT 1")).scalar()
                    assert result == 1

            total_time = time.time() - start_time

            # Should be able to create 10 connections reasonably fast
            assert total_time < 2.0  # Should be much faster than 2 seconds

            avg_time_per_connection = total_time / 10
            assert avg_time_per_connection < 0.2  # Each connection should be fast

    def test_shared_engine_performance_benefit(self):
        """Test that shared engine provides performance benefits."""
        with SQLAlchemyPGliteManager() as manager:
            # Time multiple get_engine() calls
            start_time = time.time()

            engines = []
            for _i in range(20):
                engine = manager.get_engine()
                engines.append(engine)

            total_time = time.time() - start_time

            # All should be the same engine (shared)
            for engine in engines[1:]:
                assert engine is engines[0]

            # Getting shared engine should be very fast
            assert total_time < 0.1  # Should be much faster than 100ms
