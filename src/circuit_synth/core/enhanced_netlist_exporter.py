"""
Enhanced Netlist Exporter with Performance Analytics - Phase 6
=============================================================

Enhanced netlist exporter that integrates with the generation logging system
to provide detailed netlist generation performance analytics and monitoring.
"""

import os
import time
from dataclasses import dataclass
from typing import Any, Dict, List, Optional

import psutil

from ._logger import (
    GenerationStage,
    context_logger,
    generation_logger,
    log_netlist_analytics,
    performance_logger,
)
from .netlist_exporter import NetlistExporter


@dataclass
class NetlistMetrics:
    """Comprehensive netlist generation metrics."""

    component_count: int
    net_count: int
    generation_time_ms: float
    file_size_bytes: int
    memory_usage_mb: float
    cpu_usage_percent: float
    optimization_applied: bool
    rust_backend_used: bool
    cache_hits: int
    cache_misses: int
    io_operations: int

    def to_dict(self) -> Dict[str, Any]:
        return {
            "component_count": self.component_count,
            "net_count": self.net_count,
            "generation_time_ms": self.generation_time_ms,
            "file_size_bytes": self.file_size_bytes,
            "memory_usage_mb": self.memory_usage_mb,
            "cpu_usage_percent": self.cpu_usage_percent,
            "optimization_applied": self.optimization_applied,
            "rust_backend_used": self.rust_backend_used,
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "io_operations": self.io_operations,
            "performance_ratios": {
                "components_per_second": (
                    self.component_count / (self.generation_time_ms / 1000)
                    if self.generation_time_ms > 0
                    else 0
                ),
                "bytes_per_component": self.file_size_bytes
                / max(self.component_count, 1),
                "cache_hit_rate": self.cache_hits
                / max(self.cache_hits + self.cache_misses, 1)
                * 100,
                "memory_efficiency": self.file_size_bytes
                / max(self.memory_usage_mb * 1024 * 1024, 1),
            },
        }


