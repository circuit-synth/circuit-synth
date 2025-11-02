#!/usr/bin/env python3
"""
Automated test for 01_blank_circuit bidirectional test.

Tests that a blank circuit generates valid KiCad project with no components.

TODO: Enhance validation to check for more than just components:
- labels (should be none in blank circuit)
- images (should be none in blank circuit)
- text objects (function comments are allowed)
- wires (should be none in blank circuit)
- junctions (should be none in blank circuit)
- hierarchical labels (should be none in blank circuit)
- sheets (should be none in blank circuit)

This comprehensive validation exercises kicad-sch-api logic and ensures
blank truly means blank. Critical for the most important feature of circuit-synth.
"""
import shutil
import subprocess
from pathlib import Path

import pytest


def test_01_blank_circuit(request):
    """Test that a blank circuit generates valid empty schematic.

    This test validates:
    1. Circuit generation completes successfully
    2. KiCad project and schematic files are created
    3. Schematic contains no components (blank circuit)
    4. Text boxes (like function comments) are allowed

    Args:
        request: pytest fixture for accessing test config
    """

    # Setup paths
    test_dir = Path(__file__).parent
    output_dir = test_dir / "blank"

    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    # Clean any existing output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    try:
        # Run the circuit generation
        result = subprocess.run(
            ["uv", "run", "blank.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        # Assert generation succeeded
        assert result.returncode == 0, (
            f"blank.py failed with return code {result.returncode}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # Assert files were created
        assert (output_dir / "blank.kicad_pro").exists(), (
            "KiCad project file not created"
        )
        assert (output_dir / "blank.kicad_sch").exists(), (
            "KiCad schematic file not created"
        )

        # Use kicad-sch-api to parse and validate schematic
        try:
            from kicad_sch_api import Schematic
            sch = Schematic.load(str(output_dir / "blank.kicad_sch"))

            # Get all components in the schematic
            components = sch.components

            # Assert no components (blank circuit)
            # Note: Text boxes (like function comments) are expected and allowed
            assert len(components) == 0, (
                f"Expected no components in blank circuit, found {len(components)}: "
                f"{[c.reference for c in components]}"
            )

        except ImportError:
            pytest.skip("kicad-sch-api not available, skipping schematic validation")

    finally:
        # Cleanup (always runs, even on failure)
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
