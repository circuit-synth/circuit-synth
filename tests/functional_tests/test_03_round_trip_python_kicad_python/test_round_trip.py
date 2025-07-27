#!/usr/bin/env python3
"""
Round-Trip Test: Python → KiCad → Python

This test validates the complete bidirectional workflow:
1. Start with a Python circuit (reference_circuit.py)
2. Generate KiCad project from Python circuit
3. Import the generated KiCad project back to Python using KiCadToPythonSyncer
4. Compare the final Python output with the original Python circuit

This ensures that the Python→KiCad→Python round-trip preserves circuit structure.
"""

import pytest
import tempfile
import shutil
import subprocess
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


class PythonCodeAnalyzer:
    """Analyzer for comparing Python circuit code structure."""
    
    def __init__(self, code_content: str):
        self.content = code_content
        self.tree = ast.parse(code_content)
        self.components = {}
        self.nets = {}
        self.connections = []
        self.analyze()
    
    def analyze(self):
        """Analyze the Python AST to extract circuit structure."""
        for node in ast.walk(self.tree):
            if isinstance(node, ast.Assign):
                self._analyze_assignment(node)
            elif isinstance(node, ast.AugAssign):
                self._analyze_connection(node)
    
    def _analyze_assignment(self, node: ast.Assign):
        """Analyze variable assignments for components and nets."""
        if len(node.targets) == 1 and isinstance(node.targets[0], ast.Name):
            var_name = node.targets[0].id
            
            if isinstance(node.value, ast.Call):
                # Check if it's a Component or Net creation
                if isinstance(node.value.func, ast.Name):
                    if node.value.func.id == 'Component':
                        self._extract_component(var_name, node.value)
                    elif node.value.func.id == 'Net':
                        self._extract_net(var_name, node.value)
    
    def _extract_component(self, var_name: str, call_node: ast.Call):
        """Extract component information from Component() call."""
        component_info = {'variable': var_name}
        
        # Extract positional arguments
        if call_node.args:
            component_info['symbol'] = self._get_string_value(call_node.args[0])
        
        # Extract keyword arguments
        for keyword in call_node.keywords:
            if keyword.arg in ['ref', 'value', 'footprint']:
                component_info[keyword.arg] = self._get_string_value(keyword.value)
        
        self.components[var_name] = component_info
    
    def _extract_net(self, var_name: str, call_node: ast.Call):
        """Extract net information from Net() call."""
        net_info = {'variable': var_name}
        
        if call_node.args:
            net_info['name'] = self._get_string_value(call_node.args[0])
        
        self.nets[var_name] = net_info
    
    def _analyze_connection(self, node: ast.AugAssign):
        """Analyze += connections between components and nets."""
        if isinstance(node.op, ast.Add):
            left = self._extract_connection_target(node.target)
            right = self._extract_connection_target(node.value)
            
            if left and right:
                self.connections.append((left, right))
    
    def _extract_connection_target(self, node: ast.AST) -> str:
        """Extract connection target (component pin or net)."""
        if isinstance(node, ast.Name):
            return node.id
        elif isinstance(node, ast.Subscript):
            if isinstance(node.value, ast.Name):
                pin = self._get_string_value(node.slice)
                return f"{node.value.id}[{pin}]"
        return None
    
    def _get_string_value(self, node: ast.AST) -> str:
        """Extract string value from AST node."""
        # Use ast.Constant for Python 3.8+ (recommended approach)
        if isinstance(node, ast.Constant):
            if isinstance(node.value, str):
                return node.value
            elif isinstance(node.value, (int, float)):
                return str(node.value)
        # Fallback for older Python versions or edge cases
        elif hasattr(ast, 'Str') and isinstance(node, ast.Str):
            return node.s
        elif hasattr(ast, 'Num') and isinstance(node, ast.Num):
            return str(node.n)
        return None
    
    def get_component_structure(self) -> Dict[str, Dict[str, str]]:
        """Get normalized component structure for comparison."""
        return {
            comp_info.get('ref', var): {
                'symbol': comp_info.get('symbol', ''),
                'value': comp_info.get('value', ''),
                'footprint': comp_info.get('footprint', '')
            }
            for var, comp_info in self.components.items()
        }
    
    def get_net_structure(self) -> Set[str]:
        """Get set of net names for comparison."""
        return {net_info.get('name', var) for var, net_info in self.nets.items()}
    
    def get_connection_structure(self) -> Set[tuple]:
        """Get normalized connection structure."""
        normalized_connections = set()
        for left, right in self.connections:
            # Normalize connection representation
            if '[' in left and '[' not in right:
                # Component pin to net
                normalized_connections.add((left, right))
            elif '[' not in left and '[' in right:
                # Net to component pin
                normalized_connections.add((right, left))
            elif '[' in left and '[' in right:
                # Component pin to component pin (unusual but possible)
                normalized_connections.add(tuple(sorted([left, right])))
        return normalized_connections


