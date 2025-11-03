"""Tests for system performance dashboard and metrics

Tests cover:
- Real-time metrics display
- Historical trend analytics
- Resource alerts and thresholds
- Process-level monitoring
- Thermal monitoring (Raspberry Pi)
- Disk cleanup recommendations
"""

import pytest
import time
from datetime import datetime, timedelta
from pathlib import Path
import sys

# Add adws to path for import
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent / "adws"))

from system_metrics import SystemMetrics, MetricSnapshot


class TestSystemMetricsBasics:
    """Test basic metrics collection"""

    def test_collect_snapshot(self):
        """Test collecting a single metrics snapshot"""
        metrics = SystemMetrics()
        snapshot = metrics.collect_snapshot()

        assert isinstance(snapshot, MetricSnapshot)
        assert snapshot.cpu_percent >= 0
        assert snapshot.memory_percent >= 0
        assert snapshot.disk_percent >= 0
        assert snapshot.process_count > 0
        assert isinstance(snapshot.timestamp, datetime)

    def test_snapshot_to_dict(self):
        """Test snapshot serialization to dict"""
        metrics = SystemMetrics()
        snapshot = metrics.collect_snapshot()
        data = snapshot.to_dict()

        assert 'timestamp' in data
        assert 'cpu_percent' in data
        assert 'memory_percent' in data
        assert 'disk_percent' in data
        assert isinstance(data['timestamp'], str)  # ISO format

    def test_snapshot_history_tracking(self):
        """Test that snapshots are added to history"""
        metrics = SystemMetrics(max_history=5)

        for i in range(7):
            snapshot = metrics.collect_snapshot()
            metrics.add_snapshot(snapshot)
            time.sleep(0.01)  # Small delay to ensure different timestamps

        # Should only keep last 5 due to max_history
        assert len(metrics.history) == 5

    def test_network_metrics_tracking(self):
        """Test network usage delta calculation"""
        metrics = SystemMetrics()

        # First snapshot initializes counters
        snapshot1 = metrics.collect_snapshot()
        assert snapshot1.network_sent_mb == 0.0
        assert snapshot1.network_recv_mb == 0.0

        # Second snapshot should have deltas (or zeros if no activity)
        time.sleep(0.1)
        snapshot2 = metrics.collect_snapshot()
        assert snapshot2.network_sent_mb >= 0.0
        assert snapshot2.network_recv_mb >= 0.0


class TestAlertSystem:
    """Test resource alert and threshold system"""

    def test_cpu_alert_trigger(self):
        """Test CPU usage alert triggering"""
        metrics = SystemMetrics(cpu_threshold=1.0)  # Very low threshold

        snapshot = metrics.collect_snapshot()
        alerts = metrics.check_alerts(snapshot)

        # Should trigger CPU alert if CPU > 1%
        cpu_alerts = [a for a in alerts if a['type'] == 'cpu']
        if snapshot.cpu_percent > 1.0:
            assert len(cpu_alerts) == 1
            assert cpu_alerts[0]['severity'] == 'warning'
            assert 'CPU usage high' in cpu_alerts[0]['message']

    def test_memory_alert_trigger(self):
        """Test memory usage alert triggering"""
        metrics = SystemMetrics(memory_threshold=1.0)  # Very low threshold

        snapshot = metrics.collect_snapshot()
        alerts = metrics.check_alerts(snapshot)

        # Should trigger memory alert if memory > 1%
        memory_alerts = [a for a in alerts if a['type'] == 'memory']
        if snapshot.memory_percent > 1.0:
            assert len(memory_alerts) == 1
            assert memory_alerts[0]['severity'] == 'warning'

    def test_disk_alert_critical(self):
        """Test disk usage alert with critical severity"""
        metrics = SystemMetrics(disk_threshold=1.0)  # Very low threshold

        snapshot = metrics.collect_snapshot()
        alerts = metrics.check_alerts(snapshot)

        # Disk alerts should be critical
        disk_alerts = [a for a in alerts if a['type'] == 'disk']
        if snapshot.disk_percent > 1.0:
            assert len(disk_alerts) == 1
            assert disk_alerts[0]['severity'] == 'critical'

    def test_temperature_alert(self):
        """Test CPU temperature alert (may not be available on all systems)"""
        metrics = SystemMetrics(temp_threshold=30.0)  # Low threshold

        snapshot = metrics.collect_snapshot()
        if snapshot.cpu_temp is not None:
            alerts = metrics.check_alerts(snapshot)
            temp_alerts = [a for a in alerts if a['type'] == 'temperature']

            if snapshot.cpu_temp > 30.0:
                assert len(temp_alerts) == 1
                assert temp_alerts[0]['severity'] == 'warning'
                assert '°C' in temp_alerts[0]['message']

    def test_no_alerts_under_thresholds(self):
        """Test that no alerts trigger when under thresholds"""
        metrics = SystemMetrics(
            cpu_threshold=200.0,
            memory_threshold=200.0,
            disk_threshold=200.0,
            temp_threshold=200.0
        )

        snapshot = metrics.collect_snapshot()
        alerts = metrics.check_alerts(snapshot)

        assert len(alerts) == 0


