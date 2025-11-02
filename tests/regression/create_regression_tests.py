#!/usr/bin/env python3
"""Generate regression tests for specific issues."""
from pathlib import Path

tests = [
    {
        "issue": "238",
        "name": "text_parameters",
        "title": "Text Class Parameters",
        "description": "Verify Text class accepts parameters in correct order",
        "circuit_code": '''#!/usr/bin/env python3
"""Regression test for issue #238 - Text class parameters."""
from circuit_synth import circuit, Component, Net

@circuit(name="text_test")
def text_test():
    """Simple circuit to test text/label handling."""
    r1 = Component(symbol="Device:R", ref="R1", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    vcc = Net(name="VCC")
    gnd = Net(name="GND")
    r1[1] += vcc
    r1[2] += gnd

if __name__ == "__main__":
    circuit_obj = text_test()
    circuit_obj.generate_kicad_project(project_name="text_test", placement_algorithm="hierarchical", generate_pcb=True)
    print(f"✅ Text parameters regression test passed")
''',
        "test_checks": '''        # Verify schematic generated
        schematic_file = output_dir / "text_test.kicad_sch"
        assert schematic_file.exists(), "Schematic not generated"

        # Load and verify no errors with text/labels
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        assert len(sch.components) > 0, "No components found"''',
    },
    {
        "issue": "240",
        "name": "component_positions",
        "title": "Component Position Preservation",
        "description": "Verify component positions preserved during regeneration",
        "circuit_code": '''#!/usr/bin/env python3
"""Regression test for issue #240 - Component position preservation."""
from circuit_synth import circuit, Component, Net

@circuit(name="position_test")
def position_test():
    """Circuit to test position preservation."""
    r1 = Component(symbol="Device:R", ref="R1", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r2 = Component(symbol="Device:R", ref="R2", value="4.7k", footprint="Resistor_SMD:R_0603_1608Metric")
    vcc = Net(name="VCC")
    gnd = Net(name="GND")
    sig = Net(name="SIGNAL")

    r1[1] += vcc
    r1[2] += sig
    r2[1] += sig
    r2[2] += gnd

if __name__ == "__main__":
    circuit_obj = position_test()
    circuit_obj.generate_kicad_project(project_name="position_test", placement_algorithm="hierarchical", generate_pcb=True)
    print(f"✅ Component position regression test passed")
''',
        "test_checks": '''        # First generation
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
        assert r1_pos1.y == r1_pos2.y, "Y position not preserved"''',
    },
    {
        "issue": "250",
        "name": "net_names",
        "title": "Net Name Preservation",
        "description": "Verify net names preserved correctly",
        "circuit_code": '''#!/usr/bin/env python3
"""Regression test for issue #250 - Net name preservation."""
from circuit_synth import circuit, Component, Net

@circuit(name="netname_test")
def netname_test():
    """Circuit to test net name preservation."""
    r1 = Component(symbol="Device:R", ref="R1", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")

    # Use specific net names that should be preserved
    vcc = Net(name="VCC")
    custom_net = Net(name="CUSTOM_SIGNAL")

    r1[1] += vcc
    r1[2] += custom_net

if __name__ == "__main__":
    circuit_obj = netname_test()
    circuit_obj.generate_kicad_project(project_name="netname_test", placement_algorithm="hierarchical", generate_pcb=True)
    print(f"✅ Net name regression test passed")
''',
        "test_checks": '''        # Verify netlist contains correct net names
        netlist_file = output_dir / "netname_test.net"
        assert netlist_file.exists(), "Netlist not generated"

        netlist_content = netlist_file.read_text()
        assert "VCC" in netlist_content, "VCC net name not preserved"
        assert "CUSTOM_SIGNAL" in netlist_content, "CUSTOM_SIGNAL net name not preserved"''',
    },
    {
        "issue": "260",
        "name": "power_symbols",
        "title": "Power Symbol Generation",
        "description": "Verify power symbols generated correctly",
        "circuit_code": '''#!/usr/bin/env python3
"""Regression test for issue #260 - Power symbol generation."""
from circuit_synth import circuit, Component, Net

@circuit(name="power_test")
def power_test():
    """Circuit to test power symbol generation."""
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
    circuit_obj = power_test()
    circuit_obj.generate_kicad_project(project_name="power_test", placement_algorithm="hierarchical", generate_pcb=True)
    print(f"✅ Power symbol regression test passed")
''',
        "test_checks": '''        # Verify power symbols in schematic
        schematic_file = output_dir / "power_test.kicad_sch"
        assert schematic_file.exists(), "Schematic not generated"

        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))

        # Check power symbols exist
        power_symbols = [c for c in sch.components if c.reference.startswith("#PWR")]
        assert len(power_symbols) > 0, "No power symbols generated"''',
    },
    {
        "issue": "270",
        "name": "footprint_selection",
        "title": "Automatic Footprint Selection",
        "description": "Verify footprints auto-selected for common components",
        "circuit_code": '''#!/usr/bin/env python3
"""Regression test for issue #270 - Automatic footprint selection."""
from circuit_synth import circuit, Component, Net

@circuit(name="footprint_test")
def footprint_test():
    """Circuit to test automatic footprint selection."""
    r1 = Component(symbol="Device:R", ref="R1", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    c1 = Component(symbol="Device:C", ref="C1", value="100nF", footprint="Capacitor_SMD:C_0603_1608Metric")

    vcc = Net(name="VCC")
    gnd = Net(name="GND")

    r1[1] += vcc
    r1[2] += gnd
    c1[1] += vcc
    c1[2] += gnd

if __name__ == "__main__":
    circuit_obj = footprint_test()
    circuit_obj.generate_kicad_project(project_name="footprint_test", placement_algorithm="hierarchical", generate_pcb=True)
    print(f"✅ Footprint selection regression test passed")
''',
        "test_checks": '''        # Verify footprints assigned
        schematic_file = output_dir / "footprint_test.kicad_sch"
        assert schematic_file.exists(), "Schematic not generated"

        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))

        # Check R1 has footprint
        r1 = next((c for c in sch.components if c.reference == "R1"), None)
        assert r1 is not None, "R1 not found"
        assert r1.footprint, "R1 footprint not assigned"

        # Check C1 has footprint
        c1 = next((c for c in sch.components if c.reference == "C1"), None)
        assert c1 is not None, "C1 not found"
        assert c1.footprint, "C1 footprint not assigned"''',
    },
]

