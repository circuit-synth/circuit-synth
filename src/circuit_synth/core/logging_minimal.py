"""
Minimal logging replacement for circuit-synth

This provides drop-in replacements for the complex logging infrastructure
with simple implementations that maintain API compatibility.
"""

import logging
from contextlib import contextmanager
from typing import Any, Dict, Optional

# Create a simple logger
_base_logger = logging.getLogger("circuit_synth")
_base_logger.setLevel(logging.INFO)

# Add console handler if not already present
if not _base_logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s | %(levelname)8s | %(message)s")
    handler.setFormatter(formatter)
    _base_logger.addHandler(handler)


class SimpleContextLogger:
    """Simple replacement for context_logger"""

    def __init__(self):
        self.logger = _base_logger

    def info(self, message: str, **kwargs):
        self.logger.info(f"{message} {self._format_kwargs(kwargs)}")

    def debug(self, message: str, **kwargs):
        self.logger.debug(f"{message} {self._format_kwargs(kwargs)}")

    def warning(self, message: str, **kwargs):
        self.logger.warning(f"{message} {self._format_kwargs(kwargs)}")

    def error(self, message: str, **kwargs):
        self.logger.error(f"{message} {self._format_kwargs(kwargs)}")

    def _format_kwargs(self, kwargs: Dict[str, Any]) -> str:
        if not kwargs:
            return ""
        formatted = []
        for k, v in kwargs.items():
            if k not in ["component"]:  # Skip common metadata
                formatted.append(f"{k}={v}")
        return f"[{', '.join(formatted)}]" if formatted else ""


class SimplePerformanceLogger:
    """Simple replacement for performance_logger"""

    @contextmanager
    def timer(self, operation: str, **kwargs):
        import time

        start = time.perf_counter()
        timer_id = f"{operation}_{id(self)}"
        try:
            yield timer_id
        finally:
            duration = (time.perf_counter() - start) * 1000
            _base_logger.debug(f"Performance: {operation} took {duration:.2f}ms")


class SimpleUserContext:
    """Simple replacement for UserContext"""

    def __init__(self, user_id: str, session_id: str):
        self.user_id = user_id
        self.session_id = session_id

    def __enter__(self):
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        pass


# Create singleton instances
context_logger = SimpleContextLogger()
performance_logger = SimplePerformanceLogger()
UserContext = SimpleUserContext


# Additional compatibility functions
def get_current_context():
    """Simple replacement for get_current_context"""
    return {}


@contextmanager
def monitor_performance(operation: str, **kwargs):
    """Simple replacement for monitor_performance"""
    with performance_logger.timer(operation, **kwargs):
        yield


@contextmanager
def performance_context(operation: str, **kwargs):
    """Simple replacement for performance_context"""
    with performance_logger.timer(operation, **kwargs):
        yield
