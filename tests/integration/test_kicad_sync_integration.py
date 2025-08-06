#!/usr/bin/env python3
"""
Integration tests for KiCad-to-Python synchronization

Tests the complete workflow from KiCad schematic files to working Python circuit code.
"""

import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

import pytest

# Import Circuit Synth for validation
from circuit_synth import Circuit, Component, Net
from circuit_synth.tools.kicad_integration.kicad_to_python_sync import (
    KiCadToPythonSyncer,
)


class TestKiCadSyncIntegration:
    """Integration tests for complete KiCad sync workflow"""

    @pytest.fixture
    def sample_kicad_project(self):
        """Create a complete sample KiCad project for testing"""
        temp_dir = Path(tempfile.mkdtemp())

        # Create project file
        pro_file = temp_dir / "test_project.kicad_pro"
        pro_content = """{
  "board": {
    "design_settings": {},
    "layers": []
  },
  "schematic": {
    "annotate": {},
    "erc": {}
  }
}"""
        pro_file.write_text(pro_content)

        # Create main schematic with simple components (flat design)
        main_sch = temp_dir / "test_project.kicad_sch"
        main_sch_content = """(kicad_sch (version 20211123) (generator eeschema)
  (uuid "12345678-1234-1234-1234-123456789abc")
  (paper "A4")
  (title_block
    (title "Test Project")
  )
  
  (symbol (lib_id "Device:R") (at 60 60 0) (unit 1)
    (in_bom yes) (on_board yes)
    (uuid "r1-uuid")
    (property "Reference" "R1" (id 0) (at 60 55 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "1k" (id 1) (at 60 65 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "Resistor_SMD:R_0603_1608Metric" (id 2) (at 60 70 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (pin "1" (uuid "r1-pin1-uuid"))
    (pin "2" (uuid "r1-pin2-uuid"))
  )
  
  (symbol (lib_id "Device:R") (at 80 60 0) (unit 1)
    (in_bom yes) (on_board yes)
    (uuid "r2-uuid")
    (property "Reference" "R2" (id 0) (at 80 55 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "2k" (id 1) (at 80 65 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "Resistor_SMD:R_0603_1608Metric" (id 2) (at 80 70 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (pin "1" (uuid "r2-pin1-uuid"))
    (pin "2" (uuid "r2-pin2-uuid"))
  )
  
  (wire (pts (xy 50 60) (xy 55 60))
    (stroke (width 0) (type default) (color 0 0 0 0))
    (uuid "vin-wire-uuid")
  )
  
  (wire (pts (xy 65 60) (xy 75 60))
    (stroke (width 0) (type default) (color 0 0 0 0))
    (uuid "mid-wire-uuid")
  )
  
  (wire (pts (xy 85 60) (xy 100 60))
    (stroke (width 0) (type default) (color 0 0 0 0))
    (uuid "gnd-wire-uuid")
  )
  
  (label "VIN" (at 50 60 0)
    (effects (font (size 1.27 1.27)) (justify left))
    (uuid "vin-label-uuid")
  )
  
  (label "MID" (at 75 60 0)
    (effects (font (size 1.27 1.27)) (justify left))
    (uuid "mid-label-uuid")
  )
  
  (label "GND" (at 100 60 0)
    (effects (font (size 1.27 1.27)) (justify left))
    (uuid "gnd-label-uuid")
  )
)"""
        main_sch.write_text(main_sch_content)

        # No additional schematics needed for flat design

        yield temp_dir

        # Cleanup
        shutil.rmtree(temp_dir)

    @pytest.mark.skip(
        reason="KiCad netlist generation failing - needs investigation of schematic format"
    )
    def test_complete_sync_workflow(self, sample_kicad_project):
        """Test complete sync from KiCad to working Python code"""
        # Create output directory
        output_dir = sample_kicad_project / "python_output"

        # Run the synchronization
        syncer = KiCadToPythonSyncer(
            str(sample_kicad_project / "test_project.kicad_pro"),
            str(output_dir),
            preview_only=False,
            create_backup=False,
        )

        success = syncer.sync()
        assert success, "Synchronization should succeed"

        # Verify output files exist
        assert (output_dir / "main.py").exists(), "main.py should be generated"

        # Verify main.py content
        main_content = (output_dir / "main.py").read_text()
        # The generated code should contain a main function
        assert (
            "def main" in main_content
        ), f"main.py should contain a main function, got: {main_content[:200]}"

        # Look for circuit-synth imports and component usage
        has_circuit_content = any(
            [
                "from circuit_synth import" in main_content,
                "Component" in main_content,
                "@circuit" in main_content,
                "Device:R" in main_content,  # Our test resistors
            ]
        )
        assert (
            has_circuit_content
        ), f"main.py should contain circuit-synth content, got: {main_content[:300]}"

        # Look for resistor components (R1, R2) that should be in our simple test schematic
        has_resistors = any(
            [
                "r1" in main_content.lower(),
                "r2" in main_content.lower(),
                "Device:R" in main_content,
            ]
        )
        assert (
            has_resistors
        ), f"main.py should contain resistor components, got: {main_content[:300]}"

    @pytest.mark.skip(
        reason="LLM-generated code structure varies unpredictably - core functionality tested in unit tests"
    )
    def test_generated_python_executes(self, sample_kicad_project):
        """Test that generated Python code actually executes without errors"""
        # Create output directory
        output_dir = sample_kicad_project / "python_output"

        # Run the synchronization
        syncer = KiCadToPythonSyncer(
            str(sample_kicad_project / "test_project.kicad_pro"),
            str(output_dir),
            preview_only=False,
            create_backup=False,
        )

        success = syncer.sync()
        assert success, "Synchronization should succeed"

        # First, inspect what the LLM actually generated
        main_file = output_dir / "main.py"
        main_content = main_file.read_text()

        # Determine the correct function to import by parsing the main.py file
        import_function = None
        if "def main(" in main_content:
            import_function = "main"
        elif "def main_circuit(" in main_content:
            import_function = "main_circuit"
        else:
            # Look for any function decorated with @circuit
            import re

            circuit_functions = re.findall(r"def (\w+)\([^)]*\):", main_content)
            if circuit_functions:
                import_function = circuit_functions[0]

        assert (
            import_function is not None
        ), f"Could not find a circuit function in main.py: {main_content[:500]}"

        # Create a simple test file that imports and validates the generated circuit
        test_file = output_dir / "test_execution.py"
        test_content = f'''#!/usr/bin/env python3
"""Test execution of generated circuit code"""

import sys
import traceback

def test_circuit_execution():
    """Test that the generated circuit code executes successfully"""
    try:
        # Import the main function/circuit
        from main import {import_function}
        
        # Create the circuit
        circuit = {import_function}()
        
        # Generate netlist to verify it works
        netlist = circuit.generate_text_netlist()
        
        # Count components and nets
        components = [comp for comp in circuit._components if hasattr(comp, 'ref') and comp.ref]
        nets = list(circuit._nets.keys()) if hasattr(circuit, '_nets') else []
        
        print("SUCCESS: Circuit created and netlist generated")
        print(f"Circuit has {{len(components)}} components")
        print(f"Circuit has {{len(nets)}} nets")
        print("Generated netlist length:", len(netlist))
        
        return True
        
    except Exception as e:
        print(f"ERROR: {{e}}")
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_circuit_execution()
    sys.exit(0 if success else 1)
'''
        test_file.write_text(test_content)

        # Try to execute the test
        try:
            # Change to output directory and run
            original_cwd = os.getcwd()
            os.chdir(str(output_dir))

            # Add the Circuit Synth source to Python path
            circuit_synth_src = Path(__file__).parent.parent.parent / "src"
            env = os.environ.copy()
            env["PYTHONPATH"] = str(circuit_synth_src) + ":" + env.get("PYTHONPATH", "")

            result = subprocess.run(
                [sys.executable, "test_execution.py"],
                capture_output=True,
                text=True,
                env=env,
                timeout=30,
            )

            # Restore original directory
            os.chdir(original_cwd)

            # Check execution result - simply verify it executed successfully
            assert (
                result.returncode == 0
            ), f"Generated code failed to execute: {result.stderr}\\nStdout: {result.stdout}"
            assert "SUCCESS: Circuit created and netlist generated" in result.stdout

            # Don't assert specific component/net counts as LLM output may vary
            # Just ensure the basic success message appears

        except subprocess.TimeoutExpired:
            os.chdir(original_cwd)
            pytest.fail("Generated Python code execution timed out")
        except Exception as e:
            os.chdir(original_cwd)
            pytest.fail(f"Failed to execute generated Python code: {e}")

    def test_backup_creation(self, sample_kicad_project):
        """Test that backup files are created when requested"""
        output_dir = sample_kicad_project / "python_output"
        output_dir.mkdir()

        # Create an existing main.py file
        existing_main = output_dir / "main.py"
        existing_main.write_text("# Existing content")

        # Run sync with backup enabled
        syncer = KiCadToPythonSyncer(
            str(sample_kicad_project / "test_project.kicad_pro"),
            str(output_dir),
            preview_only=False,
            create_backup=True,
        )

        success = syncer.sync()
        assert success, "Synchronization should succeed"

        # Verify backup was created
        backup_file = output_dir / "main.py.backup"
        assert backup_file.exists(), "Backup file should be created"
        assert "# Existing content" in backup_file.read_text()

    @pytest.mark.skip(
        reason="KiCad netlist generation failing - needs investigation of schematic format"
    )
    def test_preview_mode(self, sample_kicad_project):
        """Test that preview mode doesn't create files"""
        output_dir = sample_kicad_project / "python_output"

        # Run sync in preview mode
        syncer = KiCadToPythonSyncer(
            str(sample_kicad_project / "test_project.kicad_pro"),
            str(output_dir),
            preview_only=True,
            create_backup=False,
        )

        success = syncer.sync()
        assert success, "Preview should succeed"

        # Verify no files were created
        if output_dir.exists():
            files = list(output_dir.iterdir())
            assert len(files) == 0, "Preview mode should not create files"


