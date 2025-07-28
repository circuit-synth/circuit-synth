"""
Specialized loggers for different components of Circuit Synth.
Each logger extends the base CircuitSynthLogger with component-specific functionality.
"""

import json
import time
from datetime import datetime
from typing import Any, Dict, List, Optional

from .circuit_synth_logger import CircuitSynthLogger


class DashboardLogger(CircuitSynthLogger):
    """
    Specialized logger for Plotly Dash dashboard events.
    Tracks all user interactions, callback executions, and UI state changes.
    """

    def __init__(self, username: str, session_id: Optional[str] = None):
        super().__init__(username, session_id)
        self.callback_stack = []  # Track nested callbacks

    def log_callback_start(
        self,
        callback_id: str,
        inputs: Dict[str, Any],
        state: Dict[str, Any],
        triggered_by: str,
    ):
        """Log the start of a callback execution."""
        start_time = time.time()
        self.callback_stack.append(
            {
                "callback_id": callback_id,
                "start_time": start_time,
                "triggered_by": triggered_by,
            }
        )

        self.log_event(
            "dash_callback_start",
            callback_id=callback_id,
            inputs=inputs,
            state=state,
            triggered_by=triggered_by,
            stack_depth=len(self.callback_stack),
        )

        return start_time

    def log_callback_end(
        self, callback_id: str, outputs: Dict[str, Any], error: Optional[str] = None
    ):
        """Log the end of a callback execution."""
        if not self.callback_stack:
            return

        # Find and remove the callback from stack
        callback_info = None
        for i, cb in enumerate(self.callback_stack):
            if cb["callback_id"] == callback_id:
                callback_info = self.callback_stack.pop(i)
                break

        if callback_info:
            duration_ms = (time.time() - callback_info["start_time"]) * 1000

            self.log_event(
                "dash_callback_end",
                callback_id=callback_id,
                outputs=outputs,
                duration_ms=duration_ms,
                error=error,
                success=error is None,
                stack_depth=len(self.callback_stack),
            )

    def log_user_interaction(
        self,
        component_id: str,
        action: str,
        value: Any,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log a user interaction with a dashboard component."""
        self.log_event(
            "dash_user_interaction",
            component_id=component_id,
            action=action,
            value=value,
            metadata=metadata or {},
        )

    def log_page_navigation(self, from_page: str, to_page: str, navigation_method: str):
        """Log page navigation events."""
        self.log_event(
            "dash_page_navigation",
            from_page=from_page,
            to_page=to_page,
            navigation_method=navigation_method,
        )


class LLMLogger(CircuitSynthLogger):
    """
    Specialized logger for LLM (Language Model) interactions.
    Tracks API calls, responses, token usage, costs, and conversation flow.
    """

    def __init__(self, username: str, session_id: Optional[str] = None):
        super().__init__(username, session_id)
        self.active_requests = {}  # Track in-flight requests

    def log_request(
        self,
        request_id: str,
        model: str,
        provider: str,
        prompt: str,
        parameters: Dict[str, Any],
    ):
        """Log an LLM API request."""
        start_time = time.time()
        self.active_requests[request_id] = {
            "start_time": start_time,
            "model": model,
            "provider": provider,
        }

        # Calculate approximate token count (rough estimate)
        prompt_tokens = len(prompt.split()) * 1.3  # Rough approximation

        self.log_event(
            "llm_request",
            request_id=request_id,
            model=model,
            provider=provider,
            prompt_preview=prompt[:500] + "..." if len(prompt) > 500 else prompt,
            prompt_length=len(prompt),
            estimated_prompt_tokens=int(prompt_tokens),
            parameters=parameters,
            chat_id=self.chat_id,
        )

        return request_id

    def log_response(
        self,
        request_id: str,
        response: str,
        actual_tokens: Optional[Dict[str, int]] = None,
        cost: Optional[float] = None,
        error: Optional[str] = None,
    ):
        """Log an LLM API response."""
        if request_id not in self.active_requests:
            return

        request_info = self.active_requests.pop(request_id)
        duration_ms = (time.time() - request_info["start_time"]) * 1000

        self.log_event(
            "llm_response",
            request_id=request_id,
            model=request_info["model"],
            provider=request_info["provider"],
            response_preview=(
                response[:500] + "..." if len(response) > 500 else response
            ),
            response_length=len(response),
            duration_ms=duration_ms,
            tokens=actual_tokens or {},
            cost_usd=cost,
            error=error,
            success=error is None,
            chat_id=self.chat_id,
        )

    def log_conversation_turn(
        self,
        turn_number: int,
        role: str,
        content: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log a conversation turn in a chat session."""
        self.log_event(
            "llm_conversation_turn",
            turn_number=turn_number,
            role=role,
            content_preview=content[:200] + "..." if len(content) > 200 else content,
            content_length=len(content),
            metadata=metadata or {},
            chat_id=self.chat_id,
        )

    def log_model_switch(self, from_model: str, to_model: str, reason: str):
        """Log when the user switches between models."""
        self.log_event(
            "llm_model_switch",
            from_model=from_model,
            to_model=to_model,
            reason=reason,
            chat_id=self.chat_id,
        )


class FileOperationLogger(CircuitSynthLogger):
    """
    Specialized logger for file operations.
    Tracks all file I/O, circuit generation outputs, and file management.
    """

    def __init__(self, username: str, session_id: Optional[str] = None):
        super().__init__(username, session_id)
        self.operation_timers = {}

    def log_file_read(
        self,
        file_path: str,
        file_size: int,
        purpose: str,
        success: bool = True,
        error: Optional[str] = None,
    ):
        """Log a file read operation."""
        self.log_event(
            "file_read",
            file_path=file_path,
            file_size=file_size,
            purpose=purpose,
            success=success,
            error=error,
        )

    def log_file_write(
        self,
        file_path: str,
        file_size: int,
        file_type: str,
        purpose: str,
        success: bool = True,
        error: Optional[str] = None,
    ):
        """Log a file write operation."""
        self.log_event(
            "file_write",
            file_path=file_path,
            file_size=file_size,
            file_type=file_type,
            purpose=purpose,
            success=success,
            error=error,
        )

    def log_file_delete(
        self,
        file_path: str,
        reason: str,
        success: bool = True,
        error: Optional[str] = None,
    ):
        """Log a file deletion."""
        self.log_event(
            "file_delete",
            file_path=file_path,
            reason=reason,
            success=success,
            error=error,
        )

    def log_circuit_generation_start(
        self, generation_id: str, circuit_type: str, parameters: Dict[str, Any]
    ):
        """Log the start of circuit generation."""
        start_time = time.time()
        self.operation_timers[generation_id] = start_time

        self.log_event(
            "circuit_generation_start",
            generation_id=generation_id,
            circuit_type=circuit_type,
            parameters=parameters,
        )

        return generation_id

    def log_circuit_generation_complete(
        self,
        generation_id: str,
        output_files: List[str],
        success: bool = True,
        error: Optional[str] = None,
    ):
        """Log the completion of circuit generation."""
        duration_ms = 0
        if generation_id in self.operation_timers:
            duration_ms = (
                time.time() - self.operation_timers.pop(generation_id)
            ) * 1000

        self.log_event(
            "circuit_generation_complete",
            generation_id=generation_id,
            output_files=output_files,
            file_count=len(output_files),
            duration_ms=duration_ms,
            success=success,
            error=error,
        )

    def log_kicad_operation(
        self,
        operation: str,
        file_path: str,
        details: Dict[str, Any],
        success: bool = True,
    ):
        """Log KiCad-specific file operations."""
        self.log_event(
            "kicad_operation",
            operation=operation,
            file_path=file_path,
            details=details,
            success=success,
        )

    def log_file_upload(
        self, file_name: str, file_size: int, file_type: str, source: str
    ):
        """Log file upload operations."""
        self.log_event(
            "file_upload",
            file_name=file_name,
            file_size=file_size,
            file_type=file_type,
            source=source,
        )

    def log_file_download(self, file_path: str, file_size: int, destination: str):
        """Log file download operations."""
        self.log_event(
            "file_download",
            file_path=file_path,
            file_size=file_size,
            destination=destination,
        )


class PerformanceLogger(CircuitSynthLogger):
    """
    Specialized logger for performance metrics and system monitoring.
    Tracks resource usage, response times, and system health.
    """

    def __init__(self, username: str, session_id: Optional[str] = None):
        super().__init__(username, session_id)
        self.metric_buffers = {}  # Buffer metrics for batch logging

    def log_response_time(
        self,
        operation: str,
        duration_ms: float,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """Log response time for an operation."""
        self.log_event(
            "performance_response_time",
            operation=operation,
            duration_ms=duration_ms,
            metadata=metadata or {},
        )

    def log_memory_usage(
        self, process: str, memory_mb: float, peak_memory_mb: Optional[float] = None
    ):
        """Log memory usage metrics."""
        self.log_event(
            "performance_memory",
            process=process,
            memory_mb=memory_mb,
            peak_memory_mb=peak_memory_mb,
        )

    def log_cpu_usage(
        self, process: str, cpu_percent: float, core_count: Optional[int] = None
    ):
        """Log CPU usage metrics."""
        self.log_event(
            "performance_cpu",
            process=process,
            cpu_percent=cpu_percent,
            core_count=core_count,
        )

    def log_database_query(
        self,
        query_type: str,
        table: str,
        duration_ms: float,
        row_count: Optional[int] = None,
    ):
        """Log database query performance."""
        self.log_event(
            "performance_database",
            query_type=query_type,
            table=table,
            duration_ms=duration_ms,
            row_count=row_count,
        )

    def log_api_latency(
        self, endpoint: str, method: str, status_code: int, duration_ms: float
    ):
        """Log API endpoint latency."""
        self.log_event(
            "performance_api",
            endpoint=endpoint,
            method=method,
            status_code=status_code,
            duration_ms=duration_ms,
            success=200 <= status_code < 300,
        )

    def log_batch_metrics(self, metrics: List[Dict[str, Any]]):
        """Log multiple metrics in a batch."""
        self.log_event(
            "performance_batch",
            metrics=metrics,
            metric_count=len(metrics),
            timestamp_range={
                "start": min(m.get("timestamp", "") for m in metrics),
                "end": max(m.get("timestamp", "") for m in metrics),
            },
        )

    def start_operation_timer(self, operation_id: str) -> str:
        """Start timing an operation."""
        self.metric_buffers[operation_id] = time.time()
        return operation_id

    def end_operation_timer(
        self,
        operation_id: str,
        operation_name: str,
        metadata: Optional[Dict[str, Any]] = None,
    ):
        """End timing an operation and log the duration."""
        if operation_id in self.metric_buffers:
            start_time = self.metric_buffers.pop(operation_id)
            duration_ms = (time.time() - start_time) * 1000
            self.log_response_time(operation_name, duration_ms, metadata)
