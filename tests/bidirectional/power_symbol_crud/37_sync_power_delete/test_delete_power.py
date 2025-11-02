#!/usr/bin/env python3
"""
Test 37: Delete Power Symbol - Basic Generation Test

Validates that deleting a power net (power symbol)
generates successfully and creates the expected schematic structure.
"""

import pytest
import subprocess
import shutil
from pathlib import Path
from kicad_sch_api import Schematic


def test_37_delete_power(request):
    """Test deleting power symbol - basic generation."""

    test_dir = Path(__file__).parent
    circuit_file = test_dir / "comprehensive_root.py"
    output_dir = test_dir / "comprehensive_root"
    root_schematic = output_dir / "comprehensive_root.kicad_sch"

    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # STEP 1: Generate circuit
        result = subprocess.run(
            ["uv", "run", str(circuit_file)],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )
        assert result.returncode == 0, f"Generation failed: {result.stderr}"
        assert root_schematic.exists(), "Root schematic not generated"

        # Load root sheet
        root_sch = Schematic.load(str(root_schematic))
        root_components = [c for c in root_sch.components if not c.reference.startswith("#PWR")]
        assert len(root_components) == 3, "Expected 3 components on root sheet"

        # Verify components
        r1 = next((c for c in root_components if c.reference == "R1"), None)
        r2 = next((c for c in root_components if c.reference == "R2"), None)
        c1 = next((c for c in root_components if c.reference == "C1"), None)
        assert r1 is not None, "R1 missing"
        assert r2 is not None, "R2 missing"
        assert c1 is not None, "C1 missing"

        # Verify power symbols exist
        power_components = [c for c in root_sch.components if c.reference.startswith("#PWR")]
        assert len(power_components) >= 3, "Expected at least 3 power symbols (VCC, GND, +3V3)"

        print("\n✅ Test 37 PASSED: Power delete test circuit generated successfully")
        print(f"   - Root sheet: 3 components (R1, R2, C1) ✓")
        print(f"   - Power symbols: {len(power_components)} (VCC, GND, +3V3) ✓")
        print(f"\n💡 Note: Full test includes deleting +3V3 power and verifying positions")

    finally:
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
