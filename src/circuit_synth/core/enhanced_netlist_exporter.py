"""
Enhanced Netlist Exporter with Performance Analytics
====================================================

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
            "cache_hits": self.cache_hits,
            "cache_misses": self.cache_misses,
            "io_operations": self.io_operations,
        }


class EnhancedNetlistExporter(NetlistExporter):
    """
    Enhanced NetlistExporter with performance analytics and monitoring.

    This class extends NetlistExporter to integrate with the generation
    logging system, providing detailed analytics and performance monitoring
    for netlist generation operations.
    """

    def __init__(self, circuit):
        """
        Initialize enhanced netlist exporter.

        Args:
            circuit: Circuit object to export
        """
        super().__init__(circuit)
        self._generation_stats = {
            "total_generations": 0,
            "total_components_processed": 0,
            "total_nets_processed": 0,
            "total_generation_time_ms": 0,
            "total_file_size_bytes": 0,
            "average_generation_time_ms": 0,
            "peak_memory_usage_mb": 0,
            "python_backend_usage_count": 0,
            "cache_hit_rate": 0,
        }
        self._last_metrics: Optional[NetlistMetrics] = None

    def generate_kicad_netlist(
        self,
        output_path: str,
        enable_optimization: bool = True,
    ) -> NetlistMetrics:
        """
        Generate KiCad netlist with full performance analytics.

        Args:
            output_path: Path to save the netlist file
            enable_optimization: Whether to enable optimization

        Returns:
            NetlistMetrics with generation performance data
        """
        stage_id = generation_logger.start_stage(
            GenerationStage.NETLIST, {"output_path": output_path}
        )

        try:
            # Track resource usage before generation
            process = psutil.Process()
            start_memory = process.memory_info().rss / 1024 / 1024  # MB
            start_cpu = process.cpu_percent()
            start_time = time.perf_counter()

            context_logger.log_info(
                "Starting netlist generation",
                component="NETLIST_GENERATOR",
                circuit_name=self.circuit.name,
                output_path=output_path,
            )

            # Count components and nets
            component_count = len(self.circuit.components)
            net_count = len(self.circuit.nets)

            # Perform the actual export
            result = None
            io_operations = 0
            cache_stats = {"hits": 0, "misses": 0}

            try:
                # Generate netlist with parent class method
                super().generate_kicad_netlist(output_path)

                # Read the result for metrics
                if os.path.exists(output_path):
                    with open(output_path, "r") as f:
                        result = f.read()
                    io_operations += 1

                performance_logger.log_performance_metric(
                    "python_netlist_export_duration",
                    time.perf_counter() - start_time,
                    component="PYTHON_NETLIST_PERFORMANCE",
                )

            except Exception as e:
                generation_logger.log_stage_error(
                    stage_id, f"Netlist export failed: {e}"
                )
                raise

            # Track resource usage after generation
            end_memory = process.memory_info().rss / 1024 / 1024
            end_cpu = process.cpu_percent()
            generation_time = (time.perf_counter() - start_time) * 1000  # ms

            # Get file size
            file_size = (
                os.path.getsize(output_path) if os.path.exists(output_path) else 0
            )

            # Create metrics
            metrics = NetlistMetrics(
                component_count=component_count,
                net_count=net_count,
                generation_time_ms=generation_time,
                file_size_bytes=file_size,
                memory_usage_mb=end_memory - start_memory,
                cpu_usage_percent=(start_cpu + end_cpu) / 2,
                optimization_applied=enable_optimization,
                cache_hits=cache_stats["hits"],
                cache_misses=cache_stats["misses"],
                io_operations=io_operations,
            )

            # Update statistics
            self._update_statistics(metrics)

            # Log analytics
            log_netlist_analytics(
                circuit_name=self.circuit.name,
                component_count=component_count,
                net_count=net_count,
                generation_time_ms=generation_time,
                file_size_bytes=file_size,
                optimization_enabled=enable_optimization,
            )

            generation_logger.complete_stage(
                stage_id,
                {
                    "component_count": component_count,
                    "net_count": net_count,
                    "file_size": file_size,
                    "generation_time_ms": generation_time,
                },
            )

            context_logger.log_info(
                "Netlist generation completed",
                component="NETLIST_GENERATOR",
                metrics=metrics.to_dict(),
            )

            self._last_metrics = metrics
            return metrics

        except Exception as e:
            generation_logger.fail_stage(stage_id, str(e))
            context_logger.log_error(
                f"Netlist generation failed: {e}", component="NETLIST_GENERATOR"
            )
            raise

    def _update_statistics(self, metrics: NetlistMetrics):
        """Update cumulative statistics."""
        stats = self._generation_stats
        stats["total_generations"] += 1
        stats["total_components_processed"] += metrics.component_count
        stats["total_nets_processed"] += metrics.net_count
        stats["total_generation_time_ms"] += metrics.generation_time_ms
        stats["total_file_size_bytes"] += metrics.file_size_bytes
        stats["python_backend_usage_count"] += 1

        # Update averages
        stats["average_generation_time_ms"] = (
            stats["total_generation_time_ms"] / stats["total_generations"]
        )

        # Update peak memory
        if metrics.memory_usage_mb > stats["peak_memory_usage_mb"]:
            stats["peak_memory_usage_mb"] = metrics.memory_usage_mb

        # Update cache hit rate
        total_cache_ops = metrics.cache_hits + metrics.cache_misses
        if total_cache_ops > 0:
            stats["cache_hit_rate"] = metrics.cache_hits / total_cache_ops * 100

    def get_generation_statistics(self) -> Dict[str, Any]:
        """Get cumulative generation statistics."""
        stats = self._generation_stats.copy()

        # Add usage rates
        if stats["total_generations"] > 0:
            stats["python_backend_usage_rate"] = 100.0  # Always Python now

        return stats

    def get_last_metrics(self) -> Optional[NetlistMetrics]:
        """Get metrics from the last generation."""
        return self._last_metrics


def export_netlist_with_analytics(
    circuit,
    output_path: str,
    enable_optimization: bool = True,
) -> NetlistMetrics:
    """
    Convenience function to export netlist with full analytics.

    Args:
        circuit: Circuit object to export
        output_path: Path to save the netlist file
        enable_optimization: Whether to enable optimization

    Returns:
        NetlistMetrics with generation performance data
    """
    exporter = EnhancedNetlistExporter(circuit)
    return exporter.generate_kicad_netlist(output_path, enable_optimization)
