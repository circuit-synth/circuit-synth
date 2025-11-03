# Manual Recovery Guide

**For TAC-8 Coordinator Error Handling System**

This guide explains how to manually intervene when tasks fail or need human assistance.

---

## Quick Reference

### View Task Status

```bash
# View tasks.md dashboard
cat tasks.md

# View specific task health
python3 -c "
from coordinator import Coordinator
c = Coordinator()
tasks = c.parse_tasks_md()
task = next(t for t in tasks if t.id == 'gh-452')
print(f'Health: {task.error_tracking.get_health_status().value}')
print(f'Attempts: {task.error_tracking.attempt_count}/{task.error_tracking.max_attempts}')
"
```

### Manual Retry (Reset Attempts)

When a task reaches max attempts (DEAD status) but you want to retry:

```python
# In Python console or script
from adws.coordinator import Coordinator

c = Coordinator()
tasks = c.parse_tasks_md()

# Find the failed task
task = next(t for t in tasks if t.id == 'gh-452')

# Reset and retry
task.error_tracking.manual_retry()
task.status = 'pending'
task.error = None

# Save changes
c.update_tasks_md(tasks)
```

### Manual Cancel

Cancel a task that's stuck or no longer needed:

```python
from adws.coordinator import Coordinator

c = Coordinator()
tasks = c.parse_tasks_md()

task = next(t for t in tasks if t.id == 'gh-452')

# Cancel the task
task.status = 'cancelled'
task.error = 'User cancelled - no longer needed'

c.update_tasks_md(tasks)
```

### Manual Reset (Clean Slate)

Completely reset a task's error history:

```python
from adws.coordinator import Coordinator

c = Coordinator()
tasks = c.parse_tasks_md()

task = next(t for t in tasks if t.id == 'gh-452')

# Reset everything
task.error_tracking.manual_reset()
task.status = 'pending'
task.error = None

c.update_tasks_md(tasks)
```

---

## Common Scenarios

### Scenario 1: Repeated Worktree Errors

**Symptom**: Task shows "worktree_error" repeated 3 times, status is DEAD.

**Cause**: Git worktree cleanup issue, likely stale directory.

**Solution**:
```bash
# 1. Manually clean up worktree
cd /home/shane/Desktop/circuit-synth
git worktree remove trees/gh-452 --force
rm -rf trees/gh-452  # If directory still exists

# 2. Prune stale references
git worktree prune

# 3. Reset task
python3 -c "
from adws.coordinator import Coordinator
c = Coordinator()
tasks = c.parse_tasks_md()
task = next(t for t in tasks if t.id == 'gh-452')
task.error_tracking.manual_reset()
task.status = 'pending'
c.update_tasks_md(tasks)
print('✅ Task reset and ready to retry')
"
```

### Scenario 2: Repeated Timeouts

**Symptom**: Task shows "timeout" repeated multiple times.

**Cause**: Task is too complex or agent is stuck.

**Solution**:
```bash
# 1. Check if worker is still running
ps aux | grep claude | grep gh-452

# 2. If running, kill it
pkill -f "claude.*gh-452"

# 3. Investigate logs
tail -100 logs/gh-452.jsonl

# 4. Consider:
#    - Simplify the task in GitHub issue
#    - Increase timeout in config
#    - Split into smaller subtasks

# 5. Reset task to retry
python3 -c "
from adws.coordinator import Coordinator
c = Coordinator()
tasks = c.parse_tasks_md()
task = next(t for t in tasks if t.id == 'gh-452')
task.error_tracking.manual_reset()
task.status = 'pending'
c.update_tasks_md(tasks)
"
```

### Scenario 3: PR Creation Failed

**Symptom**: Worker finishes but no PR is created, fails multiple times.

**Cause**: GitHub API issue, authentication problem, or worker logic error.

**Solution**:
```bash
# 1. Check worker output
tail -200 logs/gh-452.jsonl | grep -i pr

# 2. Check if commits were made
cd trees/gh-452
git log -3
git status

# 3. Try creating PR manually
gh pr create --fill

# 4. If successful, mark task as complete
python3 -c "
from adws.coordinator import Coordinator
c = Coordinator()
tasks = c.parse_tasks_md()
task = next(t for t in tasks if t.id == 'gh-452')
task.status = 'completed'
task.pr_url = 'https://github.com/owner/repo/pull/XXX'
c.update_tasks_md(tasks)
"

# 5. If not successful, investigate logs and reset
```

### Scenario 4: Validation Errors

**Symptom**: Task fails with "validation_error" type.

**Cause**: Output doesn't meet expected format or criteria.

