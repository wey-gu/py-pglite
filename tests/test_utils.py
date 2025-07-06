"""Tests for framework-agnostic utility functions."""

import logging

from pathlib import Path

import pytest

from py_pglite.utils import find_pglite_modules
from py_pglite.utils import get_major_version


def test_get_major_version():
    """Test major version extraction from version strings."""
    assert get_major_version("14.1") == 14
    assert get_major_version("15.2.3") == 15
    assert get_major_version("16") == 16
    assert get_major_version("13.8.1") == 13


def test_find_pglite_modules():
    """Test finding PGlite modules in node_modules."""
    # Test with non-existent path
    result = find_pglite_modules(Path("/nonexistent/path"))
    assert result is None

    # Test with current directory (should traverse up)
    current_path = Path.cwd()
    result = find_pglite_modules(current_path)
    # Result could be None if no node_modules found, which is fine
    if result is not None:
        assert result.is_dir()
        assert (result / "@electric-sql/pglite").exists()


def test_utils_module_structure():
    """Test that the utils module has the expected structure."""
    from py_pglite import utils

    # Check that key functions exist
    assert hasattr(utils, "get_connection_from_string")
    assert hasattr(utils, "test_connection")
    assert hasattr(utils, "get_database_version")
    assert hasattr(utils, "get_table_names")
    assert hasattr(utils, "table_exists")
    assert hasattr(utils, "execute_sql")
    assert hasattr(utils, "get_major_version")
    assert hasattr(utils, "find_pglite_modules")


def test_utils_error_handling():
    """Test error handling in utility functions with invalid inputs."""
    from py_pglite.utils import execute_sql
    from py_pglite.utils import get_database_version
    from py_pglite.utils import get_table_names
    from py_pglite.utils import table_exists
    from py_pglite.utils import test_connection

    # Test with malformed connection strings
    malformed_strings = [
        "",
        "not-a-connection-string",
        "postgresql://",
        "postgresql://localhost",  # missing database
    ]

    for bad_string in malformed_strings:
        assert not test_connection(bad_string)
        assert get_database_version(bad_string) is None
        assert get_table_names(bad_string) == []
        assert not table_exists(bad_string, "test")
        assert execute_sql(bad_string, "SELECT 1") is None


def test_utils_with_logging(caplog):
    """Test that utility functions properly log warnings on errors."""
    from py_pglite.utils import execute_sql
    from py_pglite.utils import get_table_names
    from py_pglite.utils import table_exists

    bad_conn_string = "postgresql://baduser:badpass@localhost:9999/baddb"

    with caplog.at_level(logging.WARNING):
        # Test failed operations log warnings
        result = get_table_names(bad_conn_string)
        assert result == []
        assert "Failed to get table names" in caplog.text

        caplog.clear()

        result = table_exists(bad_conn_string, "test_table")
        assert result is False
        assert "Failed to check table existence" in caplog.text

        caplog.clear()

        result = execute_sql(bad_conn_string, "SELECT 1")
        assert result is None
        assert "Failed to execute SQL" in caplog.text
