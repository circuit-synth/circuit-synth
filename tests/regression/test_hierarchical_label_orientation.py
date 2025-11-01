#!/usr/bin/env python3
"""
Regression test for Issue #457: Hierarchical label orientation

Tests that hierarchical labels are correctly oriented to face toward
the component pins they're connected to.

Expected behavior:
- Top pin (90°): Label should face DOWN (270°) toward pin
- Bottom pin (270°): Label should face UP (90°) toward pin
- Left pin (180°): Label should face RIGHT (0°) toward pin
- Right pin (0°): Label should face LEFT (180°) toward pin
"""

import pytest
import subprocess
import tempfile
import shutil
from pathlib import Path
from kicad_sch_api import Schematic


def calculate_expected_label_angle(pin_position, component_position):
    """
    Calculate the expected label angle based on pin position relative to component.

    Returns angle that label should face to point TOWARD the pin.
    """
    dx = pin_position[0] - component_position[0]
    dy = pin_position[1] - component_position[1]

    # Determine pin direction relative to component center
    # KiCad Y-axis increases downward, so we need to invert
    if abs(dx) > abs(dy):
        # Horizontal pin
        if dx > 0:
            # Pin on right side -> label should face LEFT (180°)
            return 180.0
        else:
            # Pin on left side -> label should face RIGHT (0°)
            return 0.0
    else:
        # Vertical pin
        if dy > 0:
            # Pin below component -> label should face UP (90°)
            return 90.0
        else:
            # Pin above component -> label should face DOWN (270°)
            return 270.0


@pytest.fixture
def temp_circuit_dir():
    """Create temporary directory for test circuits."""
    tmpdir = tempfile.mkdtemp(prefix="circuit_test_")
    yield Path(tmpdir)
    shutil.rmtree(tmpdir)


