#!/usr/bin/env python3
"""
⚡ py-pglite: The Sweet Spot Between Speed & Power
================================================

Honest comparison: SQLite vs py-pglite vs Docker PostgreSQL
See why py-pglite gives you the best of both worlds!

Usage:
    python simple_performance.py
"""

import sqlite3
import time

from sqlalchemy import text

from py_pglite.sqlalchemy import SQLAlchemyPGliteManager


def measure_boot_time():
    """Measure py-pglite boot time vs Docker PostgreSQL."""

    # py-pglite boot time
    start = time.time()
    with SQLAlchemyPGliteManager() as manager:
        engine = manager.get_engine()
        with engine.connect() as conn:
            conn.execute(text("SELECT 1")).scalar()
    pglite_boot = time.time() - start

    # Docker PostgreSQL simulation (based on research)

    # SQLite boot time
    start = time.time()
    conn = sqlite3.connect(":memory:")
    conn.execute("SELECT 1").fetchone()
    conn.close()
    sqlite_boot = time.time() - start

    return pglite_boot, sqlite_boot


def measure_feature_power():
    """Show the PostgreSQL features that SQLite simply cannot do."""

    with SQLAlchemyPGliteManager() as manager:
        engine = manager.get_engine()

        with engine.connect() as conn:
            # Setup advanced table
            conn.execute(
                text("""
                CREATE TABLE analytics (
                    id SERIAL PRIMARY KEY,
                    user_data JSONB NOT NULL,
                    tags TEXT[] NOT NULL,
                    metrics NUMERIC[] NOT NULL,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            )

            # Insert complex data
            conn.execute(
                text("""
                INSERT INTO analytics (user_data, tags, metrics)
                SELECT
                    json_build_object(
                        'id', generate_series,
                        'name', 'User_' || generate_series,
                        'score', random() * 100,
                        'active', random() > 0.3
                    )::jsonb,
                    ARRAY[
                        'tag_' || (generate_series % 5),
                        'category_' || (generate_series % 3)],
                    ARRAY[random() * 100, random() * 50, random() * 200]
                FROM generate_series(1, 1000)
            """)
            )
            conn.commit()

            # JSON aggregation
            start = time.time()
            result = conn.execute(
                text("""
                SELECT
                    COUNT(*) as total_users,
                    COUNT(*) FILTER (WHERE user_data->>'active' = 'true')
                    AS active_users,
                    json_agg(
                        user_data->>'name'
                        ORDER BY (user_data->>'score')::numeric DESC
                    )
                    FILTER (WHERE (user_data->>'score')::numeric > 80)
                    AS top_users
                FROM analytics
            """)
            ).fetchone()
            json_time = time.time() - start

            # result[2] is already a Python list from PostgreSQL json_agg
            result[2] if result[2] else []

            # Array operations
            start = time.time()
            result = conn.execute(
                text("""
                SELECT
                    unnest(tags) as tag,
                    COUNT(*) as usage_count,
                    AVG(array_length(metrics, 1)) as avg_metrics
                FROM analytics
                WHERE 'tag_1' = ANY(tags)
                GROUP BY unnest(tags)
                ORDER BY usage_count DESC
                LIMIT 5
            """)
            ).fetchall()
            array_time = time.time() - start

            # Window functions
            start = time.time()
            result = conn.execute(
                text("""
                SELECT
                    user_data->>'name' as name,
                    (user_data->>'score')::numeric as score,
                    ROW_NUMBER() OVER
                       (ORDER BY (user_data->>'score')::numeric DESC) as rank,
                    PERCENT_RANK() OVER
                       (ORDER BY (user_data->>'score')::numeric) as percentile
                FROM analytics
                WHERE (user_data->>'score')::numeric > 90
                ORDER BY score DESC
                LIMIT 3
            """)
            ).fetchall()
            window_time = time.time() - start

            # Time series analysis
            start = time.time()
            result = conn.execute(
                text("""
                SELECT
                    DATE_TRUNC('minute', created_at) as minute,
                    COUNT(*) as events,
                    AVG((user_data->>'score')::numeric) as avg_score
                FROM analytics
                GROUP BY DATE_TRUNC('minute', created_at)
                ORDER BY minute
                LIMIT 1
            """)
            ).fetchone()
            time_series_time = time.time() - start

            total_feature_time = json_time + array_time + window_time + time_series_time

            return total_feature_time


def measure_raw_performance():
    """Honest comparison of raw query performance."""

    # Setup databases
    with SQLAlchemyPGliteManager() as manager:
        engine = manager.get_engine()
        sqlite_conn = sqlite3.connect(":memory:")

        # Create similar tables
        with engine.connect() as conn:
            conn.execute(
                text("""
                CREATE TABLE users (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    email TEXT,
                    created_at TIMESTAMP DEFAULT NOW()
                )
            """)
            )
            conn.commit()

        sqlite_conn.execute("""
            CREATE TABLE users (
                id INTEGER PRIMARY KEY,
                name TEXT NOT NULL,
                email TEXT,
                created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
            )
        """)

        # Bulk insert test

        # py-pglite
        start = time.time()
        with engine.connect() as conn:
            conn.execute(
                text("""
                INSERT INTO users (name, email)
                SELECT
                    'User_' || generate_series,
                    'user' || generate_series || '@test.com'
                FROM generate_series(1, 1000)
            """)
            )
            conn.commit()
        pglite_insert = time.time() - start

        # SQLite
        start = time.time()
        for i in range(1, 1001):
            sqlite_conn.execute(
                "INSERT INTO users (name, email) VALUES (?, ?)",
                (f"User_{i}", f"user{i}@test.com"),
            )
        sqlite_conn.commit()
        sqlite_insert = time.time() - start

        if sqlite_insert < pglite_insert:
            pglite_insert / sqlite_insert
        else:
            sqlite_insert / pglite_insert

        # Query test

        # py-pglite
        start = time.time()
        with engine.connect() as conn:
            conn.execute(
                text("""
                SELECT
                    COUNT(*) as total,
                    COUNT(*) FILTER (WHERE id % 2 = 0) as even_ids,
                    string_agg(name, ', ' ORDER BY id) FILTER
                         (WHERE id <= 5) as first_five
                FROM users
            """)
            ).fetchone()
        pglite_query = time.time() - start

        # SQLite (simplified - no FILTER clause)
        start = time.time()
        sqlite_conn.execute(
            "SELECT COUNT(*) FROM users",
        ).fetchone()[0]
        sqlite_conn.execute("SELECT COUNT(*) FROM users WHERE id % 2 = 0").fetchone()[0]
        sqlite_query = time.time() - start

        sqlite_conn.close()

        return pglite_insert, sqlite_insert, pglite_query, sqlite_query


def generate_final_report(boot_times, feature_time, perf_times):
    """Generate an honest and compelling final report."""
    pglite_boot, sqlite_boot = boot_times
    pglite_insert, sqlite_insert, pglite_query, sqlite_query = perf_times


def main():
    """Run the complete, honest performance showdown."""

    # Boot time comparison
    boot_times = measure_boot_time()

    # Feature power demonstration
    feature_time = measure_feature_power()

    # Raw performance test
    perf_times = measure_raw_performance()

    # Final honest report
    generate_final_report(
        boot_times,
        feature_time,
        perf_times,
    )


if __name__ == "__main__":
    main()
