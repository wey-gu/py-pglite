"""Comprehensive tests for pytest_plugin module - targeting 33.61% coverage gap."""

import warnings

from unittest.mock import Mock
from unittest.mock import call
from unittest.mock import patch

import pytest

from py_pglite.pytest_plugin import HAS_DJANGO
from py_pglite.pytest_plugin import HAS_PYTEST_DJANGO
from py_pglite.pytest_plugin import HAS_SQLALCHEMY
from py_pglite.pytest_plugin import _auto_mark_test
from py_pglite.pytest_plugin import _check_framework_isolation
from py_pglite.pytest_plugin import _is_explicitly_marked
from py_pglite.pytest_plugin import _should_disable_django_plugin
from py_pglite.pytest_plugin import pytest_collection_modifyitems
from py_pglite.pytest_plugin import pytest_configure
from py_pglite.pytest_plugin import pytest_runtest_setup
from py_pglite.pytest_plugin import pytest_terminal_summary


class TestFrameworkAvailabilityDetection:
    """Test framework availability detection flags."""

    def test_framework_availability_flags_are_set(self):
        """Test that framework availability flags are boolean values."""
        assert isinstance(HAS_SQLALCHEMY, bool)
        assert isinstance(HAS_DJANGO, bool)
        assert isinstance(HAS_PYTEST_DJANGO, bool)

    def test_framework_imports_detected_correctly(self):
        """Test that framework imports are detected correctly."""
        # These will be True in test environment where frameworks are available
        # The actual detection logic is tested by the import success/failure
        try:
            import sqlalchemy

            assert HAS_SQLALCHEMY is True
        except ImportError:
            assert HAS_SQLALCHEMY is False

        try:
            import django

            assert HAS_DJANGO is True
        except ImportError:
            assert HAS_DJANGO is False


class TestPytestConfigure:
    """Test pytest_configure function."""

    def test_pytest_configure_registers_markers(self):
        """Test that pytest_configure registers all expected markers."""
        mock_config = Mock()
        mock_config.option.file_or_dir = []  # Ensure it's iterable
        mock_config.option.plugins = None  # Ensure it's handled properly

        pytest_configure(mock_config)

        # Verify markers were registered
        expected_markers = [
            "pglite: mark test to use PGlite database",
            "pglite_sqlalchemy: mark test to use PGlite with SQLAlchemy",
            "pglite_django: mark test to use PGlite with Django",
            "pglite_pytest_django: mark test to use PGlite with pytest-django",
            "sqlalchemy: SQLAlchemy framework tests",
            "django: Django framework tests",
            "pytest_django: pytest-django specific tests",
            "fixtures: fixture pattern demonstration tests",
            "integration: integration tests",
            "performance: performance benchmark tests",
            "isolation: framework isolation tests",
        ]

        for marker in expected_markers:
            mock_config.addinivalue_line.assert_any_call("markers", marker)

        # Should have called addinivalue_line for each marker
        assert mock_config.addinivalue_line.call_count == len(expected_markers)

    def test_pytest_configure_disables_django_when_should_disable_returns_true(self):
        """Test pytest_configure disables Django plugin when appropriate."""
        mock_config = Mock()
        mock_config.pluginmanager = Mock()

        with patch(
            "py_pglite.pytest_plugin._should_disable_django_plugin",
            return_value=True,
        ):
            pytest_configure(mock_config)

            # Should disable Django debugging and block Django plugin
            assert mock_config.option.django_debug_mode is False
            mock_config.pluginmanager.set_blocked.assert_called_once_with("django")

    def test_pytest_configure_does_not_disable_django_when_should_disable_returns_false(
        self,
    ):
        """Test pytest_configure doesn't disable Django when not needed."""
        mock_config = Mock()

        with patch(
            "py_pglite.pytest_plugin._should_disable_django_plugin",
            return_value=False,
        ):
            pytest_configure(mock_config)

            # Should not attempt to block Django plugin
            assert (
                not hasattr(mock_config, "pluginmanager")
                or not mock_config.pluginmanager.set_blocked.called
            )

    def test_pytest_configure_handles_missing_plugin_manager(self):
        """Test pytest_configure handles missing plugin manager gracefully."""
        mock_config = Mock()
        delattr(mock_config, "pluginmanager")  # Remove pluginmanager attribute

        with patch(
            "py_pglite.pytest_plugin._should_disable_django_plugin",
            return_value=True,
        ):
            # Should not raise exception
            pytest_configure(mock_config)


