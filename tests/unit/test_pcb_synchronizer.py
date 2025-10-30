"""
Unit tests for PCBSynchronizer.

Tests the PCB synchronization functionality that preserves manual placement
while adding/removing/updating components.
"""

import tempfile
from pathlib import Path

import pytest
from kicad_pcb_api import PCBBoard

from circuit_synth.kicad.pcb_gen.pcb_synchronizer import PCBSynchronizer, PCBSyncReport


class TestPCBSynchronizerBasics:
    """Test basic PCBSynchronizer functionality."""

    def test_synchronizer_init_with_existing_pcb(self, tmp_path):
        """Test synchronizer initializes with existing PCB file."""
        # Create a minimal PCB file
        pcb_path = tmp_path / "test.kicad_pcb"
        project_name = "test"

        # Create minimal PCB using kicad-pcb-api
        pcb = PCBBoard()
        pcb.save(str(pcb_path))

        # Create minimal schematic
        sch_path = tmp_path / f"{project_name}.kicad_sch"
        sch_content = """(kicad_sch (version 20230121) (generator eeschema)
  (paper "A4")
  (lib_symbols)
  (symbol_instances)
)"""
        sch_path.write_text(sch_content)

        # Initialize synchronizer
        sync = PCBSynchronizer(
            pcb_path=str(pcb_path),
            project_dir=tmp_path,
            project_name=project_name
        )

        assert sync.pcb_path == pcb_path
        assert sync.project_dir == tmp_path
        assert sync.project_name == project_name
        assert sync.pcb is not None

    def test_synchronizer_raises_on_missing_pcb(self, tmp_path):
        """Test synchronizer raises error when PCB doesn't exist."""
        pcb_path = tmp_path / "nonexistent.kicad_pcb"

        with pytest.raises(FileNotFoundError):
            PCBSynchronizer(
                pcb_path=str(pcb_path),
                project_dir=tmp_path,
                project_name="test"
            )


class TestComponentExtraction:
    """Test component extraction from schematics."""

    def test_extract_components_from_single_schematic(self, tmp_path):
        """Test extracting components from a single schematic file."""
        project_name = "test"

        # Create PCB
        pcb_path = tmp_path / f"{project_name}.kicad_pcb"
        pcb = PCBBoard()
        pcb.save(str(pcb_path))

        # Create schematic with components
        sch_path = tmp_path / f"{project_name}.kicad_sch"
        sch_content = """(kicad_sch (version 20230121) (generator eeschema)
  (paper "A4")
  (lib_symbols
    (symbol "Device:R" (pin_names (offset 0)) (in_bom yes) (on_board yes))
  )
  (symbol (lib_id "Device:R") (at 50 50 0)
    (property "Reference" "R1" (at 50 48 0))
    (property "Value" "10k" (at 50 52 0))
    (property "Footprint" "Resistor_SMD:R_0603_1608Metric" (at 50 54 0))
  )
  (symbol_instances)
)"""
        sch_path.write_text(sch_content)

        # Initialize synchronizer and extract
        sync = PCBSynchronizer(str(pcb_path), tmp_path, project_name)
        components = sync._extract_components_from_schematics()

        assert len(components) == 1
        assert components[0]["reference"] == "R1"
        assert components[0]["value"] == "10k"
        assert components[0]["footprint"] == "Resistor_SMD:R_0603_1608Metric"


class TestComponentMatching:
    """Test component matching between schematic and PCB."""

    def test_match_components_by_reference(self, tmp_path):
        """Test matching components by reference designator."""
        project_name = "test"

        # Create PCB with footprint
        pcb_path = tmp_path / f"{project_name}.kicad_pcb"
        pcb = PCBBoard()
        pcb.add_footprint_from_library(
            footprint_id="Resistor_SMD:R_0603_1608Metric",
            reference="R1",
            x=100.0,
            y=100.0,
            rotation=0.0,
            value="10k"
        )
        pcb.save(str(pcb_path))

        # Create schematic
        sch_path = tmp_path / f"{project_name}.kicad_sch"
        sch_content = """(kicad_sch (version 20230121) (generator eeschema)
  (paper "A4")
  (lib_symbols)
  (symbol (lib_id "Device:R") (at 50 50 0)
    (property "Reference" "R1" (at 50 48 0))
    (property "Value" "10k" (at 50 52 0))
    (property "Footprint" "Resistor_SMD:R_0603_1608Metric" (at 50 54 0))
  )
  (symbol_instances)
)"""
        sch_path.write_text(sch_content)

        # Initialize and match
        sync = PCBSynchronizer(str(pcb_path), tmp_path, project_name)
        sch_components = sync._extract_components_from_schematics()
        pcb_footprints = sync._get_existing_footprints()
        matches = sync._match_components(sch_components, pcb_footprints)

        assert "R1" in matches
        assert matches["R1"] == "R1"


