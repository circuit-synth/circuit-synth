#!/usr/bin/env python3
"""
Circuit-Synth Coordinator - Simple TAC-8 inspired autonomous system

Polls GitHub for 'rpi-auto' issues, spawns workers, manages task queue.
"""

import re
import time
import json
import subprocess
import tomllib
import os
import shutil
from pathlib import Path
from dataclasses import dataclass, field
from typing import List, Optional, Any
from datetime import datetime
import secrets
import signal

# Import error handling
from adw_modules.error_handling import (
    TaskErrorTracking,
    FailureType,
    categorize_error,
    format_health_for_dashboard
)

# Import API logging
from adw_modules.api_logger import ClaudeAPILogger

# Configuration paths
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
CONFIG_FILE = SCRIPT_DIR / "config.toml"
TASKS_FILE = REPO_ROOT / "tasks.md"
WORKER_TEMPLATE = REPO_ROOT / "worker_template.md"
LOGS_DIR = REPO_ROOT / "logs"
TREES_DIR = REPO_ROOT / "trees"
API_LOGS_DIR = REPO_ROOT / "logs" / "api"


@dataclass
class Task:
    """Represents a task in the work queue"""
    id: str
    source: str
    number: str
    description: str
    priority: int
    status: str
    worker_id: Optional[str] = None
    tree_path: Optional[str] = None
    branch_name: Optional[str] = None
    pid: Optional[int] = None
    started: Optional[str] = None
    completed: Optional[str] = None
    commit_hash: Optional[str] = None
    pr_url: Optional[str] = None
    error: Optional[str] = None
    # Error tracking for automatic retry
    error_tracking: TaskErrorTracking = field(default_factory=TaskErrorTracking)
    # API usage tracking
    api_call_metrics: Optional[Any] = None


