"""Comprehensive client error handling and edge case tests.

Tests all the missing error paths and edge cases in clients.py
to significantly improve coverage from 43% to 70%+.
"""

import logging
from unittest.mock import AsyncMock, Mock, call, patch

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
    """Test abstract DatabaseClient interface (lines 7-48 missing)."""

    def test_abstract_client_cannot_be_instantiated(self):
        """Test that abstract DatabaseClient cannot be instantiated."""
        with pytest.raises(TypeError):
            DatabaseClient()  # type: ignore

    def test_abstract_methods_defined(self):
        """Test that all abstract methods are defined."""
        abstract_methods = {
            "connect",
            "execute_query",
            "test_connection",
            "get_database_version",
            "close_connection",
        }

        # Check that DatabaseClient has these as abstract methods
        assert hasattr(DatabaseClient, "__abstractmethods__")
        assert abstract_methods.issubset(DatabaseClient.__abstractmethods__)


class TestPsycopgClientErrorHandling:
    """Test PsycopgClient error handling (lines 53-59, 63, 69 missing)."""

    def test_psycopg_import_error(self):
        """Test PsycopgClient import error handling."""
        with patch.dict("sys.modules", {"psycopg": None}):
            with pytest.raises(ImportError, match="psycopg is required"):
                PsycopgClient()

    def test_psycopg_missing_dependency(self):
        """Test PsycopgClient with missing psycopg dependency."""
        # Mock the import at module level
        with patch(
            "builtins.__import__", side_effect=ImportError("No module named 'psycopg'")
        ):
            with pytest.raises(ImportError, match="psycopg is required"):
                PsycopgClient()

    def test_psycopg_execute_query_with_program_error(self):
        """Test PsycopgClient execute_query with ProgrammingError."""
        # Create a real client first to get the psycopg module
        try:
            client = PsycopgClient()
        except ImportError:
            pytest.skip("psycopg not available")

        # Mock connection and cursor with proper context manager
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=None)

        # Simulate ProgrammingError (not a SELECT query)
        mock_cursor.fetchall.side_effect = client._psycopg.ProgrammingError(
            "Not a SELECT"
        )

        # Should return empty list for non-SELECT queries
        result = client.execute_query(mock_conn, "INSERT INTO test VALUES (1)")
        assert result == []

        # Verify cursor was used properly
        mock_conn.cursor.assert_called_once()
        mock_cursor.__enter__.assert_called_once()
        mock_cursor.__exit__.assert_called_once()

    def test_psycopg_test_connection_failure(self):
        """Test PsycopgClient test_connection failure handling."""
        try:
            client = PsycopgClient()
        except ImportError:
            pytest.skip("psycopg not available")

        # Test with invalid connection string
        result = client.test_connection("invalid://connection/string")
        assert result is False

    def test_psycopg_get_database_version_failure(self):
        """Test PsycopgClient get_database_version failure handling."""
        try:
            client = PsycopgClient()
        except ImportError:
            pytest.skip("psycopg not available")

        # Test with invalid connection string
        result = client.get_database_version("invalid://connection/string")
        assert result is None

    def test_psycopg_close_connection_already_closed(self):
        """Test PsycopgClient close_connection with already closed connection."""
        try:
            client = PsycopgClient()
        except ImportError:
            pytest.skip("psycopg not available")

        # Mock closed connection
        mock_conn = Mock()
        mock_conn.closed = True

        # Should not raise error
        client.close_connection(mock_conn)

    def test_psycopg_close_connection_none(self):
        """Test PsycopgClient close_connection with None connection."""
        try:
            client = PsycopgClient()
        except ImportError:
            pytest.skip("psycopg not available")

        # Should not raise error
        client.close_connection(None)


