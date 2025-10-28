"""
Integration tests for component rename synchronization.

Tests the complete flow of renaming components in KiCad and ensuring
the sync system properly detects and handles the rename without losing
component identity, position, or other properties.
"""

import shutil
import tempfile
from pathlib import Path
from unittest.mock import Mock

import pytest
from kicad_sch_api.core.types import Point, Schematic, SchematicSymbol

from circuit_synth.kicad.schematic.synchronizer import APISynchronizer


class TestComponentRenameSync:
    """Test component rename detection and synchronization."""

    @pytest.fixture
    def temp_workspace(self):
        """Create temporary workspace for testing."""
        with tempfile.TemporaryDirectory() as tmpdir:
            yield Path(tmpdir)

    @pytest.fixture
    def simple_schematic_path(self, temp_workspace):
        """Create a simple schematic with one resistor."""
        schematic = Schematic()

        # Add a resistor R1
        r1_uuid = schematic.add_component(
            library_id="Device:R",
            reference="R1",
            value="10k",
            position=(100.0, 50.0),
            footprint="Resistor_SMD:R_0603_1608Metric",
        )

        # Save schematic
        sch_path = temp_workspace / "test.kicad_sch"
        schematic.save(str(sch_path))

        return sch_path, r1_uuid

    def test_rename_detected_by_uuid_match(self, simple_schematic_path):
        """Test that renaming R1->R2 in KiCad is detected by UUID matching."""
        sch_path, r1_uuid = simple_schematic_path

        # Load the schematic
        schematic = Schematic.load(str(sch_path))

        # Simulate user renaming R1 to R2 in KiCad
        r1_component = None
        for comp in schematic.components:
            if comp.reference == "R1":
                r1_component = comp
                break

        assert r1_component is not None, "R1 should exist"
        original_uuid = r1_component.uuid

        # Rename to R2
        r1_component.reference = "R2"
        schematic.save(str(sch_path))

        # Now create synchronizer with circuit that still expects R1
        # (simulating Python code hasn't been updated yet)
        synchronizer = APISynchronizer(str(sch_path), preserve_user_components=False)

        # Create mock circuit with R1 (old reference) but same UUID
        mock_circuit = Mock()
        mock_r1 = Mock()
        mock_r1.reference = "R1"
        mock_r1.ref = "R1"
        mock_r1.value = "10k"
        mock_r1.symbol = "Device:R"
        mock_r1.footprint = "Resistor_SMD:R_0603_1608Metric"
        mock_r1.position = Point(100.0, 50.0)
        mock_r1.uuid = original_uuid  # Same UUID as renamed component
        mock_r1._pins = {}

        mock_circuit._components = {"R1": mock_r1}
        mock_circuit._subcircuits = []
        mock_circuit.nets = []

        # Extract components and match
        circuit_components = synchronizer._extract_circuit_components(mock_circuit)
        kicad_components = {c.reference: c for c in synchronizer.schematic.components}

        matches = synchronizer._match_components(circuit_components, kicad_components)

        # Should match R1 (circuit) to R2 (KiCad) by UUID
        assert "R1" in matches, "R1 should be matched"
        assert matches["R1"] == "R2", "R1 should match to renamed R2"

    def test_rename_detected_by_position_match(self, temp_workspace):
        """Test that rename is detected by position+properties when UUID not available."""
        # Create schematic without preserving UUIDs (simulate legacy workflow)
        schematic = Schematic()

        # Add resistor at specific position
        schematic.add_component(
            library_id="Device:R",
            reference="R2",  # Already renamed in KiCad
            value="10k",
            position=(100.0, 50.0),
            footprint="Resistor_SMD:R_0603_1608Metric",
        )

        sch_path = temp_workspace / "test.kicad_sch"
        schematic.save(str(sch_path))

        # Create synchronizer
        synchronizer = APISynchronizer(str(sch_path), preserve_user_components=False)

        # Create mock circuit with R1 (old reference) at same position
        mock_circuit = Mock()
        mock_r1 = Mock()
        mock_r1.reference = "R1"
        mock_r1.ref = "R1"
        mock_r1.value = "10k"
        mock_r1.symbol = "Device:R"
        mock_r1.footprint = "Resistor_SMD:R_0603_1608Metric"
        mock_r1.position = Point(100.0, 50.0)  # Same position
        mock_r1.uuid = None  # No UUID
        mock_r1._pins = {}

        mock_circuit._components = {"R1": mock_r1}
        mock_circuit._subcircuits = []
        mock_circuit.nets = []

        # Extract components and match
        circuit_components = synchronizer._extract_circuit_components(mock_circuit)
        kicad_components = {c.reference: c for c in synchronizer.schematic.components}

        matches = synchronizer._match_components(circuit_components, kicad_components)

        # Should match R1 to R2 by position+properties
        assert "R1" in matches, "R1 should be matched"
        assert matches["R1"] == "R2", "R1 should match to R2 by position"

    def test_rename_with_position_change_matched_by_uuid(self, simple_schematic_path):
        """Test UUID matching works even when position changes."""
        sch_path, r1_uuid = simple_schematic_path

        # Load and modify
        schematic = Schematic.load(str(sch_path))

        r1 = None
        for comp in schematic.components:
            if comp.reference == "R1":
                r1 = comp
                break

        assert r1 is not None
        original_uuid = r1.uuid

        # Change both reference AND position
        r1.reference = "R10"
        r1.position = Point(200.0, 100.0)  # Moved far away
        schematic.save(str(sch_path))

        # Create synchronizer
        synchronizer = APISynchronizer(str(sch_path), preserve_user_components=False)

        # Circuit still has R1 at old position but same UUID
        mock_circuit = Mock()
        mock_r1 = Mock()
        mock_r1.reference = "R1"
        mock_r1.ref = "R1"
        mock_r1.value = "10k"
        mock_r1.symbol = "Device:R"
        mock_r1.footprint = "Resistor_SMD:R_0603_1608Metric"
        mock_r1.position = Point(100.0, 50.0)  # Old position
        mock_r1.uuid = original_uuid  # Same UUID
        mock_r1._pins = {}

        mock_circuit._components = {"R1": mock_r1}
        mock_circuit._subcircuits = []
        mock_circuit.nets = []

        # Extract and match
        circuit_components = synchronizer._extract_circuit_components(mock_circuit)
        kicad_components = {c.reference: c for c in synchronizer.schematic.components}

        matches = synchronizer._match_components(circuit_components, kicad_components)

        # UUID should match despite position change
        assert "R1" in matches
        assert matches["R1"] == "R10"

    def test_no_duplicate_components_after_rename(self, simple_schematic_path):
        """Test that rename doesn't create duplicate components."""
        sch_path, r1_uuid = simple_schematic_path

        # Load and rename
        schematic = Schematic.load(str(sch_path))

        r1 = None
        for comp in schematic.components:
            if comp.reference == "R1":
                r1 = comp
                break

        original_uuid = r1.uuid
        r1.reference = "R2"
        schematic.save(str(sch_path))

        # Synchronize with circuit expecting R1
        synchronizer = APISynchronizer(str(sch_path), preserve_user_components=False)

        mock_circuit = Mock()
        mock_r1 = Mock()
        mock_r1.reference = "R1"
        mock_r1.ref = "R1"
        mock_r1.value = "10k"
        mock_r1.symbol = "Device:R"
        mock_r1.footprint = "Resistor_SMD:R_0603_1608Metric"
        mock_r1.position = Point(100.0, 50.0)
        mock_r1.uuid = original_uuid
        mock_r1._pins = {}

        mock_circuit._components = {"R1": mock_r1}
        mock_circuit._subcircuits = []
        mock_circuit.nets = []
        mock_circuit.name = "test_circuit"

        # Perform sync
        report = synchronizer.sync_with_circuit(mock_circuit)

        # Should have 1 match (R1->R2), no additions, 1 rename
        assert len(report.matched) == 1
        assert len(report.added) == 0
        assert len(report.removed) == 0
        assert len(report.renamed) == 1
        assert report.renamed[0] == ("R2", "R1")  # Renamed back from R2 to R1

    def test_multiple_renames_handled_correctly(self, temp_workspace):
        """Test handling multiple component renames in same sync."""
        # Create schematic with 3 components
        schematic = Schematic()

        r1_uuid = schematic.add_component(
            library_id="Device:R",
            reference="R1",
            value="10k",
            position=(100.0, 50.0),
        )

        r2_uuid = schematic.add_component(
            library_id="Device:R",
            reference="R2",
            value="20k",
            position=(150.0, 50.0),
        )

        c1_uuid = schematic.add_component(
            library_id="Device:C",
            reference="C1",
            value="100nF",
            position=(200.0, 50.0),
        )

        sch_path = temp_workspace / "test.kicad_sch"
        schematic.save(str(sch_path))

        # Reload and rename all components
        schematic = Schematic.load(str(sch_path))
        components_list = list(schematic.components)

        # Store original UUIDs
        uuid_map = {}
        for comp in components_list:
            uuid_map[comp.reference] = comp.uuid

        # Rename: R1->R10, R2->R20, C1->C10
        for comp in components_list:
            if comp.reference == "R1":
                comp.reference = "R10"
            elif comp.reference == "R2":
                comp.reference = "R20"
            elif comp.reference == "C1":
                comp.reference = "C10"

        schematic.save(str(sch_path))

        # Create synchronizer
        synchronizer = APISynchronizer(str(sch_path), preserve_user_components=False)

        # Circuit still has old references
        mock_circuit = Mock()
        mock_r1 = Mock()
        mock_r1.reference = "R1"
        mock_r1.ref = "R1"
        mock_r1.value = "10k"
        mock_r1.symbol = "Device:R"
        mock_r1.position = Point(100.0, 50.0)
        mock_r1.uuid = uuid_map["R1"]
        mock_r1._pins = {}

        mock_r2 = Mock()
        mock_r2.reference = "R2"
        mock_r2.ref = "R2"
        mock_r2.value = "20k"
        mock_r2.symbol = "Device:R"
        mock_r2.position = Point(150.0, 50.0)
        mock_r2.uuid = uuid_map["R2"]
        mock_r2._pins = {}

        mock_c1 = Mock()
        mock_c1.reference = "C1"
        mock_c1.ref = "C1"
        mock_c1.value = "100nF"
        mock_c1.symbol = "Device:C"
        mock_c1.position = Point(200.0, 50.0)
        mock_c1.uuid = uuid_map["C1"]
        mock_c1._pins = {}

        mock_circuit._components = {"R1": mock_r1, "R2": mock_r2, "C1": mock_c1}
        mock_circuit._subcircuits = []
        mock_circuit.nets = []

        # Extract and match
        circuit_components = synchronizer._extract_circuit_components(mock_circuit)
        kicad_components = {c.reference: c for c in synchronizer.schematic.components}

        matches = synchronizer._match_components(circuit_components, kicad_components)

        # All three should match by UUID
        assert len(matches) == 3
        assert matches["R1"] == "R10"
        assert matches["R2"] == "R20"
        assert matches["C1"] == "C10"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
