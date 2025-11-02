#!/usr/bin/env python3
"""Test 04: Complex Components Netlist"""
import pytest, subprocess, shutil
from pathlib import Path

def test_04_netlist(request):
    """Test Multi-unit components in netlist."""
    test_dir = Path(__file__).parent
    circuit_file = test_dir / "complex_circuit.py"
    output_dir = test_dir / "complex_circuit"
    netlist_file = output_dir / "complex_circuit.net"
    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # Generate circuit
        result = subprocess.run(["uv", "run", str(circuit_file)], cwd=test_dir, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, f"Generation failed: {result.stderr}"

        # Verify netlist exists
        assert netlist_file.exists(), "Netlist file not generated"

        # Read and validate netlist content
        netlist_content = netlist_file.read_text()

        # Check components
        assert "R1" in netlist_content, "R1 not found in netlist"
        assert "R2" in netlist_content, "R2 not found in netlist"
        assert "C1" in netlist_content, "C1 not found in netlist"

        # Check nets
        assert "VCC" in netlist_content, "VCC net not in netlist"
        assert "GND" in netlist_content, "GND net not in netlist"
        assert "SIGNAL" in netlist_content, "SIGNAL net not in netlist"

        print(f"\n✅ Test 04 PASSED: Complex Components Netlist")
    finally:
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
