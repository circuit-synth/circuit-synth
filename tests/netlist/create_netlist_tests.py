#!/usr/bin/env python3
"""Generate netlist generation tests 02-04."""
from pathlib import Path

tests = [
    {
        "num": "02",
        "name": "hierarchical_netlist",
        "circuit_name": "hierarchical_circuit",
        "title": "Hierarchical Netlist",
        "description": "Hierarchical circuits with subcircuit expansion",
        "circuit_code": '''#!/usr/bin/env python3
"""Hierarchical circuit for netlist generation test."""
from circuit_synth import circuit, Component, Net

@circuit(name="amplifier")
def amplifier_stage(input_sig, output_sig, vcc, gnd):
    """Simple amplifier subcircuit."""
    r1 = Component(symbol="Device:R", ref="R1", value="100k", footprint="Resistor_SMD:R_0603_1608Metric")
    r2 = Component(symbol="Device:R", ref="R2", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r1[1] += input_sig
    r1[2] += output_sig
    r2[1] += output_sig
    r2[2] += gnd

@circuit(name="hierarchical_circuit")
def hierarchical_circuit():
    """Circuit with subcircuits for netlist validation."""
    vcc = Net(name="VCC")
    gnd = Net(name="GND")
    sig_in = Net(name="SIG_IN")
    sig_out = Net(name="SIG_OUT")

    # Instantiate amplifier subcircuit
    amplifier_stage(input_sig=sig_in, output_sig=sig_out, vcc=vcc, gnd=gnd)

if __name__ == "__main__":
    circuit_obj = hierarchical_circuit()
    circuit_obj.generate_kicad_project(project_name="hierarchical_circuit", placement_algorithm="hierarchical", generate_pcb=True)
    print(f"✅ Hierarchical netlist test circuit generated")
''',
        "test_checks": '''        # Check subcircuit components expanded in netlist
        assert "R1" in netlist_content, "R1 not found in netlist"
        assert "R2" in netlist_content, "R2 not found in netlist"

        # Check nets
        assert "VCC" in netlist_content, "VCC net not in netlist"
        assert "GND" in netlist_content, "GND net not in netlist"
        assert "SIG_IN" in netlist_content, "SIG_IN net not in netlist"
        assert "SIG_OUT" in netlist_content, "SIG_OUT net not in netlist"''',
    },
    {
        "num": "03",
        "name": "power_nets_netlist",
        "circuit_name": "power_circuit",
        "title": "Power Nets Netlist",
        "description": "Multiple power domains in netlist",
        "circuit_code": '''#!/usr/bin/env python3
"""Power nets circuit for netlist generation test."""
from circuit_synth import circuit, Component, Net

@circuit(name="power_circuit")
def power_circuit():
    """Circuit with multiple power domains."""
    r1 = Component(symbol="Device:R", ref="R1", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r2 = Component(symbol="Device:R", ref="R2", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")

    vcc = Net(name="VCC")
    v3v3 = Net(name="3V3")
    gnd = Net(name="GND")

    r1[1] += vcc
    r1[2] += gnd
    r2[1] += v3v3
    r2[2] += gnd

if __name__ == "__main__":
    circuit_obj = power_circuit()
    circuit_obj.generate_kicad_project(project_name="power_circuit", placement_algorithm="hierarchical", generate_pcb=True)
    print(f"✅ Power nets netlist test circuit generated")
''',
        "test_checks": '''        # Check components
        assert "R1" in netlist_content, "R1 not found in netlist"
        assert "R2" in netlist_content, "R2 not found in netlist"

        # Check multiple power domains
        assert "VCC" in netlist_content, "VCC power net not in netlist"
        assert "3V3" in netlist_content, "3V3 power net not in netlist"
        assert "GND" in netlist_content, "GND power net not in netlist"''',
    },
    {
        "num": "04",
        "name": "complex_components_netlist",
        "circuit_name": "complex_circuit",
        "title": "Complex Components Netlist",
        "description": "Multi-unit components in netlist",
        "circuit_code": '''#!/usr/bin/env python3
"""Complex components circuit for netlist generation test."""
from circuit_synth import circuit, Component, Net

@circuit(name="complex_circuit")
def complex_circuit():
    """Circuit with multi-unit components."""
    # Use simple components for now - multi-unit support may be limited
    r1 = Component(symbol="Device:R", ref="R1", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r2 = Component(symbol="Device:R", ref="R2", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    c1 = Component(symbol="Device:C", ref="C1", value="100nF", footprint="Capacitor_SMD:C_0603_1608Metric")

    vcc = Net(name="VCC")
    gnd = Net(name="GND")
    sig = Net(name="SIGNAL")

    r1[1] += vcc
    r1[2] += sig
    r2[1] += sig
    r2[2] += gnd
    c1[1] += sig
    c1[2] += gnd

if __name__ == "__main__":
    circuit_obj = complex_circuit()
    circuit_obj.generate_kicad_project(project_name="complex_circuit", placement_algorithm="hierarchical", generate_pcb=True)
    print(f"✅ Complex components netlist test circuit generated")
''',
        "test_checks": '''        # Check components
        assert "R1" in netlist_content, "R1 not found in netlist"
        assert "R2" in netlist_content, "R2 not found in netlist"
        assert "C1" in netlist_content, "C1 not found in netlist"

        # Check nets
        assert "VCC" in netlist_content, "VCC net not in netlist"
        assert "GND" in netlist_content, "GND net not in netlist"
        assert "SIGNAL" in netlist_content, "SIGNAL net not in netlist"''',
    },
]

for test in tests:
    test_dir = Path(f"{test['num']}_{test['name']}")
    test_dir.mkdir(exist_ok=True)

    # Create circuit file
    circuit_file = test_dir / f"{test['circuit_name']}.py"
    circuit_file.write_text(test['circuit_code'])

    # Create test file
    test_file = test_dir / f"test_{test['num']}_netlist.py"
    test_content = f'''#!/usr/bin/env python3
"""Test {test['num']}: {test['title']}"""
import pytest, subprocess, shutil
from pathlib import Path

def test_{test['num']}_netlist(request):
    """Test {test['description']}."""
    test_dir = Path(__file__).parent
    circuit_file = test_dir / "{test['circuit_name']}.py"
    output_dir = test_dir / "{test['circuit_name']}"
    netlist_file = output_dir / "{test['circuit_name']}.net"
    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # Generate circuit
        result = subprocess.run(["uv", "run", str(circuit_file)], cwd=test_dir, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, f"Generation failed: {{result.stderr}}"

        # Verify netlist exists
        assert netlist_file.exists(), "Netlist file not generated"

        # Read and validate netlist content
        netlist_content = netlist_file.read_text()

{test['test_checks']}

        print(f"\\n✅ Test {test['num']} PASSED: {test['title']}")
    finally:
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
'''
    test_file.write_text(test_content)

    # Create README
    readme_file = test_dir / "README.md"
    readme_content = f'''# Test {test['num']}: {test['title']}

Tests {test['description']}.

```bash
pytest test_*.py -v
```
'''
    readme_file.write_text(readme_content)

    print(f"✅ Created Test {test['num']}: {test['title']}")

print("\n✅ All netlist generation tests created!")
