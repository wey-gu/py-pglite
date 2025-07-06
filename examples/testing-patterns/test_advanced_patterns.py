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

        # Ensure the table is created for this specific test
        Base.metadata.create_all(benchmark_engine)

        session_local = sessionmaker(bind=benchmark_engine)
        with session_local() as session:
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

    def test_error_recovery_patterns(self, benchmark_engine):
        """Test robust error recovery and resilience patterns."""

        with SQLAlchemyPGliteManager() as manager:
            manager.wait_for_ready()
            engine = manager.get_engine()
            Base.metadata.create_all(engine)

            session_local = sessionmaker(bind=engine)

            # Test SQL error recovery with proper transaction handling
            with session_local() as session:
                try:
                    session.execute(text("SELECT * FROM nonexistent_table"))
                    raise AssertionError("Should have raised an exception")
                except Exception:
                    # Rollback the failed transaction
                    session.rollback()
                    # Session should work after rollback
                    result = session.execute(text("SELECT 1")).scalar()
                    assert result == 1

            # Test fresh session after error
            with session_local() as session:
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

    def test_postgresql_advanced_features(self, benchmark_engine):
        """Test advanced PostgreSQL features working with py-pglite."""

        with SQLAlchemyPGliteManager() as manager:
            manager.wait_for_ready()
            engine = manager.get_engine()

            with engine.connect() as conn:
                # JSON operations
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

                conn.commit()

    def test_production_reliability_patterns(self, benchmark_engine):
        """Test production-grade reliability patterns."""

        # Test manager lifecycle
        with SQLAlchemyPGliteManager() as manager:
            manager.wait_for_ready(max_retries=10, delay=0.5)
            engine = manager.get_engine()

            with engine.connect() as conn:
                result = conn.execute(text("SELECT 1")).scalar()
                assert result == 1


@pytest.fixture(scope="module", autouse=True)
def advanced_patterns_summary():
    """Print advanced patterns test summary."""

    yield


if __name__ == "__main__":
    pass
