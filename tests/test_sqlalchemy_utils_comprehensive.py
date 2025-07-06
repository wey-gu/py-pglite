"""Comprehensive tests for SQLAlchemy utils module."""

from pathlib import Path  # type: ignore[reportUnusedImport]
from unittest.mock import MagicMock
from unittest.mock import Mock
from unittest.mock import patch

import pytest


class TestSQLAlchemyImports:
    """Test SQLAlchemy import handling and availability detection."""

    def test_has_sqlalchemy_orm_flag(self):
        """Test that HAS_SQLALCHEMY_ORM is properly set."""
        from py_pglite.sqlalchemy.utils import HAS_SQLALCHEMY_ORM

        # Should be True in test environment
        assert HAS_SQLALCHEMY_ORM is True

    def test_has_sqlmodel_flag(self):
        """Test that HAS_SQLMODEL flag is set correctly."""
        from py_pglite.sqlalchemy.utils import HAS_SQLMODEL

        # May be True or False depending on installation
        assert isinstance(HAS_SQLMODEL, bool)

    def test_ensure_sqlalchemy_success(self):
        """Test _ensure_sqlalchemy when SQLAlchemy is available."""
        from py_pglite.sqlalchemy.utils import _ensure_sqlalchemy

        with patch("py_pglite.sqlalchemy.utils.HAS_SQLALCHEMY_ORM", True):
            # Should not raise exception
            _ensure_sqlalchemy()

    def test_ensure_sqlalchemy_failure(self):
        """Test _ensure_sqlalchemy raises error when SQLAlchemy unavailable."""
        from py_pglite.sqlalchemy.utils import _ensure_sqlalchemy

        with patch("py_pglite.sqlalchemy.utils.HAS_SQLALCHEMY_ORM", False):
            with pytest.raises(ImportError, match="SQLAlchemy is required"):
                _ensure_sqlalchemy()


class TestTableOperations:
    """Test table creation and deletion operations."""

    def test_create_all_tables_with_base(self):
        """Test create_all_tables with declarative base."""
        from py_pglite.sqlalchemy.utils import create_all_tables

        mock_engine = Mock()
        mock_base = Mock()
        mock_base.metadata = Mock()

        create_all_tables(mock_engine, mock_base)

        mock_base.metadata.create_all.assert_called_once_with(mock_engine)

    def test_create_all_tables_with_sqlmodel(self):
        """Test create_all_tables with SQLModel."""
        from py_pglite.sqlalchemy.utils import create_all_tables

        mock_engine = Mock()
        mock_sqlmodel = Mock()
        mock_sqlmodel.metadata = Mock()

        with (
            patch("py_pglite.sqlalchemy.utils.HAS_SQLMODEL", True),
            patch("py_pglite.sqlalchemy.utils.SQLModel", mock_sqlmodel),
        ):
            create_all_tables(mock_engine)

            mock_sqlmodel.metadata.create_all.assert_called_once_with(mock_engine)

    def test_create_all_tables_no_base_no_sqlmodel(self):
        """Test create_all_tables raises error when no base and no SQLModel."""
        from py_pglite.sqlalchemy.utils import create_all_tables

        mock_engine = Mock()

        with patch("py_pglite.sqlalchemy.utils.HAS_SQLMODEL", False):
            with pytest.raises(ValueError, match="Either provide a declarative base"):
                create_all_tables(mock_engine)

    def test_drop_all_tables_with_base(self):
        """Test drop_all_tables with declarative base."""
        from py_pglite.sqlalchemy.utils import drop_all_tables

        mock_engine = Mock()
        mock_base = Mock()
        mock_base.metadata = Mock()

        drop_all_tables(mock_engine, mock_base)

        mock_base.metadata.drop_all.assert_called_once_with(mock_engine)

    def test_drop_all_tables_with_sqlmodel(self):
        """Test drop_all_tables with SQLModel."""
        from py_pglite.sqlalchemy.utils import drop_all_tables

        mock_engine = Mock()
        mock_sqlmodel = Mock()
        mock_sqlmodel.metadata = Mock()

        with (
            patch("py_pglite.sqlalchemy.utils.HAS_SQLMODEL", True),
            patch("py_pglite.sqlalchemy.utils.SQLModel", mock_sqlmodel),
        ):
            drop_all_tables(mock_engine)

            mock_sqlmodel.metadata.drop_all.assert_called_once_with(mock_engine)

    def test_drop_all_tables_no_base_no_sqlmodel(self):
        """Test drop_all_tables raises error when no base and no SQLModel."""
        from py_pglite.sqlalchemy.utils import drop_all_tables

        mock_engine = Mock()

        with patch("py_pglite.sqlalchemy.utils.HAS_SQLMODEL", False):
            with pytest.raises(ValueError, match="Either provide a declarative base"):
                drop_all_tables(mock_engine)


