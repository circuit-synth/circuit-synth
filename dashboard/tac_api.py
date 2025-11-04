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
import uvicorn

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "adws"))

from adw_modules.tac_database import TACDatabase
from adw_modules.tac_models import TaskModel, TaskSummary

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

# Global database connection
db: Optional[TACDatabase] = None


@app.on_event("startup")
async def startup():
    """Connect to database on startup"""
    global db
    db = TACDatabase()
    await db.connect()
    print("✓ Connected to PostgreSQL database")


@app.on_event("shutdown")
async def shutdown():
    """Close database connection on shutdown"""
    global db
    if db:
        await db.close()
        print("✓ Closed database connection")


@app.get("/")
async def root():
    """API root endpoint"""
    return {
        "name": "TAC Dashboard API",
        "version": "1.0.0",
        "status": "running",
        "endpoints": {
            "docs": "/docs",
            "tasks": "/api/tasks",
            "active": "/api/active",
            "stats": "/api/stats",
        }
    }


@app.get("/api/tasks")
async def list_tasks(limit: int = 50):
    """List all tasks (most recent first)"""
    if not db:
        raise HTTPException(status_code=500, detail="Database not connected")

    # Get recent tasks
    query = """
        SELECT * FROM tac_tasks
        ORDER BY created_at DESC
        LIMIT $1;
    """

    rows = await db.pool.fetch(query, limit)

    tasks = []
    for row in rows:
        row_dict = dict(row)
        row_dict = db._parse_jsonb_fields(row_dict)
        tasks.append(TaskModel(**row_dict))

    return {"tasks": [t.dict() for t in tasks], "count": len(tasks)}


@app.get("/api/tasks/{task_id}")
async def get_task(task_id: str):
    """Get detailed task information with stages and helpers"""
    if not db:
        raise HTTPException(status_code=500, detail="Database not connected")

    try:
        task_uuid = UUID(task_id)
    except ValueError:
        raise HTTPException(status_code=400, detail="Invalid task ID format")

    summary = await db.get_task_summary(task_uuid)

    if not summary:
        raise HTTPException(status_code=404, detail="Task not found")

    return {
        "task": summary.task.dict(),
        "stages": [s.dict() for s in summary.stages],
        "helpers": [h.dict() for h in summary.helpers],
        "event_count": summary.event_count,
        "latest_events": [e.dict() for e in summary.latest_events],
    }


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
        "events": [e.dict() for e in events],
        "count": len(events),
    }


@app.get("/api/active")
async def get_active_tasks():
    """Get all active (running) tasks"""
    if not db:
        raise HTTPException(status_code=500, detail="Database not connected")

    active_tasks = await db.get_active_tasks()

    return {
        "tasks": [t.dict() for t in active_tasks],
        "count": len(active_tasks),
    }


@app.get("/api/stats")
async def get_statistics():
    """Get overall system statistics"""
    if not db:
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

    stats_row = await db.pool.fetchrow(stats_query)

    # Get helper count
    helper_count_query = "SELECT COUNT(*)::int as helper_count FROM tac_helper_agents;"
    helper_row = await db.pool.fetchrow(helper_count_query)

    # Get template count
    template_count_query = "SELECT COUNT(*)::int as template_count FROM tac_agent_templates WHERE is_active = true;"
    template_row = await db.pool.fetchrow(template_count_query)

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
        "templates": [t.dict() for t in templates],
        "count": len(templates),
    }


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
