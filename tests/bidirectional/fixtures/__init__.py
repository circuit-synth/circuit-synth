"""Bidirectional test fixtures and verification helpers.

This module provides:
1. Comprehensive fixture circuits for testing CRUD operations
2. Verification helper functions using kicad-sch-api
3. Utilities for preservation testing
"""

from .helpers import (
    verify_components,
    verify_power_symbols,
    verify_labels,
    verify_component_properties,
    verify_component_unchanged,
    verify_sync_log,
    verify_comprehensive_fixture_state,
    print_verification_summary,
)

__all__ = [
    "verify_components",
    "verify_power_symbols",
    "verify_labels",
    "verify_component_properties",
    "verify_component_unchanged",
    "verify_sync_log",
    "verify_comprehensive_fixture_state",
    "print_verification_summary",
]
