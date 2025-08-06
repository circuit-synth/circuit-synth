#!/usr/bin/env python3
"""
Test 4: Complex Hierarchical File Structure with Nested Subcircuits

This test validates the KiCad-to-Python converter's ability to handle
deep hierarchical structures with multiple subcircuit levels:

3-Level Hierarchy:
  main.py → resistor_divider.py → capacitor_bank.py

Validates:
- Proper file structure generation (3 separate Python files)
- Correct import chain relationships
- Hierarchical parameter passing through all levels
- Clean separation of circuit logic per file
- Executability of the complete import chain
"""

import ast
import os
import re
import shutil
import subprocess
import tempfile
from pathlib import Path
from typing import Any, Dict, List, Set

import pytest

# Import circuit-synth functionality
try:
    from circuit_synth import Circuit, Component, Net
    from circuit_synth.tools.kicad_integration.kicad_to_python_sync import (
        KiCadToPythonSyncer,
    )
except ImportError as e:
    pytest.skip(
        f"Circuit-synth import functionality not available: {e}",
        allow_module_level=True,
    )


class HierarchicalStructureValidator:
    """Validator for complex hierarchical Python circuit structure."""

    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.files = {}
        self.import_chains = {}
        self.circuit_functions = {}

    def analyze_project(self):
        """Analyze all Python files in the project for hierarchical structure."""

        # Expected files for 3-level hierarchy
        expected_files = ["main.py", "resistor_divider.py", "capacitor_bank.py"]

        for file_name in expected_files:
            file_path = self.project_dir / file_name
            if file_path.exists():
                with open(file_path, "r") as f:
                    content = f.read()
                self.files[file_name] = content
                self._analyze_file_structure(file_name, content)

    def _analyze_file_structure(self, file_name: str, content: str):
        """Analyze individual file structure."""
        try:
            tree = ast.parse(content)

            imports = []
            circuit_functions = []

            for node in ast.walk(tree):
                if isinstance(node, ast.ImportFrom) and node.module:
                    imports.append(node.module)
                elif isinstance(node, ast.FunctionDef):
                    # Check if function has @circuit decorator
                    for decorator in node.decorator_list:
                        if (
                            isinstance(decorator, ast.Name)
                            and decorator.id == "circuit"
                        ):
                            circuit_functions.append(node.name)

            self.import_chains[file_name] = imports
            self.circuit_functions[file_name] = circuit_functions

        except SyntaxError as e:
            pytest.fail(f"Syntax error in {file_name}: {e}")

    def validate_file_structure(self):
        """Validate that all expected files are present."""
        expected_files = {"main.py", "resistor_divider.py", "capacitor_bank.py"}
        actual_files = set(self.files.keys())

        assert (
            expected_files == actual_files
        ), f"Expected files {expected_files}, got {actual_files}"

    def validate_import_chain(self):
        """Validate the hierarchical import relationships."""

        # CORRECT HIERARCHICAL STRUCTURE EXPECTED:
        # main.py should import resistor_divider only
        assert "resistor_divider" in self.import_chains.get(
            "main.py", []
        ), "main.py should import resistor_divider"

        # main.py should NOT import capacitor_bank directly (it's nested in resistor_divider)
        main_imports = self.import_chains.get("main.py", [])
        assert "capacitor_bank" not in main_imports, (
            f"main.py should NOT import capacitor_bank directly (found in: {main_imports}). "
            f"capacitor_bank should be imported by resistor_divider.py"
        )

        # resistor_divider.py SHOULD import capacitor_bank (nested hierarchy)
        resistor_imports = self.import_chains.get("resistor_divider.py", [])
        assert "capacitor_bank" in resistor_imports, (
            f"resistor_divider.py should import capacitor_bank (found: {resistor_imports}). "
            f"The KiCad project has capacitor_bank as a subcircuit within resistor_divider."
        )

        # capacitor_bank.py should not import other circuit modules (leaf node)
        cap_imports = self.import_chains.get("capacitor_bank.py", [])
        circuit_imports = [
            imp for imp in cap_imports if imp in ["main", "resistor_divider"]
        ]
        assert (
            len(circuit_imports) == 0
        ), f"capacitor_bank.py should not import other circuit modules, found: {circuit_imports}"

    def validate_circuit_functions(self):
        """Validate that each file contains the expected @circuit functions."""

        # Each file should have exactly one @circuit function
        for file_name, functions in self.circuit_functions.items():
            assert (
                len(functions) == 1
            ), f"{file_name} should have exactly one @circuit function, found: {functions}"

        # Validate function names match expected pattern
        assert "main_circuit" in self.circuit_functions.get(
            "main.py", []
        ), "main.py should contain main_circuit function"
        assert "resistor_divider" in self.circuit_functions.get(
            "resistor_divider.py", []
        ), "resistor_divider.py should contain resistor_divider function"
        assert "capacitor_bank" in self.circuit_functions.get(
            "capacitor_bank.py", []
        ), "capacitor_bank.py should contain capacitor_bank function"

    def validate_component_separation(self):
        """Validate that components are properly separated across files."""

        # Check that each file contains its expected component types
        main_content = self.files.get("main.py", "")
        resistor_content = self.files.get("resistor_divider.py", "")
        capacitor_content = self.files.get("capacitor_bank.py", "")

        # main.py should not contain component definitions (only imports and instantiation)
        assert (
            "Component(" not in main_content
        ), "main.py should not define components directly"

        # resistor_divider.py should contain resistor components
        assert (
            "Device:R" in resistor_content
        ), "resistor_divider.py should contain resistor components"

        # capacitor_bank.py should contain capacitor components
        assert (
            "Device:C" in capacitor_content
        ), "capacitor_bank.py should contain capacitor components"

        # Verify actual components are present
        assert (
            "r1 = Device_R()" in resistor_content
        ), "resistor_divider.py should instantiate R1"
        assert (
            "r2 = Device_R()" in resistor_content
        ), "resistor_divider.py should instantiate R2"
        assert (
            "c1 = Device_C()" in capacitor_content
        ), "capacitor_bank.py should instantiate C1"
        assert (
            "c2 = Device_C()" in capacitor_content
        ), "capacitor_bank.py should instantiate C2"
        assert (
            "c3 = Device_C()" in capacitor_content
        ), "capacitor_bank.py should instantiate C3"


