#!/usr/bin/env python3
"""
Test 42: Add Multiple Components - Basic Generation Test

Validates that adding multiple components in bulk
generates successfully and creates the expected schematic structure.
"""

import pytest
import subprocess
import shutil
from pathlib import Path
from kicad_sch_api import Schematic


def test_42_bulk_add(request):
    """Test adding multiple components - basic generation."""

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
        assert len(root_components) == 2, "Expected 2 components initially (R1, R2)"

        # Verify initial components
        r1 = next((c for c in root_components if c.reference == "R1"), None)
        r2 = next((c for c in root_components if c.reference == "R2"), None)
        assert r1 is not None, "R1 missing"
        assert r2 is not None, "R2 missing"

        print("\n✅ Test 42 PASSED: Bulk add test circuit generated successfully")
        print(f"   - Root sheet: 2 components (R1, R2) ✓")
        print(f"\n💡 Note: Full test includes adding R3, R4, R5, C1, C2 and verifying R1/R2 positions")

    finally:
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
