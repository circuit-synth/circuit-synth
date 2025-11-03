"""
Dashboard data collection for Circuit-Synth autonomous worker system.

Provides functions to collect and format data about active agents,
completed tasks, and system status for dashboard display.
"""

import re
import json
import os
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass
from datetime import datetime


@dataclass
class AgentStatus:
    """Represents the status of an active agent"""
    issue_number: str
    status: str
    started: str
    worker_id: Optional[str] = None
    priority: Optional[str] = None
    tree_path: Optional[Path] = None


def _get_current_agents_status(trees_dir: Path) -> List[AgentStatus]:
    """
    Parse status.md files from active agent worktrees.

    Args:
        trees_dir: Path to the trees directory containing worktrees

    Returns:
        List of AgentStatus objects for all active agents
    """
    agents = []

    if not trees_dir.exists():
        return agents

    # Find all status.md files in worktrees
    for tree_path in trees_dir.iterdir():
        if not tree_path.is_dir():
            continue

        status_file = tree_path / "status.md"
        if not status_file.exists():
            continue

        try:
            content = status_file.read_text()

            # Parse status.md with correct regex patterns
            # Format: **Issue:** #449
            issue_match = re.search(r'\*\*Issue:\*\* #(\d+)', content)
            # Format: **Status:** running
            status_match = re.search(r'\*\*Status:\*\* (.+)', content)
            # Format: **Started:** 2025-10-31T18:18:16.162530
            started_match = re.search(r'\*\*Started:\*\* (.+)', content)
            # Format: **Worker ID:** w-abc123
            worker_match = re.search(r'\*\*Worker ID:\*\* (.+)', content)
            # Format: **Priority:** p0
            priority_match = re.search(r'\*\*Priority:\*\* (.+)', content)

            if issue_match and status_match and started_match:
                agent = AgentStatus(
                    issue_number=issue_match.group(1),
                    status=status_match.group(1).strip(),
                    started=started_match.group(1).strip(),
                    worker_id=worker_match.group(1).strip() if worker_match else None,
                    priority=priority_match.group(1).strip() if priority_match else None,
                    tree_path=tree_path
                )
                agents.append(agent)

        except Exception as e:
            # Skip files that can't be parsed
            print(f"Warning: Could not parse {status_file}: {e}")
            continue

    return agents


def get_active_agents_table(trees_dir: Path) -> str:
    """
    Generate a formatted table of active agents for display.

    Args:
        trees_dir: Path to the trees directory containing worktrees

    Returns:
        Formatted string table of active agents
    """
    agents = _get_current_agents_status(trees_dir)

    if not agents:
        return "No active agents currently running."

    # Build table
    lines = []
    lines.append("Active Agents")
    lines.append("=" * 80)
    lines.append(f"{'Worker ID':<12} {'Issue':<10} {'Priority':<10} {'Status':<12} {'Started':<25}")
    lines.append("-" * 80)

    for agent in sorted(agents, key=lambda a: a.started, reverse=True):
        issue_display = f"#{agent.issue_number}"
        worker_display = agent.worker_id or "unknown"
        priority_display = agent.priority or "p2"
        status_display = agent.status
        started_display = agent.started[:25] if len(agent.started) > 25 else agent.started

        lines.append(
            f"{worker_display:<12} {issue_display:<10} {priority_display:<10} "
            f"{status_display:<12} {started_display:<25}"
        )

    lines.append("=" * 80)
    lines.append(f"Total: {len(agents)} active agent(s)")

    return "\n".join(lines)


def get_agent_by_issue(trees_dir: Path, issue_number: str) -> Optional[AgentStatus]:
    """
    Find an active agent by issue number.

    Args:
        trees_dir: Path to the trees directory containing worktrees
        issue_number: GitHub issue number (without #)

    Returns:
        AgentStatus if found, None otherwise
    """
    agents = _get_current_agents_status(trees_dir)

    for agent in agents:
        if agent.issue_number == issue_number:
            return agent

    return None


