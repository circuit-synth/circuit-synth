#!/usr/bin/env python3
"""
Test suite for 03_dual_hierarchy_connected KiCad-to-Python workflow.
Tests hierarchical circuits with actual connections and signal flow.
"""

import json
import logging
import shutil
import subprocess
import tempfile
from pathlib import Path

import pytest

from circuit_synth.tools.kicad_integration.kicad_to_python_sync import (
    KiCadToPythonSyncer,
)

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Test configuration
PROJECT_DIR = Path(__file__).parent / "03_dual_hierarchy_connected"
TEST_OUTPUTS_DIR = Path(__file__).parent / "test_outputs"


class TestConnectedHierarchicalWorkflow:
    """Test connected hierarchical KiCad-to-Python conversion."""

    def setup_method(self):
        """Setup for each test method."""
        TEST_OUTPUTS_DIR.mkdir(exist_ok=True)

    def test_connected_hierarchical_parsing(self):
        """Test parsing of connected hierarchical circuit."""
        # Create output directory for this test
        test_output_dir = TEST_OUTPUTS_DIR / "connected_parsing_test"
        test_output_dir.mkdir(parents=True, exist_ok=True)

        # Parse the connected hierarchical project
        syncer = KiCadToPythonSyncer(
            kicad_project=str(PROJECT_DIR),
            python_file=str(test_output_dir),
            preview_only=False,
            create_backup=False,
        )

        success = syncer.sync()
        assert success, "Parsing should succeed"

        # Verify Python file was generated
        python_file = test_output_dir / "main.py"
        assert python_file.exists(), "Python file was not generated"

        # Check that the Python code contains expected elements
        python_content = python_file.read_text()
        logger.info(f"Generated Python code:\n{python_content}")

        # Verify hierarchical structure - current implementation uses separate files
        assert "@circuit(name='main')" in python_content, "main circuit not found"
        assert "from child1 import child1" in python_content, "child1 import not found"

        # Verify components are distributed properly
        # R3 should be in main.py, R2 should be in child1.py if it exists
        assert "R3" in python_content, "R3 component not found in main"

        # Check for child1.py file
        child1_file = test_output_dir / "child1.py"
        if child1_file.exists():
            child1_content = child1_file.read_text()
            assert (
                "@circuit(name='child1')" in child1_content
            ), "child1 circuit not found in separate file"
            assert "R2" in child1_content, "R2 component not found in child1 file"

        # Verify hierarchical instantiation (may have parameters for net connections)
        assert (
            "child1_circuit = child1(" in python_content
        ), "child1 instantiation not found"

    def test_connected_hierarchical_execution(self):
        """Test execution of generated Python code for connected circuits."""
        # Create output directory for this test
        test_output_dir = TEST_OUTPUTS_DIR / "connected_execution_test"
        test_output_dir.mkdir(parents=True, exist_ok=True)

        # Generate Python code
        syncer = KiCadToPythonSyncer(
            kicad_project=str(PROJECT_DIR),
            python_file=str(test_output_dir),
            preview_only=False,
            create_backup=False,
        )

        success = syncer.sync()
        assert success, "Python generation should succeed"

        python_file = test_output_dir / "main.py"
        assert python_file.exists(), "Python file should exist"

        # Execute the generated Python code
        output_dir = test_output_dir / "python_output"
        output_dir.mkdir(exist_ok=True)

        # Run the Python script
        cmd = ["uv", "run", "python", str(python_file)]
        proc_result = subprocess.run(
            cmd, cwd=str(output_dir), capture_output=True, text=True
        )

        assert (
            proc_result.returncode == 0
        ), f"Python execution failed: {proc_result.stderr}"

        # Check generated files
        generated_project = output_dir / "03_dual_hierarchy_connected_generated"
        assert generated_project.exists(), "Generated project directory not found"

        # Verify main schematic
        main_sch = generated_project / "03_dual_hierarchy_connected_generated.kicad_sch"
        assert main_sch.exists(), "Main schematic not generated"

        # Verify child schematic
        child_sch = generated_project / "child1.kicad_sch"
        assert child_sch.exists(), "Child schematic not generated"

        # Verify project file
        project_file = (
            generated_project / "03_dual_hierarchy_connected_generated.kicad_pro"
        )
        assert project_file.exists(), "Project file not generated"

    def test_connected_net_preservation(self):
        """Test that hierarchical connections are preserved - inspired by netlist_importer patterns."""
        # Create output directory for this test
        test_output_dir = TEST_OUTPUTS_DIR / "connected_net_test"
        test_output_dir.mkdir(parents=True, exist_ok=True)

        # Generate Python code
        syncer = KiCadToPythonSyncer(
            kicad_project=str(PROJECT_DIR),
            python_file=str(test_output_dir),
            preview_only=False,
            create_backup=False,
        )

        success = syncer.sync()
        assert success, "Python generation should succeed"

        python_file = test_output_dir / "main.py"
        python_content = python_file.read_text()

        # Check for net connections in generated code
        # The original circuit has VIN and GND connections
        assert "VIN" in python_content, "VIN net not found in generated code"
        assert "GND" in python_content, "GND net not found in generated code"

        # Execute to generate KiCad files
        output_dir = test_output_dir / "python_output"
        output_dir.mkdir(exist_ok=True)

        subprocess.run(
            ["uv", "run", "python", str(python_file)], cwd=str(output_dir), check=True
        )

        # Verify connections in generated schematics
        generated_project = output_dir / "03_dual_hierarchy_connected_generated"

        # Check main schematic for hierarchical labels and specific connections
        main_sch_content = (
            generated_project / "03_dual_hierarchy_connected_generated.kicad_sch"
        ).read_text()
        assert (
            "hierarchical_label" in main_sch_content
        ), "Hierarchical labels missing from main schematic"

        # Verify specific VIN/GND labels in main circuit (clean notation without slash)
        assert (
            "VIN" in main_sch_content
        ), "VIN hierarchical label missing from main schematic"
        assert (
            "GND" in main_sch_content
        ), "GND hierarchical label missing from main schematic"

        # Verify R3 component is present in main circuit
        assert '"R3"' in main_sch_content, "R3 component missing from main schematic"

        # Check child schematic for hierarchical labels and connections
        child_sch_content = (generated_project / "child1.kicad_sch").read_text()
        assert (
            "hierarchical_label" in child_sch_content
        ), "Hierarchical labels missing from child schematic"

        # Verify specific VIN/GND labels in child circuit (clean notation without slash)
        assert (
            "VIN" in child_sch_content
        ), "VIN hierarchical label missing from child schematic"
        assert (
            "GND" in child_sch_content
        ), "GND hierarchical label missing from child schematic"

        # Verify R2 component is present in child circuit
        assert '"R2"' in child_sch_content, "R2 component missing from child schematic"

    def test_connected_round_trip(self):
        """Test round-trip conversion for connected hierarchical circuits."""
        # Create output directory for this test
        test_output_dir_1 = TEST_OUTPUTS_DIR / "connected_round_trip_1"
        test_output_dir_1.mkdir(parents=True, exist_ok=True)

        # First conversion: KiCad → Python
        syncer1 = KiCadToPythonSyncer(
            kicad_project=str(PROJECT_DIR),
            python_file=str(test_output_dir_1),
            preview_only=False,
            create_backup=False,
        )

        success1 = syncer1.sync()
        assert success1, "First conversion failed"

        python_file_1 = test_output_dir_1 / "main.py"
        assert python_file_1.exists(), "First Python file should exist"

        # Execute Python to generate new KiCad files
        output_dir = test_output_dir_1 / "python_output"
        output_dir.mkdir(exist_ok=True)

        subprocess.run(
            ["uv", "run", "python", str(python_file_1)], cwd=str(output_dir), check=True
        )

        # Second conversion: Generated KiCad → Python
        generated_project = output_dir / "03_dual_hierarchy_connected_generated"
        assert generated_project.exists(), "Generated project should exist"

        test_output_dir_2 = TEST_OUTPUTS_DIR / "connected_round_trip_2"
        test_output_dir_2.mkdir(parents=True, exist_ok=True)

        syncer2 = KiCadToPythonSyncer(
            kicad_project=str(generated_project),
            python_file=str(test_output_dir_2),
            preview_only=False,
            create_backup=False,
        )

        success2 = syncer2.sync()
        assert success2, "Second conversion failed"

        python_file_2 = test_output_dir_2 / "main.py"
        assert python_file_2.exists(), "Second Python file should exist"

        # Compare the two Python files for consistency
        python_content_1 = python_file_1.read_text()
        python_content_2 = python_file_2.read_text()

        # They should have similar structure (allowing for naming differences)
        assert (
            "@circuit(name='main')" in python_content_2
        ), "main circuit lost in round-trip"
        assert (
            "from child1 import child1" in python_content_2
        ), "child1 import lost in round-trip"
        assert "R3" in python_content_2, "R3 component lost in round-trip"

        # Check child1.py file in second conversion
        child1_file_2 = test_output_dir_2 / "child1.py"
        if child1_file_2.exists():
            child1_content_2 = child1_file_2.read_text()
            assert (
                "@circuit(name='child1')" in child1_content_2
            ), "child1 circuit lost in round-trip"
            assert "R2" in child1_content_2, "R2 component lost in round-trip"

    def test_hierarchical_reference_uniqueness(self):
        """Test that component references remain unique across hierarchy."""
        # Create output directory for this test
        test_output_dir = TEST_OUTPUTS_DIR / "reference_uniqueness_test"
        test_output_dir.mkdir(parents=True, exist_ok=True)

        syncer = KiCadToPythonSyncer(
            kicad_project=str(PROJECT_DIR),
            python_file=str(test_output_dir),
            preview_only=False,
            create_backup=False,
        )

        success = syncer.sync()
        assert success, "Conversion should succeed"

        python_file = test_output_dir / "main.py"
        assert python_file.exists(), "Python file should exist"

        python_content = python_file.read_text()

        # Verify unique references - R3 should be in main, R2 should be in child1
        assert 'ref="R3"' in python_content, "R3 reference not preserved in main"

        # Check R2 in separate child1.py file
        child1_file = test_output_dir / "child1.py"
        if child1_file.exists():
            child1_content = child1_file.read_text()
            assert 'ref="R2"' in child1_content, "R2 reference not preserved in child1"

        # Execute and check generated schematics
        output_dir = test_output_dir / "python_output"
        output_dir.mkdir(exist_ok=True)

        subprocess.run(
            ["uv", "run", "python", str(python_file)], cwd=str(output_dir), check=True
        )

        generated_project = output_dir / "03_dual_hierarchy_connected_generated"

        # Check that references are unique in generated files
        main_sch = (
            generated_project / "03_dual_hierarchy_connected_generated.kicad_sch"
        ).read_text()
        child_sch = (generated_project / "child1.kicad_sch").read_text()

        # Should have R3 in main and R2 in child
        assert (
            '"R3"' in main_sch or "(reference R3)" in main_sch
        ), "R3 reference missing from main schematic"
        assert (
            '"R2"' in child_sch or "(reference R2)" in child_sch
        ), "R2 reference missing from child schematic"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
