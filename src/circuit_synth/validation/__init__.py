"""
Simple circuit validation for Claude Code integration.

Provides two main functions:
- validate_and_improve_circuit: Validate and auto-fix circuit code
- get_circuit_design_context: Get comprehensive design context
"""

from .simple_validator import get_circuit_design_context, validate_and_improve_circuit

__all__ = ["validate_and_improve_circuit", "get_circuit_design_context"]