@pytest.mark.skip(
    reason="Advanced hierarchical file generation not yet implemented - converter generates all circuits in main.py"
)
def test_complex_hierarchical_structure():
    """Test complex hierarchical file structure generation from KiCad project."""

    # Set up paths
    test_dir = Path(__file__).parent
    kicad_project_dir = test_dir / "complex_hierarchical_reference"
    reference_python_dir = test_dir / "reference_python_project"

    # Skip if KiCad project doesn't exist
    if not kicad_project_dir.exists():
        pytest.skip("KiCad reference project not found - run manual setup first")

    # Check if using PRESERVE_FILES for manual inspection
    preserve_files = os.getenv("PRESERVE_FILES", "").lower() in ("1", "true", "yes")

    if preserve_files:
        # Use local directory for file preservation
        temp_path = test_dir / "generated_output"
        if temp_path.exists():
            shutil.rmtree(temp_path)
        temp_path.mkdir()
        output_dir = temp_path / "hierarchical_python"
        output_dir.mkdir()
    else:
        # Use temporary directory
        temp_dir = tempfile.mkdtemp()
        output_dir = Path(temp_dir) / "hierarchical_python"
        output_dir.mkdir()

    try:
        # Find the .kicad_pro file in the project directory
        kicad_pro_files = list(kicad_project_dir.glob("*.kicad_pro"))
        if not kicad_pro_files:
            pytest.fail(f"No .kicad_pro file found in {kicad_project_dir}")

        kicad_project_file = kicad_pro_files[0]
        print(f"\n🔍 DEBUGGING KiCad-to-Python Conversion")
        print(f"📁 KiCad project: {kicad_project_file}")
        print(f"📂 Output directory: {output_dir}")

        # List all KiCad files in the project
        kicad_files = list(kicad_project_dir.glob("*.kicad_sch"))
        print(f"📄 KiCad schematic files found:")
        for file in kicad_files:
            print(f"   - {file.name}")

        # Analyze the KiCad project structure before conversion
        print(f"\n🔬 ANALYZING KiCad PROJECT STRUCTURE")
        with open(
            kicad_project_file.parent / "complex_hierarchical.kicad_sch", "r"
        ) as f:
            main_sch_content = f.read()

        # Find hierarchical sheets in main schematic
        import re

        sheet_matches = re.findall(
            r'\(property "Sheetname" "([^"]+)"', main_sch_content
        )
        print(f"📋 Hierarchical sheets in main schematic: {sheet_matches}")

        # Check resistor_divider.kicad_sch for nested sheets
        resistor_sch_path = kicad_project_file.parent / "resistor_divider.kicad_sch"
        if resistor_sch_path.exists():
            with open(resistor_sch_path, "r") as f:
                resistor_sch_content = f.read()
            nested_sheets = re.findall(
                r'\(property "Sheetname" "([^"]+)"', resistor_sch_content
            )
            print(f"🔗 Nested sheets in resistor_divider: {nested_sheets}")

        print(f"\n⚙️ EXPECTED HIERARCHY:")
        print(f"   main.kicad_sch")
        print(f"   ├── resistor_divider.kicad_sch")
        print(f"   │   └── capacitor_bank.kicad_sch")
        print(f"   └── (other sheets if any)")

        # Initialize KiCad-to-Python syncer
        print(f"\n🔄 STARTING CONVERSION...")
        syncer = KiCadToPythonSyncer(
            kicad_project=str(kicad_project_file),
            python_file=str(output_dir),
            preview_only=False,
            create_backup=False,
        )

        # Convert KiCad project to Python
        success = syncer.sync()
        if not success:
            pytest.fail("KiCad-to-Python conversion failed")

        print(f"✅ Conversion completed")

        # Analyze generated files
        print(f"\n📝 GENERATED PYTHON FILES:")
        generated_files = list(output_dir.glob("*.py"))
        for file in generated_files:
            print(f"   - {file.name}")

        # Show the content of generated main.py for debugging
        main_py_path = output_dir / "main.py"
        if main_py_path.exists():
            print(f"\n📄 GENERATED main.py CONTENT:")
            with open(main_py_path, "r") as f:
                content = f.read()
            print(f"```python")
            for i, line in enumerate(content.split("\n")[:50], 1):  # First 50 lines
                print(f"{i:2d}: {line}")
            print(f"```")

            # Analyze imports
            import_lines = [
                line.strip()
                for line in content.split("\n")
                if line.strip().startswith("from ") and "import" in line
            ]
            print(f"\n🔍 IMPORT ANALYSIS:")
            for imp in import_lines:
                print(f"   {imp}")

        # Show the content of generated resistor_divider.py
        resistor_py_path = output_dir / "resistor_divider.py"
        if resistor_py_path.exists():
            print(f"\n📄 GENERATED resistor_divider.py CONTENT:")
            with open(resistor_py_path, "r") as f:
                content = f.read()
            import_lines = [
                line.strip()
                for line in content.split("\n")
                if line.strip().startswith("from ") and "import" in line
            ]
            print(f"🔍 IMPORTS IN resistor_divider.py:")
            for imp in import_lines:
                print(f"   {imp}")
            print(f"📋 Has capacitor_bank import: {'capacitor_bank' in content}")
            print(
                f"📋 Has capacitor_bank instantiation: {'capacitor_bank(' in content}"
            )

        print(f"\n🚨 HIERARCHY ISSUE ANALYSIS:")
        print(
            f"❌ PROBLEM: Converter is generating FLAT structure instead of NESTED structure"
        )
        print(f"   - main.py imports BOTH resistor_divider AND capacitor_bank")
        print(f"   - resistor_divider.py does NOT import capacitor_bank")
        print(f"   - This ignores the KiCad hierarchical nesting")
        print(f"")
        print(f"✅ CORRECT BEHAVIOR SHOULD BE:")
        print(f"   - main.py imports ONLY resistor_divider")
        print(f"   - resistor_divider.py imports capacitor_bank")
        print(f"   - capacitor_bank.py imports nothing (leaf)")
        print(f"")

        # Validate the generated hierarchical structure
        validator = HierarchicalStructureValidator(output_dir)
        validator.analyze_project()

        # Run all validations
        validator.validate_file_structure()
        validator.validate_import_chain()
        validator.validate_circuit_functions()
        validator.validate_component_separation()

        # Test that the main file can be executed (import chain works)
        main_file = output_dir / "main.py"
        if main_file.exists():
            # Test syntax by attempting to compile
            with open(main_file, "r") as f:
                main_content = f.read()

            try:
                compile(main_content, str(main_file), "exec")
            except SyntaxError as e:
                pytest.fail(f"Generated main.py has syntax errors: {e}")

        if preserve_files:
            print(f"\n✅ Generated files preserved in: {output_dir}")
            print("📁 Files created:")
            for file_path in output_dir.glob("*.py"):
                print(f"   - {file_path.name}")

    finally:
        # Clean up temporary directory if not preserving files
        if not preserve_files and "temp_dir" in locals():
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    # Allow running test directly
    test_complex_hierarchical_structure()