class TestShouldDisableDjangoPlugin:
    """Test _should_disable_django_plugin function."""

    def test_should_disable_django_plugin_with_sqlalchemy_path(self):
        """Test disabling Django plugin for SQLAlchemy-specific paths."""
        mock_config = Mock()
        mock_config.option.file_or_dir = [
            "tests/sqlalchemy/test_models.py",
            "tests/other.py",
        ]
        mock_config.option.plugins = []  # Ensure it's iterable

        result = _should_disable_django_plugin(mock_config)

        assert result is True

    def test_should_disable_django_plugin_with_mixed_sqlalchemy_django_path(self):
        """Test not disabling Django plugin for mixed paths."""
        mock_config = Mock()
        mock_config.option.file_or_dir = ["tests/sqlalchemy_django/test_integration.py"]
        mock_config.option.plugins = []  # Ensure it's iterable

        result = _should_disable_django_plugin(mock_config)

        assert result is False  # Contains both sqlalchemy AND django

    def test_should_disable_django_plugin_with_explicit_no_django(self):
        """Test disabling Django plugin with explicit -p no:django."""
        mock_config = Mock()
        mock_config.option.file_or_dir = []
        mock_config.option.plugins = ["no:django", "other-plugin"]

        result = _should_disable_django_plugin(mock_config)

        assert result is True

    def test_should_disable_django_plugin_no_sqlalchemy_paths(self):
        """Test not disabling Django plugin for non-SQLAlchemy paths."""
        mock_config = Mock()
        mock_config.option.file_or_dir = [
            "tests/core/test_manager.py",
            "tests/django/test_fixtures.py",
        ]
        mock_config.option.plugins = []  # Ensure it's iterable

        result = _should_disable_django_plugin(mock_config)

        assert result is False

    def test_should_disable_django_plugin_no_plugins_option(self):
        """Test handling missing plugins option."""
        mock_config = Mock()
        mock_config.option.file_or_dir = []
        mock_config.option.plugins = None

        result = _should_disable_django_plugin(mock_config)

        assert result is False

    def test_should_disable_django_plugin_no_file_or_dir(self):
        """Test handling missing file_or_dir option."""
        mock_config = Mock()
        mock_config.option.plugins = []  # Ensure it's iterable
        # Mock config.option without file_or_dir attribute
        mock_option = Mock(spec=[])  # spec=[] means no attributes
        mock_option.plugins = []
        mock_config.option = mock_option

        result = _should_disable_django_plugin(mock_config)

        assert result is False


