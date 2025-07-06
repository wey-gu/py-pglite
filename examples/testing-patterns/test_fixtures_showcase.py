"""
🧪 py-pglite Testing Patterns Showcase
=====================================

Demonstrates powerful testing patterns, fixtures, and sugar for various scenarios.
This shows how py-pglite makes testing with real PostgreSQL effortless.
"""

import time

import pytest
from sqlalchemy import Boolean, Column, DateTime, Integer, String, text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session, declarative_base
from sqlalchemy.sql import func

from py_pglite.sqlalchemy import SQLAlchemyPGliteManager

Base = declarative_base()


class BlogPost(Base):
    __tablename__ = "blog_posts"

    id = Column(Integer, primary_key=True)
    title = Column(String(200), nullable=False)
    content = Column(String(2000))
    published = Column(Boolean, default=False)
    created_at = Column(DateTime, default=func.now())


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(80), unique=True, nullable=False)
    email = Column(String(120), unique=True, nullable=False)
    is_active = Column(Boolean, default=True)


# 🎯 Pattern 1: Function-scoped clean database for perfect isolation
@pytest.fixture(scope="function")
def clean_db():
    """Function-scoped clean database for perfect test isolation."""
    manager = SQLAlchemyPGliteManager()
    manager.start()
    engine = manager.get_engine()
    Base.metadata.create_all(engine)

    yield engine

    manager.stop()


# 🎯 Pattern 2: Pre-loaded test data
@pytest.fixture
def db_with_sample_data(clean_db):
    """Database pre-loaded with sample data for testing queries."""
    Session_local = Session(clean_db)

    # Create sample users
    users = [
        User(username="alice", email="alice@example.com"),
        User(username="bob", email="bob@example.com", is_active=False),
        User(username="charlie", email="charlie@example.com"),
    ]

    # Create sample blog posts
    posts = [
        BlogPost(title="First Post", content="Hello world!", published=True),
        BlogPost(title="Draft Post", content="Work in progress...", published=False),
        BlogPost(title="Published Post", content="Live content!", published=True),
    ]

    Session_local.add_all(users + posts)
    Session_local.commit()
    Session_local.close()

    return clean_db


# 🎯 Pattern 3: Transactional testing with rollback
@pytest.fixture
def transactional_session(clean_db):
    """Transactional session that automatically rolls back after test."""
    connection = clean_db.connect()
    transaction = connection.begin()

    # Create a session bound to the transaction
    session = Session(bind=connection)

    try:
        yield session
    finally:
        session.close()
        transaction.rollback()
        connection.close()


# ✅ Test 1: Basic CRUD operations
def test_basic_crud_operations(clean_db):
    """Test basic create, read, update, delete operations."""
    with Session(clean_db) as session:
        # Create
        user = User(username="testuser", email="test@example.com")
        session.add(user)
        session.commit()

        # Read
        found_user = session.query(User).filter_by(username="testuser").first()
        assert found_user is not None
        assert found_user.email == "test@example.com"  # type: ignore

        # Update
        found_user.email = "updated@example.com"  # type: ignore
        session.commit()

        # Verify update
        updated_user = session.query(User).filter_by(username="testuser").first()
        assert updated_user.email == "updated@example.com"  # type: ignore

        # Delete
        session.delete(updated_user)
        session.commit()

        # Verify deletion
        deleted_user = session.query(User).filter_by(username="testuser").first()
        assert deleted_user is None


# ✅ Test 2: Complex queries with pre-loaded data
def test_complex_queries(db_with_sample_data):
    """Test complex queries using pre-loaded sample data."""
    with Session(db_with_sample_data) as session:
        # Test filtering
        # note: using is_(True) for proper SQLAlchemy boolean comparison
        active_users = session.query(User).filter(User.is_active.is_(True)).all()
        assert len(active_users) == 2  # alice and charlie

        # Test published posts
        published_posts = (
            session.query(BlogPost).filter(BlogPost.published.is_(True)).all()
        )
        assert len(published_posts) == 2

        # Test complex join-like query
        post_count = session.query(BlogPost).count()
        assert post_count == 3


