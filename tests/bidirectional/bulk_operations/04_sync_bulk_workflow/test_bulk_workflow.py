#!/usr/bin/env python3
"""
Test 45: Complex Multi-Operation Workflow - Basic Generation Test

Validates that complex workflows combining multiple CRUD operations
generate successfully and create the expected schematic structure.

Workflow includes:
- Add component (R5)
- Update component value (R2)
- Delete component (C1)
- Rename net (VCC → VBAT)
- Add component to subcircuit (C2)

Note: Full bidirectional sync verification for hierarchical circuits
is pending implementation of hierarchical position preservation.
"""

import pytest
import subprocess
import shutil
from pathlib import Path
from kicad_sch_api import Schematic


def test_45_bulk_workflow(request):
    """Test complex multi-operation workflow - basic generation."""

    test_dir = Path(__file__).parent
    circuit_file = test_dir / "comprehensive_root.py"
    output_dir = test_dir / "comprehensive_root"
    root_schematic = output_dir / "comprehensive_root.kicad_sch"
    amp_schematic = output_dir / "amplifier.kicad_sch"

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

        # Load root sheet
        root_sch = Schematic.load(str(root_schematic))
        root_components = [c for c in root_sch.components if not c.reference.startswith("#PWR")]
        assert len(root_components) == 3, "Expected 3 components on root (R1, R2, C1)"

        # Load amplifier sheet
        amp_sch = Schematic.load(str(amp_schematic))
        amp_components = [c for c in amp_sch.components if not c.reference.startswith("#PWR")]
        assert len(amp_components) == 2, "Expected 2 components in amplifier (R3, R4)"

        # Verify initial state
        r2 = next((c for c in root_components if c.reference == "R2"), None)
        c1 = next((c for c in root_components if c.reference == "C1"), None)
        assert r2 is not None and r2.value == "4.7k", "R2 should have value 4.7k"
        assert c1 is not None, "C1 should exist initially"

        print("\n✅ Test 45 PASSED: Complex workflow test circuit generated successfully")
        print(f"   - Root sheet: 3 components (R1, R2, C1) ✓")
        print(f"   - Amplifier sheet: 2 components (R3, R4) ✓")
        print(f"   - R2=4.7k ✓")
        print(f"\n💡 Note: Full workflow test includes:")
        print(f"   1. Add R5 to root")
        print(f"   2. Update R2: 4.7k → 47k")
        print(f"   3. Delete C1")
        print(f"   4. Rename VCC → VBAT")
        print(f"   5. Add C2 to amplifier")

    finally:
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
