"""Simple logger for the open source circuit-synth package."""

import logging
import os
from typing import Any, Dict

# Create a simple logger for the circuit-synth package
logger = logging.getLogger("circuit_synth")

# Set default log level based on environment variable
# Users can set CIRCUIT_SYNTH_LOG_LEVEL=INFO for verbose logs
default_level = os.environ.get("CIRCUIT_SYNTH_LOG_LEVEL", "WARNING")
try:
    logger.setLevel(getattr(logging, default_level.upper()))
except AttributeError:
    logger.setLevel(logging.WARNING)


class ContextLogger:
    """Simple context logger that wraps standard logging."""

    def __init__(self, name: str = "circuit_synth"):
        self.logger = logging.getLogger(name)

    def debug(self, message: str, **kwargs: Any) -> None:
        """Log debug message with optional context."""
        context = " ".join(f"{k}={v}" for k, v in kwargs.items())
        if context:
            self.logger.debug(f"{message} [{context}]")
        else:
            self.logger.debug(message)

    def info(self, message: str, **kwargs: Any) -> None:
        """Log info message with optional context."""
        context = " ".join(f"{k}={v}" for k, v in kwargs.items())
        if context:
            self.logger.info(f"{message} [{context}]")
        else:
            self.logger.info(message)

    def warning(self, message: str, **kwargs: Any) -> None:
        """Log warning message with optional context."""
        context = " ".join(f"{k}={v}" for k, v in kwargs.items())
        if context:
            self.logger.warning(f"{message} [{context}]")
        else:
            self.logger.warning(message)

    def error(self, message: str, **kwargs: Any) -> None:
        """Log error message with optional context."""
        context = " ".join(f"{k}={v}" for k, v in kwargs.items())
        if context:
            self.logger.error(f"{message} [{context}]")
        else:
            self.logger.error(message)


# Global context logger instance
context_logger = ContextLogger()

# For compatibility with the generation logger
generation_logger = logger
performance_logger = logger


class GenerationStage:
    """Placeholder for generation stages."""

    pass


def log_netlist_analytics(*args, **kwargs):
    """Placeholder for netlist analytics logging."""
    pass
