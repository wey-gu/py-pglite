"""Django integration for py-pglite.

This module provides Django-specific fixtures and utilities for py-pglite.
"""

# Import fixtures and utilities
from .fixtures import (
    db,
    django_pglite_db,
    django_pglite_transactional_db,
    transactional_db,
)
from .utils import (
    configure_django_for_pglite,
    create_django_superuser,
)

__all__ = [
    "django_pglite_db",
    "django_pglite_transactional_db",
    "db",
    "transactional_db",
    "configure_django_for_pglite",
    "create_django_superuser",
]
