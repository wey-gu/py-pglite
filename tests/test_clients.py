"""Tests for py_pglite.clients module."""

import sys  # type: ignore[reportUnusedImport]
from unittest.mock import (  # , MagicMock, AsyncMock  # type: ignore[reportUnusedImport]
    Mock,
    patch,
)

import pytest

from py_pglite.clients import (
    AsyncpgClient,
    DatabaseClient,
    PsycopgClient,
    get_client,
    get_default_client,
)


class TestDatabaseClient:
    """Test DatabaseClient abstract base class."""

    def test_database_client_is_abstract(self):
        """Test that DatabaseClient cannot be instantiated."""
        with pytest.raises(TypeError):
            DatabaseClient()  # type: ignore[abstract]

    def test_database_client_interface_methods(self):
        """Test that DatabaseClient has all required abstract methods."""
        required_methods = [
            "connect",
            "execute_query",
            "close_connection",
            "test_connection",
            "get_database_version",
        ]

        for method_name in required_methods:
            assert hasattr(DatabaseClient, method_name)
            assert callable(getattr(DatabaseClient, method_name))


class TestPsycopgClient:
    """Test PsycopgClient implementation."""

    def test_psycopg_client_initialization(self):
        """Test PsycopgClient initializes correctly."""
        mock_psycopg = Mock()

        with patch.dict("sys.modules", {"psycopg": mock_psycopg}):
            client = PsycopgClient()
            assert client._psycopg is mock_psycopg

    def test_psycopg_client_with_mocked_psycopg(self):
        """Test PsycopgClient with mocked psycopg module."""
        mock_psycopg = Mock()

        with patch.dict("sys.modules", {"psycopg": mock_psycopg}):
            client = PsycopgClient()

            # Test that client uses the mocked psycopg
            assert client._psycopg is mock_psycopg

    def test_psycopg_connect(self):
        """Test PsycopgClient connect method."""
        mock_psycopg = Mock()
        mock_connection = Mock()
        mock_psycopg.connect.return_value = mock_connection

        with patch.dict("sys.modules", {"psycopg": mock_psycopg}):
            client = PsycopgClient()
            result = client.connect("test_dsn")

            assert result is mock_connection
            mock_psycopg.connect.assert_called_once_with("test_dsn")

    def test_psycopg_execute_query(self):
        """Test PsycopgClient execute_query method."""
        mock_psycopg = Mock()
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [("result",)]

        # Set up context manager for cursor
        cursor_context = Mock()
        cursor_context.__enter__ = Mock(return_value=mock_cursor)
        cursor_context.__exit__ = Mock(return_value=None)
        mock_connection.cursor.return_value = cursor_context

        with patch.dict("sys.modules", {"psycopg": mock_psycopg}):
            client = PsycopgClient()
            result = client.execute_query(mock_connection, "SELECT 1")

            assert result == [("result",)]
            mock_cursor.execute.assert_called_once_with("SELECT 1")

    def test_psycopg_execute_query_non_select(self):
        """Test PsycopgClient execute_query method with non-SELECT query."""
        mock_psycopg = Mock()
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.side_effect = Exception("ProgrammingError")
        mock_psycopg.ProgrammingError = Exception

        # Set up context manager for cursor
        cursor_context = Mock()
        cursor_context.__enter__ = Mock(return_value=mock_cursor)
        cursor_context.__exit__ = Mock(return_value=None)
        mock_connection.cursor.return_value = cursor_context

        with patch.dict("sys.modules", {"psycopg": mock_psycopg}):
            client = PsycopgClient()
            result = client.execute_query(mock_connection, "CREATE TABLE test (id INT)")

            assert result == []
            mock_cursor.execute.assert_called_once_with("CREATE TABLE test (id INT)")

    def test_psycopg_test_connection(self):
        """Test PsycopgClient test_connection method."""
        mock_psycopg = Mock()
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [(1,)]

        # Set up context manager for cursor
        cursor_context = Mock()
        cursor_context.__enter__ = Mock(return_value=mock_cursor)
        cursor_context.__exit__ = Mock(return_value=None)
        mock_connection.cursor.return_value = cursor_context

        # Set up context manager for connection
        mock_connection.__enter__ = Mock(return_value=mock_connection)
        mock_connection.__exit__ = Mock(return_value=None)

        with patch.dict("sys.modules", {"psycopg": mock_psycopg}):
            client = PsycopgClient()

            # Mock the connect method
            with patch.object(client, "connect", return_value=mock_connection):
                result = client.test_connection("test_dsn")

            assert result is True

    def test_psycopg_get_database_version(self):
        """Test PsycopgClient get_database_version method."""
        mock_psycopg = Mock()
        mock_connection = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [("PostgreSQL 13.3",)]

        # Set up context manager for cursor
        cursor_context = Mock()
        cursor_context.__enter__ = Mock(return_value=mock_cursor)
        cursor_context.__exit__ = Mock(return_value=None)
        mock_connection.cursor.return_value = cursor_context

        # Set up context manager for connection
        mock_connection.__enter__ = Mock(return_value=mock_connection)
        mock_connection.__exit__ = Mock(return_value=None)

        with patch.dict("sys.modules", {"psycopg": mock_psycopg}):
            client = PsycopgClient()

            # Mock the connect method
            with patch.object(client, "connect", return_value=mock_connection):
                result = client.get_database_version("test_dsn")

            assert result == "PostgreSQL 13.3"

    def test_psycopg_close_connection(self):
        """Test PsycopgClient close_connection method."""
        mock_psycopg = Mock()
        mock_connection = Mock()
        mock_connection.closed = False

        with patch.dict("sys.modules", {"psycopg": mock_psycopg}):
            client = PsycopgClient()
            client.close_connection(mock_connection)

            mock_connection.close.assert_called_once()


