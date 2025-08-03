#!/usr/bin/env python3
"""
Unit tests for 02_dual_hierarchy KiCad-to-Python workflow.

Tests hierarchical KiCad projects with multiple sheets and components,
focusing on proper subcircuit generation and hierarchical code structure.
"""

import os
import tempfile
import unittest
import subprocess
import sys
from pathlib import Path
from textwrap import dedent

from circuit_synth.tools.kicad_to_python_sync import KiCadToPythonSyncer
from circuit_synth.tools.python_code_generator import PythonCodeGenerator


class Test02DualHierarchyWorkflow(unittest.TestCase):
    """Test KiCad-to-Python workflow for dual hierarchy circuit"""

    @classmethod
    def setUpClass(cls):
        """Set up class-level fixtures - run once for all tests"""
        cls.test_data_dir = Path(__file__).parent
        cls.reference_project = cls.test_data_dir / "02_dual_hierarchy"
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
        # To clean up manually, delete: tests/kicad_to_python/02_dual_hierarchy/test_outputs/
        pass

    def test_hierarchical_project_detection(self):
        """Test that hierarchical projects are correctly identified"""
        if not self.reference_project.exists():
            self.skipTest(f"Reference project not found at {self.reference_project}")
            
        # Create the output directory for this test
        self.python_output_dir.mkdir(parents=True, exist_ok=True)
        
        syncer = KiCadToPythonSyncer(
            kicad_project=str(self.reference_project),
            python_file=str(self.python_output_dir),
            preview_only=False,
            create_backup=False
        )
        
        # Run the conversion
        success = syncer.sync()
        self.assertTrue(success, "Hierarchical KiCad-to-Python conversion should succeed")
        
        # Check that main.py was created
        main_py = self.python_output_dir / "main.py"
        self.assertTrue(main_py.exists(), "main.py should be created")
        
        generated_code = main_py.read_text()
        
        # Should generate hierarchical code with subcircuits
        self.assertIn("def child1()", generated_code, "Should generate child1 subcircuit function")
        self.assertIn("def main()", generated_code, "Should generate main circuit function")
        self.assertIn("@circuit(name='child1')", generated_code, "Should have child1 circuit decorator")
        self.assertIn("@circuit(name='main')", generated_code, "Should have main circuit decorator")

    def test_component_distribution_across_hierarchy(self):
        """Test that components are correctly distributed across hierarchical circuits"""
        if not self.reference_project.exists():
            self.skipTest(f"Reference project not found at {self.reference_project}")
            
        # Create the output directory for this test
        self.python_output_dir.mkdir(parents=True, exist_ok=True)
        
        syncer = KiCadToPythonSyncer(
            kicad_project=str(self.reference_project),
            python_file=str(self.python_output_dir),
            preview_only=False,
            create_backup=False
        )
        
        success = syncer.sync()
        self.assertTrue(success, "Conversion should succeed")
        
        main_py = self.python_output_dir / "main.py"
        generated_code = main_py.read_text()
        
        # Root sheet should have R1
        self.assertIn('ref="R1"', generated_code, "Main circuit should contain R1")
        self.assertIn('symbol="Device:R"', generated_code, "Should have Device:R symbols")
        self.assertIn('value="10k"', generated_code, "Should preserve 10k values")
        self.assertIn('footprint="Resistor_SMD:R_0603_1608Metric"', generated_code, "Should preserve footprints")
        
        # Child sheet should have R2
        self.assertIn('ref="R2"', generated_code, "Child circuit should contain R2")
        
        # Should have exactly 2 components total (R1 in main, R2 in child1)
        r_component_count = generated_code.count('Component(symbol="Device:R"')
        self.assertEqual(r_component_count, 2, "Should have exactly 2 resistor components")

    def test_subcircuit_instantiation(self):
        """Test that subcircuits are properly instantiated in the main circuit"""
        if not self.reference_project.exists():
            self.skipTest(f"Reference project not found at {self.reference_project}")
            
        # Create the output directory for this test
        self.python_output_dir.mkdir(parents=True, exist_ok=True)
        
        syncer = KiCadToPythonSyncer(
            kicad_project=str(self.reference_project),
            python_file=str(self.python_output_dir),
            preview_only=False,
            create_backup=False
        )
        
        success = syncer.sync()
        self.assertTrue(success, "Conversion should succeed")
        
        main_py = self.python_output_dir / "main.py"
        generated_code = main_py.read_text()
        
        # Should instantiate the child circuit in main
        self.assertIn("child1_instance = child1()", generated_code, "Should instantiate child1 subcircuit")
        
        # Should have proper function definitions
        self.assertIn("def child1():", generated_code, "Should define child1 function")
        self.assertIn("def main():", generated_code, "Should define main function")

    def test_hierarchical_code_structure(self):
        """Test the overall structure of generated hierarchical code"""
        if not self.reference_project.exists():
            self.skipTest(f"Reference project not found at {self.reference_project}")
            
        # Create the output directory for this test
        self.python_output_dir.mkdir(parents=True, exist_ok=True)
        
        syncer = KiCadToPythonSyncer(
            kicad_project=str(self.reference_project),
            python_file=str(self.python_output_dir),
            preview_only=False,
            create_backup=False
        )
        
        success = syncer.sync()
        self.assertTrue(success, "Conversion should succeed")
        
        main_py = self.python_output_dir / "main.py"
        generated_code = main_py.read_text()
        
        # Check overall code structure
        self.assertIn("from circuit_synth import *", generated_code, "Should have proper imports")
        
        # Check that child circuit comes before main circuit (dependency order)
        child1_pos = generated_code.find("def child1()")
        main_pos = generated_code.find("def main()")
        self.assertGreater(main_pos, child1_pos, "Main function should come after child functions")
        
        # Should have generation code at the end
        self.assertIn("if __name__ == '__main__':", generated_code, "Should have main execution block")
        self.assertIn("circuit = main()", generated_code, "Should call main function")
        self.assertIn('project_name="02_dual_hierarchy_generated"', generated_code, "Should generate with correct project name")

    def test_hierarchical_round_trip_execution(self):
        """Test that generated hierarchical Python code executes and creates KiCad project"""
        if not self.reference_project.exists():
            self.skipTest(f"Reference project not found at {self.reference_project}")
            
        # Create the output directory for this test
        self.python_output_dir.mkdir(parents=True, exist_ok=True)
        
        # Step 1: Convert KiCad to Python
        syncer = KiCadToPythonSyncer(
            kicad_project=str(self.reference_project),
            python_file=str(self.python_output_dir),
            preview_only=False,
            create_backup=False
        )
        
        success = syncer.sync()
        self.assertTrue(success, "Conversion should succeed")
        
        main_py = self.python_output_dir / "main.py"
        self.assertTrue(main_py.exists(), "main.py should be created")
        
        # Step 2: Execute the generated Python
        result = subprocess.run([
            sys.executable, str(main_py)
        ], cwd=str(self.python_output_dir), capture_output=True, text=True)
        
        self.assertEqual(result.returncode, 0, 
                        f"Generated hierarchical Python should execute successfully.\nstdout: {result.stdout}\nstderr: {result.stderr}")
        
        # Step 3: Verify generated KiCad project
        generated_project_dir = self.python_output_dir / "02_dual_hierarchy_generated"
        self.assertTrue(generated_project_dir.exists(), "Generated KiCad project should exist")
        
        # Should have both root schematic and child schematic
        root_sch = generated_project_dir / "02_dual_hierarchy_generated.kicad_sch"
        child_sch = generated_project_dir / "child1.kicad_sch"
        
        self.assertTrue(root_sch.exists(), "Root schematic should be generated")
        self.assertTrue(child_sch.exists(), "Child schematic should be generated")
        
        # Verify component content in schematics
        root_content = root_sch.read_text()
        child_content = child_sch.read_text()
        
        # Root should contain R1, child should contain R2
        self.assertIn('"R1"', root_content, "Root schematic should contain R1")
        self.assertIn('"R2"', child_content, "Child schematic should contain R2")
        
        # Both should have the same component type and specs
        for content, component in [(root_content, "R1"), (child_content, "R2")]:
            self.assertIn('"Device:R"', content, f"Should contain Device:R symbol for {component}")
            self.assertIn('"10k"', content, f"Should contain 10k value for {component}")
            self.assertIn('"Resistor_SMD:R_0603_1608Metric"', content, f"Should contain correct footprint for {component}")

    def test_hierarchical_reference_preservation(self):
        """Test that component references are preserved across hierarchy levels"""
        if not self.reference_project.exists():
            self.skipTest(f"Reference project not found at {self.reference_project}")
            
        # Create the output directory for this test
        self.python_output_dir.mkdir(parents=True, exist_ok=True)
        
        syncer = KiCadToPythonSyncer(
            kicad_project=str(self.reference_project),
            python_file=str(self.python_output_dir),
            preview_only=False,
            create_backup=False
        )
        
        success = syncer.sync()
        self.assertTrue(success, "Conversion should succeed")
        
        main_py = self.python_output_dir / "main.py"
        generated_code = main_py.read_text()
        
        # Both components should preserve their exact references from KiCad
        self.assertIn('ref="R1"', generated_code, "Should preserve R1 reference from root sheet")
        self.assertIn('ref="R2"', generated_code, "Should preserve R2 reference from child sheet")
        
        # Should NOT have truncated references
        self.assertNotIn('ref="R"', generated_code, "Should NOT have truncated references")
        
        # References should be in the correct circuit contexts
        # Find the positions of the circuit definitions and component references
        child1_def_pos = generated_code.find("def child1()")
        main_def_pos = generated_code.find("def main()")
        
        r1_pos = generated_code.find('ref="R1"')
        r2_pos = generated_code.find('ref="R2"')
        
        # R2 should be in child1 circuit (between child1_def and main_def)
        self.assertGreater(r2_pos, child1_def_pos, "R2 should be defined after child1 function starts")
        self.assertLess(r2_pos, main_def_pos, "R2 should be defined before main function starts")
        
        # R1 should be in main circuit (after main_def)
        self.assertGreater(r1_pos, main_def_pos, "R1 should be defined after main function starts")

    def test_full_hierarchical_round_trip(self):
        """Test complete hierarchical round-trip: KiCad→Python→KiCad→Python"""
        if not self.reference_project.exists():
            self.skipTest(f"Reference project not found at {self.reference_project}")
            
        # Step 1: First KiCad → Python conversion
        first_python_dir = self.test_specific_dir / "first_hierarchical_conversion"
        first_python_dir.mkdir(parents=True, exist_ok=True)
        
        syncer1 = KiCadToPythonSyncer(
            kicad_project=str(self.reference_project),
            python_file=str(first_python_dir),
            preview_only=False,
            create_backup=False
        )
        
        success1 = syncer1.sync()
        self.assertTrue(success1, "First hierarchical conversion should succeed")
        
        first_main_py = first_python_dir / "main.py"
        first_python_code = first_main_py.read_text()
        
        # Step 2: Execute first Python to create first KiCad project
        result1 = subprocess.run([
            sys.executable, str(first_main_py)
        ], cwd=str(first_python_dir), capture_output=True, text=True)
        
        self.assertEqual(result1.returncode, 0, 
                        f"First hierarchical Python execution should succeed.\nstderr: {result1.stderr}")
        
        first_generated_kicad = first_python_dir / "02_dual_hierarchy_generated"
        self.assertTrue(first_generated_kicad.exists(), "First generated KiCad project should exist")
        
        # Step 3: Second KiCad → Python conversion (from generated KiCad)
        second_python_dir = self.test_specific_dir / "second_hierarchical_conversion"
        second_python_dir.mkdir(parents=True, exist_ok=True)
        
        syncer2 = KiCadToPythonSyncer(
            kicad_project=str(first_generated_kicad),
            python_file=str(second_python_dir),
            preview_only=False,
            create_backup=False
        )
        
        success2 = syncer2.sync()
        self.assertTrue(success2, "Second hierarchical conversion should succeed")
        
        second_main_py = second_python_dir / "main.py"
        second_python_code = second_main_py.read_text()
        
        # Step 4: Verify hierarchical data integrity across round trip
        
        # Both Python files should have the same hierarchical structure
        for code, iteration in [(first_python_code, "first"), (second_python_code, "second")]:
            self.assertIn("def child1()", code, f"{iteration} should have child1 function")
            self.assertIn("def main()", code, f"{iteration} should have main function")
            self.assertIn('ref="R1"', code, f"{iteration} should have R1 in main circuit")
            self.assertIn('ref="R2"', code, f"{iteration} should have R2 in child circuit")
            self.assertIn("child1_instance = child1()", code, f"{iteration} should instantiate child1")
        
        # Step 5: Execute second Python to create second KiCad project
        result2 = subprocess.run([
            sys.executable, str(second_main_py)
        ], cwd=str(second_python_dir), capture_output=True, text=True)
        
        self.assertEqual(result2.returncode, 0, 
                        f"Second hierarchical Python execution should succeed.\nstderr: {result2.stderr}")
        
        second_generated_kicad = second_python_dir / "02_dual_hierarchy_generated_generated"
        self.assertTrue(second_generated_kicad.exists(), "Second generated KiCad project should exist")
        
        # Step 6: Verify project name evolution
        self.assertIn('project_name="02_dual_hierarchy_generated"', first_python_code,
                      "First Python should generate with _generated suffix")
        self.assertIn('project_name="02_dual_hierarchy_generated_generated"', second_python_code,
                      "Second Python should generate with double _generated suffix")
        
        # Step 7: Log success for manual verification
        print(f"\n✅ HIERARCHICAL ROUND TRIP SUCCESS:")
        print(f"   Original KiCad: {self.reference_project}")
        print(f"   First Python:   {first_python_dir}/main.py")
        print(f"   First KiCad:    {first_generated_kicad}")
        print(f"   Second Python:  {second_python_dir}/main.py")
        print(f"   Second KiCad:   {second_generated_kicad}")
        print(f"   Hierarchical structure and component data preserved! 🎉")


if __name__ == "__main__":
    unittest.main()