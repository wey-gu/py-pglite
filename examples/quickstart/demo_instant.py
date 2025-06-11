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

    print("⚡ py-pglite: Instant PostgreSQL Magic")
    print("=" * 40)

    # 🎯 ONE LINE: Real PostgreSQL ready!
    with SQLAlchemyPGliteManager() as db:
        engine = db.get_engine()

        print("✅ PostgreSQL started (zero config!)")

        # 🎪 Real PostgreSQL power in action
        with engine.connect() as conn:
            from sqlalchemy import text

            # Test 1: Version check
            result = conn.execute(text("SELECT version()")).scalar()
            print(f"🔥 Running: {result.split(',')[0]}")

            # Test 2: JSON power (not available in SQLite!)
            result = conn.execute(
                text("""
                SELECT '{"framework": "py-pglite", "speed": "instant"}'::json
                    ->> 'framework'
            """)
            ).scalar()
            print(f"🚀 JSON test: {result}")

            # Test 3: Array magic
            result = conn.execute(
                text("""
                SELECT array_length(ARRAY['fast', 'simple', 'powerful'], 1)
            """)
            ).scalar()
            print(f"🎯 Array test: {result} features")

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

            result = conn.execute(
                text("""
                SELECT count(*) FROM demo_users
            """)
            ).scalar()
            print(f"📊 Inserted {result} users instantly")

            # Test 5: Window functions (advanced PostgreSQL)
            result = conn.execute(
                text("""
                SELECT name,
                       row_number() OVER (ORDER BY name) as rank
                FROM demo_users
                ORDER BY rank LIMIT 1
            """)
            ).fetchone()
            print(f"🏆 First user: {result[0]} (rank #{result[1]})")

    print()
    print("🎉 DONE! Real PostgreSQL in seconds!")
    print("🔥 Key Points:")
    print("   • Zero Docker, zero config, zero setup")
    print("   • Real PostgreSQL (not SQLite/mock)")
    print("   • JSON, arrays, window functions work")
    print("   • Perfect for testing & prototyping")
    print("   • Works with SQLAlchemy, Django, FastAPI")

    print()
    print("⚡ Next steps:")
    print("   pip install py-pglite[sqlalchemy]")
    print("   # Start writing tests immediately!")


if __name__ == "__main__":
    main()
