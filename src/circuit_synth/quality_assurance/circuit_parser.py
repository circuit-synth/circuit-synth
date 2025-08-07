#!/usr/bin/env python3
"""
Circuit Parser for FMEA Analysis
Parses circuit-synth Python files to extract components and connections
"""

import ast
import json
import re
from pathlib import Path
from typing import Any, Dict, List, Optional


class CircuitSynthParser:
    """Parser for circuit-synth Python files"""

    def __init__(self):
        self.components = {}
        self.nets = {}
        self.subcircuits = {}

    def parse_python_circuit(self, file_path: str) -> Dict[str, Any]:
        """
        Parse a circuit-synth Python file to extract components and nets

        Args:
            file_path: Path to the Python circuit file

        Returns:
            Dictionary with components, nets, and metadata
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Circuit file not found: {file_path}")

        with open(file_path, "r") as f:
            source_code = f.read()

        # Parse the AST
        try:
            tree = ast.parse(source_code)
        except SyntaxError as e:
            raise ValueError(f"Failed to parse Python file: {e}")

        # Extract components and nets
        self._extract_from_ast(tree)

        # Extract docstrings and comments
        circuit_description = self._extract_description(tree)

        return {
            "name": file_path.stem,
            "description": circuit_description,
            "components": self.components,
            "nets": self.nets,
            "subcircuits": self.subcircuits,
            "source_file": str(file_path),
        }

    def _extract_from_ast(self, tree: ast.AST):
        """Extract components and nets from AST"""

        class ComponentVisitor(ast.NodeVisitor):
            def __init__(self, parser):
                self.parser = parser
                self.current_function = None

            def visit_FunctionDef(self, node):
                """Track function context"""
                self.current_function = node.name

                # Check if it's a circuit function
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name) and decorator.id == "circuit":
                        self.parser.subcircuits[node.name] = {
                            "docstring": ast.get_docstring(node),
                            "components": [],
                            "nets": [],
                        }
                    elif isinstance(decorator, ast.Call):
                        if (
                            isinstance(decorator.func, ast.Name)
                            and decorator.func.id == "circuit"
                        ):
                            self.parser.subcircuits[node.name] = {
                                "docstring": ast.get_docstring(node),
                                "components": [],
                                "nets": [],
                            }

                self.generic_visit(node)
                self.current_function = None

            def visit_Call(self, node):
                """Extract Component and Net calls"""

                # Check for Component() calls
                if isinstance(node.func, ast.Name) and node.func.id == "Component":
                    component_info = self._extract_component_info(node)
                    if component_info:
                        ref = component_info.get(
                            "ref", f"U{len(self.parser.components)+1}"
                        )
                        self.parser.components[ref] = component_info

                        # Add to current subcircuit if in a function
                        if (
                            self.current_function
                            and self.current_function in self.parser.subcircuits
                        ):
                            self.parser.subcircuits[self.current_function][
                                "components"
                            ].append(ref)

                # Check for Net() calls
                elif isinstance(node.func, ast.Name) and node.func.id == "Net":
                    net_name = self._extract_net_name(node)
                    if net_name:
                        self.parser.nets[net_name] = []

                        # Add to current subcircuit if in a function
                        if (
                            self.current_function
                            and self.current_function in self.parser.subcircuits
                        ):
                            self.parser.subcircuits[self.current_function][
                                "nets"
                            ].append(net_name)

                self.generic_visit(node)

            def _extract_component_info(self, node: ast.Call) -> Optional[Dict]:
                """Extract component parameters from Component() call"""
                info = {}

                # Extract keyword arguments
                for keyword in node.keywords:
                    if keyword.arg in ["symbol", "ref", "value", "footprint"]:
                        if isinstance(keyword.value, ast.Constant):
                            info[keyword.arg] = keyword.value.value
                        elif isinstance(keyword.value, ast.Str):
                            info[keyword.arg] = keyword.value.s

                return info if info else None

            def _extract_net_name(self, node: ast.Call) -> Optional[str]:
                """Extract net name from Net() call"""
                if node.args and len(node.args) > 0:
                    if isinstance(node.args[0], ast.Constant):
                        return node.args[0].value
                    elif isinstance(node.args[0], ast.Str):
                        return node.args[0].s
                return None

        visitor = ComponentVisitor(self)
        visitor.visit(tree)

    def _extract_description(self, tree: ast.AST) -> str:
        """Extract module-level docstring as circuit description"""
        docstring = ast.get_docstring(tree)
        return docstring if docstring else "No description available"

    def parse_circuit_directory(self, directory: str) -> List[Dict[str, Any]]:
        """
        Parse all Python circuit files in a directory

        Args:
            directory: Path to directory containing circuit files

        Returns:
            List of parsed circuit data
        """
        directory = Path(directory)

        if not directory.is_dir():
            raise ValueError(f"Not a directory: {directory}")

        circuits = []

        # Find all Python files
        for py_file in directory.glob("*.py"):
            # Skip test files and __init__.py
            if py_file.name.startswith("test_") or py_file.name == "__init__.py":
                continue

            try:
                circuit_data = self.parse_python_circuit(str(py_file))
                circuits.append(circuit_data)
                print(f"✓ Parsed: {py_file.name}")
            except Exception as e:
                print(f"✗ Failed to parse {py_file.name}: {e}")

        return circuits

    def merge_circuit_data(self, circuits: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge multiple circuit files into a single circuit representation

        Args:
            circuits: List of parsed circuit data

        Returns:
            Merged circuit data
        """
        merged = {
            "name": "Merged Circuit",
            "description": "Combined circuit from multiple files",
            "components": {},
            "nets": {},
            "subcircuits": {},
            "source_files": [],
        }

        for circuit in circuits:
            # Merge components
            merged["components"].update(circuit.get("components", {}))

            # Merge nets
            for net_name, connections in circuit.get("nets", {}).items():
                if net_name not in merged["nets"]:
                    merged["nets"][net_name] = []
                merged["nets"][net_name].extend(connections)

            # Merge subcircuits
            merged["subcircuits"].update(circuit.get("subcircuits", {}))

            # Track source files
            merged["source_files"].append(circuit.get("source_file", ""))

        return merged


