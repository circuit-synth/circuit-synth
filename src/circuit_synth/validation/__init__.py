"""
Real-time Circuit Design Validation

Provides validation functions called by Claude Code hooks for
immediate feedback on circuit design quality and correctness.
"""

from .real_time_check import validate_circuit_file

__all__ = ["validate_circuit_file"]
