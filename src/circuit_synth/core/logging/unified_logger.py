"""
Circuit Synth Unified Logging System
====================================

Main implementation of the unified logging system based on loguru with multi-user support,
performance monitoring, LLM conversation tracking, and comprehensive error handling.

This module provides the core logging infrastructure that consolidates all logging
across the Circuit Synth application into a single, scalable, thread-safe system.
"""

import json
import sys
import threading
import time
import traceback
import uuid
from concurrent.futures import ThreadPoolExecutor
from contextlib import contextmanager
from contextvars import ContextVar
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional, Union

try:
    from loguru import logger
except ImportError:
    raise ImportError(
        "loguru is required for unified logging. Install with: pip install loguru"
    )

try:
    import yaml
except ImportError:
    raise ImportError(
        "PyYAML is required for configuration. Install with: pip install PyYAML"
    )

# Context variables for user tracking (thread-safe)
current_user: ContextVar[Optional[str]] = ContextVar("current_user", default=None)
current_session: ContextVar[Optional[str]] = ContextVar("current_session", default=None)
current_request: ContextVar[Optional[str]] = ContextVar("current_request", default=None)
current_chat: ContextVar[Optional[str]] = ContextVar("current_chat", default=None)

# Global state
_config = None
_initialized = False
_failsafe_enabled = True


class LoggingFailsafe:
    """Failsafe logging when primary system fails."""

    def __init__(self):
        self.fallback_enabled = True
        self.fallback_file = Path.home() / ".circuit-synth" / "logs" / "fallback.log"
        self._lock = threading.Lock()
        self._ensure_directory()

    def _ensure_directory(self):
        """Safely ensure the logging directory exists."""
        try:
            self.fallback_file.parent.mkdir(parents=True, exist_ok=True)
        except (OSError, PermissionError) as e:
            # If we can't create the logging directory, disable fallback logging
            # This prevents import failures in CI environments
            self.fallback_enabled = False
            # Try to log to stderr as last resort
            try:
                import sys

                print(
                    f"Warning: Could not create circuit-synth logging directory: {e}",
                    file=sys.stderr,
                )
            except:
                pass  # Even stderr failed, just disable logging

    def emergency_log(self, message: str, level: str = "ERROR"):
        """Emergency logging when main system fails."""
        if not self.fallback_enabled:
            return

        timestamp = datetime.utcnow().isoformat()
        fallback_entry = f"{timestamp} | {level} | FAILSAFE | {message}\n"

        try:
            with self._lock:
                with open(self.fallback_file, "a") as f:
                    f.write(fallback_entry)
        except Exception:
            # Last resort - write to stderr
            sys.stderr.write(f"LOGGING_EMERGENCY: {fallback_entry}")

    @contextmanager
    def protected_logging(self):
        """Context manager that catches logging failures."""
        try:
            yield
        except Exception as e:
            self.emergency_log(f"Logging system failure: {e}")
            # Re-raise to maintain error visibility
            raise


# Global failsafe instance
_failsafe = LoggingFailsafe()


class UserContext:
    """Manages user context for logging isolation using contextvars."""

    def __init__(self, user_id: str, session_id: Optional[str] = None):
        self.user_id = user_id
        self.session_id = (
            session_id or f"{user_id}_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
        )
        self.request_id = None
        self.chat_id = None
        self._tokens = {}

    def __enter__(self):
        """Enter context and set context variables."""
        self._tokens["user"] = current_user.set(self.user_id)
        self._tokens["session"] = current_session.set(self.session_id)
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and reset context variables."""
        for token in self._tokens.values():
            if hasattr(token, "var"):
                token.var.reset(token)

    def set_request(self, request_id: str):
        """Set request ID for current context."""
        self.request_id = request_id
        return current_request.set(request_id)

    def set_chat(self, chat_id: str):
        """Set chat ID for current context."""
        self.chat_id = chat_id
        return current_chat.set(chat_id)


class ContextLogger:
    """Logger that automatically includes user context using loguru's bind functionality."""

    _instance = None
    _lock = threading.Lock()

    def __new__(cls):
        """Implement singleton pattern."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        # Only initialize once
        if hasattr(self, "_initialized"):
            return

        self.logger = logger
        self._error_count = 0
        self._max_errors = 100
        self._initialized = True

    def _get_context_extras(self, **kwargs) -> Dict[str, Any]:
        """Extract context information for logging."""
        extras = {
            "user": current_user.get() or "system",
            "session": current_session.get() or "none",
            "request_id": current_request.get() or "",
            "chat_id": current_chat.get() or "",
            "timestamp": datetime.now().astimezone().isoformat(),
            **kwargs,
        }
        return extras

    def _safe_log(self, level: str, message: str, **kwargs):
        """Safely execute logging with error handling using loguru's bind."""
        if self._error_count >= self._max_errors:
            return  # Logging disabled due to too many errors

        try:
            with _failsafe.protected_logging():
                extras = self._get_context_extras(**kwargs)
                # Use loguru's bind to add context
                bound_logger = self.logger.bind(**extras)
                getattr(bound_logger, level.lower())(message)
        except Exception as e:
            self._error_count += 1
            _failsafe.emergency_log(f"Log operation failed: {e}")

            if self._error_count >= self._max_errors:
                _failsafe.emergency_log(
                    "Logging system disabled due to excessive errors"
                )

    def info(self, message: str, component: str = "SYSTEM", **kwargs):
        """Log info message with context."""
        self._safe_log("INFO", message, component=component, **kwargs)

    def error(self, message: str, component: str = "ERROR", **kwargs):
        """Log error message with context."""
        self._safe_log("ERROR", message, component=component, **kwargs)

    def debug(self, message: str, component: str = "DEBUG", **kwargs):
        """Log debug message with context."""
        self._safe_log("DEBUG", message, component=component, **kwargs)

    def warning(self, message: str, component: str = "WARNING", **kwargs):
        """Log warning message with context."""
        self._safe_log("WARNING", message, component=component, **kwargs)


