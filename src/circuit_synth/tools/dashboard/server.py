"""
FastAPI server for TAC-8 dashboard

Provides REST API endpoints for metrics and serves frontend dashboard.
"""

from pathlib import Path
from typing import Optional
from datetime import datetime

from fastapi import FastAPI
from fastapi.responses import FileResponse, JSONResponse, HTMLResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from .metrics import MetricsAggregator


def create_app(tasks_file: Optional[Path] = None) -> FastAPI:
    """
    Create FastAPI application

    Args:
        tasks_file: Path to tasks.md (defaults to repo root/tasks.md)

    Returns:
        Configured FastAPI app
    """
    app = FastAPI(
        title="Circuit-Synth TAC Dashboard",
        description="Monitoring dashboard for TAC-8 autonomous coordination system",
        version="1.0.0"
    )

    # Configure CORS for local development
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],  # In production, restrict this
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    # Initialize metrics aggregator
    aggregator = MetricsAggregator(tasks_file=tasks_file)

    # Static files directory
    static_dir = Path(__file__).parent / "static"
    if static_dir.exists():
        app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/health")
    async def health_check():
        """Health check endpoint"""
        return {
            "status": "ok",
            "timestamp": datetime.now().isoformat()
        }

    @app.get("/api/status")
    async def get_status():
        """
        Get current coordinator status

        Returns task counts and timestamp
        """
        task_metrics = aggregator.get_task_metrics()

        return {
            "tasks": task_metrics,
            "timestamp": datetime.now().isoformat()
        }

    @app.get("/api/tasks")
    async def get_tasks():
        """
        Get detailed task information

        Returns lists of pending, active, completed, failed, and blocked tasks
        """
        tasks = aggregator.parse_tasks_md()
        return tasks

    @app.get("/api/workers")
    async def get_workers():
        """
        Get worker process metrics

        Returns CPU, memory usage for each active worker
        """
        workers = aggregator.get_worker_process_metrics()
        return {"workers": workers}

    @app.get("/api/system")
    async def get_system_metrics():
        """
        Get system resource metrics

        Returns CPU, memory, disk usage
        """
        system_metrics = aggregator.get_system_metrics()
        return system_metrics

    @app.get("/api/metrics")
    async def get_all_metrics():
        """
        Get complete metrics snapshot

        Returns all metrics combined
        """
        metrics = aggregator.get_all_metrics()
        return metrics

    @app.get("/api/thermal")
    async def get_thermal():
        """
        Get thermal metrics (Raspberry Pi)

        Returns CPU temperature if available
        """
        thermal = aggregator.get_thermal_metrics()
        if thermal is None:
            return JSONResponse(
                status_code=404,
                content={"detail": "Thermal metrics not available on this system"}
            )
        return thermal

    @app.get("/")
    async def serve_frontend():
        """Serve frontend dashboard HTML"""
        html_file = static_dir / "index.html"
        if html_file.exists():
            return FileResponse(html_file)

        # Fallback simple HTML if static file doesn't exist yet
        return HTMLResponse(content="""
<!DOCTYPE html>
<html>
<head>
    <title>Circuit-Synth Dashboard</title>
    <meta charset="utf-8">
    <meta name="viewport" content="width=device-width, initial-scale=1">
    <style>
        body {
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
            margin: 0;
            padding: 20px;
            background: #0d1117;
            color: #c9d1d9;
        }
        h1 { color: #58a6ff; }
        .container { max-width: 1200px; margin: 0 auto; }
        .status { padding: 20px; background: #161b22; border-radius: 6px; margin-bottom: 20px; }
    </style>
</head>
<body>
    <div class="container">
        <h1>Circuit-Synth TAC Dashboard</h1>
        <div class="status">
            <h2>Status</h2>
            <p>Dashboard is running. Visit <code>/api/metrics</code> for JSON data.</p>
            <p>Frontend UI will be available once static files are created.</p>
        </div>
    </div>
</body>
</html>
        """)

    return app


# For running with uvicorn directly
app = create_app()


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
