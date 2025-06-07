"""
Django Testing Configuration for py-pglite
==========================================

Provides fixtures and configuration for both:
• Django ORM testing patterns
• pytest-django specific patterns

Shows proper abstraction for different testing approaches.
"""

import django
import pytest
from django.conf import settings

from py_pglite import PGliteConfig, PGliteManager


@pytest.fixture(scope="function")
def pglite_manager():
    """
    🎯 Base PGlite manager fixture

    Provides fresh PGlite instance for each test.
    Used by both Django and pytest-django patterns.
    """
    manager = PGliteManager(PGliteConfig())
    manager.start()

    try:
        yield manager
    finally:
        manager.stop()


@pytest.fixture(autouse=True)
def setup_django_mail():
    """
    🎯 Ensure Django mail outbox for pytest-django

    This autouse fixture ensures mail.outbox is always available
    for pytest-django compatibility.
    """
    try:
        from django.core import mail

        if not hasattr(mail, "outbox"):
            mail.outbox = []
        else:
            mail.outbox.clear()
    except ImportError:
        pass  # Django not configured yet


@pytest.fixture(scope="function")
def configured_django(pglite_manager):
    """
    🎯 Configured Django environment

    Provides Django setup for both Django ORM and pytest-django testing.
    This is the main abstraction point for Django + py-pglite.
    """
    # Get connection details from PGlite
    conn_str = pglite_manager.config.get_connection_string()
    socket_dir = conn_str.split("host=")[1].split("&")[0].split("#")[0]

    # Configure Django if not already configured
    if not settings.configured:
        settings.configure(
            DATABASES={
                "default": {
                    "ENGINE": "django.db.backends.postgresql",
                    "NAME": "postgres",
                    "USER": "postgres",
                    "PASSWORD": "postgres",
                    "HOST": socket_dir,
                    "PORT": "",
                    "OPTIONS": {"connect_timeout": 10},
                }
            },
            INSTALLED_APPS=[
                "django.contrib.contenttypes",
                "django.contrib.auth",
            ],
            USE_TZ=False,  # Avoid timezone conflicts
            SECRET_KEY="django-pglite-testing",
            # pytest-django compatibility
            EMAIL_BACKEND="django.core.mail.backends.locmem.EmailBackend",
        )
        django.setup()

        # Initialize mail outbox for pytest-django
        from django.core import mail

        if not hasattr(mail, "outbox"):
            mail.outbox = []
    else:
        # Update existing configuration with new PGlite connection
        settings.DATABASES["default"]["HOST"] = socket_dir

        # Reset connections to use new database
        from django.db import connections

        connections.close_all()

    yield


@pytest.fixture
def django_user_model(configured_django):
    """
    🎯 Django User model fixture

    Example of providing Django model fixtures.
    Shows how to abstract common Django testing patterns.
    """
    from django.contrib.auth.models import User

    return User
