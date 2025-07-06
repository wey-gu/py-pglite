"""Django integration for py-pglite.

This module provides Django-specific fixtures and utilities for py-pglite.
"""

# Import fixtures and utilities
from py_pglite.django.fixtures import db
from py_pglite.django.fixtures import django_pglite_db
from py_pglite.django.fixtures import django_pglite_transactional_db
from py_pglite.django.fixtures import transactional_db
from py_pglite.django.utils import configure_django_for_pglite
from py_pglite.django.utils import create_django_superuser


__all__ = [
    "configure_django_for_pglite",
    "create_django_superuser",
    "db",
    "django_pglite_db",
    "django_pglite_transactional_db",
    "transactional_db",
]
