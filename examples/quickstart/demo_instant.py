#!/usr/bin/env python3
"""
⚡ py-pglite: Instant PostgreSQL Magic
====================================

The simplest demo possible - 5 lines, real PostgreSQL!
Perfect first impression, Vite-style simplicity.

Usage:
    python demo_instant.py
"""

from py_pglite.sqlalchemy import SQLAlchemyPGliteManager


def main():
    """⚡ Instant PostgreSQL in 5 lines - just like Vite!"""

    # 🎯 ONE LINE: Real PostgreSQL ready!
    with SQLAlchemyPGliteManager() as db:
        engine = db.get_engine()

        # 🎪 Real PostgreSQL power in action
        with engine.connect() as conn:
            from sqlalchemy import text

            # Test 1: Version check
            conn.execute(text("SELECT version()")).scalar()

            # Test 2: JSON power (not available in SQLite!)
            conn.execute(
                text("""
                SELECT '{"framework": "py-pglite", "speed": "instant"}'::json
                    ->> 'framework'
            """)
            ).scalar()

            # Test 3: Array magic
            conn.execute(
                text("""
                SELECT array_length(ARRAY['fast', 'simple', 'powerful'], 1)
            """)
            ).scalar()

            # Test 4: Quick table ops
            conn.execute(
                text("""
                CREATE TABLE demo_users (
                    id SERIAL PRIMARY KEY,
                    name TEXT,
                    created TIMESTAMP DEFAULT NOW()
                )
            """)
            )

            conn.execute(
                text("""
                INSERT INTO demo_users (name) VALUES
                ('Alice'), ('Bob'), ('Charlie')
            """)
            )

            conn.execute(
                text("""
                SELECT count(*) FROM demo_users
            """)
            ).scalar()

            # Test 5: Window functions (advanced PostgreSQL)
            conn.execute(
                text("""
                SELECT name,
                       row_number() OVER (ORDER BY name) as rank
                FROM demo_users
                ORDER BY rank LIMIT 1
            """)
            ).fetchone()


if __name__ == "__main__":
    main()
