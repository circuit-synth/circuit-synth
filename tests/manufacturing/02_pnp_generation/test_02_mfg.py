#!/usr/bin/env python3
"""Test 02: Pick-and-Place (PnP) Data"""
import pytest, subprocess, shutil
from pathlib import Path

def test_02_manufacturing(request):
    """Test Verify component positions available for PnP/CPL."""
    test_dir = Path(__file__).parent
    circuit_file = test_dir / "pnp_circuit.py"
    output_dir = test_dir / "pnp_circuit"
    schematic_file = output_dir / "pnp_circuit.kicad_sch"
    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # Generate circuit
        result = subprocess.run(["uv", "run", str(circuit_file)], cwd=test_dir, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, f"Generation failed: {result.stderr}"
        assert schematic_file.exists(), "Schematic not generated"

        # Verify component positions available
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))

        components = [c for c in sch.components if not c.reference.startswith("#PWR")]
        assert len(components) > 0, "No components found"

        # Verify all components have positions
        for comp in components:
            assert comp.position, f"{comp.reference} missing position"
            assert comp.position.x is not None, f"{comp.reference} missing X position"
            assert comp.position.y is not None, f"{comp.reference} missing Y position"

        print(f"\n✅ Test 02 PASSED: PnP Data Validation")
        print(f"   Components with positions: {len(components)}")
    finally:
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
