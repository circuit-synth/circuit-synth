#!/usr/bin/env python3
"""Test Issue #240: Component Position Preservation"""
import pytest, subprocess, shutil
from pathlib import Path

def test_issue_240(request):
    """Regression test: Verify component positions preserved during regeneration."""
    test_dir = Path(__file__).parent
    circuit_file = test_dir / "component_positions_circuit.py"
    output_dir = test_dir / "position_test"
    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # Generate circuit
        result = subprocess.run(["uv", "run", str(circuit_file)], cwd=test_dir, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, f"Generation failed: {result.stderr}"

        # First generation
        schematic_file = output_dir / "position_test.kicad_sch"
        assert schematic_file.exists(), "Schematic not generated"

        from kicad_sch_api import Schematic
        sch1 = Schematic.load(str(schematic_file))
        r1_pos1 = next((c for c in sch1.components if c.reference == "R1"), None).position

        # Regenerate
        result2 = subprocess.run(["uv", "run", str(circuit_file)], cwd=test_dir, capture_output=True, text=True, timeout=30)
        assert result2.returncode == 0, "Regeneration failed"

        # Verify position preserved
        sch2 = Schematic.load(str(schematic_file))
        r1_pos2 = next((c for c in sch2.components if c.reference == "R1"), None).position
        assert r1_pos1.x == r1_pos2.x, "X position not preserved"
        assert r1_pos1.y == r1_pos2.y, "Y position not preserved"

        print(f"\n✅ Issue #240 PASSED: Component Position Preservation")
    finally:
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
