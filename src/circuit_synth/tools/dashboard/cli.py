"""
CLI entry point for dashboard server

Usage:
    cs-dashboard [--port PORT] [--host HOST]
"""

import click
import uvicorn
from pathlib import Path


@click.command()
@click.option('--port', default=8000, help='Port to run dashboard server on')
@click.option('--host', default='0.0.0.0', help='Host to bind to')
@click.option('--tasks-file', type=click.Path(exists=True), help='Path to tasks.md file')
def main(port: int, host: str, tasks_file: str):
    """
    Start Circuit-Synth TAC Dashboard server

    This will start a web server that provides real-time monitoring
    of the TAC autonomous coordination system.

    Access the dashboard at: http://localhost:8000
    """
    click.echo("🔌 Circuit-Synth TAC Dashboard")
    click.echo(f"   Starting server on {host}:{port}")

    if tasks_file:
        click.echo(f"   Using tasks file: {tasks_file}")
        tasks_path = Path(tasks_file)
    else:
        # Auto-detect tasks.md
        repo_root = Path.cwd()
        tasks_path = repo_root / "tasks.md"
        if tasks_path.exists():
            click.echo(f"   Auto-detected tasks file: {tasks_path}")
        else:
            click.echo("   Warning: tasks.md not found in current directory")
            tasks_path = None

    click.echo(f"\n   Dashboard URL: http://{host if host != '0.0.0.0' else 'localhost'}:{port}")
    click.echo("   Press Ctrl+C to stop\n")

    # Import and configure app
    from .server import create_app
    app = create_app(tasks_file=tasks_path)

    # Run server
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info"
    )


if __name__ == '__main__':
    main()
