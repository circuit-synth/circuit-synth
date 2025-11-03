"""
Error handling and recovery system for TAC-8 Coordinator

Provides:
- Error categorization and classification
- Automatic retry with exponential backoff
- Health monitoring and alerts
- Manual recovery controls
"""

from enum import Enum
from dataclasses import dataclass, field
from typing import List, Optional
from datetime import datetime, timedelta


class FailureType(Enum):
    """Categorizes different types of agent failures"""
    TIMEOUT = "timeout"  # Agent exceeded time limit
    CRASH = "crash"  # Agent process crashed
    STUCK = "stuck"  # Agent stuck in infinite loop
    VALIDATION_ERROR = "validation_error"  # Output validation failed
    WORKTREE_ERROR = "worktree_error"  # Git worktree issues
    PR_CREATION_FAILED = "pr_creation_failed"  # Failed to create PR
    STARTUP_ERROR = "startup_error"  # Agent failed to start or exited in <10s
    UNKNOWN = "unknown"  # Unclassified failure


class TaskHealth(Enum):
    """Health status of a task based on failure patterns"""
    HEALTHY = "healthy"  # No failures
    DEGRADED = "degraded"  # 1 failure, recovering
    CRITICAL = "critical"  # 2+ failures, needs attention
    DEAD = "dead"  # Max attempts reached, manual intervention required


@dataclass
class RetryConfig:
    """Configuration for retry behavior"""
    max_attempts: int = 3
    base_backoff_seconds: int = 60  # First retry after 60s
    backoff_multiplier: int = 2  # Doubles each time


@dataclass
class TaskErrorTracking:
    """Tracks error history and retry state for a task"""
    attempt_count: int = 0
    max_attempts: int = 3
    last_failure_type: Optional[FailureType] = None
    failure_history: List[FailureType] = field(default_factory=list)
    failed_at: Optional[datetime] = None
    retry_after: Optional[datetime] = None

    def can_retry(self) -> bool:
        """Check if task can be retried"""
        return self.attempt_count < self.max_attempts

    def calculate_backoff(self) -> int:
        """Calculate exponential backoff delay in seconds

        Returns:
            Delay in seconds: 60 * (2^attempt_count)
            - Attempt 1: ~60 seconds
            - Attempt 2: ~120 seconds
            - Attempt 3: ~240 seconds

        For STARTUP_ERROR failures, use longer backoff to prevent spawn loops:
            - Attempt 1: ~300 seconds (5 min)
            - Attempt 2: ~600 seconds (10 min)
            - Attempt 3: ~1200 seconds (20 min)
        """
        # Use longer backoff for startup errors to prevent spawn loops
        if self.last_failure_type == FailureType.STARTUP_ERROR:
            return 300 * (2 ** self.attempt_count)

        return 60 * (2 ** self.attempt_count)

    def is_ready_for_retry(self) -> bool:
        """Check if backoff period has expired and task is ready to retry"""
        if not self.can_retry():
            return False

        if self.failed_at is None:
            return True

        backoff_seconds = self.calculate_backoff()
        retry_time = self.failed_at + timedelta(seconds=backoff_seconds)
        return datetime.now() >= retry_time

    def get_health_status(self) -> TaskHealth:
        """Determine task health based on failure patterns"""
        if self.attempt_count == 0:
            return TaskHealth.HEALTHY
        elif self.attempt_count == 1:
            return TaskHealth.DEGRADED
        elif self.attempt_count >= self.max_attempts:
            return TaskHealth.DEAD
        else:
            return TaskHealth.CRITICAL

    def has_repeated_failures(self) -> bool:
        """Check if same failure type occurred multiple times"""
        if len(self.failure_history) < 2:
            return False

        # Count occurrences of each failure type
        failure_counts = {}
        for failure in self.failure_history:
            failure_counts[failure] = failure_counts.get(failure, 0) + 1

        # Check if any failure type occurred more than once
        return any(count >= 2 for count in failure_counts.values())

    def get_repeated_failure_type(self) -> Optional[FailureType]:
        """Get the failure type that repeated most"""
        if not self.has_repeated_failures():
            return None

        failure_counts = {}
        for failure in self.failure_history:
            failure_counts[failure] = failure_counts.get(failure, 0) + 1

        # Return failure type with highest count (must be >= 2)
        most_common = max(failure_counts.items(), key=lambda x: x[1])
        return most_common[0] if most_common[1] >= 2 else None

    def get_alerts(self) -> List[str]:
        """Generate alerts based on failure patterns"""
        alerts = []

        # Alert on repeated failures
        if self.has_repeated_failures():
            failure_type = self.get_repeated_failure_type()
            alerts.append(
                f"⚠️ Repeated {failure_type.value} failures detected"
            )

        # Alert on max attempts
        if self.attempt_count >= self.max_attempts:
            alerts.append(
                f"🚨 Max attempts ({self.max_attempts}) reached - manual intervention required"
            )

        # Alert on critical health
        if self.get_health_status() == TaskHealth.CRITICAL:
            alerts.append(
                f"⚠️ Task health is CRITICAL - {self.attempt_count}/{self.max_attempts} attempts"
            )

        return alerts

    def record_failure(self, failure_type: FailureType):
        """Record a failure occurrence"""
        self.attempt_count += 1
        self.last_failure_type = failure_type
        self.failure_history.append(failure_type)
        self.failed_at = datetime.now()

    def manual_retry(self):
        """Manually trigger retry (resets attempt count)"""
        self.attempt_count = 0
        self.failed_at = None
        self.retry_after = None

    def manual_reset(self):
        """Reset to clean state"""
        self.attempt_count = 0
        self.failure_history = []
        self.last_failure_type = None
        self.failed_at = None
        self.retry_after = None


