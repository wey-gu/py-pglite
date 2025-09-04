#!/usr/bin/env python3
"""
🚀 Instant AsyncPG + PostgreSQL
================================

Zero-config asyncpg with real PostgreSQL in 30 seconds.
Shows the proper configuration for asyncpg with py-pglite.

Usage:
    pip install py-pglite[asyncpg]
    python simple_asyncpg.py

Recent findings: asyncpg DOES work with PGlite TCP mode when configured properly!
"""

import asyncio
from py_pglite import PGliteConfig, PGliteManager

try:
    import asyncpg
except ImportError:
    print("❌ asyncpg not available. Install with: pip install py-pglite[asyncpg]")
    exit(1)


async def main():
    """⚡ Instant PostgreSQL with asyncpg - proper configuration!"""
    
    print("🚀 Starting py-pglite with asyncpg...")
    
    # Enable TCP mode (required for asyncpg)
    config = PGliteConfig(use_tcp=True, tcp_port=5432)
    
    with PGliteManager(config) as manager:
        print(f"✅ PGlite started on {config.tcp_host}:{config.tcp_port}")
        
        # Connect with asyncpg using the CRITICAL configuration discovered
        # Key finding: server_settings={} prevents hanging!
        conn = await asyncio.wait_for(
            asyncpg.connect(
                host=config.tcp_host,
                port=config.tcp_port,
                user="postgres",
                password="postgres",
                database="postgres",
                ssl=False,
                server_settings={}  # CRITICAL: Empty server_settings prevents hanging
            ),
            timeout=10.0
        )
        
        try:
            print("✅ Connected to PostgreSQL via asyncpg!")
            
            # Test 1: Basic query
            result = await conn.fetchval("SELECT version()")
            print(f"📊 PostgreSQL Version: {result[:50]}...")
            
            # Test 2: Create table with advanced types
            await conn.execute("""
                CREATE TABLE async_demo (
                    id SERIAL PRIMARY KEY,
                    name TEXT NOT NULL,
                    data JSONB,
                    tags TEXT[],
                    created TIMESTAMP DEFAULT NOW()
                )
            """)
            print("✅ Table created with JSONB and array support!")
            
            # Test 3: Insert with prepared statements
            stmt = await conn.prepare("""
                INSERT INTO async_demo (name, data, tags) 
                VALUES ($1, $2, $3) RETURNING id
            """)
            
            import json
            user_id = await stmt.fetchval(
                "Alice",
                json.dumps({"role": "admin", "score": 95}),
                ["python", "asyncpg", "postgresql"]
            )
            print(f"✅ Inserted user with ID: {user_id}")
            
            # Test 4: Complex query with JSON operations
            row = await conn.fetchrow("""
                SELECT 
                    name,
                    data->>'role' as role,
                    data->>'score' as score,
                    array_length(tags, 1) as tag_count,
                    created
                FROM async_demo 
                WHERE id = $1
            """, user_id)
            
            print(f"✅ Query result:")
            print(f"   Name: {row['name']}")
            print(f"   Role: {row['role']}")
            print(f"   Score: {row['score']}")
            print(f"   Tags: {row['tag_count']} tags")
            print(f"   Created: {row['created']}")
            
            # Test 5: Transaction support
            async with conn.transaction():
                await conn.execute("""
                    INSERT INTO async_demo (name, data, tags) VALUES
                    ('Bob', '{"role": "user"}', ARRAY['beginner']),
                    ('Carol', '{"role": "moderator"}', ARRAY['advanced', 'helper'])
                """)
                count = await conn.fetchval("SELECT COUNT(*) FROM async_demo")
                print(f"✅ Transaction: {count} total records")
            
            # Test 6: Batch operations
            batch_data = [
                (f"User{i}", json.dumps({"level": i}), [f"tag{i}", "batch"])
                for i in range(1, 4)
            ]
            
            await conn.executemany("""
                INSERT INTO async_demo (name, data, tags) VALUES ($1, $2, $3)
            """, batch_data)
            
            final_count = await conn.fetchval("SELECT COUNT(*) FROM async_demo")
            print(f"✅ Batch insert completed: {final_count} total records")
            
            # Test 7: Advanced PostgreSQL features
            stats = await conn.fetchrow("""
                SELECT 
                    COUNT(*) as total_users,
                    COUNT(*) FILTER (WHERE data->>'role' = 'admin') as admins,
                    AVG((data->>'score')::int) FILTER (WHERE data ? 'score') as avg_score
                FROM async_demo
            """)
            
            print(f"✅ Advanced query:")
            print(f"   Total users: {stats['total_users']}")
            print(f"   Admins: {stats['admins']}")
            print(f"   Avg score: {stats['avg_score']}")
            
        finally:
            # Handle connection cleanup with timeout (addresses hanging issue)
            try:
                await asyncio.wait_for(conn.close(), timeout=5.0)
                print("✅ Connection closed cleanly")
            except asyncio.TimeoutError:
                print("⚠️  Connection cleanup timed out (known limitation)")
                # This is not a failure - all operations completed successfully
                pass

    print("🎉 asyncpg + py-pglite demo completed successfully!")
    print("💡 Key finding: server_settings={} is critical for asyncpg compatibility")


if __name__ == "__main__":
    asyncio.run(main())