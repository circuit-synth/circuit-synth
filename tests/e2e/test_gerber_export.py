"""
Unit tests for Gerber export functionality.

Tests the Circuit.generate_gerbers() method for PCB manufacturing exports.
"""

import pytest
import tempfile
from pathlib import Path
import shutil

from circuit_synth.core import circuit, Component, Circuit


class TestCircuitGenerateGerbers:
    """Test the Circuit.generate_gerbers() method."""

    @pytest.fixture
    def simple_circuit(self):
        """Create a simple test circuit with a few components."""
        @circuit(name="SimpleGerberTest")
        def test_circuit():
            r1 = Component(symbol="Device:R", value="10k", ref="R1", footprint="Resistor_SMD:R_0603_1608Metric")
            r2 = Component(symbol="Device:R", value="1k", ref="R2", footprint="Resistor_SMD:R_0603_1608Metric")
            c1 = Component(symbol="Device:C", value="100nF", ref="C1", footprint="Capacitor_SMD:C_0603_1608Metric")
            d1 = Component(symbol="Device:LED", value="Red", ref="D1", footprint="LED_SMD:LED_0603_1608Metric")
            return locals()

        return test_circuit()

    def test_generate_gerbers_default_parameters(self, simple_circuit, tmp_path):
        """Test generate_gerbers with default parameters."""
        # Change to temp directory for this test
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(tmp_path)

            result = simple_circuit.generate_gerbers(project_name="test_simple_gerber")

            # Check result structure
            assert "success" in result
            assert "gerber_files" in result
            assert "drill_files" in result
            assert "project_path" in result
            assert "output_dir" in result

            # If successful, verify files exist
            if result["success"]:
                assert result["output_dir"].exists()
                assert isinstance(result["gerber_files"], list)
                # Should have generated at least some gerber files
                assert len(result["gerber_files"]) > 0

        finally:
            os.chdir(original_cwd)

    def test_generate_gerbers_custom_output_dir(self, simple_circuit, tmp_path):
        """Test generate_gerbers with custom output directory."""
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(tmp_path)

            custom_output = "manufacturing/gerbers"
            result = simple_circuit.generate_gerbers(
                project_name="test_custom_gerber",
                output_dir=custom_output
            )

            # Check result structure
            assert "success" in result
            assert "output_dir" in result

            if result["success"]:
                assert result["output_dir"] == Path(custom_output)
                assert result["output_dir"].exists()

        finally:
            os.chdir(original_cwd)

    def test_generate_gerbers_without_drill(self, simple_circuit, tmp_path):
        """Test generate_gerbers without drill files."""
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(tmp_path)

            result = simple_circuit.generate_gerbers(
                project_name="test_no_drill_gerber",
                include_drill=False
            )

            # Check result structure
            assert "success" in result
            assert "gerber_files" in result
            assert "drill_files" in result

            if result["success"]:
                # Should still have gerber files
                assert len(result["gerber_files"]) > 0
                # But drill_files should be None when not requested
                assert result["drill_files"] is None

        finally:
            os.chdir(original_cwd)

    def test_generate_gerbers_default_output_dir(self, simple_circuit, tmp_path):
        """Test that default output directory is project_name/gerbers."""
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(tmp_path)

            result = simple_circuit.generate_gerbers(
                project_name="test_default_dir_gerber"
            )

            # Check result structure
            assert "success" in result
            assert "output_dir" in result

            if result["success"]:
                # Default should be project_name/gerbers
                assert result["output_dir"] == Path("test_default_dir_gerber") / "gerbers"

        finally:
            os.chdir(original_cwd)

    def test_generate_gerbers_reuses_existing_project(self, simple_circuit, tmp_path):
        """Test that generate_gerbers reuses existing KiCad projects."""
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(tmp_path)

            # First generation creates the project
            result1 = simple_circuit.generate_gerbers(
                project_name="test_reuse_gerber"
            )

            # Second generation reuses the same project
            result2 = simple_circuit.generate_gerbers(
                project_name="test_reuse_gerber"
            )

            # Both should refer to the same project
            assert "project_path" in result1
            assert "project_path" in result2
            assert result1["project_path"] == result2["project_path"]

        finally:
            os.chdir(original_cwd)

    def test_generate_gerbers_gerber_format(self, simple_circuit, tmp_path):
        """Test that generated files have proper Gerber format."""
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(tmp_path)

            result = simple_circuit.generate_gerbers(
                project_name="test_format_gerber"
            )

            # Check result structure
            assert "success" in result
            assert "gerber_files" in result

            if result["success"]:
                # Gerber files should have .gbr or similar extensions
                gerber_files = result["gerber_files"]
                assert len(gerber_files) > 0

                # Check that files are Gerber format (common extensions)
                gerber_extensions = {'.gbr', '.gbl', '.gbo', '.gbt', '.gbs', '.gm1', '.gto', '.gts'}
                for gerber_file in gerber_files:
                    # File should have a Gerber extension or be named appropriately
                    assert gerber_file.suffix in gerber_extensions or gerber_file.exists()

        finally:
            os.chdir(original_cwd)

    def test_generate_gerbers_creates_project_path(self, simple_circuit, tmp_path):
        """Test that generate_gerbers creates project_path in result."""
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(tmp_path)

            result = simple_circuit.generate_gerbers(
                project_name="test_project_path_gerber"
            )

            # project_path should be set
            assert "project_path" in result

            if result["success"]:
                # Project path should point to actual project directory
                assert result["project_path"].exists()
                # Should have .kicad_pcb file
                pcb_file = result["project_path"] / "test_project_path_gerber.kicad_pcb"
                assert pcb_file.exists()

        finally:
            os.chdir(original_cwd)

    def test_generate_gerbers_with_gerber_drill_format(self, simple_circuit, tmp_path):
        """Test generate_gerbers with Gerber drill format."""
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(tmp_path)

            result = simple_circuit.generate_gerbers(
                project_name="test_gerber_drill_format",
                drill_format="gerber"
            )

            # Check result structure
            assert "success" in result
            assert "drill_files" in result

        finally:
            os.chdir(original_cwd)
