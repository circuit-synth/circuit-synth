"""
Performance Monitoring for Unified Logging System
================================================

Provides comprehensive performance monitoring capabilities including:
- High-precision timing measurements
- Memory usage tracking
- CPU utilization monitoring
- Custom metrics collection
- Performance analytics and reporting
"""

import gc
import json
import statistics
import threading
import time
from collections import defaultdict, deque
from contextlib import contextmanager
from dataclasses import asdict, dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

import psutil

from .context_manager import get_context_extras


@dataclass
class PerformanceMetric:
    """Data structure for performance metrics."""

    operation: str
    duration_ms: float
    user_id: str
    session_id: str
    component: str
    timestamp: str
    metadata: Dict[str, Any] = field(default_factory=dict)
    memory_usage_mb: Optional[float] = None
    cpu_percent: Optional[float] = None
    thread_id: Optional[int] = None
    process_id: Optional[int] = None


@dataclass
class SystemMetrics:
    """System-level performance metrics."""

    timestamp: str
    cpu_percent: float
    memory_percent: float
    memory_used_mb: float
    memory_available_mb: float
    disk_usage_percent: float
    active_threads: int
    active_processes: int


@dataclass
class OperationStats:
    """Statistics for a specific operation."""

    operation_name: str
    total_calls: int
    total_duration_ms: float
    avg_duration_ms: float
    min_duration_ms: float
    max_duration_ms: float
    p50_duration_ms: float
    p95_duration_ms: float
    p99_duration_ms: float
    error_count: int
    last_called: str


