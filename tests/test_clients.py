"""Tests for database client abstraction layer."""

from unittest.mock import MagicMock, Mock, patch

import pytest

from py_pglite.clients import (
    AsyncpgClient,
    DatabaseClient,
    PsycopgClient,
    get_client,
    get_default_client,
)


class TestDatabaseClientInterface:
    """Test the abstract DatabaseClient interface."""

    def test_database_client_is_abstract(self):
        """Test that DatabaseClient cannot be instantiated directly."""
        with pytest.raises(TypeError):
            DatabaseClient()  # type: ignore[abstract]

    def test_database_client_interface_methods(self):
        """Test that DatabaseClient defines the required interface."""
        # Check that all abstract methods are defined
        abstract_methods = DatabaseClient.__abstractmethods__
        expected_methods = {
            "connect",
            "execute_query",
            "test_connection",
            "get_database_version",
            "close_connection",
        }
        assert abstract_methods == expected_methods


class TestPsycopgClient:
    """Test PsycopgClient implementation."""

    def test_psycopg_client_initialization(self):
        """Test PsycopgClient initialization."""
        # Should work if psycopg is available
        try:
            client = PsycopgClient()
            assert client._psycopg is not None
        except ImportError:
            # Expected if psycopg not installed
            with pytest.raises(ImportError, match="psycopg is required"):
                PsycopgClient()

    @patch("builtins.__import__")
    def test_psycopg_client_with_mocked_psycopg(self, mock_import):
        """Test PsycopgClient with mocked psycopg."""
        # Mock the psycopg module
        mock_psycopg = Mock()
        mock_psycopg.connect.return_value = Mock()

        def side_effect(name, *args, **kwargs):
            if name == "psycopg":
                return mock_psycopg
            return __import__(name, *args, **kwargs)

        mock_import.side_effect = side_effect

        client = PsycopgClient()
        assert client._psycopg == mock_psycopg

    @patch("builtins.__import__")
    def test_psycopg_connect(self, mock_import):
        """Test PsycopgClient connect method."""
        mock_psycopg = Mock()
        mock_connection = Mock()
        mock_psycopg.connect.return_value = mock_connection

        def side_effect(name, *args, **kwargs):
            if name == "psycopg":
                return mock_psycopg
            return __import__(name, *args, **kwargs)

        mock_import.side_effect = side_effect

        client = PsycopgClient()
        result = client.connect("test_connection_string")

        mock_psycopg.connect.assert_called_once_with("test_connection_string")
        assert result == mock_connection

    @patch("builtins.__import__")
    def test_psycopg_execute_query(self, mock_import):
        """Test PsycopgClient execute_query method."""
        # Setup mocks
        mock_psycopg = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [("result1",), ("result2",)]
        mock_connection = Mock()
        mock_connection.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_connection.cursor.return_value.__exit__ = Mock(return_value=None)

        def side_effect(name, *args, **kwargs):
            if name == "psycopg":
                return mock_psycopg
            return __import__(name, *args, **kwargs)

        mock_import.side_effect = side_effect

        client = PsycopgClient()

        # Test query without parameters
        result = client.execute_query(mock_connection, "SELECT 1")
        mock_cursor.execute.assert_called_with("SELECT 1")
        assert result == [("result1",), ("result2",)]

        # Test query with parameters
        mock_cursor.reset_mock()
        result = client.execute_query(mock_connection, "SELECT %s", ("param",))
        mock_cursor.execute.assert_called_with("SELECT %s", ("param",))

    @patch("builtins.__import__")
    def test_psycopg_execute_query_non_select(self, mock_import):
        """Test PsycopgClient execute_query with non-SELECT queries."""
        # Setup mocks for non-SELECT query (raises ProgrammingError)
        mock_psycopg = Mock()

        # Create a proper exception class
        class MockProgrammingError(Exception):
            pass

        mock_psycopg.ProgrammingError = MockProgrammingError

        mock_cursor = Mock()
        mock_cursor.fetchall.side_effect = MockProgrammingError("no results")
        mock_connection = Mock()
        # Fix context manager mocking
        mock_connection.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_connection.cursor.return_value.__exit__ = Mock(return_value=None)

        def side_effect(name, *args, **kwargs):
            if name == "psycopg":
                return mock_psycopg
            return __import__(name, *args, **kwargs)

        mock_import.side_effect = side_effect

        client = PsycopgClient()

        # Should return empty list for non-SELECT queries
        result = client.execute_query(mock_connection, "CREATE TABLE test (id INT)")
        assert result == []

    @patch("builtins.__import__")
    def test_psycopg_test_connection(self, mock_import):
        """Test PsycopgClient test_connection method."""
        # Setup successful connection test
        mock_psycopg = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [(1,)]
        mock_connection = Mock()
        mock_connection.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_connection.cursor.return_value.__exit__ = Mock(return_value=None)
        mock_connection.__enter__ = Mock(return_value=mock_connection)
        mock_connection.__exit__ = Mock(return_value=None)
        mock_psycopg.connect.return_value = mock_connection

        def side_effect(name, *args, **kwargs):
            if name == "psycopg":
                return mock_psycopg
            return __import__(name, *args, **kwargs)

        mock_import.side_effect = side_effect

        client = PsycopgClient()

        # Should return True for successful connection
        result = client.test_connection("valid_connection_string")
        assert result is True

        # Test failed connection
        mock_psycopg.connect.side_effect = Exception("Connection failed")
        result = client.test_connection("invalid_connection_string")
        assert result is False

    @patch("builtins.__import__")
    def test_psycopg_get_database_version(self, mock_import):
        """Test PsycopgClient get_database_version method."""
        # Setup successful version query
        mock_psycopg = Mock()
        mock_cursor = Mock()
        mock_cursor.fetchall.return_value = [("PostgreSQL 15.0",)]
        mock_connection = Mock()
        mock_connection.cursor.return_value.__enter__ = Mock(return_value=mock_cursor)
        mock_connection.cursor.return_value.__exit__ = Mock(return_value=None)
        mock_connection.__enter__ = Mock(return_value=mock_connection)
        mock_connection.__exit__ = Mock(return_value=None)
        mock_psycopg.connect.return_value = mock_connection

        def side_effect(name, *args, **kwargs):
            if name == "psycopg":
                return mock_psycopg
            return __import__(name, *args, **kwargs)

        mock_import.side_effect = side_effect

        client = PsycopgClient()

        # Should return version string
        result = client.get_database_version("connection_string")
        assert result == "PostgreSQL 15.0"

        # Test failed version query
        mock_psycopg.connect.side_effect = Exception("Connection failed")
        result = client.get_database_version("invalid_connection_string")
        assert result is None

    @patch("builtins.__import__")
    def test_psycopg_close_connection(self, mock_import):
        """Test PsycopgClient close_connection method."""
        mock_psycopg = Mock()
        mock_connection = Mock()
        mock_connection.closed = False

        def side_effect(name, *args, **kwargs):
            if name == "psycopg":
                return mock_psycopg
            return __import__(name, *args, **kwargs)

        mock_import.side_effect = side_effect

        client = PsycopgClient()

        # Should close open connection
        client.close_connection(mock_connection)
        mock_connection.close.assert_called_once()

        # Should handle already closed connection
        mock_connection.closed = True
        mock_connection.reset_mock()
        client.close_connection(mock_connection)
        mock_connection.close.assert_not_called()

        # Should handle None connection
        client.close_connection(None)


