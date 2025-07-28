"""
Context Manager for Multi-User Thread-Safe Logging
=================================================

Provides thread-safe context management for multi-user logging using Python's
contextvars. This module handles user session tracking, request correlation,
and chat context management across concurrent operations.
"""

import threading
import time
import uuid
from collections import defaultdict
from contextvars import ContextVar, Token
from dataclasses import asdict, dataclass
from datetime import datetime
from typing import Any, Dict, List, Optional

# Context variables for user tracking (automatically thread-safe)
current_user: ContextVar[Optional[str]] = ContextVar("current_user", default=None)
current_session: ContextVar[Optional[str]] = ContextVar("current_session", default=None)
current_request: ContextVar[Optional[str]] = ContextVar("current_request", default=None)
current_chat: ContextVar[Optional[str]] = ContextVar("current_chat", default=None)


@dataclass
class SessionInfo:
    """Information about a user session."""

    session_id: str
    user_id: str
    start_time: datetime
    last_activity: datetime
    request_count: int = 0
    active_requests: List[str] = None

    def __post_init__(self):
        if self.active_requests is None:
            self.active_requests = []


class UserContext:
    """
    Manages user context for logging isolation using contextvars.

    This class provides a context manager that sets user, session, and other
    contextual information that will be automatically included in all log
    messages within the context.

    Example:
        with UserContext("john_doe", "session_123"):
            logger.info("This will include user and session info")
    """

    def __init__(self, user_id: str, session_id: Optional[str] = None):
        self.user_id = user_id
        self.session_id = session_id or self._generate_session_id(user_id)
        self.request_id = None
        self.chat_id = None
        self._tokens: Dict[str, Token] = {}

    def _generate_session_id(self, user_id: str) -> str:
        """Generate a unique session ID."""
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        return f"{user_id}_{timestamp}_{uuid.uuid4().hex[:8]}"

    def __enter__(self):
        """Enter context and set context variables."""
        self._tokens["user"] = current_user.set(self.user_id)
        self._tokens["session"] = current_session.set(self.session_id)

        # Register session with session manager
        SessionManager.get_instance().register_session(self.user_id, self.session_id)

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit context and reset context variables."""
        # Reset context variables
        for token in self._tokens.values():
            if hasattr(token, "var"):
                token.var.reset(token)

        # Update session activity
        SessionManager.get_instance().update_session_activity(self.session_id)

    def set_request(self, request_id: Optional[str] = None) -> str:
        """Set request ID for current context."""
        if request_id is None:
            request_id = f"req_{uuid.uuid4().hex[:12]}"

        self.request_id = request_id
        token = current_request.set(request_id)
        self._tokens["request"] = token

        # Register request with session
        SessionManager.get_instance().add_request_to_session(
            self.session_id, request_id
        )

        return request_id

    def set_chat(self, chat_id: Optional[str] = None) -> str:
        """Set chat ID for current context."""
        if chat_id is None:
            chat_id = f"chat_{uuid.uuid4().hex[:12]}"

        self.chat_id = chat_id
        token = current_chat.set(chat_id)
        self._tokens["chat"] = token

        return chat_id

    def get_context_info(self) -> Dict[str, Any]:
        """Get current context information."""
        return {
            "user_id": self.user_id,
            "session_id": self.session_id,
            "request_id": self.request_id,
            "chat_id": self.chat_id,
            "timestamp": datetime.now().astimezone().isoformat(),
        }


class SessionManager:
    """
    Manages user sessions and provides session tracking capabilities.

    This is a singleton class that tracks active sessions, manages session
    timeouts, and provides session statistics.
    """

    _instance = None
    _lock = threading.Lock()

    def __init__(self):
        self.sessions: Dict[str, SessionInfo] = {}
        self.user_sessions: Dict[str, List[str]] = defaultdict(list)
        self._cleanup_lock = threading.Lock()
        self._last_cleanup = time.time()
        self._cleanup_interval = 3600  # 1 hour

    @classmethod
    def get_instance(cls):
        """Get singleton instance of SessionManager."""
        if cls._instance is None:
            with cls._lock:
                if cls._instance is None:
                    cls._instance = cls()
        return cls._instance

    def register_session(self, user_id: str, session_id: str) -> None:
        """Register a new session or update existing one."""
        now = datetime.now().astimezone()

        with self._lock:
            if session_id not in self.sessions:
                session_info = SessionInfo(
                    session_id=session_id,
                    user_id=user_id,
                    start_time=now,
                    last_activity=now,
                )
                self.sessions[session_id] = session_info
                self.user_sessions[user_id].append(session_id)
            else:
                # Update existing session
                self.sessions[session_id].last_activity = now

        # Periodic cleanup
        self._maybe_cleanup_sessions()

    def update_session_activity(self, session_id: str) -> None:
        """Update last activity time for a session."""
        with self._lock:
            if session_id in self.sessions:
                self.sessions[session_id].last_activity = datetime.utcnow()

    def add_request_to_session(self, session_id: str, request_id: str) -> None:
        """Add a request to a session."""
        with self._lock:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                session.request_count += 1
                session.active_requests.append(request_id)
                session.last_activity = datetime.utcnow()

    def remove_request_from_session(self, session_id: str, request_id: str) -> None:
        """Remove a request from a session."""
        with self._lock:
            if session_id in self.sessions:
                session = self.sessions[session_id]
                if request_id in session.active_requests:
                    session.active_requests.remove(request_id)

    def get_session_info(self, session_id: str) -> Optional[SessionInfo]:
        """Get information about a specific session."""
        with self._lock:
            return self.sessions.get(session_id)

    def get_user_sessions(self, user_id: str) -> List[SessionInfo]:
        """Get all sessions for a specific user."""
        with self._lock:
            session_ids = self.user_sessions.get(user_id, [])
            return [self.sessions[sid] for sid in session_ids if sid in self.sessions]

    def get_active_sessions(self, timeout_hours: int = 24) -> List[SessionInfo]:
        """Get all active sessions (not timed out)."""
        cutoff_time = datetime.utcnow() - timedelta(hours=timeout_hours)

        with self._lock:
            return [
                session
                for session in self.sessions.values()
                if session.last_activity > cutoff_time
            ]

    def get_session_stats(self) -> Dict[str, Any]:
        """Get overall session statistics."""
        with self._lock:
            total_sessions = len(self.sessions)
            active_sessions = len(self.get_active_sessions())
            unique_users = len(self.user_sessions)
            total_requests = sum(
                session.request_count for session in self.sessions.values()
            )

            return {
                "total_sessions": total_sessions,
                "active_sessions": active_sessions,
                "unique_users": unique_users,
                "total_requests": total_requests,
                "average_requests_per_session": total_requests / max(1, total_sessions),
            }

    def cleanup_expired_sessions(self, timeout_hours: int = 24) -> int:
        """Clean up expired sessions and return count of removed sessions."""
        cutoff_time = datetime.utcnow() - timedelta(hours=timeout_hours)
        removed_count = 0

        with self._lock:
            expired_sessions = [
                session_id
                for session_id, session in self.sessions.items()
                if session.last_activity < cutoff_time
            ]

            for session_id in expired_sessions:
                session = self.sessions[session_id]
                user_id = session.user_id

                # Remove from sessions
                del self.sessions[session_id]

                # Remove from user sessions
                if user_id in self.user_sessions:
                    if session_id in self.user_sessions[user_id]:
                        self.user_sessions[user_id].remove(session_id)

                    # Clean up empty user session lists
                    if not self.user_sessions[user_id]:
                        del self.user_sessions[user_id]

                removed_count += 1

        return removed_count

    def _maybe_cleanup_sessions(self) -> None:
        """Perform cleanup if enough time has passed."""
        current_time = time.time()

        if current_time - self._last_cleanup > self._cleanup_interval:
            with self._cleanup_lock:
                if current_time - self._last_cleanup > self._cleanup_interval:
                    self.cleanup_expired_sessions()
                    self._last_cleanup = current_time


class RequestContext:
    """
    Context manager for individual requests within a user session.

    This provides finer-grained context management for individual operations
    or requests within a user session.

    Example:
        with UserContext("john_doe"):
            with RequestContext("circuit_generation"):
                logger.info("Starting circuit generation")
                # ... circuit generation code ...
                logger.info("Circuit generation completed")
    """

    def __init__(self, operation_name: str, request_id: Optional[str] = None):
        self.operation_name = operation_name
        self.request_id = request_id or f"{operation_name}_{uuid.uuid4().hex[:8]}"
        self.start_time = None
        self._token = None

    def __enter__(self):
        """Enter request context."""
        self.start_time = datetime.utcnow()
        self._token = current_request.set(self.request_id)

        # Add to session if we're in a session context
        session_id = current_session.get()
        if session_id:
            SessionManager.get_instance().add_request_to_session(
                session_id, self.request_id
            )

        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        """Exit request context."""
        # Reset context variable
        if self._token:
            current_request.reset(self._token)

        # Remove from session
        session_id = current_session.get()
        if session_id:
            SessionManager.get_instance().remove_request_from_session(
                session_id, self.request_id
            )

        # Calculate duration
        if self.start_time:
            duration = (datetime.utcnow() - self.start_time).total_seconds()
            # Could log request completion here if needed

    def get_duration_ms(self) -> float:
        """Get current request duration in milliseconds."""
        if self.start_time:
            return (datetime.utcnow() - self.start_time).total_seconds() * 1000
        return 0.0


def get_current_context() -> Dict[str, Any]:
    """Get current context information from all context variables."""
    return {
        "user": current_user.get(),
        "session": current_session.get(),
        "request_id": current_request.get(),
        "chat_id": current_chat.get(),
        "timestamp": datetime.utcnow().isoformat(),
    }


def get_context_extras(**additional_extras) -> Dict[str, Any]:
    """
    Get context information formatted for logging extras.

    This function extracts all current context information and formats it
    for use with loguru's bind() method.
    """
    context = get_current_context()

    # Format for logging
    extras = {
        "user": context["user"] or "system",
        "session": context["session"] or "none",
        "request_id": context["request_id"] or "",
        "chat_id": context["chat_id"] or "",
        "timestamp": context["timestamp"],
        **additional_extras,
    }

    return extras


# Convenience functions for common patterns
def with_user_context(user_id: str, session_id: Optional[str] = None):
    """Decorator to run a function with user context."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            with UserContext(user_id, session_id):
                return func(*args, **kwargs)

        return wrapper

    return decorator


def with_request_context(operation_name: str):
    """Decorator to run a function with request context."""

    def decorator(func):
        def wrapper(*args, **kwargs):
            with RequestContext(operation_name):
                return func(*args, **kwargs)

        return wrapper

    return decorator
