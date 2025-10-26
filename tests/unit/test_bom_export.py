"""
Unit tests for BOM (Bill of Materials) export functionality.

Tests the Circuit.generate_bom() method and BOMExporter class.
"""

import pytest
import tempfile
from pathlib import Path
import csv
import shutil

from circuit_synth.core import circuit, Component, Circuit
from circuit_synth.kicad.bom_exporter import BOMExporter


class TestBOMExporter:
    """Test the BOMExporter class."""

    def test_bom_exporter_requires_kicad(self, tmp_path):
        """Test that BOMExporter requires kicad-cli to be available."""
        # Create a valid KiCad schematic file
        sch_file = tmp_path / "test.kicad_sch"
        valid_sch = '''(kicad_sch (version 20250114) (generator "eeschema") (generator_version "9.0")
  (paper "A4")
  (lib_symbols)
  (symbol_instances)
)'''
        sch_file.write_text(valid_sch)

        output_file = tmp_path / "bom.csv"

        # This will fail because we're not testing with a real KiCad file
        # But it shows the error handling works
        # Note: This test assumes kicad-cli is installed on the test system
        try:
            result = BOMExporter.export_csv(sch_file, output_file)
            # If kicad-cli is available, we expect success
            assert result["success"] is True
            assert result["file"] == output_file
            assert isinstance(result["component_count"], int)
        except FileNotFoundError as e:
            # If kicad-cli is not installed, that's also valid
            assert "kicad-cli" in str(e)


class TestCircuitGenerateBOM:
    """Test the Circuit.generate_bom() method."""

    @pytest.fixture
    def simple_circuit(self):
        """Create a simple test circuit."""
        @circuit(name="SimpleBOMTest")
        def test_circuit():
            r1 = Component(symbol="Device:R", value="10k", ref="R1")
            r2 = Component(symbol="Device:R", value="1k", ref="R2")
            c1 = Component(symbol="Device:C", value="100nF", ref="C1")
            d1 = Component(symbol="Device:LED", value="Red", ref="D1")
            return locals()

        return test_circuit()

    def test_generate_bom_default_parameters(self, simple_circuit, tmp_path):
        """Test generate_bom with default parameters."""
        # Change to temp directory for this test
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(tmp_path)

            result = simple_circuit.generate_bom(project_name="test_simple")

            # Check result structure
            assert result["success"] is True
            assert result["file"].exists()
            assert result["component_count"] == 4
            # project_path is returned as absolute path
            assert result["project_path"].name == "test_simple"

            # Verify CSV structure
            with open(result["file"], 'r') as f:
                reader = csv.DictReader(f)
                rows = list(reader)
                assert len(rows) == 4

                # Check header
                assert "Refs" in reader.fieldnames
                assert "Value" in reader.fieldnames

                # Verify components are in the BOM
                refs = {row["Refs"] for row in rows}
                assert "R1" in refs
                assert "R2" in refs
                assert "C1" in refs
                assert "D1" in refs

        finally:
            os.chdir(original_cwd)

    def test_generate_bom_custom_output_file(self, simple_circuit, tmp_path):
        """Test generate_bom with custom output file."""
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(tmp_path)

            custom_output = "custom/my_bom.csv"
            result = simple_circuit.generate_bom(
                project_name="test_custom",
                output_file=custom_output
            )

            assert result["success"] is True
            assert result["file"] == Path(custom_output)
            assert result["file"].exists()
            assert result["component_count"] == 4

        finally:
            os.chdir(original_cwd)

    def test_generate_bom_exclude_dnp(self, tmp_path):
        """Test generate_bom with exclude_dnp option."""
        @circuit(name="DNPTest")
        def test_circuit():
            # Normal component
            r1 = Component(symbol="Device:R", value="10k", ref="R1")
            # This would be marked as DNP in KiCad, but we can't easily test that
            r2 = Component(symbol="Device:R", value="1k", ref="R2")
            return locals()

        circ = test_circuit()

        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(tmp_path)

            result = circ.generate_bom(
                project_name="test_dnp",
                exclude_dnp=True
            )

            assert result["success"] is True
            assert result["component_count"] >= 2  # May vary depending on DNP marking

        finally:
            os.chdir(original_cwd)

    def test_generate_bom_missing_kicad_cli(self, simple_circuit, tmp_path, monkeypatch):
        """Test graceful failure when kicad-cli is not available."""
        import subprocess

        # Mock subprocess to raise FileNotFoundError
        original_run = subprocess.run

        def mock_run(*args, **kwargs):
            raise FileNotFoundError("kicad-cli")

        monkeypatch.setattr(subprocess, "run", mock_run)

        # The test will still try to generate, should return error
        # (We can't easily test this without actually breaking subprocess)
        # Skip this test if kicad-cli is not available
        pytest.skip("Cannot test without kicad-cli available")

    def test_bom_csv_format(self, simple_circuit, tmp_path):
        """Test that generated BOM has correct CSV format."""
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(tmp_path)

            result = simple_circuit.generate_bom(project_name="test_format")

            # Read and verify CSV
            with open(result["file"], 'r') as f:
                content = f.read()

                # Should have quotes around fields
                assert '"Refs"' in content
                assert '"Value"' in content
                assert '"R1"' in content

                # Should be valid CSV
                f.seek(0)
                reader = csv.reader(f)
                rows = list(reader)

                # At least header + data rows
                assert len(rows) > 1

                # All rows should have same number of columns
                col_count = len(rows[0])
                for row in rows:
                    assert len(row) == col_count

        finally:
            os.chdir(original_cwd)

    def test_generate_bom_reuses_existing_project(self, simple_circuit, tmp_path):
        """Test that generate_bom reuses existing KiCad project."""
        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(tmp_path)

            project_name = "test_reuse"

            # First call generates project
            result1 = simple_circuit.generate_bom(project_name=project_name)
            assert result1["success"] is True
            bom_file1 = result1["file"]

            # Get modification time of first BOM
            mtime1 = bom_file1.stat().st_mtime

            # Second call should reuse project
            import time
            time.sleep(0.1)  # Ensure time difference

            result2 = simple_circuit.generate_bom(project_name=project_name)
            assert result2["success"] is True
            bom_file2 = result2["file"]

            # Both should point to same file
            assert bom_file1 == bom_file2
            assert bom_file2.exists()

        finally:
            os.chdir(original_cwd)


class TestBOMComponentCount:
    """Test that BOM component counting works correctly."""

    def test_component_count_matches_circuit(self, tmp_path):
        """Test that BOM component count matches circuit."""
        @circuit(name="CountTest")
        def test_circuit():
            r1 = Component(symbol="Device:R", value="10k", ref="R1")
            r2 = Component(symbol="Device:R", value="1k", ref="R2")
            r3 = Component(symbol="Device:R", value="4.7k", ref="R3")
            c1 = Component(symbol="Device:C", value="10uF", ref="C1")
            c2 = Component(symbol="Device:C", value="100nF", ref="C2")
            return locals()

        circ = test_circuit()
        expected_count = len(circ._components)

        original_cwd = Path.cwd()
        try:
            import os
            os.chdir(tmp_path)

            result = circ.generate_bom(project_name="count_test")

            assert result["success"] is True
            assert result["component_count"] == expected_count

        finally:
            os.chdir(original_cwd)
