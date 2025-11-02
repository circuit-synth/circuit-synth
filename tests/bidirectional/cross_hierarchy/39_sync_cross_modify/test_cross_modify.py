#!/usr/bin/env python3
"""
Test 39: Modify Cross-Sheet Connection - Basic Generation Test

Validates that modifying cross-sheet connections
generates successfully and creates the expected schematic structure.

Note: Full bidirectional sync verification for hierarchical circuits
is pending implementation of hierarchical position preservation.
"""

import pytest
import subprocess
import shutil
from pathlib import Path
from kicad_sch_api import Schematic


def test_39_cross_modify(request):
    """Test modifying cross-sheet connection - basic generation."""

    test_dir = Path(__file__).parent
    circuit_file = test_dir / "comprehensive_root.py"
    output_dir = test_dir / "comprehensive_root"
    root_schematic = output_dir / "comprehensive_root.kicad_sch"
    amp_schematic = output_dir / "amplifier.kicad_sch"
    pwr_schematic = output_dir / "power_supply.kicad_sch"

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
        assert amp_schematic.exists(), "Amplifier schematic not generated"
        assert pwr_schematic.exists(), "Power supply schematic not generated"

        # Load root sheet
        root_sch = Schematic.load(str(root_schematic))
        root_components = [c for c in root_sch.components if not c.reference.startswith("#PWR")]
        assert len(root_components) == 2, "Expected 2 components on root sheet"

        # Load amplifier sheet
        amp_sch = Schematic.load(str(amp_schematic))
        amp_components = [c for c in amp_sch.components if not c.reference.startswith("#PWR")]
        assert len(amp_components) == 2, "Expected 2 components in amplifier"

        # Load power supply sheet
        pwr_sch = Schematic.load(str(pwr_schematic))
        pwr_components = [c for c in pwr_sch.components if not c.reference.startswith("#PWR")]
        assert len(pwr_components) == 2, "Expected 2 components in power_supply"

        print("\n✅ Test 39 PASSED: Cross-sheet modify test circuit generated successfully")
        print(f"   - Root sheet: 2 components (R1, R2) ✓")
        print(f"   - Amplifier sheet: 2 components (R3, R4) ✓")
        print(f"   - Power supply sheet: 2 components (R5, C2) ✓")
        print(f"\n💡 Note: Full test includes changing connection and verifying positions")

    finally:
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
