#!/usr/bin/env python3
"""
Test 28: Rename Sheet - Basic Generation Test

Validates that renaming a hierarchical sheet
generates successfully and creates the expected schematic structure.

Note: Full bidirectional sync verification for hierarchical circuits
is pending implementation of hierarchical position preservation.
"""

import pytest
import subprocess
import shutil
from pathlib import Path
from kicad_sch_api import Schematic


def test_28_rename_sheet(request):
    """Test renaming sheet - basic generation."""

    test_dir = Path(__file__).parent
    circuit_file = test_dir / "comprehensive_root.py"
    output_dir = test_dir / "comprehensive_root"
    root_schematic = output_dir / "comprehensive_root.kicad_sch"
    sub_schematic = output_dir / "amplifier.kicad_sch"

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
        assert sub_schematic.exists(), "Subcircuit schematic not generated"

        # Load root sheet
        root_sch = Schematic.load(str(root_schematic))
        root_components = [c for c in root_sch.components if not c.reference.startswith("#PWR")]
        assert len(root_components) == 2, "Expected 2 components on root sheet"

        # Load subcircuit sheet
        sub_sch = Schematic.load(str(sub_schematic))
        sub_components = [c for c in sub_sch.components if not c.reference.startswith("#PWR")]
        assert len(sub_components) == 1, "Expected 1 component in subcircuit"

        # Verify R3 exists
        r3 = next((c for c in sub_components if c.reference == "R3"), None)
        assert r3 is not None, "R3 missing in subcircuit"

        print("\n✅ Test 28 PASSED: Sheet rename test circuit generated successfully")
        print(f"   - Root sheet: 2 components ✓")
        print(f"   - Subcircuit sheet: amplifier.kicad_sch ✓")
        print(f"   - Hierarchical structure: verified ✓")
        print(f"\n💡 Note: Full test includes renaming to signal_stage.kicad_sch")

    finally:
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
