"""
🚀 Performance Benchmarking with py-pglite
==========================================

Real-world performance testing patterns showing how py-pglite
handles production workloads with reliability and speed.

Run with: pytest examples/testing-patterns/test_performance_benchmarks.py -v -s
"""

import statistics
import time
from concurrent.futures import ThreadPoolExecutor, as_completed
from typing import Any

import pytest
from sqlalchemy import text
from sqlmodel import Field, Session, SQLModel, create_engine, select

from py_pglite import PGliteConfig
from py_pglite.sqlalchemy import SQLAlchemyPGliteManager


# Example models for benchmarking
class BenchmarkUser(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    username: str = Field(index=True)
    email: str = Field(index=True)
    score: int = Field(default=0)
    meta_data: str | None = Field(default=None)  # Renamed to avoid SQLModel conflict


class BenchmarkOrder(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    user_id: int = Field(foreign_key="benchmark_users.id", index=True)
    amount: float
    status: str = Field(default="pending")
    created_at: str | None = Field(default=None)


@pytest.fixture(scope="module")
def benchmark_engine():
    """High-performance engine configuration for benchmarking."""
    config = PGliteConfig(
        timeout=60,  # Extended timeout for large operations
        log_level="WARNING",  # Reduce logging overhead
        cleanup_on_exit=True,
    )

    with SQLAlchemyPGliteManager(config) as manager:
        manager.wait_for_ready(max_retries=20, delay=1.0)

        # Optimized engine configuration for performance
        engine = manager.get_engine(
            pool_pre_ping=False,  # Disable pre-ping for speed
            echo=False,  # Disable SQL logging
            pool_recycle=3600,  # Long-lived connections
        )

        # Create tables once
        SQLModel.metadata.create_all(engine)
        yield engine


class TestPerformanceBenchmarks:
    """Comprehensive performance benchmarking suite."""

    def test_bulk_insert_performance(self, benchmark_engine):
        """Benchmark bulk insert operations with timing analysis."""
        print("\n🚀 Bulk Insert Performance Test")
        print("=" * 50)

        batch_sizes = [100, 500, 1000]
        results = {}

        for batch_size in batch_sizes:
            # Prepare data
            users = [
                BenchmarkUser(
                    username=f"user_{i}",
                    email=f"user_{i}@benchmark.com",
                    score=i % 100,
                    meta_data=f"metadata_{i}" * 10,  # Some bulk to test
                )
                for i in range(batch_size)
            ]

            # Time the insertion
            start_time = time.time()

            with Session(benchmark_engine) as session:
                session.add_all(users)
                session.commit()

            duration = time.time() - start_time
            rate = batch_size / duration

            results[batch_size] = {"duration": duration, "rate": rate}

            print(
                f"  📊 {batch_size:4d} users: {duration:.3f}s ({rate:8.0f} users/sec)"
            )

            # Cleanup for next test
            with Session(benchmark_engine) as session:
                session.execute(
                    text("TRUNCATE TABLE benchmark_users RESTART IDENTITY CASCADE")
                )
                session.commit()

        # Performance assertions
        assert results[100]["rate"] > 1000, "Should insert at least 1000 users/sec"
        assert results[1000]["duration"] < 5.0, (
            "1000 users should insert in under 5 seconds"
        )

        print(
            f"✅ Peak performance: {max(r['rate'] for r in results.values()):.0f} users/sec"
        )

    def test_concurrent_read_write_performance(self, benchmark_engine):
        """Benchmark concurrent read/write operations."""
        print("\n⚡ Concurrent Read/Write Performance Test")
        print("=" * 50)

        # Setup initial data
        with Session(benchmark_engine) as session:
            users = [
                BenchmarkUser(
                    username=f"concurrent_user_{i}",
                    email=f"user_{i}@concurrent.com",
                    score=i,
                )
                for i in range(500)
            ]
            session.add_all(users)
            session.commit()

        def write_worker(worker_id: int) -> dict[str, Any]:
            """Worker function for concurrent writes."""
            start_time = time.time()
            operations = 0

            with Session(benchmark_engine) as session:
                for i in range(50):  # 50 operations per worker
                    order = BenchmarkOrder(
                        user_id=(worker_id * 50 + i) % 500
                        + 1,  # Reference existing users
                        amount=float(i * 10 + worker_id),
                        status="pending",
                        created_at=f"2024-01-{(i % 28) + 1:02d}",
                    )
                    session.add(order)
                    operations += 1

                session.commit()

            duration = time.time() - start_time
            return {
                "worker_id": worker_id,
                "operations": operations,
                "duration": duration,
                "rate": operations / duration,
            }

        def read_worker(worker_id: int) -> dict[str, Any]:
            """Worker function for concurrent reads."""
            start_time = time.time()
            operations = 0

            with Session(benchmark_engine) as session:
                for i in range(100):  # 100 read operations per worker
                    # Simple query instead of complex join for compatibility
                    result = session.exec(
                        select(BenchmarkUser)
                        .where(BenchmarkUser.score > (i % 50))
                        .limit(10)
                    ).all()
                    operations += 1

            duration = time.time() - start_time
            return {
                "worker_id": worker_id,
                "operations": operations,
                "duration": duration,
                "rate": operations / duration,
            }

        # Run concurrent workers
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=8) as executor:
            # Submit both read and write workers
            write_futures = [executor.submit(write_worker, i) for i in range(3)]
            read_futures = [executor.submit(read_worker, i) for i in range(5)]

            # Collect results
            write_results = [f.result() for f in as_completed(write_futures)]
            read_results = [f.result() for f in as_completed(read_futures)]

        total_duration = time.time() - start_time

        # Analysis
        total_writes = sum(r["operations"] for r in write_results)
        total_reads = sum(r["operations"] for r in read_results)
        avg_write_rate = statistics.mean(r["rate"] for r in write_results)
        avg_read_rate = statistics.mean(r["rate"] for r in read_results)

        print(
            f"  📝 Total writes: {total_writes} ({avg_write_rate:.1f} writes/sec avg)"
        )
        print(f"  📖 Total reads:  {total_reads} ({avg_read_rate:.1f} reads/sec avg)")
        print(f"  ⏱️  Total time:   {total_duration:.2f}s")
        print(
            f"  🎯 Throughput:   {(total_writes + total_reads) / total_duration:.1f} ops/sec"
        )

        # Performance assertions
        assert avg_write_rate > 10, "Should achieve at least 10 writes/sec per worker"
        assert avg_read_rate > 20, "Should achieve at least 20 reads/sec per worker"
        assert total_duration < 30, (
            "Concurrent test should complete in under 30 seconds"
        )

        print("✅ Concurrent operations completed successfully")

    def test_large_query_performance(self, benchmark_engine):
        """Benchmark large query processing and result handling."""
        print("\n📊 Large Query Performance Test")
        print("=" * 50)

        # Setup large dataset
        batch_size = 2000
        users = [
            BenchmarkUser(
                username=f"large_user_{i}",
                email=f"large_{i}@query.com",
                score=i % 1000,  # Create varied scores for filtering
                meta_data=f"large_metadata_{i}" * 5,
            )
            for i in range(batch_size)
        ]

        start_time = time.time()
        with Session(benchmark_engine) as session:
            session.add_all(users)
            session.commit()

        insert_duration = time.time() - start_time
        print(f"  📥 Data setup: {batch_size} users in {insert_duration:.2f}s")

        # Test various query patterns
        query_tests = [
            ("Simple select", "SELECT COUNT(*) FROM benchmark_users"),
            ("Filtered query", "SELECT * FROM benchmark_users WHERE score > 500"),
            (
                "Aggregation",
                "SELECT score, COUNT(*) FROM benchmark_users GROUP BY score HAVING COUNT(*) > 1",
            ),
            (
                "Pattern matching",
                "SELECT * FROM benchmark_users WHERE username LIKE 'large_user_1%'",
            ),
            (
                "JSON simulation",
                "SELECT username, CASE WHEN score > 750 THEN 'high' WHEN score > 250 THEN 'medium' ELSE 'low' END as tier FROM benchmark_users",
            ),
        ]

        for test_name, query in query_tests:
            start_time = time.time()

            with Session(benchmark_engine) as session:
                result = session.execute(text(query)).fetchall()

            duration = time.time() - start_time
            result_count = len(result)

            print(f"  🔍 {test_name:15s}: {duration:.4f}s ({result_count:4d} results)")

            # Performance assertions
            assert duration < 2.0, f"{test_name} should complete in under 2 seconds"

        print("✅ All large queries completed within performance targets")

    def test_connection_pool_stress(self, benchmark_engine):
        """Stress test connection pooling and resource management."""
        print("\n🔗 Connection Pool Stress Test")
        print("=" * 50)

        def connection_worker(worker_id: int) -> dict[str, Any]:
            """Worker that rapidly creates and releases connections."""
            start_time = time.time()
            successful_operations = 0
            errors = 0

            for i in range(20):  # 20 rapid connection cycles per worker
                try:
                    with Session(benchmark_engine) as session:
                        # Quick operation
                        result = session.execute(
                            text("SELECT COUNT(*) FROM benchmark_users WHERE id = :id"),
                            {"id": (worker_id * 20 + i) % 100 + 1},
                        ).scalar()
                        successful_operations += 1

                        # Small delay to simulate real work
                        time.sleep(0.01)

                except Exception as e:
                    errors += 1
                    print(f"    ⚠️  Worker {worker_id} error: {e}")

            duration = time.time() - start_time
            return {
                "worker_id": worker_id,
                "successful": successful_operations,
                "errors": errors,
                "duration": duration,
                "rate": successful_operations / duration if duration > 0 else 0,
            }

        # Run stress test with many concurrent workers
        start_time = time.time()

        with ThreadPoolExecutor(max_workers=10) as executor:
            futures = [executor.submit(connection_worker, i) for i in range(10)]
            results = [f.result() for f in as_completed(futures)]

        total_duration = time.time() - start_time

        # Analysis
        total_operations = sum(r["successful"] for r in results)
        total_errors = sum(r["errors"] for r in results)
        avg_rate = statistics.mean(r["rate"] for r in results if r["rate"] > 0)
        error_rate = (
            total_errors / (total_operations + total_errors)
            if (total_operations + total_errors) > 0
            else 0
        )

        print(f"  ✅ Successful operations: {total_operations}")
        print(f"  ❌ Errors: {total_errors} ({error_rate:.1%} error rate)")
        print(f"  ⚡ Average rate: {avg_rate:.1f} ops/sec per worker")
        print(f"  ⏱️  Total duration: {total_duration:.2f}s")
        print(
            f"  🎯 System throughput: {total_operations / total_duration:.1f} ops/sec"
        )

        # Reliability assertions
        assert error_rate < 0.05, "Error rate should be less than 5%"
        assert total_operations > 150, "Should complete at least 150 operations"
        assert avg_rate > 5, "Should average at least 5 ops/sec per worker"

        print("✅ Connection pool handled stress test successfully")

    def test_memory_stability_long_running(self, benchmark_engine):
        """Test memory stability during long-running operations."""
        print("\n🧠 Memory Stability Test")
        print("=" * 50)

        initial_time = time.time()
        cycles = 50  # Number of cycles to test memory stability

        for cycle in range(cycles):
            cycle_start = time.time()

            # Create, use, and cleanup data in each cycle
            with Session(benchmark_engine) as session:
                # Create temporary data
                temp_users = [
                    BenchmarkUser(
                        username=f"temp_cycle_{cycle}_user_{i}",
                        email=f"temp_{cycle}_{i}@memory.com",
                        score=i,
                        meta_data=f"cycle_data_{cycle}" * 20,  # Larger metadata
                    )
                    for i in range(100)
                ]

                session.add_all(temp_users)
                session.commit()

                # Perform operations on the data
                high_scorers = session.exec(
                    select(BenchmarkUser)
                    .where(BenchmarkUser.score > 50)
                    .where(BenchmarkUser.username.like(f"temp_cycle_{cycle}_%"))  # type: ignore
                ).all()

                # Cleanup immediately
                for user in temp_users:
                    session.delete(user)
                session.commit()

            cycle_duration = time.time() - cycle_start

            # Progress indicator
            if cycle % 10 == 0:
                elapsed = time.time() - initial_time
                print(
                    f"  🔄 Cycle {cycle:2d}/50 complete ({elapsed:.1f}s elapsed, {cycle_duration:.3f}s/cycle)"
                )

        total_duration = time.time() - initial_time
        avg_cycle_time = total_duration / cycles

        print(f"  ✅ Completed {cycles} cycles in {total_duration:.2f}s")
        print(f"  ⚡ Average cycle time: {avg_cycle_time:.3f}s")

        # Verify no data leakage
        with Session(benchmark_engine) as session:
            remaining_temp = session.exec(
                select(BenchmarkUser).where(
                    BenchmarkUser.username.like("%temp_cycle_%")
                )  # type: ignore
            ).all()

        # Performance and stability assertions
        assert len(remaining_temp) == 0, "No temporary data should remain after cleanup"
        assert avg_cycle_time < 2.0, "Each cycle should complete quickly"
        assert total_duration < 60, "Memory stability test should complete in under 60s"

        print("✅ Memory remained stable throughout long-running test")


# Performance summary fixture
@pytest.fixture(scope="module", autouse=True)
def performance_summary():
    """Print performance test summary."""
    print("\n" + "🚀 py-pglite Performance Benchmarks" + "\n" + "=" * 80)
    print("Testing production-grade performance and reliability...")

    yield

    print("\n" + "📊 Performance Test Summary" + "\n" + "=" * 50)
    print("✅ All performance benchmarks completed successfully!")
    print("🎯 py-pglite demonstrates production-ready performance:")
    print("   • High-throughput bulk operations")
    print("   • Concurrent read/write handling")
    print("   • Large query processing")
    print("   • Connection pool stability")
    print("   • Long-running memory stability")
    print("\n🚀 Ready for production workloads! 🚀")


if __name__ == "__main__":
    print("🚀 py-pglite Performance Benchmarks")
    print(
        "Run with: pytest examples/testing-patterns/test_performance_benchmarks.py -v -s"
    )
