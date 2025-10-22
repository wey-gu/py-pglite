"""Tests for PGlite extensions."""

from typing import TYPE_CHECKING
from uuid import UUID

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


@pytest.mark.extensions
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


@pytest.mark.extensions
def test_uuid_ossp_extension():
    """Test the uuid-ossp extension for UUID generation."""
    # 1. Configure PGlite to use the uuid-ossp extension
    config = PGliteConfig(extensions=["uuid-ossp"])

    with PGliteManager(config=config) as db:
        # 2. Connect using a standard psycopg connection
        conn_string = db.get_dsn()
        with psycopg.connect(conn_string, autocommit=True) as conn:
            # 3. Enable the uuid-ossp extension in the database
            conn.execute('CREATE EXTENSION IF NOT EXISTS "uuid-ossp"')

            # 4. Test uuid_generate_v1() - UUID based on MAC address and timestamp
            result = conn.execute("SELECT uuid_generate_v1()").fetchone()
            assert result is not None
            uuid_v1 = result[0]
            assert isinstance(uuid_v1, UUID)
            assert (
                len(str(uuid_v1)) == 36
            )  # UUID format: 8-4-4-4-12 = 32 chars + 4 hyphens
            # Version 1 UUID has '1' in the version position
            assert uuid_v1.version == 1

            # 5. Test uuid_generate_v4() - Random UUID
            result = conn.execute("SELECT uuid_generate_v4()").fetchone()
            assert result is not None
            uuid_v4 = result[0]
            assert isinstance(uuid_v4, UUID)
            assert len(str(uuid_v4)) == 36
            # Version 4 UUID has '4' in the version position
            assert uuid_v4.version == 4

            # 6. Generate multiple UUIDs and verify they're unique
            result = conn.execute(
                """
                SELECT uuid_generate_v4()
                FROM generate_series(1, 10)
                """
            ).fetchall()
            uuids = [row[0] for row in result]
            assert len(uuids) == 10
            # All UUIDs should be unique
            assert len(set(uuids)) == 10

            # 7. Test uuid_nil() - Returns the nil UUID
            result = conn.execute("SELECT uuid_nil()").fetchone()
            assert result is not None
            nil_uuid = result[0]
            assert isinstance(nil_uuid, UUID)
            assert str(nil_uuid) == "00000000-0000-0000-0000-000000000000"

            # 8. Test uuid_ns_dns() - Returns the DNS namespace UUID
            result = conn.execute("SELECT uuid_ns_dns()").fetchone()
            assert result is not None
            dns_uuid = result[0]
            assert isinstance(dns_uuid, UUID)
            assert str(dns_uuid) == "6ba7b810-9dad-11d1-80b4-00c04fd430c8"

            # 9. Test uuid_generate_v3() - UUID based on MD5 hash of namespace and name
            result = conn.execute(
                "SELECT uuid_generate_v3(uuid_ns_dns(), 'example.com')"
            ).fetchone()
            assert result is not None
            uuid_v3 = result[0]
            assert isinstance(uuid_v3, UUID)
            assert len(str(uuid_v3)) == 36
            assert uuid_v3.version == 3  # Version 3
            # Same inputs should produce the same UUID
            result2 = conn.execute(
                "SELECT uuid_generate_v3(uuid_ns_dns(), 'example.com')"
            ).fetchone()
            assert result2[0] == uuid_v3

            # 10. Test uuid_generate_v5() - UUID based on SHA-1 hash
            result = conn.execute(
                "SELECT uuid_generate_v5(uuid_ns_dns(), 'example.com')"
            ).fetchone()
            assert result is not None
            uuid_v5 = result[0]
            assert isinstance(uuid_v5, UUID)
            assert len(str(uuid_v5)) == 36
            assert uuid_v5.version == 5  # Version 5
            # Same inputs should produce the same UUID
            result2 = conn.execute(
                "SELECT uuid_generate_v5(uuid_ns_dns(), 'example.com')"
            ).fetchone()
            assert result2[0] == uuid_v5

            # 11. Create a table with UUID primary key
            conn.execute(
                """
                CREATE TABLE users (
                    id UUID PRIMARY KEY DEFAULT uuid_generate_v4(),
                    name TEXT NOT NULL
                )
                """
            )

            # Insert data and verify UUID generation
            conn.execute("INSERT INTO users (name) VALUES ('Alice'), ('Bob')")

            result = conn.execute("SELECT id, name FROM users ORDER BY name").fetchall()
            assert len(result) == 2
            alice_id, alice_name = result[0]
            bob_id, bob_name = result[1]

            assert alice_name == "Alice"
            assert bob_name == "Bob"
            assert isinstance(alice_id, UUID)
            assert isinstance(bob_id, UUID)
            assert len(str(alice_id)) == 36
            assert len(str(bob_id)) == 36
            assert alice_id != bob_id  # UUIDs should be unique
