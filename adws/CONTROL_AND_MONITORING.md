# TAC-8 Coordinator: Control, Monitoring & Troubleshooting

**Purpose**: How to control running workers, monitor their progress, and fix the core issues we identified during testing.

---

## 📋 Table of Contents

1. [Viewing Worker Activity](#viewing-worker-activity)
2. [Stopping and Intervening](#stopping-and-intervening)
3. [Fixing Core Issues](#fixing-core-issues)
4. [Monitoring and Alerts](#monitoring-and-alerts)

---

## 1. Viewing Worker Activity

### See Worker Conversation

```bash
# View readable conversation for issue #471
python3 tools/view_worker.py 471

# Detailed view with all parameters
python3 tools/view_worker.py 471 --detailed
```

**Output shows**:
- Every message the worker sent
- Every tool the worker used
- File operations, commands, searches
- Timestamps and session info

### Check Raw Logs

```bash
# Stream logs as worker runs
tail -f logs/gh-471.jsonl | jq -r 'select(.type=="assistant") | .message.content[] | select(.type=="text") | .text'

# See all tool uses
cat logs/gh-471.jsonl | jq 'select(.type=="assistant") | .message.content[] | select(.type=="tool_use") | .name' | sort | uniq -c

# Find errors
cat logs/gh-471.jsonl | jq 'select(.type=="error")'
```

### Check Worker Status

```bash
# See what's currently active
cat tasks.md

# Check worker process
ps aux | grep claude | grep gh-471

# See git worktrees
git worktree list
```

---

## 2. Stopping and Intervening

### Method 1: Stop Signal File (Graceful)

Create a STOP file that worker checks periodically:

```bash
# Stop worker for issue 450
touch /home/shane/Desktop/circuit-synth/trees/gh-450/STOP
echo "User requested stop at $(date)" >> /home/shane/Desktop/circuit-synth/trees/gh-450/STOP
```

**Requires**: Worker template must check for STOP file (not currently implemented)

**Add to worker_template.md**:
```markdown
## Check for Stop Signal

Before each major operation (after each tool use), check:
```python
import os
if os.path.exists('STOP'):
    print("⏹️  STOP signal detected - exiting gracefully")
    # Commit any useful work
    subprocess.run(['git', 'add', '.'])
    subprocess.run(['git', 'commit', '-m', 'WIP: Stopped by user'])
    sys.exit(0)
```
```

### Method 2: Kill Worker Process (Immediate)

```bash
# Find worker PID from tasks.md or ps
cat tasks.md | grep "gh-450" -A 2

# Kill the worker
kill <PID>

# Or kill all claude workers
pkill -f "claude.*gh-450"
```

**Cleanup after kill**:
```bash
# Remove worktree
git worktree remove trees/gh-450 --force

# Update tasks.md manually (move to Failed section)
```

### Method 3: Cancel via tasks.md

Manually edit tasks.md to mark as cancelled:

```markdown
## Failed

[❌ w-abc123] gh-450: User cancelled
- Reason: Not needed anymore
```

Coordinator will skip it on next iteration.

### Method 4: Delete Issue Label

Remove the "rpi-auto" label from GitHub issue:

```bash
gh issue edit 450 --remove-label "rpi-auto"
```

Coordinator won't pick it up again.

---

## 3. Fixing Core Issues

### Issue 1: Repeated Worktree Creation Failures

**Problem**: Coordinator keeps trying to create worktrees that already exist.

**Root Cause**: No cleanup/reuse logic when worktree exists.

**Solution** (add to coordinator.py):

```python
def ensure_worktree(self, task: Task) -> Path:
    """Create or reuse worktree for task (idempotent)"""
    worktree_path = self.trees_dir / f"gh-{task.issue_number}"

    # Check if worktree already exists
    result = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        capture_output=True, text=True, cwd=self.repo_root
    )

    existing_paths = set()
    for line in result.stdout.split('\n'):
        if line.startswith('worktree '):
            existing_paths.add(Path(line.split(' ', 1)[1]))

    if worktree_path in existing_paths:
        logger.info(f"🔄 Worktree exists: {worktree_path} - removing and recreating")
        # Remove existing worktree
        subprocess.run(
            ["git", "worktree", "remove", str(worktree_path), "--force"],
            cwd=self.repo_root
        )

    # Create fresh worktree
    subprocess.run(
        ["git", "worktree", "add", str(worktree_path), "-b", task.branch_name],
        check=True, cwd=self.repo_root
    )

    return worktree_path
```

**Change in spawn_worker**:
```python
# OLD:
worktree_path = self.create_worktree(task)

# NEW:
worktree_path = self.ensure_worktree(task)  # Idempotent
```

---

### Issue 2: Tasks.md Status Not Updating

**Problem**: Tasks stuck in "Pending" or "Active" after PR created.

**Root Cause**: Coordinator doesn't check for PR creation.

**Solution** (add to coordinator.py):

```python
def check_completions(self, tasks: List[Task]) -> List[Task]:
    """Check if active workers have completed and update status"""
    updated_tasks = []

    for task in tasks:
        if task.status != 'active':
            updated_tasks.append(task)
            continue

        # Check if worker process still running
        if task.worker_pid:
            try:
                os.kill(task.worker_pid, 0)  # Check if exists
                # Still running - check if PR created while running
            except OSError:
                # Process exited
                pass

        # Check for PR creation (regardless of process status)
        result = subprocess.run(
            ["gh", "pr", "list",
             "--head", task.branch_name,
             "--json", "number,url,state"],
            capture_output=True, text=True, cwd=self.repo_root
        )

        if result.returncode == 0 and result.stdout.strip() != "[]":
            # PR exists!
            pr_data = json.loads(result.stdout)[0]
            task.status = 'completed'
            task.pr_url = pr_data['url']
            task.pr_number = pr_data['number']
            task.completed_at = datetime.now()

            # Post comment to issue
            subprocess.run([
                "gh", "issue", "comment", str(task.issue_number),
                "--body", f"✅ Completed! See PR #{pr_data['number']}: {pr_data['url']}"
            ], cwd=self.repo_root)

            logger.info(f"✅ Task {task.task_id} completed - PR #{pr_data['number']}")

        elif task.worker_pid:
            # Process exited but no PR - check timeout or failure
            try:
                os.kill(task.worker_pid, 0)
                # Still running - keep as active
                updated_tasks.append(task)
                continue
            except OSError:
                # Exited without PR - failed
                task.status = 'failed'
                task.failure_reason = 'Worker exited without creating PR'
                logger.warning(f"❌ Task {task.task_id} failed - no PR created")

        updated_tasks.append(task)

    return updated_tasks
```

**Call in main loop**:
```python
# In run() method, before launching new workers:
tasks = self.check_completions(tasks)
self.update_tasks_md(tasks)
```

---

### Issue 3: Zombie Processes

**Problem**: Completed workers become zombies (defunct processes).

**Root Cause**: Parent (coordinator) doesn't reap child processes.

**Solution** (add to coordinator.py):

```python
import signal

class Coordinator:
    def __init__(self, ...):
        # ... existing init ...
        self.setup_signal_handlers()

    def setup_signal_handlers(self):
        """Set up signal handlers for clean shutdown and child reaping"""
        # Reap zombie children
        signal.signal(signal.SIGCHLD, self.reap_children)

        # Graceful shutdown
        signal.signal(signal.SIGTERM, self.shutdown)
        signal.signal(signal.SIGINT, self.shutdown)

    def reap_children(self, signum, frame):
        """Reap zombie child processes"""
        while True:
            try:
                pid, status = os.waitpid(-1, os.WNOHANG)
                if pid == 0:
                    # No more children to reap
                    break

                exit_code = os.WEXITSTATUS(status) if os.WIFEXITED(status) else -1
                logger.info(f"👶 Reaped child PID {pid} (exit: {exit_code})")

            except ChildProcessError:
                # No children
                break
            except OSError:
                # Other error
                break

    def shutdown(self, signum, frame):
        """Graceful shutdown"""
        logger.info("👋 Coordinator shutting down...")
        self.running = False
```

**Alternative: Manual reaping in main loop**:

```python
def run(self):
    while self.running:
        # ... existing code ...

        # Reap any zombie children (non-blocking)
        try:
            while True:
                pid, status = os.waitpid(-1, os.WNOHANG)
                if pid == 0:
                    break
                logger.info(f"Reaped PID {pid}")
        except ChildProcessError:
            pass

        time.sleep(self.poll_interval)
```

---

## 4. Monitoring and Alerts

### Health Metrics

Create `adws/metrics.py`:

```python
"""Simple metrics tracking for coordinator health"""

import json
from pathlib import Path
from datetime import datetime

class Metrics:
    def __init__(self, metrics_file: Path):
        self.file = metrics_file
        self.data = {
            'workers_launched': 0,
            'workers_completed': 0,
            'workers_failed': 0,
            'worktree_errors': 0,
            'prs_created': 0,
            'last_update': None,
            'health': 'ok'
        }
        self.load()

    def load(self):
        """Load existing metrics"""
        if self.file.exists():
            with open(self.file) as f:
                self.data.update(json.load(f))

    def save(self):
        """Save metrics to file"""
        self.data['last_update'] = datetime.now().isoformat()

        # Update health status
        if self.data['worktree_errors'] > 10:
            self.data['health'] = 'degraded'
        elif self.data['workers_failed'] > self.data['workers_completed']:
            self.data['health'] = 'warning'
        else:
            self.data['health'] = 'ok'

        with open(self.file, 'w') as f:
            json.dump(self.data, f, indent=2)

    def increment(self, key: str):
        """Increment a metric counter"""
        self.data[key] += 1
        self.save()

    def reset_errors(self):
        """Reset error counters after cleanup"""
        self.data['worktree_errors'] = 0
        self.save()
```

**Use in coordinator**:

```python
from adws.metrics import Metrics

class Coordinator:
    def __init__(self, ...):
        # ...
        self.metrics = Metrics(self.repo_root / 'adws' / 'metrics.json')

    def spawn_worker(self, task):
        try:
            # ... spawn worker ...
            self.metrics.increment('workers_launched')
        except Exception as e:
            if 'already exists' in str(e):
                self.metrics.increment('worktree_errors')

    def check_completions(self, tasks):
        # ...
        if task.status == 'completed':
            self.metrics.increment('workers_completed')
            self.metrics.increment('prs_created')
        elif task.status == 'failed':
            self.metrics.increment('workers_failed')
```

### Automated Cleanup

Add to coordinator main loop:

```python
def run(self):
    while self.running:
        # ... existing code ...

        # Auto-cleanup if too many worktree errors
        if self.metrics.data['worktree_errors'] > 10:
            logger.warning("⚠️  Too many worktree errors - running cleanup")
            self.cleanup_all_worktrees()
            self.metrics.reset_errors()

        time.sleep(self.poll_interval)

def cleanup_all_worktrees(self):
    """Remove all worktrees and reset"""
    result = subprocess.run(
        ["git", "worktree", "list", "--porcelain"],
        capture_output=True, text=True, cwd=self.repo_root
    )

    for line in result.stdout.split('\n'):
        if line.startswith('worktree ') and '/trees/gh-' in line:
            path = line.split(' ', 1)[1]
            logger.info(f"🧹 Removing worktree: {path}")
            subprocess.run(
                ["git", "worktree", "remove", path, "--force"],
                cwd=self.repo_root
            )
```

### Status Dashboard

Simple CLI dashboard:

```bash
# Create tools/status.py
#!/usr/bin/env python3
"""Show coordinator status"""

import json
from pathlib import Path

def show_status():
    # Read metrics
    metrics_file = Path('adws/metrics.json')
    if metrics_file.exists():
        metrics = json.load(open(metrics_file))
        print("📊 Coordinator Health")
        print(f"   Status: {metrics['health'].upper()}")
        print(f"   Workers launched: {metrics['workers_launched']}")
        print(f"   Completed: {metrics['workers_completed']}")
        print(f"   Failed: {metrics['workers_failed']}")
        print(f"   PRs created: {metrics['prs_created']}")
        print(f"   Worktree errors: {metrics['worktree_errors']}")

    # Read tasks.md
    tasks_file = Path('tasks.md')
    if tasks_file.exists():
        content = open(tasks_file).read()
        pending = content.count('[] gh-')
        active = content.count('[🟡 w-')
        completed = content.count('[✅')
        failed = content.count('[❌')

        print(f"\n📋 Tasks")
        print(f"   Pending: {pending}")
        print(f"   Active: {active}")
        print(f"   Completed today: {completed}")
        print(f"   Failed: {failed}")

if __name__ == '__main__':
    show_status()
```

**Usage**:
```bash
watch -n 5 python3 tools/status.py
```

---

## Summary of Fixes Needed

1. ✅ **Worker visibility**: Created `tools/view_worker.py`
2. ⚠️  **Worktree cleanup**: Need to add `ensure_worktree()` method
3. ⚠️  **Status tracking**: Need to add `check_completions()` with PR detection
4. ⚠️  **Zombie reaping**: Need to add signal handlers
5. ⚠️  **Metrics**: Need to add metrics tracking
6. ⚠️  **Stop mechanism**: Need to add STOP file check to worker template
7. ⚠️  **GitHub updates**: Need to post comments on issues

**Priority order**:
1. Fix zombie processes (easy, immediate improvement)
2. Fix status tracking (essential for knowing when work is done)
3. Fix worktree cleanup (reduces noise, improves reliability)
4. Add metrics (helps detect issues early)
5. Add stop mechanism (nice to have for control)
