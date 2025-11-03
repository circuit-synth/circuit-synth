"""
Tests for the status dashboard tool (tools/status.py)

The dashboard displays coordinator health and task status by parsing tasks.md
"""

import tempfile
import json
from pathlib import Path
import sys
import os

# Add tools directory to path so we can import status module
sys.path.insert(0, str(Path(__file__).parent.parent / "tools"))


def test_parse_tasks_md_pending():
    """Test parsing pending tasks from tasks.md"""
    from status import parse_tasks_status

    content = """# Circuit-Synth Work Queue

## Pending

[] gh-450: Dashboard: Add token budget monitoring {p1}
[] gh-469: Test Issue {p2}

## Active (max 3)
<!-- No active tasks -->
"""

    result = parse_tasks_status(content)
    assert result['pending'] == 2
    assert result['active'] == 0


def test_parse_tasks_md_active():
    """Test parsing active tasks from tasks.md"""
    from status import parse_tasks_status

    content = """# Circuit-Synth Work Queue

## Active (max 3)

[🟡 w-abc123, trees/gh-450] gh-450: Working on dashboard

## Pending
<!-- No pending tasks -->
"""

    result = parse_tasks_status(content)
    assert result['active'] == 1
    assert result['pending'] == 0


def test_parse_tasks_md_completed():
    """Test parsing completed tasks from tasks.md"""
    from status import parse_tasks_status

    content = """# Circuit-Synth Work Queue

## Completed Today

[✅ a1b2c3d, w-xyz789] gh-451: Added metrics tracking
[✅ e4f5g6h, w-abc123] gh-452: Fixed regex bug

## Failed

[❌ w-def456] gh-453: Connection timeout

## Blocked

[⏰ w-ghi789] gh-454: Waiting for review
"""

    result = parse_tasks_status(content)
    assert result['completed'] == 2
    assert result['failed'] == 1
    assert result['blocked'] == 1


def test_parse_tasks_md_comprehensive():
    """Test parsing all task types"""
    from status import parse_tasks_status

    content = """# Circuit-Synth Work Queue

**Last updated:** 2025-11-02 14:54:56

---

## Pending

[] gh-450: Dashboard: Add token budget monitoring {p1}
[] gh-469: Test Issue {p2}
[] gh-454: Another task {p2}

---

## Active (max 3)

[🟡 w-abc123, trees/gh-450] gh-450: Working on dashboard
[🟡 w-def456, trees/gh-451] gh-451: Adding metrics

---

## Completed Today

[✅ a1b2c3d, w-xyz789] gh-449: Fixed bug

---

## Failed

[❌ w-ghi789] gh-452: Connection timeout
- Reason: Network error

---

## Blocked

[⏰ w-jkl012] gh-453: Waiting for review
- Reason: Need human input
"""

    result = parse_tasks_status(content)
    assert result['pending'] == 3
    assert result['active'] == 2
    assert result['completed'] == 1
    assert result['failed'] == 1
    assert result['blocked'] == 1


def test_parse_tasks_md_with_comments():
    """Test that HTML comments are ignored"""
    from status import parse_tasks_status

    content = """# Circuit-Synth Work Queue

## Pending

<!-- This is a comment -->
[] gh-450: Real task {p1}
<!-- Another comment: [] fake-task {p1} -->

## Active (max 3)

<!-- No active tasks -->
"""

    result = parse_tasks_status(content)
    assert result['pending'] == 1
    assert result['active'] == 0


def test_parse_metrics_file():
    """Test parsing metrics.json file"""
    from status import parse_metrics

    with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
        metrics_data = {
            'workers_launched': 15,
            'workers_completed': 10,
            'workers_failed': 2,
            'prs_created': 10,
            'worktree_errors': 3,
            'health': 'ok'
        }
        json.dump(metrics_data, f)
        metrics_file = f.name

    try:
        result = parse_metrics(Path(metrics_file))
        assert result['workers_launched'] == 15
        assert result['workers_completed'] == 10
        assert result['workers_failed'] == 2
        assert result['health'] == 'ok'
    finally:
        os.unlink(metrics_file)


def test_parse_metrics_missing_file():
    """Test parsing metrics when file doesn't exist"""
    from status import parse_metrics

    result = parse_metrics(Path('/nonexistent/metrics.json'))
    assert result is None


def test_format_status_output():
    """Test the formatted status output"""
    from status import format_status_display

    metrics = {
        'workers_launched': 15,
        'workers_completed': 10,
        'workers_failed': 2,
        'prs_created': 10,
        'worktree_errors': 0,
        'health': 'ok'
    }

    tasks = {
        'pending': 3,
        'active': 2,
        'completed': 1,
        'failed': 0,
        'blocked': 0
    }

    output = format_status_display(metrics, tasks)

    # Check that output contains expected sections
    assert 'Coordinator Health' in output
    assert 'Status: OK' in output
    assert 'Workers launched: 15' in output
    assert 'Tasks' in output
    assert 'Pending: 3' in output
    assert 'Active: 2' in output