def categorize_error(error_msg: str, context: dict = None) -> FailureType:
    """Categorize an error based on message and context

    Args:
        error_msg: The error message
        context: Optional context dict with keys like 'exit_code', 'duration', etc.

    Returns:
        FailureType enum value
    """
    error_lower = error_msg.lower()

    # Worktree errors
    if 'worktree' in error_lower or 'already exists' in error_lower:
        return FailureType.WORKTREE_ERROR

    # PR creation failures
    if 'pr' in error_lower or 'pull request' in error_lower:
        return FailureType.PR_CREATION_FAILED

    # Validation errors
    if 'validation' in error_lower or 'invalid' in error_lower:
        return FailureType.VALIDATION_ERROR

    # Timeout
    if 'timeout' in error_lower or 'timed out' in error_lower:
        return FailureType.TIMEOUT

    # Process crash
    if context and 'exit_code' in context:
        exit_code = context['exit_code']
        if exit_code < 0:  # Signal termination
            return FailureType.CRASH

    # Stuck detection (if duration is very long)
    if context and 'duration' in context:
        if context['duration'] > 3600:  # More than 1 hour
            return FailureType.STUCK

    return FailureType.UNKNOWN


def format_health_for_dashboard(tracking: TaskErrorTracking) -> List[str]:
    """Format health and retry info for tasks.md display"""
    lines = []

    if tracking.attempt_count == 0:
        return lines  # Healthy task, no extra info needed

    health = tracking.get_health_status()
    health_icon = {
        TaskHealth.HEALTHY: "✅",
        TaskHealth.DEGRADED: "⚠️",
        TaskHealth.CRITICAL: "🔴",
        TaskHealth.DEAD: "☠️"
    }[health]

    lines.append(f"  {health_icon} Attempt {tracking.attempt_count}/{tracking.max_attempts}, Health: {health.value}")

    if tracking.failed_at and not tracking.is_ready_for_retry():
        backoff = tracking.calculate_backoff()
        elapsed = (datetime.now() - tracking.failed_at).total_seconds()
        remaining = max(0, backoff - elapsed)
        lines.append(f"  ⏳ Retry in {int(remaining)}s")
    elif tracking.failed_at and tracking.is_ready_for_retry():
        lines.append(f"  ✓ Ready for retry")

    if tracking.last_failure_type:
        lines.append(f"  ⚠️ Last failure: {tracking.last_failure_type.value}")

    # Show alerts if any
    alerts = tracking.get_alerts()
    for alert in alerts:
        lines.append(f"  {alert}")

    return lines
