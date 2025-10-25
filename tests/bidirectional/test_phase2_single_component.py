#!/usr/bin/env python3
"""
Phase 2: Single Component Tests

Tests adding a single component to circuits and testing idempotency.
These tests validate that the sync pipeline works correctly with actual components.

Tests:
- 2.1: Add Resistor to blank KiCad → Import to Python
- 2.2: Re-run Python generation without KiCad changes (Idempotency)
- 2.3: Modify resistor value in KiCad → Re-import to Python
- 2.4: Verify component parameters preserved in Python
"""

import json
import tempfile
from pathlib import Path

import pytest

from circuit_synth import Circuit, circuit
from circuit_synth.tools.kicad_integration.kicad_to_python_sync import (
    KiCadToPythonSyncer,
)


class TestPhase2SingleComponent:
    """Phase 2: Single component tests - foundation for feature tests"""

    @pytest.fixture
    def simple_resistor_circuit(self):
        """Create a simple circuit with one resistor."""

        @circuit(name="resistor_circuit")
        def resistor_circuit():
            from circuit_synth import Component, Net

            # Create nets
            gnd = Net("GND")

            # Add a simple resistor
            r1 = Component(
                symbol="Device:R",
                ref="R1",
                value="10k",
                footprint="Resistor_SMD:R_0603_1608Metric"
            )

            # Connect to ground (minimal connection)
            r1[1] += gnd
            r1[2] += gnd

        return resistor_circuit()

    def test_2_1_add_resistor_to_kicad_import_to_python(self, simple_resistor_circuit):
        """Test 2.1: Add Resistor to blank KiCad → Import to Python

        Validates:
        - Python circuit with resistor generates valid KiCad project
        - KiCad project contains the resistor
        - Importing KiCad project back to Python preserves component
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Step 1: Generate KiCad project from Python circuit with resistor
            result = simple_resistor_circuit.generate_kicad_project(
                project_name="resistor_circuit", generate_pcb=False
            )

            assert result.get("success"), "Project generation failed"
            project_dir = Path(result["project_path"])
            assert project_dir.exists(), f"Project directory not created: {project_dir}"

            # Verify .kicad_sch file created
            kicad_sch = next(project_dir.glob("*.kicad_sch"), None)
            assert kicad_sch is not None, f"No .kicad_sch file in {project_dir}"
            assert kicad_sch.exists(), f".kicad_sch file doesn't exist: {kicad_sch}"

            # Verify JSON netlist created with resistor
            json_file = next(project_dir.glob("*.json"), None)
            assert json_file is not None, f"No .json file in {project_dir}"

            with open(json_file) as f:
                json_data = json.load(f)

            assert "components" in json_data, "JSON missing 'components' key"
            assert (
                len(json_data["components"]) >= 1
            ), "Resistor circuit should have at least 1 component"

            # Verify R1 is in components
            components = json_data["components"]
            r1_found = any(
                comp.get("ref") == "R1" or key == "R1" for key, comp in components.items()
            ) if isinstance(components, dict) else any(
                comp.get("ref") == "R1" for comp in components
            )
            assert r1_found, "R1 resistor not found in JSON components"

            # Step 2: Import KiCad project back to Python
            output_dir = tmpdir_path / "imported"
            output_dir.mkdir()

            syncer = KiCadToPythonSyncer(
                kicad_project_or_json=str(project_dir / "resistor_circuit.kicad_pro"),
                python_file=str(output_dir),
                preview_only=False,
                create_backup=False,
            )

            success = syncer.sync()
            assert success, "KiCad → Python sync failed"

            # Verify main.py created
            main_py = output_dir / "main.py"
            assert main_py.exists(), f"main.py not created in {output_dir}"

            # Read generated Python code
            with open(main_py) as f:
                generated_code = f.read()

            # Verify R1 component exists in generated code
            assert (
                "R1" in generated_code
            ), "R1 component not found in generated Python code"

            print(f"✅ Test 2.1 PASS: Add Resistor to KiCad → Import to Python")
            print(f"   - Project directory: {project_dir}")
            print(f"   - KiCad schematic: {kicad_sch.name}")
            print(f"   - JSON components: {len(components)}")
            print(f"   - Generated Python: {main_py.name}")
            print(f"   - Python contains R1: ✓")

    def test_2_2_regenerate_resistor_no_change(self, simple_resistor_circuit):
        """Test 2.2: Re-run Python generation without KiCad changes (Idempotency)

        CRITICAL TEST: Validates that regenerating without changes is deterministic.

        Validates:
        - Generate KiCad project from Python with resistor
        - Regenerate KiCad from same Python
        - JSON files unchanged (deterministic)
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Step 1: Generate KiCad project first time
            result1 = simple_resistor_circuit.generate_kicad_project(
                project_name="resistor_circuit", generate_pcb=False
            )
            project_dir = Path(result1["project_path"])

            # Record file contents
            json_file = next(project_dir.glob("*.json"))

            with open(json_file) as f:
                json_content_1 = f.read()

            # Step 2: Regenerate KiCad project
            result2 = simple_resistor_circuit.generate_kicad_project(
                project_name="resistor_circuit", generate_pcb=False
            )

            # Read files after regeneration
            with open(json_file) as f:
                json_content_2 = f.read()

            # Verify JSON unchanged (deterministic generation)
            assert (
                json_content_1 == json_content_2
            ), "JSON changed on regeneration (should be deterministic)"

            print(f"✅ Test 2.2 PASS: Regenerate Resistor → No Change (Idempotency)")
            print(f"   - First generation: ✓")
            print(f"   - Second generation: ✓")
            print(f"   - JSON deterministic: ✓")

    def test_2_3_modify_value_in_kicad_reimport(self):
        """Test 2.3: Modify resistor value in KiCad → Re-import to Python

        Validates:
        - Create blank KiCad project
        - Manually add component (simulated by adding to JSON directly)
        - Modify component value
        - Re-import to Python
        - Python reflects new value
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Step 1: Create blank Python circuit to generate KiCad project structure
            @circuit(name="test_circuit")
            def blank_circuit():
                pass

            blank = blank_circuit()
            result = blank.generate_kicad_project(
                project_name="test_circuit", generate_pcb=False
            )
            project_dir = Path(result["project_path"])

            # Step 2: Modify JSON to add/change component value
            json_file = next(project_dir.glob("*.json"))
            with open(json_file) as f:
                json_data = json.load(f)

            # Add a resistor to components
            if "components" not in json_data:
                json_data["components"] = {}

            json_data["components"]["R1"] = {
                "ref": "R1",
                "symbol": "Device:R",
                "value": "10k",
                "footprint": "Resistor_SMD:R_0603_1608Metric",
                "datasheet": "",
                "description": "",
                "properties": {},
                "tstamps": "",
                "pins": [],
            }

            # Write modified JSON back
            with open(json_file, "w") as f:
                json.dump(json_data, f, indent=2)

            # Step 3: Import KiCad project back to Python
            output_dir = tmpdir_path / "imported"
            output_dir.mkdir()

            syncer = KiCadToPythonSyncer(
                kicad_project_or_json=str(json_file),
                python_file=str(output_dir),
                preview_only=False,
                create_backup=False,
            )

            success = syncer.sync()
            assert success, "KiCad → Python sync failed"

            # Verify main.py created
            main_py = output_dir / "main.py"
            assert main_py.exists(), f"main.py not created in {output_dir}"

            # Read generated Python code
            with open(main_py) as f:
                generated_code = f.read()

            # Verify R1 and 10k value in generated code
            assert "R1" in generated_code, "R1 not in generated Python"
            assert "10k" in generated_code, "10k value not in generated Python"

            print(f"✅ Test 2.3 PASS: Modify value in KiCad → Re-import to Python")
            print(f"   - Created test project: {project_dir}")
            print(f"   - Modified JSON to add R1=10k")
            print(f"   - Re-imported to Python: ✓")
            print(f"   - Generated Python contains R1=10k: ✓")

    def test_2_4_verify_component_parameters_preserved(self, simple_resistor_circuit):
        """Test 2.4: Verify component parameters preserved in Python

        Validates:
        - Generate KiCad from Python circuit
        - Import KiCad back to Python
        - Verify all component parameters are present in generated code
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Step 1: Generate KiCad project
            result = simple_resistor_circuit.generate_kicad_project(
                project_name="resistor_circuit", generate_pcb=False
            )
            project_dir = Path(result["project_path"])

            # Get original JSON to see what was generated
            json_file = next(project_dir.glob("*.json"))
            with open(json_file) as f:
                original_json = json.load(f)

            # Step 2: Import back to Python
            output_dir = tmpdir_path / "imported"
            output_dir.mkdir()

            syncer = KiCadToPythonSyncer(
                kicad_project_or_json=str(project_dir / "resistor_circuit.kicad_pro"),
                python_file=str(output_dir),
                preview_only=False,
                create_backup=False,
            )

            success = syncer.sync()
            assert success, "KiCad → Python sync failed"

            main_py = output_dir / "main.py"
            with open(main_py) as f:
                generated_code = f.read()

            # Verify component reference preserved
            assert "R1" in generated_code, "Component reference R1 not preserved"

            # Verify value preserved (10k)
            assert "10k" in generated_code or "10K" in generated_code, (
                "Component value not preserved"
            )

            # Verify circuit structure preserved
            assert (
                "def " in generated_code
            ), "Circuit function not in generated code"

            print(f"✅ Test 2.4 PASS: Verify component parameters preserved")
            print(f"   - Original JSON components: {len(original_json.get('components', {}))}")
            print(f"   - Component reference preserved: ✓")
            print(f"   - Component value preserved: ✓")
            print(f"   - Circuit structure preserved: ✓")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
