"""Comprehensive tests for py_pglite utils module."""

import logging

from pathlib import Path
from unittest.mock import Mock
from unittest.mock import call
from unittest.mock import patch

import pytest

from py_pglite.utils import check_connection
from py_pglite.utils import execute_sql
from py_pglite.utils import find_pglite_modules
from py_pglite.utils import get_connection_from_string
from py_pglite.utils import get_database_version
from py_pglite.utils import get_major_version
from py_pglite.utils import get_table_names
from py_pglite.utils import table_exists


class TestConnectionUtilities:
    """Test connection-related utility functions."""

    def test_get_connection_from_string_with_default_client(self):
        """Test get_connection_from_string with default client."""
        mock_client = Mock()
        mock_connection = Mock()
        mock_client.connect.return_value = mock_connection

        with patch("py_pglite.utils.get_default_client", return_value=mock_client):
            result = get_connection_from_string("postgresql://test")

            assert result is mock_connection
            mock_client.connect.assert_called_once_with("postgresql://test")

    def test_get_connection_from_string_with_custom_client(self):
        """Test get_connection_from_string with custom client."""
        mock_client = Mock()
        mock_connection = Mock()
        mock_client.connect.return_value = mock_connection

        result = get_connection_from_string("postgresql://test", client=mock_client)

        assert result is mock_connection
        mock_client.connect.assert_called_once_with("postgresql://test")

    def test_check_connection_success_default_client(self):
        """Test check_connection with successful connection using default client."""
        mock_client = Mock()
        mock_client.test_connection.return_value = True

        with patch("py_pglite.utils.get_default_client", return_value=mock_client):
            result = check_connection("postgresql://test")

            assert result is True
            mock_client.test_connection.assert_called_once_with("postgresql://test")

    def test_check_connection_failure_custom_client(self):
        """Test check_connection with failed connection using custom client."""
        mock_client = Mock()
        mock_client.test_connection.return_value = False

        result = check_connection("postgresql://invalid", client=mock_client)

        assert result is False
        mock_client.test_connection.assert_called_once_with("postgresql://invalid")

    def test_test_connection_alias_exists(self):
        """Test that test_connection alias exists and works."""
        from py_pglite.utils import test_connection

        mock_client = Mock()
        mock_client.test_connection.return_value = True

        with patch("py_pglite.utils.get_default_client", return_value=mock_client):
            result = test_connection("postgresql://test")

            assert result is True


