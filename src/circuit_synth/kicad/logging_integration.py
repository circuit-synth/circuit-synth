"""
KiCad Integration Logging Enhancement
====================================

This module provides comprehensive logging integration for KiCad generation and PCB workflows,
building on the unified logging system to provide detailed monitoring, debugging, and
performance tracking for circuit generation processes.

Phase 3: KiCad Integration Logging Enhancement
- Schematic generation logging with detailed timing
- PCB generation and layout monitoring
- Component placement and routing tracking
- Performance optimization analytics
- Enhanced error handling and debugging
"""

import time
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

# Import unified logging system
from ..core.logging import (
    UserContext,
    context_logger,
    get_current_context,
    monitor_performance,
    performance_context,
    performance_logger,
)


@dataclass
class KiCadOperationMetrics:
    """Metrics for KiCad operations."""

    operation_type: (
        str  # 'schematic_generation', 'pcb_generation', 'component_placement', etc.
    )
    project_name: str
    component_count: int
    net_count: int
    duration_ms: float
    memory_usage_mb: Optional[float] = None
    success: bool = True
    error_message: Optional[str] = None
    file_sizes: Dict[str, int] = None  # File sizes in bytes
    placement_algorithm: Optional[str] = None
    routing_stats: Optional[Dict[str, Any]] = None


@dataclass
class SchematicGenerationMetrics:
    """Detailed metrics for schematic generation."""

    circuit_loading_ms: float
    symbol_lookup_ms: float
    placement_ms: float
    connection_analysis_ms: float
    file_writing_ms: float
    validation_ms: float
    total_symbols_placed: int
    collision_detections: int
    reference_assignments: int
    hierarchical_sheets: int


@dataclass
class PCBGenerationMetrics:
    """Detailed metrics for PCB generation."""

    netlist_parsing_ms: float
    component_loading_ms: float
    placement_ms: float
    routing_ms: float
    file_writing_ms: float
    board_size_mm: Tuple[float, float]
    components_placed: int
    nets_routed: int
    tracks_created: int
    vias_created: int
    routing_success_rate: float