class TestSessionOperations:
    """Test session class operations."""

    def test_get_session_class_sqlmodel_available(self):
        """Test get_session_class returns SQLModel session when available."""
        from py_pglite.sqlalchemy.utils import get_session_class

        mock_sqlmodel_session = Mock()

        with (
            patch("py_pglite.sqlalchemy.utils.HAS_SQLMODEL", True),
            patch("py_pglite.sqlalchemy.utils.SQLModelSession", mock_sqlmodel_session),
        ):
            result = get_session_class()

            assert result is mock_sqlmodel_session

    def test_get_session_class_sqlalchemy_fallback(self):
        """Test get_session_class falls back to SQLAlchemy session."""
        from py_pglite.sqlalchemy.utils import get_session_class

        mock_sqlalchemy_session = Mock()

        with (
            patch("py_pglite.sqlalchemy.utils.HAS_SQLMODEL", False),
            patch("py_pglite.sqlalchemy.utils.HAS_SQLALCHEMY_ORM", True),
            patch(
                "py_pglite.sqlalchemy.utils.SQLAlchemySession", mock_sqlalchemy_session
            ),
        ):
            result = get_session_class()

            assert result is mock_sqlalchemy_session

    def test_get_session_class_no_sessions_available(self):
        """Test get_session_class raises error when no sessions available."""
        from py_pglite.sqlalchemy.utils import get_session_class

        with (
            patch("py_pglite.sqlalchemy.utils.HAS_SQLMODEL", False),
            patch("py_pglite.sqlalchemy.utils.HAS_SQLALCHEMY_ORM", False),
        ):
            with pytest.raises(
                ImportError, match="Neither SQLModel nor SQLAlchemy ORM Session found"
            ):
                get_session_class()


class TestMetadataOperations:
    """Test metadata reflection and operations."""

    def test_reflect_tables(self):
        """Test reflect_tables functionality."""
        from py_pglite.sqlalchemy.utils import reflect_tables

        mock_engine = Mock()
        mock_metadata = Mock()

        with patch("py_pglite.sqlalchemy.utils.MetaData", return_value=mock_metadata):
            result = reflect_tables(mock_engine)

            assert result is mock_metadata
            mock_metadata.reflect.assert_called_once_with(bind=mock_engine)

    def test_get_table_names(self):
        """Test get_table_names functionality."""
        from py_pglite.sqlalchemy.utils import get_table_names

        mock_engine = Mock()
        mock_metadata = Mock()
        mock_metadata.tables = {"table1": Mock(), "table2": Mock()}

        with patch(
            "py_pglite.sqlalchemy.utils.reflect_tables", return_value=mock_metadata
        ):
            result = get_table_names(mock_engine)

            assert result == ["table1", "table2"]


