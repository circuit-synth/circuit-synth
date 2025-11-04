#!/usr/bin/env python3
"""
Reset TAC database with correct schema.

This script:
1. Drops all existing TAC tables
2. Recreates them from the single source of truth (001_initial_schema.sql)

Usage:
    python3 adws/database/reset_database.py
"""

import asyncio
import asyncpg
from pathlib import Path


async def reset_database():
    """Drop and recreate TAC database schema"""

    # Database connection
    conn = await asyncpg.connect(
        host='localhost',
        port=5433,
        user='tacx',
        password='tacx',
        database='tacx'
    )

    try:
        print("=" * 80)
        print("TAC DATABASE RESET")
        print("=" * 80)

        # Drop all TAC tables (cascade will handle foreign keys)
        print("\n1. Dropping existing tables...")
        tables = [
            'tac_events',
            'tac_helper_agents',
            'tac_stages',
            'tac_tasks',
            'tac_agent_templates',
            'tac_cost_summary',
            'schema_version'
        ]

        for table in tables:
            await conn.execute(f'DROP TABLE IF EXISTS {table} CASCADE')
            print(f"   ✓ Dropped {table}")

        # Read migration file
        print("\n2. Loading schema from migration file...")
        migration_file = Path(__file__).parent / "migrations" / "001_initial_schema.sql"
        schema_sql = migration_file.read_text()
        print(f"   ✓ Loaded {migration_file}")

        # Execute schema
        print("\n3. Creating tables...")
        await conn.execute(schema_sql)
        print("   ✓ Schema created successfully")

        # Verify tables were created
        print("\n4. Verifying tables...")
        tables_result = await conn.fetch('''
            SELECT tablename
            FROM pg_tables
            WHERE schemaname = 'public'
            AND tablename LIKE 'tac_%'
            ORDER BY tablename
        ''')

        print("   Created tables:")
        for row in tables_result:
            print(f"     - {row['tablename']}")

        print("\n" + "=" * 80)
        print("✓ DATABASE RESET COMPLETE")
        print("=" * 80)

    finally:
        await conn.close()


if __name__ == "__main__":
    asyncio.run(reset_database())
