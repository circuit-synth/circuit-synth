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
from pathlib import Path
from dataclasses import dataclass
from typing import List, Optional
from datetime import datetime
import secrets
import signal

# Configuration paths
SCRIPT_DIR = Path(__file__).parent
REPO_ROOT = SCRIPT_DIR.parent
CONFIG_FILE = SCRIPT_DIR / "config.toml"
TASKS_FILE = REPO_ROOT / "tasks.md"
WORKER_TEMPLATE = REPO_ROOT / "worker_template.md"
LOGS_DIR = REPO_ROOT / "logs"
TREES_DIR = REPO_ROOT / "trees"


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


class Coordinator:
    """Main coordinator - manages work queue and workers"""

    def __init__(self, config_path: Path = CONFIG_FILE):
        with open(config_path, "rb") as f:
            self.config = tomllib.load(f)

        # Create directories
        LOGS_DIR.mkdir(exist_ok=True)
        TREES_DIR.mkdir(exist_ok=True)

        self.running = True
        self.active_workers: dict[str, subprocess.Popen] = {}

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

        for line in content.split('\n'):
            line = line.strip()
            if not line or line.startswith('#') or line.startswith('<!--'):
                continue

            for status, pattern in patterns.items():
                match = re.match(pattern, line)
                if match:
                    if status == 'pending':
                        task_id, desc, priority = match.groups()
                        priority_num = int(priority[1])
                        source, number = task_id.split('-')
                        tasks.append(Task(
                            id=task_id, source=source, number=number,
                            description=desc, priority=priority_num, status='pending'
                        ))
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
        for task in sections['failed']:
            lines.append(f"[❌ {task.worker_id}] {task.id}: {task.description}")
            if task.completed:
                lines.append(f"- Failed: {task.completed}")
            if task.error:
                lines.append(f"- Reason: {task.error}")
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

            # If it has uncommitted changes, it's probably active
            if status_result.stdout.strip():
                print(f"   Worktree has uncommitted changes")
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
                        # Worker failed
                        task.status = 'failed'
                        task.error = 'Worker exited without creating PR'
                        task.completed = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                        print(f"   ❌ Task {task.id} failed - no PR created")

                    # Keep worktree for debugging (don't clean up failures)

                    # Remove from active workers
                    if task.worker_id in self.active_workers:
                        del self.active_workers[task.worker_id]

            except subprocess.CalledProcessError as e:
                task.status = 'failed'
                task.error = f'Failed to check PR status: {e}'
                task.completed = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
                print(f"   ❌ Task {task.id} failed: {task.error}")

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

                if slots > 0 and pending:
                    pending.sort(key=lambda t: t.priority)

                    for task in pending[:slots]:
                        try:
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
                            task.status = 'failed'
                            task.error = str(e)

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
