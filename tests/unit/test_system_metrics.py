"""Tests for system metrics collection"""

import pytest
from unittest.mock import MagicMock, patch, mock_open
from datetime import datetime
from adws.system_metrics import SystemMetrics, ProcessMetrics, MetricsCollector, AlertManager


class TestMetricsCollector:
    """Test metrics collector functionality"""

    @patch('psutil.cpu_percent')
    @patch('psutil.cpu_count')
    @patch('psutil.cpu_freq')
    @patch('psutil.virtual_memory')
    @patch('psutil.disk_usage')
    @patch('psutil.net_io_counters')
    @patch('psutil.getloadavg')
    def test_collect_system_metrics(
        self,
        mock_loadavg,
        mock_net,
        mock_disk,
        mock_memory,
        mock_cpu_freq,
        mock_cpu_count,
        mock_cpu_percent
    ):
        """Test collecting system metrics"""
        # Mock psutil responses
        mock_cpu_percent.return_value = 45.5
        mock_cpu_count.return_value = 4
        mock_cpu_freq.return_value = MagicMock(current=1500.0)
        mock_memory.return_value = MagicMock(
            percent=60.2,
            used=4 * 1024**3,  # 4 GB
            total=8 * 1024**3  # 8 GB
        )
        mock_disk.return_value = MagicMock(
            percent=75.0,
            used=60 * 1024**3,  # 60 GB
            total=128 * 1024**3,  # 128 GB
            free=68 * 1024**3  # 68 GB
        )
        mock_net.return_value = MagicMock(
            bytes_sent=1000000,
            bytes_recv=2000000
        )
        mock_loadavg.return_value = (1.5, 1.2, 0.9)

        collector = MetricsCollector()
        metrics = collector.collect_system_metrics()

        assert metrics.cpu_percent == 45.5
        assert metrics.cpu_count == 4
        assert metrics.memory_percent == 60.2
        assert metrics.disk_percent == 75.0
        assert metrics.load_avg_1min == 1.5
        assert metrics.network_bytes_sent == 1000000
        assert metrics.network_bytes_recv == 2000000

    @patch('psutil.Process')
    def test_collect_process_metrics(self, mock_process_class):
        """Test collecting process metrics"""
        mock_process = MagicMock()
        mock_process.name.return_value = "python3"
        mock_process.cpu_percent.return_value = 25.5
        mock_process.memory_percent.return_value = 15.3
        mock_process.memory_info.return_value = MagicMock(rss=100 * 1024**2)  # 100 MB
        mock_process.status.return_value = "running"
        mock_process.create_time.return_value = 1234567890.0
        mock_process.num_threads.return_value = 4

        mock_process_class.return_value = mock_process

        collector = MetricsCollector()
        process_metrics = collector.collect_process_metrics(12345)

        assert process_metrics is not None
        assert process_metrics.pid == 12345
        assert process_metrics.name == "python3"
        assert process_metrics.cpu_percent == 25.5
        assert process_metrics.memory_percent == 15.3
        assert process_metrics.num_threads == 4

    @patch('psutil.Process')
    def test_collect_process_metrics_no_such_process(self, mock_process_class):
        """Test handling of non-existent process"""
        import psutil
        mock_process_class.side_effect = psutil.NoSuchProcess(12345)

        collector = MetricsCollector()
        process_metrics = collector.collect_process_metrics(12345)

        assert process_metrics is None

    def test_get_temperature_from_file(self):
        """Test reading temperature from thermal file"""
        mock_data = "55000\n"  # 55 degrees C in millidegrees

        with patch('pathlib.Path.exists', return_value=True):
            with patch('pathlib.Path.read_text', return_value=mock_data):
                collector = MetricsCollector()
                temp = collector.get_temperature()
                assert temp == 55.0

    @patch('pathlib.Path.exists', return_value=False)
    @patch('psutil.sensors_temperatures')
    def test_get_temperature_from_psutil(self, mock_sensors, mock_exists):
        """Test reading temperature from psutil sensors"""
        mock_sensors.return_value = {
            'coretemp': [MagicMock(current=60.0)]
        }

        collector = MetricsCollector()
        temp = collector.get_temperature()
        assert temp == 60.0

    @patch('pathlib.Path.exists', return_value=False)
    @patch('psutil.sensors_temperatures', side_effect=AttributeError)
    def test_get_temperature_unavailable(self, mock_sensors, mock_exists):
        """Test handling when temperature is unavailable"""
        collector = MetricsCollector()
        temp = collector.get_temperature()
        assert temp is None

    @patch('psutil.disk_usage')
    def test_get_disk_space_recommendations(self, mock_disk):
        """Test disk space recommendations"""
        # Test critical disk usage
        mock_disk.return_value = MagicMock(percent=95.0)

        collector = MetricsCollector()
        recommendations = collector.get_disk_space_recommendations()

        assert len(recommendations) > 0
        assert any(r['severity'] == 'critical' for r in recommendations)

    def test_systemmetrics_to_dict(self):
        """Test converting SystemMetrics to dictionary"""
        metrics = SystemMetrics(
            timestamp="2025-11-02T10:00:00",
            cpu_percent=45.5,
            cpu_count=4,
            cpu_freq_current=1500.0,
            memory_percent=60.2,
            memory_used_gb=4.0,
            memory_total_gb=8.0,
            disk_percent=75.0,
            disk_used_gb=60.0,
            disk_total_gb=128.0,
            disk_free_gb=68.0,
            network_bytes_sent=1000000,
            network_bytes_recv=2000000,
            temperature_celsius=55.0,
            load_avg_1min=1.5,
            load_avg_5min=1.2,
            load_avg_15min=0.9
        )

        data = metrics.to_dict()
        assert data['cpu_percent'] == 45.5
        assert data['memory_percent'] == 60.2
        assert data['disk_percent'] == 75.0