class TestAddNewFootprints:
    """Test adding new footprints to PCB."""

    def test_add_new_footprint_from_schematic(self, tmp_path):
        """Test adding a footprint that exists in schematic but not PCB."""
        project_name = "test"

        # Create empty PCB
        pcb_path = tmp_path / f"{project_name}.kicad_pcb"
        pcb = PCBBoard()
        pcb.save(str(pcb_path))

        # Create schematic with R1
        sch_path = tmp_path / f"{project_name}.kicad_sch"
        sch_content = """(kicad_sch (version 20230121) (generator eeschema)
  (paper "A4")
  (lib_symbols)
  (symbol (lib_id "Device:R") (at 50 50 0)
    (property "Reference" "R1" (at 50 48 0))
    (property "Value" "10k" (at 50 52 0))
    (property "Footprint" "Resistor_SMD:R_0603_1608Metric" (at 50 54 0))
  )
  (symbol_instances)
)"""
        sch_path.write_text(sch_content)

        # Initialize synchronizer
        sync = PCBSynchronizer(str(pcb_path), tmp_path, project_name)

        # Get components and matches (should be empty)
        sch_components = sync._extract_components_from_schematics()
        pcb_footprints = sync._get_existing_footprints()
        matches = sync._match_components(sch_components, pcb_footprints)

        # Add new footprints
        report = PCBSyncReport()
        sync._add_new_footprints(sch_components, matches, report)

        assert len(report.added) == 1
        assert "R1" in report.added
        assert len(report.errors) == 0


class TestRemoveDeletedFootprints:
    """Test removing footprints that no longer exist in schematic."""

    def test_remove_footprint_not_in_schematic(self, tmp_path):
        """Test removing a footprint that's in PCB but not schematic."""
        project_name = "test"

        # Create PCB with R1 footprint
        pcb_path = tmp_path / f"{project_name}.kicad_pcb"
        pcb = PCBBoard()
        pcb.add_footprint_from_library(
            footprint_id="Resistor_SMD:R_0603_1608Metric",
            reference="R1",
            x=100.0,
            y=100.0,
            rotation=0.0,
            value="10k"
        )
        pcb.save(str(pcb_path))

        # Create empty schematic (no components)
        sch_path = tmp_path / f"{project_name}.kicad_sch"
        sch_content = """(kicad_sch (version 20230121) (generator eeschema)
  (paper "A4")
  (lib_symbols)
  (symbol_instances)
)"""
        sch_path.write_text(sch_content)

        # Initialize synchronizer
        sync = PCBSynchronizer(str(pcb_path), tmp_path, project_name)

        # Get footprints and matches
        pcb_footprints = sync._get_existing_footprints()
        matches = {}  # No matches (schematic is empty)

        # Remove deleted footprints
        report = PCBSyncReport()
        sync._remove_deleted_footprints(pcb_footprints, matches, report)

        assert len(report.removed) == 1
        assert "R1" in report.removed