class TestPytestRuntestSetup:
    """Test pytest_runtest_setup function."""

    def test_pytest_runtest_setup_skips_sqlalchemy_test_without_sqlalchemy(self):
        """Test skipping SQLAlchemy tests when SQLAlchemy unavailable."""
        mock_item = Mock()
        mock_item.name = "test_sqlalchemy_feature"
        mock_item.get_closest_marker.side_effect = (
            lambda x: Mock() if x == "sqlalchemy" else None
        )

        with (
            patch("py_pglite.pytest_plugin.HAS_SQLALCHEMY", False),
            patch("py_pglite.pytest_plugin._is_explicitly_marked", return_value=True),
        ):
            with pytest.raises(
                expected_exception=pytest.skip.Exception,
                match="SQLAlchemy not available",
            ):
                pytest_runtest_setup(mock_item)

    def test_pytest_runtest_setup_skips_django_test_without_django(self):
        """Test skipping Django tests when Django unavailable."""
        mock_item = Mock()
        mock_item.name = "test_django_feature"
        mock_item.get_closest_marker.side_effect = (
            lambda x: Mock() if x == "django" else None
        )

        with (
            patch("py_pglite.pytest_plugin.HAS_DJANGO", False),
            patch("py_pglite.pytest_plugin._is_explicitly_marked", return_value=True),
        ):
            with pytest.raises(
                expected_exception=pytest.skip.Exception,
                match="Django not available",
            ):
                pytest_runtest_setup(mock_item)

    def test_pytest_runtest_setup_skips_pytest_django_test_without_pytest_django(self):
        """Test skipping pytest-django tests when pytest-django unavailable."""
        mock_item = Mock()
        mock_item.name = "test_pytest_django_feature"
        mock_item.get_closest_marker.side_effect = (
            lambda x: Mock() if x == "pytest_django" else None
        )

        with (
            patch("py_pglite.pytest_plugin.HAS_PYTEST_DJANGO", False),
            patch("py_pglite.pytest_plugin._is_explicitly_marked", return_value=True),
        ):
            with pytest.raises(
                pytest.skip.Exception,
                match="pytest-django not available",
            ):
                pytest_runtest_setup(mock_item)

    def test_pytest_runtest_setup_does_not_skip_implicitly_marked_tests(self):
        """Test not skipping implicitly marked tests might work with core fixtures."""
        mock_item = Mock()
        mock_item.name = "test_core_feature"
        mock_item.get_closest_marker.side_effect = (
            lambda x: Mock() if x == "sqlalchemy" else None
        )

        with (
            patch("py_pglite.pytest_plugin.HAS_SQLALCHEMY", False),
            patch(
                "py_pglite.pytest_plugin._is_explicitly_marked",
                return_value=False,
            ),
            patch(
                "py_pglite.pytest_plugin._check_framework_isolation",
            ),
        ):
            # Should not raise skip exception
            pytest_runtest_setup(mock_item)

    def test_pytest_runtest_setup_calls_framework_isolation_check(self):
        """Test that pytest_runtest_setup calls framework isolation check."""
        mock_item = Mock()
        mock_item.get_closest_marker.return_value = None

        with patch("py_pglite.pytest_plugin._check_framework_isolation") as mock_check:
            pytest_runtest_setup(mock_item)

            mock_check.assert_called_once_with(mock_item)


class TestIsExplicitlyMarked:
    """Test _is_explicitly_marked function."""

    def test_is_explicitly_marked_with_sqlalchemy_in_path(self):
        """Test detecting explicit marking with SQLAlchemy in test path."""
        mock_item = Mock()
        mock_item.fspath = "/tests/sqlalchemy/test_models.py"

        result = _is_explicitly_marked(mock_item, {"sqlalchemy"})

        assert result is True

    def test_is_explicitly_marked_with_django_in_path(self):
        """Test detecting explicit marking with Django in test path."""
        mock_item = Mock()
        mock_item.fspath = "/tests/django/test_views.py"

        result = _is_explicitly_marked(mock_item, {"django"})

        assert result is True

    def test_is_explicitly_marked_with_marker_args(self):
        """Test detecting explicit marking with marker arguments."""
        mock_item = Mock()
        mock_item.fspath = "/tests/core/test_generic.py"

        mock_marker = Mock()
        mock_marker.args = ["custom_arg"]
        mock_marker.kwargs = {}
        mock_item.get_closest_marker.return_value = mock_marker

        result = _is_explicitly_marked(mock_item, {"sqlalchemy"})

        assert result is True

    def test_is_explicitly_marked_with_marker_kwargs(self):
        """Test detecting explicit marking with marker keyword arguments."""
        mock_item = Mock()
        mock_item.fspath = "/tests/core/test_generic.py"

        mock_marker = Mock()
        mock_marker.args = []
        mock_marker.kwargs = {"engine": "custom"}
        mock_item.get_closest_marker.return_value = mock_marker

        result = _is_explicitly_marked(mock_item, {"django"})

        assert result is True

    def test_is_explicitly_marked_with_module_pytestmark_list(self):
        """Test detecting explicit marking with module-level pytestmark list."""
        mock_item = Mock()
        mock_item.fspath = "/tests/core/test_generic.py"

        mock_marker = Mock()
        mock_marker.args = []
        mock_marker.kwargs = {}
        mock_item.get_closest_marker.return_value = mock_marker

        # Mock module with pytestmark list
        mock_module = Mock()
        mock_mark = Mock()
        mock_mark.name = "sqlalchemy"
        mock_module.pytestmark = [mock_mark]
        mock_item.module = mock_module

        result = _is_explicitly_marked(mock_item, {"sqlalchemy"})

        assert result is True

    def test_is_explicitly_marked_with_module_pytestmark_single(self):
        """Test detecting explicit marking with single module-level pytestmark."""
        mock_item = Mock()
        mock_item.fspath = "/tests/core/test_generic.py"

        mock_marker = Mock()
        mock_marker.args = []
        mock_marker.kwargs = {}
        mock_item.get_closest_marker.return_value = mock_marker

        # Mock module with single pytestmark
        mock_module = Mock()
        mock_pytestmark = Mock()
        mock_pytestmark.name = "django"
        mock_module.pytestmark = mock_pytestmark
        mock_item.module = mock_module

        result = _is_explicitly_marked(mock_item, {"django"})

        assert result is True

    def test_is_explicitly_marked_not_explicit(self):
        """Test detecting non-explicit marking."""
        mock_item = Mock()
        mock_item.fspath = "/tests/core/test_generic.py"

        mock_marker = Mock()
        mock_marker.args = []
        mock_marker.kwargs = {}
        mock_item.get_closest_marker.return_value = mock_marker
        mock_item.module = None

        result = _is_explicitly_marked(mock_item, {"sqlalchemy"})

        assert result is False

    def test_is_explicitly_marked_handles_attribute_error(self):
        """Test handling AttributeError when accessing module attributes."""
        mock_item = Mock()
        mock_item.fspath = "/tests/core/test_generic.py"

        mock_marker = Mock()
        mock_marker.args = []
        mock_marker.kwargs = {}
        mock_item.get_closest_marker.return_value = mock_marker

        # Mock module that raises AttributeError
        mock_module = Mock()
        del mock_module.pytestmark  # Ensure attribute doesn't exist
        mock_item.module = mock_module

        result = _is_explicitly_marked(mock_item, {"sqlalchemy"})

        assert result is False


