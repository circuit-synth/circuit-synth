#!/usr/bin/env python3
"""
Unit tests for 01_simple_resistor KiCad-to-Python workflow.

Tests the complete workflow using the simple resistor reference project,
focusing on natural hierarchy (root components) and automatic project naming.
"""

import os
import tempfile
import unittest
from pathlib import Path
from textwrap import dedent

from circuit_synth.tools.kicad_integration.kicad_to_python_sync import (
    KiCadToPythonSyncer,
)
from circuit_synth.tools.utilities.llm_code_updater import LLMCodeUpdater


class Test01SimpleResistorWorkflow(unittest.TestCase):
    """Test KiCad-to-Python workflow for simple resistor circuit"""

    @classmethod
    def setUpClass(cls):
        """Set up class-level fixtures - run once for all tests"""
        cls.test_data_dir = Path(__file__).parent
        cls.reference_project = cls.test_data_dir / "01_simple_resistor_reference"
        cls.temp_dir = cls.test_data_dir / "test_outputs"

        # Clean up any existing test outputs from previous runs
        import shutil

        if cls.temp_dir.exists():
            shutil.rmtree(cls.temp_dir)

        # Create base directory structure
        cls.temp_dir.mkdir(parents=True, exist_ok=True)

    def setUp(self):
        """Set up test fixtures for each test"""
        # Each test gets its own subdirectory to avoid conflicts
        import uuid

        test_id = str(uuid.uuid4())[:8]  # Short unique ID
        self.test_specific_dir = self.temp_dir / f"{self._testMethodName}_{test_id}"
        self.test_specific_dir.mkdir(parents=True, exist_ok=True)

        # Only create python_output_dir for tests that actually need it
        self.python_output_dir = self.test_specific_dir / "python_output"
        # Don't create it here - let individual tests create it if needed

    def tearDown(self):
        """Clean up test fixtures - DISABLED for manual inspection"""
        # Leave test outputs for manual review
        # To clean up manually, delete: tests/kicad_to_python/01_simple_resistor/test_outputs/
        pass

    def test_kicad_to_python_syncer_initialization(self):
        """Test that KiCadToPythonSyncer initializes correctly with project name"""
        # Test with .kicad_pro file - use a simple temp path, no need for full directory structure
        temp_output = self.test_specific_dir / "temp_output.py"

        kicad_pro = self.reference_project / "01_simple_resistor_reference.kicad_pro"
        syncer = KiCadToPythonSyncer(
            kicad_project=str(kicad_pro),
            python_file=str(temp_output),
            preview_only=True,
            create_backup=False,
        )

        # Check that project name was extracted correctly
        self.assertEqual(
            syncer.code_generator.project_name, "01_simple_resistor_reference"
        )

    def test_llm_code_updater_initialization(self):
        """Test that LLMCodeUpdater initializes correctly"""
        # Test basic initialization
        updater = LLMCodeUpdater()
        self.assertIsInstance(updater.llm_available, bool)
        self.assertTrue(hasattr(updater, "update_python_file"))

    def test_complete_kicad_to_python_conversion(self):
        """Test complete KiCad-to-Python conversion workflow"""
        if not self.reference_project.exists():
            self.skipTest(f"Reference project not found at {self.reference_project}")

        # Create the output directory for this test
        self.python_output_dir.mkdir(parents=True, exist_ok=True)

        # Run the conversion
        syncer = KiCadToPythonSyncer(
            kicad_project=str(self.reference_project),
            python_file=str(self.python_output_dir),
            preview_only=False,
            create_backup=False,
        )

        success = syncer.sync()
        self.assertTrue(success, "KiCad-to-Python synchronization should succeed")

        # Check that main.py was created
        main_py = self.python_output_dir / "main.py"
        self.assertTrue(main_py.exists(), "main.py should be created")

        # Read and verify the generated content
        generated_code = main_py.read_text()

        # Test 1: Check for proper imports
        self.assertIn("from circuit_synth import *", generated_code)

        # Test 2: Check for @circuit decorator
        self.assertIn("@circuit", generated_code)
        self.assertIn("def main():", generated_code)

        # Test 3: Check for component creation
        self.assertIn("Component(", generated_code)
        self.assertIn('symbol="Device:R"', generated_code)
        self.assertIn(
            'ref="R1"', generated_code
        )  # Should preserve exact reference from KiCad
        self.assertIn('value="10k"', generated_code)
        self.assertIn('footprint="Resistor_SMD:R_0603_1608Metric"', generated_code)

        # Test 4: Check for auto-generated project name (THE KEY FIX!)
        self.assertIn(
            'circuit.generate_kicad_project(project_name="01_simple_resistor_reference_generated")',
            generated_code,
        )

        # Test 5: Check that it's executable Python code
        try:
            compile(generated_code, "main.py", "exec")
        except SyntaxError as e:
            self.fail(f"Generated Python code has syntax errors: {e}")

    def test_kicad_to_python_to_kicad_workflow(self):
        """Test complete workflow: KiCad->Python->check Python->run Python successfully"""
        if not self.reference_project.exists():
            self.skipTest(f"Reference project not found at {self.reference_project}")

        # Create the output directory for this test
        self.python_output_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Run KiCad-to-Python logic on reference project
        syncer = KiCadToPythonSyncer(
            kicad_project=str(self.reference_project),
            python_file=str(self.python_output_dir),
            preview_only=False,
            create_backup=False,
        )
        success = syncer.sync()
        self.assertTrue(success, "KiCad-to-Python conversion should succeed")

        # Step 2: Check that Python file is generated exactly as expected
        main_py = self.python_output_dir / "main.py"
        self.assertTrue(main_py.exists(), "main.py should be generated")

        generated_code = main_py.read_text()

        # Verify the exact expected content
        expected_elements = [
            "from circuit_synth import *",
            "@circuit",
            "def main():",
            'Component(symbol="Device:R", ref="R1", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")',
            'circuit.generate_kicad_project(project_name="01_simple_resistor_reference_generated")',
        ]

        for element in expected_elements:
            self.assertIn(
                element, generated_code, f"Generated Python should contain: {element}"
            )

        # Step 3: Run the Python file to see that it runs successfully
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, str(main_py)],
            cwd=str(self.python_output_dir),
            capture_output=True,
            text=True,
        )

        self.assertEqual(
            result.returncode,
            0,
            f"Generated Python script should run successfully.\nstdout: {result.stdout}\nstderr: {result.stderr}",
        )

        # Verify the KiCad project was created
        generated_project_dir = (
            self.python_output_dir / "01_simple_resistor_reference_generated"
        )
        self.assertTrue(
            generated_project_dir.exists(),
            "Generated KiCad project directory should exist",
        )

        # Verify natural hierarchy: components on root schematic, no artificial main.kicad_sch
        root_schematic = (
            generated_project_dir / "01_simple_resistor_reference_generated.kicad_sch"
        )
        self.assertTrue(root_schematic.exists(), "Root schematic should exist")

        main_schematic = generated_project_dir / "main.kicad_sch"
        self.assertFalse(
            main_schematic.exists(),
            "Should NOT have artificial main.kicad_sch (natural hierarchy)",
        )

        # Verify component is in root schematic
        root_content = root_schematic.read_text()
        self.assertIn('"R1"', root_content, "R1 component should be in root schematic")
        self.assertIn(
            "Device:R", root_content, "Device:R symbol should be in root schematic"
        )

    def test_component_reference_generation(self):
        """Test that component references are properly handled (R -> R1)"""
        if not self.reference_project.exists():
            self.skipTest(f"Reference project not found at {self.reference_project}")

        # Create the output directory for this test
        self.python_output_dir.mkdir(parents=True, exist_ok=True)

        # Run conversion
        syncer = KiCadToPythonSyncer(
            kicad_project=str(self.reference_project),
            python_file=str(self.python_output_dir),
            preview_only=False,
            create_backup=False,
        )
        success = syncer.sync()
        self.assertTrue(success)

        # Check generated Python preserves exact reference from KiCad
        main_py = self.python_output_dir / "main.py"
        generated_code = main_py.read_text()

        # Should preserve the exact reference from KiCad (R1)
        self.assertIn(
            'ref="R1"', generated_code, "Should preserve exact reference from KiCad"
        )
        self.assertNotIn(
            'ref="R"', generated_code, "Should NOT truncate reference to just prefix"
        )

    def test_round_trip_consistency(self):
        """Test that KiCad -> Python -> KiCad maintains component structure"""
        if not self.reference_project.exists():
            self.skipTest(f"Reference project not found at {self.reference_project}")

        # Create the output directory for this test
        self.python_output_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: KiCad -> Python
        syncer = KiCadToPythonSyncer(
            kicad_project=str(self.reference_project),
            python_file=str(self.python_output_dir),
            preview_only=False,
            create_backup=False,
        )
        success = syncer.sync()
        self.assertTrue(success)

        # Step 2: Python -> KiCad (execute the generated Python)
        main_py = self.python_output_dir / "main.py"
        import subprocess
        import sys

        result = subprocess.run(
            [sys.executable, str(main_py)],
            cwd=str(self.python_output_dir),
            capture_output=True,
            text=True,
        )

        self.assertEqual(
            result.returncode,
            0,
            f"Generated Python should execute successfully: {result.stderr}",
        )

        # Step 3: Verify round-trip consistency
        original_sch = self.reference_project / "01_simple_resistor_reference.kicad_sch"
        generated_sch = (
            self.python_output_dir
            / "01_simple_resistor_reference_generated"
            / "01_simple_resistor_reference_generated.kicad_sch"
        )

        self.assertTrue(generated_sch.exists(), "Generated schematic should exist")

        # Compare key elements (not exact match due to UUIDs, formatting, etc.)
        original_content = original_sch.read_text()
        generated_content = generated_sch.read_text()

        # Check that both contain the same component
        self.assertIn('"Device:R"', original_content)
        self.assertIn('"Device:R"', generated_content)
        self.assertIn('"10k"', original_content)
        self.assertIn('"10k"', generated_content)
        self.assertIn('"Resistor_SMD:R_0603_1608Metric"', original_content)
        self.assertIn('"Resistor_SMD:R_0603_1608Metric"', generated_content)

    def test_directory_creation_functionality(self):
        """Test that KiCad-to-Python can create non-existent directories"""
        if not self.reference_project.exists():
            self.skipTest(f"Reference project not found at {self.reference_project}")

        # Test 1: Directory with trailing slash
        test_dir_with_slash = self.test_specific_dir / "dir_creation_test_slash/"
        self.assertFalse(
            test_dir_with_slash.exists(), "Test directory should not exist initially"
        )

        syncer_slash = KiCadToPythonSyncer(
            kicad_project=str(self.reference_project),
            python_file=str(test_dir_with_slash),
            preview_only=False,
            create_backup=False,
        )
        self.assertTrue(
            syncer_slash.is_directory_mode,
            "Should detect directory mode for path with trailing slash",
        )

        success = syncer_slash.sync()
        self.assertTrue(
            success, "Directory creation with trailing slash should succeed"
        )
        self.assertTrue(test_dir_with_slash.exists(), "Directory should be created")
        self.assertTrue(
            (test_dir_with_slash / "main.py").exists(),
            "main.py should be created in directory",
        )

        # Test 2: Directory without extension (no slash)
        test_dir_no_ext = self.test_specific_dir / "dir_creation_test_no_ext"
        self.assertFalse(
            test_dir_no_ext.exists(), "Test directory should not exist initially"
        )

        syncer_no_ext = KiCadToPythonSyncer(
            kicad_project=str(self.reference_project),
            python_file=str(test_dir_no_ext),
            preview_only=False,
            create_backup=False,
        )
        self.assertTrue(
            syncer_no_ext.is_directory_mode,
            "Should detect directory mode for path without extension",
        )

        success = syncer_no_ext.sync()
        self.assertTrue(success, "Directory creation without extension should succeed")
        self.assertTrue(test_dir_no_ext.exists(), "Directory should be created")
        self.assertTrue(
            (test_dir_no_ext / "main.py").exists(),
            "main.py should be created in directory",
        )

        # Test 3: File with .py extension
        test_file_py = self.test_specific_dir / "file_creation_test.py"
        self.assertFalse(test_file_py.exists(), "Test file should not exist initially")

        syncer_file = KiCadToPythonSyncer(
            kicad_project=str(self.reference_project),
            python_file=str(test_file_py),
            preview_only=False,
            create_backup=False,
        )
        self.assertFalse(
            syncer_file.is_directory_mode, "Should detect file mode for .py extension"
        )

        success = syncer_file.sync()
        self.assertTrue(success, "File creation should succeed")
        self.assertTrue(test_file_py.exists(), "Python file should be created")
        self.assertFalse(test_file_py.is_dir(), "Should be a file, not a directory")

    def test_preview_mode_with_non_existent_paths(self):
        """Test that preview mode works with non-existent directories"""
        if not self.reference_project.exists():
            self.skipTest(f"Reference project not found at {self.reference_project}")

        # Test preview mode with non-existent directory - don't create any structure beforehand
        test_preview_dir = Path("/tmp/circuit_synth_preview_test_dir/")
        self.assertFalse(
            test_preview_dir.exists(),
            "Preview test directory should not exist initially",
        )

        syncer = KiCadToPythonSyncer(
            kicad_project=str(self.reference_project),
            python_file=str(test_preview_dir),
            preview_only=True,  # Important: preview mode
            create_backup=False,
        )
        self.assertTrue(
            syncer.is_directory_mode, "Should detect directory mode in preview"
        )

        success = syncer.sync()
        self.assertTrue(success, "Preview mode should succeed")
        self.assertFalse(
            test_preview_dir.exists(), "Directory should NOT be created in preview mode"
        )

    def test_full_round_trip_kicad_python_kicad_python(self):
        """Test complete round-trip: KiCad→Python→KiCad→Python with no data loss"""
        if not self.reference_project.exists():
            self.skipTest(f"Reference project not found at {self.reference_project}")

        # Step 1: KiCad → Python (first conversion)
        first_python_dir = self.test_specific_dir / "first_python_conversion"
        first_python_dir.mkdir(parents=True, exist_ok=True)

        syncer1 = KiCadToPythonSyncer(
            kicad_project=str(self.reference_project),
            python_file=str(first_python_dir),
            preview_only=False,
            create_backup=False,
        )
        success1 = syncer1.sync()
        self.assertTrue(success1, "First KiCad-to-Python conversion should succeed")

        first_main_py = first_python_dir / "main.py"
        self.assertTrue(first_main_py.exists(), "First main.py should be created")
        first_python_code = first_main_py.read_text()

        # Step 2: Python → KiCad (execute first Python to create KiCad project)
        import subprocess
        import sys

        result1 = subprocess.run(
            [sys.executable, str(first_main_py)],
            cwd=str(first_python_dir),
            capture_output=True,
            text=True,
        )

        self.assertEqual(
            result1.returncode,
            0,
            f"First Python execution should succeed.\nstdout: {result1.stdout}\nstderr: {result1.stderr}",
        )

        # Step 3: Verify first generated KiCad project exists
        first_generated_kicad = (
            first_python_dir / "01_simple_resistor_reference_generated"
        )
        self.assertTrue(
            first_generated_kicad.exists(), "First generated KiCad project should exist"
        )

        first_generated_sch = (
            first_generated_kicad / "01_simple_resistor_reference_generated.kicad_sch"
        )
        self.assertTrue(
            first_generated_sch.exists(), "First generated schematic should exist"
        )

        # Step 4: KiCad → Python (second conversion from generated KiCad)
        second_python_dir = self.test_specific_dir / "second_python_conversion"
        second_python_dir.mkdir(parents=True, exist_ok=True)

        syncer2 = KiCadToPythonSyncer(
            kicad_project=str(
                first_generated_kicad
            ),  # Use the generated KiCad as input
            python_file=str(second_python_dir),
            preview_only=False,
            create_backup=False,
        )
        success2 = syncer2.sync()
        self.assertTrue(success2, "Second KiCad-to-Python conversion should succeed")

        second_main_py = second_python_dir / "main.py"
        self.assertTrue(second_main_py.exists(), "Second main.py should be created")
        second_python_code = second_main_py.read_text()

        # Step 5: Compare Python codes for data integrity
        # Both Python files should contain the same essential circuit data

        # Check that both contain the same component
        self.assertIn(
            'ref="R1"', first_python_code, "First Python should have R1 reference"
        )
        self.assertIn(
            'ref="R1"', second_python_code, "Second Python should have R1 reference"
        )

        self.assertIn(
            'symbol="Device:R"',
            first_python_code,
            "First Python should have Device:R symbol",
        )
        self.assertIn(
            'symbol="Device:R"',
            second_python_code,
            "Second Python should have Device:R symbol",
        )

        self.assertIn(
            'value="10k"', first_python_code, "First Python should have 10k value"
        )
        self.assertIn(
            'value="10k"', second_python_code, "Second Python should have 10k value"
        )

        self.assertIn(
            'footprint="Resistor_SMD:R_0603_1608Metric"',
            first_python_code,
            "First Python should have correct footprint",
        )
        self.assertIn(
            'footprint="Resistor_SMD:R_0603_1608Metric"',
            second_python_code,
            "Second Python should have correct footprint",
        )

        # Step 6: Execute second Python to create second KiCad project
        result2 = subprocess.run(
            [sys.executable, str(second_main_py)],
            cwd=str(second_python_dir),
            capture_output=True,
            text=True,
        )

        self.assertEqual(
            result2.returncode,
            0,
            f"Second Python execution should succeed.\nstdout: {result2.stdout}\nstderr: {result2.stderr}",
        )

        # Step 7: Verify second generated KiCad project
        # Note: The second conversion will have a different project name since it's generated from the first generated project
        second_generated_kicad = (
            second_python_dir / "01_simple_resistor_reference_generated_generated"
        )
        self.assertTrue(
            second_generated_kicad.exists(),
            "Second generated KiCad project should exist",
        )

        second_generated_sch = (
            second_generated_kicad
            / "01_simple_resistor_reference_generated_generated.kicad_sch"
        )
        self.assertTrue(
            second_generated_sch.exists(), "Second generated schematic should exist"
        )

        # Step 8: Compare KiCad schematic content for data integrity
        original_sch_content = (
            self.reference_project / "01_simple_resistor_reference.kicad_sch"
        ).read_text()
        first_generated_sch_content = first_generated_sch.read_text()
        second_generated_sch_content = second_generated_sch.read_text()

        # All three should contain the same essential component data
        essential_checks = [
            '"Device:R"',  # Symbol reference
            '"R1"',  # Component reference
            '"10k"',  # Component value
            '"Resistor_SMD:R_0603_1608Metric"',  # Footprint
        ]

        for check in essential_checks:
            self.assertIn(
                check,
                original_sch_content,
                f"Original schematic should contain {check}",
            )
            self.assertIn(
                check,
                first_generated_sch_content,
                f"First generated schematic should contain {check}",
            )
            self.assertIn(
                check,
                second_generated_sch_content,
                f"Second generated schematic should contain {check}",
            )

        # Step 9: Verify project name evolution
        # Original: 01_simple_resistor_reference
        # First generated: 01_simple_resistor_reference_generated
        # Second generated: 01_simple_resistor_reference_generated_generated

        self.assertIn(
            'project_name="01_simple_resistor_reference_generated"',
            first_python_code,
            "First Python should generate with _generated suffix",
        )
        self.assertIn(
            'project_name="01_simple_resistor_reference_generated_generated"',
            second_python_code,
            "Second Python should generate with double _generated suffix",
        )

        # Step 10: Log success for manual verification
        print(f"\n✅ ROUND TRIP SUCCESS:")
        print(f"   Original KiCad: {self.reference_project}")
        print(f"   First Python:   {first_python_dir}/main.py")
        print(f"   First KiCad:    {first_generated_kicad}")
        print(f"   Second Python:  {second_python_dir}/main.py")
        print(f"   Second KiCad:   {second_generated_kicad}")
        print(f"   All files preserved component data integrity! 🎉")


if __name__ == "__main__":
    unittest.main()