class TestAsyncpgClientErrorHandling:
    """Test AsyncpgClient error handling (lines 105-108, 116-122 missing)."""

    def test_asyncpg_import_error(self):
        """Test AsyncpgClient import error handling."""
        with patch.dict("sys.modules", {"asyncpg": None}):
            with pytest.raises(ImportError, match="asyncpg is required"):
                AsyncpgClient()

    def test_asyncpg_missing_asyncio(self):
        """Test AsyncpgClient with missing asyncio."""
        with patch.dict("sys.modules", {"asyncio": None}):
            with pytest.raises(ImportError, match="asyncpg is required"):
                AsyncpgClient()

    def test_asyncpg_execute_query_exception_handling(self):
        """Test AsyncpgClient execute_query exception handling."""
        try:
            client = AsyncpgClient()
        except ImportError:
            pytest.skip("asyncpg not available")

        # Mock connection that raises exception
        mock_conn = Mock()

        # Mock the async execution to raise an exception
        with patch.object(
            client, "_async_execute_query", side_effect=Exception("Test error")
        ):
            with patch.object(client, "_get_event_loop") as mock_loop:
                mock_loop.return_value.run_until_complete.side_effect = Exception(
                    "Test error"
                )

                with pytest.raises(Exception, match="Test error"):
                    client.execute_query(mock_conn, "SELECT 1")

    def test_asyncpg_async_execute_query_exception(self):
        """Test AsyncpgClient _async_execute_query exception handling."""
        try:
            client = AsyncpgClient()
        except ImportError:
            pytest.skip("asyncpg not available")

        # Test the async method directly
        import asyncio
        from unittest.mock import AsyncMock

        async def test_async():
            mock_conn = AsyncMock()
            mock_conn.fetch.side_effect = Exception("Async test error")

            with pytest.raises(Exception, match="Async test error"):
                await client._async_execute_query(mock_conn, "SELECT 1")

        # Run the async test
        asyncio.run(test_async())

    def test_asyncpg_test_connection_failure(self):
        """Test AsyncpgClient test_connection failure handling."""
        try:
            client = AsyncpgClient()
        except ImportError:
            pytest.skip("asyncpg not available")

        # Test with invalid connection string
        result = client.test_connection("invalid://connection/string")
        assert result is False

    def test_asyncpg_get_database_version_failure(self):
        """Test AsyncpgClient get_database_version failure handling."""
        try:
            client = AsyncpgClient()
        except ImportError:
            pytest.skip("asyncpg not available")

        # Test with invalid connection string
        import asyncio

        async def test_async():
            result = await client._async_execute_query(None, "SELECT version()")
            return result

        # Mock _async_execute_query to raise exception
        with patch.object(
            client, "_async_execute_query", side_effect=Exception("Test error")
        ):
            result = client.get_database_version("invalid://connection/string")
            assert result is None

    def test_asyncpg_close_connection_already_closed(self):
        """Test AsyncpgClient close_connection with already closed connection."""
        try:
            client = AsyncpgClient()
        except ImportError:
            pytest.skip("asyncpg not available")

        # Mock closed connection
        mock_conn = Mock()
        mock_conn.is_closed.return_value = True

        # Should not raise error
        client.close_connection(mock_conn)

    def test_asyncpg_close_connection_none(self):
        """Test AsyncpgClient close_connection with None connection."""
        try:
            client = AsyncpgClient()
        except ImportError:
            pytest.skip("asyncpg not available")

        # Should not raise error
        client.close_connection(None)

    def test_asyncpg_event_loop_running_warning(self):
        """Test AsyncpgClient event loop running warning."""
        try:
            client = AsyncpgClient()
        except ImportError:
            pytest.skip("asyncpg not available")

        # Mock a running event loop
        mock_loop = Mock()
        mock_loop.is_running.return_value = True

        with patch.object(client._asyncio, "get_event_loop", return_value=mock_loop):
            with patch("py_pglite.clients.logger") as mock_logger:
                result_loop = client._get_event_loop()

                # Should log warning about running loop
                mock_logger.warning.assert_called_once()
                warning_msg = mock_logger.warning.call_args[0][0]
                assert "Event loop is already running" in warning_msg
                assert result_loop == mock_loop

    def test_asyncpg_event_loop_runtime_error(self):
        """Test AsyncpgClient event loop RuntimeError handling."""
        try:
            client = AsyncpgClient()
        except ImportError:
            pytest.skip("asyncpg not available")

        # Mock RuntimeError when getting event loop
        with patch.object(
            client._asyncio, "get_event_loop", side_effect=RuntimeError("No event loop")
        ):
            with patch.object(client._asyncio, "new_event_loop") as mock_new_loop:
                with patch.object(client._asyncio, "set_event_loop") as mock_set_loop:
                    mock_loop = Mock()
                    mock_new_loop.return_value = mock_loop

                    result_loop = client._get_event_loop()

                    # Should create and set new event loop
                    mock_new_loop.assert_called_once()
                    mock_set_loop.assert_called_once_with(mock_loop)
                    assert result_loop == mock_loop

    def test_asyncpg_execute_query_in_running_loop_warning(self):
        """Test AsyncpgClient warns when used in running event loop."""
        try:
            client = AsyncpgClient()
        except ImportError:
            pytest.skip("asyncpg not available")

        mock_conn = Mock()
        mock_conn.fetch = AsyncMock(return_value=[])

        # Mock a running event loop
        mock_loop = Mock()
        mock_loop.is_running.return_value = True
        mock_loop.run_until_complete.side_effect = lambda coro: []

        with patch.object(client, "_get_event_loop", return_value=mock_loop):
            with pytest.warns(
                RuntimeWarning,
                match="Consider using PsycopgClient for synchronous operations",
            ):
                client.execute_query(mock_conn, "SELECT 1")