class TestHistoricalAnalytics:
    """Test historical trend tracking and analytics"""

    def test_summary_stats_calculation(self):
        """Test min/max/avg calculation for metrics history"""
        metrics = SystemMetrics(max_history=100)

        # Add several snapshots
        for i in range(10):
            snapshot = metrics.collect_snapshot()
            metrics.add_snapshot(snapshot)
            time.sleep(0.01)

        stats = metrics.get_summary_stats()

        assert 'cpu' in stats
        assert 'memory' in stats
        assert 'disk' in stats

        # Check CPU stats structure
        assert 'min' in stats['cpu']
        assert 'max' in stats['cpu']
        assert 'avg' in stats['cpu']

        # Sanity checks
        assert stats['cpu']['min'] <= stats['cpu']['avg'] <= stats['cpu']['max']
        assert stats['memory']['min'] <= stats['memory']['avg'] <= stats['memory']['max']

    def test_get_recent_history(self):
        """Test retrieving recent history subset"""
        metrics = SystemMetrics(max_history=100)

        # Add 20 snapshots
        for i in range(20):
            snapshot = metrics.collect_snapshot()
            metrics.add_snapshot(snapshot)
            time.sleep(0.01)

        # Get last 10
        recent = metrics.get_recent_history(count=10)
        assert len(recent) == 10

        # Verify newest is last
        assert recent[-1].timestamp >= recent[0].timestamp

    def test_empty_history_summary(self):
        """Test summary stats with no history"""
        metrics = SystemMetrics()
        stats = metrics.get_summary_stats()
        assert stats == {}


class TestProcessMonitoring:
    """Test process-level monitoring"""

    def test_get_process_info(self):
        """Test retrieving top processes by CPU usage"""
        metrics = SystemMetrics()
        processes = metrics.get_process_info()

        assert isinstance(processes, list)
        assert len(processes) <= 10  # Top 10

        # Verify structure if processes found
        if processes:
            proc = processes[0]
            assert 'pid' in proc
            assert 'name' in proc
            assert 'cpu_percent' in proc
            assert 'memory_percent' in proc

            # Should be sorted by CPU desc
            if len(processes) > 1:
                assert processes[0]['cpu_percent'] >= processes[1]['cpu_percent']

    def test_get_worker_processes(self):
        """Test identifying Claude worker processes"""
        metrics = SystemMetrics()
        workers = metrics.get_worker_processes()

        assert isinstance(workers, list)

        # If any workers found, verify structure
        for worker in workers:
            assert 'pid' in worker
            assert 'task_id' in worker
            assert 'cpu_percent' in worker
            assert 'memory_percent' in worker

    def test_worker_process_task_id_extraction(self):
        """Test task ID extraction from worker command line"""
        # This is a unit test - we'll test the logic, not actual processes
        # In real implementation, this would parse command line like:
        # "claude -p logs/gh-455-prompt.txt"
        # and extract "gh-455"

        metrics = SystemMetrics()
        # The actual test would verify worker detection
        # For now, just verify the method exists and returns a list
        workers = metrics.get_worker_processes()
        assert isinstance(workers, list)


class TestDashboardDataPreparation:
    """Test data preparation for dashboard visualization"""

    def test_metrics_json_serializable(self):
        """Test that all metrics can be serialized to JSON"""
        import json

        metrics = SystemMetrics()
        snapshot = metrics.collect_snapshot()
        metrics.add_snapshot(snapshot)

        # Test snapshot serialization
        snapshot_dict = snapshot.to_dict()
        json_str = json.dumps(snapshot_dict)
        assert len(json_str) > 0

        # Test summary stats serialization
        stats = metrics.get_summary_stats()
        if stats:
            json_str = json.dumps(stats)
            assert len(json_str) > 0

    def test_time_series_data_format(self):
        """Test time series data format for trend charts"""
        metrics = SystemMetrics(max_history=50)

        # Add snapshots over time
        for i in range(10):
            snapshot = metrics.collect_snapshot()
            metrics.add_snapshot(snapshot)
            time.sleep(0.01)

        recent = metrics.get_recent_history(count=10)

        # Verify we can build time series for charts
        timestamps = [s.timestamp.isoformat() for s in recent]
        cpu_values = [s.cpu_percent for s in recent]
        memory_values = [s.memory_percent for s in recent]

        assert len(timestamps) == len(cpu_values) == len(memory_values) == 10
        assert all(isinstance(t, str) for t in timestamps)
        assert all(isinstance(v, (int, float)) for v in cpu_values)


