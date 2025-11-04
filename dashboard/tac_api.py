#!/usr/bin/env python3
"""
TAC Dashboard API Backend

Provides REST API endpoints for TAC observability dashboard.
Exposes PostgreSQL data via FastAPI for real-time monitoring.

Endpoints:
- GET /api/tasks - List all tasks
- GET /api/tasks/{task_id} - Get task details with stages/helpers
- GET /api/tasks/{task_id}/events - Get task events
- GET /api/active - Get active tasks
- GET /api/stats - Get system statistics

Usage:
    python3 dashboard/tac_api.py

Then access: http://localhost:8001/docs for API documentation
"""

import sys
import os
import asyncio
from pathlib import Path
from typing import List, Optional
from uuid import UUID
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
import uvicorn
import asyncpg
import logging
import json

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "adws"))

from adw_modules.tac_models import TaskModel

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Create FastAPI app
app = FastAPI(
    title="TAC Dashboard API",
    description="Real-time observability API for TAC (Task-Aware Coordinator)",
    version="1.0.0"
)

# Enable CORS for frontend access
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, specify exact origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Global database connection pool
db: Optional[asyncpg.Pool] = None


@app.on_event("startup")
async def startup():
    """Connect to database on startup"""
    global db
    logger.info("Connecting to PostgreSQL database...")
    db = await asyncpg.create_pool(
        host='localhost',
        port=5433,
        user='tacx',
        password='tacx',
        database='tacx',
        min_size=2,
        max_size=10
    )
    logger.info("✓ Connected to PostgreSQL database (pool size: 2-10)")
    print("✓ Connected to PostgreSQL database")


@app.on_event("shutdown")
async def shutdown():
    """Close database connection on shutdown"""
    global db
    if db:
        await db.close()
        logger.info("✓ Closed database connection pool")
        print("✓ Closed database connection")


@app.get("/api/tasks")
async def list_tasks(limit: int = 50):
    """List all tasks (most recent first)"""
    logger.info(f"GET /api/tasks - Fetching up to {limit} tasks")

    if not db:
        logger.error("Database pool not initialized")
        raise HTTPException(status_code=500, detail="Database not connected")

    # Get recent tasks
    query = """
        SELECT * FROM tac_tasks
        ORDER BY created_at DESC
        LIMIT $1;
    """

    async with db.acquire() as conn:
        logger.debug(f"Acquired connection from pool for task list")
        rows = await conn.fetch(query, limit)
        logger.info(f"Retrieved {len(rows)} tasks from database")

    tasks = []
    for row in rows:
        row_dict = dict(row)
        # Parse workflow_config if it's a JSON string
        if 'workflow_config' in row_dict and isinstance(row_dict['workflow_config'], str):
            try:
                row_dict['workflow_config'] = json.loads(row_dict['workflow_config'])
            except (json.JSONDecodeError, TypeError):
                row_dict['workflow_config'] = None
        tasks.append(TaskModel(**row_dict))

    logger.info(f"Successfully serialized {len(tasks)} tasks")
    return {"tasks": [t.model_dump() for t in tasks], "count": len(tasks)}


@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    """Get detailed task information with stages and helpers"""
    logger.info(f"GET /api/tasks/{task_id} - Fetching task details")

    if not db:
        logger.error("Database pool not initialized")
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        task_uuid = UUID(task_id)
        logger.debug(f"Parsed task UUID: {task_uuid}")
    except ValueError as e:
        logger.warning(f"Invalid UUID format: {task_id} - {e}")
        raise HTTPException(status_code=400, detail="Invalid task ID format")

    async with db.acquire() as conn:
        logger.debug(f"Acquired database connection for task {task_uuid}")

        # Fetch task
        logger.debug(f"Fetching task {task_uuid} from tac_tasks")
        task_row = await conn.fetchrow("""
            SELECT * FROM tac_tasks WHERE id = $1
        """, task_uuid)

        if not task_row:
            logger.warning(f"Task {task_uuid} not found")
            raise HTTPException(status_code=404, detail="Task not found")

        logger.info(f"Found task: {task_row['issue_number']}")

        # Fetch stages
        logger.debug(f"Fetching stages for task {task_uuid}")
        stage_rows = await conn.fetch("""
            SELECT * FROM tac_stages WHERE task_id = $1 ORDER BY created_at
        """, task_uuid)
        logger.info(f"Found {len(stage_rows)} stages")

        # Fetch helpers
        logger.debug(f"Fetching helpers for task {task_uuid}")
        helper_rows = await conn.fetch("""
            SELECT * FROM tac_helper_agents WHERE task_id = $1 ORDER BY created_at
        """, task_uuid)
        logger.info(f"Found {len(helper_rows)} helpers")

        # Fetch events
        logger.debug(f"Fetching events for task {task_uuid}")
        event_rows = await conn.fetch("""
            SELECT * FROM tac_events WHERE task_id = $1 ORDER BY created_at DESC LIMIT 10
        """, task_uuid)
        logger.info(f"Found {len(event_rows)} events")

    result = {
        "task": dict(task_row),
        "stages": [dict(row) for row in stage_rows],
        "helpers": [dict(row) for row in helper_rows],
        "event_count": len(event_rows),
        "latest_events": [dict(row) for row in event_rows],
    }

    logger.info(f"Successfully retrieved details for task {task_uuid}")
    return result


