"""
Metrics aggregator for TAC-8 dashboard

Collects and aggregates metrics from:
- Task queue (tasks.md)
- Worker processes (psutil)
- System resources (CPU, memory, disk, thermal)
- Coordinator statistics
"""

import re
import psutil
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime


class MetricsAggregator:
    """Aggregate metrics from tasks.md, processes, and system"""

    def __init__(self, tasks_file: Optional[Path] = None):
        """
        Initialize metrics aggregator

        Args:
            tasks_file: Path to tasks.md (defaults to repo root/tasks.md)
        """
        if tasks_file is None:
            # Default to repo root/tasks.md
            # This file is in src/circuit_synth/tools/dashboard/metrics.py
            repo_root = Path(__file__).parent.parent.parent.parent.parent
            tasks_file = repo_root / "tasks.md"

        self.tasks_file = tasks_file

    def parse_tasks_md(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Parse tasks.md file into structured data

        Returns:
            Dict with keys: pending, active, completed, failed, blocked
            Each containing list of task dictionaries
        """
        if not self.tasks_file.exists():
            return {
                'pending': [],
                'active': [],
                'completed': [],
                'failed': [],
                'blocked': []
            }

        content = self.tasks_file.read_text()
        tasks = {
            'pending': [],
            'active': [],
            'completed': [],
            'failed': [],
            'blocked': []
        }

        # Regex patterns for different task statuses
        patterns = {
            'pending': r'^\[\]\s+(\w+-\d+):\s+(.+?)\s+\{(p\d)\}',
            'active': r'^\[🟡\s+(w-[a-z0-9]+),\s+trees/(\w+-\d+)\]\s+(\w+-\d+):\s+(.+)',
            'completed': r'^\[✅\s+([0-9a-f]+),\s+(w-[a-z0-9]+)\]\s+(\w+-\d+):\s+(.+)',
            'failed': r'^\[❌\s+(w-[a-z0-9]+)\]\s+(\w+-\d+):\s+(.+)',
            'blocked': r'^\[⏰\s+(w-[a-z0-9]+)\]\s+(\w+-\d+):\s+(.+)',
        }

        # Also capture metadata lines (PID, Started, etc)
        current_task = None

        for line in content.split('\n'):
            line_stripped = line.strip()

            if not line_stripped or line_stripped.startswith('#') or line_stripped.startswith('<!--'):
                continue

            # Check if it's a metadata line
            if line_stripped.startswith('- '):
                if current_task is not None:
                    # Parse metadata
                    if line_stripped.startswith('- PID:'):
                        pid_str = line_stripped.split(':')[1].strip()
                        current_task['pid'] = int(pid_str)
                    elif line_stripped.startswith('- Started:'):
                        current_task['started'] = line_stripped.split(':', 1)[1].strip()
                    elif line_stripped.startswith('- Completed:'):
                        current_task['completed'] = line_stripped.split(':', 1)[1].strip()
                    elif line_stripped.startswith('- Failed:'):
                        current_task['failed'] = line_stripped.split(':', 1)[1].strip()
                    elif line_stripped.startswith('- Blocked since:'):
                        current_task['blocked_since'] = line_stripped.split(':', 1)[1].strip()
                    elif line_stripped.startswith('- PR:'):
                        current_task['pr_url'] = line_stripped.split(':', 1)[1].strip()
                    elif line_stripped.startswith('- Reason:'):
                        current_task['error'] = line_stripped.split(':', 1)[1].strip()
                continue

            # Check for task line
            matched = False
            for status, pattern in patterns.items():
                match = re.match(pattern, line_stripped)
                if match:
                    if status == 'pending':
                        task_id, desc, priority = match.groups()
                        current_task = {
                            'task_id': task_id,
                            'description': desc,
                            'priority': int(priority[1]),
                            'status': 'pending'
                        }
                        tasks['pending'].append(current_task)
                    elif status == 'active':
                        worker_id, tree_id, task_id, desc = match.groups()
                        current_task = {
                            'task_id': task_id,
                            'description': desc,
                            'worker_id': worker_id,
                            'tree_path': f"trees/{tree_id}",
                            'status': 'active'
                        }
                        tasks['active'].append(current_task)
                    elif status == 'completed':
                        commit, worker_id, task_id, desc = match.groups()
                        current_task = {
                            'task_id': task_id,
                            'description': desc,
                            'worker_id': worker_id,
                            'commit_hash': commit,
                            'status': 'completed'
                        }
                        tasks['completed'].append(current_task)
                    elif status == 'failed':
                        worker_id, task_id, desc = match.groups()
                        current_task = {
                            'task_id': task_id,
                            'description': desc,
                            'worker_id': worker_id,
                            'status': 'failed'
                        }
                        tasks['failed'].append(current_task)
                    elif status == 'blocked':
                        worker_id, task_id, desc = match.groups()
                        current_task = {
                            'task_id': task_id,
                            'description': desc,
                            'worker_id': worker_id,
                            'status': 'blocked'
                        }
                        tasks['blocked'].append(current_task)

                    matched = True
                    break

            if not matched:
                current_task = None

        return tasks

    def get_task_metrics(self) -> Dict[str, int]:
        """
        Get task queue metrics summary

        Returns:
            Dict with counts for each task status
        """
        tasks = self.parse_tasks_md()

        return {
            'pending_count': len(tasks['pending']),
            'active_count': len(tasks['active']),
            'completed_count': len(tasks['completed']),
            'failed_count': len(tasks['failed']),
            'blocked_count': len(tasks['blocked']),
            'total_count': sum(len(tasks[k]) for k in tasks.keys())
        }

    def get_active_tasks(self) -> List[Dict[str, Any]]:
        """
        Get list of currently active tasks with details

        Returns:
            List of active task dictionaries
        """
        tasks = self.parse_tasks_md()
        return tasks['active']

    def get_system_metrics(self) -> Dict[str, Any]:
        """
        Get system resource metrics using psutil

        Returns:
            Dict with CPU, memory, disk metrics
        """
        # CPU
        cpu_percent = psutil.cpu_percent(interval=1)

        # Memory
        memory = psutil.virtual_memory()
        memory_percent = memory.percent
        memory_available_gb = memory.available / (1024 ** 3)

        # Disk (current directory)
        disk = psutil.disk_usage('.')
        disk_percent = disk.percent
        disk_free_gb = disk.free / (1024 ** 3)

        return {
            'cpu_percent': cpu_percent,
            'memory_percent': memory_percent,
            'memory_available_gb': round(memory_available_gb, 2),
            'disk_percent': disk_percent,
            'disk_free_gb': round(disk_free_gb, 2),
            'timestamp': datetime.now().isoformat()
        }

    def get_thermal_metrics(self) -> Optional[Dict[str, Any]]:
        """
        Get thermal metrics (Raspberry Pi specific)

        Returns:
            Dict with temperature data, or None if not available
        """
        try:
            # Try to read Raspberry Pi thermal zone
            thermal_file = Path("/sys/class/thermal/thermal_zone0/temp")
            if thermal_file.exists():
                temp_millidegrees = int(thermal_file.read_text().strip())
                cpu_temp = temp_millidegrees / 1000.0
                return {
                    'cpu_temp': round(cpu_temp, 1),
                    'unit': 'celsius'
                }
        except Exception:
            pass

        # Try psutil sensors_temperatures (if available)
        try:
            if hasattr(psutil, 'sensors_temperatures'):
                temps = psutil.sensors_temperatures()
                if temps:
                    # Try to find CPU temperature
                    for name, entries in temps.items():
                        for entry in entries:
                            if 'cpu' in entry.label.lower() or 'core' in entry.label.lower():
                                return {
                                    'cpu_temp': round(entry.current, 1),
                                    'unit': 'celsius'
                                }
        except Exception:
            pass

        return None

    def get_worker_process_metrics(self) -> List[Dict[str, Any]]:
        """
        Get metrics for worker processes

        Returns:
            List of worker metrics (CPU, memory usage per worker)
        """
        active_tasks = self.get_active_tasks()
        worker_metrics = []

        for task in active_tasks:
            pid = task.get('pid')
            if pid is None:
                continue

            try:
                proc = psutil.Process(pid)
                if proc.is_running():
                    worker_metrics.append({
                        'task_id': task['task_id'],
                        'worker_id': task['worker_id'],
                        'pid': pid,
                        'cpu_percent': proc.cpu_percent(interval=0.1),
                        'memory_mb': proc.memory_info().rss / (1024 * 1024),
                        'status': proc.status()
                    })
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                # Process doesn't exist or can't access
                worker_metrics.append({
                    'task_id': task['task_id'],
                    'worker_id': task['worker_id'],
                    'pid': pid,
                    'status': 'not_found'
                })

        return worker_metrics

    def get_coordinator_stats(self) -> Optional[Dict[str, Any]]:
        """
        Get coordinator process statistics

        Returns:
            Dict with coordinator stats, or None if not running
        """
        # Try to find coordinator process
        for proc in psutil.process_iter(['pid', 'name', 'cmdline']):
            try:
                cmdline = proc.info.get('cmdline', [])
                if cmdline and 'coordinator.py' in ' '.join(cmdline):
                    # Found coordinator
                    p = psutil.Process(proc.info['pid'])
                    create_time = p.create_time()
                    uptime = datetime.now().timestamp() - create_time

                    return {
                        'pid': proc.info['pid'],
                        'uptime_seconds': int(uptime),
                        'cpu_percent': p.cpu_percent(interval=0.1),
                        'memory_mb': p.memory_info().rss / (1024 * 1024)
                    }
            except (psutil.NoSuchProcess, psutil.AccessDenied):
                continue

        return None

    def get_all_metrics(self) -> Dict[str, Any]:
        """
        Get complete metrics snapshot

        Returns:
            Dict with all metrics combined
        """
        return {
            'timestamp': datetime.now().isoformat(),
            'tasks': self.get_task_metrics(),
            'active_tasks': self.get_active_tasks(),
            'system': self.get_system_metrics(),
            'thermal': self.get_thermal_metrics(),
            'workers': self.get_worker_process_metrics(),
            'coordinator': self.get_coordinator_stats()
        }
