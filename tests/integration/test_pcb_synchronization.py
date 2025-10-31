"""
End-to-end integration test for PCB synchronization (Issue #410).

Tests the core use case: adding a component to a circuit results in the component
appearing in BOTH schematic and PCB, with manual placement preserved.

Core scenario:
1. Generate initial circuit with R1 only
2. Verify R1 appears in PCB
3. Regenerate circuit with R1 + R2
4. Verify BOTH R1 and R2 appear in PCB
5. Verify R1 position is preserved (not reset)
6. Verify R2 is added at default position
"""

import tempfile
from pathlib import Path

import pytest

from circuit_synth import Circuit, Component, Net, circuit


class TestPCBSynchronization:
    """Test PCB synchronization preserves manual placement when components are added."""

    @pytest.fixture
    def temp_workspace(self):
        """Create a temporary workspace for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @staticmethod
    def _get_footprint_refs(pcb):
        """Extract list of footprint references from a PCBBoard object."""
        footprints_list = pcb.list_footprints()
        return [fp[0] for fp in footprints_list]

    @staticmethod
    def _find_footprint_by_ref(pcb, reference):
        """Find a footprint in PCB data by its reference designation."""
        for fp in pcb.pcb_data.get("footprints", []):
            # Handle both dict-like and Footprint objects
            # For Footprint objects from kicad_pcb_api, directly access reference attribute
            if hasattr(fp, 'reference'):
                if fp.reference == reference:
                    return fp
            # Fallback: search properties list
            properties = fp.get("properties", []) if hasattr(fp, 'get') else (fp.properties if hasattr(fp, 'properties') else [])
            for prop in properties:
                # Property objects have 'name' and 'value' attributes
                prop_key = prop.get("key") if hasattr(prop, 'get') else (prop.name if hasattr(prop, 'name') else None)
                prop_val = prop.get("value") if hasattr(prop, 'get') else (prop.value if hasattr(prop, 'value') else None)
                if prop_key == "Reference" and prop_val == reference:
                    return fp
        return None

    @staticmethod
    def _get_footprint_position(footprint):
        """Extract position (x, y, rotation) from a footprint object."""
        # Handle Footprint objects from kicad_pcb_api
        if hasattr(footprint, 'position'):
            # Footprint object with position attribute (Point object)
            x = float(footprint.position.x) if hasattr(footprint.position, 'x') else 5.0
            y = float(footprint.position.y) if hasattr(footprint.position, 'y') else 5.0
            rotation = float(footprint.rotation) if hasattr(footprint, 'rotation') else 0.0
            return x, y, rotation

        # Fallback for dict-like objects
        at_data = footprint.get("at", [5.0, 5.0, 0.0]) if hasattr(footprint, 'get') else [5.0, 5.0, 0.0]
        x = float(at_data[0]) if len(at_data) > 0 else 5.0
        y = float(at_data[1]) if len(at_data) > 1 else 5.0
        rotation = float(at_data[2]) if len(at_data) > 2 else 0.0
        return x, y, rotation

    @staticmethod
    def _set_footprint_position(footprint, x, y, rotation=0.0):
        """Set position on a footprint object."""
        if hasattr(footprint, 'position') and hasattr(footprint.position, 'x'):
            # Footprint object from kicad_pcb_api with Point position
            footprint.position.x = x
            footprint.position.y = y
            if hasattr(footprint, 'rotation'):
                footprint.rotation = rotation
        elif hasattr(footprint, '__setitem__'):
            # Dict-like object
            footprint["at"] = [x, y, rotation]
        else:
            # Fallback: try direct assignment as dict
            try:
                footprint["at"] = [x, y, rotation]
            except (TypeError, KeyError):
                # If that fails, just try to set the attributes
                if hasattr(footprint, 'position'):
                    footprint.position.x = x
                    footprint.position.y = y
                if hasattr(footprint, 'rotation'):
                    footprint.rotation = rotation

    def test_initial_pcb_generation_creates_single_component(self, temp_workspace):
        """
        Test that initial circuit generation with one resistor creates PCB with that resistor.

        This is the baseline: starting with R1 only.
        """
        # Define circuit with single resistor
        @circuit(name="single_resistor")
        def single_component_circuit():
            """Circuit with just one resistor."""
            r1 = Component(
                symbol="Device:R",
                ref="R1",
                value="10k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            return r1

        # Create circuit instance
        test_circuit = single_component_circuit()

        # Generate KiCad project with PCB
        project_dir = temp_workspace / "single_component_project"
        result = test_circuit.generate_kicad_project(
            str(project_dir), generate_pcb=True, force_regenerate=True
        )

        # Verify generation succeeded
        assert result is not False, "Initial KiCad project generation should succeed"

        # Verify PCB file exists
        pcb_file = project_dir / "single_resistor.kicad_pcb"
        assert pcb_file.exists(), f"PCB file should exist at {pcb_file}"

        # Load PCB and verify R1 is present
        from kicad_pcb_api import PCBBoard

        pcb = PCBBoard()
        pcb.load(str(pcb_file))

        # Extract footprint references
        footprint_refs = self._get_footprint_refs(pcb)

        assert "R1" in footprint_refs, f"R1 should be in PCB footprints. Found: {footprint_refs}"
        assert (
            len(footprint_refs) == 1
        ), f"Should have exactly 1 footprint (R1), found: {footprint_refs}"

    def test_adding_component_appears_in_pcb(self, temp_workspace):
        """
        Test that adding a second resistor to the circuit makes it appear in the PCB.

        Core issue #410 test case: R1 exists, add R2, both should appear in PCB.
        """
        # Step 1: Generate initial circuit with R1 only
        @circuit(name="dual_resistor")
        def initial_circuit():
            """Initial circuit with just R1."""
            r1 = Component(
                symbol="Device:R",
                ref="R1",
                value="10k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            return r1

        test_circuit = initial_circuit()
        project_dir = temp_workspace / "dual_resistor_project"

        # Generate initial PCB
        test_circuit.generate_kicad_project(
            str(project_dir), generate_pcb=True, force_regenerate=True
        )

        # Verify initial PCB has only R1
        from kicad_pcb_api import PCBBoard

        pcb_file = project_dir / "dual_resistor.kicad_pcb"
        pcb = PCBBoard()
        pcb.load(str(pcb_file))

        initial_footprints = self._get_footprint_refs(pcb)
        assert "R1" in initial_footprints, "Initial PCB should have R1"
        assert (
            len(initial_footprints) == 1
        ), f"Initial PCB should have only 1 component, found: {initial_footprints}"

        # Step 2: Regenerate circuit with R1 + R2
        @circuit(name="dual_resistor")
        def updated_circuit():
            """Updated circuit with R1 + R2."""
            r1 = Component(
                symbol="Device:R",
                ref="R1",
                value="10k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            r2 = Component(
                symbol="Device:R",
                ref="R2",
                value="20k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            return r1, r2

        updated_circuit_obj = updated_circuit()

        # Regenerate project (should sync PCB, not regenerate from scratch)
        result = updated_circuit_obj.generate_kicad_project(
            str(project_dir), generate_pcb=True, force_regenerate=False
        )

        assert result is not False, "PCB regeneration should succeed"

        # Step 3: Verify both R1 and R2 are in the PCB
        pcb2 = PCBBoard()
        pcb2.load(str(pcb_file))

        final_footprints = self._get_footprint_refs(pcb2)

        assert (
            "R1" in final_footprints
        ), f"R1 should still be in PCB after sync. Found: {final_footprints}"
        assert (
            "R2" in final_footprints
        ), f"R2 should be added to PCB. Found: {final_footprints}"
        assert (
            len(final_footprints) == 2
        ), f"PCB should have exactly 2 components after sync, found: {final_footprints}"

    def test_component_position_preserved_during_sync(self, temp_workspace):
        """
        Test that manually placed component position is preserved when adding new components.

        This verifies the critical feature: R1's position stays the same even after
        adding R2.
        """
        # Step 1: Generate initial circuit with R1
        @circuit(name="position_test")
        def initial_pos_circuit():
            """Circuit with R1."""
            r1 = Component(
                symbol="Device:R",
                ref="R1",
                value="10k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            return r1

        test_circuit = initial_pos_circuit()
        project_dir = temp_workspace / "position_test_project"

        # Generate initial PCB
        test_circuit.generate_kicad_project(
            str(project_dir), generate_pcb=True, force_regenerate=True
        )

        # Step 2: Manually modify R1's position in the PCB
        from kicad_pcb_api import PCBBoard

        pcb_file = project_dir / "position_test.kicad_pcb"
        pcb = PCBBoard()
        pcb.load(str(pcb_file))

        # Find R1 in the raw PCB data
        r1_footprint = self._find_footprint_by_ref(pcb, "R1")
        assert r1_footprint is not None, "R1 should exist in PCB"

        # Move R1 to a custom position
        custom_x = 75.5
        custom_y = 62.3
        custom_rotation = 90.0

        self._set_footprint_position(r1_footprint, custom_x, custom_y, custom_rotation)
        pcb.save(str(pcb_file))

        # Step 3: Regenerate circuit with R1 + R2
        @circuit(name="position_test")
        def updated_pos_circuit():
            """Updated circuit with R1 + R2."""
            r1 = Component(
                symbol="Device:R",
                ref="R1",
                value="10k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            r2 = Component(
                symbol="Device:R",
                ref="R2",
                value="20k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            return r1, r2

        updated_circuit_obj = updated_pos_circuit()

        # Regenerate (should preserve R1 position)
        updated_circuit_obj.generate_kicad_project(
            str(project_dir), generate_pcb=True, force_regenerate=False
        )

        # Step 4: Verify R1 position was preserved
        pcb_after = PCBBoard()
        pcb_after.load(str(pcb_file))

        r1_after = self._find_footprint_by_ref(pcb_after, "R1")
        assert r1_after is not None, "R1 should still exist in PCB after sync"

        # Extract position
        actual_x, actual_y, actual_rotation = self._get_footprint_position(r1_after)

        assert (
            abs(actual_x - custom_x) < 0.01
        ), f"R1 X position should be preserved. Expected {custom_x}, got {actual_x}"
        assert (
            abs(actual_y - custom_y) < 0.01
        ), f"R1 Y position should be preserved. Expected {custom_y}, got {actual_y}"
        assert (
            abs(actual_rotation - custom_rotation) < 0.01
        ), f"R1 rotation should be preserved. Expected {custom_rotation}, got {actual_rotation}"

    def test_new_component_added_at_default_position(self, temp_workspace):
        """
        Test that newly added components appear at a default position (not random).

        When R2 is added, it should be at a predictable default position (50mm, 50mm).
        """
        # Step 1: Generate initial circuit with R1
        @circuit(name="default_pos")
        def initial_default_circuit():
            """Circuit with R1."""
            r1 = Component(
                symbol="Device:R",
                ref="R1",
                value="10k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            return r1

        test_circuit = initial_default_circuit()
        project_dir = temp_workspace / "default_pos_project"

        test_circuit.generate_kicad_project(
            str(project_dir), generate_pcb=True, force_regenerate=True
        )

        # Step 2: Regenerate with R1 + R2
        @circuit(name="default_pos")
        def updated_default_circuit():
            """Updated circuit with R1 + R2."""
            r1 = Component(
                symbol="Device:R",
                ref="R1",
                value="10k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            r2 = Component(
                symbol="Device:R",
                ref="R2",
                value="20k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            return r1, r2

        updated_circuit_obj = updated_default_circuit()

        pcb_file = project_dir / "default_pos.kicad_pcb"

        updated_circuit_obj.generate_kicad_project(
            str(project_dir), generate_pcb=True, force_regenerate=False
        )

        # Step 3: Verify R2 was added at default position
        from kicad_pcb_api import PCBBoard

        pcb = PCBBoard()
        pcb.load(str(pcb_file))

        r2_footprint = self._find_footprint_by_ref(pcb, "R2")
        assert r2_footprint is not None, "R2 should be in PCB"

        # Extract position
        actual_x, actual_y, _ = self._get_footprint_position(r2_footprint)

        # Check it's at default position (50mm, 50mm) with tolerance
        assert (
            abs(actual_x - 50.0) < 1.0
        ), f"R2 should be at default X=50mm, got {actual_x}"
        assert (
            abs(actual_y - 50.0) < 1.0
        ), f"R2 should be at default Y=50mm, got {actual_y}"

    def test_multiple_additions_preserve_all_positions(self, temp_workspace):
        """
        Test that adding multiple components preserves all existing positions.

        Start: R1
        Add: R2, R3, R4
        Verify: All preserve positions, new ones at default
        """
        # Step 1: Create and place initial circuit
        @circuit(name="multi_add")
        def initial_multi():
            """Initial circuit with R1."""
            r1 = Component(
                symbol="Device:R",
                ref="R1",
                value="10k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            return r1

        test_circuit = initial_multi()
        project_dir = temp_workspace / "multi_add_project"

        test_circuit.generate_kicad_project(
            str(project_dir), generate_pcb=True, force_regenerate=True
        )

        # Step 2: Manually position R1 and R2 (when we add it)
        from kicad_pcb_api import PCBBoard

        pcb_file = project_dir / "multi_add.kicad_pcb"

        # First, manually edit R1 position
        pcb = PCBBoard()
        pcb.load(str(pcb_file))

        r1_fp = self._find_footprint_by_ref(pcb, "R1")
        if r1_fp is not None:
            self._set_footprint_position(r1_fp, 100.0, 80.0, 45.0)

        pcb.save(str(pcb_file))

        # Step 3: Add R2, R3, R4
        @circuit(name="multi_add")
        def updated_multi():
            """Updated circuit with R1-R4."""
            r1 = Component(
                symbol="Device:R",
                ref="R1",
                value="10k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            r2 = Component(
                symbol="Device:R",
                ref="R2",
                value="20k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            r3 = Component(
                symbol="Device:R",
                ref="R3",
                value="30k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            r4 = Component(
                symbol="Device:R",
                ref="R4",
                value="40k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            return r1, r2, r3, r4

        updated_circuit_obj = updated_multi()

        updated_circuit_obj.generate_kicad_project(
            str(project_dir), generate_pcb=True, force_regenerate=False
        )

        # Step 4: Verify all components present with correct positions
        pcb_final = PCBBoard()
        pcb_final.load(str(pcb_file))

        footprints = {}
        for ref in ["R1", "R2", "R3", "R4"]:
            fp = self._find_footprint_by_ref(pcb_final, ref)
            if fp:
                footprints[ref] = fp

        # R1 should be at custom position
        assert "R1" in footprints, "R1 should exist"
        r1_x, r1_y, r1_rot = self._get_footprint_position(footprints["R1"])

        assert (
            abs(r1_x - 100.0) < 0.01
        ), f"R1 X position should be preserved at 100.0, got {r1_x}"
        assert (
            abs(r1_y - 80.0) < 0.01
        ), f"R1 Y position should be preserved at 80.0, got {r1_y}"
        assert (
            abs(r1_rot - 45.0) < 0.01
        ), f"R1 rotation should be preserved at 45.0, got {r1_rot}"

        # R2, R3, R4 should exist at default positions
        for ref in ["R2", "R3", "R4"]:
            assert ref in footprints, f"{ref} should be added to PCB"
            fp_x, fp_y, _ = self._get_footprint_position(footprints[ref])
            assert (
                abs(fp_x - 50.0) < 1.0
            ), f"{ref} should be at default X=50mm, got {fp_x}"
            assert (
                abs(fp_y - 50.0) < 1.0
            ), f"{ref} should be at default Y=50mm, got {fp_y}"

        # Verify we have exactly 4 components
        assert (
            len(footprints) == 4
        ), f"PCB should have exactly 4 components, found {len(footprints)}"

    def test_component_removal_deletes_from_pcb(self, temp_workspace):
        """
        Test that removing a component from the circuit removes it from the PCB.

        Start: R1, R2, R3
        Remove: R2
        Verify: R1 and R3 remain, R2 is gone, positions preserved
        """
        # Step 1: Create circuit with 3 resistors
        @circuit(name="removal_test")
        def initial_removal():
            """Initial circuit with R1, R2, R3."""
            r1 = Component(
                symbol="Device:R",
                ref="R1",
                value="10k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            r2 = Component(
                symbol="Device:R",
                ref="R2",
                value="20k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            r3 = Component(
                symbol="Device:R",
                ref="R3",
                value="30k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            return r1, r2, r3

        test_circuit = initial_removal()
        project_dir = temp_workspace / "removal_test_project"

        test_circuit.generate_kicad_project(
            str(project_dir), generate_pcb=True, force_regenerate=True
        )

        # Step 2: Manually position components
        from kicad_pcb_api import PCBBoard

        pcb_file = project_dir / "removal_test.kicad_pcb"
        pcb = PCBBoard()
        pcb.load(str(pcb_file))

        # Move R1 and R3 to custom positions
        r1_fp = self._find_footprint_by_ref(pcb, "R1")
        if r1_fp is not None:
            self._set_footprint_position(r1_fp, 100.0, 50.0, 0.0)

        r3_fp = self._find_footprint_by_ref(pcb, "R3")
        if r3_fp is not None:
            self._set_footprint_position(r3_fp, 150.0, 100.0, 0.0)

        pcb.save(str(pcb_file))

        # Step 3: Regenerate with R1 and R3 only (remove R2)
        @circuit(name="removal_test")
        def updated_removal():
            """Updated circuit with R1 and R3 only."""
            r1 = Component(
                symbol="Device:R",
                ref="R1",
                value="10k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            r3 = Component(
                symbol="Device:R",
                ref="R3",
                value="30k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            return r1, r3

        updated_circuit_obj = updated_removal()

        updated_circuit_obj.generate_kicad_project(
            str(project_dir), generate_pcb=True, force_regenerate=False
        )

        # Step 4: Verify R2 is removed, R1 and R3 positions preserved
        pcb_final = PCBBoard()
        pcb_final.load(str(pcb_file))

        r1_fp = self._find_footprint_by_ref(pcb_final, "R1")
        r2_fp = self._find_footprint_by_ref(pcb_final, "R2")
        r3_fp = self._find_footprint_by_ref(pcb_final, "R3")

        assert (
            r1_fp is not None
        ), "R1 should remain in PCB after removing R2"
        assert (
            r3_fp is not None
        ), "R3 should remain in PCB after removing R2"
        assert (
            r2_fp is None
        ), "R2 should be removed from PCB when removed from circuit"

        # Verify R1 and R3 positions are preserved
        r1_x, _, _ = self._get_footprint_position(r1_fp)
        assert (
            abs(r1_x - 100.0) < 0.01
        ), f"R1 X position should be preserved at 100.0, got {r1_x}"

        r3_x, _, _ = self._get_footprint_position(r3_fp)
        assert (
            abs(r3_x - 150.0) < 0.01
        ), f"R3 X position should be preserved at 150.0, got {r3_x}"

        # Verify exactly 2 components remain
        all_refs = self._get_footprint_refs(pcb_final)
        assert (
            len(all_refs) == 2
        ), f"PCB should have exactly 2 components after removing R2, found {len(all_refs)}: {all_refs}"

    def test_force_regenerate_loses_position(self, temp_workspace):
        """
        Test that force_pcb_regenerate=True regenerates PCB from scratch (loses manual placement).

        This verifies the safety mechanism: when explicitly requested, full regeneration happens.
        """
        # Step 1: Create and position initial circuit
        @circuit(name="force_regen")
        def initial_force():
            """Initial circuit with R1."""
            r1 = Component(
                symbol="Device:R",
                ref="R1",
                value="10k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            return r1

        test_circuit = initial_force()
        project_dir = temp_workspace / "force_regen_project"

        test_circuit.generate_kicad_project(
            str(project_dir), generate_pcb=True, force_regenerate=True
        )

        # Step 2: Manually move R1 to custom position
        from kicad_pcb_api import PCBBoard

        pcb_file = project_dir / "force_regen.kicad_pcb"
        pcb = PCBBoard()
        pcb.load(str(pcb_file))

        custom_x = 200.0
        custom_y = 150.0
        custom_rotation = 180.0

        r1_fp = self._find_footprint_by_ref(pcb, "R1")
        if r1_fp is not None:
            self._set_footprint_position(r1_fp, custom_x, custom_y, custom_rotation)

        pcb.save(str(pcb_file))

        # Step 3: Regenerate with force_pcb_regenerate=True
        @circuit(name="force_regen")
        def updated_force():
            """Updated circuit with R1 + R2."""
            r1 = Component(
                symbol="Device:R",
                ref="R1",
                value="10k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            r2 = Component(
                symbol="Device:R",
                ref="R2",
                value="20k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            return r1, r2

        updated_circuit_obj = updated_force()

        # Force regenerate (should reset positions)
        updated_circuit_obj.generate_kicad_project(
            str(project_dir), generate_pcb=True, force_regenerate=True
        )

        # Step 4: Verify R1 position was reset (not preserved)
        pcb_after = PCBBoard()
        pcb_after.load(str(pcb_file))

        r1_after = self._find_footprint_by_ref(pcb_after, "R1")
        assert r1_after is not None, "R1 should exist after regeneration"

        # Extract position
        actual_x, _, _ = self._get_footprint_position(r1_after)

        # Position should NOT match custom position (should be reset)
        assert not (
            abs(actual_x - custom_x) < 0.01
        ), f"With force_regenerate=True, R1 position should be reset, not preserved at {custom_x}"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