@dataclass
class PerformanceMetric:
    """Performance metric data structure."""

    operation: str
    duration_ms: float
    user_id: str
    session_id: str
    component: str
    timestamp: str
    metadata: Dict[str, Any]
    memory_usage_mb: Optional[float] = None
    cpu_percent: Optional[float] = None


class PerformanceLogger:
    """High-performance timing and metrics collection."""

    def __init__(self, context_logger: ContextLogger):
        self.logger = context_logger
        self._active_timers: Dict[str, float] = {}
        self._lock = threading.Lock()

    @contextmanager
    def timer(self, operation: str, component: str = "PERF", **metadata):
        """Context manager for timing operations."""
        timer_id = f"{operation}_{time.time()}"
        start_time = time.perf_counter()

        try:
            yield timer_id
        finally:
            end_time = time.perf_counter()
            duration_ms = (end_time - start_time) * 1000

            metric = PerformanceMetric(
                operation=operation,
                duration_ms=duration_ms,
                user_id=current_user.get() or "system",
                session_id=current_session.get() or "none",
                component=component,
                timestamp=datetime.utcnow().isoformat(),
                metadata=metadata,
            )

            # Log as structured JSON for analysis using loguru's bind
            logger.bind(log_type="performance", **asdict(metric)).info(
                json.dumps(asdict(metric))
            )

            # Also log human-readable version
            self.logger.info(
                f"{operation} completed in {duration_ms:.2f}ms",
                component=component,
                duration_ms=duration_ms,
                **metadata,
            )

    def log_metric(
        self, name: str, value: float, unit: str, component: str = "METRICS", **metadata
    ):
        """Log a custom metric."""
        metric_data = {
            "metric_name": name,
            "value": value,
            "unit": unit,
            "user_id": current_user.get() or "system",
            "session_id": current_session.get() or "none",
            "timestamp": datetime.now().astimezone().isoformat(),
            "metadata": metadata,
        }

        # Use loguru's bind for structured logging
        logger.bind(log_type="performance", **metric_data).info(json.dumps(metric_data))

        self.logger.info(
            f"Metric {name}: {value} {unit}", component=component, **metric_data
        )


@dataclass
class LLMRequest:
    """LLM request data structure."""

    request_id: str
    user_id: str
    session_id: str
    chat_id: str
    model: str
    provider: str
    prompt: str
    prompt_tokens: int
    temperature: float
    max_tokens: int
    timestamp: str
    estimated_cost: float


@dataclass
class LLMResponse:
    """LLM response data structure."""

    request_id: str
    response: str
    completion_tokens: int
    total_tokens: int
    actual_cost: float
    duration_ms: float
    timestamp: str
    finish_reason: str
    model_version: str


@dataclass
class LLMConversationTurn:
    """LLM conversation turn data structure."""

    turn_number: int
    request: LLMRequest
    response: Optional[LLMResponse] = None
    error: Optional[Dict[str, Any]] = None