def extract_components_from_python(file_path: str) -> Dict[str, Any]:
    """
    High-level function to extract components from a Python circuit file

    Args:
        file_path: Path to Python circuit file or directory

    Returns:
        Dictionary with components and circuit metadata
    """
    parser = CircuitSynthParser()
    path = Path(file_path)

    if path.is_file():
        return parser.parse_python_circuit(str(path))
    elif path.is_dir():
        circuits = parser.parse_circuit_directory(str(path))
        if circuits:
            return parser.merge_circuit_data(circuits)
        else:
            return {
                "name": path.name,
                "description": "No circuit files found",
                "components": {},
                "nets": {},
                "subcircuits": {},
            }
    else:
        raise ValueError(f"Invalid path: {file_path}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python circuit_parser.py <circuit_file.py>")
        sys.exit(1)

    circuit_file = sys.argv[1]

    try:
        data = extract_components_from_python(circuit_file)

        print(f"\nCircuit: {data['name']}")
        print(f"Description: {data['description'][:100]}...")
        print(f"\nComponents found: {len(data['components'])}")

        for ref, comp in data["components"].items():
            print(f"  {ref}: {comp.get('symbol', 'Unknown')}")

        print(f"\nNets found: {len(data['nets'])}")
        for net in list(data["nets"].keys())[:10]:
            print(f"  {net}")

        if data["subcircuits"]:
            print(f"\nSubcircuits found: {len(data['subcircuits'])}")
            for name in data["subcircuits"]:
                print(f"  {name}")

    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
