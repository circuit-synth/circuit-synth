#!/usr/bin/env python3
"""
Unit tests for automatic JSON generation in generate_kicad_project()

This test verifies that:
1. JSON netlist is automatically created in project directory
2. JSON path is returned in result dict
3. generate_kicad_project() returns proper result structure
"""

import tempfile
from pathlib import Path

import pytest

from circuit_synth import Circuit, Component, Net, circuit


def test_generate_kicad_project_returns_dict():
    """Test that generate_kicad_project() returns a result dictionary."""

    @circuit(name="test_simple")
    def simple_circuit():
        """Simple resistor circuit for testing."""
        vcc = Net("VCC")
        gnd = Net("GND")

        r1 = Component(
            symbol="Device:R", ref="R1", value="10k", footprint="Resistor_SMD:R_0603_1608Metric"
        )

        r1[1] += vcc
        r1[2] += gnd

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        project_name = "test_project"

        # Create circuit
        test_circuit = simple_circuit()

        # Generate project (without PCB for faster testing)
        result = test_circuit.generate_kicad_project(
            project_name=str(tmpdir_path / project_name),
            force_regenerate=True,
            generate_pcb=False,
        )

        # Verify result structure
        assert isinstance(result, dict), "Result should be a dictionary"
        assert "success" in result, "Result should contain 'success' key"
        assert "json_path" in result, "Result should contain 'json_path' key"
        assert "project_path" in result, "Result should contain 'project_path' key"


def test_json_automatically_created_in_project_dir():
    """Test that JSON netlist is automatically created in project directory."""

    @circuit(name="test_json_auto")
    def test_circuit_json():
        """Simple circuit for JSON testing."""
        vcc = Net("VCC")
        gnd = Net("GND")

        r1 = Component(
            symbol="Device:R", ref="R1", value="10k", footprint="Resistor_SMD:R_0603_1608Metric"
        )

        r1[1] += vcc
        r1[2] += gnd

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        project_name = "test_json_project"

        # Create circuit
        cir = test_circuit_json()

        # Generate project (without PCB for faster testing)
        result = cir.generate_kicad_project(
            project_name=str(tmpdir_path / project_name),
            force_regenerate=True,
            generate_pcb=False,
        )

        # Verify success
        assert result["success"] is True, f"Generation should succeed: {result.get('error', '')}"

        # Verify JSON path is in result
        json_path = result["json_path"]
        assert json_path is not None, "json_path should not be None"
        assert isinstance(json_path, Path), "json_path should be a Path object"

        # Verify JSON file exists
        assert json_path.exists(), f"JSON file should exist at: {json_path}"

        # Verify JSON is in project directory
        assert json_path.parent.resolve() == result["project_path"].resolve(), "JSON should be in project directory"
        assert json_path.name == f"{project_name}.json", "JSON should have correct name"

        # Verify JSON is valid and contains expected structure
        import json

        with open(json_path, "r") as f:
            json_data = json.load(f)

        assert "name" in json_data, "JSON should contain circuit name"
        assert "components" in json_data, "JSON should contain components"
        assert "nets" in json_data, "JSON should contain nets"
        assert "R1" in json_data["components"], "JSON should contain R1 component"


def test_json_path_matches_project_structure():
    """Test that JSON path follows expected naming convention."""

    @circuit(name="test_naming")
    def test_circuit_naming():
        """Circuit for testing naming convention."""
        gnd = Net("GND")
        r1 = Component(
            symbol="Device:R", ref="R1", value="1k", footprint="Resistor_SMD:R_0603_1608Metric"
        )
        r1[1] += gnd

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)
        project_name = "my_custom_board"

        # Create and generate (without PCB for faster testing)
        cir = test_circuit_naming()
        result = cir.generate_kicad_project(
            project_name=str(tmpdir_path / project_name),
            force_regenerate=True,
            generate_pcb=False,
        )

        # Verify naming
        json_path = result["json_path"]
        project_path = result["project_path"]

        assert json_path.parent.resolve() == project_path.resolve(), "JSON should be in project directory"
        assert json_path.stem == project_name, "JSON should have same name as project"
        assert json_path.suffix == ".json", "JSON should have .json extension"


def test_error_handling_returns_dict():
    """Test that errors return proper dict structure."""

    @circuit(name="test_error")
    def test_circuit_error():
        """Circuit that might fail (for error testing)."""
        pass

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Create circuit
        cir = test_circuit_error()

        # Generate project (without PCB for faster testing)
        result = cir.generate_kicad_project(
            project_name=str(tmpdir_path / "test_project"),
            force_regenerate=True,
            generate_pcb=False,
        )

        # Even if it fails, should return dict
        assert isinstance(result, dict), "Result should always be a dict"
        assert "success" in result, "Result should contain 'success' key"

        # If it failed, should have error message
        if not result["success"]:
            assert "error" in result, "Failed result should contain 'error' key"
            assert isinstance(result["error"], str), "Error should be a string"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