class TestDataCleaning:
    """Test data cleaning operations."""

    def test_clear_all_data_with_base(self):
        """Test clear_all_data with declarative base."""
        from py_pglite.sqlalchemy.utils import clear_all_data

        mock_engine = Mock()
        mock_connection = Mock()
        # Properly mock the context manager
        mock_context_manager = Mock()
        mock_context_manager.__enter__ = Mock(return_value=mock_connection)
        mock_context_manager.__exit__ = Mock(return_value=None)
        mock_engine.begin.return_value = mock_context_manager

        mock_base = Mock()
        mock_table1 = Mock()
        mock_table2 = Mock()
        mock_base.metadata.sorted_tables = [mock_table1, mock_table2]

        clear_all_data(mock_engine, mock_base)

        # Verify tables cleared
        mock_connection.execute.assert_any_call(mock_table2.delete())
        mock_connection.execute.assert_any_call(mock_table1.delete())

    def test_clear_all_data_with_sqlmodel(self):
        """Test clear_all_data with SQLModel."""
        from py_pglite.sqlalchemy.utils import clear_all_data

        mock_engine = Mock()
        mock_connection = Mock()
        # Properly mock the context manager
        mock_context_manager = Mock()
        mock_context_manager.__enter__ = Mock(return_value=mock_connection)
        mock_context_manager.__exit__ = Mock(return_value=None)
        mock_engine.begin.return_value = mock_context_manager

        mock_sqlmodel = Mock()
        mock_table = Mock()
        mock_sqlmodel.metadata.sorted_tables = [mock_table]

        with (
            patch("py_pglite.sqlalchemy.utils.HAS_SQLMODEL", True),
            patch("py_pglite.sqlalchemy.utils.SQLModel", mock_sqlmodel),
        ):
            clear_all_data(mock_engine)

            # Verify table cleared
            mock_connection.execute.assert_any_call(mock_table.delete())

    def test_clear_all_data_reflect_fallback(self):
        """Test clear_all_data falls back to reflection when no base."""
        from py_pglite.sqlalchemy.utils import clear_all_data

        mock_engine = Mock()
        mock_connection = Mock()
        # Properly mock the context manager
        mock_context_manager = Mock()
        mock_context_manager.__enter__ = Mock(return_value=mock_connection)
        mock_context_manager.__exit__ = Mock(return_value=None)
        mock_engine.begin.return_value = mock_context_manager

        mock_metadata = Mock()
        mock_table = Mock()
        mock_metadata.sorted_tables = [mock_table]

        with (
            patch("py_pglite.sqlalchemy.utils.HAS_SQLMODEL", False),
            patch(
                "py_pglite.sqlalchemy.utils.reflect_tables", return_value=mock_metadata
            ),
        ):
            clear_all_data(mock_engine)

            mock_connection.execute.assert_any_call(mock_table.delete())