class LLMConversationLogger:
    """Comprehensive LLM conversation logging with cost tracking."""

    def __init__(self, context_logger: ContextLogger):
        self.logger = context_logger
        self.active_conversations: Dict[str, List[LLMConversationTurn]] = {}
        self.conversation_costs: Dict[str, float] = {}
        self._lock = threading.Lock()

    def start_conversation(self, chat_id: str) -> str:
        """Initialize a new conversation session."""
        with self._lock:
            self.active_conversations[chat_id] = []
            self.conversation_costs[chat_id] = 0.0

        self.logger.info(
            f"Started LLM conversation",
            component="LLM_CONV",
            chat_id=chat_id,
            action="conversation_start",
        )

        return chat_id

    def log_request(
        self,
        chat_id: str,
        model: str,
        provider: str,
        prompt: str,
        prompt_tokens: int,
        temperature: float = 0.7,
        max_tokens: int = 1000,
        estimated_cost: float = 0.0,
    ) -> str:
        """Log LLM request with full context."""
        request_id = str(uuid.uuid4())

        request = LLMRequest(
            request_id=request_id,
            user_id=current_user.get() or "system",
            session_id=current_session.get() or "none",
            chat_id=chat_id,
            model=model,
            provider=provider,
            prompt=prompt,
            prompt_tokens=prompt_tokens,
            temperature=temperature,
            max_tokens=max_tokens,
            timestamp=datetime.utcnow().isoformat(),
            estimated_cost=estimated_cost,
        )

        # Initialize conversation if needed
        if chat_id not in self.active_conversations:
            self.start_conversation(chat_id)

        # Create new turn
        with self._lock:
            turn_number = len(self.active_conversations[chat_id]) + 1
            turn = LLMConversationTurn(turn_number=turn_number, request=request)
            self.active_conversations[chat_id].append(turn)

        # Log structured data using loguru's bind
        logger.bind(
            log_type="llm_conversation", action="request", **asdict(request)
        ).info(json.dumps(asdict(request)))

        # Log human-readable
        prompt_preview = prompt[:100] + "..." if len(prompt) > 100 else prompt
        self.logger.info(
            f'LLM Request to {model}: "{prompt_preview}" ({prompt_tokens} tokens, ~${estimated_cost:.4f})',
            component="LLM_REQ",
            chat_id=chat_id,
            request_id=request_id,
            model=model,
            prompt_tokens=prompt_tokens,
            estimated_cost=estimated_cost,
        )

        return request_id

    def log_response(
        self,
        request_id: str,
        response: str,
        completion_tokens: int,
        total_tokens: int,
        actual_cost: float,
        duration_ms: float,
        finish_reason: str = "stop",
        model_version: str = "unknown",
    ):
        """Log LLM response with cost and performance data."""

        # Find the conversation and turn
        chat_id = None
        turn = None
        with self._lock:
            for cid, turns in self.active_conversations.items():
                for t in turns:
                    if t.request.request_id == request_id:
                        chat_id = cid
                        turn = t
                        break
                if turn:
                    break

        if not turn:
            self.logger.error(
                f"Could not find request {request_id} for response logging",
                component="LLM_ERR",
                request_id=request_id,
            )
            return

        response_obj = LLMResponse(
            request_id=request_id,
            response=response,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            actual_cost=actual_cost,
            duration_ms=duration_ms,
            timestamp=datetime.utcnow().isoformat(),
            finish_reason=finish_reason,
            model_version=model_version,
        )

        with self._lock:
            turn.response = response_obj
            self.conversation_costs[chat_id] += actual_cost

        # Log structured data using loguru's bind
        logger.bind(
            log_type="llm_conversation", action="response", **asdict(response_obj)
        ).info(json.dumps(asdict(response_obj)))

        # Log human-readable
        response_preview = response[:100] + "..." if len(response) > 100 else response
        self.logger.info(
            f'LLM Response: "{response_preview}" ({completion_tokens} tokens, ${actual_cost:.4f}, {duration_ms:.0f}ms)',
            component="LLM_RESP",
            chat_id=chat_id,
            request_id=request_id,
            completion_tokens=completion_tokens,
            actual_cost=actual_cost,
            duration_ms=duration_ms,
        )

    def log_error(self, request_id: str, error: Exception, context: Dict[str, Any]):
        """Log LLM request/response errors."""
        with self._lock:
            for chat_id, turns in self.active_conversations.items():
                for turn in turns:
                    if turn.request.request_id == request_id:
                        turn.error = {
                            "error_type": type(error).__name__,
                            "error_message": str(error),
                            "timestamp": datetime.now().astimezone().isoformat(),
                            "context": context,
                        }
                        break

        self.logger.error(
            f"LLM Error: {type(error).__name__}: {str(error)}",
            component="LLM_ERR",
            request_id=request_id,
            error_type=type(error).__name__,
            **context,
        )

    def get_conversation_summary(self, chat_id: str) -> Dict[str, Any]:
        """Get summary statistics for a conversation."""
        if chat_id not in self.active_conversations:
            return {}

        with self._lock:
            turns = self.active_conversations[chat_id]
            total_turns = len(turns)
            total_tokens = sum(t.response.total_tokens for t in turns if t.response)
            total_cost = self.conversation_costs.get(chat_id, 0.0)
            responses_with_timing = [t for t in turns if t.response]
            avg_response_time = sum(
                t.response.duration_ms for t in responses_with_timing
            ) / max(1, len(responses_with_timing))

        return {
            "chat_id": chat_id,
            "total_turns": total_turns,
            "total_tokens": total_tokens,
            "total_cost": total_cost,
            "average_response_time_ms": avg_response_time,
            "models_used": list(set(t.request.model for t in turns)),
            "error_count": len([t for t in turns if t.error]),
        }


