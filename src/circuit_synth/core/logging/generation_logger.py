"""
Circuit Generation Logging System - Phase 6 Enhancement
======================================================

Comprehensive logging architecture for circuit generation workflows with:
- Component selection decision tracking
- Netlist generation performance analytics
- Validation workflow comprehensive logging
- Error tracking and recovery monitoring
- Real-time progress tracking
- Performance metrics collection
"""

import json
import time
import uuid
from contextlib import contextmanager
from dataclasses import asdict, dataclass
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Union

try:
    from .unified_logger import UserContext, context_logger, performance_logger
except ImportError:
    from circuit_synth.core.logging.unified_logger import (
        UserContext,
        context_logger,
        performance_logger,
    )


class GenerationStage(Enum):
    """Circuit generation pipeline stages."""

    REQUIREMENTS_EXTRACTION = "requirements_extraction"
    COMPONENT_SELECTION = "component_selection"
    SYMBOL_SEARCH = "symbol_search"
    CIRCUIT_GENERATION = "circuit_generation"
    CODE_VALIDATION = "code_validation"
    NETLIST_GENERATION = "netlist_generation"
    KICAD_GENERATION = "kicad_generation"
    PCB_GENERATION = "pcb_generation"
    PACKAGING = "packaging"
    COMPLETION = "completion"


class ComponentSelectionReason(Enum):
    """Reasons for component selection decisions."""

    EXACT_MATCH = "exact_match"
    BEST_FIT = "best_fit"
    FALLBACK = "fallback"
    USER_SPECIFIED = "user_specified"
    LIBRARY_DEFAULT = "library_default"
    PERFORMANCE_OPTIMIZED = "performance_optimized"


@dataclass
class ComponentSelection:
    """Component selection decision tracking."""

    component_type: str
    selected_symbol: str
    library: str
    reason: ComponentSelectionReason
    alternatives_considered: List[str]
    selection_criteria: Dict[str, Any]
    confidence_score: float
    timestamp: datetime
    search_duration_ms: float

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "reason": self.reason.value,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class ValidationResult:
    """Validation workflow result tracking."""

    stage: GenerationStage
    validation_type: str
    success: bool
    errors: List[str]
    warnings: List[str]
    duration_ms: float
    timestamp: datetime
    context: Dict[str, Any]

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "stage": self.stage.value,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class PerformanceMetrics:
    """Performance metrics for generation stages."""

    stage: GenerationStage
    duration_ms: float
    memory_usage_mb: float
    cpu_usage_percent: float
    io_operations: int
    cache_hits: int
    cache_misses: int
    timestamp: datetime

    def to_dict(self) -> Dict[str, Any]:
        return {
            **asdict(self),
            "stage": self.stage.value,
            "timestamp": self.timestamp.isoformat(),
        }


@dataclass
class GenerationSession:
    """Complete generation session tracking."""

    session_id: str
    user_id: Optional[str]
    description: str
    requirements: Dict[str, Any]
    start_time: datetime
    end_time: Optional[datetime]
    total_duration_ms: Optional[float]
    success: bool
    error_message: Optional[str]
    component_selections: List[ComponentSelection]
    validation_results: List[ValidationResult]
    performance_metrics: List[PerformanceMetrics]
    files_generated: List[str]

    def to_dict(self) -> Dict[str, Any]:
        return {
            "session_id": self.session_id,
            "user_id": self.user_id,
            "description": self.description,
            "requirements": self.requirements,
            "start_time": self.start_time.isoformat(),
            "end_time": self.end_time.isoformat() if self.end_time else None,
            "total_duration_ms": self.total_duration_ms,
            "success": self.success,
            "error_message": self.error_message,
            "component_selections": [cs.to_dict() for cs in self.component_selections],
            "validation_results": [vr.to_dict() for vr in self.validation_results],
            "performance_metrics": [pm.to_dict() for pm in self.performance_metrics],
            "files_generated": self.files_generated,
            "statistics": {
                "total_components": len(self.component_selections),
                "validation_errors": sum(
                    len(vr.errors) for vr in self.validation_results
                ),
                "validation_warnings": sum(
                    len(vr.warnings) for vr in self.validation_results
                ),
                "avg_component_selection_time": sum(
                    cs.search_duration_ms for cs in self.component_selections
                )
                / max(len(self.component_selections), 1),
                "total_validation_time": sum(
                    vr.duration_ms for vr in self.validation_results
                ),
                "total_performance_time": sum(
                    pm.duration_ms for pm in self.performance_metrics
                ),
            },
        }