class TestDatabaseIntrospection:
    """Test database introspection utility functions."""

    def test_get_database_version_success_default_client(self):
        """Test get_database_version with successful query using default client."""
        mock_client = Mock()
        mock_client.get_database_version.return_value = "PostgreSQL 15.2"

        with patch("py_pglite.utils.get_default_client", return_value=mock_client):
            result = get_database_version("postgresql://test")

            assert result == "PostgreSQL 15.2"
            mock_client.get_database_version.assert_called_once_with(
                "postgresql://test"
            )

    def test_get_database_version_failure_custom_client(self):
        """Test get_database_version with failed query using custom client."""
        mock_client = Mock()
        mock_client.get_database_version.return_value = None

        result = get_database_version("postgresql://invalid", client=mock_client)

        assert result is None
        mock_client.get_database_version.assert_called_once_with("postgresql://invalid")

    def test_get_table_names_success_default_schema(self):
        """Test get_table_names with successful query using default schema."""
        mock_client = Mock()
        mock_connection = Mock()
        mock_client.connect.return_value = mock_connection
        mock_client.execute_query.return_value = [("users",), ("posts",), ("comments",)]

        with patch("py_pglite.utils.get_default_client", return_value=mock_client):
            result = get_table_names("postgresql://test")

            assert result == ["users", "posts", "comments"]
            mock_client.connect.assert_called_once_with("postgresql://test")
            mock_client.execute_query.assert_called_once()
            query_call = mock_client.execute_query.call_args
            assert "information_schema.tables" in query_call[0][1]
            assert query_call[0][2] == ("public",)
            mock_client.close_connection.assert_called_once_with(mock_connection)

    def test_get_table_names_custom_schema(self):
        """Test get_table_names with custom schema."""
        mock_client = Mock()
        mock_connection = Mock()
        mock_client.connect.return_value = mock_connection
        mock_client.execute_query.return_value = [("admin_users",)]

        result = get_table_names(
            "postgresql://test", schema="admin", client=mock_client
        )

        assert result == ["admin_users"]
        query_call = mock_client.execute_query.call_args
        assert query_call[0][2] == ("admin",)

    def test_get_table_names_exception_handling(self):
        """Test get_table_names exception handling."""
        mock_client = Mock()
        mock_client.connect.side_effect = Exception("Connection failed")

        with patch("py_pglite.utils.get_default_client", return_value=mock_client):
            result = get_table_names("postgresql://invalid")

            assert result == []

    def test_get_table_names_query_exception_handling(self):
        """Test get_table_names exception handling during query."""
        mock_client = Mock()
        mock_connection = Mock()
        mock_client.connect.return_value = mock_connection
        mock_client.execute_query.side_effect = Exception("Query failed")

        with patch("py_pglite.utils.get_default_client", return_value=mock_client):
            result = get_table_names("postgresql://test")

            assert result == []
            mock_client.close_connection.assert_called_once_with(mock_connection)

    def test_table_exists_true_default_schema(self):
        """Test table_exists returns True for existing table in default schema."""
        mock_client = Mock()
        mock_connection = Mock()
        mock_client.connect.return_value = mock_connection
        mock_client.execute_query.return_value = [(True,)]

        with patch("py_pglite.utils.get_default_client", return_value=mock_client):
            result = table_exists("postgresql://test", "users")

            assert result is True
            query_call = mock_client.execute_query.call_args
            assert "EXISTS" in query_call[0][1]
            assert query_call[0][2] == ("public", "users")

    def test_table_exists_false_custom_schema(self):
        """Test table_exists returns False for non-existing table in custom schema."""
        mock_client = Mock()
        mock_connection = Mock()
        mock_client.connect.return_value = mock_connection
        mock_client.execute_query.return_value = [(False,)]

        result = table_exists(
            "postgresql://test", "nonexistent", schema="admin", client=mock_client
        )

        assert result is False
        query_call = mock_client.execute_query.call_args
        assert query_call[0][2] == ("admin", "nonexistent")

    def test_table_exists_empty_result(self):
        """Test table_exists with empty result."""
        mock_client = Mock()
        mock_connection = Mock()
        mock_client.connect.return_value = mock_connection
        mock_client.execute_query.return_value = []

        with patch("py_pglite.utils.get_default_client", return_value=mock_client):
            result = table_exists("postgresql://test", "users")

            assert result is False

    def test_table_exists_exception_handling(self):
        """Test table_exists exception handling."""
        mock_client = Mock()
        mock_client.connect.side_effect = Exception("Connection failed")

        with patch("py_pglite.utils.get_default_client", return_value=mock_client):
            result = table_exists("postgresql://invalid", "users")

            assert result is False


