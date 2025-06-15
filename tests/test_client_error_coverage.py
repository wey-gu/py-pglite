"""Comprehensive client error handling and edge case tests.

Tests all the missing error paths and edge cases in clients.py
to significantly improve coverage from 43% to 70%+.
"""

import asyncio
import logging
from unittest.mock import AsyncMock, Mock, call, patch, MagicMock

import pytest

from py_pglite.clients import (
    AsyncpgClient,
    DatabaseClient,
    PsycopgClient,
    get_client,
    get_default_client,
)

# Filter expected warnings for specific test cases
pytestmark = [
    pytest.mark.filterwarnings(
        "ignore:AsyncpgClient used in running event loop context:RuntimeWarning"
    )
]


class TestDatabaseClientAbstract:
    """Test DatabaseClient abstract class."""

    def test_abstract_client_cannot_be_instantiated(self):
        """Test that DatabaseClient cannot be instantiated."""
        with pytest.raises(TypeError):
            DatabaseClient()  # type: ignore

    def test_abstract_methods_defined(self):
        """Test that all abstract methods are defined."""
        methods = [
            "connect",
            "execute_query",
            "test_connection",
            "get_database_version",
            "close_connection",
        ]
        for method in methods:
            assert hasattr(DatabaseClient, method)


class TestPsycopgClientErrorHandling:
    """Test PsycopgClient error handling."""

    def test_psycopg_import_error(self):
        """Test PsycopgClient handles import error."""
        with patch.dict("sys.modules", {"psycopg": None}):
            with pytest.raises(ImportError, match="psycopg is required"):
                PsycopgClient()

    def test_psycopg_missing_dependency(self):
        """Test PsycopgClient handles missing dependency."""
        with patch.dict("sys.modules", {"psycopg": None}):
            with pytest.raises(ImportError, match="pip install psycopg"):
                PsycopgClient()

    def test_psycopg_execute_query_with_program_error(self):
        """Test PsycopgClient handles ProgrammingError."""
        mock_psycopg = Mock()
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.__exit__.return_value = None
        mock_cursor.fetchall.side_effect = Exception("ProgrammingError")
        mock_psycopg.ProgrammingError = Exception

        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor

        with patch.dict("sys.modules", {"psycopg": mock_psycopg}):
            client = PsycopgClient()
            result = client.execute_query(mock_conn, "CREATE TABLE test")
            assert result == []

    @patch("py_pglite.clients.logger")
    def test_psycopg_test_connection_failure(self, mock_logger):
        """Test PsycopgClient handles connection test failure."""
        mock_psycopg = Mock()
        mock_psycopg.connect.side_effect = Exception("Connection failed")

        with patch.dict("sys.modules", {"psycopg": mock_psycopg}):
            client = PsycopgClient()
            assert not client.test_connection("invalid://connection/string")

            mock_logger.warning.assert_called_once_with(
                "psycopg connection test failed: Connection failed"
            )

    @patch("py_pglite.clients.logger")
    def test_psycopg_get_database_version_failure(self, mock_logger):
        """Test PsycopgClient handles version query failure."""
        mock_psycopg = Mock()
        mock_psycopg.connect.side_effect = Exception("Connection failed")

        with patch.dict("sys.modules", {"psycopg": mock_psycopg}):
            client = PsycopgClient()
            assert client.get_database_version("invalid://connection/string") is None

            mock_logger.warning.assert_called_once_with(
                "Failed to get database version via psycopg: Connection failed"
            )

    def test_psycopg_close_connection_already_closed(self):
        """Test PsycopgClient handles already closed connection."""
        mock_conn = Mock()
        mock_conn.closed = True

        client = PsycopgClient()
        client.close_connection(mock_conn)
        mock_conn.close.assert_not_called()

    def test_psycopg_close_connection_none(self):
        """Test PsycopgClient handles None connection."""
        client = PsycopgClient()
        client.close_connection(None)  # Should not raise

    def test_psycopg_execute_query_with_params(self):
        """Test PsycopgClient execute_query with parameters."""
        mock_psycopg = Mock()
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.__exit__.return_value = None
        mock_cursor.fetchall.return_value = [("result",)]

        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor

        with patch.dict("sys.modules", {"psycopg": mock_psycopg}):
            client = PsycopgClient()
            result = client.execute_query(mock_conn, "SELECT $1", ["param"])
            assert result == [("result",)]
            mock_cursor.execute.assert_called_once_with("SELECT $1", ["param"])


