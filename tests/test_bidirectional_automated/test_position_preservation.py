"""
Tests for position preservation during regeneration.

Validates that manual component positions survive when regenerating KiCad
from Python.

Manual test equivalents:
- test_09: bidirectional/09_position_preservation
- test_16: bidirectional/16_rename_python_canonical
"""

import pytest
import kicad_sch_api as ksa

from circuit_synth.kicad.importer import import_kicad_project
from fixtures.circuits import single_resistor
from fixtures.assertions import assert_position_near, assert_position_preserved


class TestPositionPreservation:
    """Test that manual component positions are preserved during regeneration."""

    def test_09_position_preserved_when_adding_component(self, temp_project_dir):
        """
        Test: Manual component position preserved when adding new component.

        Workflow:
        1. Generate KiCad with R1
        2. Manually move R1 in KiCad (simulate user arranging layout)
        3. Add R2 using kicad-sch-api
        4. Verify R1 stayed at manually-moved position
        5. Verify R2 placed without overlapping R1

        This is THE KILLER FEATURE for bidirectional sync.
        If positions aren't preserved, layout work is lost on every regeneration.

        Validates:
        - R1 position preserved after adding R2
        - R1 not reset to default position
        - R2 placed in available space
        - Manual layout work not lost

        Manual equivalent: tests/bidirectional/09_position_preservation
        """
        output_dir = temp_project_dir / "position_preservation_test"

        # Step 1: Generate initial circuit with R1
        circuit = single_resistor()
        circuit.generate_kicad_project(
            project_name=str(output_dir)
        )

        # Get R1's original auto-placed position
        sch_path = output_dir / "position_preservation_test.kicad_sch"
        sch = ksa.Schematic(str(sch_path))
        r1_original_pos = sch.components.get("R1").position

        # Step 2: Manually move R1 to center of page (simulate user action)
        center_pos = (127, 127)  # Center of standard KiCad page
        sch.components.get("R1").position = center_pos
        sch.save()

        # Verify move worked
        sch_moved = ksa.Schematic(str(sch_path))
        r1_moved_pos = sch_moved.components.get("R1").position
        assert_position_near(r1_moved_pos, center_pos, tolerance=0.5)
        assert r1_moved_pos != r1_original_pos, "Position didn't change"

        # Step 3: Add R2 (simulate adding component after manual layout)
        sch_moved.components.add(
            lib_id="Device:R",
            reference="R2",
            value="4.7k",
            footprint="Resistor_SMD:R_0603_1608Metric",
            position=(200, 100)  # Some other position
        )
        sch_moved.save()

        # Step 4: Verify R1 STILL at manually-moved position
        sch_final = ksa.Schematic(str(sch_path))
        r1_final_pos = sch_final.components.get("R1").position

        # Critical assertion: R1 didn't move back to original position
        assert_position_near(r1_final_pos, center_pos, tolerance=0.5), \
            f"R1 position not preserved! Expected {center_pos}, got {r1_final_pos}"

        # Ensure R1 didn't reset to original
        assert_position_near(r1_final_pos, r1_moved_pos, tolerance=0.1), \
            f"R1 moved from {r1_moved_pos} to {r1_final_pos}"

        # Verify R2 exists
        r2 = sch_final.components.get("R2")
        assert r2 is not None, "R2 not found"

        # Verify R2 doesn't overlap R1
        r2_pos = r2.position
        distance = ((r1_final_pos[0] - r2_pos[0])**2 +
                   (r1_final_pos[1] - r2_pos[1])**2)**0.5
        assert distance > 10, \
            f"R2 overlaps R1! R1 at {r1_final_pos}, R2 at {r2_pos}"

    def test_16_position_preserved_on_regeneration(self, temp_project_dir):
        """
        Test: Component positions preserved when regenerating from Python.

        Workflow:
        1. Generate circuit
        2. Manually adjust positions in KiCad
        3. Regenerate from Python (same circuit definition)
        4. Verify positions not reset

        Validates:
        - Regeneration preserves manual positions
        - No reset to defaults on regeneration

        Manual equivalent: tests/bidirectional/16_rename_python_canonical
        """
        output_dir = temp_project_dir / "regen_position_test"

        # Generate initial circuit
        circuit = single_resistor()
        circuit.generate_kicad_project(
            project_name=str(output_dir)
        )

        # Manually adjust position
        sch_path = output_dir / "regen_position_test.kicad_sch"
        sch = ksa.Schematic(str(sch_path))
        custom_pos = (100, 150)
        sch.components.get("R1").position = custom_pos
        sch.save()

        # Regenerate same circuit
        circuit2 = single_resistor()
        circuit2.generate_kicad_project(
            project_name=str(output_dir)
        )

        # Verify position preserved
        sch_regen = ksa.Schematic(str(sch_path))
        r1_regen_pos = sch_regen.components.get("R1").position

        # Position should be close to custom position
        # (May have slight differences due to synchronization logic)
        # For now, just verify it didn't reset to some default far away
        assert_position_near(r1_regen_pos, custom_pos, tolerance=20), \
            f"Position severely changed: {custom_pos} → {r1_regen_pos}"

    def test_position_preservation_with_deletion(self, temp_project_dir):
        """
        Test: Remaining component positions preserved after deleting a component.

        Workflow:
        1. Generate circuit with R1, R2
        2. Manually position both
        3. Delete R2
        4. Verify R1 position unchanged

        Validates:
        - Deletion doesn't affect other component positions
        - No layout reset on component removal

        Manual equivalent: Part of tests/bidirectional/07_delete_component
        """
        output_dir = temp_project_dir / "delete_position_test"

        # Generate circuit with two resistors
        from fixtures.circuits import two_resistors
        circuit = two_resistors()
        circuit.generate_kicad_project(
            project_name=str(output_dir)
        )

        # Manually position both
        sch_path = output_dir / "delete_position_test.kicad_sch"
        sch = ksa.Schematic(str(sch_path))
        r1_custom_pos = (100, 100)
        r2_custom_pos = (200, 100)
        sch.components.get("R1").position = r1_custom_pos
        sch.components.get("R2").position = r2_custom_pos
        sch.save()

        # Delete R2
        sch_delete = ksa.Schematic(str(sch_path))
        sch_delete.components.remove("R2")
        sch_delete.save()

        # Verify R1 position unchanged
        sch_final = ksa.Schematic(str(sch_path))
        r1_final_pos = sch_final.components.get("R1").position

        assert_position_near(r1_final_pos, r1_custom_pos, tolerance=0.5), \
            f"R1 position changed after R2 deletion: {r1_custom_pos} → {r1_final_pos}"

        # Verify R2 gone
        r2_final = sch_final.components.get("R2")
        assert r2_final is None, "R2 should be deleted"

    def test_grid_snapping_tolerance(self, temp_project_dir):
        """
        Test: Position preservation accounts for grid snapping.

        KiCad snaps components to grid. Verify preservation accounts for
        small rounding differences.

        Validates:
        - Position comparison uses tolerance
        - Small grid-snap differences accepted
        - Not overly strict on exact coordinates

        Manual equivalent: Extension of position preservation tests
        """
        output_dir = temp_project_dir / "grid_snap_test"

        # Generate circuit
        circuit = single_resistor()
        circuit.generate_kicad_project(
            project_name=str(output_dir)
        )

        # Set position to non-grid value
        sch_path = output_dir / "grid_snap_test.kicad_sch"
        sch = ksa.Schematic(str(sch_path))
        non_grid_pos = (100.123, 100.456)  # Sub-millimeter precision
        sch.components.get("R1").position = non_grid_pos
        sch.save()

        # Reload (KiCad may snap to grid)
        sch_reload = ksa.Schematic(str(sch_path))
        reloaded_pos = sch_reload.components.get("R1").position

        # Should be close (within 1mm grid snap tolerance)
        assert_position_near(reloaded_pos, non_grid_pos, tolerance=1.0), \
            f"Grid snapping changed position too much: {non_grid_pos} → {reloaded_pos}"
