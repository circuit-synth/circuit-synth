#!/usr/bin/env python3
"""Test Issue #260: Power Symbol Generation"""
import pytest, subprocess, shutil
from pathlib import Path

def test_issue_260(request):
    """Regression test: Verify power symbols generated correctly."""
    test_dir = Path(__file__).parent
    circuit_file = test_dir / "power_symbols_circuit.py"
    output_dir = test_dir / "power_test"
    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # Generate circuit
        result = subprocess.run(["uv", "run", str(circuit_file)], cwd=test_dir, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, f"Generation failed: {result.stderr}"

        # Verify power symbols in schematic
        schematic_file = output_dir / "power_test.kicad_sch"
        assert schematic_file.exists(), "Schematic not generated"

        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))

        # Check power symbols exist
        power_symbols = [c for c in sch.components if c.reference.startswith("#PWR")]
        assert len(power_symbols) > 0, "No power symbols generated"

        print(f"\n✅ Issue #260 PASSED: Power Symbol Generation")
    finally:
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
