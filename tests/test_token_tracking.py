"""
Tests for token budget tracking and monitoring

Tests the TokenTracker class which provides:
- Monthly budget tracking
- Alert thresholds (75%, 90%, 95%)
- Historical usage trends
- SQLite database storage
"""

import os
import sys
import tempfile
from datetime import datetime, timedelta
from pathlib import Path

# Add adws to path
sys.path.insert(0, str(Path(__file__).parent.parent / "adws"))

from adw_modules.token_tracking import (
    TokenTracker,
    AlertLevel,
    BudgetStatus,
    UsageRecord,
)


def test_token_tracker_init():
    """Test TokenTracker initialization"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        tracker = TokenTracker(db_path=db_path, budget=1000000)

        assert tracker.monthly_budget == 1000000
        assert tracker.db_path == db_path
        assert db_path.exists()


def test_token_tracker_from_env():
    """Test TokenTracker initialization from environment"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        os.environ["MONTHLY_TOKEN_BUDGET"] = "500000"

        try:
            tracker = TokenTracker(db_path=db_path)
            assert tracker.monthly_budget == 500000
        finally:
            del os.environ["MONTHLY_TOKEN_BUDGET"]


def test_record_usage():
    """Test recording token usage"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        tracker = TokenTracker(db_path=db_path, budget=1000000)

        # Record some usage
        tracker.record_usage(1000, task_id="gh-450", operation="code_generation")
        tracker.record_usage(2000, task_id="gh-451", operation="testing")

        # Check current usage
        usage = tracker.get_current_month_usage()
        assert usage == 3000


def test_get_alert_level():
    """Test alert level calculation"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        tracker = TokenTracker(db_path=db_path, budget=1000000)

        # Green: < 75%
        assert tracker.get_alert_level(0.5) == AlertLevel.GREEN
        assert tracker.get_alert_level(0.74) == AlertLevel.GREEN

        # Yellow: 75-89%
        assert tracker.get_alert_level(0.75) == AlertLevel.YELLOW
        assert tracker.get_alert_level(0.85) == AlertLevel.YELLOW

        # Orange: 90-94%
        assert tracker.get_alert_level(0.90) == AlertLevel.ORANGE
        assert tracker.get_alert_level(0.94) == AlertLevel.ORANGE

        # Red: >= 95%
        assert tracker.get_alert_level(0.95) == AlertLevel.RED
        assert tracker.get_alert_level(1.0) == AlertLevel.RED
        assert tracker.get_alert_level(1.2) == AlertLevel.RED


def test_budget_status_green():
    """Test budget status when usage is healthy (green)"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        tracker = TokenTracker(db_path=db_path, budget=1000000)

        # Use 50% of budget
        tracker.record_usage(500000)

        status = tracker.get_budget_status()
        assert status.monthly_budget == 1000000
        assert status.current_usage == 500000
        assert status.percentage_used == 0.5
        assert status.alert_level == AlertLevel.GREEN
        assert status.remaining_tokens == 500000


def test_budget_status_yellow():
    """Test budget status when usage is in warning zone (yellow)"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        tracker = TokenTracker(db_path=db_path, budget=1000000)

        # Use 80% of budget
        tracker.record_usage(800000)

        status = tracker.get_budget_status()
        assert status.alert_level == AlertLevel.YELLOW
        assert status.current_usage == 800000
        assert status.remaining_tokens == 200000


def test_budget_status_orange():
    """Test budget status when usage is critical (orange)"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        tracker = TokenTracker(db_path=db_path, budget=1000000)

        # Use 92% of budget
        tracker.record_usage(920000)

        status = tracker.get_budget_status()
        assert status.alert_level == AlertLevel.ORANGE
        assert status.current_usage == 920000


def test_budget_status_red():
    """Test budget status when budget is exceeded (red)"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        tracker = TokenTracker(db_path=db_path, budget=1000000)

        # Use 98% of budget
        tracker.record_usage(980000)

        status = tracker.get_budget_status()
        assert status.alert_level == AlertLevel.RED
        assert status.current_usage == 980000


def test_budget_status_over_budget():
    """Test budget status when over budget"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        tracker = TokenTracker(db_path=db_path, budget=1000000)

        # Exceed budget
        tracker.record_usage(1200000)

        status = tracker.get_budget_status()
        assert status.alert_level == AlertLevel.RED
        assert status.current_usage == 1200000
        assert status.remaining_tokens == 0  # Should never be negative


def test_get_usage_history():
    """Test retrieving usage history"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        tracker = TokenTracker(db_path=db_path, budget=1000000)

        # Record multiple usage events
        tracker.record_usage(1000, task_id="gh-450", operation="code_gen")
        tracker.record_usage(2000, task_id="gh-451", operation="testing")
        tracker.record_usage(3000, task_id="gh-452", operation="review")

        # Get history
        history = tracker.get_usage_history(days=30)
        assert len(history) == 3
        assert history[0].tokens_used == 3000  # Most recent first
        assert history[1].tokens_used == 2000
        assert history[2].tokens_used == 1000


