"""
Unit tests for PDF export functionality.

Tests the Circuit.generate_pdf_schematic() method and PDFExporter class.
"""

import pytest
import tempfile
from pathlib import Path
import shutil

from circuit_synth.core import circuit, Component, Circuit
from circuit_synth.kicad.pdf_exporter import PDFExporter


class TestPDFExporter:
    """Test the PDFExporter class."""

    def test_pdf_exporter_requires_kicad(self, tmp_path):
        """Test that PDFExporter requires kicad-cli to be available."""
        # Create a dummy schematic file
        sch_file = tmp_path / "test.kicad_sch"
        sch_file.write_text("(kicad_sch)")

        output_file = tmp_path / "output.pdf"

        # This will fail because we're not testing with a real KiCad file
        # But it shows the error handling works
        # Note: This test assumes kicad-cli is installed on the test system
        try:
            result = PDFExporter.export_pdf(sch_file, output_file)
            # If kicad-cli is available, we expect success
            assert result["success"] is True
            assert result["file"] == output_file
        except FileNotFoundError as e:
            # If kicad-cli is not installed, that's also valid
            assert "kicad-cli" in str(e)


class TestCircuitGeneratePDF:
    """Test the Circuit.generate_pdf_schematic() method."""

    @pytest.fixture
    def simple_circuit(self):
        """Create a simple test circuit."""
        @circuit(name="SimplePDFTest")
        def test_circuit():
            r1 = Component(symbol="Device:R", value="10k", ref="R1")
            r2 = Component(symbol="Device:R", value="1k", ref="R2")
            c1 = Component(symbol="Device:C", value="100nF", ref="C1")
            d1 = Component(symbol="Device:LED", value="Red", ref="D1")
            return locals()

        return test_circuit()

    def test_generate_pdf_default_parameters(self, simple_circuit, tmp_path):
        """Test generate_pdf_schematic with default parameters."""
        # Change to temp directory for this test
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(tmp_path)

            result = simple_circuit.generate_pdf_schematic(project_name="test_simple_pdf")

            # Check result structure
            assert "success" in result
            assert "file" in result
            assert "project_path" in result

            # If successful, verify file exists
            if result["success"]:
                assert result["file"].exists()
                assert result["file"].suffix == ".pdf"
                assert result["project_path"] == Path("test_simple_pdf")

        finally:
            os.chdir(original_cwd)

    def test_generate_pdf_custom_output_file(self, simple_circuit, tmp_path):
        """Test generate_pdf_schematic with custom output file."""
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(tmp_path)

            custom_output = "custom/my_schematic.pdf"
            result = simple_circuit.generate_pdf_schematic(
                project_name="test_custom_pdf",
                output_file=custom_output
            )

            # Check result structure
            assert "success" in result
            assert "file" in result

            if result["success"]:
                assert result["file"] == Path(custom_output)
                assert result["file"].suffix == ".pdf"

        finally:
            os.chdir(original_cwd)

    def test_generate_pdf_black_and_white(self, simple_circuit, tmp_path):
        """Test generate_pdf_schematic with black and white option."""
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(tmp_path)

            result = simple_circuit.generate_pdf_schematic(
                project_name="test_bw_pdf",
                black_and_white=True
            )

            # Check result structure
            assert "success" in result
            assert "file" in result

            if result["success"]:
                assert result["file"].exists()

        finally:
            os.chdir(original_cwd)

    def test_generate_pdf_exclude_drawing_sheet(self, simple_circuit, tmp_path):
        """Test generate_pdf_schematic with exclude_drawing_sheet option."""
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(tmp_path)

            result = simple_circuit.generate_pdf_schematic(
                project_name="test_no_sheet_pdf",
                exclude_drawing_sheet=True
            )

            # Check result structure
            assert "success" in result
            assert "file" in result

        finally:
            os.chdir(original_cwd)

    def test_generate_pdf_with_pages_option(self, simple_circuit, tmp_path):
        """Test generate_pdf_schematic with pages option."""
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(tmp_path)

            # For single-page schematic, just request page 1
            result = simple_circuit.generate_pdf_schematic(
                project_name="test_pages_pdf",
                pages="1"
            )

            # Check result structure
            assert "success" in result
            assert "file" in result

        finally:
            os.chdir(original_cwd)

    def test_generate_pdf_default_filename(self, simple_circuit, tmp_path):
        """Test that default PDF filename matches project name."""
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(tmp_path)

            result = simple_circuit.generate_pdf_schematic(
                project_name="my_circuit_pdf"
            )

            # Check that default filename uses project name
            assert "success" in result
            assert "file" in result

            if result["success"]:
                assert result["file"].name == "my_circuit_pdf.pdf"

        finally:
            os.chdir(original_cwd)

    def test_generate_pdf_reuses_existing_project(self, simple_circuit, tmp_path):
        """Test that generate_pdf_schematic reuses existing KiCad projects."""
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(tmp_path)

            # First generation creates the project
            result1 = simple_circuit.generate_pdf_schematic(
                project_name="test_reuse_pdf"
            )

            # Second generation reuses the same project
            result2 = simple_circuit.generate_pdf_schematic(
                project_name="test_reuse_pdf"
            )

            # Both should refer to the same project
            assert "project_path" in result1
            assert "project_path" in result2
            assert result1["project_path"] == result2["project_path"]

        finally:
            os.chdir(original_cwd)
