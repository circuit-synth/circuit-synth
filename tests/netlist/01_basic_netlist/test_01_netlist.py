#!/usr/bin/env python3
"""Test 01: Basic Netlist Generation"""
import pytest, subprocess, shutil
from pathlib import Path

def test_01_basic_netlist(request):
    """Test basic netlist generation with simple RC circuit."""
    test_dir = Path(__file__).parent
    circuit_file = test_dir / "basic_circuit.py"
    output_dir = test_dir / "basic_circuit"
    netlist_file = output_dir / "basic_circuit.net"
    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # Generate circuit
        result = subprocess.run(["uv", "run", str(circuit_file)], cwd=test_dir, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, f"Generation failed: {result.stderr}"

        # Verify netlist exists
        assert netlist_file.exists(), "Netlist file not generated"

        # Read and validate netlist content
        netlist_content = netlist_file.read_text()

        # Check components exist in netlist
        assert "R1" in netlist_content, "R1 not found in netlist"
        assert "R2" in netlist_content, "R2 not found in netlist"
        assert "C1" in netlist_content, "C1 not found in netlist"

        # Check values preserved
        assert "10k" in netlist_content or "10K" in netlist_content, "R1 value not in netlist"
        assert "4.7k" in netlist_content or "4.7K" in netlist_content, "R2 value not in netlist"
        assert "100nF" in netlist_content or "100n" in netlist_content, "C1 value not in netlist"

        # Check nets exist
        assert "VCC" in netlist_content, "VCC net not in netlist"
        assert "GND" in netlist_content, "GND net not in netlist"
        assert "SIGNAL" in netlist_content, "SIGNAL net not in netlist"

        print(f"\n✅ Test 01 PASSED: Basic Netlist Generation")
    finally:
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
