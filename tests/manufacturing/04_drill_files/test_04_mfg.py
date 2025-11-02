#!/usr/bin/env python3
"""Test 04: Netlist for Manufacturing"""
import pytest, subprocess, shutil
from pathlib import Path

def test_04_manufacturing(request):
    """Test Verify netlist suitable for manufacturing."""
    test_dir = Path(__file__).parent
    circuit_file = test_dir / "drill_circuit.py"
    output_dir = test_dir / "drill_circuit"
    schematic_file = output_dir / "drill_circuit.kicad_sch"
    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # Generate circuit
        result = subprocess.run(["uv", "run", str(circuit_file)], cwd=test_dir, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, f"Generation failed: {result.stderr}"
        assert schematic_file.exists(), "Schematic not generated"

        # Verify netlist generated
        netlist_file = output_dir / "drill_circuit.net"
        assert netlist_file.exists(), "Netlist not generated"

        # Validate netlist content
        netlist_content = netlist_file.read_text()
        assert len(netlist_content) > 0, "Netlist is empty"

        # Check for component data in netlist
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        components = [c for c in sch.components if not c.reference.startswith("#PWR")]

        for comp in components:
            assert comp.reference in netlist_content, f"{comp.reference} not in netlist"

        print(f"\n✅ Test 04 PASSED: Netlist for Manufacturing")
        print(f"   Netlist size: {len(netlist_content)} bytes")
        print(f"   Components in netlist: {len(components)}")
    finally:
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
