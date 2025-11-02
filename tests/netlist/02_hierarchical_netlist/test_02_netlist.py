#!/usr/bin/env python3
"""Test 02: Hierarchical Netlist"""
import pytest, subprocess, shutil
from pathlib import Path

def test_02_netlist(request):
    """Test Hierarchical circuits with subcircuit expansion."""
    test_dir = Path(__file__).parent
    circuit_file = test_dir / "hierarchical_circuit.py"
    output_dir = test_dir / "hierarchical_circuit"
    netlist_file = output_dir / "hierarchical_circuit.net"
    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # Generate circuit
        result = subprocess.run(["uv", "run", str(circuit_file)], cwd=test_dir, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, f"Generation failed: {result.stderr}"

        # Verify netlist exists
        assert netlist_file.exists(), "Netlist file not generated"

        # Read and validate netlist content
        netlist_content = netlist_file.read_text()

        # Check subcircuit components expanded in netlist
        assert "R1" in netlist_content, "R1 not found in netlist"
        assert "R2" in netlist_content, "R2 not found in netlist"
        assert "R3" in netlist_content, "R3 not found in netlist"

        # Check nets
        assert "VCC" in netlist_content, "VCC net not in netlist"
        assert "GND" in netlist_content, "GND net not in netlist"
        assert "SIG_IN" in netlist_content, "SIG_IN net not in netlist"
        assert "SIG_OUT" in netlist_content, "SIG_OUT net not in netlist"

        print(f"\n✅ Test 02 PASSED: Hierarchical Netlist")
    finally:
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