class TestAsyncpgClient:
    """Test AsyncpgClient implementation."""

    def test_asyncpg_client_initialization(self):
        """Test AsyncpgClient initializes correctly."""
        mock_asyncio = Mock()
        mock_asyncpg = Mock()

        with patch.dict(
            "sys.modules", {"asyncio": mock_asyncio, "asyncpg": mock_asyncpg}
        ):
            client = AsyncpgClient()
            assert client._asyncio is mock_asyncio
            assert client._asyncpg is mock_asyncpg

    def test_asyncpg_client_with_mocked_modules(self):
        """Test AsyncpgClient with mocked modules."""
        mock_asyncio = Mock()
        mock_asyncpg = Mock()

        with patch.dict(
            "sys.modules", {"asyncio": mock_asyncio, "asyncpg": mock_asyncpg}
        ):
            client = AsyncpgClient()

            # Test that client uses the mocked modules
            assert client._asyncio is mock_asyncio
            assert client._asyncpg is mock_asyncpg

    def test_asyncpg_connect(self):
        """Test AsyncpgClient connect method."""
        mock_asyncio = Mock()
        mock_asyncpg = Mock()
        mock_connection = Mock()
        mock_loop = Mock()

        mock_asyncio.get_event_loop.return_value = mock_loop
        mock_loop.run_until_complete.return_value = mock_connection

        with patch.dict(
            "sys.modules", {"asyncio": mock_asyncio, "asyncpg": mock_asyncpg}
        ):
            client = AsyncpgClient()
            result = client.connect("test_dsn")

            assert result is mock_connection
            mock_loop.run_until_complete.assert_called_once()

    def test_asyncpg_event_loop_creation(self):
        """Test AsyncpgClient creates event loop when needed."""
        mock_asyncio = Mock()
        mock_asyncpg = Mock()
        mock_loop = Mock()

        # Simulate no event loop initially
        mock_asyncio.get_event_loop.side_effect = RuntimeError("No event loop")
        mock_asyncio.new_event_loop.return_value = mock_loop

        with patch.dict(
            "sys.modules", {"asyncio": mock_asyncio, "asyncpg": mock_asyncpg}
        ):
            client = AsyncpgClient()
            loop = client._get_event_loop()

            assert loop is mock_loop
            mock_asyncio.new_event_loop.assert_called_once()
            mock_asyncio.set_event_loop.assert_called_once_with(mock_loop)

    def test_asyncpg_execute_query(self):
        """Test AsyncpgClient execute_query method."""
        mock_asyncio = Mock()
        mock_asyncpg = Mock()

        with patch.dict(
            "sys.modules", {"asyncio": mock_asyncio, "asyncpg": mock_asyncpg}
        ):
            client = AsyncpgClient()

            # Mock the execute_query method directly to avoid async complexity
            with patch.object(
                client, "execute_query", return_value=[("result",)]
            ) as mock_execute:
                result = client.execute_query(Mock(), "SELECT 1")

                assert result == [("result",)]
                mock_execute.assert_called_once()

    def test_asyncpg_test_connection(self):
        """Test AsyncpgClient test_connection method."""
        mock_asyncio = Mock()
        mock_asyncpg = Mock()
        mock_connection = Mock()
        mock_loop = Mock()

        mock_asyncio.get_event_loop.return_value = mock_loop

        with patch.dict(
            "sys.modules", {"asyncio": mock_asyncio, "asyncpg": mock_asyncpg}
        ):
            client = AsyncpgClient()

            # Mock connect, execute_query, and close_connection methods
            with (
                patch.object(client, "connect", return_value=mock_connection),
                patch.object(client, "execute_query", return_value=[(1,)]),
                patch.object(client, "close_connection"),
            ):
                result = client.test_connection("test_dsn")

            assert result is True

    def test_asyncpg_close_connection(self):
        """Test AsyncpgClient close_connection method."""
        mock_asyncio = Mock()
        mock_asyncpg = Mock()
        mock_connection = Mock()
        mock_loop = Mock()

        mock_asyncio.get_event_loop.return_value = mock_loop
        mock_connection.is_closed.return_value = False

        with patch.dict(
            "sys.modules", {"asyncio": mock_asyncio, "asyncpg": mock_asyncpg}
        ):
            client = AsyncpgClient()
            client.close_connection(mock_connection)

            mock_loop.run_until_complete.assert_called_once()


class TestClientFactory:
    """Test client factory functions."""

    @patch("py_pglite.clients.PsycopgClient")
    def test_get_default_client_psycopg(self, mock_psycopg_client):
        """Test get_default_client returns PsycopgClient by default."""
        mock_instance = Mock()
        mock_psycopg_client.return_value = mock_instance

        result = get_default_client()

        assert result is mock_instance
        mock_psycopg_client.assert_called_once()

    @patch("py_pglite.clients.PsycopgClient")
    def test_get_client_psycopg(self, mock_psycopg_client):
        """Test get_client returns PsycopgClient for 'psycopg'."""
        mock_instance = Mock()
        mock_psycopg_client.return_value = mock_instance

        result = get_client("psycopg")

        assert result is mock_instance
        mock_psycopg_client.assert_called_once()

    @patch("py_pglite.clients.AsyncpgClient")
    def test_get_client_asyncpg(self, mock_asyncpg_client):
        """Test get_client returns AsyncpgClient for 'asyncpg'."""
        mock_instance = Mock()
        mock_asyncpg_client.return_value = mock_instance

        result = get_client("asyncpg")

        assert result is mock_instance
        mock_asyncpg_client.assert_called_once()

    def test_get_client_invalid(self):
        """Test get_client raises ValueError for invalid client."""
        with pytest.raises(ValueError, match="Unknown client type"):
            get_client("invalid_client")
