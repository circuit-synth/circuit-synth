# Error Handling and Recovery System Integration Guide

**Status**: Implementation Complete
**Issue**: #452
**Date**: November 2, 2025

## Overview

This document describes the agent error handling and recovery system implemented for the TAC-8 Coordinator. The system provides:

✅ **Automatic failure detection** - Categorizes failures by type
✅ **Retry logic with exponential backoff** - Retries failed tasks automatically (3 attempts)
✅ **Health monitoring** - Tracks task health status
✅ **Manual recovery controls** - Manual retry, cancel, and reset capabilities
✅ **Error alerting** - Alerts for repeated failures and critical states
✅ **Dashboard integration** - Visual health status in tasks.md

---

## Architecture

### Core Components

```
adw_modules/error_handling.py
├── FailureType (Enum) - Error categorization
├── TaskHealth (Enum) - Health status levels
├── TaskErrorTracking (Class) - Per-task error tracking
├── categorize_error() - Error classification
└── format_health_for_dashboard() - Display formatting
```

### Error Categories

```python
class FailureType(Enum):
    TIMEOUT = "timeout"              # Agent exceeded time limit
    CRASH = "crash"                  # Process crashed
    STUCK = "stuck"                  # Infinite loop detection
    VALIDATION_ERROR = "validation"   # Output validation failed
    WORKTREE_ERROR = "worktree"      # Git worktree issues
    PR_CREATION_FAILED = "pr_failed"  # PR creation failed
    UNKNOWN = "unknown"               # Unclassified
```

### Health Levels

```python
class TaskHealth(Enum):
    HEALTHY = "healthy"     # No failures
    DEGRADED = "degraded"   # 1 failure
    CRITICAL = "critical"   # 2 failures
    DEAD = "dead"           # Max attempts reached
```

---

## Integration Steps

### Step 1: Extend Task Dataclass

Add error tracking to the `Task` dataclass in `coordinator.py`:

```python
from adw_modules import TaskErrorTracking

@dataclass
class Task:
    # ... existing fields ...

    # Add error tracking
    error_tracking: TaskErrorTracking = field(default_factory=TaskErrorTracking)
```

### Step 2: Update check_completions()

Integrate failure handling in the completion checker:

```python
def check_completions(self, tasks: List[Task]) -> List[Task]:
    """Check if active workers have completed"""
    for task in tasks:
        # ... existing checks ...

        if worker_failed:
            # Categorize the failure
            failure_type = categorize_error(error_msg, context={
                'exit_code': proc.returncode,
                'duration': elapsed_time
            })

            # Record failure
            task.error_tracking.record_failure(failure_type)

            # Check if can retry
            if task.error_tracking.can_retry():
                task.status = 'pending'  # Will retry after backoff
                backoff = task.error_tracking.calculate_backoff()
                print(f"   🔄 Will retry in {backoff}s")
            else:
                task.status = 'failed'  # Max attempts reached
                print(f"   ❌ Failed permanently")

                # Generate alerts
                alerts = task.error_tracking.get_alerts()
                for alert in alerts:
                    print(f"   {alert}")
```

### Step 3: Update Main Loop for Retry Logic

Respect backoff periods when launching workers:

```python
def run(self):
    while self.running:
        # ... fetch tasks ...

        # Filter pending tasks by retry readiness
        pending = [t for t in tasks if t.status == 'pending']
        pending_ready = [t for t in pending
                        if t.error_tracking.is_ready_for_retry()]
        pending_backoff = [t for t in pending
                          if not t.error_tracking.is_ready_for_retry()]

        # Log tasks still in backoff
        for task in pending_backoff:
            if task.error_tracking.failed_at:
                backoff = task.error_tracking.calculate_backoff()
                elapsed = (datetime.now() - task.error_tracking.failed_at).total_seconds()
                remaining = max(0, backoff - elapsed)
                print(f"⏳ Task {task.id} in backoff: {int(remaining)}s")

        # Launch only ready tasks
        for task in pending_ready[:available_slots]:
            if task.error_tracking.attempt_count > 0:
                print(f"🔄 Retry attempt {task.error_tracking.attempt_count + 1}")
            # ... spawn worker ...
```

### Step 4: Update tasks.md Formatting

Show health and retry info in the dashboard:

```python
from adw_modules import format_health_for_dashboard

def update_tasks_md(self, tasks: List[Task]):
    # ... generate task sections ...

    # Pending section with health info
    for task in pending_tasks:
        lines.append(f"[] {task.id}: {task.description}")

        # Add health and retry info
        health_lines = format_health_for_dashboard(task.error_tracking)
        lines.extend(health_lines)
        lines.append("")

    # Failed section with detailed history
    for task in failed_tasks:
        health = task.error_tracking.get_health_status()
        icon = "☠️" if health == TaskHealth.DEAD else "❌"

        lines.append(f"[{icon}] {task.id}: {task.description}")
        lines.append(f"- Attempts: {task.error_tracking.attempt_count}/{task.error_tracking.max_attempts}")

        # Show failure history
        if task.error_tracking.failure_history:
            types = [f.value for f in task.error_tracking.failure_history]
            lines.append(f"- Failure types: {', '.join(types)}")

        # Show alerts
        for alert in task.error_tracking.get_alerts():
            lines.append(f"- {alert}")
```

---

## Manual Recovery Controls

### Retry a Failed Task

```python
# Reset attempt counter and retry immediately
task.error_tracking.manual_retry()
task.status = 'pending'
```

### Cancel a Task

```python
# Mark as cancelled
task.status = 'cancelled'
task.error = "User requested cancellation"
```

### Reset Task to Clean State

