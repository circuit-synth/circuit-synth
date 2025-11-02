#!/usr/bin/env python3
"""
Test 46: Empty Circuit - Edge Case Test

Validates that an empty circuit (no components) generates without errors.
"""

import pytest
import subprocess
import shutil
from pathlib import Path
from kicad_sch_api import Schematic


def test_46_empty_circuit(request):
    """Test empty circuit generation."""

    test_dir = Path(__file__).parent
    circuit_file = test_dir / "comprehensive_root.py"
    output_dir = test_dir / "comprehensive_root"
    root_schematic = output_dir / "comprehensive_root.kicad_sch"

    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # Generate empty circuit
        result = subprocess.run(
            ["uv", "run", str(circuit_file)],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, f"Empty circuit generation failed: {result.stderr}"
        assert root_schematic.exists(), "Schematic file not generated"

        # Load and verify
        root_sch = Schematic.load(str(root_schematic))
        components = [c for c in root_sch.components if not c.reference.startswith("#PWR")]
        assert len(components) == 0, "Expected 0 components in empty circuit"

        print("\n✅ Test 46 PASSED: Empty circuit generated successfully")
        print(f"   - No components ✓")
        print(f"   - Schematic file created ✓")

    finally:
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