class PerformanceLogger:
    """
    High-performance timing and metrics collection.

    This class provides comprehensive performance monitoring capabilities
    with minimal overhead. It supports timing operations, collecting custom
    metrics, and generating performance reports.
    """

    def __init__(self, context_logger=None):
        self.logger = context_logger
        self._active_timers: Dict[str, float] = {}
        self._operation_history: Dict[str, deque] = defaultdict(
            lambda: deque(maxlen=1000)
        )
        self._system_metrics_history: deque = deque(maxlen=100)
        self._lock = threading.RLock()
        self._metrics_enabled = True
        self._memory_tracking_enabled = True
        self._cpu_tracking_enabled = True

        # Performance tracking
        self._last_gc_time = time.time()
        self._gc_interval = 300  # 5 minutes

        # Start system monitoring thread
        self._monitoring_thread = None
        self._monitoring_enabled = False
        self._start_system_monitoring()

    def _start_system_monitoring(self):
        """Start background system monitoring."""
        if not self._monitoring_enabled:
            self._monitoring_enabled = True
            self._monitoring_thread = threading.Thread(
                target=self._system_monitoring_loop, daemon=True
            )
            self._monitoring_thread.start()

    def _system_monitoring_loop(self):
        """Background loop for collecting system metrics."""
        while self._monitoring_enabled:
            try:
                self._collect_system_metrics()
                time.sleep(60)  # Collect every minute
            except Exception as e:
                if self.logger:
                    self.logger.error(
                        f"System monitoring error: {e}", component="PERF_MONITOR"
                    )

    def _collect_system_metrics(self):
        """Collect current system metrics."""
        try:
            # CPU and memory
            cpu_percent = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage("/")

            # Process information
            process = psutil.Process()
            thread_count = process.num_threads()

            metrics = SystemMetrics(
                timestamp=datetime.utcnow().isoformat(),
                cpu_percent=cpu_percent,
                memory_percent=memory.percent,
                memory_used_mb=memory.used / (1024 * 1024),
                memory_available_mb=memory.available / (1024 * 1024),
                disk_usage_percent=disk.percent,
                active_threads=thread_count,
                active_processes=len(psutil.pids()),
            )

            with self._lock:
                self._system_metrics_history.append(metrics)

            # Log system metrics if logger is available
            if self.logger:
                from loguru import logger

                logger.bind(
                    log_type="performance",
                    metric_type="system",
                    component="PERFORMANCE",
                    user="system",
                    session="performance",
                    request_id="system_metrics",
                    **asdict(metrics),
                ).info(json.dumps(asdict(metrics)))

        except Exception as e:
            if self.logger:
                self.logger.error(
                    f"Failed to collect system metrics: {e}", component="PERF_MONITOR"
                )

    @contextmanager
    def timer(self, operation: str, component: str = "PERF", **metadata):
        """
        Context manager for timing operations.

        Example:
            with perf_logger.timer("database_query", component="DB", query_type="SELECT"):
                result = execute_query()
        """
        timer_id = f"{operation}_{threading.get_ident()}_{time.time()}"
        start_time = time.perf_counter()
        start_memory = None
        start_cpu = None

        # Collect initial metrics if enabled
        if self._memory_tracking_enabled:
            try:
                process = psutil.Process()
                start_memory = process.memory_info().rss / (1024 * 1024)  # MB
            except:
                pass

        if self._cpu_tracking_enabled:
            try:
                start_cpu = psutil.cpu_percent()
            except:
                pass

        try:
            yield timer_id
        finally:
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000

            # Collect final metrics
            end_memory = None
            end_cpu = None

            if self._memory_tracking_enabled and start_memory is not None:
                try:
                    process = psutil.Process()
                    end_memory = process.memory_info().rss / (1024 * 1024)  # MB
                except:
                    pass

            if self._cpu_tracking_enabled:
                try:
                    end_cpu = psutil.cpu_percent()
                except:
                    pass

            # Create performance metric
            context_extras = get_context_extras()

            metric = PerformanceMetric(
                operation=operation,
                duration_ms=duration_ms,
                user_id=context_extras.get("user", "system"),
                session_id=context_extras.get("session", "none"),
                component=component,
                timestamp=datetime.utcnow().isoformat(),
                metadata=metadata,
                memory_usage_mb=end_memory,
                cpu_percent=end_cpu,
                thread_id=threading.get_ident(),
                process_id=psutil.Process().pid,
            )

            # Store in history
            with self._lock:
                self._operation_history[operation].append(metric)

            # Log structured data
            if self.logger:
                from loguru import logger

                # Map PerformanceMetric fields to expected format fields
                metric_dict = asdict(metric)
                # Convert user_id to user for format compatibility
                metric_dict["user"] = metric_dict.pop("user_id", "system")
                metric_dict["session"] = metric_dict.pop("session_id", "none")
                # Ensure request_id field exists for format compatibility
                if "request_id" not in metric_dict:
                    metric_dict["request_id"] = "perf_monitor"

                logger.bind(log_type="performance", **metric_dict).info(
                    json.dumps(asdict(metric))
                )

                # Also log human-readable version
                self.logger.info(
                    f"{operation} completed in {duration_ms:.2f}ms",
                    component=component,
                    duration_ms=duration_ms,
                    **metadata,
                )

            # Periodic garbage collection
            self._maybe_run_gc()

    def log_metric(
        self, name: str, value: float, unit: str, component: str = "METRICS", **metadata
    ):
        """
        Log a custom metric.

        Example:
            perf_logger.log_metric("cache_hit_rate", 0.85, "ratio", cache_type="redis")
        """
        context_extras = get_context_extras()

        metric_data = {
            "metric_name": name,
            "value": value,
            "unit": unit,
            "user_id": context_extras.get("user", "system"),
            "session_id": context_extras.get("session", "none"),
            "timestamp": datetime.utcnow().isoformat(),
            "metadata": metadata,
        }

        # Log structured data
        if self.logger:
            from loguru import logger

            logger.bind(
                log_type="performance", metric_type="custom", **metric_data
            ).info(json.dumps(metric_data))

            self.logger.info(
                f"Metric {name}: {value} {unit}", component=component, **metric_data
            )

    def log_counter(
        self, name: str, increment: int = 1, component: str = "METRICS", **metadata
    ):
        """Log a counter metric."""
        self.log_metric(name, increment, "count", component, **metadata)

    def log_gauge(
        self, name: str, value: float, component: str = "METRICS", **metadata
    ):
        """Log a gauge metric."""
        self.log_metric(name, value, "value", component, **metadata)

    def log_histogram(
        self, name: str, value: float, component: str = "METRICS", **metadata
    ):
        """Log a histogram metric."""
        self.log_metric(name, value, "histogram", component, **metadata)

    def get_operation_stats(
        self, operation: str, hours: int = 24
    ) -> Optional[OperationStats]:
        """Get statistics for a specific operation."""
        with self._lock:
            if operation not in self._operation_history:
                return None

            # Filter by time window
            cutoff_time = datetime.utcnow() - timedelta(hours=hours)
            recent_metrics = [
                metric
                for metric in self._operation_history[operation]
                if datetime.fromisoformat(metric.timestamp) > cutoff_time
            ]

            if not recent_metrics:
                return None

            # Calculate statistics
            durations = [metric.duration_ms for metric in recent_metrics]
            error_count = sum(
                1 for metric in recent_metrics if metric.metadata.get("error", False)
            )

            return OperationStats(
                operation_name=operation,
                total_calls=len(recent_metrics),
                total_duration_ms=sum(durations),
                avg_duration_ms=statistics.mean(durations),
                min_duration_ms=min(durations),
                max_duration_ms=max(durations),
                p50_duration_ms=statistics.median(durations),
                p95_duration_ms=self._percentile(durations, 0.95),
                p99_duration_ms=self._percentile(durations, 0.99),
                error_count=error_count,
                last_called=max(metric.timestamp for metric in recent_metrics),
            )

    def get_all_operation_stats(self, hours: int = 24) -> Dict[str, OperationStats]:
        """Get statistics for all operations."""
        stats = {}
        with self._lock:
            for operation in self._operation_history.keys():
                operation_stats = self.get_operation_stats(operation, hours)
                if operation_stats:
                    stats[operation] = operation_stats
        return stats

    def get_system_metrics_summary(self, hours: int = 1) -> Dict[str, Any]:
        """Get summary of system metrics."""
        cutoff_time = datetime.utcnow() - timedelta(hours=hours)

        with self._lock:
            recent_metrics = [
                metric
                for metric in self._system_metrics_history
                if datetime.fromisoformat(metric.timestamp) > cutoff_time
            ]

        if not recent_metrics:
            return {}

        cpu_values = [m.cpu_percent for m in recent_metrics]
        memory_values = [m.memory_percent for m in recent_metrics]

        return {
            "time_window_hours": hours,
            "sample_count": len(recent_metrics),
            "cpu": {
                "avg_percent": statistics.mean(cpu_values),
                "max_percent": max(cpu_values),
                "min_percent": min(cpu_values),
            },
            "memory": {
                "avg_percent": statistics.mean(memory_values),
                "max_percent": max(memory_values),
                "min_percent": min(memory_values),
                "current_used_mb": recent_metrics[-1].memory_used_mb,
                "current_available_mb": recent_metrics[-1].memory_available_mb,
            },
            "disk": {"current_usage_percent": recent_metrics[-1].disk_usage_percent},
            "threads": {"current_count": recent_metrics[-1].active_threads},
        }

    def generate_performance_report(self, hours: int = 24) -> Dict[str, Any]:
        """Generate comprehensive performance report."""
        operation_stats = self.get_all_operation_stats(hours)
        system_summary = self.get_system_metrics_summary(hours)

        # Calculate top operations by various metrics
        if operation_stats:
            top_by_calls = sorted(
                operation_stats.items(), key=lambda x: x[1].total_calls, reverse=True
            )[:10]
            top_by_duration = sorted(
                operation_stats.items(),
                key=lambda x: x[1].total_duration_ms,
                reverse=True,
            )[:10]
            slowest_avg = sorted(
                operation_stats.items(),
                key=lambda x: x[1].avg_duration_ms,
                reverse=True,
            )[:10]
        else:
            top_by_calls = top_by_duration = slowest_avg = []

        return {
            "report_timestamp": datetime.utcnow().isoformat(),
            "time_window_hours": hours,
            "summary": {
                "total_operations": len(operation_stats),
                "total_calls": sum(
                    stats.total_calls for stats in operation_stats.values()
                ),
                "total_duration_ms": sum(
                    stats.total_duration_ms for stats in operation_stats.values()
                ),
                "total_errors": sum(
                    stats.error_count for stats in operation_stats.values()
                ),
            },
            "top_operations": {
                "by_call_count": [
                    (op, stats.total_calls) for op, stats in top_by_calls
                ],
                "by_total_duration": [
                    (op, stats.total_duration_ms) for op, stats in top_by_duration
                ],
                "by_avg_duration": [
                    (op, stats.avg_duration_ms) for op, stats in slowest_avg
                ],
            },
            "operation_details": {
                op: asdict(stats) for op, stats in operation_stats.items()
            },
            "system_metrics": system_summary,
        }

    def _percentile(self, data: List[float], percentile: float) -> float:
        """Calculate percentile of a list of values."""
        if not data:
            return 0.0

        sorted_data = sorted(data)
        index = int(percentile * (len(sorted_data) - 1))
        return sorted_data[index]

    def _maybe_run_gc(self):
        """Run garbage collection if enough time has passed."""
        current_time = time.time()
        if current_time - self._last_gc_time > self._gc_interval:
            gc.collect()
            self._last_gc_time = current_time

    def enable_memory_tracking(self, enabled: bool = True):
        """Enable or disable memory tracking."""
        self._memory_tracking_enabled = enabled

    def enable_cpu_tracking(self, enabled: bool = True):
        """Enable or disable CPU tracking."""
        self._cpu_tracking_enabled = enabled

    def clear_history(self, operation: Optional[str] = None):
        """Clear performance history for specific operation or all operations."""
        with self._lock:
            if operation:
                if operation in self._operation_history:
                    self._operation_history[operation].clear()
            else:
                self._operation_history.clear()
                self._system_metrics_history.clear()

    def stop_monitoring(self):
        """Stop background system monitoring."""
        self._monitoring_enabled = False
        if self._monitoring_thread and self._monitoring_thread.is_alive():
            self._monitoring_thread.join(timeout=5)


# Decorator for automatic performance monitoring
def monitor_performance(operation_name: str = None, component: str = "PERF"):
    """
    Decorator to automatically monitor function performance.

    Example:
        @monitor_performance("database_query", "DB")
        def execute_query(sql):
            # ... query execution ...
            return result
    """

    def decorator(func):
        nonlocal operation_name
        if operation_name is None:
            operation_name = f"{func.__module__}.{func.__name__}"

        def wrapper(*args, **kwargs):
            # Get performance logger from context or create a basic one
            perf_logger = getattr(wrapper, "_perf_logger", None)
            if perf_logger is None:
                from .unified_logger import performance_logger

                perf_logger = performance_logger

            with perf_logger.timer(operation_name, component):
                return func(*args, **kwargs)

        return wrapper

    return decorator


# Context manager for performance monitoring
@contextmanager
def performance_context(operation_name: str, component: str = "PERF", **metadata):
    """
    Context manager for performance monitoring.

    Example:
        with performance_context("file_processing", "FILES", file_size=1024):
            process_file(filename)
    """
    from .unified_logger import performance_logger

    with performance_logger.timer(operation_name, component, **metadata):
        yield
