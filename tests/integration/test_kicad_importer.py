"""
Unit tests for KiCad project import API.

Tests the import_kicad_project() function and its helper functions.
"""

import json
import pytest
from pathlib import Path
from circuit_synth.kicad.importer import (
    import_kicad_project,
    load_kicad_json,
    _json_to_models_circuit,
    _convert_models_circuit_to_api_circuit,
)


class TestLoadKicadJson:
    """Test JSON loading from various input formats."""

    def test_load_from_json_file(self, tmp_path):
        """Test loading from .json netlist file."""
        # Create test JSON file
        json_data = {
            "name": "test_circuit",
            "components": {
                "R1": {
                    "ref": "R1",
                    "symbol": "Device:R",
                    "value": "10k",
                    "footprint": "Resistor_SMD:R_0603_1608Metric",
                }
            },
            "nets": {},
        }
        json_path = tmp_path / "test.json"
        with open(json_path, "w") as f:
            json.dump(json_data, f)

        # Load JSON
        loaded_data = load_kicad_json(json_path)

        # Verify
        assert loaded_data["name"] == "test_circuit"
        assert "R1" in loaded_data["components"]
        assert loaded_data["components"]["R1"]["value"] == "10k"

    def test_load_nonexistent_file_raises_error(self):
        """Test that loading nonexistent file raises FileNotFoundError."""
        with pytest.raises(FileNotFoundError):
            load_kicad_json("nonexistent.json")


class TestJsonToModelsCircuit:
    """Test conversion from JSON to models.Circuit."""

    def test_convert_simple_circuit(self):
        """Test converting circuit with single component."""
        json_data = {
            "name": "simple",
            "components": {
                "R1": {
                    "ref": "R1",
                    "symbol": "Device:R",
                    "value": "10k",
                    "footprint": "Resistor_SMD:R_0603_1608Metric",
                }
            },
            "nets": {},
        }

        circuit = _json_to_models_circuit(json_data)

        assert circuit.name == "simple"
        assert len(circuit.components) == 1
        # models.Circuit.components is a list, not a dict
        assert circuit.components[0].reference == "R1"
        assert circuit.components[0].value == "10k"

    def test_convert_circuit_with_nets(self):
        """Test converting circuit with net connections."""
        json_data = {
            "name": "with_nets",
            "components": {
                "R1": {"ref": "R1", "symbol": "Device:R", "value": "10k", "footprint": ""},
                "R2": {"ref": "R2", "symbol": "Device:R", "value": "4.7k", "footprint": ""},
            },
            "nets": {
                "NET1": [
                    {"component": "R1", "pin_id": 1},
                    {"component": "R2", "pin_id": 1},
                ]
            },
        }

        circuit = _json_to_models_circuit(json_data)

        assert len(circuit.components) == 2
        assert len(circuit.nets) == 1
        assert circuit.nets[0].name == "NET1"
        # models.Net uses 'connections' attribute (not 'nodes')
        assert len(circuit.nets[0].connections) == 2
        assert ("R1", "1") in circuit.nets[0].connections
        assert ("R2", "1") in circuit.nets[0].connections


class TestConvertModelsCircuitToApiCircuit:
    """Test conversion from models.Circuit to API Circuit."""

    def test_convert_simple_circuit(self):
        """Test converting simple circuit with one component."""
        from circuit_synth.tools.utilities.models import (
            Circuit as ModelsCircuit,
            Component as ModelsComponent,
        )

        # Create models.Circuit
        models_circuit = ModelsCircuit(
            name="test",
            components=[
                ModelsComponent(
                    reference="R1",
                    lib_id="Device:R",
                    value="10k",
                    footprint="Resistor_SMD:R_0603_1608Metric",
                )
            ],
            nets=[],
        )

        # Convert to API Circuit
        circuit = _convert_models_circuit_to_api_circuit(models_circuit)

        # Verify
        assert circuit.name == "test"
        assert len(circuit.components) == 1
        # components is a dict, so access by reference
        assert circuit.components["R1"].ref == "R1"
        assert circuit.components["R1"].value == "10k"
        assert circuit.components["R1"].symbol == "Device:R"

    def test_convert_circuit_with_nets(self):
        """Test converting circuit with net connections."""
        from circuit_synth.tools.utilities.models import (
            Circuit as ModelsCircuit,
            Component as ModelsComponent,
            Net as ModelsNet,
        )

        # Create models.Circuit with nets
        models_circuit = ModelsCircuit(
            name="with_nets",
            components=[
                ModelsComponent(
                    reference="R1",
                    lib_id="Device:R",
                    value="10k",
                    footprint="",
                ),
                ModelsComponent(
                    reference="R2",
                    lib_id="Device:R",
                    value="4.7k",
                    footprint="",
                ),
            ],
            nets=[
                ModelsNet(
                    name="NET1",
                    connections=[("R1", "1"), ("R2", "1")],
                )
            ],
        )

        # Convert to API Circuit
        circuit = _convert_models_circuit_to_api_circuit(models_circuit)

        # Verify components
        assert len(circuit.components) == 2
        # Find components by ref - circuit.components is a dict, iterate over values
        comp_refs = [c.ref for c in circuit.components.values()]
        assert "R1" in comp_refs
        assert "R2" in comp_refs

        # Verify nets - nets is a list of Net objects
        assert len(list(circuit.nets.values())) >= 1
        # NET1 should be in the nets dict
        assert "NET1" in circuit.nets
        # Note: Actual net connection validation depends on Component pin setup


