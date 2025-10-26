"""
Tests for blank PCB generation (Issue #249)

Verify that when generate_pcb=True is set on a blank schematic (no components),
circuit-synth generates a valid blank .kicad_pcb file instead of failing.
"""

import tempfile
from pathlib import Path

import pytest

from circuit_synth import circuit


class TestBlankPCBGeneration:
    """Test blank PCB file generation for empty schematics"""

    def test_blank_circuit_generates_pcb_file(self, tmp_path):
        """
        Test that a blank circuit generates a valid .kicad_pcb file.

        This verifies Issue #249: When generate_pcb=True is set but the
        schematic has no components, a blank .kicad_pcb file should still
        be generated.
        """

        # Define blank circuit
        @circuit(name="blank")
        def blank_circuit():
            pass

        # Create circuit instance
        test_circuit = blank_circuit()

        # Generate KiCad project with PCB generation enabled
        project_dir = tmp_path / "blank_project"
        result = test_circuit.generate_kicad_project(
            str(project_dir), generate_pcb=True, force_regenerate=True
        )

        # Verify the result indicates success
        assert result is not False, "PCB generation should not fail for blank circuits"

        # Verify .kicad_pcb file was created (named after project, not circuit)
        pcb_file = project_dir / "blank_project.kicad_pcb"
        assert (
            pcb_file.exists()
        ), f"blank_project.kicad_pcb should be created, but file not found at {pcb_file}"

        # Verify PCB file has content (not empty)
        assert pcb_file.stat().st_size > 0, "PCB file should have content"

        # Verify PCB file has proper KiCad structure
        pcb_content = pcb_file.read_text()
        assert (
            "(kicad_pcb" in pcb_content
        ), "PCB file should contain KiCad PCB structure"
        assert (
            'generator "pcbnew"' in pcb_content
        ), "PCB file should have generator attribute"

    def test_blank_circuit_creates_all_three_core_files(self, tmp_path):
        """
        Test that a blank circuit creates all three core KiCad project files.

        Expected result:
        - .kicad_pro (project file named after project directory)
        - .kicad_sch (schematic file named after project directory)
        - .kicad_pcb (PCB file named after project directory)
        """

        @circuit(name="test_circuit")
        def blank_circuit():
            pass

        test_circuit = blank_circuit()
        project_dir = tmp_path / "test_project"

        result = test_circuit.generate_kicad_project(
            str(project_dir), generate_pcb=True, force_regenerate=True
        )

        # Verify all three core files exist (named after project directory)
        pro_file = project_dir / "test_project.kicad_pro"
        sch_file = project_dir / "test_project.kicad_sch"
        pcb_file = project_dir / "test_project.kicad_pcb"

        assert pro_file.exists(), ".kicad_pro file should be created"
        assert sch_file.exists(), ".kicad_sch file should be created"
        assert pcb_file.exists(), ".kicad_pcb file should be created"

    def test_blank_pcb_has_valid_structure(self, tmp_path):
        """
        Test that blank PCB has valid KiCad 9.0 structure with default settings.
        """

        @circuit(name="blank_circuit")
        def blank_circuit():
            pass

        test_circuit = blank_circuit()
        project_dir = tmp_path / "blank_valid"

        test_circuit.generate_kicad_project(
            str(project_dir), generate_pcb=True, force_regenerate=True
        )

        pcb_file = project_dir / "blank_valid.kicad_pcb"
        pcb_content = pcb_file.read_text()

        # Verify essential KiCad PCB elements
        assert "(kicad_pcb" in pcb_content, "Should have kicad_pcb element"
        assert "version" in pcb_content, "Should have version attribute"
        assert "generator" in pcb_content, "Should have generator attribute"
        # A valid blank PCB should have layers definition or be minimal
        # Exact structure depends on implementation

    def test_blank_pcb_can_be_opened_in_kicad(self, tmp_path):
        """
        Test that the generated blank PCB can be loaded as valid KiCad structure.

        This is a minimal validation test - it doesn't verify the file can
        actually open in KiCad, but it verifies the structure is parseable.
        """

        @circuit(name="blank_circuit")
        def blank_circuit():
            pass

        test_circuit = blank_circuit()
        project_dir = tmp_path / "blank_kicad"

        test_circuit.generate_kicad_project(
            str(project_dir), generate_pcb=True, force_regenerate=True
        )

        pcb_file = project_dir / "blank_kicad.kicad_pcb"

        # Try to parse the PCB file content
        # A minimal valid PCB should at least have the opening (kicad_pcb)
        pcb_content = pcb_file.read_text()

        # Count parentheses to verify balanced S-expression structure
        # This is a quick sanity check
        open_count = pcb_content.count("(")
        close_count = pcb_content.count(")")
        assert (
            open_count == close_count
        ), f"PCB file should have balanced parentheses, got {open_count} open, {close_count} close"
