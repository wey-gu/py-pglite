"""Tests for pytest fixtures functionality."""

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlalchemy.ext.asyncio import AsyncSession

from py_pglite import PGliteConfig
from py_pglite.sqlalchemy import SQLAlchemyAsyncPGliteManager
from py_pglite.sqlalchemy.fixtures import pglite_async_engine
from py_pglite.sqlalchemy.fixtures import pglite_async_session
from py_pglite.sqlalchemy.fixtures import pglite_async_sqlalchemy_manager


class TestSQLAlchemyAsyncFixtures:
    """Test async sqlalchemy fixtures."""

    def test_async_sqlalchemy_manager_fixture(self, pglite_async_sqlalchemy_manager):  # noqa: F811
        """Test pglite_manager fixture provides running manager."""
        assert isinstance(pglite_async_sqlalchemy_manager, SQLAlchemyAsyncPGliteManager)
        assert pglite_async_sqlalchemy_manager.is_running()
        assert pglite_async_sqlalchemy_manager.config is not None

        # Should be able to get connection info
        conn_str = pglite_async_sqlalchemy_manager.get_connection_string()
        assert conn_str is not None
        assert "postgresql" in conn_str

    def test_async_sqlalchemy_manager_fixture_cleanup(
        self,
        pglite_async_sqlalchemy_manager,  # noqa: F811
    ):
        """Test that pglite_manager fixture handles cleanup."""
        # Manager should be running during test
        assert pglite_async_sqlalchemy_manager.is_running()

        # Store reference to check cleanup later
        process = pglite_async_sqlalchemy_manager.process
        assert process is not None

        # Fixture should handle cleanup automatically after test

    async def test_async_sqlalchemy_manager_custom_fixture_context_manager(self):
        """Test custom manager as context manager."""
        config = PGliteConfig(timeout=45)

        # Use manager as context manager
        async with SQLAlchemyAsyncPGliteManager(config) as manager:
            assert manager.is_running()
            assert manager.config.timeout == 45

        # Should be stopped after context
        assert not manager.is_running()

    async def test_multiple_async_sqlalchemy_managers_isolation(
        self,
        pglite_async_sqlalchemy_manager,  # noqa: F811
    ):
        """Test isolation between multiple manager instances."""
        # Get the fixture manager
        manager1 = pglite_async_sqlalchemy_manager

        # Create another manager manually
        manager2 = SQLAlchemyAsyncPGliteManager()
        manager2.start()

        try:
            # Should be different instances
            assert manager1 is not manager2
            assert manager1.config.socket_path != manager2.config.socket_path

            # Both should be running independently
            assert manager1.is_running()
            assert manager2.is_running()

            # Should have different processes
            assert manager1.process != manager2.process
        finally:
            await manager2.stop()

    async def test_fixture_manager_lifecycle(self, pglite_async_sqlalchemy_manager):  # noqa: F811
        """Test manager lifecycle through fixtures."""
        # Should be running
        assert pglite_async_sqlalchemy_manager.is_running()

        # Should be able to restart
        pglite_async_sqlalchemy_manager.restart()
        assert pglite_async_sqlalchemy_manager.is_running()

        # Should be able to check readiness
        ready = await pglite_async_sqlalchemy_manager.wait_for_ready(
            max_retries=5, delay=0.1
        )
        assert isinstance(ready, bool)

    def test_async_engine_fixture(
        self,
        pglite_async_engine,  # noqa: F811
        pglite_async_sqlalchemy_manager,  # noqa: F811
    ):
        assert isinstance(pglite_async_engine, AsyncEngine)
        assert pglite_async_engine is pglite_async_sqlalchemy_manager.get_engine()

    async def test_async_session_fixture(self, pglite_async_session):  # noqa: F811
        async with pglite_async_session as session:
            result = await session.execute(
                text("""
                    SELECT table_name
                    FROM information_schema.tables
                    WHERE table_schema = 'public'
                    AND table_type = 'BASE TABLE'
                """)
            )

            # All tables should be empty
            table_names = [row[0] for row in result]
            for table_name in table_names:
                count = (
                    await session.execute(text(f'SELECT COUNT(*) FROM "{table_name}"'))
                ).scalar_one()
                assert count == 0

    async def test_async_session_fixture_bind(
        self,
        pglite_async_session,  # noqa: F811
        pglite_async_engine,  # noqa: F811
    ):
        assert isinstance(pglite_async_session, AsyncSession)
        assert pglite_async_session.is_active
        assert pglite_async_session.bind is pglite_async_engine
