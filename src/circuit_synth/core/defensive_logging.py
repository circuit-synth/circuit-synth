# FILE: src/circuit_synth/core/defensive_logging.py
"""
Ultra-defensive logging framework for Rust integration safety.

This module provides comprehensive logging, validation, and safety mechanisms
for gradually integrating Rust optimizations while maintaining 100% Python
compatibility and graceful fallback behavior.

Philosophy: "Log everything, trust nothing, fail safely"
"""

import hashlib
import json
import logging
import os
import sys
import time
from contextlib import contextmanager
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Callable, Dict, Optional, Union

# Configure logging format for defensive operations
DEFENSIVE_LOG_FORMAT = (
    "%(asctime)s | %(levelname)-8s | DEFENSIVE-%(name)s | %(message)s"
)


@dataclass
class OperationMetrics:
    """Metrics for tracking operation performance and reliability"""

    operation_name: str
    start_time: float
    end_time: Optional[float] = None
    success: bool = False
    error_message: Optional[str] = None
    rust_used: bool = False
    python_fallback: bool = False
    input_size: Optional[int] = None
    output_size: Optional[int] = None
    checksum: Optional[str] = None


@dataclass
class ComponentMetrics:
    """Aggregated metrics for a specific component (e.g., schematic_writer)"""

    component_name: str
    total_operations: int = 0
    rust_successes: int = 0
    rust_failures: int = 0
    python_operations: int = 0
    total_rust_time: float = 0.0
    total_python_time: float = 0.0
    operations: list[OperationMetrics] = field(default_factory=list)

    @property
    def rust_failure_rate(self) -> float:
        """Calculate Rust failure rate"""
        total_rust = self.rust_successes + self.rust_failures
        return self.rust_failures / total_rust if total_rust > 0 else 0.0

    @property
    def avg_rust_time(self) -> float:
        """Average Rust operation time"""
        return (
            self.total_rust_time / self.rust_successes
            if self.rust_successes > 0
            else 0.0
        )

    @property
    def avg_python_time(self) -> float:
        """Average Python operation time"""
        return (
            self.total_python_time / self.python_operations
            if self.python_operations > 0
            else 0.0
        )

    @property
    def performance_improvement(self) -> float:
        """Performance improvement ratio (Python time / Rust time)"""
        if self.avg_rust_time > 0 and self.avg_python_time > 0:
            return self.avg_python_time / self.avg_rust_time
        return 1.0


