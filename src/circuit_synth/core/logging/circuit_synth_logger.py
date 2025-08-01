"""
Core logging module for Circuit Synth.
Provides session-aware logging with microsecond timestamps and user-based directory structure.
"""

import json
import logging
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from .unified_logger import context_logger


class CircuitSynthLogger:
    """
    Main logger class for Circuit Synth that handles session tracking,
    event logging, and directory structure management.
    """

    def __init__(self, username: str, session_id: Optional[str] = None):
        """
        Initialize the logger for a specific user session.

        Args:
            username: The username for this session
            session_id: Optional session ID. If not provided, one will be generated.
        """
        self.username = username
        self.session_id = session_id or self._generate_session_id()
        self.chat_id = None
        self.loggers = {}
        self._setup_loggers()

    def _generate_session_id(self) -> str:
        """Generate a unique session ID with timestamp."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        unique_id = str(uuid.uuid4())[:8]
        return f"{self.username}_{timestamp}_{unique_id}"

    def _setup_loggers(self):
        """Set up all the different loggers with appropriate handlers."""
        # Create base log directory structure in user's home directory to avoid polluting projects
        base_log_dir = Path.home() / ".circuit-synth" / "logs"

        # User-specific logs
        user_log_dir = (
            base_log_dir / "users" / self.username / datetime.now().strftime("%Y-%m-%d")
        )
        user_log_dir.mkdir(parents=True, exist_ok=True)

        # System logs
        system_log_dir = base_log_dir / "system" / datetime.now().strftime("%Y-%m-%d")
        system_log_dir.mkdir(parents=True, exist_ok=True)

        # Performance logs
        perf_log_dir = (
            base_log_dir / "performance" / datetime.now().strftime("%Y-%m-%d")
        )
        perf_log_dir.mkdir(parents=True, exist_ok=True)

        # Master logs
        master_log_dir = base_log_dir / "master" / datetime.now().strftime("%Y-%m-%d")
        master_log_dir.mkdir(parents=True, exist_ok=True)

        # Create formatters with microsecond precision
        detailed_formatter = logging.Formatter(
            "%(asctime)s.%(msecs)03d %(message)s", datefmt="%Y-%m-%dT%H:%M:%S"
        )

        # Custom filter to add microseconds
        class MicrosecondFilter(logging.Filter):
            def filter(self, record):
                # Add microseconds to the timestamp
                record.asctime = datetime.now().strftime("%Y-%m-%dT%H:%M:%S.%f")[:-3]
                return True

        microsecond_filter = MicrosecondFilter()

        # Session logger (user-specific)
        session_log_path = (
            user_log_dir / f"session_{self.session_id.split('_', 1)[1]}.log"
        )
        self._create_logger(
            "session", session_log_path, detailed_formatter, microsecond_filter
        )

        # Daily summary logger
        daily_log_path = user_log_dir / "daily_summary.log"
        self._create_logger(
            "daily", daily_log_path, detailed_formatter, microsecond_filter
        )

        # System loggers
        dashboard_log_path = system_log_dir / "dashboard.log"
        self._create_logger(
            "dashboard", dashboard_log_path, detailed_formatter, microsecond_filter
        )

        orchestrator_log_path = system_log_dir / "orchestrator.log"
        self._create_logger(
            "orchestrator",
            orchestrator_log_path,
            detailed_formatter,
            microsecond_filter,
        )

        llm_log_path = system_log_dir / "llm_interactions.log"
        self._create_logger("llm", llm_log_path, detailed_formatter, microsecond_filter)

        error_log_path = system_log_dir / "errors.log"
        self._create_logger(
            "errors", error_log_path, detailed_formatter, microsecond_filter
        )

        # Performance logger
        metrics_log_path = perf_log_dir / "metrics.log"
        self._create_logger(
            "performance", metrics_log_path, detailed_formatter, microsecond_filter
        )

        # Master logger (everything)
        master_log_path = master_log_dir / "circuit_synth_all.log"
        self._create_logger(
            "master", master_log_path, detailed_formatter, microsecond_filter
        )

        # Log session start
        self.log_session_start()

    def _create_logger(
        self,
        name: str,
        log_path: Path,
        formatter: logging.Formatter,
        filter: logging.Filter,
    ):
        """Create and configure a logger with the given parameters."""
        logger = logging.getLogger(f"circuit_synth.{name}.{self.session_id}")
        logger.setLevel(logging.DEBUG)

        # Remove existing handlers to avoid duplicates
        logger.handlers = []

        # File handler
        file_handler = logging.FileHandler(log_path, encoding="utf-8")
        file_handler.setFormatter(formatter)
        file_handler.addFilter(filter)
        logger.addHandler(file_handler)

        # Store logger reference
        self.loggers[name] = logger

    def set_chat_id(self, chat_id: str):
        """Set the current chat ID for this session."""
        self.chat_id = chat_id
        self.log_event("chat_session_start", chat_id=chat_id)

    def log_event(self, event_type: str, **kwargs):
        """
        Log a generic event with timestamp and session context.

        Args:
            event_type: Type of event being logged
            **kwargs: Additional event data
        """
        event = self._create_event(event_type, **kwargs)
        event_json = json.dumps(event, default=str)

        # Log to appropriate loggers based on event type
        if event_type.startswith("dash_"):
            self.loggers["dashboard"].info(event_json)
        elif event_type.startswith("llm_"):
            self.loggers["llm"].info(event_json)
        elif event_type.startswith("performance_"):
            self.loggers["performance"].info(event_json)
        elif event_type == "error":
            self.loggers["errors"].error(event_json)

        # Always log to session, daily, and master
        self.loggers["session"].info(event_json)
        self.loggers["daily"].info(event_json)
        self.loggers["master"].info(event_json)

    def log_dash_callback(
        self,
        callback_id: str,
        action: str,
        duration_ms: float,
        input_state: Dict[str, Any],
        output_state: Dict[str, Any],
    ):
        """Log a Plotly Dash callback execution."""
        self.log_event(
            "dash_callback",
            callback_id=callback_id,
            action=action,
            duration_ms=duration_ms,
            input_state=input_state,
            output_state=output_state,
        )

    def log_user_action(self, action: str, details: Dict[str, Any]):
        """Log a user action."""
        self.log_event("user_action", action=action, details=details)

    def log_llm_request(
        self,
        model: str,
        prompt_tokens: int,
        max_tokens: int,
        temperature: float,
        request_id: str,
        prompt_preview: str,
    ):
        """Log an LLM API request."""
        self.log_event(
            "llm_request",
            model=model,
            prompt_tokens=prompt_tokens,
            max_tokens=max_tokens,
            temperature=temperature,
            request_id=request_id,
            prompt_preview=(
                prompt_preview[:200] + "..."
                if len(prompt_preview) > 200
                else prompt_preview
            ),
        )

    def log_llm_response(
        self,
        model: str,
        request_id: str,
        completion_tokens: int,
        total_tokens: int,
        duration_ms: float,
        cost_usd: float,
        response_preview: str,
    ):
        """Log an LLM API response."""
        self.log_event(
            "llm_response",
            model=model,
            request_id=request_id,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            duration_ms=duration_ms,
            cost_usd=cost_usd,
            response_preview=(
                response_preview[:200] + "..."
                if len(response_preview) > 200
                else response_preview
            ),
        )

    def log_file_operation(
        self,
        operation: str,
        file_path: str,
        file_size: Optional[int] = None,
        success: bool = True,
    ):
        """Log a file operation."""
        self.log_event(
            "file_operation",
            operation=operation,
            file_path=file_path,
            file_size=file_size,
            success=success,
        )

    def log_circuit_generation(
        self, stage: str, circuit_type: str, components: list, duration_ms: float
    ):
        """Log a circuit generation event."""
        self.log_event(
            "circuit_generation",
            stage=stage,
            circuit_type=circuit_type,
            components=components,
            duration_ms=duration_ms,
        )

    def log_performance_metric(
        self, metric: str, value: float, unit: str, process: str
    ):
        """Log a performance metric."""
        self.log_event(
            "performance_metric", metric=metric, value=value, unit=unit, process=process
        )

    def log_error(
        self, error_type: str, error_message: str, traceback: Optional[str] = None
    ):
        """Log an error."""
        context_logger.error(
            f"{error_type}: {error_message}",
            component="CIRCUIT_SYNTH_LOGGER",
            error_type=error_type,
            traceback=traceback,
            username=self.username,
            session_id=self.session_id,
        )

    def log_session_start(self):
        """Log the start of a user session."""
        self.log_event(
            "session_start", username=self.username, session_id=self.session_id
        )

    def log_session_end(self):
        """Log the end of a user session."""
        self.log_event(
            "session_end", username=self.username, session_id=self.session_id
        )

    def _create_event(self, event_type: str, **kwargs) -> Dict[str, Any]:
        """Create a standardized event dictionary."""
        event = {
            "timestamp": datetime.now().isoformat(),
            "session_id": self.session_id,
            "event_type": event_type,
        }

        if self.chat_id:
            event["chat_id"] = self.chat_id

        event.update(kwargs)
        return event

    def __enter__(self):
        """Context manager entry."""
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - log session end."""
        self.log_session_end()
        # Close all handlers
        for logger in self.loggers.values():
            for handler in logger.handlers:
                handler.close()