class TestAsyncpgClientErrorHandling:
    """Test AsyncpgClient error handling."""

    def test_asyncpg_import_error(self):
        """Test AsyncpgClient handles import error."""
        with patch.dict("sys.modules", {"asyncpg": None}):
            with pytest.raises(ImportError, match="asyncpg is required"):
                AsyncpgClient()

    def test_asyncpg_missing_asyncio(self):
        """Test AsyncpgClient handles missing asyncio."""
        with patch.dict("sys.modules", {"asyncio": None}):
            with pytest.raises(ImportError):
                AsyncpgClient()

    @patch("py_pglite.clients.logger")
    def test_asyncpg_execute_query_exception_handling(self, mock_logger):
        """Test AsyncpgClient handles query execution errors."""
        mock_asyncio = Mock()
        mock_asyncpg = Mock()
        mock_conn = AsyncMock()
        mock_conn.fetch.side_effect = Exception("Query failed")

        async def mock_async_execute(*args, **kwargs):
            raise Exception("Query failed")

        mock_loop = Mock()
        mock_loop.is_running.return_value = False
        mock_loop.run_until_complete.side_effect = lambda x: asyncio.run(x)
        mock_asyncio.get_event_loop.return_value = mock_loop
        mock_asyncio.run.side_effect = mock_async_execute

        with patch.dict(
            "sys.modules", {"asyncio": mock_asyncio, "asyncpg": mock_asyncpg}
        ):
            client = AsyncpgClient()
            with pytest.raises(Exception, match="Query failed"):
                client.execute_query(mock_conn, "SELECT 1")

            assert mock_logger.warning.call_count == 2
            assert (
                "async query execution failed"
                in mock_logger.warning.call_args_list[0][0][0]
            )
            assert "execute_query failed" in mock_logger.warning.call_args_list[1][0][0]

    @pytest.mark.asyncio
    @patch("py_pglite.clients.logger")
    async def test_asyncpg_async_execute_query_exception(self, mock_logger):
        """Test AsyncpgClient handles async query execution errors."""
        mock_asyncio = Mock()
        mock_asyncpg = Mock()
        mock_conn = AsyncMock()
        mock_conn.fetch.side_effect = Exception("Async query failed")

        with patch.dict(
            "sys.modules", {"asyncio": mock_asyncio, "asyncpg": mock_asyncpg}
        ):
            client = AsyncpgClient()
            with pytest.raises(Exception, match="Async query failed"):
                await client._async_execute_query(mock_conn, "SELECT 1")

            mock_logger.warning.assert_called_once_with(
                "AsyncpgClient async query execution failed: Async query failed"
            )

    @patch("py_pglite.clients.logger")
    def test_asyncpg_test_connection_failure(self, mock_logger):
        """Test AsyncpgClient handles connection test failure."""
        mock_asyncio = Mock()
        mock_asyncpg = Mock()
        mock_asyncpg.connect.side_effect = Exception("Connection failed")

        mock_loop = Mock()
        mock_loop.is_running.return_value = False
        mock_asyncio.get_event_loop.return_value = mock_loop

        with patch.dict(
            "sys.modules", {"asyncio": mock_asyncio, "asyncpg": mock_asyncpg}
        ):
            client = AsyncpgClient()
            assert not client.test_connection("invalid://connection/string")

            assert mock_logger.warning.call_count == 1
            assert "connection test failed" in mock_logger.warning.call_args[0][0]

    @patch("py_pglite.clients.logger")
    def test_asyncpg_get_database_version_failure(self, mock_logger):
        """Test AsyncpgClient handles version query failure."""
        mock_asyncio = Mock()
        mock_asyncpg = Mock()
        mock_asyncpg.connect.side_effect = Exception("Connection failed")

        mock_loop = Mock()
        mock_loop.is_running.return_value = False
        mock_asyncio.get_event_loop.return_value = mock_loop

        with patch.dict(
            "sys.modules", {"asyncio": mock_asyncio, "asyncpg": mock_asyncpg}
        ):
            client = AsyncpgClient()
            assert client.get_database_version("invalid://connection/string") is None

            assert mock_logger.warning.call_count == 1
            assert "Failed to get database version" in mock_logger.warning.call_args[0][0]

    def test_asyncpg_close_connection_already_closed(self):
        """Test AsyncpgClient handles already closed connection."""
        mock_conn = AsyncMock()
        mock_conn.is_closed.return_value = True

        client = AsyncpgClient()
        client.close_connection(mock_conn)
        mock_conn.close.assert_not_awaited()

    def test_asyncpg_close_connection_none(self):
        """Test AsyncpgClient handles None connection."""
        client = AsyncpgClient()
        client.close_connection(None)  # Should not raise

    @patch("py_pglite.clients.logger")
    def test_asyncpg_event_loop_running_warning(self, mock_logger):
        """Test AsyncpgClient warns when event loop is running."""
        mock_asyncio = Mock()
        mock_loop = Mock()
        mock_loop.is_running.return_value = True
        mock_asyncio.get_event_loop.return_value = mock_loop

        with patch.dict("sys.modules", {"asyncio": mock_asyncio}):
            client = AsyncpgClient()
            loop = client._get_event_loop()
            assert loop is mock_loop

            mock_logger.warning.assert_called_once_with(
                "AsyncpgClient: Event loop is already running. "
                "Consider using psycopg client for synchronous usage."
            )

    def test_asyncpg_event_loop_runtime_error(self):
        """Test AsyncpgClient handles RuntimeError in event loop."""
        mock_asyncio = Mock()
        mock_loop = Mock()
        mock_asyncio.get_event_loop.side_effect = RuntimeError("No event loop")
        mock_asyncio.new_event_loop.return_value = mock_loop

        with patch.dict("sys.modules", {"asyncio": mock_asyncio}):
            client = AsyncpgClient()
            loop = client._get_event_loop()
            assert loop is mock_loop
            mock_asyncio.set_event_loop.assert_called_once_with(mock_loop)

    @patch("py_pglite.clients.logger")
    def test_asyncpg_execute_query_in_running_loop_warning(self, mock_logger):
        """Test AsyncpgClient warns and handles running loop."""
        mock_asyncio = Mock()
        mock_loop = Mock()
        mock_loop.is_running.return_value = True
        mock_asyncio.get_event_loop.return_value = mock_loop
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = [(1,)]

        async def mock_async_execute(*args, **kwargs):
            return [(1,)]

        mock_asyncio.run.side_effect = mock_async_execute

        # Mock ThreadPoolExecutor to handle the coroutine
        mock_executor = Mock()
        mock_executor.__enter__ = Mock(return_value=mock_executor)
        mock_executor.__exit__ = Mock(return_value=None)
        mock_executor.submit.return_value.result.return_value = [(1,)]

        with patch("concurrent.futures.ThreadPoolExecutor", return_value=mock_executor):
            with patch.dict("sys.modules", {"asyncio": mock_asyncio}):
                client = AsyncpgClient()
                with pytest.warns(RuntimeWarning, match="Consider using PsycopgClient"):
                    result = client.execute_query(mock_conn, "SELECT 1")
                    assert result == [(1,)]

                mock_logger.warning.assert_called_once_with(
                    "AsyncpgClient: Event loop is already running. "
                    "Consider using psycopg client for synchronous usage."
                )

    def test_asyncpg_execute_query_with_single_param(self):
        """Test AsyncpgClient execute_query with single parameter."""
        mock_asyncio = Mock()
        mock_asyncpg = Mock()
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = [("result",)]

        async def mock_async_execute(*args, **kwargs):
            return [("result",)]

        mock_loop = Mock()
        mock_loop.is_running.return_value = False
        mock_loop.run_until_complete.side_effect = lambda x: asyncio.run(x)
        mock_asyncio.get_event_loop.return_value = mock_loop
        mock_asyncio.run.side_effect = mock_async_execute

        with patch.dict(
            "sys.modules", {"asyncio": mock_asyncio, "asyncpg": mock_asyncpg}
        ):
            client = AsyncpgClient()
            result = client.execute_query(mock_conn, "SELECT $1", ["param"])
            assert result == [("result",)]
            mock_conn.fetch.assert_awaited_once_with("SELECT $1", "param")

    def test_asyncpg_execute_query_with_multiple_params(self):
        """Test AsyncpgClient execute_query with multiple parameters."""
        mock_asyncio = Mock()
        mock_asyncpg = Mock()
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = [("result",)]

        async def mock_async_execute(*args, **kwargs):
            return [("result",)]

        mock_loop = Mock()
        mock_loop.is_running.return_value = False
        mock_loop.run_until_complete.side_effect = lambda x: asyncio.run(x)
        mock_asyncio.get_event_loop.return_value = mock_loop
        mock_asyncio.run.side_effect = mock_async_execute

        with patch.dict(
            "sys.modules", {"asyncio": mock_asyncio, "asyncpg": mock_asyncpg}
        ):
            client = AsyncpgClient()
            result = client.execute_query(mock_conn, "SELECT $1, $2", ["param1", "param2"])
            assert result == [("result",)]
            mock_conn.fetch.assert_awaited_once_with("SELECT $1, $2", "param1", "param2")