def get_budget_status(log_dir: Path) -> Optional[Dict]:
    """
    Calculate monthly token budget status from API logs.

    Args:
        log_dir: Path to API logs directory (e.g., logs/api)

    Returns:
        Dict with budget information:
        - budget_usd: Monthly budget in USD
        - used_usd: Amount used this month
        - remaining_usd: Amount remaining
        - percentage_used: Percentage of budget used (0-100)
        - alert_level: 'green', 'yellow', 'orange', or 'red'
        - month: Current month (YYYY-MM format)

        Returns None if budget not configured.
    """
    # Get budget from environment variable
    budget_str = os.environ.get('MONTHLY_TOKEN_BUDGET_USD')
    if not budget_str:
        # Return None if no budget configured
        return None

    try:
        budget_usd = float(budget_str)
    except ValueError:
        return None

    # Calculate current month's usage
    current_month = datetime.now().strftime('%Y-%m')
    used_usd = 0.0

    # Sum up costs from all log files this month
    if log_dir.exists():
        for log_file in log_dir.glob(f"api-calls-{current_month}-*.jsonl"):
            try:
                with open(log_file, 'r') as f:
                    for line in f:
                        try:
                            call = json.loads(line)
                            cost = call.get('estimated_cost_usd', 0.0)
                            if cost:
                                used_usd += cost
                        except json.JSONDecodeError:
                            continue
            except Exception as e:
                # Log warning but continue
                print(f"Warning: Could not read log file {log_file}: {e}")
                continue

    # Calculate metrics
    remaining_usd = budget_usd - used_usd
    percentage_used = (used_usd / budget_usd * 100) if budget_usd > 0 else 0

    # Determine alert level based on thresholds
    if percentage_used >= 95:
        alert_level = 'red'
    elif percentage_used >= 90:
        alert_level = 'orange'
    elif percentage_used >= 75:
        alert_level = 'yellow'
    else:
        alert_level = 'green'

    return {
        'budget_usd': budget_usd,
        'used_usd': round(used_usd, 4),
        'remaining_usd': round(remaining_usd, 4),
        'percentage_used': round(percentage_used, 2),
        'alert_level': alert_level,
        'month': current_month
    }


def get_budget_display(log_dir: Path) -> str:
    """
    Generate a formatted budget status display for dashboard.

    Args:
        log_dir: Path to API logs directory

    Returns:
        Formatted string showing budget status with color-coded alert
    """
    status = get_budget_status(log_dir)

    if status is None:
        return "Token Budget: Not configured (set MONTHLY_TOKEN_BUDGET_USD)"

    # Color codes for terminal display
    alert_colors = {
        'green': '\033[92m',   # Green
        'yellow': '\033[93m',  # Yellow
        'orange': '\033[33m',  # Orange
        'red': '\033[91m'      # Red
    }
    reset_color = '\033[0m'

    alert_symbols = {
        'green': '✓',
        'yellow': '⚠',
        'orange': '⚠⚠',
        'red': '🔴'
    }

    color = alert_colors.get(status['alert_level'], '')
    symbol = alert_symbols.get(status['alert_level'], '')

    lines = []
    lines.append("Token Budget Status")
    lines.append("=" * 80)
    lines.append(f"Month: {status['month']}")
    lines.append(f"Budget: ${status['budget_usd']:.2f}")
    lines.append(f"Used:   ${status['used_usd']:.4f} ({status['percentage_used']:.1f}%)")
    lines.append(f"Remaining: ${status['remaining_usd']:.4f}")
    lines.append("")
    lines.append(f"{color}Status: {symbol} {status['alert_level'].upper()}{reset_color}")

    # Add warning messages for different alert levels
    if status['alert_level'] == 'yellow':
        lines.append(f"{color}⚠  Warning: Approaching budget limit (75%){reset_color}")
    elif status['alert_level'] == 'orange':
        lines.append(f"{color}⚠⚠ Alert: Near budget limit (90%){reset_color}")
    elif status['alert_level'] == 'red':
        lines.append(f"{color}🔴 CRITICAL: Budget limit exceeded (95%+){reset_color}")

    lines.append("=" * 80)

    return "\n".join(lines)
