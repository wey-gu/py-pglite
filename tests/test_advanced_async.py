"""Advanced example showing manual PGlite management and custom configuration."""

from typing import TYPE_CHECKING

import pytest

from sqlalchemy import text
from sqlalchemy.exc import ProgrammingError
from sqlalchemy.orm import registry
from sqlmodel import Field
from sqlmodel import SQLModel
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession

from py_pglite import PGliteConfig
from py_pglite.sqlalchemy import SQLAlchemyAsyncPGliteManager


if TYPE_CHECKING:
    from py_pglite.sqlalchemy import (
        SQLAlchemyAsyncPGliteManager as SQLAlchemyAsyncPGliteManagerType,
    )

# Base class with separate registry
# not to conflict with other tests
registry = registry()


class SQLModel(SQLModel, registry=registry):
    pass


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


async def test_custom_configuration():
    """Test using custom PGlite configuration."""
    # Custom config with longer timeout
    config = PGliteConfig(timeout=30, log_level="DEBUG", cleanup_on_exit=True)
    manager: SQLAlchemyAsyncPGliteManager
    with SQLAlchemyAsyncPGliteManager(config) as manager:
        engine = manager.get_engine()

        # Create tables
        # async with engine.connect() as conn:
        #     await conn.run_sync(SQLModel.metadata.create_all)

        async with AsyncSession(engine) as session:
            # Test database connectivity using connection directly
            conn = await session.connection()
            result = await conn.execute(text("SELECT version()"))
            version = result.fetchone()
            assert version is not None
            assert "PostgreSQL" in version[0]
            await conn.close()


async def test_manual_lifecycle_management():
    """Test manual management of PGlite lifecycle."""
    manager: SQLAlchemyAsyncPGliteManager = SQLAlchemyAsyncPGliteManager()

    try:
        # Start manually
        manager.start()
        assert manager.is_running()

        # Get engine and use it (readiness is checked in fixture, no need to check
        # again)
        engine = manager.get_engine(echo=True)  # Enable SQL logging
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        async with AsyncSession(engine) as session:
            # Create some test data
            products = [
                Product(name="Laptop", price=999.99, category="Electronics"),
                Product(name="Coffee", price=4.50, category="Food"),
                Product(name="Book", price=12.99, category="Education"),
            ]

            for product in products:
                session.add(product)
            await session.commit()
            await session.refresh(products[0])  # Refresh to get the ID

            # Query products by category
            electronics = (
                await session.exec(
                    select(Product).where(Product.category == "Electronics")
                )
            ).all()
            assert len(electronics) == 1
            assert electronics[0].name == "Laptop"

            # Test complex query with joins (after adding orders)
            laptop = electronics[0]
            assert laptop.id is not None  # Ensure ID is set
            order = Order(product_id=laptop.id, quantity=2, total=1999.98)
            session.add(order)
            await session.commit()

            # Raw SQL query using connection
            conn = await session.connection()
            result = await conn.execute(
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
        await manager.stop()
        assert not manager.is_running()


async def test_multiple_sessions():
    """Test multiple sessions with the same engine (recommended approach).

    Note: Creating multiple engines from the same PGlite manager can cause
    connection pool conflicts. The recommended approach is to use multiple
    sessions with the same engine.
    """
    manager: SQLAlchemyAsyncPGliteManager
    async with SQLAlchemyAsyncPGliteManager() as manager:
        # Use a single engine with multiple sessions (recommended)
        engine = manager.get_engine(echo=False)

        # Test basic functionality
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)

        # Test first session
        session1 = AsyncSession(engine)
        try:
            product = Product(name="Widget", price=5.99, category="Tools")
            session1.add(product)
            await session1.commit()
        finally:
            await session1.close()

        # Test second session (same engine, different session)
        session2 = AsyncSession(engine)
        try:
            result = (await session2.exec(select(Product))).all()
            assert len(result) == 1
            assert result[0].name == "Widget"
        finally:
            await session2.close()

        # Test concurrent sessions
        sessions = []
        try:
            for i in range(3):
                session = AsyncSession(engine)
                sessions.append(session)

                # Each session can read the existing data
                products = (await session.exec(select(Product))).all()
                expected_count = 1 + i  # 1 original + i new products
                assert len(products) == expected_count

                # Each session can add new data
                new_product = Product(
                    name=f"Product {i}", price=float(i * 10), category="Test"
                )
                session.add(new_product)
                await session.commit()

        finally:
            for session in sessions:
                await session.close()

        # Verify final state
        final_session = AsyncSession(engine)
        try:
            all_products = (await final_session.exec(select(Product))).all()
            assert len(all_products) == 4  # 1 original + 3 new
        finally:
            await final_session.close()


async def test_error_handling():
    """Test error handling scenarios."""
    manager = SQLAlchemyAsyncPGliteManager()

    # Should fail if not started
    with pytest.raises(RuntimeError, match="not running"):
        manager.get_engine()

    # Start and test
    manager.start()
    conn = None

    try:
        engine = manager.get_engine()

        # Test invalid SQL using connection
        async with AsyncSession(engine) as session:
            with pytest.raises(ProgrammingError):
                conn = await session.connection()
                await conn.execute(text("SELECT invalid_syntax FROM nonexistent_table"))

    finally:
        await manager.stop()
        if conn:
            await conn.close()


async def test_concurrent_sessions():
    """Test multiple concurrent sessions."""
    manager: SQLAlchemyAsyncPGliteManager
    async with SQLAlchemyAsyncPGliteManager() as manager:
        engine = manager.get_engine()
        async with engine.begin() as conn:
            await conn.run_sync(SQLModel.metadata.create_all)
        # Create multiple sessions
        sessions = [AsyncSession(engine) for _ in range(5)]

        try:
            # Each session creates a product
            products = []
            for i, session in enumerate(sessions):
                product = Product(
                    name=f"Product {i}", price=float(i * 10), category="Test"
                )
                session.add(product)
                await session.commit()
                products.append(product)

            # Verify all products exist using a new session
            async with AsyncSession(engine) as verify_session:
                all_products = (await verify_session.exec(select(Product))).all()
                assert len(all_products) == 5

        finally:
            for session in sessions:
                await session.close()