class KiCadLogger:
    """
    Enhanced logger for KiCad operations with comprehensive monitoring.

    This class provides specialized logging for KiCad generation workflows,
    including performance tracking, error analysis, and detailed operation metrics.
    """

    def __init__(self, component: str = "KICAD"):
        self.component = component
        self.logger = context_logger
        self.perf_logger = performance_logger
        self._operation_stack: List[str] = []
        self._metrics_cache: Dict[str, Any] = {}

    @contextmanager
    def operation_context(
        self, operation_name: str, project_name: str = "", **metadata
    ):
        """
        Context manager for tracking KiCad operations with comprehensive metrics.

        Args:
            operation_name: Name of the operation (e.g., 'schematic_generation')
            project_name: Name of the KiCad project
            **metadata: Additional metadata to track
        """
        operation_id = f"{operation_name}_{uuid.uuid4().hex[:8]}"
        self._operation_stack.append(operation_id)

        # Log operation start
        self.logger.info(
            f"Starting KiCad operation: {operation_name}",
            component=self.component,
            operation_id=operation_id,
            project_name=project_name,
            **metadata,
        )

        start_time = time.perf_counter()
        start_memory = self._get_memory_usage()

        try:
            with self.perf_logger.timer(
                operation_name, component=self.component
            ) as timer_id:
                yield KiCadOperationContext(
                    operation_id=operation_id,
                    operation_name=operation_name,
                    project_name=project_name,
                    logger=self,
                    timer_id=timer_id,
                )

        except Exception as e:
            # Log operation failure
            duration_ms = (time.perf_counter() - start_time) * 1000
            self.logger.error(
                f"KiCad operation failed: {operation_name}",
                component=self.component,
                operation_id=operation_id,
                project_name=project_name,
                duration_ms=duration_ms,
                error_type=type(e).__name__,
                error_message=str(e),
                **metadata,
            )
            raise

        finally:
            # Log operation completion
            duration_ms = (time.perf_counter() - start_time) * 1000
            end_memory = self._get_memory_usage()
            memory_delta = (
                end_memory - start_memory if start_memory and end_memory else None
            )

            self.logger.info(
                f"Completed KiCad operation: {operation_name}",
                component=self.component,
                operation_id=operation_id,
                project_name=project_name,
                duration_ms=duration_ms,
                memory_delta_mb=memory_delta,
                **metadata,
            )

            if operation_id in self._operation_stack:
                self._operation_stack.remove(operation_id)

    def log_schematic_generation(
        self, metrics: SchematicGenerationMetrics, project_name: str
    ):
        """Log detailed schematic generation metrics."""
        total_time = (
            metrics.circuit_loading_ms
            + metrics.symbol_lookup_ms
            + metrics.placement_ms
            + metrics.connection_analysis_ms
            + metrics.file_writing_ms
            + metrics.validation_ms
        )

        self.logger.info(
            "Schematic generation completed",
            component=f"{self.component}_SCHEMATIC",
            project_name=project_name,
            total_duration_ms=total_time,
            circuit_loading_ms=metrics.circuit_loading_ms,
            symbol_lookup_ms=metrics.symbol_lookup_ms,
            placement_ms=metrics.placement_ms,
            connection_analysis_ms=metrics.connection_analysis_ms,
            file_writing_ms=metrics.file_writing_ms,
            validation_ms=metrics.validation_ms,
            symbols_placed=metrics.total_symbols_placed,
            collision_detections=metrics.collision_detections,
            reference_assignments=metrics.reference_assignments,
            hierarchical_sheets=metrics.hierarchical_sheets,
        )

    def log_pcb_generation(self, metrics: PCBGenerationMetrics, project_name: str):
        """Log detailed PCB generation metrics."""
        total_time = (
            metrics.netlist_parsing_ms
            + metrics.component_loading_ms
            + metrics.placement_ms
            + metrics.routing_ms
            + metrics.file_writing_ms
        )

        self.logger.info(
            "PCB generation completed",
            component=f"{self.component}_PCB",
            project_name=project_name,
            total_duration_ms=total_time,
            netlist_parsing_ms=metrics.netlist_parsing_ms,
            component_loading_ms=metrics.component_loading_ms,
            placement_ms=metrics.placement_ms,
            routing_ms=metrics.routing_ms,
            file_writing_ms=metrics.file_writing_ms,
            board_width_mm=metrics.board_size_mm[0],
            board_height_mm=metrics.board_size_mm[1],
            components_placed=metrics.components_placed,
            nets_routed=metrics.nets_routed,
            tracks_created=metrics.tracks_created,
            vias_created=metrics.vias_created,
            routing_success_rate=metrics.routing_success_rate,
        )

    def log_component_placement(
        self,
        component_ref: str,
        position: Tuple[float, float],
        rotation: float = 0.0,
        placement_algorithm: str = "default",
    ):
        """Log individual component placement."""
        self.logger.debug(
            f"Component placed: {component_ref}",
            component=f"{self.component}_PLACEMENT",
            component_ref=component_ref,
            x_position=position[0],
            y_position=position[1],
            rotation=rotation,
            placement_algorithm=placement_algorithm,
        )

    def log_symbol_lookup(
        self, lib_id: str, lookup_time_ms: float, found: bool, cache_hit: bool = False
    ):
        """Log symbol library lookup operations."""
        self.logger.debug(
            f"Symbol lookup: {lib_id}",
            component=f"{self.component}_SYMBOL",
            lib_id=lib_id,
            lookup_time_ms=lookup_time_ms,
            found=found,
            cache_hit=cache_hit,
        )

    def log_collision_detection(
        self, component_ref: str, collision_count: int, resolution_time_ms: float
    ):
        """Log collision detection and resolution."""
        self.logger.debug(
            f"Collision detection: {component_ref}",
            component=f"{self.component}_COLLISION",
            component_ref=component_ref,
            collision_count=collision_count,
            resolution_time_ms=resolution_time_ms,
        )

    def log_routing_progress(
        self,
        nets_completed: int,
        total_nets: int,
        success_rate: float,
        current_net: str = "",
    ):
        """Log routing progress during PCB generation."""
        progress_percent = (nets_completed / total_nets * 100) if total_nets > 0 else 0

        self.logger.info(
            f"Routing progress: {nets_completed}/{total_nets} nets ({progress_percent:.1f}%)",
            component=f"{self.component}_ROUTING",
            nets_completed=nets_completed,
            total_nets=total_nets,
            progress_percent=progress_percent,
            success_rate=success_rate,
            current_net=current_net,
        )

    def log_file_generation(
        self,
        file_path: Path,
        file_type: str,
        size_bytes: int,
        generation_time_ms: float,
    ):
        """Log KiCad file generation."""
        self.logger.info(
            f"Generated {file_type} file: {file_path.name}",
            component=f"{self.component}_FILE",
            file_path=str(file_path),
            file_type=file_type,
            size_bytes=size_bytes,
            size_kb=size_bytes / 1024,
            generation_time_ms=generation_time_ms,
        )

    def log_validation_result(
        self,
        validation_type: str,
        passed: bool,
        issues: List[str] = None,
        validation_time_ms: float = 0,
    ):
        """Log validation results."""
        self.logger.info(
            f"Validation {validation_type}: {'PASSED' if passed else 'FAILED'}",
            component=f"{self.component}_VALIDATION",
            validation_type=validation_type,
            passed=passed,
            issue_count=len(issues) if issues else 0,
            issues=issues[:5] if issues else [],  # Log first 5 issues
            validation_time_ms=validation_time_ms,
        )

    def log_performance_bottleneck(
        self,
        operation: str,
        duration_ms: float,
        threshold_ms: float,
        details: Dict[str, Any] = None,
    ):
        """Log performance bottlenecks for optimization."""
        self.logger.warning(
            f"Performance bottleneck detected: {operation}",
            component=f"{self.component}_PERFORMANCE",
            operation=operation,
            duration_ms=duration_ms,
            threshold_ms=threshold_ms,
            slowdown_factor=duration_ms / threshold_ms,
            details=details or {},
        )

    def _get_memory_usage(self) -> Optional[float]:
        """Get current memory usage in MB."""
        try:
            import psutil

            process = psutil.Process()
            return process.memory_info().rss / 1024 / 1024
        except ImportError:
            return None