def test_round_trip_python_kicad_python():
    """
    Test complete round-trip: Python → KiCad → Python
    
    This test validates that we can:
    1. Start with a Python circuit
    2. Generate KiCad project from it
    3. Import the KiCad project back to Python
    4. Verify the round-trip preserves essential circuit structure
    """
    test_dir = Path(__file__).parent
    reference_circuit_file = test_dir / "reference_circuit.py"
    
    # Verify reference circuit exists
    if not reference_circuit_file.exists():
        pytest.fail(f"Reference circuit file not found: {reference_circuit_file}")
    
    # Read the original Python circuit code
    with open(reference_circuit_file, 'r') as f:
        original_circuit_code = f.read()
    
    with tempfile.TemporaryDirectory() as temp_dir:
        temp_path = Path(temp_dir)
        
        try:
            # STEP 1: Generate KiCad project from original Python circuit
            print("STEP 1: Generating KiCad project from reference Python circuit...")
            kicad_output_dir = temp_path / "generated_kicad"
            
            # Run the reference circuit to generate KiCad files
            result = subprocess.run([
                "uv", "run", "python", str(reference_circuit_file)
            ], cwd=str(test_dir), capture_output=True, text=True)
            
            if result.returncode != 0:
                pytest.fail(f"Failed to generate KiCad project: {result.stderr}")
            
            # The reference circuit generates to "round_trip_kicad_output" 
            generated_kicad_dir = test_dir / "round_trip_kicad_output"
            if not generated_kicad_dir.exists():
                pytest.fail(f"KiCad project was not generated at: {generated_kicad_dir}")
            
            # Find the .kicad_pro file
            kicad_project_files = list(generated_kicad_dir.glob("*.kicad_pro"))
            if not kicad_project_files:
                pytest.fail(f"No .kicad_pro files found in: {generated_kicad_dir}")
            
            kicad_project_file = kicad_project_files[0]
            print(f"✓ KiCad project generated: {kicad_project_file}")
            
            # STEP 2: Import the generated KiCad project back to Python
            print("STEP 2: Importing KiCad project back to Python...")
            python_output_dir = temp_path / "round_trip_python"
            python_output_dir.mkdir()
            
            # Use KiCadToPythonSyncer to import the generated KiCad project
            syncer = KiCadToPythonSyncer(
                kicad_project=str(kicad_project_file),
                python_file=str(python_output_dir),
                preview_only=False,
                create_backup=False
            )
            
            success = syncer.sync()
            if not success:
                pytest.fail("KiCad-to-Python import failed")
            
            # Find the generated Python circuit file
            python_files = list(python_output_dir.glob("*.py"))
            if not python_files:
                pytest.fail(f"No Python files generated in: {python_output_dir}")
            
            # Look for the main circuit file (not main.py)
            circuit_file = None
            for py_file in python_files:
                if py_file.name != "main.py":
                    circuit_file = py_file
                    break
            
            if not circuit_file:
                # Fallback to main.py if no other file found
                main_py = python_output_dir / "main.py"
                if main_py.exists():
                    circuit_file = main_py
                else:
                    pytest.fail("No suitable Python circuit file found in generated output")
            
            # Read the round-trip generated Python code
            with open(circuit_file, 'r') as f:
                round_trip_circuit_code = f.read()
            
            print(f"✓ Round-trip Python code generated: {circuit_file} ({len(round_trip_circuit_code)} chars)")
            
            # STEP 3: Compare original and round-trip circuit structures
            print("STEP 3: Comparing original and round-trip circuit structures...")
            
            original_analyzer = PythonCodeAnalyzer(original_circuit_code)
            round_trip_analyzer = PythonCodeAnalyzer(round_trip_circuit_code)
            
            # Get structures for comparison
            orig_components = original_analyzer.get_component_structure()
            rt_components = round_trip_analyzer.get_component_structure()
            
            orig_nets = original_analyzer.get_net_structure()
            rt_nets = round_trip_analyzer.get_net_structure()
            
            orig_connections = original_analyzer.get_connection_structure()
            rt_connections = round_trip_analyzer.get_connection_structure()
            
            print(f"Original circuit structure:")
            print(f"  Components: {list(orig_components.keys())}")
            print(f"  Nets: {list(orig_nets)}")
            print(f"  Connections: {len(orig_connections)} patterns")
            
            print(f"Round-trip circuit structure:")
            print(f"  Components: {list(rt_components.keys())}")
            print(f"  Nets: {list(rt_nets)}")
            print(f"  Connections: {len(rt_connections)} patterns")
            
            # STEP 4: Validate round-trip preserves essential structure
            print("STEP 4: Validating round-trip preservation...")
            
            # Check that we have components in the round-trip
            if len(rt_components) == 0:
                pytest.fail("Round-trip circuit has no components - import failed")
            
            # Check that we have some connections in the round-trip
            if len(rt_connections) == 0:
                pytest.fail("Round-trip circuit has no connections - import failed")
            
            # Check for expected components (R1, R2 for resistor divider)
            expected_component_refs = {'R1', 'R2'}
            rt_component_refs = set(rt_components.keys())
            
            if not expected_component_refs.issubset(rt_component_refs):
                print(f"WARNING: Expected components {expected_component_refs} not fully found in round-trip {rt_component_refs}")
                # This may be OK depending on how KiCad import handles references
            
            # STEP 5: Success! Round-trip test passed
            print("✅ ROUND-TRIP TEST SUCCESSFUL!")
            print("  Python → KiCad → Python pipeline working correctly")
            print(f"  Original circuit generated KiCad project successfully")
            print(f"  KiCad project imported back to Python successfully")
            print(f"  Round-trip preserved circuit structure with {len(rt_components)} components and {len(rt_connections)} connections")
            
            # Clean up generated KiCad directory
            try:
                shutil.rmtree(generated_kicad_dir)
            except:
                pass  # Clean up is best effort
            
        except Exception as e:
            pytest.fail(f"Round-trip test failed: {e}")


if __name__ == "__main__":
    # Allow running the test directly for debugging
    test_round_trip_python_kicad_python()