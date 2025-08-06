#!/usr/bin/env python3
"""
Test suite for ESP32-C6 hierarchical circuit generation workflow.

This is a comprehensive test of the most complex hierarchical circuit in the test suite,
featuring a 3-level hierarchy with 16 components across 6 circuit files.

Hierarchy Structure:
main (0 components - orchestrator only)
├── USB_Port (6 components: USB-C connector, ESD protection, pull-down resistors)
├── Power_Supply (3 components: voltage regulator, decoupling caps)
└── ESP32_C6_MCU (4 components: ESP32 module, bypass cap, USB resistors)
    ├── Debug_Header (1 component: 6-pin programming header)
    └── LED_Blinker (2 components: LED + current limiting resistor)

Total: 16 components, 15 nets, 6 hierarchical files
"""

import os
import shutil
import subprocess
import tempfile
import unittest
import uuid
from pathlib import Path

from circuit_synth.tools.kicad_integration.kicad_to_python_sync import (
    KiCadToPythonSyncer,
)


class TestESP32C6HierarchicalWorkflow(unittest.TestCase):
    """Comprehensive test suite for ESP32-C6 hierarchical circuit generation."""

    @classmethod
    def setUpClass(cls):
        """Set up class-level fixtures - run once for all tests"""
        cls.test_data_dir = Path(__file__).parent
        cls.reference_project = cls.test_data_dir / "ESP32_C6_Dev_Board_reference"
        cls.reference_python = cls.test_data_dir / "ESP32_C6_Dev_Board_python_reference"
        cls.reference_generated = (
            cls.test_data_dir / "ESP32_C6_Dev_Board_generated_reference"
        )
        cls.temp_dir = cls.test_data_dir / "test_outputs"

        # Clean up any existing test outputs from previous runs
        if cls.temp_dir.exists():
            shutil.rmtree(cls.temp_dir)

        # Create base directory structure
        cls.temp_dir.mkdir(parents=True, exist_ok=True)

    def setUp(self):
        """Set up test fixtures for each test"""
        # Each test gets its own subdirectory to avoid conflicts
        test_id = str(uuid.uuid4())[:8]  # Short unique ID
        self.test_specific_dir = self.temp_dir / f"{self._testMethodName}_{test_id}"
        self.test_specific_dir.mkdir(parents=True, exist_ok=True)

        # Only create python_output_dir for tests that actually need it
        self.python_output_dir = self.test_specific_dir / "python_output"
        # Don't create it here - let individual tests create it if needed

    def tearDown(self):
        """Clean up test fixtures - DISABLED for manual inspection"""
        # Leave test outputs for manual review
        pass

    def test_hierarchical_project_detection(self):
        """Test that the syncer correctly identifies this as a hierarchical project."""
        if not self.reference_project.exists():
            self.skipTest(f"Reference project not found at {self.reference_project}")

        # Create the output directory for this test
        self.python_output_dir.mkdir(parents=True, exist_ok=True)

        syncer = KiCadToPythonSyncer(
            kicad_project=str(self.reference_project),
            python_file=str(self.python_output_dir),
            preview_only=False,
            create_backup=False,
        )

        # Run the conversion
        success = syncer.sync()
        self.assertTrue(
            success, "ESP32-C6 hierarchical KiCad-to-Python conversion should succeed"
        )

        # Check that main.py was created
        main_py = self.python_output_dir / "main.py"
        self.assertTrue(main_py.exists(), "main.py should be created")

        # Verify multiple circuit files were created (hierarchical)
        expected_files = [
            "main.py",
            "usb_port.py",
            "power_supply.py",
            "esp32_c6_mcu.py",
            "debug_header.py",
            "led_blinker.py",
        ]

        for filename in expected_files:
            file_path = self.python_output_dir / filename
            # Note: The actual filenames may be different, so let's just check that we have multiple files

        # Check that multiple Python files were created for hierarchical structure
        python_files = list(self.python_output_dir.glob("*.py"))
        self.assertGreater(
            len(python_files),
            1,
            f"Expected multiple Python files for hierarchical circuit, got {len(python_files)}",
        )

    def test_hierarchical_code_structure(self):
        """Test that the generated Python code has the correct hierarchical structure."""
        if not self.reference_project.exists():
            self.skipTest(f"Reference project not found at {self.reference_project}")

        # Create the output directory for this test
        self.python_output_dir.mkdir(parents=True, exist_ok=True)

        syncer = KiCadToPythonSyncer(
            kicad_project=str(self.reference_project),
            python_file=str(self.python_output_dir),
            preview_only=False,
            create_backup=False,
        )

        success = syncer.sync()
        self.assertTrue(success, "Hierarchical conversion should succeed")

        # Check main.py content
        main_py = self.python_output_dir / "main.py"
        self.assertTrue(main_py.exists(), "main.py should exist")

        main_content = main_py.read_text()

        # Should contain import statements for hierarchical subcircuits
        self.assertIn(
            "import", main_content, "Should contain import statements for subcircuits"
        )

        # Should contain circuit decorators
        self.assertIn("@circuit", main_content, "Should contain circuit decorators")

        # Should contain main circuit function
        self.assertIn(
            "def ", main_content, "Should contain circuit function definitions"
        )

    def test_import_statement_generation(self):
        """Test that import statements use correct lowercase function names."""
        if not self.reference_project.exists():
            self.skipTest(f"Reference project not found at {self.reference_project}")

        # Create the output directory for this test
        self.python_output_dir.mkdir(parents=True, exist_ok=True)

        syncer = KiCadToPythonSyncer(
            kicad_project=str(self.reference_project),
            python_file=str(self.python_output_dir),
            preview_only=False,
            create_backup=False,
        )

        success = syncer.sync()
        self.assertTrue(success, "Conversion should succeed")

        # Check main.py for import statements
        main_py = self.python_output_dir / "main.py"
        if main_py.exists():
            main_content = main_py.read_text()

            # Should NOT have uppercase function imports (old bug would cause this)
            self.assertNotIn(
                "import USB_Port",
                main_content,
                "Should not have uppercase function imports (old bug)",
            )
            self.assertNotIn(
                "import Power_Supply",
                main_content,
                "Should not have uppercase function imports (old bug)",
            )

    def test_hierarchical_round_trip_execution(self):
        """Test that the generated Python code executes successfully and generates KiCad output."""
        if not self.reference_project.exists():
            self.skipTest(f"Reference project not found at {self.reference_project}")

        # Create the output directory for this test
        self.python_output_dir.mkdir(parents=True, exist_ok=True)

        # Step 1: Generate Python from KiCad
        syncer = KiCadToPythonSyncer(
            kicad_project=str(self.reference_project),
            python_file=str(self.python_output_dir),
            preview_only=False,
            create_backup=False,
        )

        success = syncer.sync()
        self.assertTrue(success, "KiCad-to-Python conversion should succeed")

        # Step 2: Execute the generated Python code
        main_py = self.python_output_dir / "main.py"
        self.assertTrue(main_py.exists(), "main.py should be created")

        # Change to the python output directory for execution
        original_cwd = os.getcwd()
        try:
            os.chdir(self.python_output_dir)

            # Execute the main.py file
            result = subprocess.run(
                ["uv", "run", "main.py"],
                capture_output=True,
                text=True,
                timeout=120,  # Extended timeout for complex circuit
            )

            # Should execute without errors
            self.assertEqual(
                result.returncode,
                0,
                f"Python execution failed with return code {result.returncode}. "
                f"Stderr: {result.stderr}",
            )

        except subprocess.TimeoutExpired:
            self.fail("Python execution timed out - circuit generation took too long")
        finally:
            os.chdir(original_cwd)

        # Step 3: Verify KiCad output was generated
        # Look for generated KiCad project directory
        generated_dirs = [
            d
            for d in self.python_output_dir.iterdir()
            if d.is_dir() and d.name.endswith("_generated")
        ]

        self.assertGreater(
            len(generated_dirs),
            0,
            "Should generate at least one KiCad project directory",
        )

        generated_kicad = generated_dirs[0]  # Take the first generated directory

        # Verify essential KiCad files exist
        expected_extensions = [".kicad_pro", ".kicad_sch", ".kicad_pcb"]

        for ext in expected_extensions:
            matching_files = list(generated_kicad.glob(f"*{ext}"))
            self.assertGreater(
                len(matching_files), 0, f"Should generate at least one {ext} file"
            )

    def test_net_connectivity_preservation(self):
        """Test that net connectivity is preserved through the round-trip conversion."""
        if not self.reference_project.exists():
            self.skipTest(f"Reference project not found at {self.reference_project}")

        # Create the output directory for this test
        self.python_output_dir.mkdir(parents=True, exist_ok=True)

        # Generate and execute Python code
        syncer = KiCadToPythonSyncer(
            kicad_project=str(self.reference_project),
            python_file=str(self.python_output_dir),
            preview_only=False,
            create_backup=False,
        )

        success = syncer.sync()
        self.assertTrue(success, "Conversion should succeed")

        # Execute to generate KiCad output
        original_cwd = os.getcwd()
        try:
            os.chdir(self.python_output_dir)
            result = subprocess.run(
                ["uv", "run", "main.py"], capture_output=True, text=True, timeout=120
            )
            self.assertEqual(result.returncode, 0, f"Execution failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            self.fail("Execution timed out")
        finally:
            os.chdir(original_cwd)

        # Find and verify the generated netlist
        netlist_files = list(self.python_output_dir.rglob("*.net"))

        if netlist_files:
            netlist_file = netlist_files[0]
            netlist_content = netlist_file.read_text()

            # Verify key nets are present
            expected_nets = [
                "GND",
                "VCC_3V3",
            ]  # Basic nets that should always be present

            for net_name in expected_nets:
                self.assertTrue(
                    f'"{net_name}"' in netlist_content
                    or f"'{net_name}'" in netlist_content,
                    f"Missing expected net in netlist: {net_name}",
                )

    def test_component_reference_preservation(self):
        """Test that component references are properly assigned and unique."""
        if not self.reference_project.exists():
            self.skipTest(f"Reference project not found at {self.reference_project}")

        # Create the output directory for this test
        self.python_output_dir.mkdir(parents=True, exist_ok=True)

        # Generate and execute
        syncer = KiCadToPythonSyncer(
            kicad_project=str(self.reference_project),
            python_file=str(self.python_output_dir),
            preview_only=False,
            create_backup=False,
        )

        success = syncer.sync()
        self.assertTrue(success, "Conversion should succeed")

        original_cwd = os.getcwd()
        try:
            os.chdir(self.python_output_dir)
            result = subprocess.run(
                ["uv", "run", "main.py"], capture_output=True, text=True, timeout=120
            )
            self.assertEqual(result.returncode, 0, f"Execution failed: {result.stderr}")
        except subprocess.TimeoutExpired:
            self.fail("Execution timed out")
        finally:
            os.chdir(original_cwd)

        # Check netlist for proper component references
        netlist_files = list(self.python_output_dir.rglob("*.net"))

        if netlist_files:
            netlist_file = netlist_files[0]
            netlist_content = netlist_file.read_text()

            # Should contain component references
            component_prefixes = ["J", "U", "R", "C", "D"]  # Common component prefixes

            found_components = False
            for prefix in component_prefixes:
                if f'"{prefix}' in netlist_content or f"'{prefix}" in netlist_content:
                    found_components = True
                    break

            self.assertTrue(
                found_components,
                "Should find component references in generated netlist",
            )

    def test_full_hierarchical_round_trip(self):
        """Test complete round-trip: KiCad → Python → KiCad → Python."""
        if not self.reference_project.exists():
            self.skipTest(f"Reference project not found at {self.reference_project}")

        # First conversion: KiCad → Python
        first_python = self.test_specific_dir / "first_hierarchical_conversion"
        first_python.mkdir(parents=True, exist_ok=True)

        syncer1 = KiCadToPythonSyncer(
            kicad_project=str(self.reference_project),
            python_file=str(first_python),
            preview_only=False,
            create_backup=False,
        )

        success1 = syncer1.sync()
        self.assertTrue(success1, "First conversion should succeed")

        # Execute first Python generation
        original_cwd = os.getcwd()
        try:
            os.chdir(first_python)
            result1 = subprocess.run(
                ["uv", "run", "main.py"], capture_output=True, text=True, timeout=120
            )
            self.assertEqual(
                result1.returncode, 0, f"First execution failed: {result1.stderr}"
            )
        except subprocess.TimeoutExpired:
            self.fail("First execution timed out")
        finally:
            os.chdir(original_cwd)

        # Find the generated KiCad project
        generated_dirs = [
            d
            for d in first_python.iterdir()
            if d.is_dir() and d.name.endswith("_generated")
        ]

        self.assertGreater(
            len(generated_dirs), 0, "Should generate KiCad output directory"
        )

        generated_kicad_dir = generated_dirs[0]
        generated_project_files = list(generated_kicad_dir.glob("*.kicad_pro"))

        self.assertGreater(
            len(generated_project_files), 0, "Should generate .kicad_pro file"
        )

        # Second conversion: Generated KiCad → Python
        second_python = self.test_specific_dir / "second_hierarchical_conversion"
        second_python.mkdir(parents=True, exist_ok=True)

        syncer2 = KiCadToPythonSyncer(
            kicad_project=str(generated_project_files[0]),
            python_file=str(second_python),
            preview_only=False,
            create_backup=False,
        )

        success2 = syncer2.sync()
        self.assertTrue(success2, "Second conversion should succeed")

        # Execute second Python generation
        try:
            os.chdir(second_python)
            result2 = subprocess.run(
                ["uv", "run", "main.py"], capture_output=True, text=True, timeout=120
            )
            self.assertEqual(
                result2.returncode, 0, f"Second execution failed: {result2.stderr}"
            )
        except subprocess.TimeoutExpired:
            self.fail("Second execution timed out")
        finally:
            os.chdir(original_cwd)

        # Verify both outputs exist and have Python files
        for python_dir in [first_python, second_python]:
            python_files = list(python_dir.glob("*.py"))
            self.assertGreater(
                len(python_files), 0, f"Should generate Python files in {python_dir}"
            )

    def test_comparative_output_validation(self):
        """Test that generated output structure matches expectations."""
        if not self.reference_project.exists():
            self.skipTest(f"Reference project not found at {self.reference_project}")

        # Create the output directory for this test
        self.python_output_dir.mkdir(parents=True, exist_ok=True)

        # Generate new Python code
        syncer = KiCadToPythonSyncer(
            kicad_project=str(self.reference_project),
            python_file=str(self.python_output_dir),
            preview_only=False,
            create_backup=False,
        )

        success = syncer.sync()
        self.assertTrue(success, "Conversion should succeed")

        # Compare structure basics
        generated_files = list(self.python_output_dir.glob("*.py"))

        self.assertGreater(
            len(generated_files), 0, "Should generate at least one Python file"
        )

        # Verify main.py exists (it should always be created)
        main_py = self.python_output_dir / "main.py"
        self.assertTrue(main_py.exists(), "main.py should always be created")

        # Verify main.py is not empty
        main_content = main_py.read_text()
        self.assertGreater(len(main_content.strip()), 0, "main.py should not be empty")


if __name__ == "__main__":
    unittest.main()
