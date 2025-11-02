#!/usr/bin/env python3
"""Generate PCB validation tests."""
from pathlib import Path

tests = [
    {
        "num": "01",
        "name": "pcb_generation",
        "circuit_name": "pcb_gen",
        "title": "PCB File Generation",
        "description": "Verify PCB file generated with basic structure",
        "test_checks": '''        # Verify PCB file exists
        pcb_file = output_dir / "pcb_gen.kicad_pcb"
        assert pcb_file.exists(), "PCB file not generated"

        # Validate PCB content
        pcb_content = pcb_file.read_text()
        assert len(pcb_content) > 100, "PCB file too small to be valid"
        assert "kicad_pcb" in pcb_content, "Missing kicad_pcb header"
        assert "version" in pcb_content, "Missing version info"

        print(f"\\n✅ Test 01 PASSED: PCB File Generation")
        print(f"   PCB file size: {len(pcb_content)} bytes")''',
    },
    {
        "num": "02",
        "name": "footprint_placement",
        "circuit_name": "footprint_test",
        "title": "Footprint Placement",
        "description": "Verify footprints placed in PCB",
        "test_checks": '''        # Verify PCB file has footprints
        pcb_file = output_dir / "footprint_test.kicad_pcb"
        assert pcb_file.exists(), "PCB file not generated"

        pcb_content = pcb_file.read_text()
        assert "footprint" in pcb_content.lower(), "No footprints found in PCB"

        # Count footprints
        footprint_count = pcb_content.lower().count("(footprint")
        assert footprint_count >= 3, f"Expected >= 3 footprints, found {footprint_count}"

        print(f"\\n✅ Test 02 PASSED: Footprint Placement")
        print(f"   Footprints in PCB: {footprint_count}")''',
    },
    {
        "num": "03",
        "name": "pcb_nets",
        "circuit_name": "pcb_nets",
        "title": "PCB Net Definitions",
        "description": "Verify nets defined in PCB",
        "test_checks": '''        # Verify PCB has net definitions
        pcb_file = output_dir / "pcb_nets.kicad_pcb"
        assert pcb_file.exists(), "PCB file not generated"

        pcb_content = pcb_file.read_text()
        assert "(net " in pcb_content, "No net definitions found"

        # Check for specific nets
        assert "VCC" in pcb_content or "Net-" in pcb_content, "No nets found in PCB"

        # Count nets
        net_count = pcb_content.count("(net ")
        print(f"\\n✅ Test 03 PASSED: PCB Net Definitions")
        print(f"   Nets in PCB: {net_count}")''',
    },
    {
        "num": "04",
        "name": "pcb_layers",
        "circuit_name": "pcb_layers",
        "title": "PCB Layer Structure",
        "description": "Verify PCB has proper layer definitions",
        "test_checks": '''        # Verify PCB has layer definitions
        pcb_file = output_dir / "pcb_layers.kicad_pcb"
        assert pcb_file.exists(), "PCB file not generated"

        pcb_content = pcb_file.read_text()
        assert "(layers" in pcb_content, "No layer definitions found"

        # Check for standard layers
        assert "F.Cu" in pcb_content or "0 \"F.Cu\"" in pcb_content, "Front copper layer missing"
        assert "B.Cu" in pcb_content or "31 \"B.Cu\"" in pcb_content, "Back copper layer missing"

        print(f"\\n✅ Test 04 PASSED: PCB Layer Structure")''',
    },
]

circuit_template = '''#!/usr/bin/env python3
"""Circuit for {title} testing."""
from circuit_synth import circuit, Component, Net

@circuit(name="{circuit_name}")
def {circuit_name}():
    """Circuit for PCB validation."""
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
    test_file = test_dir / f"test_{test['num']}_pcb.py"
    test_content = f'''#!/usr/bin/env python3
"""Test {test['num']}: {test['title']}"""
import pytest, subprocess, shutil
from pathlib import Path

def test_{test['num']}_pcb(request):
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

print("\n✅ All PCB validation tests created!")