class KiCadOperationContext:
    """Context object for KiCad operations."""

    def __init__(
        self,
        operation_id: str,
        operation_name: str,
        project_name: str,
        logger: KiCadLogger,
        timer_id: str,
    ):
        self.operation_id = operation_id
        self.operation_name = operation_name
        self.project_name = project_name
        self.logger = logger
        self.timer_id = timer_id
        self.metrics: Dict[str, Any] = {}

    def add_metric(self, key: str, value: Any):
        """Add a metric to the operation context."""
        self.metrics[key] = value

    def log_progress(self, message: str, progress_percent: float = None, **kwargs):
        """Log progress within the operation."""
        self.logger.logger.info(
            f"[{self.operation_name}] {message}",
            component=self.logger.component,
            operation_id=self.operation_id,
            project_name=self.project_name,
            progress_percent=progress_percent,
            **kwargs,
        )


# Global KiCad logger instances
kicad_logger = KiCadLogger("KICAD")
schematic_logger = KiCadLogger("KICAD_SCHEMATIC")
pcb_logger = KiCadLogger("KICAD_PCB")


# Convenience functions for common operations
@contextmanager
def log_schematic_generation(project_name: str, **metadata):
    """Context manager for schematic generation logging."""
    with kicad_logger.operation_context(
        "schematic_generation", project_name, **metadata
    ) as ctx:
        yield ctx


@contextmanager
def log_pcb_generation(project_name: str, **metadata):
    """Context manager for PCB generation logging."""
    with kicad_logger.operation_context(
        "pcb_generation", project_name, **metadata
    ) as ctx:
        yield ctx


@contextmanager
def log_component_placement(project_name: str, algorithm: str = "default", **metadata):
    """Context manager for component placement logging."""
    with kicad_logger.operation_context(
        "component_placement", project_name, placement_algorithm=algorithm, **metadata
    ) as ctx:
        yield ctx


def log_kicad_error(
    error: Exception, operation: str, project_name: str = "", **context
):
    """Log KiCad-specific errors with context."""
    kicad_logger.logger.error(
        f"KiCad error in {operation}: {str(error)}",
        component="KICAD_ERROR",
        operation=operation,
        project_name=project_name,
        error_type=type(error).__name__,
        error_message=str(error),
        **context,
    )


def log_kicad_warning(message: str, operation: str, project_name: str = "", **context):
    """Log KiCad-specific warnings."""
    kicad_logger.logger.warning(
        f"KiCad warning in {operation}: {message}",
        component="KICAD_WARNING",
        operation=operation,
        project_name=project_name,
        **context,
    )