class TestClientFactoryFunctions:
    """Test client factory functions."""

    def test_get_default_client_psycopg_preferred(self):
        """Test get_default_client prefers psycopg."""
        with patch("py_pglite.clients.PsycopgClient") as mock_psycopg:
            get_default_client()
            mock_psycopg.assert_called_once()

    def test_get_default_client_fallback_to_asyncpg(self):
        """Test get_default_client falls back to asyncpg."""
        with patch("py_pglite.clients.PsycopgClient", side_effect=ImportError), patch(
            "py_pglite.clients.AsyncpgClient"
        ) as mock_asyncpg:
            get_default_client()
            mock_asyncpg.assert_called_once()

    def test_get_default_client_no_clients_available(self):
        """Test get_default_client when no clients available."""
        with patch("py_pglite.clients.PsycopgClient", side_effect=ImportError), patch(
            "py_pglite.clients.AsyncpgClient", side_effect=ImportError
        ):
            with pytest.raises(ImportError, match="No supported database client found"):
                get_default_client()

    def test_get_client_auto_mode(self):
        """Test get_client in auto mode."""
        with patch("py_pglite.clients.get_default_client") as mock_get_default:
            get_client("auto")
            mock_get_default.assert_called_once()

    def test_get_client_psycopg_mode(self):
        """Test get_client with psycopg mode."""
        with patch("py_pglite.clients.PsycopgClient") as mock_psycopg:
            get_client("psycopg")
            mock_psycopg.assert_called_once()

    def test_get_client_asyncpg_mode(self):
        """Test get_client with asyncpg mode."""
        with patch("py_pglite.clients.AsyncpgClient") as mock_asyncpg:
            get_client("asyncpg")
            mock_asyncpg.assert_called_once()

    def test_get_client_invalid_type(self):
        """Test get_client with invalid type."""
        with pytest.raises(ValueError, match="Unknown client type"):
            get_client("invalid")


