"""Extension management for py-pglite.

This module provides a registry of supported PGlite extensions and the
necessary JavaScript import details for each.
"""

SUPPORTED_EXTENSIONS: dict[str, dict[str, str]] = {
    "pgvector": {"module": "@electric-sql/pglite/vector", "name": "vector"},
    "pg_trgm": {"module": "@electric-sql/pglite/contrib/pg_trgm", "name": "pg_trgm"},
    "btree_gin": {
        "module": "@electric-sql/pglite/contrib/btree_gin",
        "name": "btree_gin",
    },
    "btree_gist": {
        "module": "@electric-sql/pglite/contrib/btree_gist",
        "name": "btree_gist",
    },
    "fuzzystrmatch": {
        "module": "@electric-sql/pglite/contrib/fuzzystrmatch",
        "name": "fuzzystrmatch",
    },
}