@app.get("/api/tasks/{task_id}/events")
async def get_task_events(
    task_id: str,
    limit: int = 100,
    category: Optional[str] = None
):
    """Get events for a specific task"""
    if not db:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        task_uuid = UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID format")

    events = await db.get_task_events(
        task_uuid,
        limit=limit,
        event_category=category
    )

    return {
        "task_id": task_id,
        "events": [e.model_dump() for e in events],
        "count": len(events),
    }


@app.get("/api/active")
async def get_active_tasks():
    """Get all active (running) tasks"""
    if not db:
        raise HTTPException(status_code=500, detail="Database not connected")

    active_tasks = await db.get_active_tasks()

    return {
        "tasks": [t.model_dump() for t in active_tasks],
        "count": len(active_tasks),
    }


@app.get("/api/stats")
async def get_statistics():
    """Get overall system statistics"""
    logger.info("GET /api/stats - Fetching system statistics")

    if not db:
        logger.error("Database pool not initialized")
        raise HTTPException(status_code=500, detail="Database not connected")

    # Get aggregate statistics
    stats_query = """
        SELECT
            COUNT(*)::int as total_tasks,
            COUNT(*) FILTER (WHERE status = 'running')::int as running_tasks,
            COUNT(*) FILTER (WHERE status = 'completed')::int as completed_tasks,
            COUNT(*) FILTER (WHERE status = 'errored')::int as errored_tasks,
            COALESCE(SUM(total_cost), 0) as total_cost,
            COALESCE(SUM(total_input_tokens), 0)::bigint as total_input_tokens,
            COALESCE(SUM(total_output_tokens), 0)::bigint as total_output_tokens
        FROM tac_tasks;
    """

    async with db.acquire() as conn:
        logger.debug("Acquired connection from pool for statistics")

        # Get task statistics
        logger.debug("Fetching task statistics...")
        stats_row = await conn.fetchrow(stats_query)
        logger.info(f"Task stats: {stats_row['total_tasks']} total, {stats_row['running_tasks']} running")

        # Get helper count
        logger.debug("Fetching helper agent count...")
        helper_count_query = "SELECT COUNT(*)::int as helper_count FROM tac_helper_agents;"
        helper_row = await conn.fetchrow(helper_count_query)
        logger.info(f"Helper agents: {helper_row['helper_count']}")

        # Get template count
        logger.debug("Fetching agent template count...")
        template_count_query = "SELECT COUNT(*)::int as template_count FROM tac_agent_templates WHERE is_active = true;"
        template_row = await conn.fetchrow(template_count_query)
        logger.info(f"Active templates: {template_row['template_count']}")

    return {
        "tasks": {
            "total": stats_row['total_tasks'],
            "running": stats_row['running_tasks'],
            "completed": stats_row['completed_tasks'],
            "errored": stats_row['errored_tasks'],
        },
        "costs": {
            "total": float(stats_row['total_cost']),
            "input_tokens": stats_row['total_input_tokens'],
            "output_tokens": stats_row['total_output_tokens'],
        },
        "helpers": {
            "total": helper_row['helper_count'],
        },
        "templates": {
            "active": template_row['template_count'],
        }
    }


@app.get("/api/templates")
async def get_templates():
    """Get all active agent templates"""
    if not db:
        raise HTTPException(status_code=500, detail="Database not connected")

    templates = await db.list_agent_templates(active_only=True)

    return {
        "templates": [t.model_dump() for t in templates],
        "count": len(templates),
    }


# Mount static files for frontend
dashboard_dir = Path(__file__).parent
app.mount("/", StaticFiles(directory=dashboard_dir, html=True), name="static")


def main():
    """Run the API server"""
    print("=" * 50)
    print("TAC Dashboard API Server")
    print("=" * 50)
    print()
    print("Starting server on http://localhost:8001")
    print("API Documentation: http://localhost:8001/docs")
    print()

    uvicorn.run(
        app,
        host="0.0.0.0",
        port=8001,
        log_level="info"
    )


if __name__ == "__main__":
    main()