**Solution**:
```bash
# 1. Review worker output
python3 tools/view_worker.py 452

# 2. Check what was produced
cd trees/gh-452
ls -la
git diff main

# 3. Investigate validation logic
# (depends on your validation implementation)

# 4. If validation is too strict, adjust validation rules

# 5. Reset task to retry
```

### Scenario 5: Critical Health (2 Failures)

**Symptom**: Task shows "🔴 Health: CRITICAL", 2/3 attempts used.

**Action**: Investigate before final retry!

```bash
# 1. Don't let it fail a 3rd time - investigate first
cat tasks.md | grep -A 5 "gh-452"

# 2. Review failure history
python3 -c "
from adws.coordinator import Coordinator
c = Coordinator()
tasks = c.parse_tasks_md()
task = next(t for t in tasks if t.id == 'gh-452')
print('Failure history:')
for i, failure in enumerate(task.error_tracking.failure_history, 1):
    print(f'  {i}. {failure.value}')
"

# 3. Address root cause before retry
#    - Fix worktree issues
#    - Check GitHub auth
#    - Review task complexity

# 4. Reset attempts to give more chances
python3 -c "
from adws.coordinator import Coordinator
c = Coordinator()
tasks = c.parse_tasks_md()
task = next(t for t in tasks if t.id == 'gh-452')
task.error_tracking.manual_reset()
task.status = 'pending'
c.update_tasks_md(tasks)
"
```

---

## Recovery Scripts

### Script: Reset All Failed Tasks

```python
#!/usr/bin/env python3
"""Reset all DEAD tasks to pending"""

from adws.coordinator import Coordinator

c = Coordinator()
tasks = c.parse_tasks_md()

reset_count = 0
for task in tasks:
    if task.status == 'failed' and task.error_tracking.get_health_status() == TaskHealth.DEAD:
        print(f"Resetting {task.id}")
        task.error_tracking.manual_reset()
        task.status = 'pending'
        task.error = None
        reset_count += 1

if reset_count > 0:
    c.update_tasks_md(tasks)
    print(f"\n✅ Reset {reset_count} tasks")
else:
    print("No tasks to reset")
```

### Script: Cancel All Stuck Tasks

```python
#!/usr/bin/env python3
"""Cancel tasks that have been active too long"""

from adws.coordinator import Coordinator
from datetime import datetime, timedelta

c = Coordinator()
tasks = c.parse_tasks_md()

# Cancel tasks active for more than 2 hours
threshold = datetime.now() - timedelta(hours=2)

cancelled_count = 0
for task in tasks:
    if task.status == 'active' and task.started:
        started_time = datetime.strptime(task.started, '%Y-%m-%d %H:%M:%S')
        if started_time < threshold:
            print(f"Cancelling stuck task {task.id}")
            task.status = 'cancelled'
            task.error = 'Stuck - active for more than 2 hours'
            cancelled_count += 1

if cancelled_count > 0:
    c.update_tasks_md(tasks)
    print(f"\n✅ Cancelled {cancelled_count} stuck tasks")
else:
    print("No stuck tasks found")
```

### Script: Generate Health Report

```python
#!/usr/bin/env python3
"""Generate health report for all tasks"""

from adws.coordinator import Coordinator
from collections import Counter

c = Coordinator()
tasks = c.parse_tasks_md()

print("=" * 60)
print("Task Health Report")
print("=" * 60)
print()

# Overall stats
total = len(tasks)
by_status = Counter(t.status for t in tasks)
by_health = Counter(t.error_tracking.get_health_status().value for t in tasks if hasattr(t, 'error_tracking'))

print(f"Total tasks: {total}")
print()
print("By Status:")
for status, count in by_status.items():
    print(f"  {status}: {count}")
print()

print("By Health:")
for health, count in by_health.items():
    print(f"  {health}: {count}")
print()

# Detailed failure analysis
print("=" * 60)
print("Failure Analysis")
print("=" * 60)
print()

failed_tasks = [t for t in tasks if t.status == 'failed' or t.error_tracking.attempt_count > 0]

if failed_tasks:
    # Count failure types
    all_failures = []
    for task in failed_tasks:
        all_failures.extend(task.error_tracking.failure_history)

    failure_counts = Counter(f.value for f in all_failures)

    print("Failure Type Frequency:")
    for failure_type, count in failure_counts.most_common():
        print(f"  {failure_type}: {count}")
    print()

    # Tasks needing attention
    critical_tasks = [t for t in failed_tasks
                     if t.error_tracking.get_health_status().value in ['critical', 'dead']]

    if critical_tasks:
        print(f"⚠️  {len(critical_tasks)} tasks need attention:")
        for task in critical_tasks:
            health = task.error_tracking.get_health_status()
            print(f"  - {task.id}: {health.value} ({task.error_tracking.attempt_count}/{task.error_tracking.max_attempts} attempts)")
        print()
else:
    print("✅ No failed tasks")

print("=" * 60)
```

