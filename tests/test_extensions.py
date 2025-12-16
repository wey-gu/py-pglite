"""Tests for PGlite extensions."""

from typing import TYPE_CHECKING

import psycopg
import pytest

from py_pglite import PGliteManager
from py_pglite.config import PGliteConfig


if TYPE_CHECKING:
    import numpy as np

    from pgvector.psycopg import register_vector

# Mark all tests in this module as 'extensions'
pytestmark = pytest.mark.extensions

# Try to import optional dependencies, or skip tests
try:
    import numpy as np  # type: ignore[import-untyped]

    from pgvector.psycopg import register_vector  # type: ignore[import-untyped]
except ImportError:
    np = None
    register_vector = None


@pytest.mark.skipif(not np, reason="numpy and/or pgvector not available")
def test_pgvector_extension():
    """Test the pgvector extension for vector similarity search."""
    assert np, "numpy is not available"
    assert register_vector, "pgvector is not available"

    # 1. Configure PGlite to use the pgvector extension
    config = PGliteConfig(extensions=["pgvector"])

    with PGliteManager(config=config) as db:
        # 2. Connect using a standard psycopg connection
        conn_string = db.get_dsn()
        with psycopg.connect(conn_string, autocommit=True) as conn:
            # 3. Enable the vector extension in the database FIRST
            conn.execute("CREATE EXTENSION IF NOT EXISTS vector")

            # 4. THEN register the vector type with the connection
            assert register_vector is not None
            register_vector(conn)

            # 5. Create a table with a vector column
            conn.execute("CREATE TABLE items (embedding vector(3))")

            # 6. Insert vector data
            embedding = np.array([1, 2, 3])
            neighbor = np.array([1, 2, 4])
            far_away = np.array([5, 6, 7])
            conn.execute(
                "INSERT INTO items (embedding) VALUES (%s), (%s), (%s)",
                (embedding, neighbor, far_away),
            )

            # 7. Perform a vector similarity search (L2 distance)
            result = conn.execute(
                "SELECT * FROM items ORDER BY embedding <-> %s LIMIT 1", (embedding,)
            ).fetchone()

            # 8. Assert that the closest vector is the original embedding itself
            assert result is not None
            retrieved_embedding = result[0]
            assert np.array_equal(retrieved_embedding, embedding)

            # 9. Find the nearest neighbor
            result = conn.execute(
                "SELECT * FROM items ORDER BY embedding <-> %s LIMIT 2", (embedding,)
            ).fetchall()

            assert len(result) == 2
            nearest_neighbor = result[1][0]
            assert np.array_equal(nearest_neighbor, neighbor)