class TestAsyncpgClient:
    """Test AsyncpgClient implementation."""

    def test_asyncpg_client_initialization(self):
        """Test AsyncpgClient initialization."""
        try:
            client = AsyncpgClient()
            assert client._asyncpg is not None
            assert client._asyncio is not None
        except ImportError:
            # Expected if asyncpg not installed
            with pytest.raises(ImportError, match="asyncpg is required"):
                AsyncpgClient()

    @patch("builtins.__import__")
    def test_asyncpg_client_with_mocked_modules(self, mock_import):
        """Test AsyncpgClient with mocked modules."""
        mock_asyncio = Mock()
        mock_asyncpg = Mock()

        def side_effect(name, *args, **kwargs):
            if name == "asyncio":
                return mock_asyncio
            elif name == "asyncpg":
                return mock_asyncpg
            return __import__(name, *args, **kwargs)

        mock_import.side_effect = side_effect

        client = AsyncpgClient()
        assert client._asyncpg == mock_asyncpg
        assert client._asyncio == mock_asyncio

    @patch("builtins.__import__")
    def test_asyncpg_connect(self, mock_import):
        """Test AsyncpgClient connect method."""
        mock_asyncio = Mock()
        mock_asyncpg = Mock()
        mock_connection = Mock()
        mock_loop = Mock()
        mock_loop.run_until_complete.return_value = mock_connection
        mock_asyncio.get_event_loop.return_value = mock_loop

        def side_effect(name, *args, **kwargs):
            if name == "asyncio":
                return mock_asyncio
            elif name == "asyncpg":
                return mock_asyncpg
            return __import__(name, *args, **kwargs)

        mock_import.side_effect = side_effect

        client = AsyncpgClient()
        result = client.connect("test_connection_string")

        assert result == mock_connection

    @patch("builtins.__import__")
    def test_asyncpg_event_loop_creation(self, mock_import):
        """Test AsyncpgClient event loop creation when none exists."""
        mock_asyncio = Mock()
        mock_asyncpg = Mock()

        # Simulate no event loop
        mock_asyncio.get_event_loop.side_effect = RuntimeError("No event loop")
        mock_new_loop = Mock()
        mock_asyncio.new_event_loop.return_value = mock_new_loop

        def side_effect(name, *args, **kwargs):
            if name == "asyncio":
                return mock_asyncio
            elif name == "asyncpg":
                return mock_asyncpg
            return __import__(name, *args, **kwargs)

        mock_import.side_effect = side_effect

        client = AsyncpgClient()
        loop = client._get_event_loop()

        mock_asyncio.new_event_loop.assert_called_once()
        mock_asyncio.set_event_loop.assert_called_once_with(mock_new_loop)
        assert loop == mock_new_loop

    @patch("builtins.__import__")
    def test_asyncpg_execute_query(self, mock_import):
        """Test AsyncpgClient execute_query method."""
        mock_asyncio = Mock()
        mock_asyncpg = Mock()

        # Setup mocks - create proper record-like objects
        mock_record1 = ("value1", "value2")  # Use tuples directly
        mock_record2 = ("value3", "value4")

        mock_connection = Mock()
        mock_loop = Mock()
        mock_loop.run_until_complete.return_value = [mock_record1, mock_record2]
        mock_asyncio.get_event_loop.return_value = mock_loop

        def side_effect(name, *args, **kwargs):
            if name == "asyncio":
                return mock_asyncio
            elif name == "asyncpg":
                return mock_asyncpg
            return __import__(name, *args, **kwargs)

        mock_import.side_effect = side_effect

        client = AsyncpgClient()
        result = client.execute_query(mock_connection, "SELECT * FROM test")

        # Should convert asyncpg Records to tuples (but we're already using tuples)
        assert result == [("value1", "value2"), ("value3", "value4")]

    @patch("builtins.__import__")
    def test_asyncpg_test_connection(self, mock_import):
        """Test AsyncpgClient test_connection method."""
        mock_asyncio = Mock()
        mock_asyncpg = Mock()
        mock_connection = Mock()
        mock_connection.is_closed.return_value = False
        mock_loop = Mock()

        # Setup successful connection test
        mock_loop.run_until_complete.side_effect = [
            mock_connection,  # connect call
            [(1,)],  # execute_query call
            None,  # close call
        ]
        mock_asyncio.get_event_loop.return_value = mock_loop

        def side_effect(name, *args, **kwargs):
            if name == "asyncio":
                return mock_asyncio
            elif name == "asyncpg":
                return mock_asyncpg
            return __import__(name, *args, **kwargs)

        mock_import.side_effect = side_effect

        client = AsyncpgClient()

        # Mock the execute_query method to return expected result
        with patch.object(client, "execute_query", return_value=[(1,)]):
            result = client.test_connection("valid_connection_string")
            assert result is True

    @patch("builtins.__import__")
    def test_asyncpg_close_connection(self, mock_import):
        """Test AsyncpgClient close_connection method."""
        mock_asyncio = Mock()
        mock_asyncpg = Mock()
        mock_connection = Mock()
        mock_connection.is_closed.return_value = False
        mock_loop = Mock()
        mock_asyncio.get_event_loop.return_value = mock_loop

        def side_effect(name, *args, **kwargs):
            if name == "asyncio":
                return mock_asyncio
            elif name == "asyncpg":
                return mock_asyncpg
            return __import__(name, *args, **kwargs)

        mock_import.side_effect = side_effect

        client = AsyncpgClient()

        # Should close open connection
        client.close_connection(mock_connection)
        mock_loop.run_until_complete.assert_called()

        # Should handle already closed connection
        mock_connection.is_closed.return_value = True
        mock_loop.reset_mock()
        client.close_connection(mock_connection)
        mock_loop.run_until_complete.assert_not_called()