class GenerationLogger:
    """Enhanced circuit generation logger with comprehensive tracking."""

    def __init__(self):
        self.current_session: Optional[GenerationSession] = None
        self._stage_timers: Dict[str, float] = {}

    def start_session(
        self,
        description: str,
        requirements: Dict[str, Any],
        user_id: Optional[str] = None,
    ) -> str:
        """Start a new generation session."""
        session_id = str(uuid.uuid4())

        self.current_session = GenerationSession(
            session_id=session_id,
            user_id=user_id,
            description=description,
            requirements=requirements,
            start_time=datetime.now(),
            end_time=None,
            total_duration_ms=None,
            success=False,
            error_message=None,
            component_selections=[],
            validation_results=[],
            performance_metrics=[],
            files_generated=[],
        )

        context_logger.info(
            f"Started generation session: {session_id}",
            component="GENERATION_SESSION",
            session_id=session_id,
            description=description,
            requirements=requirements,
        )

        return session_id

    def end_session(
        self,
        success: bool,
        error_message: Optional[str] = None,
        files_generated: Optional[List[str]] = None,
    ):
        """End the current generation session."""
        if not self.current_session:
            context_logger.warning(
                "No active session to end", component="GENERATION_SESSION"
            )
            return

        self.current_session.end_time = datetime.now()
        self.current_session.total_duration_ms = (
            self.current_session.end_time - self.current_session.start_time
        ).total_seconds() * 1000
        self.current_session.success = success
        self.current_session.error_message = error_message
        self.current_session.files_generated = files_generated or []

        # Log comprehensive session summary
        session_data = self.current_session.to_dict()

        context_logger.info(
            f"Completed generation session: {self.current_session.session_id}",
            component="GENERATION_SESSION_COMPLETE",
            session_data=session_data,
            success=success,
            duration_ms=self.current_session.total_duration_ms,
        )

        # Log performance summary
        performance_logger.log_metric(
            "generation_session_duration",
            self.current_session.total_duration_ms,
            unit="milliseconds",
            component="GENERATION_PERFORMANCE",
            session_id=self.current_session.session_id,
            success=success,
        )

        self.current_session = None

    @contextmanager
    def stage_timer(self, stage: GenerationStage):
        """Context manager for timing generation stages."""
        stage_key = f"{stage.value}_{time.time()}"
        start_time = time.time()
        self._stage_timers[stage_key] = start_time

        context_logger.info(
            f"Starting stage: {stage.value}",
            component="GENERATION_STAGE",
            stage=stage.value,
            session_id=(
                self.current_session.session_id if self.current_session else None
            ),
        )

        try:
            yield
        finally:
            duration_ms = (time.time() - start_time) * 1000

            context_logger.info(
                f"Completed stage: {stage.value}",
                component="GENERATION_STAGE_COMPLETE",
                stage=stage.value,
                duration_ms=duration_ms,
                session_id=(
                    self.current_session.session_id if self.current_session else None
                ),
            )

            performance_logger.log_metric(
                f"stage_{stage.value}_duration",
                duration_ms,
                unit="milliseconds",
                component="GENERATION_STAGE_PERFORMANCE",
                stage=stage.value,
            )

            del self._stage_timers[stage_key]

    def log_component_selection(
        self,
        component_type: str,
        selected_symbol: str,
        library: str,
        reason: ComponentSelectionReason,
        alternatives_considered: List[str],
        selection_criteria: Dict[str, Any],
        confidence_score: float,
        search_duration_ms: float,
    ):
        """Log component selection decision with full context."""
        selection = ComponentSelection(
            component_type=component_type,
            selected_symbol=selected_symbol,
            library=library,
            reason=reason,
            alternatives_considered=alternatives_considered,
            selection_criteria=selection_criteria,
            confidence_score=confidence_score,
            timestamp=datetime.now(),
            search_duration_ms=search_duration_ms,
        )

        if self.current_session:
            self.current_session.component_selections.append(selection)

        context_logger.info(
            f"Component selected: {component_type} -> {selected_symbol}",
            component="COMPONENT_SELECTION",
            selection_data=selection.to_dict(),
            session_id=(
                self.current_session.session_id if self.current_session else None
            ),
        )

        performance_logger.log_metric(
            "component_selection_duration",
            search_duration_ms,
            unit="milliseconds",
            component="COMPONENT_SELECTION_PERFORMANCE",
            component_type=component_type,
            confidence_score=confidence_score,
        )

    def log_validation_result(
        self,
        stage: GenerationStage,
        validation_type: str,
        success: bool,
        errors: List[str],
        warnings: List[str],
        duration_ms: float,
        context: Dict[str, Any],
    ):
        """Log validation workflow results."""
        result = ValidationResult(
            stage=stage,
            validation_type=validation_type,
            success=success,
            errors=errors,
            warnings=warnings,
            duration_ms=duration_ms,
            timestamp=datetime.now(),
            context=context,
        )

        if self.current_session:
            self.current_session.validation_results.append(result)

        log_level = "error" if not success else "warning" if warnings else "info"
        getattr(context_logger, log_level)(
            f"Validation {validation_type}: {'PASSED' if success else 'FAILED'}",
            component="VALIDATION_RESULT",
            validation_data=result.to_dict(),
            session_id=(
                self.current_session.session_id if self.current_session else None
            ),
        )

        performance_logger.log_metric(
            "validation_duration",
            duration_ms,
            unit="milliseconds",
            component="VALIDATION_PERFORMANCE",
            validation_type=validation_type,
            success=success,
        )

    def log_performance_metrics(
        self,
        stage: GenerationStage,
        duration_ms: float,
        memory_usage_mb: float,
        cpu_usage_percent: float,
        io_operations: int,
        cache_hits: int,
        cache_misses: int,
    ):
        """Log detailed performance metrics for a stage."""
        metrics = PerformanceMetrics(
            stage=stage,
            duration_ms=duration_ms,
            memory_usage_mb=memory_usage_mb,
            cpu_usage_percent=cpu_usage_percent,
            io_operations=io_operations,
            cache_hits=cache_hits,
            cache_misses=cache_misses,
            timestamp=datetime.now(),
        )

        if self.current_session:
            self.current_session.performance_metrics.append(metrics)

        context_logger.info(
            f"Performance metrics for {stage.value}",
            component="PERFORMANCE_METRICS",
            metrics_data=metrics.to_dict(),
            session_id=(
                self.current_session.session_id if self.current_session else None
            ),
        )

        # Log individual metrics
        performance_logger.log_metric(
            f"{stage.value}_memory_usage",
            memory_usage_mb,
            unit="megabytes",
            component="MEMORY_USAGE",
        )
        performance_logger.log_metric(
            f"{stage.value}_cpu_usage",
            cpu_usage_percent,
            unit="percent",
            component="CPU_USAGE",
        )
        performance_logger.log_metric(
            f"{stage.value}_io_operations",
            io_operations,
            unit="count",
            component="IO_OPERATIONS",
        )
        performance_logger.log_metric(
            f"{stage.value}_cache_hit_rate",
            cache_hits / max(cache_hits + cache_misses, 1) * 100,
            unit="percent",
            component="CACHE_PERFORMANCE",
        )

    def log_error_with_recovery(
        self,
        stage: GenerationStage,
        error: Exception,
        recovery_attempted: bool,
        recovery_successful: bool,
        recovery_details: Optional[Dict[str, Any]] = None,
    ):
        """Log errors with recovery tracking."""
        error_data = {
            "stage": stage.value,
            "error_type": type(error).__name__,
            "error_message": str(error),
            "recovery_attempted": recovery_attempted,
            "recovery_successful": recovery_successful,
            "recovery_details": recovery_details or {},
            "timestamp": datetime.now().isoformat(),
        }

        context_logger.error(
            f"Error in {stage.value}: {str(error)}",
            component="GENERATION_ERROR",
            error_data=error_data,
            session_id=(
                self.current_session.session_id if self.current_session else None
            ),
            traceback=True,
        )

        if recovery_attempted:
            recovery_status = "successful" if recovery_successful else "failed"
            context_logger.info(
                f"Recovery {recovery_status} for {stage.value} error",
                component="ERROR_RECOVERY",
                recovery_data=error_data,
                session_id=(
                    self.current_session.session_id if self.current_session else None
                ),
            )

    def log_netlist_generation_analytics(
        self,
        component_count: int,
        net_count: int,
        generation_time_ms: float,
        file_size_bytes: int,
        optimization_applied: bool,
        rust_backend_used: bool,
    ):
        """Log detailed netlist generation analytics."""
        analytics_data = {
            "component_count": component_count,
            "net_count": net_count,
            "generation_time_ms": generation_time_ms,
            "file_size_bytes": file_size_bytes,
            "optimization_applied": optimization_applied,
            "rust_backend_used": rust_backend_used,
            "components_per_second": (
                component_count / (generation_time_ms / 1000)
                if generation_time_ms > 0
                else 0
            ),
            "bytes_per_component": file_size_bytes / max(component_count, 1),
            "timestamp": datetime.now().isoformat(),
        }

        context_logger.info(
            "Netlist generation analytics",
            component="NETLIST_ANALYTICS",
            analytics_data=analytics_data,
            session_id=(
                self.current_session.session_id if self.current_session else None
            ),
        )

        # Log performance metrics
        performance_logger.log_metric(
            "netlist_generation_time",
            generation_time_ms,
            component="NETLIST_PERFORMANCE",
        )
        performance_logger.log_metric(
            "netlist_components_per_second",
            analytics_data["components_per_second"],
            component="NETLIST_PERFORMANCE",
        )
        performance_logger.log_metric(
            "netlist_file_size", file_size_bytes, component="NETLIST_PERFORMANCE"
        )