# ✅ Test 3: PostgreSQL-specific features
def test_postgresql_features(clean_db):
    """Test PostgreSQL-specific features that aren't available in SQLite."""
    with Session(clean_db) as session:
        # Create test data
        posts = [
            BlogPost(
                title=f"Post {i}",
                content=f"Content {i}",
                published=i % 2 == 0,
            )
            for i in range(10)
        ]
        session.add_all(posts)
        session.commit()

        # Test window functions
        result = session.execute(
            text("""
            SELECT
                title,
                ROW_NUMBER() OVER (ORDER BY created_at) as row_num,
                LAG(title) OVER (ORDER BY created_at) as prev_title
            FROM blog_posts
            LIMIT 3
        """)
        ).fetchall()

        assert len(result) == 3
        assert result[0][1] == 1  # First row number
        assert result[0][2] is None  # No previous title for first row

        # Test array aggregation
        array_result = session.execute(
            text("""
            SELECT array_agg(title ORDER BY id) as all_titles
            FROM blog_posts
        """)
        ).fetchone()

        assert array_result is not None
        assert array_result[0] is not None
        assert len(array_result[0]) == 10


# ✅ Test 4: Transaction isolation with rollback
def test_transaction_isolation(transactional_session):
    """Test that changes get rolled back automatically."""
    # Insert data using the transactional session
    user = User(username="tx_user", email="tx@example.com")
    transactional_session.add(user)
    transactional_session.commit()

    # Verify data exists in this transaction
    found_user = transactional_session.query(User).filter_by(username="tx_user").first()
    assert found_user is not None


def test_transaction_isolation_verification(clean_db):
    """Verify that previous test's data was rolled back."""
    # This should not see data from previous test due to rollback
    with Session(clean_db) as session:
        user_count = session.query(User).filter_by(username="tx_user").count()
        assert user_count == 0  # Data should be gone due to rollback


# ✅ Test 5: Reasonable bulk operations
def test_bulk_operations_performance(clean_db):
    """Test pattern for performance testing bulk operations (realistic size)."""
    with Session(clean_db) as session:
        # Bulk insert performance test - realistic size for PGlite
        start_time = time.time()

        users = [
            User(username=f"bulk_user_{i}", email=f"bulk_user_{i}@example.com")
            for i in range(50)  # Reduced to a very reasonable size
        ]

        session.add_all(users)
        session.commit()

        insert_time = time.time() - start_time

        # Verify all users were created
        user_count = session.query(User).count()
        assert user_count == 50

        # Performance assertion (should be fast with py-pglite)
        assert insert_time < 10.0  # Should complete reasonably fast

        print(
            f"✅ Inserted 50 users in {insert_time:.2f}s "
            f"({50 / insert_time:.0f} users/sec)"
        )


# ✅ Test 6: Error handling patterns
def test_database_constraints_and_errors(clean_db):
    """Test error handling and database constraint violations."""
    with Session(clean_db) as session:
        # Create user
        user1 = User(username="unique_user", email="unique@example.com")
        session.add(user1)
        session.commit()

        # Try to create duplicate username (should fail)
        user2 = User(username="unique_user", email="different@example.com")
        session.add(user2)

        with pytest.raises(IntegrityError):  # Should raise integrity error
            session.commit()

        # Session should still be usable after rollback
        session.rollback()

        # Verify original user still exists
        existing_user = session.query(User).filter_by(username="unique_user").first()
        assert existing_user is not None
        assert existing_user.email == "unique@example.com"  # type: ignore


# ✅ Test 7: JSON and array operations
def test_postgresql_json_and_arrays(clean_db):
    """Test PostgreSQL-specific JSON and array operations."""
    with Session(clean_db) as session:
        # Test JSON operations
        result = session.execute(
            text("""
            SELECT '{"name": "py-pglite", "version": "0.1.0"}'::json ->> 'name' as name
        """)
        ).fetchone()
        assert result is not None
        assert result[0] == "py-pglite"

        # Test array operations
        result = session.execute(
            text("""
            SELECT (ARRAY[1,2,3,4,5])[3] as third_element
        """)
        ).fetchone()
        assert result is not None
        assert result[0] == 3

        # Test array functions
        result = session.execute(
            text("""
            SELECT array_length(ARRAY['a','b','c'], 1) as length
        """)
        ).fetchone()
        assert result is not None
        assert result[0] == 3


# 🎯 Pytest markers for categorization
pytestmark = [
    pytest.mark.integration,
    pytest.mark.database,
]

if __name__ == "__main__":
    print("🧪 py-pglite Testing Patterns Showcase")
    print("Run with: pytest examples/testing-patterns/test_fixtures_showcase.py -v")
