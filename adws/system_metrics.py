#!/usr/bin/env python3
"""
System metrics collection for Raspberry Pi dashboard monitoring.

Collects real-time CPU, memory, disk, network, and thermal data.
"""

import psutil
import time
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from datetime import datetime
from pathlib import Path


@dataclass
class SystemMetrics:
    """Snapshot of system resource usage"""
    timestamp: str
    cpu_percent: float
    cpu_count: int
    cpu_freq_current: Optional[float]
    memory_percent: float
    memory_used_gb: float
    memory_total_gb: float
    disk_percent: float
    disk_used_gb: float
    disk_total_gb: float
    disk_free_gb: float
    network_bytes_sent: int
    network_bytes_recv: int
    temperature_celsius: Optional[float]
    load_avg_1min: float
    load_avg_5min: float
    load_avg_15min: float

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


@dataclass
class ProcessMetrics:
    """Metrics for a specific process (worker, coordinator, etc)"""
    pid: int
    name: str
    cpu_percent: float
    memory_percent: float
    memory_mb: float
    status: str
    create_time: float
    num_threads: int

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization"""
        return asdict(self)


class MetricsCollector:
    """Collects system and process-level metrics"""

    def __init__(self):
        self.last_network_counters = None
        self.last_network_time = None

    def get_temperature(self) -> Optional[float]:
        """Get Raspberry Pi CPU temperature (if available)"""
        try:
            # Try Raspberry Pi thermal zone
            thermal_file = Path("/sys/class/thermal/thermal_zone0/temp")
            if thermal_file.exists():
                temp_millidegrees = int(thermal_file.read_text().strip())
                return temp_millidegrees / 1000.0
        except Exception:
            pass

        try:
            # Try psutil sensors (may not work on all systems)
            temps = psutil.sensors_temperatures()
            if temps:
                # Get first available temperature sensor
                for name, entries in temps.items():
                    if entries:
                        return entries[0].current
        except (AttributeError, Exception):
            pass

        return None

    def get_network_rate(self) -> tuple[float, float]:
        """Get network send/receive rates in bytes per second"""
        counters = psutil.net_io_counters()
        current_time = time.time()

        if self.last_network_counters is None:
            self.last_network_counters = counters
            self.last_network_time = current_time
            return 0.0, 0.0

        time_delta = current_time - self.last_network_time
        if time_delta == 0:
            return 0.0, 0.0

        send_rate = (counters.bytes_sent - self.last_network_counters.bytes_sent) / time_delta
        recv_rate = (counters.bytes_recv - self.last_network_counters.bytes_recv) / time_delta

        self.last_network_counters = counters
        self.last_network_time = current_time

        return send_rate, recv_rate

    def collect_system_metrics(self) -> SystemMetrics:
        """Collect current system metrics snapshot"""
        # CPU metrics
        cpu_percent = psutil.cpu_percent(interval=0.1)
        cpu_count = psutil.cpu_count()

        # Try to get CPU frequency (may not be available on all systems)
        try:
            cpu_freq = psutil.cpu_freq()
            cpu_freq_current = cpu_freq.current if cpu_freq else None
        except Exception:
            cpu_freq_current = None

        # Memory metrics
        memory = psutil.virtual_memory()
        memory_used_gb = memory.used / (1024 ** 3)
        memory_total_gb = memory.total / (1024 ** 3)

        # Disk metrics (for root partition)
        disk = psutil.disk_usage('/')
        disk_used_gb = disk.used / (1024 ** 3)
        disk_total_gb = disk.total / (1024 ** 3)
        disk_free_gb = disk.free / (1024 ** 3)

        # Network metrics
        network_counters = psutil.net_io_counters()

        # Temperature
        temperature = self.get_temperature()

        # Load average
        load_avg = psutil.getloadavg()

        return SystemMetrics(
            timestamp=datetime.now().isoformat(),
            cpu_percent=cpu_percent,
            cpu_count=cpu_count,
            cpu_freq_current=cpu_freq_current,
            memory_percent=memory.percent,
            memory_used_gb=round(memory_used_gb, 2),
            memory_total_gb=round(memory_total_gb, 2),
            disk_percent=disk.percent,
            disk_used_gb=round(disk_used_gb, 2),
            disk_total_gb=round(disk_total_gb, 2),
            disk_free_gb=round(disk_free_gb, 2),
            network_bytes_sent=network_counters.bytes_sent,
            network_bytes_recv=network_counters.bytes_recv,
            temperature_celsius=temperature,
            load_avg_1min=load_avg[0],
            load_avg_5min=load_avg[1],
            load_avg_15min=load_avg[2]
        )

    def collect_process_metrics(self, pid: int) -> Optional[ProcessMetrics]:
        """Collect metrics for a specific process"""
        try:
            process = psutil.Process(pid)

            return ProcessMetrics(
                pid=pid,
                name=process.name(),
                cpu_percent=process.cpu_percent(interval=0.1),
                memory_percent=process.memory_percent(),
                memory_mb=round(process.memory_info().rss / (1024 ** 2), 2),
                status=process.status(),
                create_time=process.create_time(),
                num_threads=process.num_threads()
            )
        except (psutil.NoSuchProcess, psutil.AccessDenied, psutil.ZombieProcess):
            return None

    def collect_worker_metrics(self, worker_pids: List[int]) -> List[ProcessMetrics]:
        """Collect metrics for all worker processes"""
        metrics = []
        for pid in worker_pids:
            worker_metrics = self.collect_process_metrics(pid)
            if worker_metrics:
                metrics.append(worker_metrics)
        return metrics

    def get_disk_space_recommendations(self) -> List[Dict[str, str]]:
        """Analyze disk usage and provide cleanup recommendations"""
        recommendations = []

        # Check disk usage
        disk = psutil.disk_usage('/')
        disk_percent = disk.percent

        if disk_percent > 90:
            recommendations.append({
                "severity": "critical",
                "title": "Critical disk space",
                "message": f"Disk usage at {disk_percent}%! Immediate cleanup needed."
            })
        elif disk_percent > 80:
            recommendations.append({
                "severity": "warning",
                "title": "High disk usage",
                "message": f"Disk usage at {disk_percent}%. Consider cleanup soon."
            })
        elif disk_percent > 70:
            recommendations.append({
                "severity": "info",
                "title": "Moderate disk usage",
                "message": f"Disk usage at {disk_percent}%. Monitor space."
            })

        # Check for large log directories
        try:
            logs_dir = Path("logs")
            if logs_dir.exists():
                log_size_mb = sum(f.stat().st_size for f in logs_dir.rglob('*') if f.is_file()) / (1024 ** 2)
                if log_size_mb > 500:
                    recommendations.append({
                        "severity": "info",
                        "title": "Large log directory",
                        "message": f"logs/ directory is {log_size_mb:.1f} MB. Consider archiving old logs."
                    })
        except Exception:
            pass

        # Check for git worktrees
        try:
            trees_dir = Path("trees")
            if trees_dir.exists():
                tree_count = sum(1 for d in trees_dir.iterdir() if d.is_dir())
                if tree_count > 10:
                    recommendations.append({
                        "severity": "info",
                        "title": "Many git worktrees",
                        "message": f"{tree_count} worktrees in trees/. Consider cleanup of completed tasks."
                    })
        except Exception:
            pass

        # Check Python cache
        try:
            cache_dirs = list(Path(".").rglob("__pycache__"))
            if len(cache_dirs) > 100:
                recommendations.append({
                    "severity": "info",
                    "title": "Python cache buildup",
                    "message": f"{len(cache_dirs)} __pycache__ directories. Run: find . -type d -name '__pycache__' -exec rm -r {{}} +"
                })
        except Exception:
            pass

        return recommendations


class AlertManager:
    """Manages alerts and threshold checks for system resources"""

    def __init__(self):
        self.thresholds = {
            'cpu_percent': {'warning': 75, 'critical': 90},
            'memory_percent': {'warning': 80, 'critical': 95},
            'disk_percent': {'warning': 80, 'critical': 90},
            'temperature_celsius': {'warning': 70, 'critical': 80},
            'load_avg_1min': {'warning': 4.0, 'critical': 6.0}  # For typical 4-core Pi
        }
        self.active_alerts = []

    def check_thresholds(self, metrics: SystemMetrics) -> List[Dict[str, str]]:
        """Check metrics against thresholds and return alerts"""
        alerts = []

        # Check CPU
        if metrics.cpu_percent > self.thresholds['cpu_percent']['critical']:
            alerts.append({
                'severity': 'critical',
                'metric': 'CPU Usage',
                'value': f"{metrics.cpu_percent}%",
                'message': f"Critical CPU usage: {metrics.cpu_percent}%"
            })
        elif metrics.cpu_percent > self.thresholds['cpu_percent']['warning']:
            alerts.append({
                'severity': 'warning',
                'metric': 'CPU Usage',
                'value': f"{metrics.cpu_percent}%",
                'message': f"High CPU usage: {metrics.cpu_percent}%"
            })

        # Check memory
        if metrics.memory_percent > self.thresholds['memory_percent']['critical']:
            alerts.append({
                'severity': 'critical',
                'metric': 'Memory Usage',
                'value': f"{metrics.memory_percent}%",
                'message': f"Critical memory usage: {metrics.memory_percent}%"
            })
        elif metrics.memory_percent > self.thresholds['memory_percent']['warning']:
            alerts.append({
                'severity': 'warning',
                'metric': 'Memory Usage',
                'value': f"{metrics.memory_percent}%",
                'message': f"High memory usage: {metrics.memory_percent}%"
            })

        # Check disk
        if metrics.disk_percent > self.thresholds['disk_percent']['critical']:
            alerts.append({
                'severity': 'critical',
                'metric': 'Disk Usage',
                'value': f"{metrics.disk_percent}%",
                'message': f"Critical disk usage: {metrics.disk_percent}% ({metrics.disk_free_gb:.1f} GB free)"
            })
        elif metrics.disk_percent > self.thresholds['disk_percent']['warning']:
            alerts.append({
                'severity': 'warning',
                'metric': 'Disk Usage',
                'value': f"{metrics.disk_percent}%",
                'message': f"High disk usage: {metrics.disk_percent}% ({metrics.disk_free_gb:.1f} GB free)"
            })

        # Check temperature
        if metrics.temperature_celsius:
            if metrics.temperature_celsius > self.thresholds['temperature_celsius']['critical']:
                alerts.append({
                    'severity': 'critical',
                    'metric': 'Temperature',
                    'value': f"{metrics.temperature_celsius}°C",
                    'message': f"Critical temperature: {metrics.temperature_celsius}°C"
                })
            elif metrics.temperature_celsius > self.thresholds['temperature_celsius']['warning']:
                alerts.append({
                    'severity': 'warning',
                    'metric': 'Temperature',
                    'value': f"{metrics.temperature_celsius}°C",
                    'message': f"High temperature: {metrics.temperature_celsius}°C"
                })

        # Check load average
        if metrics.load_avg_1min > self.thresholds['load_avg_1min']['critical']:
            alerts.append({
                'severity': 'critical',
                'metric': 'Load Average',
                'value': f"{metrics.load_avg_1min:.2f}",
                'message': f"Critical load average: {metrics.load_avg_1min:.2f}"
            })
        elif metrics.load_avg_1min > self.thresholds['load_avg_1min']['warning']:
            alerts.append({
                'severity': 'warning',
                'metric': 'Load Average',
                'value': f"{metrics.load_avg_1min:.2f}",
                'message': f"High load average: {metrics.load_avg_1min:.2f}"
            })

        self.active_alerts = alerts
        return alerts


if __name__ == '__main__':
    """Test metrics collection"""
    collector = MetricsCollector()
    alert_manager = AlertManager()

    print("Collecting system metrics...")
    metrics = collector.collect_system_metrics()

    print(f"\n📊 System Metrics:")
    print(f"  CPU: {metrics.cpu_percent}% ({metrics.cpu_count} cores)")
    print(f"  Memory: {metrics.memory_percent}% ({metrics.memory_used_gb:.1f}/{metrics.memory_total_gb:.1f} GB)")
    print(f"  Disk: {metrics.disk_percent}% ({metrics.disk_used_gb:.1f}/{metrics.disk_total_gb:.1f} GB)")
    if metrics.temperature_celsius:
        print(f"  Temperature: {metrics.temperature_celsius}°C")
    print(f"  Load: {metrics.load_avg_1min:.2f}, {metrics.load_avg_5min:.2f}, {metrics.load_avg_15min:.2f}")

    # Check for alerts
    alerts = alert_manager.check_thresholds(metrics)
    if alerts:
        print(f"\n⚠️  Active Alerts:")
        for alert in alerts:
            print(f"  [{alert['severity'].upper()}] {alert['message']}")
    else:
        print(f"\n✅ All metrics within normal ranges")

    # Get cleanup recommendations
    recommendations = collector.get_disk_space_recommendations()
    if recommendations:
        print(f"\n💡 Cleanup Recommendations:")
        for rec in recommendations:
            print(f"  [{rec['severity'].upper()}] {rec['title']}: {rec['message']}")
