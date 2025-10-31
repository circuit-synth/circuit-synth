#!/usr/bin/env python3
"""
Unit tests for refactored KiCadToPythonSyncer with JSON input.

Tests the new JSON-first architecture where JSON is the canonical format
instead of direct .net file parsing.
"""

import json
import warnings
from pathlib import Path
from unittest.mock import Mock, patch

import pytest

from circuit_synth.tools.kicad_integration.kicad_to_python_sync import (
    KiCadToPythonSyncer,
)


class TestKiCadToPythonSyncerRefactored:
    """Unit tests for JSON-first KiCadToPythonSyncer"""

    def test_accept_json_file_path(self, tmp_path):
        """Test 1: Accept .json file path as input."""
        # Create sample JSON netlist
        json_file = tmp_path / "test.json"
        json_data = {
            "name": "test_circuit",
            "components": {
                "R1": {
                    "ref": "R1",
                    "symbol": "Device:R",
                    "value": "10k",
                    "footprint": "R_0603",
                }
            },
            "nets": {},
            "source_file": "test.kicad_sch",
        }
        json_file.write_text(json.dumps(json_data, indent=2))

        # Create syncer with JSON path (should not raise warnings)
        with warnings.catch_warnings():
            warnings.simplefilter("error")  # Turn warnings into errors
            syncer = KiCadToPythonSyncer(str(json_file), str(tmp_path / "output.py"))

        # Verify JSON was loaded
        assert syncer.json_path == json_file
        assert syncer.json_data["name"] == "test_circuit"
        assert len(syncer.json_data["components"]) == 1

    def test_accept_kicad_pro_legacy_with_warning(self, tmp_path):
        """Test 2: Accept .kicad_pro with deprecation warning."""
        # Create minimal KiCad project structure
        kicad_pro = tmp_path / "test.kicad_pro"
        kicad_pro.write_text("{}")

        kicad_sch = tmp_path / "test.kicad_sch"
        kicad_sch.write_text("(kicad_sch)")

        # Create JSON that would be found
        json_file = tmp_path / "test.json"
        json_data = {"name": "test", "components": {}, "nets": {}}
        json_file.write_text(json.dumps(json_data))

        # Should trigger deprecation warning
        with pytest.warns(DeprecationWarning, match="Passing KiCad project directly"):
            syncer = KiCadToPythonSyncer(str(kicad_pro), str(tmp_path / "output.py"))

        # Verify JSON was loaded (fallback path)
        assert syncer.json_path == json_file

    def test_find_existing_json(self, tmp_path):
        """Test 3: _find_or_generate_json() finds existing JSON file."""
        # Create KiCad project and existing JSON
        kicad_pro = tmp_path / "test.kicad_pro"
        kicad_pro.write_text("{}")

        json_file = tmp_path / "test.json"
        json_file.write_text('{"name": "test", "components": {}, "nets": {}}')

        # Create syncer instance (uninitialized)
        syncer = KiCadToPythonSyncer.__new__(KiCadToPythonSyncer)

        # Should find existing JSON
        found_json = syncer._find_or_generate_json(kicad_pro)
        assert found_json == json_file

    def test_generate_json_when_missing(self, tmp_path):
        """Test 4: _find_or_generate_json() generates JSON when missing."""
        kicad_pro = tmp_path / "test.kicad_pro"
        kicad_pro.write_text("{}")

        # Create syncer instance
        syncer = KiCadToPythonSyncer.__new__(KiCadToPythonSyncer)

        # Mock _export_kicad_to_json
        expected_json = tmp_path / "test.json"
        with patch.object(
            syncer, "_export_kicad_to_json", return_value=expected_json
        ) as mock_export:
            result = syncer._find_or_generate_json(kicad_pro)

            assert result == expected_json
            mock_export.assert_called_once_with(kicad_pro)

    def test_export_kicad_to_json_integration(self, tmp_path):
        """Test 5: _export_kicad_to_json() uses KiCadSchematicParser."""
        # Create minimal project structure
        kicad_pro = tmp_path / "test.kicad_pro"
        kicad_pro.write_text("{}")

        kicad_sch = tmp_path / "test.kicad_sch"
        kicad_sch.write_text("(kicad_sch)")

        # Mock KiCadSchematicParser class
        mock_parser_instance = Mock()
        mock_parser_instance.parse_and_export.return_value = {
            "success": True,
            "json_path": str(tmp_path / "test.json"),
        }

        mock_parser_class = Mock(return_value=mock_parser_instance)

        syncer = KiCadToPythonSyncer.__new__(KiCadToPythonSyncer)

        # Patch the import at the point where it's used
        with patch.dict(
            "sys.modules",
            {
                "circuit_synth.tools.utilities.kicad_schematic_parser": Mock(
                    KiCadSchematicParser=mock_parser_class
                )
            },
        ):
            result = syncer._export_kicad_to_json(kicad_pro)

            assert result == tmp_path / "test.json"
            mock_parser_instance.parse_and_export.assert_called_once()

    def test_load_json_success(self, tmp_path):
        """Test 6: _load_json() loads valid JSON file."""
        json_file = tmp_path / "test.json"
        json_data = {"name": "test", "components": {"R1": {}}, "nets": {}}
        json_file.write_text(json.dumps(json_data))

        syncer = KiCadToPythonSyncer.__new__(KiCadToPythonSyncer)
        syncer.json_path = json_file

        loaded = syncer._load_json()

        assert loaded == json_data
        assert loaded["name"] == "test"
        assert "R1" in loaded["components"]

    def test_load_json_file_not_found(self, tmp_path):
        """Test 7: _load_json() raises error for missing file."""
        syncer = KiCadToPythonSyncer.__new__(KiCadToPythonSyncer)
        syncer.json_path = tmp_path / "nonexistent.json"

        with pytest.raises(FileNotFoundError, match="JSON netlist not found"):
            syncer._load_json()

    def test_load_json_invalid_format(self, tmp_path):
        """Test 8: _load_json() raises error for malformed JSON."""
        json_file = tmp_path / "invalid.json"
        json_file.write_text("{invalid json content")

        syncer = KiCadToPythonSyncer.__new__(KiCadToPythonSyncer)
        syncer.json_path = json_file

        with pytest.raises(ValueError, match="Invalid JSON format"):
            syncer._load_json()

    def test_json_to_circuits_conversion(self, tmp_path):
        """Test 9: _json_to_circuits() converts JSON to Circuit objects."""
        json_data = {
            "name": "test_circuit",
            "components": {
                "R1": {
                    "ref": "R1",
                    "symbol": "Device:R",
                    "value": "10k",
                    "footprint": "R_0603",
                },
                "C1": {
                    "ref": "C1",
                    "symbol": "Device:C",
                    "value": "100nF",
                    "footprint": "C_0603",
                },
            },
            "nets": {
                "VCC": [
                    {"component": "R1", "pin": {"number": "1"}},
                    {"component": "C1", "pin": {"number": "1"}},
                ],
                "GND": [{"component": "C1", "pin": {"number": "2"}}],
            },
            "source_file": "test.kicad_sch",
        }

        syncer = KiCadToPythonSyncer.__new__(KiCadToPythonSyncer)
        syncer.json_data = json_data

        circuits = syncer._json_to_circuits()

        # Verify circuit structure
        assert len(circuits) == 1
        assert "test_circuit" in circuits

        circuit = circuits["test_circuit"]
        assert len(circuit.components) == 2
        assert len(circuit.nets) == 2

        # Verify component data
        refs = [c.reference for c in circuit.components]
        assert "R1" in refs
        assert "C1" in refs

        # Verify component details
        r1 = next(c for c in circuit.components if c.reference == "R1")
        assert r1.lib_id == "Device:R"
        assert r1.value == "10k"
        assert r1.footprint == "R_0603"

        # Verify net data
        net_names = [n.name for n in circuit.nets]
        assert "VCC" in net_names
        assert "GND" in net_names

        # Verify net connections
        vcc_net = next(n for n in circuit.nets if n.name == "VCC")
        assert len(vcc_net.connections) == 2
        assert ("R1", "1") in vcc_net.connections
        assert ("C1", "1") in vcc_net.connections

    def test_unsupported_input_type(self, tmp_path):
        """Test 10: Reject unsupported file types."""
        txt_file = tmp_path / "test.txt"
        txt_file.write_text("not a valid input")

        with pytest.raises(ValueError, match="Unsupported input"):
            KiCadToPythonSyncer(str(txt_file), str(tmp_path / "output.py"))

    def test_update_json_from_schematic_regenerates_json(self, tmp_path):
        """Test 11: update_json_from_schematic() regenerates JSON from .kicad_sch"""
        # Create a minimal KiCad project structure
        kicad_pro = tmp_path / "test.kicad_pro"
        kicad_pro.write_text("{}")

        kicad_sch = tmp_path / "test.kicad_sch"
        kicad_sch.write_text("(kicad_sch (version 6) (generator kicad))")

        # Create JSON file
        json_file = tmp_path / "test.json"
        json_file.write_text('{"name": "test", "components": {}, "nets": {}}')

        # Create syncer
        syncer = KiCadToPythonSyncer.__new__(KiCadToPythonSyncer)
        syncer.json_path = json_file
        syncer.kicad_project = kicad_pro

        # Mock KiCadParser to avoid actual parsing
        mock_circuit = Mock()
        mock_circuit.name = "test"
        mock_circuit.components = []  # Empty list of components
        mock_circuit.nets = []  # Empty list of nets
        mock_circuit.to_circuit_synth_json = Mock(
            return_value={
                "name": "test",
                "components": {},
                "nets": {},
            }
        )

        with patch(
            "circuit_synth.tools.kicad_integration.kicad_to_python_sync.KiCadParser"
        ) as mock_parser_class:
            mock_parser_instance = Mock()
            mock_parser_instance.parse_circuits.return_value = {"main": mock_circuit}
            mock_parser_class.return_value = mock_parser_instance

            syncer.update_json_from_schematic()

            # Verify KiCadParser was called
            mock_parser_class.assert_called_once()
            # Verify circuit.to_circuit_synth_json was called (returns dict for json.dump)
            mock_circuit.to_circuit_synth_json.assert_called_once()
            # Verify JSON file was written
            assert json_file.exists()
            written_data = json.loads(json_file.read_text())
            assert written_data["name"] == "test"

    def test_sync_regenerates_json_before_importing(self, tmp_path):
        """Test 12: sync() regenerates JSON from .kicad_sch before importing"""
        # Create JSON netlist
        json_file = tmp_path / "test.json"
        json_data = {
            "name": "test_circuit",
            "components": {
                "R1": {
                    "ref": "R1",
                    "symbol": "Device:R",
                    "value": "10k",
                    "footprint": "R_0603",
                }
            },
            "nets": {},
        }
        json_file.write_text(json.dumps(json_data))

        # Create KiCad schematic
        kicad_sch = tmp_path / "test.kicad_sch"
        kicad_sch.write_text("(kicad_sch)")

        python_file = tmp_path / "output.py"

        # Create syncer
        syncer = KiCadToPythonSyncer(str(json_file), str(python_file))

        # Mock the update method to verify it's called during sync
        with patch.object(syncer, "update_json_from_schematic") as mock_update:
            with patch.object(syncer, "_json_to_circuits", return_value={}):
                with patch.object(syncer, "code_generator"):
                    syncer.sync()

                    # Verify update_json_from_schematic was called at start of sync
                    mock_update.assert_called_once()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