def test_pg_trgm_extension():
    """Test the pg_trgm extension for trigram similarity search."""
    config = PGliteConfig(extensions=["pg_trgm"])
    with PGliteManager(config=config) as db:
        with psycopg.connect(db.get_dsn(), autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS pg_trgm")
            conn.execute("SELECT word_similarity('word', 'two words')")


def test_btree_gin_extension():
    """Test the btree_gin extension for gin index."""
    config = PGliteConfig(extensions=["btree_gin"])
    with PGliteManager(config=config) as db:
        with psycopg.connect(db.get_dsn(), autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS btree_gin")
            # TODO: Test btree_gin extension functionality


def test_btree_gist_extension():
    """Test the btree_gist extension for gist index."""
    config = PGliteConfig(extensions=["btree_gist"])
    with PGliteManager(config=config) as db:
        with psycopg.connect(db.get_dsn(), autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS btree_gist")
            # TODO: Test btree_gist extension functionality


def test_fuzzystrmatch_extension():
    """Test the fuzzystrmatch extension for fuzzy string matching."""
    config = PGliteConfig(extensions=["fuzzystrmatch"])
    with PGliteManager(config=config) as db:
        with psycopg.connect(db.get_dsn(), autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS fuzzystrmatch")
            conn.execute("SELECT soundex('hello world!')")


def test_uuid_ossp_extension():
    """Test the uuid_ossp extension for UUID generation."""
    config = PGliteConfig(extensions=["uuid_ossp"])
    with PGliteManager(config=config) as db:
        with psycopg.connect(db.get_dsn(), autocommit=True) as conn:
            conn.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')
            conn.execute("SELECT uuid_generate_v4()")


@pytest.mark.skip(reason="currently not working")
def test_pg_uuidv7_extension():
    """Test the pg_uuidv7 extension for UUID generation."""
    config = PGliteConfig(extensions=["pg_uuidv7"])
    with PGliteManager(config=config) as db:
        with psycopg.connect(db.get_dsn(), autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS pg_uuidv7")
            conn.execute("SELECT uuid_generate_v7()")


def test_tablefunc_extension():
    """Test the tablefunc extension for table functions."""
    config = PGliteConfig(extensions=["tablefunc"])
    with PGliteManager(config=config) as db:
        with psycopg.connect(db.get_dsn(), autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS tablefunc")
            conn.execute("SELECT * FROM normal_rand(1000, 5, 3)")


def test_tcn_extension():
    """Test the tcn extension for tcn functions."""
    config = PGliteConfig(extensions=["tcn"])
    with PGliteManager(config=config) as db:
        with psycopg.connect(db.get_dsn(), autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS tcn")
            # TODO: Test tcn extension functionality


def test_amcheck_extension():
    """Test the amcheck extension for relation consistency checks."""
    config = PGliteConfig(extensions=["amcheck"])
    with PGliteManager(config=config) as db:
        with psycopg.connect(db.get_dsn(), autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS amcheck")
            # TODO: Test amcheck extension functionality


@pytest.mark.skip(reason="currently not working")
def test_auto_explain_extension():
    """Test the auto_explain extension for automatic query plan logging."""
    config = PGliteConfig(extensions=["auto_explain"])
    with PGliteManager(config=config) as db:
        with psycopg.connect(db.get_dsn(), autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS auto_explain")
            # TODO: Test auto_explain extension functionality


def test_bloom_extension():
    """Test the bloom extension for bloom filter indexes."""
    config = PGliteConfig(extensions=["bloom"])
    with PGliteManager(config=config) as db:
        with psycopg.connect(db.get_dsn(), autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS bloom")
            # TODO: Test bloom extension functionality


def test_citext_extension():
    """Test the citext extension for case-insensitive text."""
    config = PGliteConfig(extensions=["citext"])
    with PGliteManager(config=config) as db:
        with psycopg.connect(db.get_dsn(), autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS citext")
            conn.execute("CREATE TABLE test_citext (name citext)")
            conn.execute("INSERT INTO test_citext VALUES ('Hello')")
            result = conn.execute(
                "SELECT * FROM test_citext WHERE name = 'HELLO'"
            ).fetchone()
            assert result is not None


def test_cube_extension():
    """Test the cube extension for multidimensional cubes."""
    config = PGliteConfig(extensions=["cube"])
    with PGliteManager(config=config) as db:
        with psycopg.connect(db.get_dsn(), autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS cube")
            conn.execute("SELECT cube('(1,2,3)')")
            # TODO: Test cube extension functionality more thoroughly


@pytest.mark.skip(reason="currently not working")
def test_dict_int_extension():
    """Test the dict_int extension for integer dictionary."""
    config = PGliteConfig(extensions=["dict_int"])
    with PGliteManager(config=config) as db:
        with psycopg.connect(db.get_dsn(), autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS 'dict_int")
            # TODO: Test dict_int extension functionality


@pytest.mark.skip(reason="currently not working")
def test_dict_xsyn_extension():
    """Test the dict_xsyn extension for extended synonym dictionary."""
    config = PGliteConfig(extensions=["dict_xsyn"])
    with PGliteManager(config=config) as db:
        with psycopg.connect(db.get_dsn(), autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS dict_xsyn")
            # TODO: Test dict_xsyn extension functionality


def test_earthdistance_extension():
    """Test the earthdistance extension for great circle distance."""
    config = PGliteConfig(extensions=["cube", "earthdistance"])
    with PGliteManager(config=config) as db:
        with psycopg.connect(db.get_dsn(), autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS cube")
            conn.execute("CREATE EXTENSION IF NOT EXISTS earthdistance")
            conn.execute(
                "SELECT earth_distance(ll_to_earth(51.5074, -0.1278), ll_to_earth(48.8566, 2.3522)) AS distance_meters"
            )


@pytest.mark.skip(reason="currently not working")
def test_file_fdw_extension():
    """Test the file_fdw extension for foreign data wrapper."""
    config = PGliteConfig(extensions=["file_fdw"])
    with PGliteManager(config=config) as db:
        with psycopg.connect(db.get_dsn(), autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS file_fdw")
            # TODO: Test file_fdw extension functionality


def test_hstore_extension():
    """Test the hstore extension for key-value pairs."""
    config = PGliteConfig(extensions=["hstore"])
    with PGliteManager(config=config) as db:
        with psycopg.connect(db.get_dsn(), autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS hstore")
            conn.execute("SELECT 'a=>1, b=>2'::hstore")


@pytest.mark.skip(reason="currently not working")
def test_intarray_extension():
    """Test the intarray extension for integer array operations."""
    config = PGliteConfig(extensions=["intarray"])
    with PGliteManager(config=config) as db:
        with psycopg.connect(db.get_dsn(), autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS intarray")
            # TODO: Test intarray extension functionality


def test_isn_extension():
    """Test the isn extension for product number types."""
    config = PGliteConfig(extensions=["isn"])
    with PGliteManager(config=config) as db:
        with psycopg.connect(db.get_dsn(), autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS isn")
            # TODO: Test isn extension functionality


def test_lo_extension():
    """Test the lo extension for large objects."""
    config = PGliteConfig(extensions=["lo"])
    with PGliteManager(config=config) as db:
        with psycopg.connect(db.get_dsn(), autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS lo")
            # TODO: Test lo extension functionality


def test_ltree_extension():
    """Test the ltree extension for tree-like data structures."""
    config = PGliteConfig(extensions=["ltree"])
    with PGliteManager(config=config) as db:
        with psycopg.connect(db.get_dsn(), autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS ltree")
            # TODO: Test ltree extension functionality


@pytest.mark.skip(reason="currently not working")
def test_pageinspect_extension():
    """Test the pageinspect extension for low-level page inspection."""
    config = PGliteConfig(extensions=["pageinspect"])
    with PGliteManager(config=config) as db:
        with psycopg.connect(db.get_dsn(), autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS pageinspect")
            # TODO: Test pageinspect extension functionality


@pytest.mark.skip(reason="currently not working")
def test_pg_buffercache_extension():
    """Test the pg_buffercache extension for buffer cache inspection."""
    config = PGliteConfig(extensions=["pg_buffercache"])
    with PGliteManager(config=config) as db:
        with psycopg.connect(db.get_dsn(), autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS pg_buffercache")
            # TODO: Test pg_buffercache extension functionality


@pytest.mark.skip(reason="currently not working")
def test_pg_freespacemap_extension():
    """Test the pg_freespacemap extension for free space map inspection."""
    config = PGliteConfig(extensions=["pg_freespacemap"])
    with PGliteManager(config=config) as db:
        with psycopg.connect(db.get_dsn(), autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS pg_freespacemap")
            # TODO: Test pg_freespacemap extension functionality


@pytest.mark.skip(reason="currently not working")
def test_pg_ivm_extension():
    """Test the pg_ivm extension for incremental view maintenance."""
    config = PGliteConfig(extensions=["pg_ivm"])
    with PGliteManager(config=config) as db:
        with psycopg.connect(db.get_dsn(), autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS pg_ivm")
            # TODO: Test pg_ivm extension functionality


@pytest.mark.skip(reason="currently not working")
def test_pg_surgery_extension():
    """Test the pg_surgery extension for relation surgery functions."""
    config = PGliteConfig(extensions=["pg_surgery"])
    with PGliteManager(config=config) as db:
        with psycopg.connect(db.get_dsn(), autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS pg_surgery")
            # TODO: Test pg_surgery extension functionality


@pytest.mark.skip(reason="currently not working")
def test_pg_visibility_extension():
    """Test the pg_visibility extension for visibility map inspection."""
    config = PGliteConfig(extensions=["pg_visibility"])
    with PGliteManager(config=config) as db:
        with psycopg.connect(db.get_dsn(), autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS pg_visibility")
            # TODO: Test pg_visibility extension functionality


@pytest.mark.skip(reason="currently not working")
def test_pg_walinspect_extension():
    """Test the pg_walinspect extension for WAL inspection."""
    config = PGliteConfig(extensions=["pg_walinspect"])
    with PGliteManager(config=config) as db:
        with psycopg.connect(db.get_dsn(), autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS pg_walinspect")
            # TODO: Test pg_walinspect extension functionality


@pytest.mark.skip(reason="currently not working")
def test_pgtap_extension():
    """Test the pgtap extension for TAP-emitting unit tests."""
    config = PGliteConfig(extensions=["pgtap"])
    with PGliteManager(config=config) as db:
        with psycopg.connect(db.get_dsn(), autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS pgtap")
            # TODO: Test pgtap extension functionality


def test_seg_extension():
    """Test the seg extension for line segments and intervals."""
    config = PGliteConfig(extensions=["seg"])
    with PGliteManager(config=config) as db:
        with psycopg.connect(db.get_dsn(), autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS seg")
            # TODO: Test seg extension functionality


def test_tsm_system_rows_extension():
    """Test the tsm_system_rows extension for SYSTEM_ROWS table sampling."""
    config = PGliteConfig(extensions=["tsm_system_rows"])
    with PGliteManager(config=config) as db:
        with psycopg.connect(db.get_dsn(), autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS tsm_system_rows")
            # TODO: Test tsm_system_rows extension functionality


def test_tsm_system_time_extension():
    """Test the tsm_system_time extension for SYSTEM_TIME table sampling."""
    config = PGliteConfig(extensions=["tsm_system_time"])
    with PGliteManager(config=config) as db:
        with psycopg.connect(db.get_dsn(), autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS tsm_system_time")
            # TODO: Test tsm_system_time extension functionality


@pytest.mark.skip(reason="currently not working")
def test_unaccent_extension():
    """Test the unaccent extension for accent removal in text search."""
    config = PGliteConfig(extensions=["unaccent"])
    with PGliteManager(config=config) as db:
        with psycopg.connect(db.get_dsn(), autocommit=True) as conn:
            conn.execute("CREATE EXTENSION IF NOT EXISTS unaccent")
            conn.execute("SELECT unaccent('Hôtel')")