class TestDatabaseMaintenance:
    """Test database maintenance utilities."""

    def test_clean_database_data(self):
        """Test clean_database_data functionality."""
        from py_pglite.sqlalchemy.utils import clean_database_data

        mock_engine = Mock()
        mock_session = Mock()
        mock_connection = Mock()
        # Properly mock the session context manager
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)
        # Properly mock the connection context manager
        mock_conn_context = Mock()
        mock_conn_context.__enter__ = Mock(return_value=mock_connection)
        mock_conn_context.__exit__ = Mock(return_value=None)
        mock_session.connection.return_value = mock_conn_context

        # Mock query result
        mock_result = Mock()
        mock_result.fetchall.return_value = [("table1",), ("table2",)]
        mock_connection.execute.return_value = mock_result

        with (
            patch("py_pglite.sqlalchemy.utils._ensure_sqlalchemy"),
            patch(
                "py_pglite.sqlalchemy.utils.SQLAlchemySession",
                return_value=mock_session,
            ),
        ):
            clean_database_data(mock_engine)

            # Verify session was used
            mock_session.commit.assert_called_once()

    def test_clean_database_data_with_exclusions(self):
        """Test clean_database_data with excluded tables."""
        from py_pglite.sqlalchemy.utils import clean_database_data

        mock_engine = Mock()
        mock_session = Mock()
        mock_connection = Mock()
        # Properly mock the session context manager
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)
        # Properly mock the connection context manager
        mock_conn_context = Mock()
        mock_conn_context.__enter__ = Mock(return_value=mock_connection)
        mock_conn_context.__exit__ = Mock(return_value=None)
        mock_session.connection.return_value = mock_conn_context

        # Mock query result
        mock_result = Mock()
        mock_result.fetchall.return_value = [("table1",), ("exclude_me",), ("table2",)]
        mock_connection.execute.return_value = mock_result

        with (
            patch("py_pglite.sqlalchemy.utils._ensure_sqlalchemy"),
            patch(
                "py_pglite.sqlalchemy.utils.SQLAlchemySession",
                return_value=mock_session,
            ),
        ):
            clean_database_data(mock_engine, exclude_tables=["exclude_me"])

            # Verify execution happened
            mock_session.commit.assert_called_once()

    def test_reset_sequences(self):
        """Test reset_sequences functionality."""
        from py_pglite.sqlalchemy.utils import reset_sequences

        mock_engine = Mock()
        mock_session = Mock()
        mock_connection = Mock()
        # Properly mock the session context manager
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)
        # Properly mock the connection context manager
        mock_conn_context = Mock()
        mock_conn_context.__enter__ = Mock(return_value=mock_connection)
        mock_conn_context.__exit__ = Mock(return_value=None)
        mock_session.connection.return_value = mock_conn_context

        # Mock sequence query result
        mock_result = Mock()
        mock_result.fetchall.return_value = [("seq1",), ("seq2",)]
        mock_connection.execute.return_value = mock_result

        with (
            patch("py_pglite.sqlalchemy.utils._ensure_sqlalchemy"),
            patch(
                "py_pglite.sqlalchemy.utils.SQLAlchemySession",
                return_value=mock_session,
            ),
        ):
            reset_sequences(mock_engine)

            mock_session.commit.assert_called_once()

    def test_get_table_row_counts(self):
        """Test get_table_row_counts functionality."""
        from py_pglite.sqlalchemy.utils import get_table_row_counts

        mock_engine = Mock()
        mock_session = Mock()
        mock_connection = Mock()
        # Properly mock the session context manager
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)
        # Properly mock the connection context manager
        mock_conn_context = Mock()
        mock_conn_context.__enter__ = Mock(return_value=mock_connection)
        mock_conn_context.__exit__ = Mock(return_value=None)
        mock_session.connection.return_value = mock_conn_context

        # Mock table list query
        mock_tables_result = Mock()
        mock_tables_result.fetchall.return_value = [("table1",), ("table2",)]

        # Mock count queries
        mock_count_result1 = Mock()
        mock_count_result1.fetchone.return_value = (5,)
        mock_count_result2 = Mock()
        mock_count_result2.fetchone.return_value = (10,)

        mock_connection.execute.side_effect = [
            mock_tables_result,  # Table list query
            mock_count_result1,  # Count for table1
            mock_count_result2,  # Count for table2
        ]

        with (
            patch("py_pglite.sqlalchemy.utils._ensure_sqlalchemy"),
            patch(
                "py_pglite.sqlalchemy.utils.SQLAlchemySession",
                return_value=mock_session,
            ),
        ):
            result = get_table_row_counts(mock_engine)

            assert result == {"table1": 5, "table2": 10}

    def test_get_table_row_counts_empty_result(self):
        """Test get_table_row_counts handles empty count results."""
        from py_pglite.sqlalchemy.utils import get_table_row_counts

        mock_engine = Mock()
        mock_session = Mock()
        mock_connection = Mock()
        # Properly mock the session context manager
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)
        # Properly mock the connection context manager
        mock_conn_context = Mock()
        mock_conn_context.__enter__ = Mock(return_value=mock_connection)
        mock_conn_context.__exit__ = Mock(return_value=None)
        mock_session.connection.return_value = mock_conn_context

        # Mock table list query
        mock_tables_result = Mock()
        mock_tables_result.fetchall.return_value = [("table1",)]

        # Mock count query returning None
        mock_count_result = Mock()
        mock_count_result.fetchone.return_value = None

        mock_connection.execute.side_effect = [
            mock_tables_result,  # Table list query
            mock_count_result,  # Count query returning None
        ]

        with (
            patch("py_pglite.sqlalchemy.utils._ensure_sqlalchemy"),
            patch(
                "py_pglite.sqlalchemy.utils.SQLAlchemySession",
                return_value=mock_session,
            ),
        ):
            result = get_table_row_counts(mock_engine)

            assert result == {"table1": 0}

    def test_verify_database_empty_true(self):
        """Test verify_database_empty returns True for empty database."""
        from py_pglite.sqlalchemy.utils import verify_database_empty

        mock_engine = Mock()

        with patch(
            "py_pglite.sqlalchemy.utils.get_table_row_counts",
            return_value={"table1": 0, "table2": 0},
        ):
            result = verify_database_empty(mock_engine)
            assert result is True

    def test_verify_database_empty_false(self):
        """Test verify_database_empty returns False for non-empty database."""
        from py_pglite.sqlalchemy.utils import verify_database_empty

        mock_engine = Mock()

        with patch(
            "py_pglite.sqlalchemy.utils.get_table_row_counts",
            return_value={"table1": 5, "table2": 0},
        ):
            result = verify_database_empty(mock_engine)
            assert result is False

    def test_verify_database_empty_with_exclusions(self):
        """Test verify_database_empty with excluded tables."""
        from py_pglite.sqlalchemy.utils import verify_database_empty

        mock_engine = Mock()

        # Table 'exclude_me' has data but should be ignored
        with patch(
            "py_pglite.sqlalchemy.utils.get_table_row_counts",
            return_value={"table1": 0, "exclude_me": 100},
        ):
            result = verify_database_empty(mock_engine, exclude_tables=["exclude_me"])
            assert result is True


