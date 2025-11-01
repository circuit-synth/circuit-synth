"""
Test suite for custom component properties (Issue #409).

Tests bidirectional flow of custom properties:
- Python → JSON → KiCad schematic
- KiCad schematic → Python
- Round-trip preservation
- Synchronizer integration
- Edge cases and validation
"""