class Coordinator:
    """Main coordinator - manages work queue and workers"""

    def __init__(self, config_path: Path = CONFIG_FILE):
        with open(config_path, "rb") as f:
            self.config = tomllib.load(f)

        # Create directories
        LOGS_DIR.mkdir(exist_ok=True)
        TREES_DIR.mkdir(exist_ok=True)
        API_LOGS_DIR.mkdir(parents=True, exist_ok=True)

        self.running = True
        self.active_workers: dict[str, subprocess.Popen] = {}

        # Initialize API logger
        self.api_logger = ClaudeAPILogger(API_LOGS_DIR)

        # Setup signal handlers
        signal.signal(signal.SIGCHLD, self._reap_children)
        signal.signal(signal.SIGINT, self._shutdown)
        signal.signal(signal.SIGTERM, self._shutdown)

    def _shutdown(self, signum, frame):
        """Graceful shutdown"""
        print(f"\n🛑 Shutting down (signal {signum})...")
        self.running = False

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

    @staticmethod
    def generate_worker_id() -> str:
        """Generate short random worker ID"""
        return f"w-{secrets.token_hex(3)}"

    def fetch_github_issues(self) -> List[Task]:
        """Fetch issues from GitHub with rpi-auto label"""
        repo = f"{self.config['github']['repo_owner']}/{self.config['github']['repo_name']}"
        label = self.config['github']['issue_label']

        try:
            result = subprocess.run(
                ['gh', 'issue', 'list', '-R', repo, '-l', label,
                 '--json', 'number,title,labels', '--limit', '50'],
                capture_output=True, text=True, check=True, cwd=REPO_ROOT
            )
            issues = json.loads(result.stdout)

            tasks = []
            for issue in issues:
                # Extract priority from labels (default p2)
                priority = 2
                for label_obj in issue.get('labels', []):
                    label_name = label_obj.get('name', '')
                    if label_name == 'priority:P0':
                        priority = 0
                    elif label_name == 'priority:P1':
                        priority = 1

                task = Task(
                    id=f"gh-{issue['number']}",
                    source='gh',
                    number=str(issue['number']),
                    description=issue['title'],
                    priority=priority,
                    status='pending'
                )
                tasks.append(task)

            return tasks

        except subprocess.CalledProcessError as e:
            print(f"⚠️  Failed to fetch GitHub issues: {e}")
            return []

    def parse_tasks_md(self) -> List[Task]:
        """Parse tasks.md to extract current tasks"""
        if not TASKS_FILE.exists():
            return []

        content = TASKS_FILE.read_text()
        tasks = []

        # Regex patterns for different task statuses
        patterns = {
            'pending': r'^\[\]\s+(\w+-\d+):\s+(.+?)\s+\{(p\d)\}',
            'active': r'^\[🟡\s+(w-[a-f0-9]+),\s+trees/(\w+-\d+)\]\s+(\w+-\d+):\s+(.+)',
            'completed': r'^\[✅\s+([a-f0-9]+),\s+(w-[a-f0-9]+)\]\s+(\w+-\d+):\s+(.+)',
            'failed': r'^\[❌\s+(w-[a-f0-9]+)\]\s+(\w+-\d+):\s+(.+)',
            'blocked': r'^\[⏰\s+(w-[a-f0-9]+)\]\s+(\w+-\d+):\s+(.+)',
        }

        lines_list = content.split('\n')
        i = 0
        while i < len(lines_list):
            line = lines_list[i].strip()
            i += 1

            if not line or line.startswith('#'):
                continue

            # Check for task pattern
            matched = False
            for status, pattern in patterns.items():
                match = re.match(pattern, line)
                if match:
                    matched = True
                    if status == 'pending':
                        task_id, desc, priority = match.groups()
                        priority_num = int(priority[1])
                        source, number = task_id.split('-')
                        task = Task(
                            id=task_id, source=source, number=number,
                            description=desc, priority=priority_num, status='pending'
                        )

                        # Check next line for metadata
                        if i < len(lines_list) and lines_list[i].strip().startswith('<!-- META:'):
                            meta_line = lines_list[i].strip()
                            i += 1
                            try:
                                # Extract JSON from HTML comment
                                json_str = meta_line.replace('<!-- META:', '').replace(' -->', '')
                                metadata = json.loads(json_str)

                                # Restore error tracking state
                                task.error_tracking.attempt_count = metadata.get('attempts', 0)
                                task.error_tracking.max_attempts = metadata.get('max_attempts', 3)

                                if metadata.get('failed_at'):
                                    task.error_tracking.failed_at = datetime.fromisoformat(metadata['failed_at'])

                                # Restore failure history
                                for failure_type_str in metadata.get('failure_types', []):
                                    try:
                                        failure_type = FailureType(failure_type_str)
                                        task.error_tracking.failure_history.append(failure_type)
                                    except ValueError:
                                        pass

                                if metadata.get('last_failure'):
                                    try:
                                        task.error_tracking.last_failure_type = FailureType(metadata['last_failure'])
                                    except ValueError:
                                        pass
                            except (json.JSONDecodeError, KeyError) as e:
                                print(f"⚠️  Failed to parse metadata for {task_id}: {e}")

                        tasks.append(task)
                    elif status == 'active':
                        worker_id, tree_id, task_id, desc = match.groups()
                        source, number = task_id.split('-')
                        tasks.append(Task(
                            id=task_id, source=source, number=number,
                            description=desc, priority=2, status='active',
                            worker_id=worker_id, tree_path=f"trees/{tree_id}"
                        ))
                    break

        return tasks

    def update_tasks_md(self, tasks: List[Task]):
        """Update tasks.md with current task state (atomic write)"""
        sections = {
            'pending': [],
            'active': [],
            'completed': [],
            'failed': [],
            'blocked': []
        }

        for task in tasks:
            sections[task.status].append(task)

        lines = [
            "# Circuit-Synth Work Queue",
            "",
            f"**Last updated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "---",
            "",
            "## Pending",
            ""
        ]

        # Pending (sorted by priority)
        for task in sorted(sections['pending'], key=lambda t: t.priority):
            lines.append(f"[] {task.id}: {task.description} {{p{task.priority}}}")

            # Store error tracking as JSON metadata (machine-readable)
            if task.error_tracking.attempt_count > 0:
                metadata = {
                    'attempts': task.error_tracking.attempt_count,
                    'max_attempts': task.error_tracking.max_attempts,
                    'failed_at': task.error_tracking.failed_at.isoformat() if task.error_tracking.failed_at else None,
                    'failure_types': [f.value for f in task.error_tracking.failure_history],
                    'last_failure': task.error_tracking.last_failure_type.value if task.error_tracking.last_failure_type else None
                }
                lines.append(f"<!-- META:{json.dumps(metadata)} -->")

            # Add health and retry info (human-readable)
            health_lines = format_health_for_dashboard(task.error_tracking)
            lines.extend(health_lines)

            if health_lines:  # Add blank line only if there was health info
                lines.append("")

        if not sections['pending']:
            lines.append("<!-- No pending tasks -->")

        lines.extend(["", "---", "", "## Active (max 3)", ""])

        # Active
        for task in sections['active']:
            lines.append(f"[🟡 {task.worker_id}, {task.tree_path}] {task.id}: {task.description}")
            if task.started:
                lines.append(f"- Started: {task.started}")
            if task.pid:
                lines.append(f"- PID: {task.pid}")
            lines.append("")

        if not sections['active']:
            lines.append("<!-- No active tasks -->")

        lines.extend(["", "---", "", "## Completed Today", ""])

        # Completed
        for task in sections['completed']:
            commit = task.commit_hash[:7] if task.commit_hash else "unknown"
            lines.append(f"[✅ {commit}, {task.worker_id}] {task.id}: {task.description}")
            if task.completed:
                lines.append(f"- Completed: {task.completed}")
            if task.pr_url:
                lines.append(f"- PR: {task.pr_url}")
            lines.append("")

        if not sections['completed']:
            lines.append("<!-- No completed tasks today -->")

        lines.extend(["", "---", "", "## Failed", ""])

        # Failed
        from adw_modules.error_handling import TaskHealth
        for task in sections['failed']:
            health = task.error_tracking.get_health_status()
            icon = "☠️" if health == TaskHealth.DEAD else "❌"

            lines.append(f"[{icon} {task.worker_id}] {task.id}: {task.description}")
            lines.append(f"- Attempts: {task.error_tracking.attempt_count}/{task.error_tracking.max_attempts}")

            # Show failure history
            if task.error_tracking.failure_history:
                types = [f.value for f in task.error_tracking.failure_history]
                lines.append(f"- Failure types: {', '.join(types)}")

            if task.completed:
                lines.append(f"- Failed: {task.completed}")
            if task.error:
                error_display = task.error[:100] + "..." if len(task.error) > 100 else task.error
                lines.append(f"- Reason: {error_display}")

            # Show alerts
            for alert in task.error_tracking.get_alerts():
                lines.append(f"- {alert}")

            lines.append("")

        if not sections['failed']:
            lines.append("<!-- No failed tasks -->")

        lines.extend(["", "---", "", "## Blocked", ""])

        # Blocked
        for task in sections['blocked']:
            lines.append(f"[⏰ {task.worker_id}] {task.id}: {task.description}")
            if task.started:
                lines.append(f"- Blocked since: {task.started}")
            lines.append("")

        if not sections['blocked']:
            lines.append("<!-- No blocked tasks -->")

        # Atomic write
        temp_file = TASKS_FILE.with_suffix('.md.tmp')
        temp_file.write_text('\n'.join(lines))
        temp_file.replace(TASKS_FILE)

    def get_dashboard_status(self, tasks: List[Task]) -> dict:
        """Generate status data for dashboard display

        This provides comprehensive status information including:
        - Task counts by status
        - Health metrics
        - Active workers with health scores
        - Pending tasks
        - Recent completions
        - Errors and alerts

        Args:
            tasks: List of all tasks

        Returns:
            Dashboard status dictionary
        """
        from adw_modules.error_handling import TaskHealth

        # Categorize tasks
        active = [t for t in tasks if t.status == 'active']
        pending = [t for t in tasks if t.status == 'pending']
        completed = [t for t in tasks if t.status == 'completed']
        failed = [t for t in tasks if t.status == 'failed']
        blocked = [t for t in tasks if t.status == 'blocked']

        # Calculate overall health
        if tasks:
            health_scores = [self._calculate_task_health_score(t) for t in tasks]
            avg_health = sum(health_scores) / len(health_scores)
        else:
            avg_health = 1.0

        # Determine health status
        if avg_health >= 0.9:
            health_status = "excellent"
        elif avg_health >= 0.7:
            health_status = "good"
        elif avg_health >= 0.5:
            health_status = "fair"
        elif avg_health >= 0.3:
            health_status = "poor"
        else:
            health_status = "critical"

        # Generate alerts
        alerts = self._generate_alerts(tasks)

        return {
            "summary": {
                "active": len(active),
                "pending": len(pending),
                "completed": len(completed),
                "failed": len(failed),
                "total": len(tasks)
            },
            "health_metrics": {
                "overall_health": avg_health,
                "health_status": health_status,
                "timestamp": datetime.now().isoformat()
            },
            "alerts": alerts,
            "active_workers": [
                {
                    "task_id": t.id,
                    "worker_id": t.worker_id,
                    "description": t.description,
                    "started": t.started,
                    "pid": t.pid,
                    "health_score": self._calculate_task_health_score(t)
                }
                for t in active
            ],
            "pending_tasks": [
                {
                    "task_id": t.id,
                    "description": t.description,
                    "priority": t.priority
                }
                for t in sorted(pending, key=lambda x: x.priority)
            ],
            "recent_completions": [
                {
                    "task_id": t.id,
                    "description": t.description,
                    "completed": t.completed,
                    "pr_url": t.pr_url
                }
                for t in completed[-5:]  # Last 5
            ],
            "errors": [
                {
                    "task_id": t.id,
                    "description": t.description,
                    "error": t.error,
                    "retry_count": t.error_tracking.attempt_count,
                    "category": t.error_tracking.last_failure_type.value if t.error_tracking.last_failure_type else "unknown"
                }
                for t in failed
            ]
        }

    def _calculate_task_health_score(self, task: Task) -> float:
        """Calculate health score for a task (0.0 to 1.0)"""
        score = 1.0

        # Active tasks
        if task.status == 'active' and task.started:
            try:
                started = datetime.strptime(task.started, '%Y-%m-%d %H:%M:%S')
                elapsed_minutes = (datetime.now() - started).total_seconds() / 60

                # Deduct points for age
                if elapsed_minutes > 120:  # 2 hours
                    score -= 0.5
                elif elapsed_minutes > 90:
                    score -= 0.3
                elif elapsed_minutes > 60:
                    score -= 0.1
            except ValueError:
                pass

        # Failed tasks
        elif task.status == 'failed':
            retry_count = task.error_tracking.attempt_count
            score -= (0.2 * retry_count)

        # Blocked tasks
        elif task.status == 'blocked':
            score = 0.5

        # Completed tasks
        elif task.status == 'completed':
            score = 1.0

        return max(0.0, min(1.0, score))

    def _generate_alerts(self, tasks: List[Task]) -> List[dict]:
        """Generate alerts based on task status"""
        alerts = []

        # Check for repeated failures
        for task in tasks:
            if task.status == 'failed' and task.error_tracking.attempt_count >= 3:
                alerts.append({
                    "severity": "critical",
                    "task_id": task.id,
                    "message": f"Task {task.id} has failed {task.error_tracking.attempt_count} times",
                    "type": "repeated_failure"
                })

        # Check for high failure rate
        recent_tasks = tasks[-20:]  # Last 20 tasks
        if recent_tasks:
            failed = [t for t in recent_tasks if t.status == 'failed']
            failure_rate = len(failed) / len(recent_tasks)

            if failure_rate > 0.5:
                alerts.append({
                    "severity": "critical",
                    "message": f"High failure rate: {failure_rate:.1%} of recent tasks failed",
                    "type": "high_failure_rate"
                })

        # Check for all workers stuck
        active = [t for t in tasks if t.status == 'active']
        if active:
            stuck_count = 0
            for t in active:
                if t.started:
                    try:
                        started = datetime.strptime(t.started, '%Y-%m-%d %H:%M:%S')
                        elapsed = (datetime.now() - started).total_seconds() / 60
                        if elapsed > 120:  # 2 hours
                            stuck_count += 1
                    except ValueError:
                        pass

            if stuck_count > 0 and stuck_count == len(active):
                alerts.append({
                    "severity": "critical",
                    "message": f"All {len(active)} active workers appear to be stuck",
                    "type": "all_workers_stuck"
                })

        return alerts

    def _worker_is_running(self, task: Task) -> bool:
        """Check if worker process is still running"""
        if not task.pid:
            return False

        try:
            os.kill(task.pid, 0)  # Signal 0 just checks existence
            return True
        except OSError:
            return False

    def ensure_worktree(self, task: Task) -> Path:
        """Create git worktree for task (idempotent)

        Handles existing worktrees by removing them if stale.
        A worktree is considered stale if the worker is no longer running.
        """
        worktree_path = TREES_DIR / task.id

        # Check if worktree already exists
        if worktree_path.exists():
            print(f"⚠️  Worktree already exists: {worktree_path}")

            # Check git status
            status_result = subprocess.run(
                ["git", "status", "--porcelain"],
                capture_output=True, text=True, cwd=worktree_path
            )

            # Log current state for debugging
            changes = status_result.stdout.strip()
            worker_running = self._worker_is_running(task)
            print(f"   🔍 Worktree status check:")
            print(f"      - Has changes: {bool(changes)}")
            print(f"      - Worker running: {worker_running}")
            print(f"      - Worker PID: {task.pid}")

            # If it has uncommitted changes
            if changes:
                print(f"   📝 Worktree has uncommitted changes ({len(changes.splitlines())} files)")

                # Check if worker is still running
                if not worker_running:
                    print(f"   ⏸️  Worker not running (PID {task.pid})")

                    # Check if this is work in progress or a true crash
                    # Strategy: Check file modification times to determine if work is fresh
                    # If files were modified recently, it's likely completed work, not a crash
                    from datetime import datetime
                    import os

                    # Find most recent file modification time in worktree
                    most_recent_mtime = 0
                    for root, dirs, files in os.walk(worktree_path):
                        # Skip .git directory
                        if '.git' in root:
                            continue
                        for file in files:
                            file_path = os.path.join(root, file)
                            try:
                                mtime = os.path.getmtime(file_path)
                                most_recent_mtime = max(most_recent_mtime, mtime)
                            except OSError:
                                pass

                    # Calculate age of most recent change
                    now = datetime.now().timestamp()
                    age_seconds = now - most_recent_mtime
                    age_minutes = age_seconds / 60

                    print(f"      - Most recent file change: {age_minutes:.1f} minutes ago")

                    # If files were modified in the last hour, treat as completed work
                    if age_minutes < 60:  # Changed within last 60 minutes
                        print(f"   ✅ Recent changes detected - preserving completed work")
                        print(f"      Worktree appears to contain fresh work, not crash debris")
                        print(f"      Worker should commit its changes or be cleaned up later")
                        # Don't remove! Let the worker commit its work
                        return worktree_path

                    # Files are old - likely stale worktree from ancient crash
                    print(f"   🗑️  Stale worktree detected (no recent changes) - removing")
                    self._remove_worktree(worktree_path)
                else:
                    print(f"   ⚠️  Worker still running - worktree is active")
                    raise Exception(f"Worktree {worktree_path} is still active")
            else:
                # Clean worktree - remove and recreate
                print(f"   🔄 Worktree is clean - removing and recreating")
                self._remove_worktree(worktree_path)

        # Prune any stale worktree references
        subprocess.run(
            ["git", "worktree", "prune"],
            cwd=REPO_ROOT, capture_output=True
        )

        # Create fresh worktree
        print(f"🌲 Creating worktree: {worktree_path}")
        subprocess.run(
            ["git", "worktree", "add", str(worktree_path), "-b", task.branch_name],
            check=True, cwd=REPO_ROOT
        )

        return worktree_path

    def _remove_worktree(self, worktree_path: Path):
        """Remove worktree (handles both git and orphaned directories)"""
        # Try git worktree remove first
        result = subprocess.run(
            ["git", "worktree", "remove", str(worktree_path), "--force"],
            cwd=REPO_ROOT, capture_output=True, text=True
        )

        # If directory still exists after git remove, manually delete it
        if worktree_path.exists():
            print(f"   Git couldn't remove worktree, deleting directory manually")
            shutil.rmtree(worktree_path)
            print(f"   ✓ Worktree removed")

    def spawn_worker(self, task: Task):
        """Spawn LLM worker agent (non-blocking)"""

        # Build prompt from template
        template = WORKER_TEMPLATE.read_text()
        prompt = template.format(
            task_id=task.id,
            source=task.source,
            priority=f"p{task.priority}",
            description=task.description,
            worktree_path=str(task.tree_path),
            branch_name=task.branch_name,
            worker_id=task.worker_id,
            issue_number=task.number
        )

        # Write prompt to file
        prompt_file = LOGS_DIR / f"{task.id}-prompt.txt"
        prompt_file.write_text(prompt)

        # Start API call tracking
        task.api_call_metrics = self.api_logger.start_call(
            task_id=task.id,
            worker_id=task.worker_id,
            model=self.config['llm']['model_default'],
            prompt_file=str(prompt_file),
            prompt_content=prompt,
            settings={'source': task.source, 'priority': task.priority}
        )

        # Build LLM command from config
        cmd_template = self.config['llm']['command_template']
        model = self.config['llm']['model_default']

        cmd = [
            part.replace('{prompt_file}', str(prompt_file))
                .replace('{model}', model)
            for part in cmd_template
        ]

        print(f"🤖 Spawning worker for {task.id}")
        print(f"   Command: {' '.join(cmd)}")

        # Spawn worker (non-blocking)
        log_file = LOGS_DIR / f"{task.id}.jsonl"
        with open(log_file, 'w') as f:
            proc = subprocess.Popen(
                cmd,
                cwd=task.tree_path,
                stdout=f,
                stderr=subprocess.STDOUT
            )

        self.active_workers[task.worker_id] = proc
        task.pid = proc.pid
        task.started = datetime.now().strftime('%Y-%m-%d %H:%M:%S')

        print(f"   ✓ Worker {task.worker_id} started (PID: {proc.pid})")

    def check_completions(self, tasks: List[Task]) -> List[Task]:
        """Check if active workers have completed

        Detects completion by:
        1. Checking if PR was created for the branch
        2. Checking if worker process has exited
        3. Updating task status accordingly
        4. Posting comments to GitHub issues
        5. Cleaning up worktrees
        """
        updated_tasks = []

        for task in tasks:
            if task.status != 'active':
                updated_tasks.append(task)
                continue

            # Check if process still running
            proc = self.active_workers.get(task.worker_id)
            if proc and proc.poll() is None:
                updated_tasks.append(task)
                continue

            print(f"🏁 Worker {task.worker_id} finished for {task.id}")

            # Check if worker exited too quickly (likely an error)
            instant_failure = False
            if task.started:
                try:
                    started_dt = datetime.strptime(task.started, '%Y-%m-%d %H:%M:%S')
                    elapsed_seconds = (datetime.now() - started_dt).total_seconds()
                    if elapsed_seconds < 10:
                        instant_failure = True
                        print(f"   ⚠️  Worker exited in {elapsed_seconds:.1f}s (instant failure)")
                except ValueError:
                    pass

            # Parse API usage from worker log
            log_file = LOGS_DIR / f"{task.id}.jsonl"
            api_data = self.api_logger.parse_stream_json_output(log_file)
            tokens_input = api_data['tokens_input']
            tokens_output = api_data['tokens_output']
            response_content = api_data['response_content']

            print(f"   📊 Tokens: {tokens_input} in / {tokens_output} out / {tokens_input + tokens_output} total")

            # Check for PR creation (primary completion signal)
            try:
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

                    # Log API usage for successful completion
                    if task.api_call_metrics:
                        self.api_logger.end_call(
                            metrics=task.api_call_metrics,
                            response_content=response_content[:1000],  # First 1000 chars
                            tokens_input=tokens_input,
                            tokens_output=tokens_output,
                            success=True,
                            exit_code=0
                        )

                    print(f"   ✅ Task {task.id} completed - PR #{pr_data['number']}")

                    # Post comment to GitHub issue
                    comment = f"""✅ **Autonomous work completed!**

PR: {pr_data['url']}
Commit: `{commit_hash}`
Worker: {task.worker_id}

The PR is ready for your review."""

                    try:
                        subprocess.run(
                            ["gh", "issue", "comment", task.number, "--body", comment],
                            cwd=REPO_ROOT, check=True
                        )
                        print(f"   💬 Posted comment to issue #{task.number}")
                    except subprocess.CalledProcessError as e:
                        print(f"   ⚠️  Failed to post comment: {e}")

                    # Cleanup worktree
                    try:
                        subprocess.run(
                            ["git", "worktree", "remove", str(task.tree_path), "--force"],
                            cwd=REPO_ROOT, check=True
                        )
                        print(f"   🧹 Cleaned up worktree: {task.tree_path}")
                    except subprocess.CalledProcessError as e:
                        print(f"   ⚠️  Failed to clean up worktree: {e}")

                    # Remove from active workers
                    if task.worker_id in self.active_workers:
                        del self.active_workers[task.worker_id]

                elif not self._worker_is_running(task):
                    # Worker exited but no PR - check for BLOCKED.md
                    blocked_file = Path(task.tree_path) / "BLOCKED.md"
                    if blocked_file.exists():
                        task.status = 'blocked'
                        task.error = blocked_file.read_text()[:200]
                        task.completed = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        print(f"   ⏰ Task {task.id} blocked - waiting for human")
                    else:
                        # Worker failed - categorize error and decide on retry
                        error_msg = task.error or 'Worker exited without creating PR'

                        # Get exit code if available
                        exit_code = proc.returncode if proc else None

                        # Categorize the failure (instant failures are likely config/setup errors)
                        if instant_failure:
                            failure_type = FailureType.STARTUP_ERROR
                            error_msg = f"Worker exited in <10s: {error_msg}"
                        else:
                            failure_type = categorize_error(error_msg, context={'exit_code': exit_code})

                        # Record failure in error tracking
                        task.error_tracking.record_failure(failure_type)
                        task.error = error_msg

                        # Log API usage for failed completion
                        if task.api_call_metrics:
                            self.api_logger.end_call(
                                metrics=task.api_call_metrics,
                                response_content=response_content[:1000] if response_content else None,
                                tokens_input=tokens_input if tokens_input > 0 else None,
                                tokens_output=tokens_output if tokens_output > 0 else None,
                                success=False,
                                error_message=error_msg,
                                exit_code=exit_code
                            )

                        # Check if can retry
                        if task.error_tracking.can_retry():
                            task.status = 'pending'  # Will retry after backoff
                            backoff = task.error_tracking.calculate_backoff()
                            print(f"   ⚠️ Failed (attempt {task.error_tracking.attempt_count}/{task.error_tracking.max_attempts}): {failure_type.value}")
                            print(f"   🔄 Will retry in {backoff}s")
                        else:
                            task.status = 'failed'
                            task.completed = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                            print(f"   ❌ Failed permanently after {task.error_tracking.attempt_count} attempts: {failure_type.value}")

                            # Show alerts
                            for alert in task.error_tracking.get_alerts():
                                print(f"   {alert}")

                    # Keep worktree for debugging (don't clean up failures)

                    # Remove from active workers
                    if task.worker_id in self.active_workers:
                        del self.active_workers[task.worker_id]

            except subprocess.CalledProcessError as e:
                # Failure in PR checking - record and potentially retry
                error_msg = f'Failed to check PR status: {e}'
                failure_type = categorize_error(error_msg)

                task.error_tracking.record_failure(failure_type)
                task.error = error_msg

                if task.error_tracking.can_retry():
                    task.status = 'pending'
                    backoff = task.error_tracking.calculate_backoff()
                    print(f"   ⚠️ Failed (attempt {task.error_tracking.attempt_count}/{task.error_tracking.max_attempts}): {failure_type.value}")
                    print(f"   🔄 Will retry in {backoff}s")
                else:
                    task.status = 'failed'
                    task.completed = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                    print(f"   ❌ Task {task.id} failed permanently: {task.error}")

                # Remove from active workers
                if task.worker_id in self.active_workers:
                    del self.active_workers[task.worker_id]

            updated_tasks.append(task)

        return updated_tasks

    def run(self):
        """Main coordinator loop"""
        print("🚀 Circuit-Synth Coordinator starting...")
        print(f"   Config: {CONFIG_FILE}")
        print(f"   Tasks: {TASKS_FILE}")
        print(f"   Max concurrent: {self.config['coordinator']['max_concurrent_workers']}")
        print()

        while self.running:
            try:
                # 1. Fetch GitHub issues
                github_tasks = self.fetch_github_issues()

                # 2. Parse current tasks.md
                current_tasks = self.parse_tasks_md()
                current_ids = {t.id for t in current_tasks}

                # 3. Add new tasks
                new_tasks = [t for t in github_tasks if t.id not in current_ids]
                if new_tasks:
                    print(f"📥 Found {len(new_tasks)} new tasks from GitHub")
                    current_tasks.extend(new_tasks)

                # 4. Check completions
                current_tasks = self.check_completions(current_tasks)

                # 5. Launch new workers
                active = [t for t in current_tasks if t.status == 'active']
                pending = [t for t in current_tasks if t.status == 'pending']
                slots = self.config['coordinator']['max_concurrent_workers'] - len(active)

                # Filter pending tasks by retry readiness
                pending_ready = [t for t in pending if t.error_tracking.is_ready_for_retry()]
                pending_backoff = [t for t in pending if not t.error_tracking.is_ready_for_retry()]

                # Log tasks still in backoff
                for task in pending_backoff:
                    if task.error_tracking.failed_at:
                        backoff = task.error_tracking.calculate_backoff()
                        elapsed = (datetime.now() - task.error_tracking.failed_at).total_seconds()
                        remaining = max(0, backoff - elapsed)
                        if remaining > 0:
                            print(f"⏳ Task {task.id} in backoff: {int(remaining)}s remaining")

                if slots > 0 and pending_ready:
                    pending_ready.sort(key=lambda t: t.priority)

                    for task in pending_ready[:slots]:
                        try:
                            # Log retry attempt if this is a retry
                            if task.error_tracking.attempt_count > 0:
                                print(f"🔄 Retry attempt {task.error_tracking.attempt_count + 1}/{task.error_tracking.max_attempts} for {task.id}")

                            task.worker_id = self.generate_worker_id()
                            task.branch_name = f"auto/{task.worker_id}"

                            # Claim IMMEDIATELY
                            task.status = 'active'
                            self.update_tasks_md(current_tasks)

                            # Create worktree (idempotent)
                            task.tree_path = str(self.ensure_worktree(task))

                            # Spawn worker
                            self.spawn_worker(task)

                        except Exception as e:
                            print(f"❌ Failed to launch worker for {task.id}: {e}")
                            # Record worktree error
                            failure_type = categorize_error(str(e))
                            task.error_tracking.record_failure(failure_type)
                            task.error = str(e)

                            if task.error_tracking.can_retry():
                                task.status = 'pending'
                            else:
                                task.status = 'failed'

                # 6. Update tasks.md
                self.update_tasks_md(current_tasks)

                # 7. Sleep
                time.sleep(self.config['coordinator']['poll_interval_seconds'])

            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error in main loop: {e}")
                import traceback
                traceback.print_exc()
                time.sleep(10)

        print("\n👋 Coordinator shutting down...")


if __name__ == '__main__':
    coordinator = Coordinator()
    coordinator.run()