def initialize_logging(
    config_path: str = "src/circuit_synth/core/logging/logging_config.yaml",
):
    """Initialize the unified logging system with proper loguru configuration."""
    global _config, _initialized

    if _initialized:
        return

    try:
        # Load configuration
        from .config_manager import LoggingConfig

        _config = LoggingConfig(config_path)

        # Remove default loguru handler
        logger.remove()

        # Configure console sink if enabled
        if _config.get("logging.sinks.console.enabled", True):
            console_format = _config.get(
                "logging.format.console",
                "<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{extra[component]: <10}</cyan> | <blue>{extra[user]: <12}</blue> | <yellow>{extra[session]: <8}</yellow> | {message}",
            )
            console_level = _config.get("logging.sinks.console.level", "INFO")

            logger.add(
                sys.stderr,
                format=console_format,
                level=console_level,
                filter=lambda record: record["extra"].get("sink_type") != "file_only",
            )

        # Configure main file sink
        main_file_path = _config.get(
            "logging.sinks.main_file.path", "logs/circuit_synth_{time:YYYY-MM-DD}.log"
        )
        file_format = _config.get(
            "logging.format.file",
            "{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {extra[component]: <10} | {extra[user]: <12} | {extra[session]: <8} | {extra[request_id]: <12} | {message}",
        )

        # Create logs directory
        Path(main_file_path).parent.mkdir(exist_ok=True)

        logger.add(
            main_file_path,
            format=file_format,
            rotation=_config.get("logging.sinks.main_file.rotation", "100 MB"),
            retention=_config.get("logging.sinks.main_file.retention", "30 days"),
            compression=_config.get("logging.sinks.main_file.compression", "gz"),
            level=_config.get("logging.sinks.main_file.level", "DEBUG"),
            enqueue=_config.get(
                "logging.performance.async_logging", True
            ),  # Enable async for performance
        )

        # Configure performance file sink
        if _config.get("logging.sinks.performance_file.enabled", True):
            perf_file_path = _config.get(
                "logging.sinks.performance_file.path",
                "logs/performance_{time:YYYY-MM-DD}.jsonl",
            )
            Path(perf_file_path).parent.mkdir(exist_ok=True)

            logger.add(
                perf_file_path,
                format="{message}",
                filter=lambda record: record["extra"].get("log_type") == "performance",
                rotation=_config.get(
                    "logging.sinks.performance_file.rotation", "50 MB"
                ),
                retention=_config.get(
                    "logging.sinks.performance_file.retention", "7 days"
                ),
                level=_config.get("logging.sinks.performance_file.level", "DEBUG"),
                enqueue=_config.get("logging.performance.async_logging", True),
            )

        # Configure LLM conversation file sink
        if _config.get("logging.sinks.llm_conversations.enabled", True):
            llm_file_path = _config.get(
                "logging.sinks.llm_conversations.path",
                "logs/llm_conversations_{time:YYYY-MM-DD}.jsonl",
            )
            Path(llm_file_path).parent.mkdir(exist_ok=True)

            logger.add(
                llm_file_path,
                format="{message}",
                filter=lambda record: record["extra"].get("log_type")
                == "llm_conversation",
                rotation=_config.get(
                    "logging.sinks.llm_conversations.rotation", "200 MB"
                ),
                retention=_config.get(
                    "logging.sinks.llm_conversations.retention", "90 days"
                ),
                level=_config.get("logging.sinks.llm_conversations.level", "DEBUG"),
                enqueue=_config.get("logging.performance.async_logging", True),
            )

        _initialized = True

        # Log successful initialization
        context_logger = ContextLogger()
        context_logger.info(
            "Unified logging system initialized successfully", component="SYSTEM"
        )

    except Exception as e:
        _failsafe.emergency_log(f"Failed to initialize unified logging: {e}")
        raise


# Create global instances for easy import
context_logger = ContextLogger()
performance_logger = PerformanceLogger(context_logger)
llm_conversation_logger = LLMConversationLogger(context_logger)


# Convenience functions for backward compatibility
def get_logger() -> ContextLogger:
    """Get the global context logger instance."""
    return context_logger


def get_performance_logger() -> PerformanceLogger:
    """Get the global performance logger instance."""
    return performance_logger


def get_llm_logger() -> LLMConversationLogger:
    """Get the global LLM conversation logger instance."""
    return llm_conversation_logger