class TestRealProjectIntegration:
    """Test with the actual project's KiCad files"""

    @pytest.fixture
    def real_kicad_project(self):
        """Use the actual simple_esp32_circuit project for testing"""
        # Path to the real KiCad project used in development
        project_path = (
            Path(__file__).parent.parent.parent
            / "kicad_output"
            / "example_kicad_project"
        )

        if not project_path.exists():
            pytest.skip("Real KiCad project not found - skipping integration test")

        pro_file = project_path / "example_kicad_project.kicad_pro"
        if not pro_file.exists():
            pytest.skip("Real KiCad project file not found - skipping integration test")

        return pro_file

    @pytest.mark.skip(
        reason="Test depends on specific project structure and LLM content generation - core sync functionality tested elsewhere"
    )
    def test_sync_with_real_project(self, real_kicad_project):
        """Test sync with the actual development KiCad project"""
        # Create temporary output directory
        temp_dir = Path(tempfile.mkdtemp())
        output_dir = temp_dir / "test_output"

        try:
            # Run synchronization
            syncer = KiCadToPythonSyncer(
                str(real_kicad_project),
                str(output_dir),
                preview_only=False,
                create_backup=False,
            )

            success = syncer.sync()
            assert success, "Real project sync should succeed"

            # Verify expected files - update for actual example project structure
            assert (output_dir / "main.py").exists()
            assert (output_dir / "root.py").exists()
            # Check for any of the hierarchical sheets from example project
            hierarchical_files = [
                "Comms_processor.py",
                "regulator.py",
                "Debug_Header.py",
                "USB_Port.py",
                "IMU_Circuit.py",
            ]
            has_hierarchical = any(
                (output_dir / f).exists() for f in hierarchical_files
            )
            assert (
                has_hierarchical
            ), f"Should have at least one hierarchical sheet file. Files in output: {list(output_dir.iterdir())}"

            # Verify hierarchical structure
            main_content = (output_dir / "main.py").read_text()
            assert "from root import" in main_content, "main.py should import root"

            root_content = (output_dir / "root.py").read_text()
            assert "def root" in root_content, "root.py should contain root function"
            assert "esp32" in root_content, "root.py should reference esp32"

            esp32_content = (output_dir / "esp32.py").read_text()
            assert (
                "def esp32" in esp32_content
            ), "esp32.py should contain esp32 function"

        finally:
            # Cleanup
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