class TestClientFactoryFunctions:
    """Test client factory functions (lines 127-162, 171-188 missing)."""

    def test_get_default_client_psycopg_preferred(self):
        """Test get_default_client prefers psycopg when available."""
        # Mock psycopg as available
        with patch("py_pglite.clients.PsycopgClient") as mock_psycopg:
            mock_client = Mock()
            mock_psycopg.return_value = mock_client

            result = get_default_client()

            mock_psycopg.assert_called_once()
            assert result == mock_client

    def test_get_default_client_fallback_to_asyncpg(self):
        """Test get_default_client falls back to asyncpg when psycopg unavailable."""
        # Mock psycopg as unavailable, asyncpg as available
        with patch(
            "py_pglite.clients.PsycopgClient", side_effect=ImportError("No psycopg")
        ):
            with patch("py_pglite.clients.AsyncpgClient") as mock_asyncpg:
                mock_client = Mock()
                mock_asyncpg.return_value = mock_client

                result = get_default_client()

                mock_asyncpg.assert_called_once()
                assert result == mock_client

    def test_get_default_client_no_clients_available(self):
        """Test get_default_client when no clients are available."""
        # Mock both clients as unavailable
        with patch(
            "py_pglite.clients.PsycopgClient", side_effect=ImportError("No psycopg")
        ):
            with patch(
                "py_pglite.clients.AsyncpgClient", side_effect=ImportError("No asyncpg")
            ):
                with pytest.raises(
                    ImportError, match="No supported database client found"
                ):
                    get_default_client()

    def test_get_client_auto_mode(self):
        """Test get_client with 'auto' mode."""
        with patch("py_pglite.clients.get_default_client") as mock_default:
            mock_client = Mock()
            mock_default.return_value = mock_client

            result = get_client("auto")

            mock_default.assert_called_once()
            assert result == mock_client

    def test_get_client_psycopg_mode(self):
        """Test get_client with 'psycopg' mode."""
        with patch("py_pglite.clients.PsycopgClient") as mock_psycopg:
            mock_client = Mock()
            mock_psycopg.return_value = mock_client

            result = get_client("psycopg")

            mock_psycopg.assert_called_once()
            assert result == mock_client

    def test_get_client_asyncpg_mode(self):
        """Test get_client with 'asyncpg' mode."""
        with patch("py_pglite.clients.AsyncpgClient") as mock_asyncpg:
            mock_client = Mock()
            mock_asyncpg.return_value = mock_client

            result = get_client("asyncpg")

            mock_asyncpg.assert_called_once()
            assert result == mock_client

    def test_get_client_invalid_type(self):
        """Test get_client with invalid client type."""
        with pytest.raises(ValueError, match="Unknown client type: invalid"):
            get_client("invalid")