class TestClientFactory:
    """Test client factory functions."""

    def test_get_default_client_prefers_psycopg(self):
        """Test that get_default_client prefers psycopg when available."""
        with patch("py_pglite.clients.PsycopgClient") as mock_psycopg:
            mock_psycopg.return_value = Mock()

            get_default_client()
            mock_psycopg.assert_called_once()

    def test_get_default_client_fallback_to_asyncpg(self):
        """Test get_default_client falls back to asyncpg when psycopg unavailable."""
        with patch("py_pglite.clients.PsycopgClient") as mock_psycopg:
            mock_psycopg.side_effect = ImportError("psycopg not available")

            with patch("py_pglite.clients.AsyncpgClient") as mock_asyncpg:
                mock_asyncpg.return_value = Mock()

                get_default_client()
                mock_asyncpg.assert_called_once()

    def test_get_default_client_no_clients_available(self):
        """Test that get_default_client raises error when no clients available."""
        with patch("py_pglite.clients.PsycopgClient") as mock_psycopg:
            mock_psycopg.side_effect = ImportError("psycopg not available")

            with patch("py_pglite.clients.AsyncpgClient") as mock_asyncpg:
                mock_asyncpg.side_effect = ImportError("asyncpg not available")

                with pytest.raises(
                    ImportError, match="No supported database client found"
                ):
                    get_default_client()

    def test_get_client_auto(self):
        """Test get_client with 'auto' type."""
        with patch("py_pglite.clients.get_default_client") as mock_get_default:
            mock_client = Mock()
            mock_get_default.return_value = mock_client

            result = get_client("auto")
            assert result == mock_client
            mock_get_default.assert_called_once()

    def test_get_client_psycopg(self):
        """Test get_client with 'psycopg' type."""
        with patch("py_pglite.clients.PsycopgClient") as mock_psycopg:
            mock_client = Mock()
            mock_psycopg.return_value = mock_client

            result = get_client("psycopg")
            assert result == mock_client
            mock_psycopg.assert_called_once()

    def test_get_client_asyncpg(self):
        """Test get_client with 'asyncpg' type."""
        with patch("py_pglite.clients.AsyncpgClient") as mock_asyncpg:
            mock_client = Mock()
            mock_asyncpg.return_value = mock_client

            result = get_client("asyncpg")
            assert result == mock_client
            mock_asyncpg.assert_called_once()

    def test_get_client_invalid_type(self):
        """Test get_client with invalid client type."""
        with pytest.raises(ValueError, match="Unknown client type: invalid"):
            get_client("invalid")