class TestAlertManager:
    """Test alert management"""

    def test_check_thresholds_normal(self):
        """Test that normal metrics produce no alerts"""
        metrics = SystemMetrics(
            timestamp="2025-11-02T10:00:00",
            cpu_percent=50.0,
            cpu_count=4,
            cpu_freq_current=1500.0,
            memory_percent=60.0,
            memory_used_gb=4.0,
            memory_total_gb=8.0,
            disk_percent=70.0,
            disk_used_gb=60.0,
            disk_total_gb=128.0,
            disk_free_gb=68.0,
            network_bytes_sent=1000000,
            network_bytes_recv=2000000,
            temperature_celsius=55.0,
            load_avg_1min=2.0,
            load_avg_5min=1.5,
            load_avg_15min=1.0
        )

        alert_manager = AlertManager()
        alerts = alert_manager.check_thresholds(metrics)

        assert len(alerts) == 0

    def test_check_thresholds_cpu_warning(self):
        """Test CPU warning alert"""
        metrics = SystemMetrics(
            timestamp="2025-11-02T10:00:00",
            cpu_percent=80.0,  # Above warning threshold (75)
            cpu_count=4,
            cpu_freq_current=1500.0,
            memory_percent=60.0,
            memory_used_gb=4.0,
            memory_total_gb=8.0,
            disk_percent=70.0,
            disk_used_gb=60.0,
            disk_total_gb=128.0,
            disk_free_gb=68.0,
            network_bytes_sent=1000000,
            network_bytes_recv=2000000,
            temperature_celsius=55.0,
            load_avg_1min=2.0,
            load_avg_5min=1.5,
            load_avg_15min=1.0
        )

        alert_manager = AlertManager()
        alerts = alert_manager.check_thresholds(metrics)

        assert len(alerts) == 1
        assert alerts[0]['severity'] == 'warning'
        assert alerts[0]['metric'] == 'CPU Usage'

    def test_check_thresholds_multiple_critical(self):
        """Test multiple critical alerts"""
        metrics = SystemMetrics(
            timestamp="2025-11-02T10:00:00",
            cpu_percent=95.0,  # Critical
            cpu_count=4,
            cpu_freq_current=1500.0,
            memory_percent=96.0,  # Critical
            memory_used_gb=7.5,
            memory_total_gb=8.0,
            disk_percent=92.0,  # Critical
            disk_used_gb=120.0,
            disk_total_gb=128.0,
            disk_free_gb=8.0,
            network_bytes_sent=1000000,
            network_bytes_recv=2000000,
            temperature_celsius=82.0,  # Critical
            load_avg_1min=7.0,  # Critical
            load_avg_5min=6.5,
            load_avg_15min=5.0
        )

        alert_manager = AlertManager()
        alerts = alert_manager.check_thresholds(metrics)

        assert len(alerts) == 5  # CPU, Memory, Disk, Temperature, Load
        assert all(alert['severity'] == 'critical' for alert in alerts)

    def test_check_thresholds_no_temperature(self):
        """Test alerts when temperature is unavailable"""
        metrics = SystemMetrics(
            timestamp="2025-11-02T10:00:00",
            cpu_percent=50.0,
            cpu_count=4,
            cpu_freq_current=1500.0,
            memory_percent=60.0,
            memory_used_gb=4.0,
            memory_total_gb=8.0,
            disk_percent=70.0,
            disk_used_gb=60.0,
            disk_total_gb=128.0,
            disk_free_gb=68.0,
            network_bytes_sent=1000000,
            network_bytes_recv=2000000,
            temperature_celsius=None,  # No temperature sensor
            load_avg_1min=2.0,
            load_avg_5min=1.5,
            load_avg_15min=1.0
        )

        alert_manager = AlertManager()
        alerts = alert_manager.check_thresholds(metrics)

        # Should not crash, just skip temperature checks
        assert len(alerts) == 0