class TestSchemaOperations:
    """Test schema creation and management."""

    def test_create_test_schema(self):
        """Test create_test_schema functionality."""
        from py_pglite.sqlalchemy.utils import create_test_schema

        mock_engine = Mock()
        mock_session = Mock()
        mock_connection = Mock()
        # Properly mock the session context manager
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)
        # Properly mock the connection context manager
        mock_conn_context = Mock()
        mock_conn_context.__enter__ = Mock(return_value=mock_connection)
        mock_conn_context.__exit__ = Mock(return_value=None)
        mock_session.connection.return_value = mock_conn_context

        with (
            patch("py_pglite.sqlalchemy.utils._ensure_sqlalchemy"),
            patch(
                "py_pglite.sqlalchemy.utils.SQLAlchemySession",
                return_value=mock_session,
            ),
        ):
            create_test_schema(mock_engine, "test_schema")

            mock_session.commit.assert_called_once()

    def test_create_test_schema_invalid_name(self):
        """Test create_test_schema rejects invalid schema names."""
        from py_pglite.sqlalchemy.utils import create_test_schema

        mock_engine = Mock()
        mock_session = Mock()
        mock_connection = Mock()
        # Properly mock the session context manager
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)
        # Properly mock the connection context manager
        mock_conn_context = Mock()
        mock_conn_context.__enter__ = Mock(return_value=mock_connection)
        mock_conn_context.__exit__ = Mock(return_value=None)
        mock_session.connection.return_value = mock_conn_context

        with (
            patch("py_pglite.sqlalchemy.utils._ensure_sqlalchemy"),
            patch(
                "py_pglite.sqlalchemy.utils.SQLAlchemySession",
                return_value=mock_session,
            ),
        ):
            # The validation should happen after session creation
            # but before SQL execution
            with pytest.raises(ValueError, match="Invalid schema name"):
                create_test_schema(mock_engine, "invalid; DROP TABLE users;")

    def test_drop_test_schema(self):
        """Test drop_test_schema functionality."""
        from py_pglite.sqlalchemy.utils import drop_test_schema

        mock_engine = Mock()
        mock_session = Mock()
        mock_connection = Mock()
        # Properly mock the session context manager
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)
        # Properly mock the connection context manager
        mock_conn_context = Mock()
        mock_conn_context.__enter__ = Mock(return_value=mock_connection)
        mock_conn_context.__exit__ = Mock(return_value=None)
        mock_session.connection.return_value = mock_conn_context

        with (
            patch("py_pglite.sqlalchemy.utils._ensure_sqlalchemy"),
            patch(
                "py_pglite.sqlalchemy.utils.SQLAlchemySession",
                return_value=mock_session,
            ),
        ):
            drop_test_schema(mock_engine, "test_schema")

            mock_session.commit.assert_called_once()

    def test_drop_test_schema_invalid_name(self):
        """Test drop_test_schema rejects invalid schema names."""
        from py_pglite.sqlalchemy.utils import drop_test_schema

        mock_engine = Mock()
        mock_session = Mock()
        mock_connection = Mock()
        # Properly mock the session context manager
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)
        # Properly mock the connection context manager
        mock_conn_context = Mock()
        mock_conn_context.__enter__ = Mock(return_value=mock_connection)
        mock_conn_context.__exit__ = Mock(return_value=None)
        mock_session.connection.return_value = mock_conn_context

        with (
            patch("py_pglite.sqlalchemy.utils._ensure_sqlalchemy"),
            patch(
                "py_pglite.sqlalchemy.utils.SQLAlchemySession",
                return_value=mock_session,
            ),
        ):
            # The validation should happen after session creation
            # but before SQL execution
            with pytest.raises(ValueError, match="Invalid schema name"):
                drop_test_schema(mock_engine, "invalid; DROP DATABASE production;")