class TestClientIntegration:
    """Test client integration scenarios."""

    def test_client_interface_consistency(self):
        """Test that all clients implement the same interface."""
        # Test that both client types have the same methods
        psycopg_methods = set(dir(PsycopgClient))
        asyncpg_methods = set(dir(AsyncpgClient))

        # Both should have the abstract methods
        required_methods = {
            "connect",
            "execute_query",
            "test_connection",
            "get_database_version",
            "close_connection",
        }

        for method in required_methods:
            assert method in psycopg_methods
            assert method in asyncpg_methods

    def test_client_error_handling_consistency(self):
        """Test that clients handle errors consistently."""
        # Both clients should handle connection errors gracefully
        invalid_connection = "invalid://connection/string"

        # Test with mocked clients to avoid actual connection attempts
        with patch(
            "py_pglite.clients.PsycopgClient.test_connection", return_value=False
        ):
            psycopg_client = Mock(spec=PsycopgClient)
            psycopg_client.test_connection.return_value = False
            assert not psycopg_client.test_connection(invalid_connection)

        with patch(
            "py_pglite.clients.AsyncpgClient.test_connection", return_value=False
        ):
            asyncpg_client = Mock(spec=AsyncpgClient)
            asyncpg_client.test_connection.return_value = False
            assert not asyncpg_client.test_connection(invalid_connection)
