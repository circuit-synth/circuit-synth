#!/usr/bin/env python3
"""Test Issue #270: Automatic Footprint Selection"""
import pytest, subprocess, shutil
from pathlib import Path

def test_issue_270(request):
    """Regression test: Verify footprints auto-selected for common components."""
    test_dir = Path(__file__).parent
    circuit_file = test_dir / "footprint_selection_circuit.py"
    output_dir = test_dir / "footprint_test"
    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # Generate circuit
        result = subprocess.run(["uv", "run", str(circuit_file)], cwd=test_dir, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, f"Generation failed: {result.stderr}"

        # Verify footprints assigned
        schematic_file = output_dir / "footprint_test.kicad_sch"
        assert schematic_file.exists(), "Schematic not generated"

        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))

        # Check R1 has footprint
        r1 = next((c for c in sch.components if c.reference == "R1"), None)
        assert r1 is not None, "R1 not found"
        assert r1.footprint, "R1 footprint not assigned"

        # Check C1 has footprint
        c1 = next((c for c in sch.components if c.reference == "C1"), None)
        assert c1 is not None, "C1 not found"
        assert c1.footprint, "C1 footprint not assigned"

        print(f"\n✅ Issue #270 PASSED: Automatic Footprint Selection")
    finally:
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