class TestCheckFrameworkIsolation:
    """Test _check_framework_isolation function."""

    def test_check_framework_isolation_warns_for_mixed_fixtures(self):
        """Test warning for mixed SQLAlchemy and Django fixtures."""
        mock_item = Mock()
        mock_item.fixturenames = ["pglite_engine", "django_pglite_db", "other_fixture"]

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _check_framework_isolation(mock_item)

            assert len(w) == 1
            assert "Mixed framework fixtures detected" in str(w[0].message)

    def test_check_framework_isolation_no_warning_for_sqlalchemy_only(self):
        """Test no warning for SQLAlchemy-only fixtures."""
        mock_item = Mock()
        mock_item.fixturenames = ["pglite_engine", "pglite_session"]

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _check_framework_isolation(mock_item)

            assert len(w) == 0

    def test_check_framework_isolation_no_warning_for_django_only(self):
        """Test no warning for Django-only fixtures."""
        mock_item = Mock()
        mock_item.fixturenames = ["django_pglite_db", "db"]

        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _check_framework_isolation(mock_item)

            assert len(w) == 0

    def test_check_framework_isolation_handles_missing_fixturenames(self):
        """Test handling missing fixturenames attribute."""
        mock_item = Mock()
        delattr(mock_item, "fixturenames")

        # Should not raise exception
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            _check_framework_isolation(mock_item)

            assert len(w) == 0


class TestPytestCollectionModifyitems:
    """Test pytest_collection_modifyitems function."""

    def test_pytest_collection_modifyitems_calls_auto_mark_for_each_item(self):
        """Test that pytest_collection_modifyitems calls auto-mark for each item."""
        mock_config = Mock()
        mock_items = [Mock(), Mock(), Mock()]

        with patch("py_pglite.pytest_plugin._auto_mark_test") as mock_auto_mark:
            pytest_collection_modifyitems(mock_config, mock_items)  # type: ignore

            assert mock_auto_mark.call_count == 3
            for item in mock_items:
                mock_auto_mark.assert_any_call(item)


