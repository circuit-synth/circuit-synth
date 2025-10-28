#!/usr/bin/env python3
"""
Automated test for 07_b_delete_component_kicad bidirectional test.

Tests deleting component in KiCad → syncing back to Python.
This is the KiCad side deletion (counterpart to 07 which tests Python side deletion).

Workflow:
1. Generate KiCad with both R1 and R2
2. Delete R2 from schematic (using direct file editing)
3. Import KiCad back to Python
4. Validate Python only has R1 (R2 removed)

Validation uses kicad-sch-api and AST parsing.
"""
import ast
import re
import shutil
import subprocess
from pathlib import Path

import pytest


def test_07_b_delete_component_kicad(request):
    """Test deleting component in KiCad → syncs to Python.

    Workflow:
    1. Generate KiCad with R1 and R2
    2. Delete R2 from KiCad schematic (direct file edit)
    3. Import KiCad back to Python
    4. Validate Python only has R1 (R2 removed from code)

    This tests KiCad → Python deletion sync.

    Level 2 Semantic Validation:
    - kicad-sch-api for schematic validation
    - AST parsing for Python code validation
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "two_resistors.py"
    output_dir = test_dir / "two_resistors"
    schematic_file = output_dir / "two_resistors.kicad_sch"

    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    # Clean any existing output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Read original Python file
    with open(python_file, "r") as f:
        original_code = f.read()

    try:
        # =====================================================================
        # STEP 1: Generate KiCad with both R1 and R2
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate KiCad with R1 and R2")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "two_resistors.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 1 failed: Initial generation\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        assert schematic_file.exists(), "Schematic not created"

        # Validate both R1 and R2 in schematic
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        assert len(components) == 2, (
            f"Step 1: Expected 2 components, found {len(components)}"
        )

        refs = {c.reference for c in components}
        assert "R1" in refs and "R2" in refs

        print(f"✅ Step 1: KiCad generated with R1 and R2")

        # =====================================================================
        # STEP 2: Delete R2 from KiCad schematic
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Delete R2 from KiCad schematic")
        print("="*70)

        # Read schematic file
        with open(schematic_file, 'r') as f:
            sch_content = f.read()

        # Find and remove R2 symbol block
        # Pattern to match the entire R2 symbol block
        r2_pattern = r'\(symbol[^)]*?"R2"[^)]*?\(instances[^)]*?\)\s*\)'

        # More comprehensive pattern that handles nested parentheses
        # Find R2 symbol block start
        import re
        r2_start = sch_content.find('(property "Reference" "R2"')

        if r2_start != -1:
            # Search backwards to find the opening (symbol
            symbol_start = sch_content.rfind('(symbol', 0, r2_start)

            # Now find the matching closing parenthesis
            # Count parentheses to find the correct closing one
            paren_count = 0
            i = symbol_start
            symbol_end = -1

            while i < len(sch_content):
                if sch_content[i] == '(':
                    paren_count += 1
                elif sch_content[i] == ')':
                    paren_count -= 1
                    if paren_count == 0:
                        symbol_end = i + 1
                        break
                i += 1

            if symbol_end != -1:
                # Remove R2 symbol block
                sch_content_modified = (
                    sch_content[:symbol_start] +
                    sch_content[symbol_end:]
                )

                # Write modified schematic
                with open(schematic_file, 'w') as f:
                    f.write(sch_content_modified)
            else:
                raise AssertionError("Could not find closing parenthesis for R2 symbol")
        else:
            raise AssertionError("Could not find R2 in schematic")

        # Verify R2 was removed
        sch_reloaded = Schematic.load(str(schematic_file))
        components_after = sch_reloaded.components

        assert len(components_after) == 1, (
            f"Step 2: Expected 1 component after deleting R2, found {len(components_after)}"
        )
        assert components_after[0].reference == "R1"

        print(f"✅ Step 2: R2 deleted from schematic, only R1 remains")

        # =====================================================================
        # STEP 3: Import KiCad back to Python
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Import KiCad → Python (should remove R2)")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "kicad-to-python", "two_resistors", "two_resistors.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 3 failed: KiCad → Python import\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # =====================================================================
        # STEP 4: Validate Python only has R1 (R2 removed)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 4: Validate Python only has R1")
        print("="*70)

        with open(python_file, "r") as f:
            imported_code = f.read()

        tree = ast.parse(imported_code)

        # Find circuit function
        circuit_functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    if isinstance(decorator, ast.Name) and decorator.id == "circuit":
                        circuit_functions.append(node)
                        break
                    elif isinstance(decorator, ast.Call):
                        if isinstance(decorator.func, ast.Name) and decorator.func.id == "circuit":
                            circuit_functions.append(node)
                            break

        assert len(circuit_functions) == 1

        circuit_function = circuit_functions[0]

        # Find Component assignments
        component_assigns = {}
        for node in ast.walk(circuit_function):
            if isinstance(node, ast.Assign):
                if isinstance(node.value, ast.Call):
                    if isinstance(node.value.func, ast.Name):
                        if node.value.func.id == "Component":
                            if node.targets and isinstance(node.targets[0], ast.Name):
                                var_name = node.targets[0].id
                                component_assigns[var_name] = node

        # Should only have R1 now (R2 deleted)
        assert len(component_assigns) == 1, (
            f"Expected 1 Component (R1 only), found {len(component_assigns)}: {list(component_assigns.keys())}"
        )

        assert "r1" in component_assigns or "R1" in component_assigns, (
            f"R1 not found. Found: {list(component_assigns.keys())}"
        )

        # R2 should not be present
        assert "r2" not in component_assigns and "R2" not in component_assigns, (
            f"R2 should be deleted but still found in Python code"
        )

        print(f"✅ Step 4: Python validated - only R1 present")
        print(f"   - Found components: {list(component_assigns.keys())}")
        print(f"   - R2 successfully removed from Python code")

    finally:
        # Restore original Python file (both R1 and R2)
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