class TestImportKicadProject:
    """Integration tests for main import_kicad_project() function."""

    def test_import_from_json(self, tmp_path):
        """Test importing from JSON file (end-to-end)."""
        # Create test JSON file
        json_data = {
            "name": "test_project",
            "components": {
                "R1": {
                    "ref": "R1",
                    "symbol": "Device:R",
                    "value": "10k",
                    "footprint": "Resistor_SMD:R_0603_1608Metric",
                },
                "C1": {
                    "ref": "C1",
                    "symbol": "Device:C",
                    "value": "100nF",
                    "footprint": "Capacitor_SMD:C_0603_1608Metric",
                },
            },
            "nets": {
                "NET1": [
                    {"component": "R1", "pin_id": 1},
                    {"component": "C1", "pin_id": 1},
                ]
            },
        }
        json_path = tmp_path / "test_project.json"
        with open(json_path, "w") as f:
            json.dump(json_data, f)

        # Import project
        circuit = import_kicad_project(json_path)

        # Verify
        assert circuit.name == "test_project"
        assert len(circuit.components) == 2
        # Find components by ref - circuit.components is a dict, iterate over values
        comp_map = {c.ref: c for c in circuit.components.values()}
        assert "R1" in comp_map
        assert "C1" in comp_map
        assert comp_map["R1"].value == "10k"
        assert comp_map["C1"].value == "100nF"

    def test_import_nonexistent_raises_error(self):
        """Test that importing nonexistent project raises error."""
        with pytest.raises(FileNotFoundError):
            import_kicad_project("nonexistent_project.json")

    def test_import_preserves_component_properties(self, tmp_path):
        """Test that all component properties are preserved."""
        json_data = {
            "name": "properties_test",
            "components": {
                "L1": {
                    "ref": "L1",
                    "symbol": "Device:L",
                    "value": "100uH",
                    "footprint": "Inductor_SMD:L_0805_2012Metric",
                }
            },
            "nets": {},
        }
        json_path = tmp_path / "props.json"
        with open(json_path, "w") as f:
            json.dump(json_data, f)

        circuit = import_kicad_project(json_path)

        # Find L1 component - circuit.components is a dict, iterate over values
        l1 = next(c for c in circuit.components.values() if c.ref == "L1")
        assert l1.ref == "L1"
        assert l1.symbol == "Device:L"
        assert l1.value == "100uH"
        assert l1.footprint == "Inductor_SMD:L_0805_2012Metric"


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_empty_circuit(self, tmp_path):
        """Test importing circuit with no components."""
        json_data = {"name": "empty", "components": {}, "nets": {}}
        json_path = tmp_path / "empty.json"
        with open(json_path, "w") as f:
            json.dump(json_data, f)

        circuit = import_kicad_project(json_path)

        assert circuit.name == "empty"
        assert len(circuit.components) == 0
        assert len(circuit.nets) == 0  # nets is a dict

    def test_circuit_with_disconnected_components(self, tmp_path):
        """Test importing circuit where components have no connections."""
        json_data = {
            "name": "disconnected",
            "components": {
                "R1": {"ref": "R1", "symbol": "Device:R", "value": "10k", "footprint": ""},
                "R2": {"ref": "R2", "symbol": "Device:R", "value": "10k", "footprint": ""},
            },
            "nets": {},  # No connections
        }
        json_path = tmp_path / "disconnected.json"
        with open(json_path, "w") as f:
            json.dump(json_data, f)

        circuit = import_kicad_project(json_path)

        assert len(circuit.components) == 2
        assert len(circuit.nets) == 0

    def test_malformed_json_raises_error(self, tmp_path):
        """Test that malformed JSON raises ValueError."""
        json_path = tmp_path / "malformed.json"
        with open(json_path, "w") as f:
            f.write("{invalid json")

        with pytest.raises(ValueError):
            import_kicad_project(json_path)
