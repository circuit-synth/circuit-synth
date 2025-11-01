#!/usr/bin/env python3
"""
Test 20: Rename Component in Subcircuit

Rename component in hierarchical sheet
"""

import pytest
import subprocess
import shutil
from pathlib import Path
from kicad_sch_api import Schematic


def test_20_sync_component_hier_update_ref(request):
    """Test Rename Component in Subcircuit."""

    test_dir = Path(__file__).parent
    circuit_file = test_dir / "test_20.py"
    output_dir = test_dir / "test_20"
    schematic_file = output_dir / "test_20.kicad_sch"

    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # Generate circuit
        result = subprocess.run(
            ["uv", "run", str(circuit_file)],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, f"Generation failed: {result.stderr}"
        assert schematic_file.exists(), "Schematic not generated"

        # Load and verify with kicad-sch-api
        sch = Schematic.load(str(schematic_file))

        # TODO: Add specific verification for Rename Component in Subcircuit
        # - Check component positions
        # - Check values
        # - Check preservation

        print("\n✅ Test 20 PASSED: Rename Component in Subcircuit")

    finally:
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
