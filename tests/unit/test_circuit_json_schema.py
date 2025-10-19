#!/usr/bin/env python3
"""
Unit tests for Circuit JSON schema conversion.

Tests the transformation from Circuit.to_dict() format to circuit-synth JSON schema format.
This covers the schema conversion logic in Circuit.to_circuit_synth_json() method.
"""

import json
import tempfile
from pathlib import Path

import pytest

from circuit_synth.tools.utilities.models import Circuit, Component, Net


class TestCircuitJSONSchemaConversion:
    """Test suite for Circuit → JSON schema transformation."""

    def test_components_list_to_dict_transformation(self):
        """Test transforming components from list format to dict format."""
        # Create circuit with component list
        components = [
            Component(
                reference="R1",
                lib_id="Device:R",
                value="10k",
                footprint="Resistor_SMD:R_0603_1608Metric",
                position=(10.0, 20.0),
            ),
            Component(
                reference="C1",
                lib_id="Device:C",
                value="100nF",
                footprint="Capacitor_SMD:C_0603_1608Metric",
                position=(30.0, 20.0),
            ),
        ]
        nets = [Net(name="VCC", connections=[("R1", "1"), ("C1", "1")])]

        circuit = Circuit(
            name="test_circuit",
            components=components,
            nets=nets,
            schematic_file="test.kicad_sch",
        )

        # Convert to JSON schema format
        json_data = circuit.to_circuit_synth_json()

        # Verify components is a dict keyed by reference
        assert isinstance(json_data["components"], dict)
        assert "R1" in json_data["components"]
        assert "C1" in json_data["components"]

        # Verify component structure
        r1 = json_data["components"]["R1"]
        assert r1["ref"] == "R1"
        assert r1["symbol"] == "Device:R"
        assert r1["value"] == "10k"
        assert r1["footprint"] == "Resistor_SMD:R_0603_1608Metric"

    def test_nets_list_to_dict_transformation(self):
        """Test transforming nets from list format to dict format."""
        components = [
            Component(reference="R1", lib_id="Device:R", value="10k"),
            Component(reference="C1", lib_id="Device:C", value="100nF"),
        ]
        nets = [
            Net(name="VCC", connections=[("R1", "1")]),
            Net(name="OUT", connections=[("R1", "2"), ("C1", "1")]),
            Net(name="GND", connections=[("C1", "2")]),
        ]

        circuit = Circuit(
            name="test_rc",
            components=components,
            nets=nets,
            schematic_file="test.kicad_sch",
        )

        # Convert to JSON schema format
        json_data = circuit.to_circuit_synth_json()

        # Verify nets is a dict keyed by name
        assert isinstance(json_data["nets"], dict)
        assert "VCC" in json_data["nets"]
        assert "OUT" in json_data["nets"]
        assert "GND" in json_data["nets"]

        # Verify net structure - connections should be arrays
        vcc_connections = json_data["nets"]["VCC"]
        assert isinstance(vcc_connections, list)
        assert len(vcc_connections) == 1

        out_connections = json_data["nets"]["OUT"]
        assert len(out_connections) == 2

    def test_schema_field_mapping(self):
        """Test lib_id → symbol and other field mappings."""
        components = [
            Component(
                reference="U1",
                lib_id="MCU_ST_STM32F4:STM32F405RGTx",
                value="STM32F405",
                footprint="Package_QFP:LQFP-64_10x10mm_P0.5mm",
            )
        ]
        nets = []

        circuit = Circuit(
            name="test_mcu", components=components, nets=nets, schematic_file="mcu.kicad_sch"
        )

        json_data = circuit.to_circuit_synth_json()

        u1 = json_data["components"]["U1"]

        # Verify field mappings
        assert u1["symbol"] == "MCU_ST_STM32F4:STM32F405RGTx"  # lib_id → symbol
        assert u1["ref"] == "U1"  # reference → ref
        assert u1["value"] == "STM32F405"
        assert u1["footprint"] == "Package_QFP:LQFP-64_10x10mm_P0.5mm"

    def test_default_fields_added(self):
        """Test that missing fields get default values."""
        # Create minimal component (no optional fields)
        components = [Component(reference="R1", lib_id="Device:R", value="10k")]
        nets = []

        circuit = Circuit(
            name="minimal", components=components, nets=nets, schematic_file="min.kicad_sch"
        )

        json_data = circuit.to_circuit_synth_json()
        r1 = json_data["components"]["R1"]

        # Verify default fields exist
        assert "datasheet" in r1
        assert "description" in r1
        assert "properties" in r1
        assert "tstamps" in r1
        assert "pins" in r1

        # Verify default values
        assert r1["datasheet"] == ""
        assert r1["description"] == ""
        assert r1["properties"] == {}
        assert r1["tstamps"] == ""
        assert r1["pins"] == []

    def test_pin_format_transformation(self):
        """Test connection format: (ref, pin) → pin object."""
        components = [
            Component(reference="R1", lib_id="Device:R", value="10k"),
            Component(reference="R2", lib_id="Device:R", value="1k"),
        ]
        nets = [Net(name="VCC", connections=[("R1", "1"), ("R2", "1")])]

        circuit = Circuit(
            name="test_pins", components=components, nets=nets, schematic_file="test.kicad_sch"
        )

        json_data = circuit.to_circuit_synth_json()
        vcc_connections = json_data["nets"]["VCC"]

        # Verify pin format
        assert len(vcc_connections) == 2

        for conn in vcc_connections:
            assert "component" in conn
            assert "pin" in conn

            # Pin should be an object, not a simple value
            pin = conn["pin"]
            assert isinstance(pin, dict)
            assert "number" in pin
            assert "name" in pin
            assert "type" in pin

    def test_top_level_fields_present(self):
        """Test that all top-level JSON schema fields are present."""
        components = [Component(reference="R1", lib_id="Device:R", value="10k")]
        nets = [Net(name="VCC", connections=[("R1", "1")])]

        circuit = Circuit(
            name="full_test",
            components=components,
            nets=nets,
            schematic_file="full.kicad_sch",
        )

        json_data = circuit.to_circuit_synth_json()

        # Verify all required top-level fields
        required_fields = [
            "name",
            "description",
            "tstamps",
            "source_file",
            "components",
            "nets",
            "subcircuits",
            "annotations",
        ]

        for field in required_fields:
            assert field in json_data, f"Missing required field: {field}"

    def test_empty_circuit(self):
        """Test handling of empty circuit with no components."""
        components = []
        nets = []

        circuit = Circuit(
            name="empty", components=components, nets=nets, schematic_file="empty.kicad_sch"
        )

        json_data = circuit.to_circuit_synth_json()

        # Should still have valid structure
        assert json_data["name"] == "empty"
        assert json_data["components"] == {}
        assert json_data["nets"] == {}
        assert json_data["subcircuits"] == []

    def test_json_serializable(self):
        """Test that output is JSON serializable."""
        components = [
            Component(
                reference="R1",
                lib_id="Device:R",
                value="10k",
                position=(10.0, 20.0),
            )
        ]
        nets = [Net(name="VCC", connections=[("R1", "1")])]

        circuit = Circuit(
            name="serializable",
            components=components,
            nets=nets,
            schematic_file="test.kicad_sch",
        )

        json_data = circuit.to_circuit_synth_json()

        # Should be able to serialize to JSON without errors
        try:
            json_str = json.dumps(json_data, indent=2)
            assert len(json_str) > 0
        except (TypeError, ValueError) as e:
            pytest.fail(f"JSON serialization failed: {e}")

    def test_net_with_multiple_connections(self):
        """Test net with multiple component connections."""
        components = [
            Component(reference=f"R{i}", lib_id="Device:R", value="10k") for i in range(1, 6)
        ]
        # Net connecting 5 resistors
        nets = [
            Net(
                name="COMMON",
                connections=[("R1", "1"), ("R2", "1"), ("R3", "1"), ("R4", "1"), ("R5", "1")],
            )
        ]

        circuit = Circuit(
            name="multi_conn",
            components=components,
            nets=nets,
            schematic_file="multi.kicad_sch",
        )

        json_data = circuit.to_circuit_synth_json()

        # Verify all connections preserved
        common_net = json_data["nets"]["COMMON"]
        assert len(common_net) == 5

        # Verify component references
        refs = {conn["component"] for conn in common_net}
        assert refs == {"R1", "R2", "R3", "R4", "R5"}

    def test_pin_number_as_string(self):
        """Test that pin numbers are converted to strings."""
        components = [Component(reference="R1", lib_id="Device:R", value="10k")]
        # Pin numbers could be integers or strings from KiCad
        nets = [Net(name="VCC", connections=[("R1", 1)])]  # Integer pin number

        circuit = Circuit(
            name="pin_test", components=components, nets=nets, schematic_file="test.kicad_sch"
        )

        json_data = circuit.to_circuit_synth_json()
        vcc_conn = json_data["nets"]["VCC"][0]

        # Pin number should be string in JSON
        assert isinstance(vcc_conn["pin"]["number"], str)
        assert vcc_conn["pin"]["number"] == "1"

    def test_special_characters_in_net_names(self):
        """Test handling of special characters in net names."""
        components = [
            Component(reference="R1", lib_id="Device:R", value="10k"),
            Component(reference="R2", lib_id="Device:R", value="1k"),
        ]
        # Net names with special characters
        nets = [
            Net(name="/VCC_3V3", connections=[("R1", "1")]),
            Net(name="Net-(R1-Pad2)", connections=[("R1", "2"), ("R2", "1")]),
            Net(name="~{RESET}", connections=[("R2", "2")]),
        ]

        circuit = Circuit(
            name="special_chars",
            components=components,
            nets=nets,
            schematic_file="special.kicad_sch",
        )

        json_data = circuit.to_circuit_synth_json()

        # Verify special character net names are preserved
        assert "/VCC_3V3" in json_data["nets"]
        assert "Net-(R1-Pad2)" in json_data["nets"]
        assert "~{RESET}" in json_data["nets"]

    def test_component_without_footprint(self):
        """Test component with missing footprint field."""
        components = [
            Component(reference="TP1", lib_id="Connector:TestPoint", value="", footprint="")
        ]
        nets = []

        circuit = Circuit(
            name="no_footprint",
            components=components,
            nets=nets,
            schematic_file="test.kicad_sch",
        )

        json_data = circuit.to_circuit_synth_json()
        tp1 = json_data["components"]["TP1"]

        # Should still have footprint field, even if empty
        assert "footprint" in tp1
        assert tp1["footprint"] == ""

    def test_source_file_preserved(self):
        """Test that source_file is correctly set from schematic_file."""
        components = [Component(reference="R1", lib_id="Device:R", value="10k")]
        nets = []

        circuit = Circuit(
            name="source_test",
            components=components,
            nets=nets,
            schematic_file="my_board_v2.kicad_sch",
        )

        json_data = circuit.to_circuit_synth_json()

        assert json_data["source_file"] == "my_board_v2.kicad_sch"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
