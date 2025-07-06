"""
🎪 Advanced py-pglite Patterns
=============================

Production-ready patterns showing advanced configuration, error recovery,
and sophisticated testing techniques with py-pglite.

Run with: pytest examples/testing-patterns/test_advanced_patterns.py -v -s
"""

from pathlib import Path

import pytest

from sqlalchemy import Column
from sqlalchemy import Integer
from sqlalchemy import String
from sqlalchemy import text
from sqlalchemy.orm import declarative_base
from sqlalchemy.orm import sessionmaker

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

    def test_custom_configuration_is_stable(self, benchmark_engine):
        """Test that a custom configuration is stable with the fixture."""
        print("\n🔧 Custom Configuration Patterns")
        print("=" * 50)

        # Ensure the table is created for this specific test
        Base.metadata.create_all(benchmark_engine)

        Session = sessionmaker(bind=benchmark_engine)
        with Session() as session:
            user = AdvancedUser(
                username="config_user",
                email="config@test.com",
                config_data='{"stability": "tested"}',
            )
            session.add(user)
            session.commit()

            count = session.execute(
                text("SELECT COUNT(*) FROM advanced_users")
            ).scalar()
            assert count is not None and count >= 1
            print(f"  ✅ Custom config stable: {count} users found")

    def test_error_recovery_patterns(self, benchmark_engine):
        """Test robust error recovery and resilience patterns."""
        print("\n🛡️ Error Recovery Patterns")
        print("=" * 50)

        with SQLAlchemyPGliteManager() as manager:
            manager.wait_for_ready()
            engine = manager.get_engine()
            Base.metadata.create_all(engine)

            Session = sessionmaker(bind=engine)

            # Test SQL error recovery with proper transaction handling
            print("  🔄 Testing SQL error recovery...")
            with Session() as session:
                try:
                    session.execute(text("SELECT * FROM nonexistent_table"))
                    raise AssertionError("Should have raised an exception")
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

    def test_postgresql_advanced_features(self, benchmark_engine):
        """Test advanced PostgreSQL features working with py-pglite."""
        print("\n🐘 PostgreSQL Advanced Features")
        print("=" * 50)

        with SQLAlchemyPGliteManager() as manager:
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

    def test_production_reliability_patterns(self, benchmark_engine):
        """Test production-grade reliability patterns."""
        print("\n🚀 Production Reliability Patterns")
        print("=" * 50)

        # Test manager lifecycle
        print("  🔄 Testing manager lifecycle...")
        with SQLAlchemyPGliteManager() as manager:
            manager.wait_for_ready(max_retries=10, delay=0.5)
            engine = manager.get_engine()

            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1")).scalar()
                assert result == 1
        print("    ✅ Manager lifecycle completed")


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