class TestPositionPreservation:
    """Test that manual footprint placements are preserved."""

    def test_preserve_footprint_position_on_sync(self, tmp_path):
        """Test that existing footprint positions are preserved during sync."""
        project_name = "test"
        original_x = 123.45
        original_y = 678.90

        # Create PCB with R1 at specific position
        pcb_path = tmp_path / f"{project_name}.kicad_pcb"
        pcb = PCBBoard()
        pcb.add_footprint_from_library(
            footprint_id="Resistor_SMD:R_0603_1608Metric",
            reference="R1",
            x=original_x,
            y=original_y,
            rotation=0.0,
            value="10k"
        )
        pcb.save(str(pcb_path))

        # Create schematic with R1 (value unchanged)
        sch_path = tmp_path / f"{project_name}.kicad_sch"
        sch_content = """(kicad_sch (version 20230121) (generator eeschema)
  (paper "A4")
  (lib_symbols)
  (symbol (lib_id "Device:R") (at 50 50 0)
    (property "Reference" "R1" (at 50 48 0))
    (property "Value" "10k" (at 50 52 0))
    (property "Footprint" "Resistor_SMD:R_0603_1608Metric" (at 50 54 0))
  )
  (symbol_instances)
)"""
        sch_path.write_text(sch_content)

        # Run synchronization
        sync = PCBSynchronizer(str(pcb_path), tmp_path, project_name)
        sch_components = sync._extract_components_from_schematics()
        matches = sync._match_components(sch_components, sync._get_existing_footprints())
        report = PCBSyncReport()
        sync._update_existing_footprints(sch_components, matches, report)

        # Verify position preserved
        pcb_after = PCBBoard()
        pcb_after.load(str(pcb_path))
        r1_after = pcb_after.get_footprint("R1")

        assert r1_after is not None
        assert abs(r1_after.position.x - original_x) < 0.01
        assert abs(r1_after.position.y - original_y) < 0.01
        assert "R1" in report.preserved


class TestValueUpdate:
    """Test updating component values while preserving position."""

    def test_update_value_preserve_position(self, tmp_path):
        """Test updating component value while preserving position."""
        project_name = "test"
        original_x = 123.45
        original_y = 678.90

        # Create PCB with R1 value="10k"
        pcb_path = tmp_path / f"{project_name}.kicad_pcb"
        pcb = PCBBoard()
        pcb.add_footprint_from_library(
            footprint_id="Resistor_SMD:R_0603_1608Metric",
            reference="R1",
            x=original_x,
            y=original_y,
            rotation=0.0,
            value="10k"
        )
        pcb.save(str(pcb_path))

        # Create schematic with R1 value="22k" (changed)
        sch_path = tmp_path / f"{project_name}.kicad_sch"
        sch_content = """(kicad_sch (version 20230121) (generator eeschema)
  (paper "A4")
  (lib_symbols)
  (symbol (lib_id "Device:R") (at 50 50 0)
    (property "Reference" "R1" (at 50 48 0))
    (property "Value" "22k" (at 50 52 0))
    (property "Footprint" "Resistor_SMD:R_0603_1608Metric" (at 50 54 0))
  )
  (symbol_instances)
)"""
        sch_path.write_text(sch_content)

        # Run synchronization
        sync = PCBSynchronizer(str(pcb_path), tmp_path, project_name)
        sch_components = sync._extract_components_from_schematics()
        matches = sync._match_components(sch_components, sync._get_existing_footprints())
        report = PCBSyncReport()
        sync._update_existing_footprints(sch_components, matches, report)
        sync.pcb.save(str(pcb_path))

        # Verify value updated, position preserved
        pcb_after = PCBBoard()
        pcb_after.load(str(pcb_path))
        r1_after = pcb_after.get_footprint("R1")

        assert r1_after is not None
        assert r1_after.value == "22k"
        assert abs(r1_after.position.x - original_x) < 0.01
        assert abs(r1_after.position.y - original_y) < 0.01
        assert "R1" in report.updated


class TestSyncReport:
    """Test sync report generation."""

    def test_sync_report_to_dict(self):
        """Test converting sync report to dictionary."""
        report = PCBSyncReport()
        report.matched["R1"] = "R1"
        report.added.append("R2")
        report.removed.append("R3")
        report.updated.append("R4")
        report.preserved.append("R5")
        report.errors.append("Test error")

        report_dict = report.to_dict()

        assert report_dict["matched"] == 1
        assert report_dict["added"] == 1
        assert report_dict["removed"] == 1
        assert report_dict["updated"] == 1
        assert report_dict["preserved"] == 1
        assert report_dict["errors"] == 1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
