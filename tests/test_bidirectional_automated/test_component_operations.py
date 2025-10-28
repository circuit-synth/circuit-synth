"""
Tests for component operations (add, delete, modify, rename).

Validates component manipulation operations work correctly and properties
are preserved.

Manual test equivalents:
- test_06: bidirectional/06_add_component
- test_07: bidirectional/07_delete_component
- test_08: bidirectional/08_modify_value
- test_13: bidirectional/13_rename_component
"""

import pytest
import kicad_sch_api as ksa

from circuit_synth.kicad.importer import import_kicad_project
from fixtures.circuits import single_resistor, two_resistors
from fixtures.assertions import assert_schematic_has_component, assert_schematic_component_count


class TestComponentOperations:
    """Test component add, delete, modify, and rename operations."""

    def test_06_add_component(self, temp_project_dir):
        """
        Test: Add component to existing circuit.

        Workflow:
        1. Generate circuit with R1
        2. Add R2 using kicad-sch-api
        3. Import and verify both present

        Validates:
        - Adding component works
        - Original component preserved
        - New component has correct properties

        Manual equivalent: tests/bidirectional/06_add_component
        """
        output_dir = temp_project_dir / "add_component_test"

        # Start with R1
        circuit = single_resistor()
        circuit.generate_kicad_project(
            project_name=str(output_dir)
        )

        # Add R2
        sch_path = output_dir / "add_component_test.kicad_sch"
        sch = ksa.Schematic.load(str(sch_path))
        sch.components.add(
            lib_id="Device:R",
            reference="R2",
            value="1k",
            footprint="Resistor_SMD:R_0603_1608Metric",
            position=(150, 100)
        )
        sch.save()

        # Verify
        sch_verify = ksa.Schematic.load(str(sch_path))
        assert_schematic_component_count(sch_verify, 2)
        assert_schematic_has_component(sch_verify, "R1", value="10k")
        assert_schematic_has_component(sch_verify, "R2", value="1k")

        # Import and verify
        project_file = output_dir / "add_component_test.kicad_pro"
        imported = import_kicad_project(str(project_file))
        assert len(imported.components) == 2
        assert "R1" in imported.components
        assert "R2" in imported.components

    def test_07_delete_component(self, temp_project_dir):
        """
        Test: Delete component from circuit.

        Workflow:
        1. Generate circuit with R1, R2
        2. Delete R2 using kicad-sch-api
        3. Import and verify only R1 remains

        Validates:
        - Component deletion works
        - Other components unaffected
        - Deletion reflected in import

        Manual equivalent: tests/bidirectional/07_delete_component
        """
        output_dir = temp_project_dir / "delete_component_test"

        # Start with R1, R2
        circuit = two_resistors()
        circuit.generate_kicad_project(
            project_name=str(output_dir)
        )

        # Delete R2
        sch_path = output_dir / "delete_component_test.kicad_sch"
        sch = ksa.Schematic.load(str(sch_path))
        sch.components.remove("R2")
        sch.save()

        # Verify
        sch_verify = ksa.Schematic.load(str(sch_path))
        assert_schematic_component_count(sch_verify, 1)
        assert_schematic_has_component(sch_verify, "R1", value="10k")

        r2 = sch_verify.components.get("R2")
        assert r2 is None, "R2 should be deleted"

        # Import and verify
        project_file = output_dir / "delete_component_test.kicad_pro"
        imported = import_kicad_project(str(project_file))
        assert len(imported.components) == 1
        assert "R1" in imported.components
        assert "R2" not in imported.components

    def test_08_modify_component_value(self, temp_project_dir):
        """
        Test: Modify component value.

        Workflow:
        1. Generate circuit with R1 (10k)
        2. Change R1 value to 22k using kicad-sch-api
        3. Import and verify new value

        Validates:
        - Value modification works
        - Modified value reflected in import
        - Other properties unchanged

        Manual equivalent: tests/bidirectional/08_modify_value
        """
        output_dir = temp_project_dir / "modify_value_test"

        # Start with R1 = 10k
        circuit = single_resistor()
        circuit.generate_kicad_project(
            project_name=str(output_dir)
        )

        # Change to 22k
        sch_path = output_dir / "modify_value_test.kicad_sch"
        sch = ksa.Schematic.load(str(sch_path))
        r1 = sch.components.get("R1")
        r1.value = "22k"
        sch.save()

        # Verify
        sch_verify = ksa.Schematic.load(str(sch_path))
        assert_schematic_has_component(sch_verify, "R1", value="22k")

        # Import and verify
        project_file = output_dir / "modify_value_test.kicad_pro"
        imported = import_kicad_project(str(project_file))
        assert imported.components["R1"].value == "22k", \
            f"Expected value '22k', got '{imported.components['R1'].value}'"

        # Verify other properties unchanged
        assert imported.components["R1"].footprint == \
            "Resistor_SMD:R_0603_1608Metric"

    def test_13_rename_component(self, temp_project_dir):
        """
        Test: Rename component reference.

        Workflow:
        1. Generate circuit with R1
        2. Rename R1 → R192713402134 using kicad-sch-api
        3. Import and verify new reference

        Validates:
        - Reference rename works
        - Renamed component imported correctly
        - Old reference no longer exists
        - Properties preserved

        Manual equivalent: tests/bidirectional/13_rename_component
        """
        output_dir = temp_project_dir / "rename_component_test"

        # Start with R1
        circuit = single_resistor()
        circuit.generate_kicad_project(
            project_name=str(output_dir)
        )

        # Rename R1 → R192713402134
        sch_path = output_dir / "rename_component_test.kicad_sch"
        sch = ksa.Schematic.load(str(sch_path))
        r1 = sch.components.get("R1")
        r1.reference = "R192713402134"
        sch.save()

        # Verify in schematic
        sch_verify = ksa.Schematic.load(str(sch_path))
        assert sch_verify.components.get("R1") is None, \
            "Old reference R1 should not exist"
        assert_schematic_has_component(
            sch_verify,
            "R192713402134",
            value="10k",
            footprint="Resistor_SMD:R_0603_1608Metric"
        )

        # Import and verify
        project_file = output_dir / "rename_component_test.kicad_pro"
        imported = import_kicad_project(str(project_file))
        assert "R1" not in imported.components, \
            "Old reference should not be imported"
        assert "R192713402134" in imported.components, \
            "New reference not found"
        assert imported.components["R192713402134"].value == "10k"

    def test_modify_footprint(self, temp_project_dir):
        """
        Test: Modify component footprint.

        Validates:
        - Footprint modification works
        - Modified footprint reflected in import

        Manual equivalent: Extension of test_08
        """
        output_dir = temp_project_dir / "modify_footprint_test"

        # Generate circuit
        circuit = single_resistor()
        circuit.generate_kicad_project(
            project_name=str(output_dir)
        )

        # Change footprint
        sch_path = output_dir / "modify_footprint_test.kicad_sch"
        sch = ksa.Schematic.load(str(sch_path))
        r1 = sch.components.get("R1")
        new_footprint = "Resistor_SMD:R_0805_2012Metric"  # Larger package
        r1.footprint = new_footprint
        sch.save()

        # Verify
        sch_verify = ksa.Schematic.load(str(sch_path))
        assert_schematic_has_component(
            sch_verify, "R1",
            footprint=new_footprint
        )

        # Import and verify
        project_file = output_dir / "modify_footprint_test.kicad_pro"
        imported = import_kicad_project(str(project_file))
        assert imported.components["R1"].footprint == new_footprint

    def test_bulk_component_operations(self, temp_project_dir):
        """
        Test: Multiple component operations in sequence.

        Workflow:
        1. Generate with R1, R2
        2. Add R3
        3. Delete R2
        4. Modify R1 value
        5. Verify final state

        Validates:
        - Multiple operations work together
        - No conflicts between operations
        - Final state correct

        Manual equivalent: Combination of tests 06, 07, 08
        """
        output_dir = temp_project_dir / "bulk_operations_test"

        # Start with R1, R2
        circuit = two_resistors()
        circuit.generate_kicad_project(
            project_name=str(output_dir)
        )

        sch_path = output_dir / "bulk_operations_test.kicad_sch"
        sch = ksa.Schematic.load(str(sch_path))

        # Add R3
        sch.components.add(
            lib_id="Device:R",
            reference="R3",
            value="1k",
            footprint="Resistor_SMD:R_0603_1608Metric",
            position=(200, 100)
        )

        # Delete R2
        sch.components.remove("R2")

        # Modify R1 value
        sch.components.get("R1").value = "47k"

        sch.save()

        # Verify final state
        sch_verify = ksa.Schematic.load(str(sch_path))
        assert_schematic_component_count(sch_verify, 2)  # R1, R3 (R2 deleted)
        assert_schematic_has_component(sch_verify, "R1", value="47k")
        assert sch_verify.components.get("R2") is None
        assert_schematic_has_component(sch_verify, "R3", value="1k")

        # Import and verify
        project_file = output_dir / "bulk_operations_test.kicad_pro"
        imported = import_kicad_project(str(project_file))
        assert len(imported.components) == 2
        assert imported.components["R1"].value == "47k"
        assert "R2" not in imported.components
        assert imported.components["R3"].value == "1k"
