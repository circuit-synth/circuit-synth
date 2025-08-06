"""
Circuit-Synth Logging

Simple logging system for circuit-synth with minimal overhead.
Provides drop-in compatibility with the previous complex logging system.
"""

# Import from minimal logging implementation
from ..logging_minimal import (
    UserContext,
    context_logger,
    get_current_context,
    monitor_performance,
    performance_context,
    performance_logger,
)

__all__ = [
    "UserContext",
    "context_logger",
    "get_current_context",
    "monitor_performance",
    "performance_context",
    "performance_logger",
]
