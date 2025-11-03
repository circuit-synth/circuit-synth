#!/usr/bin/env python3
"""
Show coordinator status dashboard

Displays coordinator health metrics and task queue status by parsing:
- adws/metrics.json (if exists) - coordinator performance metrics
- tasks.md - current task queue status

Usage:
    python tools/status.py
    watch -n 5 python tools/status.py  # Auto-refresh every 5 seconds
"""

import json
import re
from pathlib import Path
from typing import Dict, Optional


def parse_metrics(metrics_file: Path) -> Optional[Dict]:
    """
    Parse metrics.json file for coordinator health

    Args:
        metrics_file: Path to adws/metrics.json

    Returns:
        Dictionary of metrics or None if file doesn't exist
    """
    if not metrics_file.exists():
        return None

    try:
        with open(metrics_file) as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError):
        return None


def parse_tasks_status(content: str) -> Dict[str, int]:
    """
    Parse tasks.md content to count tasks by status

    Handles the following task formats:
    - Pending: [] gh-450: Description {p1}
    - Active: [🟡 w-abc123, trees/gh-450] gh-450: Description
    - Completed: [✅ a1b2c3d, w-abc123] gh-450: Description
    - Failed: [❌ w-abc123] gh-450: Description
    - Blocked: [⏰ w-abc123] gh-450: Description

    Args:
        content: Full text content of tasks.md

    Returns:
        Dictionary with counts: {pending, active, completed, failed, blocked}
    """
    # Regex patterns for different task statuses
    # Fixed: Properly escape special regex characters
    patterns = {
        'pending': r'^\[\]\s+gh-\d+:',  # [] gh-450: ...
        'active': r'^\[🟡\s+w-[a-f0-9]+',  # [🟡 w-abc123, ...]
        'completed': r'^\[✅\s+[a-f0-9]+',  # [✅ a1b2c3d, w-abc123]
        'failed': r'^\[❌\s+w-[a-f0-9]+\]',  # [❌ w-abc123]
        'blocked': r'^\[⏰\s+w-[a-f0-9]+\]',  # [⏰ w-abc123]
    }

    counts = {status: 0 for status in patterns.keys()}

    for line in content.split('\n'):
        line = line.strip()

        # Skip empty lines, headers, comments
        if not line or line.startswith('#') or line.startswith('<!--'):
            continue

        # Check each pattern
        for status, pattern in patterns.items():
            if re.match(pattern, line):
                counts[status] += 1
                break  # Only count each line once

    return counts


def format_status_display(metrics: Optional[Dict], tasks: Dict[str, int]) -> str:
    """
    Format the status display output

    Args:
        metrics: Coordinator metrics (or None if not available)
        tasks: Task counts by status

    Returns:
        Formatted string ready for display
    """
    lines = []

    # Coordinator Health Section
    lines.append("📊 Coordinator Health")

    if metrics:
        health = metrics.get('health', 'unknown').upper()
        lines.append(f"   Status: {health}")
        lines.append(f"   Workers launched: {metrics.get('workers_launched', 0)}")
        lines.append(f"   Completed: {metrics.get('workers_completed', 0)}")
        lines.append(f"   Failed: {metrics.get('workers_failed', 0)}")
        lines.append(f"   PRs created: {metrics.get('prs_created', 0)}")

        worktree_errors = metrics.get('worktree_errors', 0)
        if worktree_errors > 0:
            lines.append(f"   ⚠️  Worktree errors: {worktree_errors}")
    else:
        lines.append("   No metrics available (metrics.json not found)")

    # Tasks Section
    lines.append("")
    lines.append("📋 Tasks")
    lines.append(f"   Pending: {tasks.get('pending', 0)}")
    lines.append(f"   Active: {tasks.get('active', 0)}")
    lines.append(f"   Completed today: {tasks.get('completed', 0)}")
    lines.append(f"   Failed: {tasks.get('failed', 0)}")

    blocked = tasks.get('blocked', 0)
    if blocked > 0:
        lines.append(f"   ⏰ Blocked: {blocked}")

    return '\n'.join(lines)


def show_status():
    """Main function to display status dashboard"""
    # Determine repository root (script is in tools/ subdirectory)
    script_dir = Path(__file__).parent
    repo_root = script_dir.parent

    # Read metrics
    metrics_file = repo_root / 'adws' / 'metrics.json'
    metrics = parse_metrics(metrics_file)

    # Read tasks.md
    tasks_file = repo_root / 'tasks.md'

    if not tasks_file.exists():
        print("❌ tasks.md not found")
        return

    try:
        content = tasks_file.read_text()
        tasks = parse_tasks_status(content)
    except IOError as e:
        print(f"❌ Error reading tasks.md: {e}")
        return

    # Display formatted output
    output = format_status_display(metrics, tasks)
    print(output)


if __name__ == '__main__':
    show_status()