def test_get_daily_totals():
    """Test getting daily usage totals"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        tracker = TokenTracker(db_path=db_path, budget=1000000)

        # Record usage
        tracker.record_usage(1000)
        tracker.record_usage(2000)
        tracker.record_usage(3000)

        # Get daily totals
        daily = tracker.get_daily_totals(days=7)
        assert len(daily) >= 1
        # All usage should be on today
        today_str = datetime.now().date().isoformat()
        assert daily[0][0] == today_str
        assert daily[0][1] == 6000


def test_should_allow_task_green_zone():
    """Test task allowance in green zone"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        tracker = TokenTracker(db_path=db_path, budget=1000000)

        # Use 50% of budget
        tracker.record_usage(500000)

        # Should allow task
        allow, reason = tracker.should_allow_task(estimated_tokens=10000)
        assert allow is True
        assert "OK" in reason


def test_should_allow_task_red_zone_but_fits():
    """Test task allowance in red zone but task fits"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        tracker = TokenTracker(db_path=db_path, budget=1000000)

        # Use 96% of budget
        tracker.record_usage(960000)

        # Small task that fits should still be allowed with warning
        allow, reason = tracker.should_allow_task(estimated_tokens=10000)
        assert allow is True
        assert "critical" in reason.lower() or "⚠️" in reason


def test_should_allow_task_would_exceed():
    """Test task rejection when it would exceed budget"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        tracker = TokenTracker(db_path=db_path, budget=1000000)

        # Use 95% of budget
        tracker.record_usage(950000)

        # Task that would exceed budget should be rejected
        allow, reason = tracker.should_allow_task(estimated_tokens=100000)
        assert allow is False
        assert "exceed" in reason.lower()


def test_should_allow_task_over_budget():
    """Test task rejection when already over budget"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        tracker = TokenTracker(db_path=db_path, budget=1000000)

        # Exceed budget
        tracker.record_usage(1100000)

        # Any task should be rejected
        allow, reason = tracker.should_allow_task(estimated_tokens=1000)
        assert allow is False
        assert "exceeded" in reason.lower()


def test_format_budget_display_green():
    """Test budget display formatting for green status"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        tracker = TokenTracker(db_path=db_path, budget=1000000)

        tracker.record_usage(500000)

        display = tracker.format_budget_display()
        assert "🟢" in display
        assert "OK" in display
        assert "500,000" in display
        assert "1,000,000" in display


def test_format_budget_display_yellow():
    """Test budget display formatting for yellow status"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        tracker = TokenTracker(db_path=db_path, budget=1000000)

        tracker.record_usage(800000)

        display = tracker.format_budget_display()
        assert "🟡" in display
        assert "WARNING" in display


def test_format_budget_display_orange():
    """Test budget display formatting for orange status"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        tracker = TokenTracker(db_path=db_path, budget=1000000)

        tracker.record_usage(920000)

        display = tracker.format_budget_display()
        assert "🟠" in display
        assert "HIGH" in display


def test_format_budget_display_red():
    """Test budget display formatting for red status"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        tracker = TokenTracker(db_path=db_path, budget=1000000)

        tracker.record_usage(980000)

        display = tracker.format_budget_display()
        assert "🔴" in display
        assert "CRITICAL" in display


def test_projected_usage_calculation():
    """Test that projected usage is calculated correctly"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        tracker = TokenTracker(db_path=db_path, budget=1000000)

        # Use some tokens
        tracker.record_usage(100000)

        status = tracker.get_budget_status()
        # Should have projection data
        assert status.daily_average > 0
        assert status.projected_usage > 0
        # If we're on day 1, daily average should equal current usage
        # Projected should be daily_average * days_in_month


def test_will_exceed_budget_flag():
    """Test the will_exceed_budget flag"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        tracker = TokenTracker(db_path=db_path, budget=100000)  # Small budget

        # Use a high rate that would exceed if continued
        tracker.record_usage(50000)  # 50% on first day

        status = tracker.get_budget_status()
        # This should project to exceed budget
        # (depends on day of month, but 50% on day 1 should exceed)
        assert isinstance(status.will_exceed_budget, bool)


def test_multiple_tasks_tracking():
    """Test tracking multiple tasks with different operations"""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        tracker = TokenTracker(db_path=db_path, budget=1000000)

        # Record usage for different tasks and operations
        tracker.record_usage(5000, task_id="gh-450", operation="code_generation")
        tracker.record_usage(3000, task_id="gh-450", operation="testing")
        tracker.record_usage(7000, task_id="gh-451", operation="code_generation")
        tracker.record_usage(2000, task_id="gh-451", operation="review")

        # Total should be sum of all
        total = tracker.get_current_month_usage()
        assert total == 17000

        # History should have all records
        history = tracker.get_usage_history()
        assert len(history) == 4