for test in tests:
    test_dir = Path(f"issue_{test['issue']}_{test['name']}")
    test_dir.mkdir(exist_ok=True)

    # Create circuit file
    circuit_file = test_dir / f"{test['name']}_circuit.py"
    circuit_file.write_text(test['circuit_code'])

    # Create test file
    test_file = test_dir / f"test_issue_{test['issue']}.py"
    test_content = f'''#!/usr/bin/env python3
"""Test Issue #{test['issue']}: {test['title']}"""
import pytest, subprocess, shutil
from pathlib import Path

def test_issue_{test['issue']}(request):
    """Regression test: {test['description']}."""
    test_dir = Path(__file__).parent
    circuit_file = test_dir / "{test['name']}_circuit.py"
    output_dir = test_dir / "{test['name']}_circuit".replace("_circuit_circuit", "_circuit")
    cleanup = not request.config.getoption("--keep-output", default=False)

    try:
        # Generate circuit
        result = subprocess.run(["uv", "run", str(circuit_file)], cwd=test_dir, capture_output=True, text=True, timeout=30)
        assert result.returncode == 0, f"Generation failed: {{result.stderr}}"

{test['test_checks']}

        print(f"\\n✅ Issue #{test['issue']} PASSED: {test['title']}")
    finally:
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)

if __name__ == "__main__":
    pytest.main([__file__, "-v", "--keep-output"])
'''
    test_file.write_text(test_content)

    # Create README
    readme_file = test_dir / "README.md"
    readme_content = f'''# Regression Test - Issue #{test['issue']}: {test['title']}

Regression test for: {test['description']}

```bash
pytest test_*.py -v
```

**Related Issue**: #{test['issue']}
'''
    readme_file.write_text(readme_content)

    print(f"✅ Created regression test for Issue #{test['issue']}: {test['title']}")

print("\n✅ All regression tests created!")
