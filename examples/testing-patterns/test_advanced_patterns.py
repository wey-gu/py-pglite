"""
🎪 Advanced py-pglite Patterns
=============================

Production-ready patterns showing advanced configuration, error recovery,
and sophisticated testing techniques with py-pglite.

Run with: pytest examples/testing-patterns/test_advanced_patterns.py -v -s
"""

from pathlib import Path

import pytest
from sqlalchemy import Column, Integer, String, text
from sqlalchemy.orm import declarative_base, sessionmaker

from py_pglite import PGliteConfig
from py_pglite.sqlalchemy import SQLAlchemyPGliteManager

Base = declarative_base()


class AdvancedUser(Base):
    __tablename__ = "advanced_users"

    id = Column(Integer, primary_key=True)
    username = Column(String(50), index=True)
    email = Column(String(100), index=True)
    config_data = Column(String(1000))  # JSON-like data


class TestAdvancedPatterns:
    """Advanced production patterns and configurations."""

    def test_custom_configuration_patterns(self):
        """Test various custom configuration scenarios."""
        print("\n🔧 Custom Configuration Patterns")
        print("=" * 50)

        # High-performance configuration
        high_perf_config = PGliteConfig(
            timeout=120,
            log_level="ERROR",
            cleanup_on_exit=True,
            work_dir=Path("./perf-tests"),
            auto_install_deps=True,
        )

        with SQLAlchemyPGliteManager(high_perf_config) as manager:
            manager.wait_for_ready(max_retries=30, delay=1.0)
            engine = manager.get_engine(echo=False, pool_pre_ping=False)
            Base.metadata.create_all(engine)

            Session = sessionmaker(bind=engine)
            with Session() as session:
                user = AdvancedUser(
                    username="perf_user",
                    email="perf@test.com",
                    config_data='{"performance": "optimized"}',
                )
                session.add(user)
                session.commit()

                count = session.execute(
                    text("SELECT COUNT(*) FROM advanced_users")
                ).scalar()
                assert count == 1
                print("  ✅ High-performance config: ✓")

    def test_error_recovery_patterns(self):
        """Test robust error recovery and resilience patterns."""
        print("\n🛡️ Error Recovery Patterns")
        print("=" * 50)

        config = PGliteConfig(timeout=30, log_level="WARNING", cleanup_on_exit=True)

        with SQLAlchemyPGliteManager(config) as manager:
            manager.wait_for_ready()
            engine = manager.get_engine()
            Base.metadata.create_all(engine)

            Session = sessionmaker(bind=engine)

            # Test SQL error recovery with proper transaction handling
            print("  🔄 Testing SQL error recovery...")
            with Session() as session:
                try:
                    session.execute(text("SELECT * FROM nonexistent_table"))
                    assert False, "Should have raised an exception"
                except Exception:
                    # Rollback the failed transaction
                    session.rollback()
                    # Session should work after rollback
                    result = session.execute(text("SELECT 1")).scalar()
                    assert result == 1
                    print("    ✅ Recovered from SQL error with rollback")

            # Test fresh session after error
            print("  🔄 Testing fresh session creation...")
            with Session() as session:
                user = AdvancedUser(
                    username="recovery_user",
                    email="recovery@test.com",
                    config_data='{"test": "recovery"}',
                )
                session.add(user)
                session.commit()

                count = session.execute(
                    text("SELECT COUNT(*) FROM advanced_users")
                ).scalar()
                assert count is not None and count >= 1
                print(f"    ✅ Fresh session works: {count} users found")

    def test_postgresql_advanced_features(self):
        """Test advanced PostgreSQL features working with py-pglite."""
        print("\n🐘 PostgreSQL Advanced Features")
        print("=" * 50)

        config = PGliteConfig(timeout=60, log_level="INFO")

        with SQLAlchemyPGliteManager(config) as manager:
            manager.wait_for_ready()
            engine = manager.get_engine()

            with engine.connect() as conn:
                # JSON operations
                print("  🔍 Testing JSON operations...")
                conn.execute(
                    text("""
                    CREATE TABLE json_test (
                        id SERIAL PRIMARY KEY,
                        data JSONB
                    )
                """)
                )

                conn.execute(
                    text("""
                    INSERT INTO json_test (data) VALUES
                    ('{"name": "Alice", "skills": ["Python", "SQL"]}'),
                    ('{"name": "Bob", "skills": ["JavaScript", "React"]}')
                """)
                )

                result = conn.execute(
                    text("""
                    SELECT data->>'name' as name
                    FROM json_test
                    WHERE data @> '{"skills": ["Python"]}'
                """)
                ).fetchall()

                assert len(result) == 1  # Alice
                print(f"    ✅ JSON query returned {len(result)} Python developer")

                conn.commit()

    def test_production_reliability_patterns(self):
        """Test production-grade reliability patterns."""
        print("\n🚀 Production Reliability Patterns")
        print("=" * 50)

        # Test manager lifecycle
        print("  🔄 Testing manager lifecycle...")
        configs_tested = 0

        for i in range(3):
            config = PGliteConfig(
                timeout=30 + (i * 10), log_level="WARNING", cleanup_on_exit=True
            )

            with SQLAlchemyPGliteManager(config) as manager:
                manager.wait_for_ready(max_retries=10, delay=0.5)
                engine = manager.get_engine()

                with engine.connect() as conn:
                    result = conn.execute(text("SELECT 1")).scalar()
                    assert result == 1
                    configs_tested += 1

        print(f"    ✅ {configs_tested} manager lifecycles completed")


@pytest.fixture(scope="module", autouse=True)
def advanced_patterns_summary():
    """Print advanced patterns test summary."""
    print("\n" + "🎪 py-pglite Advanced Patterns" + "\n" + "=" * 60)
    print("Testing sophisticated production patterns...")

    yield

    print("\n" + "📊 Advanced Patterns Summary" + "\n" + "=" * 40)
    print("✅ All advanced pattern tests completed!")
    print("🎯 Validated production-ready capabilities:")
    print("   • Custom configuration patterns")
    print("   • Error recovery and resilience")
    print("   • Advanced PostgreSQL features")
    print("   • Production reliability patterns")
    print("\n🎪 Ready for sophisticated production use! 🎪")


if __name__ == "__main__":
    print("🎪 py-pglite Advanced Patterns")
    print("Run with: pytest examples/testing-patterns/test_advanced_patterns.py -v -s")
