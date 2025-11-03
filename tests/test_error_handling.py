"""
Tests for error handling and recovery system (adw_modules/error_handling.py)

Verifies all acceptance criteria from issue #452:
- Automatic agent failure detection
- Retry failed agents automatically (3 attempts)
- Dashboard shows agent health status  
- Manual recovery controls available
- Error patterns logged and categorized
- Alert system for repeated failures
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add adws module to path
sys.path.insert(0, str(Path(__file__).parent.parent / "adws"))

from adw_modules.error_handling import (
    FailureType,
    TaskHealth,
    TaskErrorTracking,
    categorize_error,
    format_health_for_dashboard
)


def test_automatic_failure_detection():
    """Test that failures are automatically detected and categorized"""
    # Timeout detection
    assert categorize_error("timeout occurred") == FailureType.TIMEOUT
    
    # Crash detection
    assert categorize_error("failed", context={'exit_code': -9}) == FailureType.CRASH
    
    # Worktree error detection
    assert categorize_error("worktree already exists") == FailureType.WORKTREE_ERROR
    
    # Validation error detection
    assert categorize_error("validation failed") == FailureType.VALIDATION_ERROR
    
    print("✅ Automatic failure detection works")


def test_retry_three_attempts():
    """Test automatic retry with 3 attempts max"""
    tracking = TaskErrorTracking(max_attempts=3)
    
    # Can retry after attempt 1
    tracking.record_failure(FailureType.TIMEOUT)
    assert tracking.can_retry() is True
    assert tracking.attempt_count == 1
    
    # Can retry after attempt 2
    tracking.record_failure(FailureType.TIMEOUT)
    assert tracking.can_retry() is True
    assert tracking.attempt_count == 2
    
    # Cannot retry after attempt 3
    tracking.record_failure(FailureType.TIMEOUT)
    assert tracking.can_retry() is False
    assert tracking.attempt_count == 3
    
    print("✅ Retry logic with 3 attempts works")


def test_dashboard_health_status():
    """Test dashboard shows agent health status"""
    # Healthy task
    tracking = TaskErrorTracking()
    lines = format_health_for_dashboard(tracking)
    assert len(lines) == 0  # No health info for healthy task
    
    # Degraded task (1 failure)
    tracking.record_failure(FailureType.TIMEOUT)
    lines = format_health_for_dashboard(tracking)
    assert any("degraded" in line.lower() for line in lines)
    assert any("Attempt 1/3" in line for line in lines)
    
    # Critical task (2 failures)
    tracking.record_failure(FailureType.CRASH)
    lines = format_health_for_dashboard(tracking)
    assert any("critical" in line.lower() for line in lines)
    assert any("Attempt 2/3" in line for line in lines)
    
    # Dead task (3 failures)
    tracking.record_failure(FailureType.UNKNOWN)
    lines = format_health_for_dashboard(tracking)
    assert any("dead" in line.lower() for line in lines)
    assert any("Attempt 3/3" in line for line in lines)
    
    print("✅ Dashboard health status display works")


def test_manual_recovery_controls():
    """Test manual recovery buttons/controls"""
    tracking = TaskErrorTracking()
    
    # Simulate failures
    tracking.record_failure(FailureType.TIMEOUT)
    tracking.record_failure(FailureType.TIMEOUT)
    tracking.record_failure(FailureType.TIMEOUT)
    
    assert tracking.can_retry() is False  # Max attempts reached
    
    # Manual retry - allows immediate retry
    tracking.manual_retry()
    assert tracking.can_retry() is True
    assert tracking.attempt_count == 0
    assert tracking.is_ready_for_retry() is True
    
    # Re-fail
    tracking.record_failure(FailureType.CRASH)
    
    # Manual reset - clears all history
    tracking.manual_reset()
    assert tracking.attempt_count == 0
    assert tracking.failure_history == []
    assert tracking.last_failure_type is None
    
    print("✅ Manual recovery controls work")


def test_error_categorization():
    """Test error patterns are logged and categorized"""
    tracking = TaskErrorTracking()
    
    # Record different failure types
    tracking.record_failure(FailureType.TIMEOUT)
    tracking.record_failure(FailureType.CRASH)
    tracking.record_failure(FailureType.WORKTREE_ERROR)
    
    # Check failure history
    assert len(tracking.failure_history) == 3
    assert tracking.failure_history[0] == FailureType.TIMEOUT
    assert tracking.failure_history[1] == FailureType.CRASH
    assert tracking.failure_history[2] == FailureType.WORKTREE_ERROR
    assert tracking.last_failure_type == FailureType.WORKTREE_ERROR
    
    print("✅ Error categorization and logging works")


def test_repeated_failure_alerts():
    """Test alert system for repeated failures"""
    tracking = TaskErrorTracking()
    
    # Record repeated failures
    tracking.record_failure(FailureType.TIMEOUT)
    tracking.record_failure(FailureType.TIMEOUT)
    tracking.record_failure(FailureType.TIMEOUT)
    
    # Check for alerts
    alerts = tracking.get_alerts()
    
    # Should have repeated failure alert
    assert any("Repeated timeout" in alert for alert in alerts)
    
    # Should have max attempts alert
    assert any("Max attempts" in alert for alert in alerts)
    assert any("manual intervention" in alert for alert in alerts)
    
    print("✅ Alert system for repeated failures works")


def test_exponential_backoff():
    """Test exponential backoff for retries"""
    tracking = TaskErrorTracking()
    
    # Backoff increases exponentially: 60, 120, 240
    assert tracking.calculate_backoff() == 60
    
    tracking.record_failure(FailureType.TIMEOUT)
    assert tracking.calculate_backoff() == 120
    
    tracking.record_failure(FailureType.TIMEOUT)
    assert tracking.calculate_backoff() == 240
    
    print("✅ Exponential backoff calculation works")


def test_retry_timing():
    """Test tasks wait for backoff before retrying"""
    tracking = TaskErrorTracking()
    tracking.record_failure(FailureType.TIMEOUT)
    
    # Not ready immediately after failure
    assert tracking.is_ready_for_retry() is False
    
    # Ready after backoff period (120s for first attempt)
    tracking.failed_at = datetime.now() - timedelta(seconds=130)
    assert tracking.is_ready_for_retry() is True
    
    print("✅ Retry timing with backoff works")


if __name__ == '__main__':
    print("Testing Error Handling and Recovery System (Issue #452)\n")
    print("="*60)
    
    # Run all tests
    test_automatic_failure_detection()
    test_retry_three_attempts()
    test_dashboard_health_status()
    test_manual_recovery_controls()
    test_error_categorization()
    test_repeated_failure_alerts()
    test_exponential_backoff()
    test_retry_timing()
    
    print("="*60)
    print("\n✅ ALL TESTS PASSED - Issue #452 acceptance criteria met!")
    print("\nAcceptance Criteria Verified:")
    print("  ✅ Automatic agent failure detection")
    print("  ✅ Retry failed agents automatically (3 attempts)")
    print("  ✅ Dashboard shows agent health status")
    print("  ✅ Manual recovery buttons available")
    print("  ✅ Error patterns logged and categorized")
    print("  ✅ Alert system for repeated failures")
