"""
Defensive Logging Framework

Ultra-defensive logging framework for safety and performance monitoring.

This module provides comprehensive logging for all circuit-synth operations
for maintaining 100% Python fallback capabilities.

Philosophy: "Log everything, trust nothing, fail safely"
"""

import hashlib
import logging
import os
import time
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, Optional


class OperationStatus(Enum):
    """Status of an operation"""

    SUCCESS = "success"
    FAILURE = "failure"
    FALLBACK = "fallback"
    VALIDATION_FAILED = "validation_failed"


@dataclass
class OperationMetrics:
    """Metrics for a single operation"""

    operation_name: str
    duration: float
    status: OperationStatus
    component_count: Optional[int] = None
    net_count: Optional[int] = None
    validation_passed: bool = False
    error_message: Optional[str] = None


@dataclass
class ComponentMetrics:
    """Aggregate metrics for a component"""

    total_operations: int = 0
    successes: int = 0
    failures: int = 0
    total_python_time: float = 0.0
    total_components_processed: int = 0
    total_nets_processed: int = 0

    @property
    def failure_rate(self) -> float:
        """Calculate failure rate"""
        return self.failures / self.total_operations if self.total_operations > 0 else 0.0

    @property
    def avg_python_time(self) -> float:
        """Average Python operation time"""
        return (
            self.total_python_time / self.successes
            if self.successes > 0
            else 0.0
        )


