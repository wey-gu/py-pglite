"""Advanced example showing manual PGlite management and custom configuration."""

from typing import TYPE_CHECKING

import pytest
from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlmodel import Field, Session, SQLModel, select

from py_pglite import PGliteConfig
from py_pglite.sqlalchemy import SQLAlchemyPGliteManager

if TYPE_CHECKING:
    from py_pglite.sqlalchemy import (
        SQLAlchemyPGliteManager as SQLAlchemyPGliteManagerType,
    )


# Example models
class Product(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    name: str
    price: float
    category: str


class Order(SQLModel, table=True):
    id: int | None = Field(default=None, primary_key=True)
    product_id: int = Field(foreign_key="product.id")
    quantity: int
    total: float


def test_custom_configuration():
    """Test using custom PGlite configuration."""
    # Custom config with longer timeout
    config = PGliteConfig(timeout=30, log_level="DEBUG", cleanup_on_exit=True)

    manager: SQLAlchemyPGliteManager
    with SQLAlchemyPGliteManager(config) as manager:
        engine = manager.get_engine()

        # Create tables
        SQLModel.metadata.create_all(engine)

        with Session(engine) as session:
            # Test database connectivity using connection directly
            with session.connection() as conn:
                result = conn.execute(text("SELECT version()"))
                version = result.fetchone()
                assert version is not None
                assert "PostgreSQL" in version[0]


def test_manual_lifecycle_management():
    """Test manual management of PGlite lifecycle."""
    manager: SQLAlchemyPGliteManager = SQLAlchemyPGliteManager()

    try:
        # Start manually
        manager.start()
        assert manager.is_running()

        # Get engine and use it (readiness is checked in fixture, no need to check
        # again)
        engine = manager.get_engine(echo=True)  # Enable SQL logging
        SQLModel.metadata.create_all(engine)

        with Session(engine) as session:
            # Create some test data
            products = [
                Product(name="Laptop", price=999.99, category="Electronics"),
                Product(name="Coffee", price=4.50, category="Food"),
                Product(name="Book", price=12.99, category="Education"),
            ]

            for product in products:
                session.add(product)
            session.commit()
            session.refresh(products[0])  # Refresh to get the ID

            # Query products by category
            electronics = session.exec(
                select(Product).where(Product.category == "Electronics")
            ).all()
            assert len(electronics) == 1
            assert electronics[0].name == "Laptop"

            # Test complex query with joins (after adding orders)
            laptop = electronics[0]
            assert laptop.id is not None  # Ensure ID is set
            order = Order(product_id=laptop.id, quantity=2, total=1999.98)
            session.add(order)
            session.commit()

            # Raw SQL query using connection
            with session.connection() as conn:
                result = conn.execute(
                    text("""
                        SELECT p.name, o.quantity, o.total
                        FROM product p
                        JOIN "order" o ON p.id = o.product_id
                        WHERE p.category = :category
                    """),
                    {"category": "Electronics"},
                )

                row = result.fetchone()
                assert row is not None
                assert row[0] == "Laptop"
                assert row[1] == 2
                assert row[2] == 1999.98

    finally:
        # Clean shutdown
        manager.stop()
        assert not manager.is_running()


def test_multiple_sessions():
    """Test multiple sessions with the same engine (recommended approach).

    Note: Creating multiple engines from the same PGlite manager can cause
    connection pool conflicts. The recommended approach is to use multiple
    sessions with the same engine.
    """
    manager: SQLAlchemyPGliteManager
    with SQLAlchemyPGliteManager() as manager:
        # Use a single engine with multiple sessions (recommended)
        engine = manager.get_engine(echo=False)

        # Test basic functionality
        SQLModel.metadata.create_all(engine)

        # Test first session
        session1 = Session(engine)
        try:
            product = Product(name="Widget", price=5.99, category="Tools")
            session1.add(product)
            session1.commit()
            print("Session 1 commit successful")
        finally:
            session1.close()
            print("Session 1 closed")

        # Test second session (same engine, different session)
        session2 = Session(engine)
        try:
            result = session2.exec(select(Product)).all()
            print(f"Session 2 query successful, found {len(result)} products")
            assert len(result) == 1
            assert result[0].name == "Widget"
        finally:
            session2.close()
            print("Session 2 closed")

        # Test concurrent sessions
        sessions = []
        try:
            for i in range(3):
                session = Session(engine)
                sessions.append(session)

                # Each session can read the existing data
                products = session.exec(select(Product)).all()
                expected_count = 1 + i  # 1 original + i new products
                assert len(products) == expected_count

                # Each session can add new data
                new_product = Product(
                    name=f"Product {i}", price=float(i * 10), category="Test"
                )
                session.add(new_product)
                session.commit()

        finally:
            for session in sessions:
                session.close()

        # Verify final state
        final_session = Session(engine)
        try:
            all_products = final_session.exec(select(Product)).all()
            assert len(all_products) == 4  # 1 original + 3 new
            print(
                f"All sessions completed successfully, total products: "
                f"{len(all_products)}"
            )
        finally:
            final_session.close()

        print("Multiple sessions test completed successfully")


def test_error_handling():
    """Test error handling scenarios."""
    manager = SQLAlchemyPGliteManager()

    # Should fail if not started
    with pytest.raises(RuntimeError, match="not running"):
        manager.get_engine()

    # Start and test
    manager.start()

    try:
        engine = manager.get_engine()

        # Test invalid SQL using connection
        with Session(engine) as session:
            with pytest.raises(ProgrammingError):  # Should raise SQL syntax error
                with session.connection() as conn:
                    conn.execute(text("SELECT invalid_syntax FROM nonexistent_table"))

    finally:
        manager.stop()


def test_concurrent_sessions():
    """Test multiple concurrent sessions."""
    manager: SQLAlchemyPGliteManager
    with SQLAlchemyPGliteManager() as manager:
        engine = manager.get_engine()
        SQLModel.metadata.create_all(engine)

        # Create multiple sessions
        sessions = [Session(engine) for _ in range(5)]

        try:
            # Each session creates a product
            products = []
            for i, session in enumerate(sessions):
                product = Product(
                    name=f"Product {i}", price=float(i * 10), category="Test"
                )
                session.add(product)
                session.commit()
                products.append(product)

            # Verify all products exist using a new session
            with Session(engine) as verify_session:
                all_products = verify_session.exec(select(Product)).all()
                assert len(all_products) == 5

        finally:
            for session in sessions:
                session.close()