class TestSQLFileOperations:
    """Test SQL file execution functionality."""

    def test_execute_sql_file(self):
        """Test execute_sql_file functionality."""
        from py_pglite.sqlalchemy.utils import execute_sql_file

        mock_engine = Mock()
        mock_session = Mock()
        mock_connection = Mock()
        # Properly mock the session context manager
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)
        # Properly mock the connection context manager
        mock_conn_context = Mock()
        mock_conn_context.__enter__ = Mock(return_value=mock_connection)
        mock_conn_context.__exit__ = Mock(return_value=None)
        mock_session.connection.return_value = mock_conn_context

        test_sql = "CREATE TABLE test (id INTEGER); INSERT INTO test VALUES (1);"

        with (
            patch("py_pglite.sqlalchemy.utils._ensure_sqlalchemy"),
            patch(
                "py_pglite.sqlalchemy.utils.SQLAlchemySession",
                return_value=mock_session,
            ),
            patch("builtins.open", mock_open(test_sql)),
        ):
            execute_sql_file(mock_engine, "/path/to/test.sql")

            # Verify statements were executed
            assert mock_connection.execute.call_count >= 2  # At least 2 statements
            mock_session.commit.assert_called_once()

    def test_execute_sql_file_empty_statements_filtered(self):
        """Test execute_sql_file filters out empty statements."""
        from py_pglite.sqlalchemy.utils import execute_sql_file

        mock_engine = Mock()
        mock_session = Mock()
        mock_connection = Mock()
        # Properly mock the session context manager
        mock_session.__enter__ = Mock(return_value=mock_session)
        mock_session.__exit__ = Mock(return_value=None)
        # Properly mock the connection context manager
        mock_conn_context = Mock()
        mock_conn_context.__enter__ = Mock(return_value=mock_connection)
        mock_conn_context.__exit__ = Mock(return_value=None)
        mock_session.connection.return_value = mock_conn_context

        # SQL with empty statements and whitespace
        test_sql = (
            "CREATE TABLE test (id INTEGER);\n\n; \n; INSERT INTO test VALUES (1);"
        )

        with (
            patch("py_pglite.sqlalchemy.utils._ensure_sqlalchemy"),
            patch(
                "py_pglite.sqlalchemy.utils.SQLAlchemySession",
                return_value=mock_session,
            ),
            patch("builtins.open", mock_open(test_sql)),
        ):
            execute_sql_file(mock_engine, "/path/to/test.sql")

            # Should only execute non-empty statements
            assert mock_connection.execute.call_count == 2  # Only 2 non-empty stmt
            mock_session.commit.assert_called_once()


def mock_open(content):
    """Helper function to create a mock open context manager."""
    mock_file = MagicMock()
    mock_file.read.return_value = content
    mock_file.__enter__.return_value = mock_file
    mock_file.__exit__.return_value = None
    return MagicMock(return_value=mock_file)
