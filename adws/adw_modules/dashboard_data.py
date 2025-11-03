"""
Dashboard data collection for Circuit-Synth autonomous worker system.

Provides functions to collect and format data about active agents,
completed tasks, and system status for dashboard display.
"""

import re
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
