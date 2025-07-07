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