class TestClientParameterHandling:
    """Test client parameter handling edge cases."""

    def test_psycopg_execute_query_with_params(self):
        """Test PsycopgClient execute_query with parameters."""
        try:
            client = PsycopgClient()
        except ImportError:
            pytest.skip("psycopg not available")

        # Mock connection and cursor with proper context manager
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=None)
        mock_cursor.fetchall.return_value = [(1,)]

        # Test with parameters
        result = client.execute_query(
            mock_conn, "SELECT * FROM test WHERE id = %s", (1,)
        )

        # Verify cursor.execute was called with parameters
        mock_cursor.execute.assert_called_once_with(
            "SELECT * FROM test WHERE id = %s", (1,)
        )
        assert result == [(1,)]

    def test_psycopg_execute_query_without_params(self):
        """Test PsycopgClient execute_query without parameters."""
        try:
            client = PsycopgClient()
        except ImportError:
            pytest.skip("psycopg not available")

        # Mock connection and cursor with proper context manager
        mock_conn = Mock()
        mock_cursor = Mock()
        mock_conn.cursor.return_value = mock_cursor
        mock_cursor.__enter__ = Mock(return_value=mock_cursor)
        mock_cursor.__exit__ = Mock(return_value=None)
        mock_cursor.fetchall.return_value = [(1,)]

        # Test without parameters
        result = client.execute_query(mock_conn, "SELECT 1")

        # Verify cursor.execute was called without parameters
        mock_cursor.execute.assert_called_once_with("SELECT 1")
        assert result == [(1,)]

    def test_asyncpg_execute_query_single_parameter(self):
        """Test AsyncpgClient parameter handling for single parameter."""
        try:
            client = AsyncpgClient()
        except ImportError:
            pytest.skip("asyncpg not available")

        # Mock connection with proper async response
        mock_conn = Mock()
        mock_record = Mock()
        mock_record.__iter__ = lambda self: iter([1])

        # Create a proper coroutine mock
        async def mock_fetch(query, *args):
            return [mock_record]

        mock_conn.fetch = mock_fetch

        # Test single parameter in list
        import asyncio

        async def test_async():
            result = await client._async_execute_query(
                mock_conn, "SELECT * FROM test WHERE id = $1", [42]
            )
            assert result == [(1,)]

        # Run the async test
        try:
            loop = asyncio.new_event_loop()
            if loop.is_running():
                pytest.skip("Cannot run async test in running loop")
            loop.run_until_complete(test_async())
        except RuntimeError:
            # No event loop, create one
            asyncio.run(test_async())

    def test_asyncpg_execute_query_multiple_parameters(self):
        """Test AsyncpgClient parameter handling for multiple parameters."""
        try:
            client = AsyncpgClient()
        except ImportError:
            pytest.skip("asyncpg not available")

        # Mock connection with proper async response
        mock_conn = Mock()
        mock_record = Mock()
        mock_record.__iter__ = lambda self: iter([1, 2])

        # Create a proper coroutine mock
        async def mock_fetch(query, *args):
            return [mock_record]

        mock_conn.fetch = mock_fetch

        # Test multiple parameters
        import asyncio

        async def test_async():
            result = await client._async_execute_query(
                mock_conn,
                "SELECT * FROM test WHERE id = $1 AND name = $2",
                [42, "test"],
            )
            assert result == [(1, 2)]

        # Run the async test
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                pytest.skip("Cannot run async test in running loop")
            loop.run_until_complete(test_async())
        except RuntimeError:
            # No event loop, create one
            asyncio.run(test_async())

    def test_asyncpg_execute_query_no_parameters(self):
        """Test AsyncpgClient parameter handling without parameters."""
        try:
            client = AsyncpgClient()
        except ImportError:
            pytest.skip("asyncpg not available")

        # Mock connection with proper async response
        mock_conn = Mock()
        mock_record = Mock()
        mock_record.__iter__ = lambda self: iter([1])

        # Create a proper coroutine mock
        async def mock_fetch(query):
            return [mock_record]

        mock_conn.fetch = mock_fetch

        # Test no parameters
        import asyncio

        async def test_async():
            result = await client._async_execute_query(mock_conn, "SELECT 1", None)
            assert result == [(1,)]

        # Run the async test
        try:
            loop = asyncio.get_event_loop()
            if loop.is_running():
                pytest.skip("Cannot run async test in running loop")
            loop.run_until_complete(test_async())
        except RuntimeError:
            # No event loop, create one
            asyncio.run(test_async())


class TestClientLogging:
    """Test client logging behavior."""

    def test_asyncpg_execute_query_logs_warning_on_exception(self):
        """Test AsyncpgClient logs warning when execute_query fails."""
        try:
            client = AsyncpgClient()
        except ImportError:
            pytest.skip("asyncpg not available")

        mock_conn = Mock()
        mock_conn.fetch = AsyncMock(side_effect=Exception("Test error"))

        with patch.object(client, "_get_event_loop") as mock_get_loop:
            mock_loop = Mock()
            mock_loop.run_until_complete.side_effect = Exception("Test error")
            mock_get_loop.return_value = mock_loop

            with patch("py_pglite.clients.logger") as mock_logger:
                with pytest.raises(Exception, match="Test error"):
                    client.execute_query(mock_conn, "SELECT 1")

                # Should log warnings for both async and sync failures
                assert mock_logger.warning.call_count == 2
                assert (
                    "async query execution failed"
                    in mock_logger.warning.call_args_list[0][0][0]
                )
                assert (
                    "execute_query failed"
                    in mock_logger.warning.call_args_list[1][0][0]
                )

    def test_psycopg_test_connection_logs_warning_on_failure(self):
        """Test PsycopgClient logs warning when test_connection fails."""
        try:
            client = PsycopgClient()
        except ImportError:
            pytest.skip("psycopg not available")

        with patch("py_pglite.clients.logger") as mock_logger:
            # Test with invalid connection string
            result = client.test_connection("invalid://connection")

            assert result is False
            # Should log warning
            mock_logger.warning.assert_called_once()
            warning_msg = mock_logger.warning.call_args[0][0]
            assert "psycopg connection test failed" in warning_msg

    def test_asyncpg_get_database_version_logs_warning_on_failure(self):
        """Test AsyncpgClient logs warning when get_database_version fails."""
        try:
            client = AsyncpgClient()
        except ImportError:
            pytest.skip("asyncpg not available")

        with patch("py_pglite.clients.logger") as mock_logger:
            # Test with invalid connection string
            result = client.get_database_version("invalid://connection")

            assert result is None
            # Should log warning
            mock_logger.warning.assert_called_once()
            warning_msg = mock_logger.warning.call_args[0][0]
            assert "Failed to get database version via asyncpg" in warning_msg