class DefensiveLogger:
    """
    Ultra-defensive logger for safety and performance monitoring.

    Features:
    - Operation metrics tracking
    - Failure rate monitoring
    - Performance benchmarking
    - Automatic safety checks
    - Detailed error reporting
    """

    def __init__(self, component_name: str):
        """
        Initialize defensive logger for a component.

        Args:
            component_name: Name of the component being logged
        """
        self.component_name = component_name
        self.logger = logging.getLogger(f"defensive.{component_name}")
        self.metrics = ComponentMetrics()

        # Configuration from environment
        self.enable_validation = (
            os.environ.get("CIRCUIT_SYNTH_ENABLE_VALIDATION", "false").lower()
            == "true"
        )
        self.max_failure_rate = float(
            os.environ.get("CIRCUIT_SYNTH_MAX_FAILURE_RATE", "0.1")
        )
        self.verbose = (
            os.environ.get("CIRCUIT_SYNTH_DEFENSIVE_VERBOSE", "false").lower()
            == "true"
        )

        # Initial log
        self.logger.info(f"🛡️ DEFENSIVE LOGGER INITIALIZED [{component_name}]")
        self.logger.info(f"   🔍 Validation enabled: {self.enable_validation}")

    def log_operation_start(
        self,
        operation_name: str,
        component_count: Optional[int] = None,
        net_count: Optional[int] = None,
    ) -> OperationMetrics:
        """
        Log the start of an operation.

        Args:
            operation_name: Name of the operation
            component_count: Number of components being processed
            net_count: Number of nets being processed

        Returns:
            OperationMetrics object to be used for tracking
        """
        metrics = OperationMetrics(
            operation_name=operation_name,
            duration=0.0,
            status=OperationStatus.FAILURE,  # Assume failure until proven otherwise
            component_count=component_count,
            net_count=net_count,
        )

        if self.verbose:
            self.logger.debug(
                f"🚀 OPERATION START [{self.component_name}] {operation_name}"
            )
            if component_count:
                self.logger.debug(f"   📊 Components: {component_count}")
            if net_count:
                self.logger.debug(f"   🔗 Nets: {net_count}")

        return metrics

    def log_operation_success(
        self,
        metrics: OperationMetrics,
        duration: float,
        python_output: Optional[Any] = None,
    ):
        """Log successful Python operation"""
        metrics.status = OperationStatus.SUCCESS
        metrics.duration = duration

        # Optional validation
        if self.enable_validation and python_output is not None:
            try:
                checksum = hashlib.md5(str(python_output).encode()).hexdigest()
                metrics.validation_passed = True
                if self.verbose:
                    self.logger.debug(
                        f"🔍 VALIDATION: Python output checksum: {checksum[:16]}..."
                    )
            except Exception as e:
                self.logger.warning(f"⚠️ Validation failed: {e}")

        self.logger.info(
            f"✅ SUCCESS [{self.component_name}] {metrics.operation_name}"
        )
        self.logger.info(f"   ⏱️ Duration: {duration:.4f}s")

        # Update aggregate metrics
        self.metrics.total_operations += 1
        self.metrics.successes += 1
        self.metrics.total_python_time += duration
        if metrics.component_count:
            self.metrics.total_components_processed += metrics.component_count
        if metrics.net_count:
            self.metrics.total_nets_processed += metrics.net_count

    def log_operation_failure(
        self, metrics: OperationMetrics, error: Exception, duration: float
    ):
        """Log Python operation failure"""
        metrics.status = OperationStatus.FAILURE
        metrics.duration = duration
        metrics.error_message = str(error)

        self.logger.error(
            f"❌ FAILURE [{self.component_name}] {metrics.operation_name}"
        )
        self.logger.error(f"   🐛 Error: {error}")
        self.logger.error(f"   ⏱️ Failed after: {duration:.4f}s")

        # Update aggregate metrics
        self.metrics.total_operations += 1
        self.metrics.failures += 1

    def validate_output(self, output1: Any, output2: Any) -> bool:
        """
        Validate that two outputs are equivalent.

        Args:
            output1: First output to compare
            output2: Second output to compare

        Returns:
            True if outputs match, False otherwise
        """
        try:
            # Simple string comparison for now
            return str(output1) == str(output2)
        except:
            return False

    def get_summary(self) -> Dict[str, Any]:
        """
        Get summary statistics for this component.

        Returns:
            Dictionary with aggregate metrics
        """
        summary = {
            "component": self.component_name,
            "total_operations": self.metrics.total_operations,
            "successes": self.metrics.successes,
            "failures": self.metrics.failures,
            "success_rate": (
                1.0 - self.metrics.failure_rate
                if self.metrics.total_operations > 0
                else 1.0
            ),
            "avg_python_time": self.metrics.avg_python_time,
            "total_components": self.metrics.total_components_processed,
            "total_nets": self.metrics.total_nets_processed,
        }

        if self.verbose:
            self.logger.info(f"📊 SUMMARY [{self.component_name}]")
            self.logger.info(f"   📈 Operations: {summary['total_operations']}")
            self.logger.info(f"   ✅ Successes: {summary['successes']}")
            self.logger.info(f"   ❌ Failures: {summary['failures']}")

            if summary["total_operations"] > 0:
                self.logger.info(
                    f"   📈 Success rate: {summary['success_rate']:.1%}"
                )
                self.logger.info(
                    f"   ⏱️  Avg Python time: {summary['avg_python_time']:.4f}s"
                )

            self.logger.info(f"   📊 Components: {summary['total_components']}")
            self.logger.info(f"   🔗 Nets: {summary['total_nets']}")

        return summary

    def with_fallback(self, python_fn, *args, **kwargs):
        """
        Execute operation with comprehensive logging.

        Args:
            python_fn: Python function to execute
            *args: Arguments for the function
            **kwargs: Keyword arguments for the function

        Returns:
            Result from the Python function
        """
        operation_name = python_fn.__name__
        metrics = self.log_operation_start(operation_name)

        start_time = time.perf_counter()
        try:
            result = python_fn(*args, **kwargs)
            duration = time.perf_counter() - start_time
            self.log_operation_success(metrics, duration, result)
            return result
        except Exception as e:
            duration = time.perf_counter() - start_time
            self.log_operation_failure(metrics, e, duration)
            raise


# Global registry of defensive loggers
_loggers: Dict[str, DefensiveLogger] = {}


def get_defensive_logger(component_name: str) -> DefensiveLogger:
    """
    Get or create a defensive logger for a component.

    Args:
        component_name: Name of the component

    Returns:
        DefensiveLogger instance
    """
    if component_name not in _loggers:
        _loggers[component_name] = DefensiveLogger(component_name)
    return _loggers[component_name]


def get_global_summary() -> Dict[str, Any]:
    """
    Get summary statistics for all components.

    Returns:
        Dictionary with global metrics
    """
    summaries = {}
    for name, logger in _loggers.items():
        summaries[name] = logger.get_summary()

    total_ops = sum(s["total_operations"] for s in summaries.values())
    total_successes = sum(s["successes"] for s in summaries.values())
    total_failures = sum(s["failures"] for s in summaries.values())

    return {
        "components": list(summaries.keys()),
        "total_operations": total_ops,
        "total_successes": total_successes,
        "total_failures": total_failures,
        "global_success_rate": (
            total_successes / total_ops if total_ops > 0 else 1.0
        ),
        "component_summaries": summaries,
    }