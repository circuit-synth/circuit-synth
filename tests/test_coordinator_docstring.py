#!/usr/bin/env python3
"""Test that coordinator.py has the correct docstring"""

import sys
from pathlib import Path

# Add adws to path
REPO_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(REPO_ROOT / "adws"))

import coordinator


def test_coordinator_module_docstring():
    """Test that coordinator.py has the expected module-level docstring"""
    expected_docstring = """
Circuit-Synth Autonomous Coordinator

TAC-8 inspired system for autonomous issue resolution.
See adws/README.md for documentation.
"""

    actual_docstring = coordinator.__doc__

    # Normalize whitespace for comparison
    assert actual_docstring is not None, "coordinator.py must have a module docstring"

    # Strip leading/trailing whitespace for comparison
    expected_clean = expected_docstring.strip()
    actual_clean = actual_docstring.strip()

    assert actual_clean == expected_clean, (
        f"Docstring mismatch.\n"
        f"Expected:\n{expected_clean}\n\n"
        f"Actual:\n{actual_clean}"
    )


if __name__ == "__main__":
    test_coordinator_module_docstring()
    print("✓ Coordinator docstring test passed")
