"""SQLAlchemy + py-pglite Real Usage Example"""

import pytest

# Mark all tests in this module as SQLAlchemy tests
pytestmark = pytest.mark.sqlalchemy
from collections.abc import Generator

from sqlalchemy import Boolean, Column, Integer, String, select
from sqlalchemy.engine import Engine
from sqlalchemy.orm import Session, declarative_base, sessionmaker
from sqlalchemy.pool import StaticPool

from py_pglite import PGliteConfig, PGliteManager

Base = declarative_base()


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    active = Column(Boolean, default=True)


# Module-specific fixtures to avoid cross-module conflicts
@pytest.fixture(scope="module")
def sqlalchemy_pglite_engine() -> Generator[Engine, None, None]:
    """Module-scoped PGlite engine to avoid conflicts with other test modules."""
    manager = PGliteManager(PGliteConfig())
    manager.start()

    try:
        engine = manager.get_engine(
            poolclass=StaticPool, pool_pre_ping=True, echo=False
        )
        yield engine
    finally:
        manager.stop()


@pytest.fixture(scope="function")
def sqlalchemy_session(
    sqlalchemy_pglite_engine: Engine,
) -> Generator[Session, None, None]:  # type: ignore
    """Function-scoped session for clean test isolation."""
    SessionLocal = sessionmaker(bind=sqlalchemy_pglite_engine)
    session = SessionLocal()
    try:
        yield session
    finally:
        session.close()


def test_user_creation_with_pglite(sqlalchemy_session: Session):
    """Test using py-pglite's session fixture - real PostgreSQL!

    Zero-config SQLAlchemy testing with ultra-fast PGlite.
    Just use the fixtures and everything works automatically! 🚀
    """
    # Create tables for this test
    Base.metadata.create_all(sqlalchemy_session.bind)

    # Create user
    user = User(username="testuser", email="test@example.com")
    sqlalchemy_session.add(user)
    sqlalchemy_session.commit()

    # Test - check the user was created properly
    assert user.id is not None
    # Use modern SQLAlchemy 2.0 style query
    found_user = sqlalchemy_session.execute(
        select(User).where(User.username == "testuser")  # type: ignore
    ).scalar_one_or_none()
    assert found_user is not None
    assert found_user.email == "test@example.com"  # type: ignore


def test_multiple_users(sqlalchemy_session: Session):
    """Test with multiple records and zero configuration required."""
    # Create tables for this test
    Base.metadata.create_all(sqlalchemy_session.bind)

    # Create users with unique usernames to avoid conflicts
    users = [
        User(username="alice_test", email="alice_test@example.com"),
        User(username="bob_test", email="bob_test@example.com"),
    ]
    sqlalchemy_session.add_all(users)
    sqlalchemy_session.commit()

    # Test - use modern SQLAlchemy 2.0 style queries
    alice = sqlalchemy_session.execute(
        select(User).where(User.username == "alice_test")  # type: ignore
    ).scalar_one_or_none()
    bob = sqlalchemy_session.execute(
        select(User).where(User.username == "bob_test")  # type: ignore
    ).scalar_one_or_none()

    assert alice is not None
    assert bob is not None
    assert alice.email == "alice_test@example.com"  # type: ignore
    assert bob.email == "bob_test@example.com"  # type: ignore


if __name__ == "__main__":
    print("SQLAlchemy + py-pglite Real Usage Example")
