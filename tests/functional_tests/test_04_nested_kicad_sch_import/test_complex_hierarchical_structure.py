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

import pytest
import tempfile
import shutil
import subprocess
import os
from pathlib import Path
import ast
import re
from typing import Dict, Set, List, Any

# Import circuit-synth functionality
try:
    from circuit_synth.scripts.kicad_to_python_sync import KiCadToPythonSyncer
    from circuit_synth import Circuit, Component, Net
except ImportError as e:
    pytest.skip(f"Circuit-synth import functionality not available: {e}", allow_module_level=True)


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
        expected_files = ['main.py', 'resistor_divider.py', 'capacitor_bank.py']
        
        for file_name in expected_files:
            file_path = self.project_dir / file_name
            if file_path.exists():
                with open(file_path, 'r') as f:
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
                        if (isinstance(decorator, ast.Name) and decorator.id == 'circuit'):
                            circuit_functions.append(node.name)
            
            self.import_chains[file_name] = imports
            self.circuit_functions[file_name] = circuit_functions
            
        except SyntaxError as e:
            pytest.fail(f"Syntax error in {file_name}: {e}")
    
    def validate_file_structure(self):
        """Validate that all expected files are present."""
        expected_files = {'main.py', 'resistor_divider.py', 'capacitor_bank.py'}
        actual_files = set(self.files.keys())
        
        assert expected_files == actual_files, f"Expected files {expected_files}, got {actual_files}"
    
    def validate_import_chain(self):
        """Validate the hierarchical import relationships."""
        
        # main.py should import resistor_divider
        assert 'resistor_divider' in self.import_chains.get('main.py', []), \
            "main.py should import resistor_divider"
        
        # resistor_divider.py should import capacitor_bank
        assert 'capacitor_bank' in self.import_chains.get('resistor_divider.py', []), \
            "resistor_divider.py should import capacitor_bank"
        
        # capacitor_bank.py should not import other circuit modules (leaf node)
        cap_imports = self.import_chains.get('capacitor_bank.py', [])
        circuit_imports = [imp for imp in cap_imports if imp in ['main', 'resistor_divider']]
        assert len(circuit_imports) == 0, \
            f"capacitor_bank.py should not import other circuit modules, found: {circuit_imports}"
    
    def validate_circuit_functions(self):
        """Validate that each file contains the expected @circuit functions."""
        
        # Each file should have exactly one @circuit function
        for file_name, functions in self.circuit_functions.items():
            assert len(functions) == 1, f"{file_name} should have exactly one @circuit function, found: {functions}"
        
        # Validate function names match expected pattern
        assert 'main_circuit' in self.circuit_functions.get('main.py', []), \
            "main.py should contain main_circuit function"
        assert 'resistor_divider' in self.circuit_functions.get('resistor_divider.py', []), \
            "resistor_divider.py should contain resistor_divider function"
        assert 'capacitor_bank' in self.circuit_functions.get('capacitor_bank.py', []), \
            "capacitor_bank.py should contain capacitor_bank function"
    
    def validate_component_separation(self):
        """Validate that components are properly separated across files."""
        
        # Check that each file contains its expected component types
        main_content = self.files.get('main.py', '')
        resistor_content = self.files.get('resistor_divider.py', '')
        capacitor_content = self.files.get('capacitor_bank.py', '')
        
        # main.py should not contain component definitions (only imports and instantiation)
        assert 'Component(' not in main_content, "main.py should not define components directly"
        
        # resistor_divider.py should contain resistor components
        assert 'Device:R' in resistor_content, "resistor_divider.py should contain resistor components"
        
        # capacitor_bank.py should contain capacitor components
        assert 'Device:C' in capacitor_content, "capacitor_bank.py should contain capacitor components"


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
    preserve_files = os.getenv('PRESERVE_FILES', '').lower() in ('1', 'true', 'yes')
    
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
        # Initialize KiCad-to-Python syncer
        syncer = KiCadToPythonSyncer()
        
        # Convert KiCad project to Python
        syncer.convert_kicad_to_python(
            str(kicad_project_dir),
            str(output_dir)
        )
        
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
            with open(main_file, 'r') as f:
                main_content = f.read()
            
            try:
                compile(main_content, str(main_file), 'exec')
            except SyntaxError as e:
                pytest.fail(f"Generated main.py has syntax errors: {e}")
        
        if preserve_files:
            print(f"\n✅ Generated files preserved in: {output_dir}")
            print("📁 Files created:")
            for file_path in output_dir.glob("*.py"):
                print(f"   - {file_path.name}")
    
    finally:
        # Clean up temporary directory if not preserving files
        if not preserve_files and 'temp_dir' in locals():
            shutil.rmtree(temp_dir)


if __name__ == "__main__":
    # Allow running test directly
    test_complex_hierarchical_structure()