class TestAutoMarkTest:
    """Test _auto_mark_test function."""

    def test_auto_mark_test_marks_sqlalchemy_fixtures(self):
        """Test auto-marking tests with SQLAlchemy fixtures."""
        mock_item = Mock()
        mock_item.fixturenames = ["pglite_engine", "pglite_session", "other_fixture"]
        mock_item.add_marker = Mock()

        _auto_mark_test(mock_item)

        # Should add SQLAlchemy markers
        mock_item.add_marker.assert_any_call(pytest.mark.sqlalchemy)
        mock_item.add_marker.assert_any_call(pytest.mark.pglite_sqlalchemy)

    def test_auto_mark_test_marks_django_fixtures(self):
        """Test auto-marking tests with Django fixtures."""
        mock_item = Mock()
        mock_item.fixturenames = ["django_pglite_db", "django_client"]
        mock_item.add_marker = Mock()

        _auto_mark_test(mock_item)

        # Should add Django markers
        mock_item.add_marker.assert_any_call(pytest.mark.django)
        mock_item.add_marker.assert_any_call(pytest.mark.pglite_django)

    def test_auto_mark_test_marks_pytest_django_fixtures(self):
        """Test auto-marking tests with pytest-django fixtures."""
        mock_item = Mock()
        mock_item.fixturenames = ["db", "transactional_db"]
        mock_item.add_marker = Mock()

        _auto_mark_test(mock_item)

        # Should add pytest-django markers
        mock_item.add_marker.assert_any_call(pytest.mark.pytest_django)
        mock_item.add_marker.assert_any_call(pytest.mark.pglite_pytest_django)

    def test_auto_mark_test_marks_based_on_path_patterns(self):
        """Test auto-marking tests based on file path patterns."""
        mock_item = Mock()
        mock_item.fixturenames = []
        mock_item.add_marker = Mock()

        # Test fixtures pattern
        mock_item.fspath = "/tests/fixtures/test_showcase.py"
        _auto_mark_test(mock_item)
        mock_item.add_marker.assert_any_call(pytest.mark.fixtures)

        # Reset mock
        mock_item.add_marker.reset_mock()

        # Test performance pattern
        mock_item.fspath = "/tests/performance/test_benchmarks.py"
        _auto_mark_test(mock_item)
        mock_item.add_marker.assert_any_call(pytest.mark.performance)

        # Reset mock
        mock_item.add_marker.reset_mock()

        # Test integration pattern
        mock_item.fspath = "/tests/integration/test_full_stack.py"
        _auto_mark_test(mock_item)
        mock_item.add_marker.assert_any_call(pytest.mark.integration)

    def test_auto_mark_test_handles_missing_fixturenames(self):
        """Test auto-marking handles missing fixturenames attribute."""
        mock_item = Mock()
        delattr(mock_item, "fixturenames")
        mock_item.fspath = "/tests/core/test_basic.py"

        # Should not raise exception
        _auto_mark_test(mock_item)


class TestPytestTerminalSummary:
    """Test pytest_terminal_summary function."""

    def test_pytest_terminal_summary_shows_tips_on_failure(self):
        """Test terminal summary shows isolation tips on test failure."""
        mock_terminalreporter = Mock()
        mock_config = Mock()

        # Test with non-zero exit status (failure)
        pytest_terminal_summary(mock_terminalreporter, 1, mock_config)

        # Should write framework isolation tips
        mock_terminalreporter.write_sep.assert_called_once_with(
            "=",
            "🚀 py-pglite Framework Isolation Tips",
        )
        mock_terminalreporter.write_line.assert_called_once()

        # Verify the content contains useful isolation tips
        written_content = mock_terminalreporter.write_line.call_args[0][0]
        assert "pytest -m sqlalchemy -p no:django" in written_content
        assert "pytest -m django" in written_content
        assert "pytest.ini" in written_content

    def test_pytest_terminal_summary_no_tips_on_success(self):
        """Test terminal summary doesn't show tips on test success."""
        mock_terminalreporter = Mock()
        mock_config = Mock()

        # Test with zero exit status (success)
        pytest_terminal_summary(mock_terminalreporter, 0, mock_config)

        # Should not write framework isolation tips
        mock_terminalreporter.write_sep.assert_not_called()
        mock_terminalreporter.write_line.assert_not_called()


class TestPluginIntegration:
    """Test overall plugin integration and edge cases."""

    def test_all_exported_functions_exist(self):
        """Test that all expected functions are exported in __all__."""
        expected_functions = [
            "pytest_configure",
            "pytest_runtest_setup",
            "pytest_collection_modifyitems",
            "pytest_terminal_summary",
        ]

        from py_pglite.pytest_plugin import __all__

        for func_name in expected_functions:
            assert func_name in __all__
