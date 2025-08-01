"""
Database-backed logger for Circuit Synth.
Provides dual logging to both files and SQLite database for enhanced querying.
"""

import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, Optional

from .circuit_synth_logger import CircuitSynthLogger
from .database import LogDatabase


class DatabaseLogger(CircuitSynthLogger):
    """
    Extended logger that writes to both files and database.
    Provides enhanced search and analysis capabilities.
    """

    def __init__(
        self,
        username: str,
        session_id: Optional[str] = None,
        db_path: Optional[Path] = None,
    ):
        """
        Initialize database-backed logger.

        Args:
            username: The username for this session
            session_id: Optional session ID
            db_path: Optional path to database file
        """
        # Initialize instance variables before calling super().__init__
        self.db = LogDatabase(db_path)
        self.line_counters = {}  # Track line numbers for each log file

        # Now call parent init which will call log_event
        super().__init__(username, session_id)

        # Create session in database
        self.db.create_user_session(
            session_id=self.session_id,
            username=username,
            metadata={"logger_version": "2.0", "dual_logging": True},
        )

    def log_event(self, event_type: str, **kwargs):
        """
        Override to also log to database.

        Args:
            event_type: Type of event being logged
            **kwargs: Additional event data
        """
        # First, log to files as usual
        super().log_event(event_type, **kwargs)

        # Then, add to database index
        timestamp = datetime.now().isoformat()

        # Determine which log file this event goes to
        log_file = self._get_log_file_for_event(event_type)
        line_number = self._get_next_line_number(log_file)

        # Create event summary
        summary = self._create_event_summary(event_type, kwargs)

        # Add to database index
        self.db.add_event_to_index(
            timestamp=timestamp,
            session_id=self.session_id,
            event_type=event_type,
            log_file=str(log_file),
            line_number=line_number,
            chat_id=self.chat_id,
            summary=summary,
            metadata=kwargs,
        )

        # Handle specific event types
        self._handle_special_events(event_type, kwargs)

    def set_chat_id(self, chat_id: str):
        """Override to also create chat session in database."""
        super().set_chat_id(chat_id)

        # Create chat session in database
        self.db.create_chat_session(
            chat_id=chat_id,
            session_id=self.session_id,
            model_used="",  # Will be updated when model is selected
        )

    def log_llm_request(
        self,
        model: str,
        prompt_tokens: int,
        max_tokens: int,
        temperature: float,
        request_id: str,
        prompt_preview: str,
    ):
        """Override to track LLM usage in database."""
        super().log_llm_request(
            model, prompt_tokens, max_tokens, temperature, request_id, prompt_preview
        )

        # Store initial request info (will be updated with response)
        self.db.add_llm_usage(
            request_id=request_id,
            session_id=self.session_id,
            chat_id=self.chat_id,
            model=model,
            provider=self._extract_provider(model),
            prompt_tokens=prompt_tokens,
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
        """Override to update LLM usage in database."""
        super().log_llm_response(
            model,
            request_id,
            completion_tokens,
            total_tokens,
            duration_ms,
            cost_usd,
            response_preview,
        )

        # Update the existing record with response info
        self.db.update_llm_usage(
            request_id=request_id,
            completion_tokens=completion_tokens,
            total_tokens=total_tokens,
            cost_usd=cost_usd,
            duration_ms=duration_ms,
            success=True,
        )

    def log_performance_metric(
        self, metric: str, value: float, unit: str, process: str
    ):
        """Override to store performance metrics in database."""
        super().log_performance_metric(metric, value, unit, process)

        self.db.add_performance_metric(
            session_id=self.session_id,
            metric_type="system",
            metric_name=f"{process}.{metric}",
            value=value,
            unit=unit,
        )

    def log_session_end(self):
        """Override to update session end time in database."""
        super().log_session_end()

        # Update session with end time and event count
        event_count = sum(self.line_counters.values())
        self.db.update_user_session(
            session_id=self.session_id,
            end_time=datetime.now(),
            total_events=event_count,
        )

    def search_events(self, **criteria) -> list:
        """
        Search for events using database index.

        Args:
            **criteria: Search criteria (event_type, session_id, start_time, end_time)

        Returns:
            List of matching events
        """
        return self.db.search_events(**criteria)

    def get_session_summary(self) -> Dict[str, Any]:
        """Get comprehensive summary of current session."""
        return self.db.get_session_summary(self.session_id)

    def _get_log_file_for_event(self, event_type: str) -> Path:
        """Determine which log file an event type goes to."""
        base_log_dir = Path.home() / ".circuit-synth" / "logs"
        date_str = datetime.now().strftime("%Y-%m-%d")

        if event_type.startswith("dash_"):
            return base_log_dir / "system" / date_str / "dashboard.log"
        elif event_type.startswith("llm_"):
            return base_log_dir / "system" / date_str / "llm_interactions.log"
        elif event_type.startswith("performance_"):
            return base_log_dir / "performance" / date_str / "metrics.log"
        elif event_type == "error":
            return base_log_dir / "system" / date_str / "errors.log"
        else:
            # Default to session log
            user_log_dir = base_log_dir / "users" / self.username / date_str
            return user_log_dir / f"session_{self.session_id.split('_', 1)[1]}.log"

    def _get_next_line_number(self, log_file: Path) -> int:
        """Get the next line number for a log file."""
        file_key = str(log_file)
        if file_key not in self.line_counters:
            self.line_counters[file_key] = 0

        self.line_counters[file_key] += 1
        return self.line_counters[file_key]

    def _create_event_summary(self, event_type: str, data: Dict[str, Any]) -> str:
        """Create a human-readable summary of an event."""
        if event_type == "dash_callback":
            return f"Callback: {data.get('callback_id', 'unknown')}"
        elif event_type == "user_action":
            return f"User: {data.get('action', 'unknown')}"
        elif event_type == "llm_request":
            return f"LLM Request: {data.get('model', 'unknown')}"
        elif event_type == "llm_response":
            return f"LLM Response: {data.get('total_tokens', 0)} tokens"
        elif event_type == "file_operation":
            return f"File: {data.get('operation', 'unknown')} - {data.get('file_path', 'unknown')}"
        elif event_type == "circuit_generation":
            return f"Circuit: {data.get('stage', 'unknown')} - {data.get('circuit_type', 'unknown')}"
        elif event_type == "performance_metric":
            return f"Metric: {data.get('metric', 'unknown')} = {data.get('value', 0)} {data.get('unit', '')}"
        elif event_type == "error":
            return f"Error: {data.get('error_type', 'unknown')}"
        else:
            return event_type.replace("_", " ").title()

    def _extract_provider(self, model: str) -> str:
        """Extract provider from model name."""
        if "gpt" in model.lower():
            return "openai"
        elif "claude" in model.lower():
            return "anthropic"
        elif "gemini" in model.lower():
            return "google"
        elif "llama" in model.lower():
            return "meta"
        else:
            return "unknown"

    def _handle_special_events(self, event_type: str, data: Dict[str, Any]):
        """Handle special event types that need additional database updates."""
        if event_type == "chat_session_start" and "model" in data:
            # Update chat session with model info
            self.db.update_chat_session(chat_id=self.chat_id, message_count=0)
        elif event_type == "llm_conversation_turn":
            # Increment message count
            # In a real implementation, we'd track this properly
            pass

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit - close database connection."""
        super().__exit__(exc_type, exc_val, exc_tb)
        self.db.close()


class DatabaseLoggerFactory:
    """Factory for creating database-backed loggers."""

    _instances = {}

    @classmethod
    def get_logger(
        cls,
        username: str,
        session_id: Optional[str] = None,
        db_path: Optional[Path] = None,
    ) -> DatabaseLogger:
        """
        Get or create a database logger instance.

        Args:
            username: Username for the logger
            session_id: Optional session ID
            db_path: Optional database path

        Returns:
            DatabaseLogger instance
        """
        key = f"{username}:{session_id or 'default'}"

        if key not in cls._instances:
            cls._instances[key] = DatabaseLogger(username, session_id, db_path)

        return cls._instances[key]

    @classmethod
    def close_all(cls):
        """Close all logger instances."""
        for logger in cls._instances.values():
            logger.db.close()
        cls._instances.clear()
