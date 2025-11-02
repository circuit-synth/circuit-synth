#!/usr/bin/env python3
"""Test Issue #250: Net Name Preservation"""
import pytest, subprocess, shutil
from pathlib import Path

def test_issue_250(request):
    """Regression test: Verify net names preserved correctly."""
    test_dir = Path(__file__).parent
    circuit_file = test_dir / "net_names_circuit.py"
    output_dir = test_dir / "netname_test"
    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # Generate circuit
        result = subprocess.run(["uv", "run", str(circuit_file)], cwd=test_dir, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, f"Generation failed: {result.stderr}"

        # Verify netlist contains correct net names
        netlist_file = output_dir / "netname_test.net"
        assert netlist_file.exists(), "Netlist not generated"

        netlist_content = netlist_file.read_text()
        assert "VCC" in netlist_content, "VCC net name not preserved"
        assert "CUSTOM_SIGNAL" in netlist_content, "CUSTOM_SIGNAL net name not preserved"

        print(f"\n✅ Issue #250 PASSED: Net Name Preservation")
    finally:
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