---

## Preventive Actions

### Monitor Health Regularly

```bash
# Check health every 5 minutes
watch -n 300 'cat tasks.md | grep -E "(⚠️|🔴|☠️)" || echo "All healthy"'
```

### Set Up Alerts

Add to crontab:
```bash
# Check for DEAD tasks every hour and email
0 * * * * cd /home/shane/Desktop/circuit-synth && python3 -c "
from adws.coordinator import Coordinator
c = Coordinator()
tasks = c.parse_tasks_md()
dead = [t for t in tasks if t.error_tracking.get_health_status().value == 'dead']
if dead:
    print(f'WARNING: {len(dead)} DEAD tasks need attention')
" | mail -s "TAC-8 Alert" you@example.com
```

### Regular Maintenance

Weekly cleanup:
```bash
#!/bin/bash
# Weekly TAC-8 maintenance

cd /home/shane/Desktop/circuit-synth

echo "1. Pruning worktrees..."
git worktree prune

echo "2. Checking for orphaned directories..."
find trees/ -maxdepth 1 -type d -mtime +7  # Show old directories

echo "3. Checking task health..."
python3 -c "
from adws.coordinator import Coordinator
c = Coordinator()
tasks = c.parse_tasks_md()
degraded = [t for t in tasks if t.error_tracking.get_health_status().value != 'healthy']
print(f'{len(degraded)} tasks with health issues')
"

echo "4. Checking logs disk usage..."
du -sh logs/

echo "✅ Maintenance complete"
```

---

## Emergency Procedures

### Stop Everything

```bash
# 1. Stop coordinator
sudo systemctl stop circuit-synth-coordinator

# 2. Kill all workers
pkill -f claude

# 3. Check no processes remain
ps aux | grep claude

# 4. Mark all active tasks as failed
python3 -c "
from adws.coordinator import Coordinator
c = Coordinator()
tasks = c.parse_tasks_md()
for task in tasks:
    if task.status == 'active':
        task.status = 'failed'
        task.error = 'Emergency stop'
c.update_tasks_md(tasks)
"
```

### Clean Slate Reset

```bash
# WARNING: This clears all task state!

cd /home/shane/Desktop/circuit-synth

# 1. Stop coordinator
sudo systemctl stop circuit-synth-coordinator

# 2. Remove all worktrees
git worktree list | grep trees/ | awk '{print $1}' | xargs -I {} git worktree remove {} --force
rm -rf trees/*

# 3. Archive logs
mkdir -p logs/archive/$(date +%Y%m%d)
mv logs/*.jsonl logs/archive/$(date +%Y%m%d)/ 2>/dev/null || true

# 4. Reset tasks.md
cat > tasks.md << 'EOF'
# Circuit-Synth Work Queue

**Last updated:** $(date '+%Y-%m-%d %H:%M:%S')

---

## Pending

<!-- No pending tasks -->

---

## Active (max 3)

<!-- No active tasks -->

---

## Completed Today

<!-- No completed tasks today -->

---

## Failed

<!-- No failed tasks -->

---

## Blocked

<!-- No blocked tasks -->
EOF

# 5. Restart coordinator
sudo systemctl start circuit-synth-coordinator
```

---

## Getting Help

### Debug Checklist

1. ☐ Checked tasks.md for current status
2. ☐ Reviewed logs/gh-XXX.jsonl for details
3. ☐ Verified Git worktree state
4. ☐ Checked GitHub API authentication
5. ☐ Reviewed failure history and patterns
6. ☐ Attempted manual recovery steps
7. ☐ Consulted ERROR_HANDLING_INTEGRATION.md

### Contact Information

- **Documentation**: `adws/ERROR_HANDLING_INTEGRATION.md`
- **Examples**: `adws/example_error_handling_usage.py`
- **GitHub Issues**: Tag @maintainer or create issue with #452 reference
- **Logs**: Always attach logs/gh-XXX.jsonl when reporting issues

---

**Remember**: The error handling system is designed to recover automatically. Manual intervention should only be needed for:
- Repeated failures of the same type (3x)
- Critical health status requiring investigation
- Emergency stops or system maintenance
- Debugging specific issues

Most tasks will retry automatically and succeed without human intervention!
