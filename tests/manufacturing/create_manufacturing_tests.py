#!/usr/bin/env python3
"""Generate manufacturing tests 02-04."""
from pathlib import Path

tests = [
    {
        "num": "02",
        "name": "pnp_generation",
        "circuit_name": "pnp_circuit",
        "title": "Pick-and-Place (PnP) Data",
        "description": "Verify component positions available for PnP/CPL",
        "test_checks": '''        # Verify component positions available
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))

        components = [c for c in sch.components if not c.reference.startswith("#PWR")]
        assert len(components) > 0, "No components found"

        # Verify all components have positions
        for comp in components:
            assert comp.position, f"{comp.reference} missing position"
            assert comp.position.x is not None, f"{comp.reference} missing X position"
            assert comp.position.y is not None, f"{comp.reference} missing Y position"

        print(f"\\n✅ Test 02 PASSED: PnP Data Validation")
        print(f"   Components with positions: {len(components)}")''',
    },
    {
        "num": "03",
        "name": "gerber_validation",
        "circuit_name": "gerber_circuit",
        "title": "PCB File Generation",
        "description": "Verify PCB file generated and valid",
        "test_checks": '''        # Verify PCB file generated
        pcb_file = output_dir / "gerber_circuit.kicad_pcb"
        assert pcb_file.exists(), "PCB file not generated"

        # Basic validation: file not empty and contains expected content
        pcb_content = pcb_file.read_text()
        assert len(pcb_content) > 0, "PCB file is empty"
        assert "kicad_pcb" in pcb_content, "PCB file doesn't appear to be valid KiCad PCB"
        assert "footprint" in pcb_content.lower(), "PCB file missing footprints"

        print(f"\\n✅ Test 03 PASSED: PCB File Validation")
        print(f"   PCB file size: {len(pcb_content)} bytes")''',
    },
    {
        "num": "04",
        "name": "drill_files",
        "circuit_name": "drill_circuit",
        "title": "Netlist for Manufacturing",
        "description": "Verify netlist suitable for manufacturing",
        "test_checks": '''        # Verify netlist generated
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

        print(f"\\n✅ Test 04 PASSED: Netlist for Manufacturing")
        print(f"   Netlist size: {len(netlist_content)} bytes")
        print(f"   Components in netlist: {len(components)}")''',
    },
]

circuit_template = '''#!/usr/bin/env python3
"""Circuit for {title} testing."""
from circuit_synth import circuit, Component, Net

@circuit(name="{circuit_name}")
def {circuit_name}():
    """Circuit for manufacturing validation."""
    r1 = Component(symbol="Device:R", ref="R1", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r2 = Component(symbol="Device:R", ref="R2", value="4.7k", footprint="Resistor_SMD:R_0603_1608Metric")
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
    circuit_obj = {circuit_name}()
    circuit_obj.generate_kicad_project(project_name="{circuit_name}", placement_algorithm="hierarchical", generate_pcb=True)
    print(f"✅ {title} circuit generated")
'''

for test in tests:
    test_dir = Path(f"{test['num']}_{test['name']}")
    test_dir.mkdir(exist_ok=True)

    # Create circuit file
    circuit_file = test_dir / f"{test['circuit_name']}.py"
    circuit_file.write_text(circuit_template.format(**test))

    # Create test file
    test_file = test_dir / f"test_{test['num']}_mfg.py"
    test_content = f'''#!/usr/bin/env python3
"""Test {test['num']}: {test['title']}"""
import pytest, subprocess, shutil
from pathlib import Path

def test_{test['num']}_manufacturing(request):
    """Test {test['description']}."""
    test_dir = Path(__file__).parent
    circuit_file = test_dir / "{test['circuit_name']}.py"
    output_dir = test_dir / "{test['circuit_name']}"
    schematic_file = output_dir / "{test['circuit_name']}.kicad_sch"
    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # Generate circuit
        result = subprocess.run(["uv", "run", str(circuit_file)], cwd=test_dir, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, f"Generation failed: {{result.stderr}}"
        assert schematic_file.exists(), "Schematic not generated"

{test['test_checks']}
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

print("\n✅ All manufacturing tests created!")