class TestSQLExecution:
    """Test SQL execution utility functions."""

    def test_execute_sql_success_no_params(self):
        """Test execute_sql with successful query and no parameters."""
        mock_client = Mock()
        mock_connection = Mock()
        mock_client.connect.return_value = mock_connection
        mock_client.execute_query.return_value = [("result1",), ("result2",)]

        with patch("py_pglite.utils.get_default_client", return_value=mock_client):
            result = execute_sql("postgresql://test", "SELECT * FROM users")

            assert result == [("result1",), ("result2",)]
            mock_client.connect.assert_called_once_with("postgresql://test")
            mock_client.execute_query.assert_called_once_with(
                mock_connection, "SELECT * FROM users", None
            )
            mock_client.close_connection.assert_called_once_with(mock_connection)

    def test_execute_sql_success_with_params(self):
        """Test execute_sql with successful query and parameters."""
        mock_client = Mock()
        mock_connection = Mock()
        mock_client.connect.return_value = mock_connection
        mock_client.execute_query.return_value = [("john",)]

        result = execute_sql(
            "postgresql://test",
            "SELECT name FROM users WHERE id = %s",
            params=(1,),
            client=mock_client,
        )

        assert result == [("john",)]
        mock_client.execute_query.assert_called_once_with(
            mock_connection, "SELECT name FROM users WHERE id = %s", (1,)
        )

    def test_execute_sql_connection_exception(self):
        """Test execute_sql exception handling during connection."""
        mock_client = Mock()
        mock_client.connect.side_effect = Exception("Connection failed")

        with patch("py_pglite.utils.get_default_client", return_value=mock_client):
            result = execute_sql("postgresql://invalid", "SELECT 1")

            assert result is None

    def test_execute_sql_query_exception(self):
        """Test execute_sql exception handling during query execution."""
        mock_client = Mock()
        mock_connection = Mock()
        mock_client.connect.return_value = mock_connection
        mock_client.execute_query.side_effect = Exception("Query failed")

        with patch("py_pglite.utils.get_default_client", return_value=mock_client):
            result = execute_sql("postgresql://test", "INVALID SQL")

            assert result is None
            mock_client.close_connection.assert_called_once_with(mock_connection)


class TestVersionParsing:
    """Test version parsing utility functions."""

    def test_get_major_version_standard_format(self):
        """Test get_major_version with standard version format."""
        assert get_major_version("15.2") == 15
        assert get_major_version("14.8") == 14
        assert get_major_version("13.11") == 13

    def test_get_major_version_single_digit(self):
        """Test get_major_version with single digit version."""
        assert get_major_version("9") == 9

    def test_get_major_version_with_patch(self):
        """Test get_major_version with patch version."""
        assert get_major_version("15.2.1") == 15
        assert get_major_version("14.8.0") == 14

    def test_get_major_version_beta_versions(self):
        """Test get_major_version with beta versions."""
        assert get_major_version("16.0beta1") == 16
        assert get_major_version("15.2rc1") == 15


class TestNodeModulesFinding:
    """Test Node.js modules finding utility functions."""

    def test_find_pglite_modules_not_found(self):
        """Test find_pglite_modules when modules are not found."""
        with (
            patch.object(Path, "resolve") as mock_resolve,
            patch.object(Path, "exists") as mock_exists,
        ):
            # Create a path that reaches root without finding modules
            test_path = Path("/test")
            mock_resolve.return_value = test_path
            mock_exists.return_value = False

            result = find_pglite_modules(test_path)

            assert result is None

    def test_find_pglite_modules_found_in_directory(self):
        """Test find_pglite_modules integration with simple case."""
        import os
        import tempfile

        with tempfile.TemporaryDirectory() as temp_dir:
            # Create the expected directory structure
            pglite_dir = Path(temp_dir) / "node_modules" / "@electric-sql" / "pglite"
            pglite_dir.mkdir(parents=True, exist_ok=True)

            result = find_pglite_modules(Path(temp_dir))

            expected_path = Path(temp_dir) / "node_modules"
            assert result is not None
            assert result.resolve() == expected_path.resolve()


class TestLoggingAndErrorHandling:
    """Test logging and error handling in utility functions."""

    def test_get_table_names_logs_warning_on_exception(self):
        """Test that get_table_names logs warning on exception."""
        mock_client = Mock()
        mock_client.connect.side_effect = Exception("Connection failed")

        with (
            patch("py_pglite.utils.get_default_client", return_value=mock_client),
            patch("py_pglite.utils.logger") as mock_logger,
        ):
            result = get_table_names("postgresql://invalid")

            assert result == []
            mock_logger.warning.assert_called_once()
            assert "Failed to get table names" in mock_logger.warning.call_args[0][0]

    def test_table_exists_logs_warning_on_exception(self):
        """Test that table_exists logs warning on exception."""
        mock_client = Mock()
        mock_client.connect.side_effect = Exception("Connection failed")

        with (
            patch("py_pglite.utils.get_default_client", return_value=mock_client),
            patch("py_pglite.utils.logger") as mock_logger,
        ):
            result = table_exists("postgresql://invalid", "users")

            assert result is False
            mock_logger.warning.assert_called_once()
            assert (
                "Failed to check table existence" in mock_logger.warning.call_args[0][0]
            )

    def test_execute_sql_logs_warning_on_exception(self):
        """Test that execute_sql logs warning on exception."""
        mock_client = Mock()
        mock_client.connect.side_effect = Exception("Connection failed")

        with (
            patch("py_pglite.utils.get_default_client", return_value=mock_client),
            patch("py_pglite.utils.logger") as mock_logger,
        ):
            result = execute_sql("postgresql://invalid", "SELECT 1")

            assert result is None
            mock_logger.warning.assert_called_once()
            assert "Failed to execute SQL" in mock_logger.warning.call_args[0][0]


