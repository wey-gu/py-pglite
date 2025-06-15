"""Example showing how to use py-pglite utils for advanced database operations."""

from sqlalchemy import text
from sqlmodel import Field, Session, SQLModel, select

from py_pglite.sqlalchemy import utils


# Example models for testing
class Author(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    email: str


class Book(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    title: str
    author_id: int = Field(foreign_key="author.id")
    isbn: str
    published_year: int


def test_database_cleanup_utils(pglite_engine):
    """Test using utils for database cleanup operations."""
    # Create tables manually for this test
    SQLModel.metadata.create_all(pglite_engine)

    # Clean any existing data from previous tests
    utils.clean_database_data(pglite_engine)
    utils.reset_sequences(pglite_engine)

    with Session(pglite_engine) as session:
        # Add some test data
        author = Author(name="Jane Doe", email="jane@example.com")
        session.add(author)
        session.commit()
        session.refresh(author)

        assert author.id is not None  # Ensure ID is set
        book = Book(
            title="Python Testing Guide",
            author_id=author.id,
            isbn="978-0123456789",
            published_year=2024,
        )
        session.add(book)
        session.commit()

        # Verify data exists
        authors = session.exec(select(Author)).all()
        books = session.exec(select(Book)).all()
        assert len(authors) == 1
        assert len(books) == 1

    # Check row counts using utils
    counts = utils.get_table_row_counts(pglite_engine)
    assert counts["author"] == 1
    assert counts["book"] == 1
    assert not utils.verify_database_empty(pglite_engine)

    # Clean all data
    utils.clean_database_data(pglite_engine)

    # Verify cleanup
    counts_after = utils.get_table_row_counts(pglite_engine)
    assert counts_after["author"] == 0
    assert counts_after["book"] == 0
    assert utils.verify_database_empty(pglite_engine)


def test_sequence_reset(pglite_engine):
    """Test sequence reset functionality."""
    SQLModel.metadata.create_all(pglite_engine)

    # Clean any existing data and reset sequences for clean start
    utils.clean_database_data(pglite_engine)
    utils.reset_sequences(pglite_engine)

    with Session(pglite_engine) as session:
        # Create multiple authors to increment sequence
        authors = [
            Author(name="Author 1", email="author1@example.com"),
            Author(name="Author 2", email="author2@example.com"),
            Author(name="Author 3", email="author3@example.com"),
        ]

        for author in authors:
            session.add(author)
        session.commit()

        # Get the authors to check highest ID
        all_authors = session.exec(select(Author)).all()
        max_id = max(author.id for author in all_authors if author.id is not None)
        assert max_id == 3

    # Clean data but don't reset sequences
    utils.clean_database_data(pglite_engine)

    with Session(pglite_engine) as session:
        # Add new author - ID should continue from 4
        new_author = Author(name="Author 4", email="author4@example.com")
        session.add(new_author)
        session.commit()
        session.refresh(new_author)
        assert new_author.id == 4

    # Now reset sequences
    utils.reset_sequences(pglite_engine)
    utils.clean_database_data(pglite_engine)

    with Session(pglite_engine) as session:
        # Add author after reset - ID should be 1
        reset_author = Author(name="Reset Author", email="reset@example.com")
        session.add(reset_author)
        session.commit()
        session.refresh(reset_author)
        assert reset_author.id == 1


def test_partial_cleanup(pglite_engine):
    """Test excluding tables from cleanup."""
    SQLModel.metadata.create_all(pglite_engine)

    # Clean any existing data for clean start
    utils.clean_database_data(pglite_engine)
    utils.reset_sequences(pglite_engine)

    with Session(pglite_engine) as session:
        # Add data to both tables
        author = Author(name="Persistent Author", email="persistent@example.com")
        session.add(author)
        session.commit()
        session.refresh(author)

        assert author.id is not None  # Ensure ID is set
        book = Book(
            title="Temporary Book",
            author_id=author.id,
            isbn="978-0987654321",
            published_year=2024,
        )
        session.add(book)
        session.commit()

    # Clean only book table, exclude author
    utils.clean_database_data(pglite_engine, exclude_tables=["author"])

    # Verify author remains, book is gone
    counts = utils.get_table_row_counts(pglite_engine)
    assert counts["author"] == 1
    assert counts["book"] == 0

    # Verify with exclude list in verification
    assert utils.verify_database_empty(pglite_engine, exclude_tables=["author"])
    assert not utils.verify_database_empty(
        pglite_engine
    )  # Should be False due to author


def test_schema_operations(pglite_engine):
    """Test schema creation and deletion."""
    test_schema = "test_operations"

    # Create test schema
    utils.create_test_schema(pglite_engine, test_schema)

    # Verify schema exists
    with Session(pglite_engine) as session:
        with session.connection() as conn:
            result = conn.execute(
                text(
                    "SELECT schema_name FROM information_schema.schemata "
                    "WHERE schema_name = :name"
                ),
                {"name": test_schema},
            )
            schemas = result.fetchall()
            assert len(schemas) == 1

    # Drop schema
    utils.drop_test_schema(pglite_engine, test_schema)

    # Verify schema is gone
    with Session(pglite_engine) as session:
        with session.connection() as conn:
            result = conn.execute(
                text(
                    "SELECT schema_name FROM information_schema.schemata "
                    "WHERE schema_name = :name"
                ),
                {"name": test_schema},
            )
            schemas = result.fetchall()
            assert len(schemas) == 0


def test_combined_cleanup_fixture(pglite_session: Session):
    """Test using utils with session fixture for comprehensive cleanup."""
    # The pglite_session fixture automatically handles table creation/cleanup
    # We should avoid using utility functions that create new connections
    # when we already have an active session

    # Clean any existing data for a predictable test state
    with pglite_session.connection() as conn:
        # Clean all tables manually to ensure fresh state
        conn.execute(text('DELETE FROM "book"'))
        conn.execute(text('DELETE FROM "author"'))
        conn.execute(text("ALTER SEQUENCE author_id_seq RESTART WITH 1"))
        conn.execute(text("ALTER SEQUENCE book_id_seq RESTART WITH 1"))
        pglite_session.commit()

    # Add test data directly using the existing session
    author = Author(name="Test Author", email="test@example.com")
    pglite_session.add(author)
    pglite_session.commit()
    pglite_session.refresh(author)

    assert author.id is not None  # Ensure ID is set
    book = Book(
        title="Test Book",
        author_id=author.id,
        isbn="978-0111111111",
        published_year=2024,
    )
    pglite_session.add(book)
    pglite_session.commit()

    # Verify data exists using the current session
    authors = pglite_session.exec(select(Author)).all()
    books = pglite_session.exec(select(Book)).all()
    assert len(authors) == 1
    assert len(books) == 1

    # Test cleanup using the session's connection directly (avoid utility functions)
    with pglite_session.connection() as conn:
        # Check table counts manually
        author_count = conn.execute(text('SELECT COUNT(*) FROM "author"')).scalar()
        book_count = conn.execute(text('SELECT COUNT(*) FROM "book"')).scalar()
        assert author_count == 1
        assert book_count == 1

    # Note: The pglite_session fixture will automatically clean up
    # when this test function exits, demonstrating the fixture's cleanup capability
