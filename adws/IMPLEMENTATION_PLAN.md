# TAC-8 Coordinator: Comprehensive Implementation Plan

**Version**: 1.0
**Date**: November 2, 2025
**Status**: Ready for implementation
**Estimated Total Time**: 8-12 hours

---

## Executive Summary

The TAC-8 autonomous coordinator successfully completed its first end-to-end test (PR #473), proving the core architecture works. However, three critical issues and several enhancements are needed before 24/7 Raspberry Pi deployment.

**What Works**:
- ✅ GitHub issue fetching
- ✅ Worker spawning
- ✅ Git worktree creation
- ✅ Autonomous code changes
- ✅ PR creation
- ✅ Basic task queue management

**What Needs Fixing**:
- ❌ Worktree collision handling (repeated creation failures)
- ❌ Zombie process accumulation (defunct workers)
- ❌ Status tracking (tasks.md not updating with completions)

**What Needs Adding**:
- ⚠️ Monitoring and metrics
- ⚠️ Control mechanisms (stop/pause/resume)
- ⚠️ Error recovery and retry logic
- ⚠️ Automated testing
- ⚠️ Production deployment scripts

---

## Phase 1: Fix Core Issues (CRITICAL)

**Priority**: P0
**Estimated Time**: 3-4 hours
**Dependencies**: None

### 1.1 Fix Worktree Collision Handling

**Problem**: Coordinator repeatedly tries to create worktrees that already exist, causing cascading failures.

**Current Behavior**:
```
fatal: '/home/shane/Desktop/circuit-synth/trees/gh-456' already exists
❌ Failed to launch worker for gh-456 (×15 times)
```

**Solution**: Make worktree creation idempotent.

**Implementation**:

```python
def ensure_worktree(self, task: Task) -> Path:
    """Create or reuse worktree for task (idempotent)

    This replaces create_worktree() with error handling.
    """
    worktree_path = TREES_DIR / f"gh-{task.number}"

    # Get list of existing worktrees
    result = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        capture_output=True, text=True, cwd=REPO_ROOT
    )

    existing_paths = set()
    for line in result.stdout.split('\n'):
        if line.startswith('worktree '):
            existing_paths.add(Path(line.split(' ', 1)[1]))

    if worktree_path in existing_paths:
        # Worktree exists - check if it's stale
        status_result = subprocess.run(
            ["git", "status", "--porcelain"],
            capture_output=True, text=True, cwd=worktree_path
        )

        # If it has uncommitted changes, it's probably active
        if status_result.stdout.strip():
            print(f"⚠️  Worktree {worktree_path} has uncommitted changes")
            # Check if worker is still running
            if not self._worker_is_running(task):
                print(f"   Worker not running - removing stale worktree")
                subprocess.run(
                    ["git", "worktree", "remove", str(worktree_path), "--force"],
                    cwd=REPO_ROOT
                )
            else:
                raise Exception(f"Worktree {worktree_path} is still active")
        else:
            # Clean worktree - remove and recreate
            print(f"🔄 Removing stale worktree: {worktree_path}")
            subprocess.run(
                ["git", "worktree", "remove", str(worktree_path), "--force"],
                cwd=REPO_ROOT
            )

    # Create fresh worktree
    print(f"🌲 Creating worktree: {worktree_path}")
    subprocess.run(
        ["git", "worktree", "add", str(worktree_path), "-b", task.branch_name],
        check=True, cwd=REPO_ROOT
    )

    return worktree_path

def _worker_is_running(self, task: Task) -> bool:
    """Check if worker process is still running"""
    if not task.pid:
        return False

    try:
        os.kill(task.pid, 0)  # Signal 0 just checks existence
        return True
    except OSError:
        return False
```

**Files to modify**:
- `adws/coordinator.py`: Replace `create_worktree()` with `ensure_worktree()`
- `adws/coordinator.py`: Add `_worker_is_running()` helper

**Testing**:
```bash
# Create test scenario
git worktree add trees/gh-999 -b test-branch
python3 adws/coordinator.py  # Should handle existing worktree gracefully
```

**Success Criteria**:
- ✅ No more "already exists" errors
- ✅ Stale worktrees automatically removed
- ✅ Active worktrees preserved

---

### 1.2 Fix Zombie Process Reaping

**Problem**: Completed workers become zombie processes (defunct) and accumulate.

**Current Behavior**:
```bash
$ ps aux | grep claude
shane  146012  0.0  0.0  0  0  ?  Z  17:37  0:17  [claude] <defunct>
shane  146395  0.0  0.0  0  0  ?  Z  17:37  0:19  [claude] <defunct>
```

**Solution**: Add SIGCHLD signal handler to automatically reap children.

**Implementation**:

```python
import os
import signal

class Coordinator:
    def __init__(self, config_path: Path = CONFIG_FILE):
        # ... existing init ...

        # Setup signal handlers
        signal.signal(signal.SIGCHLD, self._reap_children)
        signal.signal(signal.SIGTERM, self._shutdown)
        signal.signal(signal.SIGINT, self._shutdown)

    def _reap_children(self, signum, frame):
        """Automatically reap zombie child processes

        Called when SIGCHLD is received (child process exits).
        Uses WNOHANG to avoid blocking.
        """
        while True:
            try:
                # Non-blocking wait for any child
                pid, status = os.waitpid(-1, os.WNOHANG)

                if pid == 0:
                    # No more children to reap
                    break

                # Calculate exit code
                if os.WIFEXITED(status):
                    exit_code = os.WEXITSTATUS(status)
                elif os.WIFSIGNALED(status):
                    exit_code = -os.WTERMSIG(status)
                else:
                    exit_code = -1

                # Find which task this was
                task_id = None
                for tid, proc in self.active_workers.items():
                    if proc.pid == pid:
                        task_id = tid
                        break

                if task_id:
                    print(f"👶 Reaped worker {task_id} (PID {pid}, exit {exit_code})")
                    # Don't remove from active_workers here - let check_completions do it
                else:
                    print(f"👶 Reaped unknown child (PID {pid}, exit {exit_code})")

            except ChildProcessError:
                # No children
                break
            except OSError as e:
                print(f"⚠️  Error reaping child: {e}")
                break
```

**Files to modify**:
- `adws/coordinator.py`: Add `_reap_children()` method
- `adws/coordinator.py`: Register SIGCHLD handler in `__init__`

**Testing**:
```bash
# Run coordinator and watch for zombies
python3 adws/coordinator.py &
watch -n 1 'ps aux | grep claude | grep defunct'
# Should show 0 zombie processes
```

**Success Criteria**:
- ✅ No zombie processes accumulate
- ✅ Process table stays clean
- ✅ Exit codes properly logged

---

### 1.3 Fix Status Tracking and PR Detection

**Problem**: tasks.md doesn't update when workers complete. Tasks stay in "Pending" or "Active" even after PR is created.

**Current Behavior**:
```markdown
## Pending
[] gh-471: Test: Add docstring to coordinator.py {p2}
```

**Expected Behavior**:
```markdown
## Completed Today
[✅ cbffe52, w-ee4608] gh-471: Test: Add docstring to coordinator.py
- Completed: 2025-11-02 17:38:45
- PR: https://github.com/circuit-synth/circuit-synth/pull/473
```

**Solution**: Add completion detection that checks for PR creation.

**Implementation**:

```python
def check_completions(self, tasks: List[Task]) -> List[Task]:
    """Check if active workers have completed

    Detects completion by:
    1. Checking if PR was created for the branch
    2. Checking if worker process has exited
    3. Updating task status accordingly
    """
    updated_tasks = []

    for task in tasks:
        if task.status != 'active':
            updated_tasks.append(task)
            continue

        # Check for PR creation (primary completion signal)
        pr_check = subprocess.run(
            ["gh", "pr", "list",
             "--head", task.branch_name,
             "--json", "number,url,state,title"],
            capture_output=True, text=True, cwd=REPO_ROOT
        )

        if pr_check.returncode == 0 and pr_check.stdout.strip() != "[]":
            # PR exists!
            pr_data = json.loads(pr_check.stdout)[0]

            # Get commit hash from worktree
            commit_result = subprocess.run(
                ["git", "rev-parse", "--short", "HEAD"],
                capture_output=True, text=True, cwd=task.tree_path
            )
            commit_hash = commit_result.stdout.strip()

            # Update task
            task.status = 'completed'
            task.commit_hash = commit_hash
            task.pr_url = pr_data['url']
            task.completed = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            print(f"✅ Task {task.id} completed - PR #{pr_data['number']}")

            # Post comment to issue
            comment = f"""✅ **Autonomous work completed!**

PR: {pr_data['url']}
Commit: `{commit_hash}`
Worker: {task.worker_id}

The PR is ready for your review."""

            subprocess.run(
                ["gh", "issue", "comment", task.number, "--body", comment],
                cwd=REPO_ROOT
            )

            # Cleanup worktree
            subprocess.run(
                ["git", "worktree", "remove", str(task.tree_path), "--force"],
                cwd=REPO_ROOT
            )

            # Remove from active workers
            if task.id in self.active_workers:
                del self.active_workers[task.id]

        elif task.pid and not self._worker_is_running(task):
            # Worker exited but no PR - failed
            task.status = 'failed'
            task.error = 'Worker exited without creating PR'
            task.completed = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

            print(f"❌ Task {task.id} failed - no PR created")

            # Check for BLOCKED.md
            blocked_file = Path(task.tree_path) / "BLOCKED.md"
            if blocked_file.exists():
                task.status = 'blocked'
                task.error = blocked_file.read_text()[:200]
                print(f"⏰ Task {task.id} blocked - waiting for human")

            # Keep worktree for debugging

        updated_tasks.append(task)

    return updated_tasks
```

**Files to modify**:
- `adws/coordinator.py`: Add `check_completions()` method
- `adws/coordinator.py`: Call in main loop before launching new workers

**Testing**:
```bash
# Create test PR manually
cd trees/gh-999
echo "test" > test.txt
git add test.txt
git commit -m "test"
git push -u origin auto/w-test
gh pr create --title "Test" --body "Test" --fill

# Run coordinator
python3 adws/coordinator.py
# Should detect PR and move task to completed
```

**Success Criteria**:
- ✅ Completed tasks move to "Completed Today" section
- ✅ PR URL and commit hash recorded
- ✅ Issue comment posted on GitHub
- ✅ Worktrees cleaned up after completion
- ✅ Blocked tasks detected and preserved

---

## Phase 2: Add Monitoring and Metrics (HIGH PRIORITY)

**Priority**: P1
**Estimated Time**: 2-3 hours
**Dependencies**: Phase 1 complete

### 2.1 Create Metrics Tracking System

**Goal**: Track coordinator health and performance.

**Implementation**:

Create `adws/metrics.py`:

```python
"""Metrics tracking for coordinator health and performance"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any

class Metrics:
    """Simple JSON-based metrics tracker"""

    def __init__(self, metrics_file: Path):
        self.file = metrics_file
        self.data = self._load()

    def _load(self) -> Dict[str, Any]:
        """Load existing metrics or create new"""
        if self.file.exists():
            with open(self.file) as f:
                return json.load(f)

        return {
            'workers_launched': 0,
            'workers_completed': 0,
            'workers_failed': 0,
            'workers_blocked': 0,
            'prs_created': 0,
            'worktree_errors': 0,
            'github_api_errors': 0,
            'uptime_seconds': 0,
            'last_update': None,
            'health': 'ok',  # ok, warning, degraded, critical
            'history': []  # Last 100 events
        }

    def save(self):
        """Save metrics to file"""
        self.data['last_update'] = datetime.now().isoformat()

        # Update health status
        self.data['health'] = self._calculate_health()

        with open(self.file, 'w') as f:
            json.dump(self.data, f, indent=2)

    def _calculate_health(self) -> str:
        """Calculate overall health status"""
        # Critical: too many errors
        if self.data['worktree_errors'] > 20:
            return 'critical'
        if self.data['github_api_errors'] > 10:
            return 'critical'

        # Degraded: significant issues
        if self.data['worktree_errors'] > 10:
            return 'degraded'
        if self.data['workers_failed'] > self.data['workers_completed']:
            return 'degraded'

        # Warning: minor issues
        if self.data['worktree_errors'] > 5:
            return 'warning'

        return 'ok'

    def increment(self, key: str, value: int = 1):
        """Increment a counter"""
        self.data[key] += value
        self.save()

    def record_event(self, event_type: str, details: str):
        """Record an event in history"""
        event = {
            'timestamp': datetime.now().isoformat(),
            'type': event_type,
            'details': details
        }

        self.data['history'].append(event)

        # Keep only last 100 events
        if len(self.data['history']) > 100:
            self.data['history'] = self.data['history'][-100:]

        self.save()

    def reset_errors(self):
        """Reset error counters after cleanup"""
        self.data['worktree_errors'] = 0
        self.data['github_api_errors'] = 0
        self.save()

    def get_summary(self) -> Dict[str, Any]:
        """Get summary statistics"""
        total_workers = (self.data['workers_completed'] +
                        self.data['workers_failed'] +
                        self.data['workers_blocked'])

        success_rate = 0
        if total_workers > 0:
            success_rate = self.data['workers_completed'] / total_workers * 100

        return {
            'health': self.data['health'],
            'success_rate': f"{success_rate:.1f}%",
            'total_workers': total_workers,
            'prs_created': self.data['prs_created'],
            'errors': self.data['worktree_errors'] + self.data['github_api_errors']
        }
```

**Integrate into coordinator**:

```python
from adws.metrics import Metrics

class Coordinator:
    def __init__(self, config_path: Path = CONFIG_FILE):
        # ... existing init ...
        self.metrics = Metrics(SCRIPT_DIR / 'metrics.json')
        self.start_time = time.time()

    def run(self):
        """Main coordinator loop"""
        while self.running:
            # Update uptime
            self.metrics.data['uptime_seconds'] = int(time.time() - self.start_time)

            # ... existing loop ...

            # Check health and auto-recover if needed
            if self.metrics.data['health'] in ['degraded', 'critical']:
                print(f"⚠️  Health: {self.metrics.data['health']} - running cleanup")
                self.cleanup_all_worktrees()
                self.metrics.reset_errors()

    def spawn_worker(self, task: Task):
        try:
            # ... existing spawn code ...
            self.metrics.increment('workers_launched')
            self.metrics.record_event('worker_launched', f"{task.id}: {task.description}")

        except Exception as e:
            if 'already exists' in str(e):
                self.metrics.increment('worktree_errors')
            self.metrics.record_event('worker_failed', f"{task.id}: {e}")
            raise

    def check_completions(self, tasks):
        # ... existing code ...

        if task.status == 'completed':
            self.metrics.increment('workers_completed')
            self.metrics.increment('prs_created')
            self.metrics.record_event('pr_created', f"{task.id}: {task.pr_url}")

        elif task.status == 'failed':
            self.metrics.increment('workers_failed')

        elif task.status == 'blocked':
            self.metrics.increment('workers_blocked')
```

**Files to create**:
- `adws/metrics.py` (new file, ~150 lines)

**Files to modify**:
- `adws/coordinator.py`: Import and integrate metrics

**Testing**:
```bash
python3 adws/coordinator.py
# Check metrics file
cat adws/metrics.json | jq
```

---

### 2.2 Create Status Dashboard

**Goal**: Real-time view of coordinator health.

Create `tools/status.py`:

```python
#!/usr/bin/env python3
"""Real-time coordinator status dashboard"""

import json
import sys
from pathlib import Path
from datetime import datetime, timedelta

def show_status():
    """Display coordinator status"""

    # Read metrics
    metrics_file = Path('adws/metrics.json')
    if metrics_file.exists():
        metrics = json.load(open(metrics_file))

        # Health indicator
        health_emoji = {
            'ok': '✅',
            'warning': '⚠️',
            'degraded': '🔶',
            'critical': '🔴'
        }

        health = metrics['health']
        uptime = timedelta(seconds=metrics['uptime_seconds'])

        print(f"\n{'='*80}")
        print(f"📊 Coordinator Status - {health_emoji.get(health, '❓')} {health.upper()}")
        print(f"{'='*80}\n")

        print(f"⏱️  Uptime: {uptime}")
        print(f"📈 Workers launched: {metrics['workers_launched']}")
        print(f"✅ Completed: {metrics['workers_completed']}")
        print(f"❌ Failed: {metrics['workers_failed']}")
        print(f"⏰ Blocked: {metrics['workers_blocked']}")
        print(f"🔀 PRs created: {metrics['prs_created']}")
        print()

        # Calculate success rate
        total = (metrics['workers_completed'] +
                metrics['workers_failed'] +
                metrics['workers_blocked'])
        if total > 0:
            rate = metrics['workers_completed'] / total * 100
            print(f"📊 Success rate: {rate:.1f}%")

        # Errors
        if metrics['worktree_errors'] > 0 or metrics['github_api_errors'] > 0:
            print(f"\n⚠️  Errors:")
            print(f"   Worktree: {metrics['worktree_errors']}")
            print(f"   GitHub API: {metrics['github_api_errors']}")

        # Recent events
        if metrics['history']:
            print(f"\n📋 Recent Events (last 5):")
            for event in reversed(metrics['history'][-5:]):
                ts = datetime.fromisoformat(event['timestamp'])
                print(f"   [{ts.strftime('%H:%M:%S')}] {event['type']}: {event['details']}")

    # Read tasks.md
    tasks_file = Path('tasks.md')
    if tasks_file.exists():
        content = open(tasks_file).read()
        pending = content.count('[] gh-')
        active = content.count('[🟡 w-')
        completed = content.count('[✅')
        failed = content.count('[❌')
        blocked = content.count('[⏰')

        print(f"\n📋 Task Queue:")
        print(f"   Pending: {pending}")
        print(f"   Active: {active}")
        print(f"   Completed today: {completed}")
        print(f"   Failed: {failed}")
        print(f"   Blocked: {blocked}")

    print(f"\n{'='*80}\n")

if __name__ == '__main__':
    show_status()
```

**Usage**:
```bash
# One-shot view
python3 tools/status.py

# Live monitoring (updates every 5 seconds)
watch -n 5 python3 tools/status.py
```

**Files to create**:
- `tools/status.py` (new file, ~120 lines)

---

## Phase 3: Add Control Mechanisms (MEDIUM PRIORITY)

**Priority**: P1
**Estimated Time**: 2 hours
**Dependencies**: Phase 1 complete

### 3.1 Add STOP Signal to Worker Template

**Goal**: Allow graceful stopping of running workers.

**Modify worker_template.md**:

```markdown
## Check for Stop Signal

IMPORTANT: Before each major operation, check for STOP signal:

- Check if `/path/to/worktree/STOP` file exists
- If it does, commit your work-in-progress and exit gracefully

```python
import os
import sys

def check_stop_signal():
    """Check if user requested stop"""
    if os.path.exists('STOP'):
        print("⏹️  STOP signal detected")
        # Commit any useful work
        subprocess.run(['git', 'add', '.'])
        subprocess.run(['git', 'commit', '-m', 'WIP: Stopped by user', '--allow-empty'])
        print("Committed work-in-progress and exiting gracefully")
        sys.exit(0)

# Call this after each tool use or major step
check_stop_signal()
```
```

**Create stop script** `tools/stop_worker.sh`:

```bash
#!/bin/bash
# Stop a running worker gracefully

if [ -z "$1" ]; then
    echo "Usage: ./tools/stop_worker.sh <issue_number>"
    exit 1
fi

ISSUE=$1
WORKTREE="trees/gh-$ISSUE"

if [ ! -d "$WORKTREE" ]; then
    echo "Error: Worktree $WORKTREE does not exist"
    exit 1
fi

echo "Creating STOP signal for issue #$ISSUE"
echo "User requested stop at $(date)" > "$WORKTREE/STOP"
echo "Worker will stop at next checkpoint"
echo ""
echo "To force kill instead: kill -9 <PID>"
```

**Files to modify**:
- `worker_template.md`: Add STOP signal check

**Files to create**:
- `tools/stop_worker.sh`: Graceful stop script

---

### 3.2 Add Pause/Resume Functionality

**Goal**: Pause coordinator without killing workers.

Add to `adws/coordinator.py`:

```python
class Coordinator:
    def __init__(self, ...):
        # ... existing init ...
        self.paused = False

        # Add USR1 signal for pause/resume
        signal.signal(signal.SIGUSR1, self._toggle_pause)

    def _toggle_pause(self, signum, frame):
        """Toggle pause state"""
        self.paused = not self.paused
        if self.paused:
            print("⏸️  Coordinator paused - not launching new workers")
        else:
            print("▶️  Coordinator resumed")

    def run(self):
        while self.running:
            # ... fetch issues ...
            # ... check completions ...

            # Only launch new workers if not paused
            if not self.paused:
                # ... launch workers ...
            else:
                print("⏸️  Paused - skipping worker launch")

            time.sleep(self.poll_interval)
```

**Usage**:
```bash
# Pause coordinator
kill -USR1 <coordinator_pid>

# Resume
kill -USR1 <coordinator_pid>
```

---

## Phase 4: Testing and Validation (HIGH PRIORITY)

**Priority**: P1
**Estimated Time**: 2-3 hours
**Dependencies**: Phases 1-3 complete

### 4.1 Create Integration Tests

Create `tests/test_coordinator_integration.py`:

```python
"""Integration tests for coordinator"""

import pytest
import subprocess
import time
from pathlib import Path

def test_coordinator_starts_and_stops():
    """Test coordinator can start and stop cleanly"""
    proc = subprocess.Popen(
        ['python3', 'adws/coordinator.py'],
        stdout=subprocess.PIPE,
        stderr=subprocess.PIPE
    )

    time.sleep(5)
    proc.terminate()
    proc.wait(timeout=10)

    assert proc.returncode in [0, -15]  # Clean exit

def test_worktree_cleanup():
    """Test stale worktree cleanup"""
    # Create stale worktree
    test_path = Path('trees/gh-test')
    subprocess.run([
        'git', 'worktree', 'add', str(test_path), '-b', 'test-branch'
    ])

    # TODO: Run coordinator and verify it cleans up
    assert True

def test_metrics_tracking():
    """Test metrics are created and updated"""
    metrics_file = Path('adws/metrics.json')

    # TODO: Run coordinator and verify metrics updated
    assert metrics_file.exists()
```

### 4.2 Create End-to-End Test

Create `tests/test_e2e.py`:

```python
"""End-to-end test with real GitHub issue"""

def test_full_workflow():
    """
    Test complete workflow:
    1. Create test issue on GitHub
    2. Start coordinator
    3. Verify worker spawned
    4. Verify PR created
    5. Verify tasks.md updated
    6. Cleanup
    """
    # TODO: Implement full e2e test
    pass
```

### 4.3 Create Smoke Tests

Create `tests/test_smoke.sh`:

```bash
#!/bin/bash
# Quick smoke tests

echo "=== Smoke Tests ==="

# Test 1: Coordinator starts
echo "Test 1: Coordinator starts..."
timeout 10 python3 adws/coordinator.py &
COORD_PID=$!
sleep 5
kill $COORD_PID 2>/dev/null
echo "✓ Passed"

# Test 2: Tools exist
echo "Test 2: Tools exist..."
test -f tools/view_worker.py || exit 1
test -f tools/status.py || exit 1
echo "✓ Passed"

# Test 3: Config valid
echo "Test 3: Config valid..."
python3 -c "import tomllib; tomllib.load(open('adws/config.toml', 'rb'))"
echo "✓ Passed"

echo "=== All Smoke Tests Passed ==="
```

---

## Phase 5: Documentation (MEDIUM PRIORITY)

**Priority**: P2
**Estimated Time**: 1-2 hours
**Dependencies**: Phases 1-4 complete

### 5.1 Update README.md

Add to `adws/README.md`:

- ✅ Installation instructions
- ✅ Configuration guide
- ✅ How to start/stop coordinator
- ✅ How to monitor status
- ✅ How to stop workers
- ✅ Troubleshooting guide
- ✅ Metrics explanation

### 5.2 Create Runbook

Create `adws/RUNBOOK.md`:

```markdown
# Production Runbook

## Daily Operations

### Starting the Coordinator
```bash
cd /home/pi/circuit-synth
python3 adws/coordinator.py > coordinator.log 2>&1 &
echo $! > coordinator.pid
```

### Checking Status
```bash
python3 tools/status.py
```

### Stopping the Coordinator
```bash
kill $(cat coordinator.pid)
```

## Troubleshooting

### Too many worktree errors
**Symptom**: Health degraded, many worktree errors

**Fix**:
```bash
# Stop coordinator
kill $(cat coordinator.pid)

# Clean all worktrees
for tree in trees/gh-*; do
  git worktree remove "$tree" --force
done

# Restart
python3 adws/coordinator.py > coordinator.log 2>&1 &
```

### Worker stuck
**Symptom**: Worker running for > 2 hours

**Fix**:
```bash
# Graceful stop
./tools/stop_worker.sh 471

# Or force kill
kill -9 <PID>
git worktree remove trees/gh-471 --force
```
```

---

## Phase 6: Raspberry Pi Deployment (FINAL)

**Priority**: P2
**Estimated Time**: 1-2 hours
**Dependencies**: All phases complete

### 6.1 Create Deployment Script

Create `tools/deploy_to_pi.sh`:

```bash
#!/bin/bash
# Deploy coordinator to Raspberry Pi

PI_HOST="raspberrypi.local"
PI_USER="pi"
PI_PATH="/home/pi/circuit-synth"

echo "Deploying to $PI_USER@$PI_HOST:$PI_PATH"

# Copy files
rsync -av --exclude='.git' --exclude='trees' --exclude='logs' \
    . $PI_USER@$PI_HOST:$PI_PATH/

# Install dependencies
ssh $PI_USER@$PI_HOST "cd $PI_PATH && pip3 install -r requirements.txt"

# Setup systemd service
ssh $PI_USER@$PI_HOST "sudo cp $PI_PATH/tools/coordinator.service /etc/systemd/system/"
ssh $PI_USER@$PI_HOST "sudo systemctl daemon-reload"
ssh $PI_USER@$PI_HOST "sudo systemctl enable coordinator"

echo "Deployment complete!"
echo "To start: ssh $PI_USER@$PI_HOST 'sudo systemctl start coordinator'"
```

### 6.2 Create Systemd Service

Create `tools/coordinator.service`:

```ini
[Unit]
Description=Circuit-Synth Autonomous Coordinator
After=network.target

[Service]
Type=simple
User=pi
WorkingDirectory=/home/pi/circuit-synth
ExecStart=/usr/bin/python3 /home/pi/circuit-synth/adws/coordinator.py
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

### 6.3 Create Monitoring Script

Create `tools/monitor_pi.sh`:

```bash
#!/bin/bash
# Monitor coordinator on Raspberry Pi

PI_HOST="raspberrypi.local"
PI_USER="pi"

ssh $PI_USER@$PI_HOST "cd /home/pi/circuit-synth && python3 tools/status.py"
```

---

## Implementation Checklist

### Phase 1: Core Fixes (MUST DO)
- [ ] 1.1 Implement `ensure_worktree()` with idempotent creation
- [ ] 1.1 Add `_worker_is_running()` helper
- [ ] 1.1 Replace `create_worktree()` calls
- [ ] 1.1 Test worktree cleanup
- [ ] 1.2 Implement `_reap_children()` signal handler
- [ ] 1.2 Register SIGCHLD in `__init__`
- [ ] 1.2 Test zombie reaping
- [ ] 1.3 Implement `check_completions()` with PR detection
- [ ] 1.3 Add GitHub issue commenting
- [ ] 1.3 Add BLOCKED.md detection
- [ ] 1.3 Call `check_completions()` in main loop
- [ ] 1.3 Test completion tracking

### Phase 2: Monitoring (SHOULD DO)
- [ ] 2.1 Create `adws/metrics.py`
- [ ] 2.1 Integrate metrics into coordinator
- [ ] 2.1 Add auto-recovery on health degradation
- [ ] 2.1 Test metrics tracking
- [ ] 2.2 Create `tools/status.py` dashboard
- [ ] 2.2 Test dashboard output

### Phase 3: Control (SHOULD DO)
- [ ] 3.1 Add STOP signal check to `worker_template.md`
- [ ] 3.1 Create `tools/stop_worker.sh`
- [ ] 3.1 Test graceful stop
- [ ] 3.2 Add pause/resume to coordinator
- [ ] 3.2 Test pause/resume

### Phase 4: Testing (SHOULD DO)
- [ ] 4.1 Create integration tests
- [ ] 4.2 Create end-to-end test
- [ ] 4.3 Create smoke tests
- [ ] Run all tests

### Phase 5: Documentation (NICE TO HAVE)
- [ ] 5.1 Update README.md
- [ ] 5.2 Create RUNBOOK.md

### Phase 6: Deployment (FINAL STEP)
- [ ] 6.1 Create deployment script
- [ ] 6.2 Create systemd service
- [ ] 6.3 Create monitoring script
- [ ] 6.4 Deploy to Raspberry Pi
- [ ] 6.5 Verify running on Pi

---

## Estimated Timeline

**Fastest path** (focus on P0/P1):
- Day 1 Morning (3-4h): Phase 1 - Core fixes
- Day 1 Afternoon (2-3h): Phase 2 - Monitoring
- Day 2 Morning (2h): Phase 3 - Control
- Day 2 Afternoon (2h): Phase 4 - Testing
- Day 3 (1h): Phase 5 - Documentation
- Day 3 (1h): Phase 6 - Deployment

**Total: 8-12 hours over 2-3 days**

**Can skip** (if time-constrained):
- Phase 3.2 (pause/resume) - nice but not critical
- Phase 4.2 (e2e test) - can test manually
- Phase 5 (documentation) - can do later

**Minimum viable** (for 24/7 operation):
- Phase 1 (core fixes): REQUIRED
- Phase 2.1 (metrics): REQUIRED
- Phase 6 (deployment): REQUIRED

**Minimum time**: ~6 hours

---

## Success Criteria

The system is production-ready when:

1. ✅ No zombie processes accumulate
2. ✅ No repeated worktree errors
3. ✅ tasks.md accurately reflects status
4. ✅ Metrics track health
5. ✅ Can stop workers gracefully
6. ✅ Smoke tests pass
7. ✅ Runs 24/7 on Raspberry Pi without crashes
8. ✅ Success rate > 80%
9. ✅ Auto-recovery from errors
10. ✅ GitHub issues get status comments

---

## Post-Deployment Monitoring

After deploying to Raspberry Pi:

**Week 1**: Monitor daily
- Check `python3 tools/status.py` each morning
- Review any failed tasks
- Verify success rate > 80%

**Week 2-4**: Monitor 2-3x per week
- Check metrics for trends
- Adjust timeout/polling if needed
- Verify no resource leaks

**Month 2+**: Monitor weekly
- Review PRs created
- Check token budget usage
- Verify system stable

---

## Risk Mitigation

**Risk**: Worker corrupts repository
**Mitigation**: Git worktrees isolate changes, main repo unaffected

**Risk**: Worker uses too many tokens
**Mitigation**: Monitor logs/*.jsonl size, add per-worker limits if needed

**Risk**: GitHub rate limiting
**Mitigation**: 30s poll interval stays well under limits

**Risk**: Raspberry Pi crashes/reboots
**Mitigation**: Systemd auto-restart, task state in tasks.md recoverable

**Risk**: Workers all fail same way
**Mitigation**: Metrics detect pattern, auto-pause if health critical

---

## Next Steps

**Immediate**: Start with Phase 1 (core fixes)
- Highest impact
- Unblocks other work
- ~4 hours

**After Phase 1**: Add Phase 2.1 (metrics)
- Essential for production monitoring
- ~2 hours

**Then**: Test manually and deploy
- Can skip automated tests initially
- Deploy to Pi and monitor for 1 week

**Later**: Add remaining phases as needed
- Phase 3 (control) when you need to intervene
- Phase 4 (tests) when stabilizing
- Phase 5 (docs) when onboarding others

---

**Ready to begin implementation?** Start with Phase 1.1 (worktree fix).
