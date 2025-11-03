#!/usr/bin/env python3
"""
Live monitoring dashboard for TAC-8 coordinator.

Usage:
    ./tools/monitor-live.py

Shows real-time status of:
- Coordinator process
- Active workers
- Recent log activity
- Token usage
- Worktrees
"""

import os
import sys
import time
import subprocess
from pathlib import Path
from datetime import datetime, timedelta

PROJECT_ROOT = Path("/home/shane/Desktop/circuit-synth")
LOGS_DIR = PROJECT_ROOT / "logs"
TREES_DIR = PROJECT_ROOT / "trees"

def clear_screen():
    """Clear terminal screen."""
    os.system('clear')

def get_coordinator_pid():
    """Get coordinator.py PID if running."""
    try:
        result = subprocess.run(
            ["pgrep", "-f", "coordinator.py"],
            capture_output=True,
            text=True
        )
        if result.stdout.strip():
            return result.stdout.strip().split('\n')
        return []
    except:
        return []

def get_active_workers():
    """Get active Claude worker processes."""
    try:
        result = subprocess.run(
            ["ps", "aux"],
            capture_output=True,
            text=True
        )
        workers = []
        for line in result.stdout.split('\n'):
            if 'claude -p' in line and 'grep' not in line:
                parts = line.split()
                workers.append({
                    'pid': parts[1],
                    'cpu': parts[2],
                    'mem': parts[3],
                    'time': parts[9]
                })
        return workers
    except:
        return []

def get_recent_logs(minutes=5):
    """Get recently modified log files."""
    now = datetime.now()
    cutoff = now - timedelta(minutes=minutes)

    recent = []
    for log_file in LOGS_DIR.glob("gh-*.jsonl"):
        mtime = datetime.fromtimestamp(log_file.stat().st_mtime)
        if mtime > cutoff:
            age_seconds = (now - mtime).total_seconds()
            recent.append({
                'task': log_file.stem,
                'age_seconds': age_seconds,
                'size_kb': log_file.stat().st_size / 1024
            })

    return sorted(recent, key=lambda x: x['age_seconds'])

def get_worktrees():
    """Get active worktrees."""
    if not TREES_DIR.exists():
        return []

    trees = []
    for tree_dir in TREES_DIR.iterdir():
        if tree_dir.is_dir():
            # Check for recent activity
            mtime = datetime.fromtimestamp(tree_dir.stat().st_mtime)
            age = datetime.now() - mtime

            # Check if has uncommitted changes
            try:
                result = subprocess.run(
                    ["git", "status", "--short"],
                    cwd=tree_dir,
                    capture_output=True,
                    text=True,
                    timeout=2
                )
                has_changes = bool(result.stdout.strip())
            except:
                has_changes = False

            trees.append({
                'name': tree_dir.name,
                'age_minutes': age.total_seconds() / 60,
                'has_changes': has_changes
            })

    return trees

def get_token_usage_today():
    """Get token usage for today."""
    today = datetime.now().strftime("%Y-%m-%d")
    api_log = LOGS_DIR / "api" / f"api-calls-{today}.jsonl"

    if not api_log.exists():
        return {"calls": 0, "cost": 0.0, "tokens": 0}

    import json
    calls = 0
    cost = 0.0
    tokens = 0

    try:
        with open(api_log, 'r') as f:
            for line in f:
                if line.strip():
                    try:
                        data = json.loads(line)
                        calls += 1
                        cost += data.get('estimated_cost_usd', 0.0)
                        tokens += data.get('total_tokens', 0)
                    except:
                        pass
    except:
        pass

    return {"calls": calls, "cost": cost, "tokens": tokens}

def render_dashboard():
    """Render the live dashboard."""
    clear_screen()

    print("=" * 80)
    print("TAC-8 COORDINATOR - LIVE MONITOR")
    print("=" * 80)
    print(f"Time: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
    print()

    # Coordinator status
    pids = get_coordinator_pid()
    print("COORDINATOR STATUS")
    print("-" * 80)
    if pids:
        print(f"✅ Running (PID: {', '.join(pids)})")
    else:
        print("❌ Not running")
    print()

    # Active workers
    workers = get_active_workers()
    print("ACTIVE WORKERS")
    print("-" * 80)
    if workers:
        print(f"{'PID':<10} {'CPU%':<8} {'MEM%':<8} {'TIME':<10}")
        for w in workers:
            print(f"{w['pid']:<10} {w['cpu']:<8} {w['mem']:<8} {w['time']:<10}")
    else:
        print("No active workers")
    print()

    # Recent log activity
    recent = get_recent_logs(minutes=5)
    print("RECENT LOG ACTIVITY (last 5 minutes)")
    print("-" * 80)
    if recent:
        print(f"{'Task':<15} {'Age':<20} {'Size':<10}")
        for log in recent:
            age_str = f"{int(log['age_seconds'])} seconds ago"
            print(f"{log['task']:<15} {age_str:<20} {log['size_kb']:>6.1f} KB")
    else:
        print("No recent activity")
    print()

    # Worktrees
    trees = get_worktrees()
    print("WORKTREES")
    print("-" * 80)
    if trees:
        print(f"{'Task':<15} {'Age':<20} {'Changes':<10}")
        for tree in trees:
            age_str = f"{int(tree['age_minutes'])} min ago"
            changes = "Yes" if tree['has_changes'] else "No"
            print(f"{tree['name']:<15} {age_str:<20} {changes:<10}")
    else:
        print("No worktrees")
    print()

    # Today's token usage
    usage = get_token_usage_today()
    print("TODAY'S API USAGE")
    print("-" * 80)
    print(f"API Calls: {usage['calls']}")
    print(f"Tokens: {usage['tokens']:,}")
    print(f"Cost: ${usage['cost']:.4f}")
    print()

    print("=" * 80)
    print("Press Ctrl+C to exit | Refresh every 5 seconds")
    print("=" * 80)

def main():
    """Main monitoring loop."""
    try:
        while True:
            render_dashboard()
            time.sleep(5)
    except KeyboardInterrupt:
        print("\nMonitoring stopped.")
        sys.exit(0)

if __name__ == "__main__":
    main()
