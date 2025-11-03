"""
Tests for dashboard metrics aggregator

Following TDD approach - tests written before implementation.
"""

import pytest
import tempfile
from pathlib import Path
from datetime import datetime
from circuit_synth.tools.dashboard.metrics import MetricsAggregator


class TestMetricsAggregator:
    """Test metrics aggregation functionality"""

    @pytest.fixture
    def temp_tasks_file(self):
        """Create a temporary tasks.md file for testing"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("""# Circuit-Synth Work Queue

**Last updated:** 2025-11-02 10:30:00

---

## Pending

[] gh-455: Dashboard: Add system performance metrics and resource monitoring {p1}
[] gh-456: Add token budget monitoring {p2}

---

## Active (max 3)

[🟡 w-abc123, trees/gh-450] gh-450: Add live agent logs viewer
- Started: 2025-11-02 10:00:00
- PID: 12345

[🟡 w-def456, trees/gh-451] gh-451: Implement agent error handling
- Started: 2025-11-02 10:15:00
- PID: 12346

---

## Completed Today

[✅ 0b06456, w-ghi789] gh-461: Phase 1: Bidirectional test infrastructure
- Completed: 2025-11-02 09:45:00
- PR: https://github.com/circuit-synth/circuit-synth/pull/461

---

## Failed

[❌ w-jkl012] gh-440: Some failed task
- Failed: 2025-11-02 08:30:00
- Reason: Worker finished but no PR created

---

## Blocked

[⏰ w-mno345] gh-435: Some blocked task
- Blocked since: 2025-11-02 07:00:00
""")
            path = Path(f.name)

        yield path

        # Cleanup
        if path.exists():
            path.unlink()

    def test_parse_tasks_md(self, temp_tasks_file):
        """Test parsing tasks.md file"""
        aggregator = MetricsAggregator(tasks_file=temp_tasks_file)
        metrics = aggregator.get_task_metrics()

        assert metrics['pending_count'] == 2
        assert metrics['active_count'] == 2
        assert metrics['completed_count'] == 1
        assert metrics['failed_count'] == 1
        assert metrics['blocked_count'] == 1
        assert metrics['total_count'] == 7

    def test_get_active_tasks(self, temp_tasks_file):
        """Test getting active task details"""
        aggregator = MetricsAggregator(tasks_file=temp_tasks_file)
        active_tasks = aggregator.get_active_tasks()

        assert len(active_tasks) == 2
        assert active_tasks[0]['task_id'] == 'gh-450'
        assert active_tasks[0]['worker_id'] == 'w-abc123'
        assert active_tasks[0]['pid'] == 12345
        assert active_tasks[1]['task_id'] == 'gh-451'

    def test_get_system_metrics(self):
        """Test system resource metrics collection"""
        aggregator = MetricsAggregator()
        metrics = aggregator.get_system_metrics()

        # Check required fields exist
        assert 'cpu_percent' in metrics
        assert 'memory_percent' in metrics
        assert 'memory_available_gb' in metrics
        assert 'disk_percent' in metrics
        assert 'disk_free_gb' in metrics

        # Check values are reasonable
        assert 0 <= metrics['cpu_percent'] <= 100
        assert 0 <= metrics['memory_percent'] <= 100
        assert metrics['memory_available_gb'] >= 0
        assert 0 <= metrics['disk_percent'] <= 100
        assert metrics['disk_free_gb'] >= 0

    def test_get_thermal_metrics(self):
        """Test Raspberry Pi thermal monitoring"""
        aggregator = MetricsAggregator()
        thermal = aggregator.get_thermal_metrics()

        # Should return data or None if not on Raspberry Pi
        if thermal is not None:
            assert 'cpu_temp' in thermal
            assert thermal['cpu_temp'] >= 0  # Temperature in Celsius
            assert thermal['cpu_temp'] < 150  # Sanity check

    def test_get_worker_process_metrics(self, temp_tasks_file):
        """Test monitoring worker process resources"""
        aggregator = MetricsAggregator(tasks_file=temp_tasks_file)

        # Note: PIDs 12345 and 12346 likely don't exist in test environment
        # This tests the function handles missing processes gracefully
        worker_metrics = aggregator.get_worker_process_metrics()

        assert isinstance(worker_metrics, list)
        # Each worker should have metrics or be marked as not found
        for worker in worker_metrics:
            assert 'task_id' in worker
            assert 'worker_id' in worker
            assert 'pid' in worker

    def test_get_coordinator_stats(self, temp_tasks_file):
        """Test getting coordinator statistics"""
        aggregator = MetricsAggregator(tasks_file=temp_tasks_file)
        stats = aggregator.get_coordinator_stats()

        assert stats is None or 'uptime_seconds' in stats
        # Note: uptime requires reading coordinator process, may not exist in test

    def test_get_all_metrics(self, temp_tasks_file):
        """Test getting complete metrics snapshot"""
        aggregator = MetricsAggregator(tasks_file=temp_tasks_file)
        all_metrics = aggregator.get_all_metrics()

        # Check all sections present
        assert 'timestamp' in all_metrics
        assert 'tasks' in all_metrics
        assert 'active_tasks' in all_metrics
        assert 'system' in all_metrics
        assert 'workers' in all_metrics

        # Validate timestamp format
        timestamp = all_metrics['timestamp']
        assert isinstance(timestamp, str)
        # Should be ISO format
        datetime.fromisoformat(timestamp)

    def test_empty_tasks_file(self):
        """Test handling of missing or empty tasks.md"""
        with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as f:
            f.write("")
            path = Path(f.name)

        try:
            aggregator = MetricsAggregator(tasks_file=path)
            metrics = aggregator.get_task_metrics()

            assert metrics['pending_count'] == 0
            assert metrics['active_count'] == 0
            assert metrics['completed_count'] == 0
            assert metrics['total_count'] == 0
        finally:
            path.unlink()

    def test_nonexistent_tasks_file(self):
        """Test handling of nonexistent tasks.md"""
        aggregator = MetricsAggregator(tasks_file=Path("/nonexistent/tasks.md"))
        metrics = aggregator.get_task_metrics()

        # Should return zero counts rather than error
        assert metrics['pending_count'] == 0
        assert metrics['total_count'] == 0