class TestClientIntegration:
    """Test integration with different database clients."""

    def test_functions_use_get_default_client_when_none_provided(self):
        """Test that all funcs properly use get_default_client when client is None."""
        mock_client = Mock()
        mock_client.test_connection.return_value = True
        mock_client.get_database_version.return_value = "15.2"
        mock_client.connect.return_value = Mock()
        mock_client.execute_query.return_value = []

        with patch(
            "py_pglite.utils.get_default_client", return_value=mock_client
        ) as mock_get_client:
            # Test all functions that use client
            check_connection("postgresql://test")
            get_database_version("postgresql://test")
            get_table_names("postgresql://test")
            table_exists("postgresql://test", "users")
            execute_sql("postgresql://test", "SELECT 1")

            # Should call get_default_client 5 times
            assert mock_get_client.call_count == 5

    def test_functions_accept_custom_client(self):
        """Test that all functions properly accept and use custom client."""
        mock_client = Mock()
        mock_client.test_connection.return_value = True
        mock_client.get_database_version.return_value = "15.2"
        mock_client.connect.return_value = Mock()
        mock_client.execute_query.return_value = []

        with patch("py_pglite.utils.get_default_client") as mock_get_client:
            # Test all functions with custom client
            check_connection("postgresql://test", client=mock_client)
            get_database_version("postgresql://test", client=mock_client)
            get_table_names("postgresql://test", client=mock_client)
            table_exists("postgresql://test", "users", client=mock_client)
            execute_sql("postgresql://test", "SELECT 1", client=mock_client)

            # Should not call get_default_client at all
            mock_get_client.assert_not_called()


class TestGetConnectionFromString:
    """Additional tests for get_connection_from_string function."""

    def test_get_connection_from_string_passes_through_exceptions(self):
        """Test that get_connection_from_string allows exceptions to propagate."""
        mock_client = Mock()
        mock_client.connect.side_effect = Exception("Connection failed")

        with pytest.raises(Exception, match="Connection failed"):
            get_connection_from_string("postgresql://invalid", client=mock_client)


class TestUtilityFunctionIntegration:
    """Test integration scenarios between utility functions."""

    def test_execute_sql_with_table_existence_check(self):
        """Test combining table_exists with execute_sql."""
        mock_client = Mock()
        mock_connection = Mock()
        mock_client.connect.return_value = mock_connection

        # First call for table_exists - table exists
        # Second call for execute_sql - return some data
        mock_client.execute_query.side_effect = [
            [(True,)],  # table exists
            [("row1",), ("row2",)],  # execute_sql results
        ]

        with patch("py_pglite.utils.get_default_client", return_value=mock_client):
            # Check if table exists
            exists = table_exists("postgresql://test", "users")
            assert exists is True

            # If it exists, query it
            if exists:
                results = execute_sql("postgresql://test", "SELECT * FROM users")
                assert results == [("row1",), ("row2",)]

    def test_version_parsing_integration(self):
        """Test version parsing with database version retrieval."""
        mock_client = Mock()
        mock_client.get_database_version.return_value = "15.2.1"

        with patch("py_pglite.utils.get_default_client", return_value=mock_client):
            version_string = get_database_version("postgresql://test")
            if version_string:
                major_version = get_major_version(version_string)
                assert major_version == 15