class TestClientParameterHandling:
    """Test client parameter handling."""

    def test_psycopg_execute_query_with_params(self):
        """Test PsycopgClient execute_query with parameters."""
        mock_psycopg = Mock()
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.__exit__.return_value = None
        mock_cursor.fetchall.return_value = [("result",)]

        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor

        with patch.dict("sys.modules", {"psycopg": mock_psycopg}):
            client = PsycopgClient()
            result = client.execute_query(mock_conn, "SELECT $1", ["param"])
            assert result == [("result",)]
            mock_cursor.execute.assert_called_once_with("SELECT $1", ["param"])

    def test_psycopg_execute_query_without_params(self):
        """Test PsycopgClient execute_query without parameters."""
        mock_psycopg = Mock()
        mock_cursor = MagicMock()
        mock_cursor.__enter__.return_value = mock_cursor
        mock_cursor.__exit__.return_value = None
        mock_cursor.fetchall.return_value = [("result",)]

        mock_conn = Mock()
        mock_conn.cursor.return_value = mock_cursor

        with patch.dict("sys.modules", {"psycopg": mock_psycopg}):
            client = PsycopgClient()
            result = client.execute_query(mock_conn, "SELECT 1")
            assert result == [("result",)]
            mock_cursor.execute.assert_called_once_with("SELECT 1")

    def test_asyncpg_execute_query_single_parameter(self):
        """Test AsyncpgClient execute_query with single parameter."""
        mock_asyncio = Mock()
        mock_asyncpg = Mock()
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = [("result",)]

        async def mock_async_execute(*args, **kwargs):
            return [("result",)]

        mock_loop = Mock()
        mock_loop.is_running.return_value = False
        mock_loop.run_until_complete.side_effect = lambda x: asyncio.run(x)
        mock_asyncio.get_event_loop.return_value = mock_loop
        mock_asyncio.run.side_effect = mock_async_execute

        with patch.dict(
            "sys.modules", {"asyncio": mock_asyncio, "asyncpg": mock_asyncpg}
        ):
            client = AsyncpgClient()
            result = client.execute_query(mock_conn, "SELECT $1", ["param"])
            assert result == [("result",)]
            mock_conn.fetch.assert_awaited_once_with("SELECT $1", "param")

    def test_asyncpg_execute_query_multiple_parameters(self):
        """Test AsyncpgClient execute_query with multiple parameters."""
        mock_asyncio = Mock()
        mock_asyncpg = Mock()
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = [("result",)]

        async def mock_async_execute(*args, **kwargs):
            return [("result",)]

        mock_loop = Mock()
        mock_loop.is_running.return_value = False
        mock_loop.run_until_complete.side_effect = lambda x: asyncio.run(x)
        mock_asyncio.get_event_loop.return_value = mock_loop
        mock_asyncio.run.side_effect = mock_async_execute

        with patch.dict(
            "sys.modules", {"asyncio": mock_asyncio, "asyncpg": mock_asyncpg}
        ):
            client = AsyncpgClient()
            result = client.execute_query(mock_conn, "SELECT $1, $2", ["param1", "param2"])
            assert result == [("result",)]
            mock_conn.fetch.assert_awaited_once_with("SELECT $1, $2", "param1", "param2")

    def test_asyncpg_execute_query_no_parameters(self):
        """Test AsyncpgClient execute_query without parameters."""
        mock_asyncio = Mock()
        mock_asyncpg = Mock()
        mock_conn = AsyncMock()
        mock_conn.fetch.return_value = [("result",)]

        async def mock_async_execute(*args, **kwargs):
            return [("result",)]

        mock_loop = Mock()
        mock_loop.is_running.return_value = False
        mock_loop.run_until_complete.side_effect = lambda x: asyncio.run(x)
        mock_asyncio.get_event_loop.return_value = mock_loop
        mock_asyncio.run.side_effect = mock_async_execute

        with patch.dict(
            "sys.modules", {"asyncio": mock_asyncio, "asyncpg": mock_asyncpg}
        ):
            client = AsyncpgClient()
            result = client.execute_query(mock_conn, "SELECT 1")
            assert result == [("result",)]
            mock_conn.fetch.assert_awaited_once_with("SELECT 1")