```python
# Clear all error history
task.error_tracking.manual_reset()
task.status = 'pending'
```

---

## Dashboard Display

### tasks.md Format

#### Pending Tasks (with retry info)

```markdown
## Pending

[] gh-452: Dashboard error handling {p1}
  ⚠️ Attempt 1/3, Health: degraded
  ⏳ Retry in 45s
  ⚠️ Last failure: worktree_error
```

#### Failed Tasks (with alerts)

```markdown
## Failed

[☠️ w-abc123] gh-450: Test task
- Attempts: 3/3
- Failure types: timeout, timeout, crash
- ⚠️ Repeated timeout failures detected
- 🚨 Max attempts (3) reached - manual intervention required
```

---

## Testing

### Unit Tests

Run the test suite:

```bash
# Note: pytest not available in current environment
# Tests are located in: tests/test_coordinator_error_handling.py

python3 -m tests.test_coordinator_error_handling
```

### Manual Testing

1. **Test Retry Logic**:
   ```python
   # Create a task that will fail
   task = Task(id="gh-test", ...)
   task.error_tracking.record_failure(FailureType.TIMEOUT)

   # Check backoff calculation
   assert task.error_tracking.calculate_backoff() == 60
   assert not task.error_tracking.is_ready_for_retry()  # Too soon
   ```

2. **Test Health Monitoring**:
   ```python
   # Simulate multiple failures
   task.error_tracking.record_failure(FailureType.TIMEOUT)
   assert task.error_tracking.get_health_status() == TaskHealth.DEGRADED

   task.error_tracking.record_failure(FailureType.TIMEOUT)
   assert task.error_tracking.get_health_status() == TaskHealth.CRITICAL

   task.error_tracking.record_failure(FailureType.CRASH)
   assert task.error_tracking.get_health_status() == TaskHealth.DEAD
   ```

3. **Test Alerts**:
   ```python
   # Repeated failures trigger alerts
   for _ in range(3):
       task.error_tracking.record_failure(FailureType.TIMEOUT)

   alerts = task.error_tracking.get_alerts()
   assert any("repeated" in a.lower() for a in alerts)
   assert any("max attempts" in a.lower() for a in alerts)
   ```

---

## Configuration

### Adjust Retry Parameters

Modify defaults in `error_handling.py`:

```python
@dataclass
class TaskErrorTracking:
    max_attempts: int = 3  # Change to 5 for more retries
    # ...

    def calculate_backoff(self) -> int:
        # Change formula for different backoff strategy
        return 60 * (2 ** self.attempt_count)  # Exponential
        # OR
        return 60 * self.attempt_count  # Linear
        # OR
        return 60  # Fixed
```

---

## Monitoring and Alerts

### Console Output

The coordinator logs provide real-time monitoring:

```
🏁 Worker w-abc123 finished for gh-452
   ⚠️ Failed (attempt 1/3): worktree_error
   🔄 Will retry in 60s

⏳ Task gh-452 in backoff: 45s remaining

🔄 Retry attempt 2/3 for gh-452
🤖 Spawning worker for gh-452

🏁 Worker w-def456 finished for gh-452
   ❌ Failed permanently after 3 attempts: timeout
   ⚠️ Repeated timeout failures detected
   🚨 Max attempts (3) reached - manual intervention required
```

### tasks.md Dashboard

Monitor health visually in `tasks.md`:
- ✅ = Healthy (no failures)
- ⚠️ = Degraded (1 failure)
- 🔴 = Critical (2 failures)
- ☠️ = Dead (max attempts reached)

---

## Future Enhancements

### Potential Improvements

1. **Adaptive Backoff**: Adjust backoff based on failure type
   - Worktree errors: Short backoff (30s)
   - Timeouts: Medium backoff (60s)
   - Crashes: Long backoff (120s)

2. **Failure Pattern Detection**: ML-based failure prediction
   - Learn which tasks are likely to fail
   - Preemptively allocate more resources

3. **Notification System**: External alerts
   - Email on repeated failures
   - Slack integration for DEAD tasks
   - GitHub issue comments for critical health

4. **Recovery Strategies**: Smart recovery
   - Auto-cleanup for worktree errors
   - Resource allocation for timeout errors
   - Automatic debugging for crashes

5. **Metrics and Analytics**:
   - Track failure rates over time
   - Identify problematic issue patterns
   - Optimize backoff parameters

---

## Troubleshooting

### Common Issues

**Q: Task stuck in pending with backoff?**
A: This is normal. The task will retry automatically when the backoff period expires. Check the countdown in console or tasks.md.

**Q: Task shows DEAD status but still retrying?**
A: Use `manual_reset()` to clear error state and restart from clean state.

**Q: Alerts not showing in tasks.md?**
A: Ensure you're calling `format_health_for_dashboard()` when generating the tasks.md content.

**Q: Want different backoff timing?**
A: Modify `calculate_backoff()` in `TaskErrorTracking` class.

---

## Summary

The error handling system is fully implemented and ready for integration. Key features:

✅ **Automatic retry** - 3 attempts with 60s/120s/240s backoff
✅ **Error categorization** - 7 failure types
✅ **Health monitoring** - 4 health levels (healthy → dead)
✅ **Manual controls** - Retry, cancel, reset
✅ **Dashboard integration** - Visual health indicators
✅ **Alert system** - Repeated failure and critical state alerts

**Next Steps**:
1. Integrate into coordinator.py following steps above
2. Test with real workloads
3. Monitor dashboard for health indicators
4. Adjust retry parameters based on observed patterns

**Documentation**: See `adw_modules/error_handling.py` for implementation details.
