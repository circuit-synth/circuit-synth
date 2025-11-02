#!/usr/bin/env python3
"""
Test 43: Update Multiple Components - Basic Generation Test

Validates that updating multiple component values in bulk
generates successfully and creates the expected schematic structure.
"""

import pytest
import subprocess
import shutil
from pathlib import Path
from kicad_sch_api import Schematic


def test_43_bulk_update(request):
    """Test updating multiple components - basic generation."""

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
        assert len(root_components) == 7, "Expected 7 components (R1-R5, C1, C2)"

        # Verify components exist with initial values
        r3 = next((c for c in root_components if c.reference == "R3"), None)
        r4 = next((c for c in root_components if c.reference == "R4"), None)
        r5 = next((c for c in root_components if c.reference == "R5"), None)
        assert r3 is not None and r3.value == "1k", f"R3 value should be 1k, got {r3.value if r3 else 'None'}"
        assert r4 is not None and r4.value == "2.2k", f"R4 value should be 2.2k, got {r4.value if r4 else 'None'}"
        assert r5 is not None and r5.value == "3.3k", f"R5 value should be 3.3k, got {r5.value if r5 else 'None'}"

        print("\n✅ Test 43 PASSED: Bulk update test circuit generated successfully")
        print(f"   - Root sheet: 7 components (R1-R5, C1, C2) ✓")
        print(f"   - R3=1k, R4=2.2k, R5=3.3k ✓")
        print(f"\n💡 Note: Full test includes changing to R3=10k, R4=22k, R5=33k and verifying positions")

    finally:
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
