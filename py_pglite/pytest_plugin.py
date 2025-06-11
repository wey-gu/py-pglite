"""Pytest plugin for py-pglite.

Provides automatic fixture discovery and perfect isolation between frameworks,
delivering a Vite-like developer experience for database testing.
"""

import warnings

import pytest

# Framework availability detection
HAS_SQLALCHEMY = False
HAS_DJANGO = False
HAS_PYTEST_DJANGO = False

try:
    import sqlalchemy  # noqa: F401

    HAS_SQLALCHEMY = True
except ImportError:
    pass

try:
    import django  # noqa: F401

    HAS_DJANGO = True
except ImportError:
    pass

try:
    import pytest_django  # noqa: F401

    HAS_PYTEST_DJANGO = True
except ImportError:
    pass


def pytest_configure(config: pytest.Config) -> None:
    """Configure pytest with world-class py-pglite integration."""
    # Register comprehensive markers for elegant test organization
    markers = [
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

    for marker in markers:
        config.addinivalue_line("markers", marker)

    # Smart isolation: Disable Django plugin for pure SQLAlchemy directories
    if _should_disable_django_plugin(config):
        config.option.django_debug_mode = False
        # Prevent Django plugin interference
        if hasattr(config, "pluginmanager"):
            config.pluginmanager.set_blocked("django")


def _should_disable_django_plugin(config: pytest.Config) -> bool:
    """Determine if Django plugin should be disabled for better isolation."""
    # Check if we're running pure SQLAlchemy tests
    test_paths = getattr(config.option, "file_or_dir", [])
    if any(
        "sqlalchemy" in str(path) and "django" not in str(path) for path in test_paths
    ):
        return True

    # Check for explicit -p no:django
    if hasattr(config.option, "plugins") and config.option.plugins:
        if "no:django" in config.option.plugins:
            return True

    return False


# Core fixtures (always available)
from .fixtures import (  # noqa: F401
    pglite_manager,
    pglite_manager_custom,
)

# Smart fixture loading with perfect isolation
if HAS_SQLALCHEMY:
    try:
        from .sqlalchemy.fixtures import (  # noqa: F401
            pglite_config,
            pglite_engine,
            pglite_session,
            pglite_sqlalchemy_engine,
            pglite_sqlalchemy_session,
        )
    except ImportError:
        pass

if HAS_DJANGO:
    try:
        from .django.fixtures import (  # noqa: F401
            db,
            django_admin_user,
            django_client,
            django_pglite_db,
            django_pglite_settings,
            django_pglite_transactional_db,
            django_user_model,
            pglite_django_manager,
            transactional_db,
        )
    except ImportError:
        pass


def pytest_runtest_setup(item: pytest.Item) -> None:
    """Setup each test with perfect framework isolation."""
    # Check for missing dependencies with helpful messages
    if item.get_closest_marker("pglite_sqlalchemy") and not HAS_SQLALCHEMY:
        pytest.skip(
            "🚫 SQLAlchemy not available.\n"
            "Install with: pip install 'py-pglite[sqlalchemy]'"
        )

    if item.get_closest_marker("pglite_django") and not HAS_DJANGO:
        pytest.skip(
            "🚫 Django not available. Install with: pip install py-pglite[django]"
        )

    # Only check for pytest-django if the test is explicitly marked to use it
    if item.get_closest_marker("pytest_django") and not HAS_PYTEST_DJANGO:
        pytest.skip(
            "🚫 pytest-django not available. Install with: pip install pytest-django"
        )

    # Framework isolation warnings for better DX
    _check_framework_isolation(item)


def _check_framework_isolation(item: pytest.Item) -> None:
    """Check and warn about potential framework isolation issues."""
    fixture_names = getattr(item, "fixturenames", [])

    # Detect mixed framework usage (potential conflicts)
    sqlalchemy_fixtures = {
        "pglite_engine",
        "pglite_session",
        "pglite_sqlalchemy_session",
    }
    django_fixtures = {
        "django_pglite_db",
        "django_pglite_transactional_db",
        "db",
        "transactional_db",
    }

    uses_sqlalchemy = any(f in fixture_names for f in sqlalchemy_fixtures)
    uses_django = any(f in fixture_names for f in django_fixtures)

    if uses_sqlalchemy and uses_django:
        warnings.warn(
            "⚠️  Mixed framework fixtures detected.\n"
            "Consider running frameworks separately:\n"
            " • pytest -m sqlalchemy -p no:django  (pure SQLAlchemy)\n"
            " • pytest -m django                   (pure Django)\n"
            " • See pytest.ini for more patterns",
            UserWarning,
            stacklevel=2,
        )


def pytest_collection_modifyitems(
    config: pytest.Config, items: list[pytest.Item]
) -> None:
    """Auto-mark tests based on fixture usage for elegant organization."""
    for item in items:
        _auto_mark_test(item)


def _auto_mark_test(item: pytest.Item) -> None:
    """Auto-mark tests based on their fixture usage."""
    fixture_names = set(getattr(item, "fixturenames", []))

    # SQLAlchemy framework detection
    sqlalchemy_fixtures = {
        "pglite_engine",
        "pglite_session",
        "pglite_sqlalchemy_session",
        "pglite_sqlalchemy_engine",
        "pglite_config",
        "pglite_manager",
    }
    if fixture_names & sqlalchemy_fixtures:
        item.add_marker(pytest.mark.sqlalchemy)
        item.add_marker(pytest.mark.pglite_sqlalchemy)

    # Django framework detection
    django_fixtures = {
        "django_pglite_db",
        "django_pglite_transactional_db",
        "django_client",
        "django_user_model",
        "django_admin_user",
        "pglite_django_manager",
    }
    if fixture_names & django_fixtures:
        item.add_marker(pytest.mark.django)
        item.add_marker(pytest.mark.pglite_django)

    # pytest-django specific detection
    pytest_django_fixtures = {"db", "transactional_db"}
    if fixture_names & pytest_django_fixtures:
        item.add_marker(pytest.mark.pytest_django)
        item.add_marker(pytest.mark.pglite_pytest_django)

    # Test pattern detection
    test_path = str(item.fspath)
    if "fixtures" in test_path or "showcase" in test_path:
        item.add_marker(pytest.mark.fixtures)

    if "performance" in test_path or "benchmark" in test_path:
        item.add_marker(pytest.mark.performance)

    if "integration" in test_path:
        item.add_marker(pytest.mark.integration)


def pytest_terminal_summary(terminalreporter, exitstatus, config):
    """Provide helpful summary with framework isolation tips."""
    if exitstatus != 0:
        terminalreporter.write_sep("=", "🚀 py-pglite Framework Isolation Tips")
        terminalreporter.write_line(
            "For perfect framework isolation, try these patterns:\n"
            "  pytest -m sqlalchemy -p no:django     # Pure SQLAlchemy tests\n"
            "  pytest -m django                      # Pure Django tests\n"
            "  pytest testing-patterns/sqlalchemy/   # Directory isolation\n"
            "  pytest testing-patterns/django/       # Directory isolation\n"
            "\nSee pytest.ini for more elegant patterns! ✨"
        )


# Make plugin discoverable
__all__ = [
    "pytest_configure",
    "pytest_runtest_setup",
    "pytest_collection_modifyitems",
    "pytest_terminal_summary",
]
