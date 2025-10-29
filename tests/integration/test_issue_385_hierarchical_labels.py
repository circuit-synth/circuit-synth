#!/usr/bin/env python3
"""
Test for Issue #385: Missing hierarchical labels on component pins in generated schematics.

The schematic writer was using a non-existent API (net.connections) instead of the correct
API (net.pins). This test validates that hierarchical labels are properly generated.

Test strategy:
1. Create a simple resistor divider circuit with named nets
2. Generate KiCad schematic
3. Verify hierarchical_label elements exist in the .kicad_sch file
4. Verify label names match the net names
5. Verify labels appear for each pin connected to a net
"""

import tempfile
from pathlib import Path

import pytest

from circuit_synth import circuit, Component, Net


class TestIssue385HierarchicalLabels:
    """Test Issue #385: Hierarchical labels missing from generated schematics"""

    def test_simple_resistor_divider_hierarchical_labels(self, tmp_path):
        """
        Test that a simple resistor divider generates hierarchical labels for non-power nets.

        Circuit structure:
        - R1 (1k): pin 1 = VIN_5V, pin 2 = VOUT_3V3
        - R2 (2k): pin 1 = VOUT_3V3, pin 2 = GND_SENSE (NOT GND)

        Expected hierarchical labels in .kicad_sch:
        - VIN_5V (on R1 pin 1)
        - VOUT_3V3 (on R1 pin 2 and R2 pin 1)
        - GND_SENSE (on R2 pin 2) - not GND because GND is auto-detected as power net

        This test verifies the fix for Issue #385:
        The circuit loader was looking for "connections" key in JSON nets,
        but NetlistExporter uses "nodes" key instead.
        """

        # Define resistor divider circuit
        @circuit(name="resistor_divider")
        def resistor_divider():
            r1 = Component(
                symbol="Device:R",
                ref="R1",
                value="1k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            r2 = Component(
                symbol="Device:R",
                ref="R2",
                value="2k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )

            # Create nets (avoid names that trigger power net auto-detection)
            # Use non-power net names to ensure hierarchical labels are created
            vin_in = Net("VIN_IN", is_power=False)
            vout_div = Net("VOUT_DIV", is_power=False)
            gnd_ref = Net("GND_REF", is_power=False)

            # Connect R1: pin 1 to VIN_IN, pin 2 to VOUT_DIV
            vin_in += r1[1]
            vout_div += r1[2]

            # Connect R2: pin 1 to VOUT_DIV, pin 2 to GND_REF
            vout_div += r2[1]
            gnd_ref += r2[2]

        # Create circuit instance
        test_circuit = resistor_divider()

        # Generate KiCad project
        project_dir = tmp_path / "resistor_divider"
        result = test_circuit.generate_kicad_project(
            str(project_dir), generate_pcb=False, force_regenerate=True
        )

        # Verify generation succeeded
        assert result is not False, "KiCad project generation should succeed"

        # Verify schematic file exists
        schematic_file = project_dir / "resistor_divider.kicad_sch"
        assert schematic_file.exists(), f"Schematic file should exist at {schematic_file}"

        # Read schematic content
        sch_content = schematic_file.read_text()

        # Verify hierarchical_label elements exist for each net
        # Each net should have labels on all connected pins

        # VIN_IN should appear once (R1 pin 1)
        vin_in_labels = sch_content.count('hierarchical_label "VIN_IN"')
        assert vin_in_labels >= 1, (
            f"Expected at least 1 hierarchical label for VIN_IN, found {vin_in_labels}. "
            f"This indicates Issue #385 is not fixed: net loader not reading 'nodes' key from JSON."
        )

        # VOUT_DIV should appear twice (R1 pin 2 and R2 pin 1)
        vout_div_labels = sch_content.count('hierarchical_label "VOUT_DIV"')
        assert vout_div_labels >= 2, (
            f"Expected at least 2 hierarchical labels for VOUT_DIV, found {vout_div_labels}. "
            f"This indicates Issue #385 is not fixed: net loader not reading 'nodes' key from JSON."
        )

        # GND_REF should appear once (R2 pin 2)
        gnd_ref_labels = sch_content.count('hierarchical_label "GND_REF"')
        assert gnd_ref_labels >= 1, (
            f"Expected at least 1 hierarchical label for GND_REF, found {gnd_ref_labels}. "
            f"This indicates Issue #385 is not fixed: net loader not reading 'nodes' key from JSON."
        )

        print(f"\n✅ Hierarchical labels verified:")
        print(f"   - VIN_IN labels: {vin_in_labels}")
        print(f"   - VOUT_DIV labels: {vout_div_labels}")
        print(f"   - GND_REF labels: {gnd_ref_labels}")

    def test_two_resistors_connected_hierarchical_labels(self, tmp_path):
        """
        Test the exact fixture from test_10_generate_with_net.

        This validates the same scenario as the bidirectional test but
        focuses specifically on hierarchical label generation.

        Circuit: R1 and R2 connected via NET1
        Expected: 2 hierarchical_label "NET1" elements (one on each component)
        """

        @circuit(name="two_resistors_connected")
        def two_resistors_connected():
            r1 = Component(
                symbol="Device:R",
                ref="R1",
                value="10k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            r2 = Component(
                symbol="Device:R",
                ref="R2",
                value="4.7k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )

            # Connect both resistors' pin 1 to NET1
            net1 = Net(name="NET1")
            net1 += r1[1]
            net1 += r2[1]

        # Create circuit instance
        test_circuit = two_resistors_connected()

        # Generate KiCad project
        project_dir = tmp_path / "two_resistors_connected"
        result = test_circuit.generate_kicad_project(
            str(project_dir), generate_pcb=False, force_regenerate=True
        )

        # Verify generation succeeded
        assert result is not False, "KiCad project generation should succeed"

        # Verify schematic file exists
        schematic_file = project_dir / "two_resistors_connected.kicad_sch"
        assert schematic_file.exists(), f"Schematic file should exist at {schematic_file}"

        # Read schematic content
        sch_content = schematic_file.read_text()

        # Verify hierarchical labels exist for NET1
        net1_labels = sch_content.count('hierarchical_label "NET1"')
        assert net1_labels >= 2, (
            f"Expected at least 2 NET1 hierarchical labels (one per connected pin), "
            f"found {net1_labels}. "
            f"This indicates Issue #385 is not fixed: net.connections API is wrong."
        )

        print(f"\n✅ NET1 hierarchical labels verified: {net1_labels}")

    def test_net_pins_iteration(self):
        """
        Unit test: Verify that Net.pins contains Pin objects with correct structure.

        This validates the API that should be used in schematic_writer.py:
        - net.pins returns frozenset[Pin]
        - Pin objects have _component.ref and num attributes
        """

        @circuit(name="test_net_structure")
        def test_circuit():
            r1 = Component(
                symbol="Device:R",
                ref="R1",
                value="1k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            r2 = Component(
                symbol="Device:R",
                ref="R2",
                value="2k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )

            net = Net(name="TEST_NET")
            net += r1[1]
            net += r2[1]

        test_circuit_obj = test_circuit()

        # Get the net from the circuit's nets dictionary
        assert "TEST_NET" in test_circuit_obj.nets, "TEST_NET should exist in circuit"
        test_net = test_circuit_obj.nets["TEST_NET"]

        # Verify net.pins structure
        pins = test_net.pins
        assert isinstance(pins, frozenset), "net.pins should return frozenset"
        assert len(pins) == 2, f"Expected 2 pins, got {len(pins)}"

        # Verify each pin has required attributes
        for pin in pins:
            assert hasattr(pin, "_component"), "Pin should have _component attribute"
            assert hasattr(pin, "num"), "Pin should have num attribute"
            assert hasattr(
                pin._component, "ref"
            ), "Pin._component should have ref attribute"

            comp_ref = pin._component.ref
            pin_num = pin.num
            assert comp_ref in ["R1", "R2"], f"Component ref should be R1 or R2, got {comp_ref}"
            assert pin_num == "1", f"Pin num should be '1', got {pin_num}"

        print(f"\n✅ Net.pins API verified:")
        print(f"   - Pins in net: {len(pins)}")
        for pin in pins:
            print(f"   - {pin._component.ref}[{pin.num}]")
