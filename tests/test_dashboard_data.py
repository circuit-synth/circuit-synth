"""
Tests for dashboard_data module - agent status parsing and display.
"""

import pytest
import tempfile
from pathlib import Path
import sys

# Add adw_modules to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent / "adws" / "adw_modules"))

from dashboard_data import (
    _get_current_agents_status,
    get_active_agents_table,
    get_agent_by_issue,
    AgentStatus
)


@pytest.fixture
def temp_trees_dir():
    """Create a temporary trees directory for testing"""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield Path(tmpdir)


@pytest.fixture
def sample_status_md_content():
    """Sample status.md content matching the correct format"""
    return """# Agent Status

**Issue:** #449
**Status:** running
**Started:** 2025-10-31T18:18:16.162530
**Worker ID:** w-abc123
**Priority:** p0
"""


@pytest.fixture
def sample_status_md_minimal():
    """Minimal valid status.md content"""
    return """**Issue:** #123
**Status:** running
**Started:** 2025-11-02T10:00:00
"""


def test_parse_status_md_with_all_fields(temp_trees_dir, sample_status_md_content):
    """Test parsing status.md with all fields present"""
    # Create a worktree with status.md
    worktree = temp_trees_dir / "gh-449"
    worktree.mkdir()
    status_file = worktree / "status.md"
    status_file.write_text(sample_status_md_content)

    # Parse agents
    agents = _get_current_agents_status(temp_trees_dir)

    # Verify
    assert len(agents) == 1
    agent = agents[0]
    assert agent.issue_number == "449"
    assert agent.status == "running"
    assert agent.started == "2025-10-31T18:18:16.162530"
    assert agent.worker_id == "w-abc123"
    assert agent.priority == "p0"
    assert agent.tree_path == worktree


def test_parse_status_md_minimal_fields(temp_trees_dir, sample_status_md_minimal):
    """Test parsing status.md with only required fields"""
    # Create a worktree with minimal status.md
    worktree = temp_trees_dir / "gh-123"
    worktree.mkdir()
    status_file = worktree / "status.md"
    status_file.write_text(sample_status_md_minimal)

    # Parse agents
    agents = _get_current_agents_status(temp_trees_dir)

    # Verify
    assert len(agents) == 1
    agent = agents[0]
    assert agent.issue_number == "123"
    assert agent.status == "running"
    assert agent.started == "2025-11-02T10:00:00"
    assert agent.worker_id is None
    assert agent.priority is None


def test_parse_multiple_agents(temp_trees_dir):
    """Test parsing multiple active agents"""
    # Create multiple worktrees
    for i, (issue, priority) in enumerate([(449, "p0"), (450, "p1"), (451, "p2")]):
        worktree = temp_trees_dir / f"gh-{issue}"
        worktree.mkdir()
        status_file = worktree / "status.md"
        content = f"""**Issue:** #{issue}
**Status:** running
**Started:** 2025-11-02T10:0{i}:00
**Worker ID:** w-{i:06x}
**Priority:** {priority}
"""
        status_file.write_text(content)

    # Parse agents
    agents = _get_current_agents_status(temp_trees_dir)

    # Verify
    assert len(agents) == 3
    issue_numbers = {agent.issue_number for agent in agents}
    assert issue_numbers == {"449", "450", "451"}


def test_empty_trees_directory(temp_trees_dir):
    """Test parsing when trees directory is empty"""
    agents = _get_current_agents_status(temp_trees_dir)
    assert len(agents) == 0


def test_nonexistent_trees_directory():
    """Test parsing when trees directory doesn't exist"""
    nonexistent = Path("/nonexistent/path/to/trees")
    agents = _get_current_agents_status(nonexistent)
    assert len(agents) == 0


def test_worktree_without_status_file(temp_trees_dir):
    """Test parsing when worktree exists but has no status.md"""
    worktree = temp_trees_dir / "gh-999"
    worktree.mkdir()

    agents = _get_current_agents_status(temp_trees_dir)
    assert len(agents) == 0


def test_malformed_status_file(temp_trees_dir):
    """Test parsing with malformed status.md (missing required fields)"""
    worktree = temp_trees_dir / "gh-bad"
    worktree.mkdir()
    status_file = worktree / "status.md"
    status_file.write_text("This is not a valid status file")

    # Should not crash, just skip the invalid file
    agents = _get_current_agents_status(temp_trees_dir)
    assert len(agents) == 0


