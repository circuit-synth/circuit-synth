"""
AI Integration Module for Circuit-Synth

This module provides AI assistant integration tools including:
- Agent-based circuit design assistance (claude/)
- Real-time validation and feedback (validation/)
- Memory bank for session context preservation (memory_bank/)
- Component intelligence and search (component_info/)
- AI design bridge plugins (plugins/)

Supports various AI assistants including Claude Code, GitHub Copilot, Cursor, and others.
"""

# Core exports
from .validation import get_circuit_design_context, validate_and_improve_circuit

__all__ = ["validate_and_improve_circuit", "get_circuit_design_context"]
