#!/usr/bin/env python3
"""
Automated test for 02_kicad_to_python bidirectional test.

Tests that a blank KiCad schematic converts to valid Python with no components.

Validation Level 2 (Semantic): Uses AST parsing to validate structure
independent of formatting/spacing. This allows code formatting to change
while still catching semantic regressions.
"""
import ast
import shutil
import subprocess
from pathlib import Path

import pytest


def test_02_kicad_to_python(request):
    """Test that blank KiCad schematic converts to valid Python.

    This test validates:
    1. kicad-to-python tool executes successfully
    2. Python file is created with valid syntax
    3. Generated code has @circuit decorator
    4. Circuit function exists (named 'main' by default)
    5. Circuit function body is empty (no components for blank circuit)
    6. Has __main__ block for execution

    Level 2 Semantic Validation:
    - Uses AST parsing to validate structure
    - Independent of formatting/spacing
    - Catches semantic regressions without brittleness
    """

    # Setup paths
    test_dir = Path(__file__).parent
    kicad_input = test_dir / "blank_kicad_ref"
    python_output = test_dir / "imported_blank.py"

    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    # Clean any existing output
    if python_output.exists():
        python_output.unlink()

    try:
        # Run kicad-to-python conversion
        result = subprocess.run(
            ["uv", "run", "kicad-to-python", str(kicad_input), str(python_output)],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        # Assert conversion succeeded (warnings are OK for blank circuit)
        assert result.returncode == 0, (
            f"kicad-to-python failed with return code {result.returncode}\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # Assert Python file was created
        assert python_output.exists(), "Python file not created"

        # Read generated Python code
        with open(python_output, "r") as f:
            code = f.read()

        # Level 2: Semantic validation via AST
        tree = ast.parse(code)

        # Find all circuit decorators and functions
        circuit_functions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                # Check if function has @circuit decorator
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name) and decorator.id == "circuit":
                        circuit_functions.append(node)
                        break

        # Assert exactly ONE @circuit decorator exists
        assert len(circuit_functions) == 1, (
            f"Expected exactly 1 @circuit decorator, found {len(circuit_functions)}"
        )

        # Get the single circuit function
        circuit_function = circuit_functions[0]

        # Assert circuit function is empty (blank circuit)
        # Function body should only contain docstring or pass statements
        # Filter out docstrings (Expr nodes with Constant values)
        non_docstring_statements = [
            stmt for stmt in circuit_function.body
            if not (isinstance(stmt, ast.Expr) and
                   isinstance(stmt.value, ast.Constant))
        ]

        # After filtering docstrings, should have no statements or only 'pass'
        for stmt in non_docstring_statements:
            assert isinstance(stmt, ast.Pass), (
                f"Expected empty circuit function, found statement: {ast.dump(stmt)}"
            )

        # Assert __main__ block exists (for execution)
        has_main_block = False
        for node in ast.walk(tree):
            if isinstance(node, ast.If):
                # Check if it's 'if __name__ == "__main__":'
                if isinstance(node.test, ast.Compare):
                    if (isinstance(node.test.left, ast.Name) and
                        node.test.left.id == "__name__"):
                        has_main_block = True
                        break

        assert has_main_block, (
            "Generated code does not have __main__ execution block"
        )

        print(f"✅ Level 2 validation passed:")
        print(f"   - @circuit decorator: found")
        print(f"   - Circuit function: {circuit_function.name}()")
        print(f"   - Function body: empty (blank circuit)")
        print(f"   - __main__ block: found")

    finally:
        # Cleanup
        if cleanup and python_output.exists():
            python_output.unlink()
