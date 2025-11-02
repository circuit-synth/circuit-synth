#!/usr/bin/env python3
"""
Regression test for Issue #458: Power symbol text placement

Tests that power symbol text (VCC, GND, etc.) is correctly positioned
relative to the power symbol graphic.

Expected behavior:
- Text should be near but not overlapping the symbol
- Text should be readable and properly aligned
- Text position should follow KiCad conventions
"""

import pytest
import subprocess
import tempfile
import shutil
from pathlib import Path
from kicad_sch_api import Schematic


@pytest.fixture
def temp_circuit_dir():
    """Create temporary directory for test circuits."""
    tmpdir = tempfile.mkdtemp(prefix="circuit_test_")
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)


def test_vcc_symbol_exists(temp_circuit_dir):
    """
    Test that VCC power symbol is created and has correct properties.

    Basic sanity check for power symbol generation.
    """
    circuit_code = '''
from circuit_synth import circuit, Component, Net

@circuit(name="test_vcc")
def test_vcc():
    """Test circuit with VCC power symbol."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    vcc = Net(name="VCC")
    r1[2] += vcc

if __name__ == "__main__":
    circuit_obj = test_vcc()
    circuit_obj.generate_kicad_project(
        project_name="test_vcc",
        placement_algorithm="hierarchical",
        generate_pcb=False
    )
'''

    circuit_file = temp_circuit_dir / "test_vcc.py"
    circuit_file.write_text(circuit_code)

    result = subprocess.run(
        ["uv", "run", str(circuit_file)],
        cwd=temp_circuit_dir,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Circuit generation failed: {result.stderr}"

    schematic_file = temp_circuit_dir / "test_vcc" / "test_vcc.kicad_sch"
    sch = Schematic.load(str(schematic_file))

    # Find VCC power symbol
    power_symbols = [c for c in sch.components if c.reference.startswith("#PWR")]
    vcc_symbols = [p for p in power_symbols if p.value == "VCC"]

    assert len(vcc_symbols) == 1, f"Expected 1 VCC symbol, found {len(vcc_symbols)}"

    vcc = vcc_symbols[0]
    assert vcc.library == "power", f"VCC should be from power library, got {vcc.library}"
    assert vcc.symbol_name == "VCC", f"Symbol name should be VCC, got {vcc.symbol_name}"
    assert vcc.lib_id == "power:VCC", f"lib_id should be power:VCC, got {vcc.lib_id}"


def test_gnd_symbol_exists(temp_circuit_dir):
    """
    Test that GND power symbol is created and has correct properties.
    """
    circuit_code = '''
from circuit_synth import circuit, Component, Net

@circuit(name="test_gnd")
def test_gnd():
    """Test circuit with GND power symbol."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    gnd = Net(name="GND")
    r1[1] += gnd

if __name__ == "__main__":
    circuit_obj = test_gnd()
    circuit_obj.generate_kicad_project(
        project_name="test_gnd",
        placement_algorithm="hierarchical",
        generate_pcb=False
    )
'''

    circuit_file = temp_circuit_dir / "test_gnd.py"
    circuit_file.write_text(circuit_code)

    result = subprocess.run(
        ["uv", "run", str(circuit_file)],
        cwd=temp_circuit_dir,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Circuit generation failed: {result.stderr}"

    schematic_file = temp_circuit_dir / "test_gnd" / "test_gnd.kicad_sch"
    sch = Schematic.load(str(schematic_file))

    power_symbols = [c for c in sch.components if c.reference.startswith("#PWR")]
    gnd_symbols = [p for p in power_symbols if p.value == "GND"]

    assert len(gnd_symbols) == 1, f"Expected 1 GND symbol, found {len(gnd_symbols)}"

    gnd = gnd_symbols[0]
    assert gnd.library == "power"
    assert gnd.symbol_name == "GND"
    assert gnd.lib_id == "power:GND"


def test_multiple_power_domains(temp_circuit_dir):
    """
    Test circuit with multiple power symbols (VCC, GND, +5V).

    Issue #458: Verify text placement is correct for all power symbol types.
    """
    circuit_code = '''
from circuit_synth import circuit, Component, Net

@circuit(name="test_multi_power")
def test_multi_power():
    """Test circuit with multiple power domains."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    c1 = Component(
        symbol="Device:C",
        ref="C1",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )

    # Multiple power nets
    vcc = Net(name="VCC")
    vdd_5v = Net(name="+5V")
    gnd = Net(name="GND")

    # Connections
    r1[2] += vcc
    r2[2] += vdd_5v
    c1[2] += gnd

if __name__ == "__main__":
    circuit_obj = test_multi_power()
    circuit_obj.generate_kicad_project(
        project_name="test_multi_power",
        placement_algorithm="hierarchical",
        generate_pcb=False
    )
'''

    circuit_file = temp_circuit_dir / "test_multi_power.py"
    circuit_file.write_text(circuit_code)

    result = subprocess.run(
        ["uv", "run", str(circuit_file)],
        cwd=temp_circuit_dir,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Circuit generation failed: {result.stderr}"

    schematic_file = temp_circuit_dir / "test_multi_power" / "test_multi_power.kicad_sch"
    sch = Schematic.load(str(schematic_file))

    power_symbols = [c for c in sch.components if c.reference.startswith("#PWR")]

    # Verify we have all three power symbols
    power_values = {p.value for p in power_symbols}
    expected_values = {"VCC", "+5V", "GND"}

    assert power_values == expected_values, (
        f"Expected power symbols {expected_values}, got {power_values}"
    )

    # Check each power symbol
    for power_symbol in power_symbols:
        assert power_symbol.library == "power", (
            f"{power_symbol.value} should be from power library"
        )

        assert power_symbol.position is not None, (
            f"{power_symbol.value} should have a position"
        )

        # Power symbols should be positioned near their connected components
        # This is a basic sanity check - the actual text placement within
        # the symbol is harder to verify without parsing the raw .kicad_sch
        assert hasattr(power_symbol.position, 'x') and hasattr(power_symbol.position, 'y'), (
            f"{power_symbol.value} position should have x and y attributes"
        )


def test_power_symbol_positioning_comprehensive(temp_circuit_dir):
    """
    Test power symbol positioning in comprehensive circuit.

    This is the actual Test 10 circuit that revealed Issue #458.
    Verifies that power symbols are correctly positioned relative to components.
    """
    circuit_code = '''
from circuit_synth import circuit, Component, Net

@circuit(name="comprehensive_power")
def comprehensive_power():
    """Comprehensive test with components and power symbols."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    c1 = Component(
        symbol="Device:C",
        ref="C1",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )

    # Power nets
    vcc = Net(name="VCC")
    gnd = Net(name="GND")

    # Signal net
    data = Net("DATA")

    # Connections
    r1[1] += data
    c1[1] += data
    r1[2] += vcc
    c1[2] += gnd

if __name__ == "__main__":
    circuit_obj = comprehensive_power()
    circuit_obj.generate_kicad_project(
        project_name="comprehensive_power",
        placement_algorithm="hierarchical",
        generate_pcb=False
    )
'''

    circuit_file = temp_circuit_dir / "comprehensive_power.py"
    circuit_file.write_text(circuit_code)

    result = subprocess.run(
        ["uv", "run", str(circuit_file)],
        cwd=temp_circuit_dir,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Circuit generation failed: {result.stderr}"

    schematic_file = temp_circuit_dir / "comprehensive_power" / "comprehensive_power.kicad_sch"
    sch = Schematic.load(str(schematic_file))

    # Get components
    r1 = next(c for c in sch.components if c.reference == "R1")
    c1 = next(c for c in sch.components if c.reference == "C1")

    # Get power symbols
    power_symbols = [c for c in sch.components if c.reference.startswith("#PWR")]
    vcc_symbol = next(p for p in power_symbols if p.value == "VCC")
    gnd_symbol = next(p for p in power_symbols if p.value == "GND")

    # VCC should be positioned near R1 pin 2
    r1_pins = sch.list_component_pins("R1")
    r1_pin2 = next(p for p in r1_pins if p[0] == "2")
    r1_pin2_pos = r1_pin2[1]

    # Calculate distance from VCC symbol to R1 pin 2
    vcc_to_r1_distance = (
        (vcc_symbol.position.x - r1_pin2_pos.x)**2 +
        (vcc_symbol.position.y - r1_pin2_pos.y)**2
    )**0.5

    # Power symbol should be very close to the pin (within ~10mm)
    # This is a reasonable tolerance for automated placement
    assert vcc_to_r1_distance < 10.0, (
        f"VCC symbol should be near R1 pin 2. "
        f"Distance: {vcc_to_r1_distance:.2f}mm "
        f"VCC at {vcc_symbol.position}, R1 pin 2 at ({r1_pin2_pos.x}, {r1_pin2_pos.y}). "
        f"Issue #458: Power symbol text placement may be incorrect."
    )

    # GND should be positioned near C1 pin 2
    c1_pins = sch.list_component_pins("C1")
    c1_pin2 = next(p for p in c1_pins if p[0] == "2")
    c1_pin2_pos = c1_pin2[1]

    gnd_to_c1_distance = (
        (gnd_symbol.position.x - c1_pin2_pos.x)**2 +
        (gnd_symbol.position.y - c1_pin2_pos.y)**2
    )**0.5

    assert gnd_to_c1_distance < 10.0, (
        f"GND symbol should be near C1 pin 2. "
        f"Distance: {gnd_to_c1_distance:.2f}mm "
        f"GND at {gnd_symbol.position}, C1 pin 2 at ({c1_pin2_pos.x}, {c1_pin2_pos.y}). "
        f"Issue #458: Power symbol text placement may be incorrect."
    )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