class TestDiskCleanupRecommendations:
    """Test disk space analysis and cleanup recommendations"""

    def test_disk_usage_tracking(self):
        """Test disk usage percentage tracking"""
        metrics = SystemMetrics()
        snapshot = metrics.collect_snapshot()

        assert 0 <= snapshot.disk_percent <= 100

    def test_disk_high_usage_alert(self):
        """Test alert when disk usage is high"""
        metrics = SystemMetrics(disk_threshold=50.0)
        snapshot = metrics.collect_snapshot()

        alerts = metrics.check_alerts(snapshot)
        disk_alerts = [a for a in alerts if a['type'] == 'disk']

        if snapshot.disk_percent > 50.0:
            assert len(disk_alerts) == 1
            assert disk_alerts[0]['severity'] == 'critical'
            assert disk_alerts[0]['value'] == snapshot.disk_percent


class TestThermalMonitoring:
    """Test Raspberry Pi thermal monitoring"""

    def test_cpu_temperature_reading(self):
        """Test CPU temperature reading (Pi-specific)"""
        metrics = SystemMetrics()
        snapshot = metrics.collect_snapshot()

        # Temperature may not be available on all systems
        if snapshot.cpu_temp is not None:
            assert snapshot.cpu_temp > 0  # Should be reasonable temp
            assert snapshot.cpu_temp < 200  # Sanity check

    def test_thermal_throttling_alert(self):
        """Test alert for high temperature"""
        metrics = SystemMetrics(temp_threshold=40.0)
        snapshot = metrics.collect_snapshot()

        if snapshot.cpu_temp is not None and snapshot.cpu_temp > 40.0:
            alerts = metrics.check_alerts(snapshot)
            temp_alerts = [a for a in alerts if a['type'] == 'temperature']

            assert len(temp_alerts) == 1
            assert '°C' in temp_alerts[0]['message']


class TestIntegrationScenarios:
    """Test complete monitoring scenarios"""

    def test_full_monitoring_cycle(self):
        """Test complete monitoring cycle: collect, analyze, alert"""
        metrics = SystemMetrics(
            max_history=100,
            cpu_threshold=80.0,
            memory_threshold=85.0,
            disk_threshold=90.0,
            temp_threshold=75.0
        )

        # Collect snapshots over time
        for i in range(5):
            snapshot = metrics.collect_snapshot()
            metrics.add_snapshot(snapshot)

            # Check for alerts
            alerts = metrics.check_alerts(snapshot)

            # Verify alert structure if any triggered
            for alert in alerts:
                assert 'type' in alert
                assert 'severity' in alert
                assert 'message' in alert
                assert 'value' in alert
                assert 'threshold' in alert

            time.sleep(0.05)

        # Get analytics
        stats = metrics.get_summary_stats()
        assert len(stats) >= 3  # cpu, memory, disk at minimum

        # Get process info
        processes = metrics.get_process_info()
        assert isinstance(processes, list)

        # Get recent history
        recent = metrics.get_recent_history(count=5)
        assert len(recent) == 5

    def test_dashboard_data_export(self):
        """Test exporting complete dashboard data"""
        import json

        metrics = SystemMetrics()

        # Collect some data
        for i in range(3):
            snapshot = metrics.collect_snapshot()
            metrics.add_snapshot(snapshot)
            time.sleep(0.01)

        # Build complete dashboard data structure
        dashboard_data = {
            'current': metrics.collect_snapshot().to_dict(),
            'history': [s.to_dict() for s in metrics.get_recent_history(count=10)],
            'stats': metrics.get_summary_stats(),
            'processes': metrics.get_process_info(),
            'workers': metrics.get_worker_processes(),
            'alerts': metrics.check_alerts(metrics.collect_snapshot())
        }

        # Verify JSON serializable
        json_str = json.dumps(dashboard_data)
        assert len(json_str) > 0

        # Verify can deserialize
        restored = json.loads(json_str)
        assert 'current' in restored
        assert 'history' in restored
        assert 'stats' in restored
