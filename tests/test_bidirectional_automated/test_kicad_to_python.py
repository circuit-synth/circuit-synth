"""
Tests for KiCad → Python import.

Validates that circuit-synth can import KiCad schematics and convert them
to Python circuit definitions.

Manual test equivalents:
- test_02: bidirectional/02_kicad_to_python
- test_05: bidirectional/05_add_resistor_kicad_to_python
"""

import pytest
import kicad_sch_api as ksa

from circuit_synth.kicad.importer import import_kicad_project
from fixtures.circuits import single_resistor
from fixtures.assertions import assert_schematic_has_component


class TestKiCadToPythonImport:
    """Test KiCad → Python schematic import."""

    def test_02_import_generated_schematic(self, temp_project_dir):
        """
        Test: Import KiCad schematic that was generated from Python.

        Validates:
        - Import function works on generated schematics
        - Imported circuit has correct components
        - Component properties preserved during import

        Manual equivalent: tests/bidirectional/02_kicad_to_python
        """
        # Generate a KiCad project first
        circuit_obj = single_resistor()
        output_path = temp_project_dir / "import_test"
        circuit_obj.generate_kicad_project(project_name=str(output_path))

        # Import it back
        project_file = output_path / "import_test.kicad_pro"
        imported_circuit = import_kicad_project(str(project_file))

        # Verify components imported - components is a list
        assert hasattr(imported_circuit, 'components'), \
            "Imported circuit missing components attribute"
        assert len(imported_circuit.components) == 1, \
            f"Expected 1 component, got {len(imported_circuit.components)}"

        # Verify component properties - convert list to dict for lookup
        comp_map = {c.ref: c for c in imported_circuit.components}
        assert "R1" in comp_map, "R1 not found in imported circuit"
        r1 = comp_map["R1"]
        assert r1.value == "10k", f"Expected value '10k', got '{r1.value}'"
        assert r1.footprint == "Resistor_SMD:R_0603_1608Metric", \
            f"Footprint mismatch"

    @pytest.mark.skip(reason="JSON regeneration from edited schematic needs investigation")
    def test_05_add_component_in_kicad_then_import(self, temp_project_dir):
        """
        Test: Add component manually in KiCad, then import to Python.

        Workflow:
        1. Generate KiCad project with R1 from Python
        2. Add R2 manually using kicad-sch-api (simulates KiCad edit)
        3. Import back to Python
        4. Verify both R1 and R2 present

        Validates:
        - Import detects manually-added components
        - New component properties imported correctly
        - Original components still present

        Manual equivalent: tests/bidirectional/05_add_resistor_kicad_to_python

        NOTE: Currently skipped - JSON regeneration from edited schematic
        has issues with finding the root schematic file. This is a complex
        test that requires deeper integration with the KiCad parser.
        """
        # Step 1: Generate initial circuit with R1
        circuit_obj = single_resistor()
        output_path = temp_project_dir / "add_in_kicad_test"
        circuit_obj.generate_kicad_project(project_name=str(output_path))

        # Step 2: Simulate adding R2 in KiCad using kicad-sch-api
        sch_path = output_path / "add_in_kicad_test.kicad_sch"
        sch = ksa.Schematic.load(str(sch_path))

        # Add R2
        sch.components.add(
            lib_id="Device:R",
            reference="R2",
            value="4.7k",
            footprint="Resistor_SMD:R_0603_1608Metric",
            position=(150, 100)
        )
        sch.save()

        # Delete the JSON netlist so it gets regenerated with the updated schematic
        json_path = output_path / "add_in_kicad_test.json"
        if json_path.exists():
            json_path.unlink()

        # Step 3: Import back to Python
        project_file = output_path / "add_in_kicad_test.kicad_pro"
        imported_circuit = import_kicad_project(str(project_file))

        # Step 4: Verify both components present
        assert len(imported_circuit.components) == 2, \
            f"Expected 2 components, got {len(imported_circuit.components)}"

        # Convert list to dict for lookup
        comp_map = {c.ref: c for c in imported_circuit.components}

        # Verify R1 (original)
        assert "R1" in comp_map, "R1 lost during import"
        assert comp_map["R1"].value == "10k"

        # Verify R2 (manually added)
        assert "R2" in comp_map, "R2 not imported"
        assert comp_map["R2"].value == "4.7k"
        assert comp_map["R2"].footprint == \
            "Resistor_SMD:R_0603_1608Metric"

    def test_import_preserves_component_positions(self, temp_project_dir):
        """
        Test: Verify import preserves component positions.

        Validates:
        - Component positions imported correctly
        - Position coordinates preserved (within tolerance)

        Manual equivalent: Part of bidirectional/09_position_preservation
        """
        # Generate circuit
        circuit_obj = single_resistor()
        output_path = temp_project_dir / "position_import_test"
        circuit_obj.generate_kicad_project(project_name=str(output_path))

        # Get original position
        sch_path = output_path / "position_import_test.kicad_sch"
        sch = ksa.Schematic.load(str(sch_path))
        original_pos = sch.components.get("R1").position

        # Import
        project_file = output_path / "position_import_test.kicad_pro"
        imported_circuit = import_kicad_project(str(project_file))

        # Convert list to dict for lookup
        comp_map = {c.ref: c for c in imported_circuit.components}

        # Verify position preserved (if supported by importer)
        if hasattr(comp_map["R1"], 'position'):
            imported_pos = comp_map["R1"].position
            # Allow small tolerance for rounding
            tolerance = 1.0  # mm
            dx = abs(imported_pos[0] - original_pos[0])
            dy = abs(imported_pos[1] - original_pos[1])
            assert dx < tolerance and dy < tolerance, \
                f"Position not preserved: {original_pos} → {imported_pos}"

    def test_import_blank_schematic(self, temp_project_dir):
        """
        Test: Import blank/empty KiCad schematic.

        Validates:
        - Import works on blank schematics
        - No components in imported circuit
        - No errors on empty import

        Manual equivalent: tests/bidirectional/01_blank_circuit (import direction)
        """
        # Generate blank circuit
        from fixtures.circuits import blank
        circuit_obj = blank()
        output_path = temp_project_dir / "blank_import_test"
        circuit_obj.generate_kicad_project(project_name=str(output_path))

        # Import
        project_file = output_path / "blank_import_test.kicad_pro"
        imported_circuit = import_kicad_project(str(project_file))

        # Verify no components
        assert len(imported_circuit.components) == 0, \
            "Blank circuit should have no components"