class DefensiveLogger:
    """
    Ultra-defensive logger for Rust integration safety.

    Features:
    - Comprehensive operation logging with timing
    - Automatic checksum validation
    - Performance metrics collection
    - Automatic Rust disable on high failure rates
    - Safe fallback mechanisms
    """

    def __init__(self, component_name: str):
        self.component_name = component_name
        self.logger = logging.getLogger(f"circuit_synth.defensive.{component_name}")

        # Configure formatter if not already set
        if not self.logger.handlers:
            handler = logging.StreamHandler(sys.stdout)
            formatter = logging.Formatter(DEFENSIVE_LOG_FORMAT)
            handler.setFormatter(formatter)
            self.logger.addHandler(handler)
            self.logger.setLevel(logging.INFO)

        # Metrics tracking
        self.metrics = ComponentMetrics(component_name=component_name)

        # Safety thresholds
        self.max_failure_rate = float(
            os.environ.get("CIRCUIT_SYNTH_MAX_RUST_FAILURE_RATE", "0.1")
        )  # 10%
        self.min_operations_for_disable = int(
            os.environ.get("CIRCUIT_SYNTH_MIN_OPS_FOR_DISABLE", "10")
        )

        # Rust availability check
        self.rust_globally_disabled = (
            os.environ.get("CIRCUIT_SYNTH_DISABLE_RUST", "false").lower() == "true"
        )
        self.rust_auto_disabled = False

        self.logger.info(f"🛡️  DEFENSIVE LOGGER INITIALIZED [{component_name}]")
        self.logger.info(f"   📊 Max failure rate: {self.max_failure_rate:.1%}")
        self.logger.info(
            f"   📊 Min operations for auto-disable: {self.min_operations_for_disable}"
        )
        self.logger.info(f"   🦀 Rust globally disabled: {self.rust_globally_disabled}")

    def is_rust_available(self) -> bool:
        """Check if Rust should be used for operations"""
        if self.rust_globally_disabled:
            return False

        if self.rust_auto_disabled:
            return False

        # Check if we should auto-disable due to high failure rate
        if (
            self.metrics.total_operations >= self.min_operations_for_disable
            and self.metrics.rust_failure_rate > self.max_failure_rate
        ):

            self.rust_auto_disabled = True
            self.logger.warning(f"🚨 AUTO-DISABLING RUST [{self.component_name}]")
            self.logger.warning(
                f"   📈 Failure rate: {self.metrics.rust_failure_rate:.1%} > {self.max_failure_rate:.1%}"
            )
            self.logger.warning(f"   📊 Operations: {self.metrics.total_operations}")
            self.logger.warning(f"   🔄 All future operations will use Python fallback")
            return False

        return True

    def log_operation_start(self, operation: str, **kwargs) -> OperationMetrics:
        """Log the start of an operation and return metrics tracker"""
        start_time = time.perf_counter()

        self.logger.info(f"🚀 STARTING [{self.component_name}] {operation}")
        for key, value in kwargs.items():
            if isinstance(value, (str, int, float, bool)):
                self.logger.info(f"   📊 {key}: {value}")
            else:
                self.logger.info(f"   📊 {key}: {type(value).__name__}")

        metrics = OperationMetrics(
            operation_name=operation,
            start_time=start_time,
            input_size=kwargs.get("input_size"),
        )

        return metrics

    def log_python_success(
        self, metrics: OperationMetrics, result: Any, **kwargs
    ) -> None:
        """Log successful Python operation"""
        metrics.end_time = time.perf_counter()
        metrics.success = True
        metrics.rust_used = False

        duration = metrics.end_time - metrics.start_time

        # Calculate result metadata
        result_size = self._calculate_size(result)
        checksum = self._calculate_checksum(result)

        metrics.output_size = result_size
        metrics.checksum = checksum

        self.logger.info(
            f"✅ PYTHON SUCCESS [{self.component_name}] {metrics.operation_name}"
        )
        self.logger.info(f"   ⏱️  Duration: {duration:.4f}s")
        self.logger.info(f"   📏 Output size: {result_size} bytes")
        self.logger.info(f"   🔐 Checksum: {checksum[:16]}...")
        for key, value in kwargs.items():
            self.logger.info(f"   📈 {key}: {value}")

        # Update metrics
        self.metrics.python_operations += 1
        self.metrics.total_python_time += duration
        self.metrics.total_operations += 1
        self.metrics.operations.append(metrics)

    def log_rust_success(
        self,
        metrics: OperationMetrics,
        result: Any,
        python_result: Any = None,
        **kwargs,
    ) -> None:
        """Log successful Rust operation with optional validation against Python"""
        metrics.end_time = time.perf_counter()
        metrics.success = True
        metrics.rust_used = True

        duration = metrics.end_time - metrics.start_time

        # Calculate result metadata
        result_size = self._calculate_size(result)
        checksum = self._calculate_checksum(result)

        metrics.output_size = result_size
        metrics.checksum = checksum

        # Validate against Python if provided
        validation_status = "NO_VALIDATION"
        if python_result is not None:
            python_checksum = self._calculate_checksum(python_result)
            if checksum == python_checksum:
                validation_status = "VALIDATED_IDENTICAL"
                self.logger.info(
                    f"🔍 VALIDATION PASSED: Rust output identical to Python"
                )
            else:
                validation_status = "VALIDATION_FAILED"
                self.logger.error(f"❌ VALIDATION FAILED: Output mismatch!")
                self.logger.error(f"   🐍 Python checksum: {python_checksum[:16]}...")
                self.logger.error(f"   🦀 Rust checksum:   {checksum[:16]}...")
                # This should trigger a fallback in the calling code

        self.logger.info(
            f"✅ RUST SUCCESS [{self.component_name}] {metrics.operation_name}"
        )
        self.logger.info(f"   ⏱️  Duration: {duration:.4f}s")
        self.logger.info(f"   📏 Output size: {result_size} bytes")
        self.logger.info(f"   🔐 Checksum: {checksum[:16]}...")
        self.logger.info(f"   🔍 Validation: {validation_status}")
        for key, value in kwargs.items():
            self.logger.info(f"   📈 {key}: {value}")

        # Update metrics
        self.metrics.rust_successes += 1
        self.metrics.total_rust_time += duration
        self.metrics.total_operations += 1
        self.metrics.operations.append(metrics)

    def log_rust_fallback(
        self, metrics: OperationMetrics, error: Exception, **kwargs
    ) -> None:
        """Log Rust operation failure and fallback to Python"""
        metrics.end_time = time.perf_counter()
        metrics.success = False
        metrics.error_message = str(error)
        metrics.python_fallback = True

        duration = metrics.end_time - metrics.start_time

        self.logger.warning(
            f"⚠️  RUST FALLBACK [{self.component_name}] {metrics.operation_name}"
        )
        self.logger.warning(f"   ⏱️  Failed after: {duration:.4f}s")
        self.logger.warning(f"   🔴 Error type: {type(error).__name__}")
        self.logger.warning(f"   🔴 Error message: {error}")
        for key, value in kwargs.items():
            self.logger.warning(f"   📊 {key}: {value}")
        self.logger.warning(f"   🔄 Falling back to Python implementation")

        # Update metrics
        self.metrics.rust_failures += 1
        self.metrics.total_operations += 1
        self.metrics.operations.append(metrics)

    def log_file_validation(
        self, filepath: Union[str, Path], expected_checksum: Optional[str] = None
    ) -> bool:
        """Validate file existence and optionally checksum"""
        filepath = Path(filepath)

        if not filepath.exists():
            self.logger.error(f"❌ FILE VALIDATION FAILED: {filepath}")
            self.logger.error(f"   📁 File does not exist")
            return False

        try:
            with open(filepath, "rb") as f:
                content = f.read()
                actual_checksum = hashlib.md5(content).hexdigest()
                file_size = len(content)

            self.logger.info(f"🔍 FILE VALIDATION [{filepath.name}]")
            self.logger.info(f"   📏 Size: {file_size} bytes")
            self.logger.info(f"   🔐 Checksum: {actual_checksum[:16]}...")

            if expected_checksum:
                if actual_checksum == expected_checksum:
                    self.logger.info(f"   ✅ Checksum matches expected")
                    return True
                else:
                    self.logger.error(f"   ❌ Checksum mismatch!")
                    self.logger.error(f"      Expected: {expected_checksum[:16]}...")
                    self.logger.error(f"      Actual:   {actual_checksum[:16]}...")
                    return False

            return True

        except Exception as e:
            self.logger.error(f"❌ FILE VALIDATION ERROR: {filepath}")
            self.logger.error(f"   🔴 {type(e).__name__}: {e}")
            return False

    def get_performance_summary(self) -> Dict[str, Any]:
        """Get comprehensive performance summary"""
        summary = {
            "component": self.component_name,
            "total_operations": self.metrics.total_operations,
            "rust_operations": self.metrics.rust_successes + self.metrics.rust_failures,
            "python_operations": self.metrics.python_operations,
            "rust_success_rate": (
                1.0 - self.metrics.rust_failure_rate
                if self.metrics.rust_successes + self.metrics.rust_failures > 0
                else 0.0
            ),
            "performance_improvement": self.metrics.performance_improvement,
            "avg_rust_time": self.metrics.avg_rust_time,
            "avg_python_time": self.metrics.avg_python_time,
            "rust_available": self.is_rust_available(),
            "rust_auto_disabled": self.rust_auto_disabled,
        }

        return summary

    def log_performance_summary(self) -> None:
        """Log comprehensive performance summary"""
        try:
            summary = self.get_performance_summary()

            self.logger.info(f"📊 PERFORMANCE SUMMARY [{self.component_name}]")
            self.logger.info(f"   🔢 Total operations: {summary['total_operations']}")
            self.logger.info(f"   🦀 Rust operations: {summary['rust_operations']}")
            self.logger.info(f"   🐍 Python operations: {summary['python_operations']}")

            if summary["rust_operations"] > 0:
                self.logger.info(
                    f"   📈 Rust success rate: {summary['rust_success_rate']:.1%}"
                )
                self.logger.info(
                    f"   ⚡ Performance improvement: {summary['performance_improvement']:.1f}x"
                )
                self.logger.info(
                    f"   ⏱️  Avg Rust time: {summary['avg_rust_time']:.4f}s"
                )

            if summary["python_operations"] > 0:
                self.logger.info(
                    f"   ⏱️  Avg Python time: {summary['avg_python_time']:.4f}s"
                )

            self.logger.info(f"   🦀 Rust available: {summary['rust_available']}")
            if summary["rust_auto_disabled"]:
                self.logger.warning(f"   🚨 Rust auto-disabled due to failures")
        except (ValueError, OSError):
            # Ignore logging errors during shutdown (closed file descriptors)
            pass

    @contextmanager
    def defensive_operation(self, operation_name: str, **kwargs):
        """Context manager for defensive operation logging"""
        metrics = self.log_operation_start(operation_name, **kwargs)
        try:
            yield metrics
        except Exception as e:
            self.log_rust_fallback(metrics, e)
            raise

    def _calculate_size(self, obj: Any) -> int:
        """Calculate approximate size of an object"""
        if isinstance(obj, str):
            return len(obj.encode("utf-8"))
        elif isinstance(obj, bytes):
            return len(obj)
        elif isinstance(obj, (list, dict)):
            return len(json.dumps(obj, default=str).encode("utf-8"))
        else:
            return len(str(obj).encode("utf-8"))

    def _calculate_checksum(self, obj: Any) -> str:
        """Calculate MD5 checksum of an object"""
        if isinstance(obj, str):
            content = obj.encode("utf-8")
        elif isinstance(obj, bytes):
            content = obj
        else:
            content = json.dumps(obj, default=str, sort_keys=True).encode("utf-8")

        return hashlib.md5(content).hexdigest()


# Global registry of defensive loggers
_loggers: Dict[str, DefensiveLogger] = {}


def get_defensive_logger(component_name: str) -> DefensiveLogger:
    """Get or create a defensive logger for a component"""
    if component_name not in _loggers:
        _loggers[component_name] = DefensiveLogger(component_name)
    return _loggers[component_name]


def log_all_performance_summaries() -> None:
    """Log performance summaries for all components"""
    try:
        print("\n" + "=" * 80)
        print("🛡️  DEFENSIVE LOGGING - FINAL PERFORMANCE SUMMARY")
        print("=" * 80)

        for logger in _loggers.values():
            logger.log_performance_summary()
            print("-" * 80)
    except (ValueError, OSError):
        # Ignore logging errors during shutdown (closed file descriptors)
        pass


# Install exit handler to log final summaries
import atexit
import os

# Only register the exit handler if not in test mode
if not any("pytest" in arg for arg in os.sys.argv):
    atexit.register(log_all_performance_summaries)