def test_regex_matches_correct_format():
    """Test that regex patterns match the documented format exactly"""
    import re

    # Test Issue pattern
    issue_pattern = r'\*\*Issue:\*\* #(\d+)'
    assert re.search(issue_pattern, "**Issue:** #449")
    assert re.search(issue_pattern, "**Issue:** #449").group(1) == "449"
    # Should NOT match wrong format
    assert not re.search(issue_pattern, "Issue:** #449")
    assert not re.search(issue_pattern, "**Issue: #449")

    # Test Status pattern
    status_pattern = r'\*\*Status:\*\* (.+)'
    assert re.search(status_pattern, "**Status:** running")
    assert re.search(status_pattern, "**Status:** running").group(1).strip() == "running"

    # Test Started pattern
    started_pattern = r'\*\*Started:\*\* (.+)'
    assert re.search(started_pattern, "**Started:** 2025-10-31T18:18:16.162530")
    assert re.search(started_pattern, "**Started:** 2025-10-31T18:18:16.162530").group(1).strip() == "2025-10-31T18:18:16.162530"


def test_get_active_agents_table(temp_trees_dir, sample_status_md_content):
    """Test generating formatted table of active agents"""
    # Create a worktree with status.md
    worktree = temp_trees_dir / "gh-449"
    worktree.mkdir()
    status_file = worktree / "status.md"
    status_file.write_text(sample_status_md_content)

    # Get table
    table = get_active_agents_table(temp_trees_dir)

    # Verify table contains expected info
    assert "w-abc123" in table
    assert "#449" in table
    assert "p0" in table
    assert "running" in table
    assert "Total: 1 active agent(s)" in table


def test_get_active_agents_table_empty(temp_trees_dir):
    """Test table generation with no active agents"""
    table = get_active_agents_table(temp_trees_dir)
    assert "No active agents currently running" in table


def test_get_agent_by_issue(temp_trees_dir, sample_status_md_content):
    """Test finding agent by issue number"""
    # Create a worktree with status.md
    worktree = temp_trees_dir / "gh-449"
    worktree.mkdir()
    status_file = worktree / "status.md"
    status_file.write_text(sample_status_md_content)

    # Find by issue
    agent = get_agent_by_issue(temp_trees_dir, "449")

    # Verify
    assert agent is not None
    assert agent.issue_number == "449"
    assert agent.worker_id == "w-abc123"


def test_get_agent_by_issue_not_found(temp_trees_dir):
    """Test finding agent when issue doesn't exist"""
    agent = get_agent_by_issue(temp_trees_dir, "999")
    assert agent is None


def test_regression_wrong_regex_patterns():
    """
    Regression test: Verify we're using the CORRECT regex patterns for issue #456.

    Issue #456 documented that the regex patterns need to match this format:
    - **Issue:** #449
    - **Status:** running
    - **Started:** 2025-10-31T18:18:16.162530

    The correct patterns are:
    - r'\\*\\*Issue:\\*\\* #(\\d+)'
    - r'\\*\\*Status:\\*\\* (.+)'
    - r'\\*\\*Started:\\*\\* (.+)'
    """
    import re

    test_content = """**Issue:** #449
**Status:** running
**Started:** 2025-10-31T18:18:16.162530"""

    # Correct patterns - these SHOULD match
    correct_issue_pattern = r'\*\*Issue:\*\* #(\d+)'
    correct_status_pattern = r'\*\*Status:\*\* (.+)'
    correct_started_pattern = r'\*\*Started:\*\* (.+)'

    assert re.search(correct_issue_pattern, test_content)
    assert re.search(correct_status_pattern, test_content)
    assert re.search(correct_started_pattern, test_content)

    # Verify captured groups are correct
    issue_match = re.search(correct_issue_pattern, test_content)
    assert issue_match.group(1) == "449"

    status_match = re.search(correct_status_pattern, test_content)
    assert status_match.group(1).strip() == "running"

    started_match = re.search(correct_started_pattern, test_content)
    assert started_match.group(1).strip() == "2025-10-31T18:18:16.162530"