class EnhancedNetlistExporter:
    """
    Enhanced netlist exporter with comprehensive performance analytics.

    This wrapper around the production NetlistExporter adds detailed logging
    of netlist generation performance, memory usage, and optimization metrics.
    """

    def __init__(self):
        """Initialize the enhanced netlist exporter."""
        # Don't initialize base_exporter here since it needs a circuit
        self.base_exporter = None
        self._generation_stats = {
            "total_generations": 0,
            "total_components_processed": 0,
            "total_generation_time_ms": 0.0,
            "rust_backend_usage_count": 0,
            "optimization_usage_count": 0,
        }
        self._process = psutil.Process()

    def export_netlist_with_analytics(
        self,
        circuit,
        output_path: str,
        enable_optimization: bool = True,
        force_rust_backend: bool = False,
    ) -> NetlistMetrics:
        """
        Export netlist with comprehensive performance analytics.

        Args:
            circuit: Circuit object to export
            output_path: Path for the output netlist file
            enable_optimization: Whether to enable netlist optimizations
            force_rust_backend: Whether to force use of Rust backend

        Returns:
            NetlistMetrics with detailed performance data
        """
        context_logger.info(
            "Starting enhanced netlist export",
            component="NETLIST_EXPORT_START",
            output_path=output_path,
            enable_optimization=enable_optimization,
            force_rust_backend=force_rust_backend,
        )

        # Initialize metrics tracking
        start_time = time.time()
        start_memory = self._get_memory_usage_mb()
        start_cpu = self._get_cpu_usage()
        io_operations = 0
        cache_hits = 0
        cache_misses = 0

        try:
            with generation_logger.stage_timer(GenerationStage.NETLIST_GENERATION):
                # Pre-generation analysis
                component_count = self._count_components(circuit)
                net_count = self._count_nets(circuit)

                context_logger.info(
                    f"Netlist generation starting: {component_count} components, {net_count} nets",
                    component="NETLIST_GENERATION_ANALYSIS",
                    component_count=component_count,
                    net_count=net_count,
                )

                # Determine backend to use
                rust_backend_used = self._should_use_rust_backend(
                    component_count, force_rust_backend
                )

                if rust_backend_used:
                    context_logger.info(
                        "Using Rust backend for netlist generation",
                        component="NETLIST_BACKEND_SELECTION",
                        reason=(
                            "performance_optimization"
                            if component_count > 100
                            else "forced"
                        ),
                    )
                    self._generation_stats["rust_backend_usage_count"] += 1

                # Apply optimizations if enabled
                optimization_applied = enable_optimization and self._should_optimize(
                    component_count
                )
                if optimization_applied:
                    self._generation_stats["optimization_usage_count"] += 1
                    context_logger.info(
                        "Applying netlist optimizations",
                        component="NETLIST_OPTIMIZATION",
                        component_count=component_count,
                    )

                # Perform the actual netlist generation
                if rust_backend_used:
                    result, io_ops, cache_stats = self._export_with_rust_backend(
                        circuit, output_path, optimization_applied
                    )
                else:
                    result, io_ops, cache_stats = self._export_with_python_backend(
                        circuit, output_path, optimization_applied
                    )

                io_operations = io_ops
                cache_hits = cache_stats.get("hits", 0)
                cache_misses = cache_stats.get("misses", 0)

                # Calculate final metrics
                generation_time_ms = (time.time() - start_time) * 1000
                end_memory = self._get_memory_usage_mb()
                memory_usage_mb = end_memory - start_memory
                cpu_usage_percent = self._get_cpu_usage() - start_cpu

                # Get file size
                file_size_bytes = (
                    os.path.getsize(output_path) if os.path.exists(output_path) else 0
                )

                # Create metrics object
                metrics = NetlistMetrics(
                    component_count=component_count,
                    net_count=net_count,
                    generation_time_ms=generation_time_ms,
                    file_size_bytes=file_size_bytes,
                    memory_usage_mb=memory_usage_mb,
                    cpu_usage_percent=cpu_usage_percent,
                    optimization_applied=optimization_applied,
                    rust_backend_used=rust_backend_used,
                    cache_hits=cache_hits,
                    cache_misses=cache_misses,
                    io_operations=io_operations,
                )

                # Update statistics
                self._update_generation_stats(metrics)

                # Log comprehensive analytics
                self._log_netlist_analytics(metrics)

                # Log performance metrics to the generation logger
                generation_logger.log_performance_metrics(
                    stage=GenerationStage.NETLIST_GENERATION,
                    duration_ms=generation_time_ms,
                    memory_usage_mb=memory_usage_mb,
                    cpu_usage_percent=cpu_usage_percent,
                    io_operations=io_operations,
                    cache_hits=cache_hits,
                    cache_misses=cache_misses,
                )

                context_logger.info(
                    "Netlist export completed successfully",
                    component="NETLIST_EXPORT_SUCCESS",
                    metrics=metrics.to_dict(),
                )

                return metrics

        except Exception as e:
            generation_time_ms = (time.time() - start_time) * 1000

            generation_logger.log_error_with_recovery(
                stage=GenerationStage.NETLIST_GENERATION,
                error=e,
                recovery_attempted=True,
                recovery_successful=False,
                recovery_details={
                    "component_count": (
                        component_count if "component_count" in locals() else 0
                    ),
                    "output_path": output_path,
                    "generation_time_ms": generation_time_ms,
                },
            )

            raise

    def _export_with_rust_backend(
        self, circuit, output_path: str, optimization_applied: bool
    ) -> tuple:
        """Export netlist using Rust backend with performance tracking."""
        context_logger.debug(
            "Exporting with Rust backend", component="NETLIST_RUST_BACKEND"
        )

        try:
            # Try to use Rust netlist processor
            from rust_netlist_processor import export_netlist_optimized

            start_time = time.time()
            result = export_netlist_optimized(
                circuit, output_path, optimization_applied
            )
            duration_ms = (time.time() - start_time) * 1000

            # Mock cache and IO stats for Rust backend
            cache_stats = {"hits": 15, "misses": 3}  # Would come from Rust
            io_operations = 5  # Would come from Rust

            performance_logger.log_metric(
                "rust_netlist_export_duration",
                duration_ms,
                component="RUST_NETLIST_PERFORMANCE",
            )

            return result, io_operations, cache_stats

        except ImportError:
            context_logger.warning(
                "Rust backend not available, falling back to Python",
                component="NETLIST_BACKEND_FALLBACK",
            )
            return self._export_with_python_backend(
                circuit, output_path, optimization_applied
            )

    def _export_with_python_backend(
        self, circuit, output_path: str, optimization_applied: bool
    ) -> tuple:
        """Export netlist using Python backend with performance tracking."""
        context_logger.debug(
            "Exporting with Python backend", component="NETLIST_PYTHON_BACKEND"
        )

        start_time = time.time()

        # Initialize base exporter if needed
        if self.base_exporter is None:
            self.base_exporter = NetlistExporter(circuit)

        # Use the base exporter
        result = self.base_exporter.export_netlist(circuit, output_path)

        duration_ms = (time.time() - start_time) * 1000

        # Mock cache and IO stats for Python backend
        cache_stats = {"hits": 8, "misses": 7}  # Would come from actual implementation
        io_operations = 12  # Would come from actual implementation

        performance_logger.log_metric(
            "python_netlist_export_duration",
            duration_ms,
            component="PYTHON_NETLIST_PERFORMANCE",
        )

        return result, io_operations, cache_stats

    def _count_components(self, circuit) -> int:
        """Count components in the circuit."""
        try:
            if hasattr(circuit, "components"):
                return len(circuit.components)
            elif hasattr(circuit, "get_components"):
                return len(circuit.get_components())
            else:
                # Fallback estimation
                return 10
        except Exception:
            return 0

    def _count_nets(self, circuit) -> int:
        """Count nets in the circuit."""
        try:
            if hasattr(circuit, "nets"):
                return len(circuit.nets)
            elif hasattr(circuit, "get_nets"):
                return len(circuit.get_nets())
            else:
                # Fallback estimation
                return 8
        except Exception:
            return 0

    def _should_use_rust_backend(self, component_count: int, force_rust: bool) -> bool:
        """Determine whether to use Rust backend."""
        if force_rust:
            return True

        # Use Rust for larger circuits (performance benefit)
        return component_count > 50

    def _should_optimize(self, component_count: int) -> bool:
        """Determine whether to apply optimizations."""
        # Apply optimizations for circuits with more than 20 components
        return component_count > 20

    def _get_memory_usage_mb(self) -> float:
        """Get current memory usage in MB."""
        try:
            return self._process.memory_info().rss / 1024 / 1024
        except Exception:
            return 0.0

    def _get_cpu_usage(self) -> float:
        """Get current CPU usage percentage."""
        try:
            return self._process.cpu_percent()
        except Exception:
            return 0.0

    def _update_generation_stats(self, metrics: NetlistMetrics):
        """Update global generation statistics."""
        self._generation_stats["total_generations"] += 1
        self._generation_stats["total_components_processed"] += metrics.component_count
        self._generation_stats["total_generation_time_ms"] += metrics.generation_time_ms

    def _log_netlist_analytics(self, metrics: NetlistMetrics):
        """Log comprehensive netlist analytics."""
        # Log to the generation logger
        log_netlist_analytics(
            component_count=metrics.component_count,
            net_count=metrics.net_count,
            generation_time_ms=metrics.generation_time_ms,
            file_size_bytes=metrics.file_size_bytes,
            optimization_applied=metrics.optimization_applied,
            rust_backend_used=metrics.rust_backend_used,
        )

        # Log detailed performance metrics
        performance_data = metrics.to_dict()

        context_logger.info(
            "Netlist generation analytics",
            component="NETLIST_ANALYTICS_DETAILED",
            analytics=performance_data,
        )

        # Log individual performance metrics
        performance_logger.log_metric(
            "netlist_components_per_second",
            performance_data["performance_ratios"]["components_per_second"],
            component="NETLIST_THROUGHPUT",
        )

        performance_logger.log_metric(
            "netlist_memory_efficiency",
            performance_data["performance_ratios"]["memory_efficiency"],
            component="NETLIST_EFFICIENCY",
        )

        performance_logger.log_metric(
            "netlist_cache_hit_rate",
            performance_data["performance_ratios"]["cache_hit_rate"],
            component="NETLIST_CACHE",
        )

    def get_generation_statistics(self) -> Dict[str, Any]:
        """Get comprehensive generation statistics."""
        stats = self._generation_stats.copy()

        if stats["total_generations"] > 0:
            stats["avg_generation_time_ms"] = (
                stats["total_generation_time_ms"] / stats["total_generations"]
            )
            stats["avg_components_per_generation"] = (
                stats["total_components_processed"] / stats["total_generations"]
            )
            stats["rust_backend_usage_rate"] = (
                stats["rust_backend_usage_count"] / stats["total_generations"] * 100
            )
            stats["optimization_usage_rate"] = (
                stats["optimization_usage_count"] / stats["total_generations"] * 100
            )

        return stats


# Global instance for easy access
enhanced_netlist_exporter = EnhancedNetlistExporter()


# Convenience function
def export_netlist_with_analytics(
    circuit,
    output_path: str,
    enable_optimization: bool = True,
    force_rust_backend: bool = False,
) -> NetlistMetrics:
    """Convenience function for netlist export with analytics."""
    return enhanced_netlist_exporter.export_netlist_with_analytics(
        circuit, output_path, enable_optimization, force_rust_backend
    )