# Global instance
generation_logger = GenerationLogger()


# Convenience functions for backward compatibility
def start_generation_session(
    description: str, requirements: Dict[str, Any], user_id: Optional[str] = None
) -> str:
    """Start a new generation session."""
    return generation_logger.start_session(description, requirements, user_id)


def end_generation_session(
    success: bool,
    error_message: Optional[str] = None,
    files_generated: Optional[List[str]] = None,
):
    """End the current generation session."""
    generation_logger.end_session(success, error_message, files_generated)


def log_component_selection(
    component_type: str,
    selected_symbol: str,
    library: str,
    reason: ComponentSelectionReason,
    alternatives: List[str],
    criteria: Dict[str, Any],
    confidence: float,
    duration_ms: float,
):
    """Log component selection decision."""
    generation_logger.log_component_selection(
        component_type,
        selected_symbol,
        library,
        reason,
        alternatives,
        criteria,
        confidence,
        duration_ms,
    )


def log_validation_result(
    stage: GenerationStage,
    validation_type: str,
    success: bool,
    errors: List[str],
    warnings: List[str],
    duration_ms: float,
    context: Dict[str, Any],
):
    """Log validation result."""
    generation_logger.log_validation_result(
        stage, validation_type, success, errors, warnings, duration_ms, context
    )


def log_netlist_analytics(
    component_count: int,
    net_count: int,
    generation_time_ms: float,
    file_size_bytes: int,
    optimization_applied: bool,
    rust_backend_used: bool,
):
    """Log netlist generation analytics."""
    generation_logger.log_netlist_generation_analytics(
        component_count,
        net_count,
        generation_time_ms,
        file_size_bytes,
        optimization_applied,
        rust_backend_used,
    )
