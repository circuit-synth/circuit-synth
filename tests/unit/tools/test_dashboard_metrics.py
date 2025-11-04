"""Tests for dashboard system metrics collection"""

import pytest
from circuit_synth.tools.dashboard.metrics import SystemMetrics


class TestSystemMetrics:
    """Test system metrics collection"""

    def test_collect_cpu_metrics(self):
        """Test CPU metrics collection"""
        metrics = SystemMetrics()
        cpu_data = metrics.collect_cpu()

        assert "percent" in cpu_data
        assert "per_cpu" in cpu_data
        assert "load_avg" in cpu_data
        assert 0 <= cpu_data["percent"] <= 100
        assert len(cpu_data["per_cpu"]) > 0
        assert len(cpu_data["load_avg"]) == 3  # 1, 5, 15 minute averages

    def test_collect_memory_metrics(self):
        """Test memory metrics collection"""
        metrics = SystemMetrics()
        mem_data = metrics.collect_memory()

        assert "total" in mem_data
        assert "available" in mem_data
        assert "percent" in mem_data
        assert "used" in mem_data
        assert 0 <= mem_data["percent"] <= 100
        assert mem_data["used"] <= mem_data["total"]

    def test_collect_disk_metrics(self):
        """Test disk metrics collection"""
        metrics = SystemMetrics()
        disk_data = metrics.collect_disk()

        assert "total" in disk_data
        assert "used" in disk_data
        assert "free" in disk_data
        assert "percent" in disk_data
        assert 0 <= disk_data["percent"] <= 100
        assert disk_data["used"] + disk_data["free"] <= disk_data["total"] * 1.1  # Allow some overhead

    def test_collect_network_metrics(self):
        """Test network metrics collection"""
        metrics = SystemMetrics()
        net_data = metrics.collect_network()

        assert "bytes_sent" in net_data
        assert "bytes_recv" in net_data
        assert "packets_sent" in net_data
        assert "packets_recv" in net_data
        assert all(v >= 0 for v in net_data.values())

    def test_collect_thermal_metrics(self):
        """Test thermal metrics collection (Raspberry Pi specific)"""
        metrics = SystemMetrics()
        thermal_data = metrics.collect_thermal()

        # Should return temperature data or None if not on Pi
        if thermal_data is not None:
            assert "cpu_temp" in thermal_data
            assert 0 <= thermal_data["cpu_temp"] <= 150  # Reasonable temp range

    def test_collect_process_metrics(self):
        """Test process-level metrics collection"""
        metrics = SystemMetrics()
        process_data = metrics.collect_processes()

        assert isinstance(process_data, list)
        if len(process_data) > 0:
            proc = process_data[0]
            assert "pid" in proc
            assert "name" in proc
            assert "cpu_percent" in proc
            assert "memory_percent" in proc
            assert "status" in proc

    def test_collect_all_metrics(self):
        """Test collecting all metrics at once"""
        metrics = SystemMetrics()
        all_data = metrics.collect_all()

        assert "cpu" in all_data
        assert "memory" in all_data
        assert "disk" in all_data
        assert "network" in all_data
        assert "timestamp" in all_data

    def test_metrics_snapshot_format(self):
        """Test that metrics snapshot has correct format"""
        metrics = SystemMetrics()
        snapshot = metrics.snapshot()

        assert isinstance(snapshot, dict)
        assert "timestamp" in snapshot
        assert "cpu" in snapshot
        assert "memory" in snapshot
        assert "disk" in snapshot
