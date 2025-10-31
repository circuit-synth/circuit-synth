"""
Unit tests for ComponentManager deletion logic.

Tests component removal from schematics using the kicad-sch-api,
including reference-based and UUID-based removal approaches.
"""

import tempfile
from pathlib import Path

import pytest
import kicad_sch_api as ksa

from circuit_synth.kicad.schematic.component_manager import ComponentManager


class TestComponentManagerDeletion:
    """Test ComponentManager component removal functionality."""

    @pytest.fixture
    def temp_schematic(self):
        """Create a temporary schematic for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create a simple schematic with 2 components
            sch = ksa.Schematic.create()
            c1 = sch.components.add(
                lib_id="Device:R",
                reference="R1",
                value="10k",
                position=(50, 50)
            )
            c2 = sch.components.add(
                lib_id="Device:R",
                reference="R2",
                value="20k",
                position=(100, 50)
            )

            # Save schematic
            sch_file = tmpdir_path / "test.kicad_sch"
            sch.save(str(sch_file))

            yield sch_file, c1.uuid, c2.uuid

    def test_remove_component_by_reference(self, temp_schematic):
        """Test removing a component by reference."""
        sch_file, r1_uuid, r2_uuid = temp_schematic

        # Load schematic
        sch = ksa.Schematic.load(str(sch_file))
        manager = ComponentManager(sch)

        # Verify initial state
        assert len(sch.components) == 2
        assert manager.find_component("R1") is not None
        assert manager.find_component("R2") is not None

        # Remove R2
        result = manager.remove_component("R2")
        assert result is True

        # Verify R2 is gone
        assert len(sch.components) == 1
        assert manager.find_component("R1") is not None
        assert manager.find_component("R2") is None

    def test_remove_component_persistence(self, temp_schematic):
        """Test that removed components stay removed after save/reload."""
        sch_file, r1_uuid, r2_uuid = temp_schematic

        # Load, remove, and save
        sch = ksa.Schematic.load(str(sch_file))
        manager = ComponentManager(sch)

        manager.remove_component("R2")
        sch.save(str(sch_file))

        # Reload and verify
        sch2 = ksa.Schematic.load(str(sch_file))
        manager2 = ComponentManager(sch2)

        assert len(sch2.components) == 1
        assert manager2.find_component("R1") is not None
        assert manager2.find_component("R2") is None

    def test_remove_nonexistent_component(self, temp_schematic):
        """Test removing a non-existent component returns False."""
        sch_file, _, _ = temp_schematic

        sch = ksa.Schematic.load(str(sch_file))
        manager = ComponentManager(sch)

        # Try to remove non-existent component
        result = manager.remove_component("R999")
        assert result is False

        # Verify no components were removed
        assert len(sch.components) == 2

    def test_remove_by_uuid(self, temp_schematic):
        """Test removing a component by UUID."""
        sch_file, r1_uuid, r2_uuid = temp_schematic

        sch = ksa.Schematic.load(str(sch_file))
        manager = ComponentManager(sch)

        # Remove R2 by UUID
        result = manager.remove_component("R2", uuid=r2_uuid)
        assert result is True

        # Verify R2 is gone
        assert len(sch.components) == 1
        assert manager.find_component("R1") is not None
        assert manager.find_component("R2") is None

    def test_remove_updates_component_index(self, temp_schematic):
        """Test that component index is updated after removal."""
        sch_file, _, _ = temp_schematic

        sch = ksa.Schematic.load(str(sch_file))
        manager = ComponentManager(sch)

        # Remove R2
        manager.remove_component("R2")

        # Verify index is updated
        # Index keys are stored as "{reference}_unit{n}" format
        assert "R1_unit1" in manager._component_index
        assert "R2_unit1" not in manager._component_index
        assert len(manager._component_index) == 1

    def test_remove_multiple_components_sequential(self, temp_schematic):
        """Test removing multiple components sequentially."""
        sch_file, _, _ = temp_schematic

        sch = ksa.Schematic.load(str(sch_file))
        manager = ComponentManager(sch)

        # Remove R2 first
        result1 = manager.remove_component("R2")
        assert result1 is True
        assert len(sch.components) == 1

        # Remove R1 next
        result2 = manager.remove_component("R1")
        assert result2 is True
        assert len(sch.components) == 0

    def test_remove_preserves_other_components(self, temp_schematic):
        """Test that removing one component doesn't affect others."""
        sch_file, r1_uuid, r2_uuid = temp_schematic

        sch = ksa.Schematic.load(str(sch_file))
        manager = ComponentManager(sch)

        # Get R1 details before removal
        r1_before = manager.find_component("R1")
        r1_value = r1_before.value
        r1_position = r1_before.position

        # Remove R2
        manager.remove_component("R2")

        # Verify R1 is unchanged
        r1_after = manager.find_component("R1")
        assert r1_after.value == r1_value
        assert r1_after.position == r1_position

    def test_remove_with_large_circuit(self):
        """Test removing a component from a larger circuit."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            sch_file = tmpdir_path / "large.kicad_sch"

            # Create schematic with 10 components
            sch = ksa.Schematic.create()
            for i in range(10):
                sch.components.add(
                    lib_id="Device:R",
                    reference=f"R{i+1}",
                    value=f"{(i+1)*10}k",
                    position=(50 + i*10, 50)
                )

            sch.save(str(sch_file))

            # Load and remove components
            sch = ksa.Schematic.load(str(sch_file))
            manager = ComponentManager(sch)

            # Remove R5
            result = manager.remove_component("R5")
            assert result is True
            assert len(sch.components) == 9

            # Save and reload
            sch.save(str(sch_file))
            sch2 = ksa.Schematic.load(str(sch_file))
            manager2 = ComponentManager(sch2)

            # Verify R5 is gone
            assert manager2.find_component("R5") is None
            assert len(sch2.components) == 9

            # Verify other components still exist
            for i in range(10):
                if i + 1 != 5:  # Skip R5
                    assert manager2.find_component(f"R{i+1}") is not None

    def test_remove_and_re_add_same_reference(self, temp_schematic):
        """Test that we can re-add a component with the same reference after removing."""
        sch_file, _, _ = temp_schematic

        sch = ksa.Schematic.load(str(sch_file))
        manager = ComponentManager(sch)

        # Remove R2
        manager.remove_component("R2")
        assert manager.find_component("R2") is None

        # Re-add R2 with different value
        new_r2 = manager.add_component(
            library_id="Device:R",
            reference="R2",
            value="30k",
            position=(100, 50)
        )
        assert new_r2 is not None
        assert manager.find_component("R2") is not None
        assert manager.find_component("R2").value == "30k"

    def test_remove_with_properties(self):
        """Test removing a component that has custom properties."""
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)
            sch_file = tmpdir_path / "props.kicad_sch"

            # Create schematic with component with properties
            sch = ksa.Schematic.create()
            sch.components.add(
                lib_id="Device:R",
                reference="R1",
                value="10k",
                position=(50, 50),
                MPN="RC0603FR-0710KL",
                Tolerance="1%"
            )

            sch.save(str(sch_file))

            # Load and remove
            sch = ksa.Schematic.load(str(sch_file))
            manager = ComponentManager(sch)

            result = manager.remove_component("R1")
            assert result is True
            assert len(sch.components) == 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
