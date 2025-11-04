#!/usr/bin/env python3
"""
TAC-X Database Migration Runner

Applies SQL migrations to PostgreSQL database.
Idempotent - safe to run multiple times.

Usage:
    python3 run_migrations.py                    # Apply all migrations
    python3 run_migrations.py --test             # Test connection only
    python3 run_migrations.py --rollback         # Rollback last migration (NOT IMPLEMENTED YET)

Environment Variables:
    DATABASE_URL - PostgreSQL connection string
        Example: postgresql://user:pass@localhost:5432/tacx
        Default: postgresql://tacx:tacx@localhost:5432/tacx
"""

import os
import sys
import asyncio
import logging
from pathlib import Path
import asyncpg

logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def get_connection():
    """Get database connection"""
    database_url = os.getenv(
        "DATABASE_URL",
        "postgresql://tacx:tacx@localhost:5432/tacx"
    )

    logger.info(f"Connecting to database...")
    try:
        conn = await asyncpg.connect(database_url)
        logger.info("✓ Database connection successful")
        return conn
    except Exception as e:
        logger.error(f"✗ Database connection failed: {e}")
        logger.info("\nTo fix:")
        logger.info("1. Ensure PostgreSQL is running")
        logger.info("2. Create database: createdb tacx")
        logger.info("3. Set DATABASE_URL environment variable")
        logger.info(f"   Current: {database_url}")
        raise


async def test_connection():
    """Test database connection"""
    conn = await get_connection()
    version = await conn.fetchval("SELECT version()")
    logger.info(f"PostgreSQL version: {version[:50]}...")
    await conn.close()
    return True


async def apply_migrations():
    """Apply all pending migrations"""
    migrations_dir = Path(__file__).parent / "migrations"
    migration_files = sorted(migrations_dir.glob("*.sql"))

    if not migration_files:
        logger.warning("No migration files found")
        return

    conn = await get_connection()

    try:
        for migration_file in migration_files:
            logger.info(f"\n{'='*60}")
            logger.info(f"Applying migration: {migration_file.name}")
            logger.info(f"{'='*60}")

            sql = migration_file.read_text()

            # Execute migration
            await conn.execute(sql)

            logger.info(f"✓ Migration {migration_file.name} applied successfully")

        # Check schema version
        version = await conn.fetchval("SELECT MAX(version) FROM schema_version")
        logger.info(f"\n{'='*60}")
        logger.info(f"✓ All migrations applied successfully")
        logger.info(f"Current schema version: {version}")
        logger.info(f"{'='*60}")

        # Show table counts for verification
        logger.info("\nTable status:")
        tables = ['tac_tasks', 'tac_stages', 'tac_helper_agents', 'tac_events', 'tac_agent_templates']
        for table in tables:
            count = await conn.fetchval(f"SELECT COUNT(*) FROM {table}")
            logger.info(f"  {table}: {count} rows")

    except Exception as e:
        logger.error(f"✗ Migration failed: {e}")
        raise
    finally:
        await conn.close()


async def run_test_insertion():
    """Test database by inserting and querying test data"""
    conn = await get_connection()

    try:
        logger.info("\n" + "="*60)
        logger.info("Running test data insertion...")
        logger.info("="*60)

        # Insert test task using function
        task_id = await conn.fetchval("SELECT insert_test_task('TEST-123')")
        logger.info(f"✓ Created test task: {task_id}")

        # Insert test stage
        stage_id = await conn.fetchval("""
            INSERT INTO tac_stages (task_id, stage_name, status, provider, model)
            VALUES ($1, 'planning', 'running', 'openrouter', 'google/gemini-2.5-flash')
            RETURNING id
        """, task_id)
        logger.info(f"✓ Created test stage: {stage_id}")

        # Insert test event
        event_id = await conn.fetchval("""
            INSERT INTO tac_events (task_id, stage_id, event_category, event_type, content)
            VALUES ($1, $2, 'stage', 'Info', 'Test event from migration runner')
            RETURNING id
        """, task_id, stage_id)
        logger.info(f"✓ Created test event: {event_id}")

        # Query test data back
        task = await conn.fetchrow("""
            SELECT * FROM tac_tasks WHERE id = $1
        """, task_id)
        logger.info(f"\n✓ Test task retrieved:")
        logger.info(f"  Issue: {task['issue_number']}")
        logger.info(f"  Status: {task['status']}")
        logger.info(f"  Stage: {task['current_stage']}")

        # Query events
        events = await conn.fetch("""
            SELECT * FROM tac_events WHERE task_id = $1 ORDER BY timestamp DESC
        """, task_id)
        logger.info(f"\n✓ Events: {len(events)}")
        for event in events:
            logger.info(f"  - {event['event_type']}: {event['content']}")

        # Clean up test data
        await conn.execute("DELETE FROM tac_tasks WHERE issue_number LIKE 'TEST-%'")
        logger.info(f"\n✓ Test data cleaned up")

        logger.info("\n" + "="*60)
        logger.info("✓ Database test completed successfully!")
        logger.info("="*60)

    except Exception as e:
        logger.error(f"✗ Test failed: {e}")
        raise
    finally:
        await conn.close()


async def main():
    """Main entry point"""
    if "--test" in sys.argv:
        await test_connection()
        return

    if "--test-data" in sys.argv:
        await run_test_insertion()
        return

    if "--rollback" in sys.argv:
        logger.error("Rollback not implemented yet")
        return

    # Default: apply migrations
    await apply_migrations()

    # Auto-test after migration
    logger.info("\n" + "="*60)
    logger.info("Running post-migration tests...")
    logger.info("="*60)
    await run_test_insertion()


if __name__ == "__main__":
    asyncio.run(main())