class TestClientLogging:
    """Test client logging."""

    @patch("py_pglite.clients.logger")
    def test_asyncpg_execute_query_logs_warning_on_exception(self, mock_logger):
        """Test AsyncpgClient logs warning on query execution failure."""
        mock_asyncio = Mock()
        mock_asyncpg = Mock()
        mock_conn = AsyncMock()
        mock_conn.fetch.side_effect = Exception("Query failed")

        async def mock_async_execute(*args, **kwargs):
            raise Exception("Query failed")

        mock_loop = Mock()
        mock_loop.is_running.return_value = False
        mock_loop.run_until_complete.side_effect = lambda x: asyncio.run(x)
        mock_asyncio.get_event_loop.return_value = mock_loop
        mock_asyncio.run.side_effect = mock_async_execute

        with patch.dict(
            "sys.modules", {"asyncio": mock_asyncio, "asyncpg": mock_asyncpg}
        ):
            client = AsyncpgClient()
            with pytest.raises(Exception):
                client.execute_query(mock_conn, "SELECT 1")

            # Should log warnings for both async and sync failures
            assert mock_logger.warning.call_count == 2
            assert (
                "async query execution failed"
                in mock_logger.warning.call_args_list[0][0][0]
            )
            assert "execute_query failed" in mock_logger.warning.call_args_list[1][0][0]

    @patch("py_pglite.clients.logger")
    def test_psycopg_test_connection_logs_warning_on_failure(self, mock_logger):
        """Test PsycopgClient logs warning on connection test failure."""
        mock_psycopg = Mock()
        mock_psycopg.connect.side_effect = Exception("Connection failed")

        with patch.dict("sys.modules", {"psycopg": mock_psycopg}):
            client = PsycopgClient()
            assert not client.test_connection("invalid://connection/string")

            mock_logger.warning.assert_called_once_with(
                "psycopg connection test failed: Connection failed"
            )

    @patch("py_pglite.clients.logger")
    def test_asyncpg_get_database_version_logs_warning_on_failure(self, mock_logger):
        """Test AsyncpgClient logs warning on version query failure."""
        mock_asyncio = Mock()
        mock_asyncpg = Mock()
        mock_asyncpg.connect.side_effect = Exception("Connection failed")

        mock_loop = Mock()
        mock_loop.is_running.return_value = False
        mock_asyncio.get_event_loop.return_value = mock_loop

        with patch.dict(
            "sys.modules", {"asyncio": mock_asyncio, "asyncpg": mock_asyncpg}
        ):
            client = AsyncpgClient()
            assert client.get_database_version("invalid://connection/string") is None

            mock_logger.warning.assert_called_once_with(
                "Failed to get database version via asyncpg: Connection failed"
            )
