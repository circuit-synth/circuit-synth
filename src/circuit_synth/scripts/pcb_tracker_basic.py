#!/usr/bin/env python3
"""Basic PCB tracking CLI commands."""

from pathlib import Path

import click

from circuit_synth.pcb_tracking.models import BoardState, TrackingEntry
from circuit_synth.pcb_tracking.storage import SimpleFileStorage
from circuit_synth.pcb_tracking.structure import PCBTrackingStructure


@click.group()
def cli():
    """Basic PCB tracking commands."""
    pass


@cli.command()
@click.argument("project_path", type=click.Path(exists=True))
def init(project_path):
    """Initialize tracking for a project."""
    structure = PCBTrackingStructure(project_path)
    tracking_path = structure.initialize()

    # Create initial board state
    project_name = Path(project_path).name
    state = BoardState(board_name=project_name)
    storage = SimpleFileStorage(tracking_path)
    storage.save_board_state(state)

    click.echo(f"✓ Initialized PCB tracking in {tracking_path}")


@cli.command()
@click.argument("summary")
@click.option(
    "--type",
    "entry_type",
    default="note",
    type=click.Choice(["note", "test", "decision"]),
)
@click.option("--details", help="Additional details for the entry")
def log(summary, entry_type, details):
    """Log a manual entry."""
    # Find tracking directory
    tracking_path = Path.cwd() / "board_log"
    if not tracking_path.exists():
        click.echo("❌ No board_log found. Run 'init' first.")
        return

    storage = SimpleFileStorage(tracking_path)
    entry = TrackingEntry(entry_type=entry_type, summary=summary, details=details)
    storage.add_entry(entry)
    click.echo(f"✓ Logged {entry_type}: {summary}")


@cli.command()
@click.option("--type", "entry_type", help="Filter by entry type")
@click.option("--limit", default=20, help="Number of entries to show")
def list(entry_type, limit):
    """List tracking entries."""
    tracking_path = Path.cwd() / "board_log"
    if not tracking_path.exists():
        click.echo("❌ No board_log found.")
        return

    storage = SimpleFileStorage(tracking_path)
    entries = storage.get_entries(entry_type)

    if not entries:
        click.echo("No entries found.")
        return

    # Show most recent entries first
    entries = sorted(entries, key=lambda e: e.timestamp, reverse=True)[:limit]

    click.echo(f"\nShowing {len(entries)} most recent entries:\n")
    for entry in entries:
        timestamp = entry.timestamp.strftime("%Y-%m-%d %H:%M")
        click.echo(f"[{timestamp}] {entry.entry_type.upper()}: {entry.summary}")
        if entry.details:
            click.echo(f"  Details: {entry.details}")


@cli.command()
@click.option("--install", is_flag=True, help="Install git hooks")
def install_hooks(install):
    """Install git hooks for automatic tracking."""
    if not install:
        click.echo("Use --install flag to install git hooks")
        return

    # Check if we're in a git repository
    git_dir = Path.cwd() / ".git"
    if not git_dir.exists():
        click.echo("❌ Not in a git repository")
        return

    # Check if board_log exists
    tracking_path = Path.cwd() / "board_log"
    if not tracking_path.exists():
        click.echo("❌ No board_log found. Run 'init' first.")
        return

    # Create hooks directory if it doesn't exist
    hooks_dir = git_dir / "hooks"
    hooks_dir.mkdir(exist_ok=True)

    # Create post-commit hook
    hook_path = hooks_dir / "post-commit"
    hook_content = '''#!/usr/bin/env python3
"""Git post-commit hook for PCB tracking."""

import sys
import subprocess
from pathlib import Path

# Add project root to Python path
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

try:
    from circuit_synth.pcb_tracking.git_hook import process_git_commit
    process_git_commit()
except Exception as e:
    # Don't fail the commit if tracking fails
    print(f"PCB Tracking warning: {e}")
'''

    hook_path.write_text(hook_content)
    hook_path.chmod(0o755)

    click.echo(f"✓ Installed git post-commit hook at {hook_path}")
    click.echo("  Git commits will now be automatically tracked")


if __name__ == "__main__":
    cli()