def test_label_orientation_resistor_top_pin(temp_circuit_dir):
    """
    Test hierarchical label orientation on top pin of resistor.

    Issue #457: Label should face DOWN (270°) toward top pin.
    Currently fails because label faces UP (90°) away from pin.
    """
    # Create test circuit
    circuit_code = '''
from circuit_synth import circuit, Component, Net

@circuit(name="test_top_pin")
def test_top_pin():
    """Test circuit with label on top pin."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    data = Net("DATA")
    r1[2] += data  # Pin 2 is top pin of resistor

if __name__ == "__main__":
    circuit_obj = test_top_pin()
    circuit_obj.generate_kicad_project(
        project_name="test_top_pin",
        placement_algorithm="hierarchical",
        generate_pcb=False
    )
'''

    # Write circuit file
    circuit_file = temp_circuit_dir / "test_top_pin.py"
    circuit_file.write_text(circuit_code)

    # Generate circuit
    result = subprocess.run(
        ["uv", "run", str(circuit_file)],
        cwd=temp_circuit_dir,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Circuit generation failed: {result.stderr}"

    # Load schematic
    schematic_file = temp_circuit_dir / "test_top_pin" / "test_top_pin.kicad_sch"
    assert schematic_file.exists(), "Schematic file not generated"

    sch = Schematic.load(str(schematic_file))

    # Find R1 component
    r1 = next(c for c in sch.components if c.reference == "R1")

    # Get pin 2 position (top pin)
    pins = sch.list_component_pins("R1")
    pin2_info = next(p for p in pins if p[0] == "2")
    pin2_pos = pin2_info[1]  # Point object with x, y

    # Find DATA hierarchical label
    data_labels = [l for l in sch.hierarchical_labels if l.text == "DATA"]
    assert len(data_labels) == 1, f"Expected 1 DATA label, found {len(data_labels)}"

    label = data_labels[0]

    # Calculate expected angle
    expected_angle = calculate_expected_label_angle(
        (pin2_pos.x, pin2_pos.y),
        (r1.position.x, r1.position.y)
    )

    # Verify label orientation
    assert label.rotation == expected_angle, (
        f"Label rotation {label.rotation}° should be {expected_angle}° "
        f"to face toward pin at ({pin2_pos.x}, {pin2_pos.y}). "
        f"Component R1 at {r1.position}. "
        f"Issue #457: Label faces away from pin instead of toward it."
    )


def test_label_orientation_resistor_bottom_pin(temp_circuit_dir):
    """
    Test hierarchical label orientation on bottom pin of resistor.

    Issue #457: Label should face UP (90°) toward bottom pin.
    """
    circuit_code = '''
from circuit_synth import circuit, Component, Net

@circuit(name="test_bottom_pin")
def test_bottom_pin():
    """Test circuit with label on bottom pin."""
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    data = Net("DATA")
    r1[1] += data  # Pin 1 is bottom pin of resistor

if __name__ == "__main__":
    circuit_obj = test_bottom_pin()
    circuit_obj.generate_kicad_project(
        project_name="test_bottom_pin",
        placement_algorithm="hierarchical",
        generate_pcb=False
    )
'''

    circuit_file = temp_circuit_dir / "test_bottom_pin.py"
    circuit_file.write_text(circuit_code)

    result = subprocess.run(
        ["uv", "run", str(circuit_file)],
        cwd=temp_circuit_dir,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Circuit generation failed: {result.stderr}"

    schematic_file = temp_circuit_dir / "test_bottom_pin" / "test_bottom_pin.kicad_sch"
    sch = Schematic.load(str(schematic_file))

    r1 = next(c for c in sch.components if c.reference == "R1")
    pins = sch.list_component_pins("R1")
    pin1_info = next(p for p in pins if p[0] == "1")
    pin1_pos = pin1_info[1]

    data_labels = [l for l in sch.hierarchical_labels if l.text == "DATA"]
    assert len(data_labels) == 1
    label = data_labels[0]

    expected_angle = calculate_expected_label_angle(
        (pin1_pos.x, pin1_pos.y),
        (r1.position.x, r1.position.y)
    )

    assert label.rotation == expected_angle, (
        f"Label rotation {label.rotation}° should be {expected_angle}° "
        f"to face toward pin at ({pin1_pos.x}, {pin1_pos.y}). "
        f"Issue #457: Label faces away from pin instead of toward it."
    )


def test_label_orientation_comprehensive(temp_circuit_dir):
    """
    Test multiple hierarchical labels in comprehensive circuit.

    This is the actual Test 10 circuit that revealed Issue #457.
    """
    circuit_code = '''
from circuit_synth import circuit, Component, Net

@circuit(name="comprehensive_test")
def comprehensive_test():
    """Comprehensive test with multiple components and nets."""
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
    circuit_obj = comprehensive_test()
    circuit_obj.generate_kicad_project(
        project_name="comprehensive_test",
        placement_algorithm="hierarchical",
        generate_pcb=False
    )
'''

    circuit_file = temp_circuit_dir / "comprehensive_test.py"
    circuit_file.write_text(circuit_code)

    result = subprocess.run(
        ["uv", "run", str(circuit_file)],
        cwd=temp_circuit_dir,
        capture_output=True,
        text=True
    )
    assert result.returncode == 0, f"Circuit generation failed: {result.stderr}"

    schematic_file = temp_circuit_dir / "comprehensive_test" / "comprehensive_test.kicad_sch"
    sch = Schematic.load(str(schematic_file))

    # Verify all DATA labels face their connected pins
    data_labels = [l for l in sch.hierarchical_labels if l.text == "DATA"]
    assert len(data_labels) == 2, f"Expected 2 DATA labels (R1, C1), found {len(data_labels)}"

    # Test each label
    for label in data_labels:
        # Find which component this label is closest to
        label_pos = label.position

        # Find nearest component pin
        min_distance = float('inf')
        nearest_component = None
        nearest_pin = None

        for comp in sch.components:
            if comp.reference.startswith("#PWR"):
                continue

            pins = sch.list_component_pins(comp.reference)
            for pin_num, pin_pos in pins:
                distance = ((label_pos.x - pin_pos.x)**2 +
                           (label_pos.y - pin_pos.y)**2)**0.5
                if distance < min_distance:
                    min_distance = distance
                    nearest_component = comp
                    nearest_pin = pin_pos

        # Calculate expected angle
        expected_angle = calculate_expected_label_angle(
            (nearest_pin.x, nearest_pin.y),
            (nearest_component.position.x, nearest_component.position.y)
        )

        assert label.rotation == expected_angle, (
            f"Label '{label.text}' at {label.position} rotation {label.rotation}° "
            f"should be {expected_angle}° to face toward {nearest_component.reference} "
            f"pin at ({nearest_pin.x}, {nearest_pin.y}). "
            f"Issue #457: Label faces away from pin."
        )


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
