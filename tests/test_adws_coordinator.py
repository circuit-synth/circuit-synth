#!/usr/bin/env python3
"""Tests for adws/coordinator.py module"""

import ast
from pathlib import Path


def test_coordinator_module_has_docstring():
    """Verify that coordinator.py has a module-level docstring"""
    coordinator_path = Path(__file__).parent.parent / "adws" / "coordinator.py"
    assert coordinator_path.exists(), f"coordinator.py not found at {coordinator_path}"

    # Parse the file to extract docstring
    with open(coordinator_path, 'r') as f:
        tree = ast.parse(f.read())

    docstring = ast.get_docstring(tree)
    assert docstring is not None, "coordinator.py should have a module-level docstring"
    assert len(docstring.strip()) > 0, "Docstring should not be empty"


def test_coordinator_docstring_content():
    """Verify that the docstring contains expected content"""
    coordinator_path = Path(__file__).parent.parent / "adws" / "coordinator.py"

    # Parse the file to extract docstring
    with open(coordinator_path, 'r') as f:
        tree = ast.parse(f.read())

    docstring = ast.get_docstring(tree)
    assert docstring is not None, "coordinator.py should have a docstring"

    assert "Circuit-Synth Autonomous Coordinator" in docstring, \
        "Docstring should mention 'Circuit-Synth Autonomous Coordinator'"
    assert "TAC-8" in docstring, \
        "Docstring should mention 'TAC-8'"
    assert "adws/README.md" in docstring, \
        "Docstring should reference 'adws/README.md'"


if __name__ == "__main__":
    # Allow running directly for quick testing
    test_coordinator_module_has_docstring()
    test_coordinator_docstring_content()
    print("✅ All tests passed!")
