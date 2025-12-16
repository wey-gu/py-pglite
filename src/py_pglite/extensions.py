"""Extension management for py-pglite.

This module provides a registry of supported PGlite extensions and the
necessary JavaScript import details for each.
"""

SUPPORTED_EXTENSIONS: dict[str, dict[str, str]] = {
    "pgvector": {"module": "@electric-sql/pglite/vector", "name": "vector"},
    # "pg_uuidv7": {
    #     "module": "@electric-sql/pglite/pg_uuidv7",
    #     "name": "pg_uuidv7",
    # },
    # "pg_ivm": {"module": "@electric-sql/pglite/pg_ivm", "name": "pg_ivm"},
    # "pgtap": {"module": "@electric-sql/pglite/pgtap", "name": "pgtap"},
    "amcheck": {
        "module": "@electric-sql/pglite/contrib/amcheck",
        "name": "amcheck",
    },
    # "auto_explain": {
    #     "module": "@electric-sql/pglite/contrib/auto_explain",
    #     "name": "auto_explain",
    # },
    "bloom": {"module": "@electric-sql/pglite/contrib/bloom", "name": "bloom"},
    "btree_gin": {
        "module": "@electric-sql/pglite/contrib/btree_gin",
        "name": "btree_gin",
    },
    "btree_gist": {
        "module": "@electric-sql/pglite/contrib/btree_gist",
        "name": "btree_gist",
    },
    "citext": {
        "module": "@electric-sql/pglite/contrib/citext",
        "name": "citext",
    },
    "cube": {"module": "@electric-sql/pglite/contrib/cube", "name": "cube"},
    # "dict_int": {
    #     "module": "@electric-sql/pglite/contrib/dict_int",
    #     "name": "dict_int",
    # },
    # "dict_xsyn": {
    #     "module": "@electric-sql/pglite/contrib/dict_xsyn",
    #     "name": "dict_xsyn",
    # },
    "earthdistance": {
        "module": "@electric-sql/pglite/contrib/earthdistance",
        "name": "earthdistance",
    },
    # "file_fdw": {
    #     "module": "@electric-sql/pglite/contrib/file_fdw",
    #     "name": "file_fdw",
    # },
    "fuzzystrmatch": {
        "module": "@electric-sql/pglite/contrib/fuzzystrmatch",
        "name": "fuzzystrmatch",
    },
    "hstore": {
        "module": "@electric-sql/pglite/contrib/hstore",
        "name": "hstore",
    },
    # "intarray": {
    #     "module": "@electric-sql/pglite/contrib/intarray",
    #     "name": "intarray",
    # },
    "isn": {"module": "@electric-sql/pglite/contrib/isn", "name": "isn"},
    "lo": {"module": "@electric-sql/pglite/contrib/lo", "name": "lo"},
    "ltree": {"module": "@electric-sql/pglite/contrib/ltree", "name": "ltree"},
    # "pageinspect": {
    #     "module": "@electric-sql/pglite/contrib/pageinspect",
    #     "name": "pageinspect",
    # },
    # "pg_buffercache": {
    #     "module": "@electric-sql/pglite/contrib/pg_buffercache",
    #     "name": "pg_buffercache",
    # },
    # "pg_freespacemap": {
    #     "module": "@electric-sql/pglite/contrib/pg_freespacemap",
    #     "name": "pg_freespacemap",
    # },
    # "pg_surgery": {
    #     "module": "@electric-sql/pglite/contrib/pg_surgery",
    #     "name": "pg_surgery",
    # },
    "pg_trgm": {
        "module": "@electric-sql/pglite/contrib/pg_trgm",
        "name": "pg_trgm",
    },
    # "pg_visibility": {
    #     "module": "@electric-sql/pglite/contrib/pg_visibility",
    #     "name": "pg_visibility",
    # },
    # "pg_walinspect": {
    #     "module": "@electric-sql/pglite/contrib/pg_walinspect",
    #     "name": "pg_walinspect",
    # },
    "seg": {"module": "@electric-sql/pglite/contrib/seg", "name": "seg"},
    "tablefunc": {
        "module": "@electric-sql/pglite/contrib/tablefunc",
        "name": "tablefunc",
    },
    "tcn": {"module": "@electric-sql/pglite/contrib/tcn", "name": "tcn"},
    "tsm_system_rows": {
        "module": "@electric-sql/pglite/contrib/tsm_system_rows",
        "name": "tsm_system_rows",
    },
    "tsm_system_time": {
        "module": "@electric-sql/pglite/contrib/tsm_system_time",
        "name": "tsm_system_time",
    },
    # "unaccent": {
    #     "module": "@electric-sql/pglite/contrib/unaccent",
    #     "name": "unaccent",
    # },
    "uuid_ossp": {
        "module": "@electric-sql/pglite/contrib/uuid_ossp",
        "name": "uuid_ossp",
    },
}
