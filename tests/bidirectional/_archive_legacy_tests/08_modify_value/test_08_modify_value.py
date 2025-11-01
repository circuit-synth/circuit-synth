#!/usr/bin/env python3
"""
Automated test for 08_modify_value bidirectional test.

Tests modifying component attributes (value, footprint) in KiCad → syncing to Python
→ regenerating KiCad while preserving position.

NOTE: Reference changes are NOT tested here due to known limitation (issue #369).
This test focuses on value and footprint changes which work correctly.

Workflow:
1. Generate KiCad with R1 (10k, 0603) at default position
2. Edit KiCad schematic:
   - Move R1 to specific position (x=100mm, y=50mm)
   - Change value: 10k → 4.7k
   - Change footprint: 0603 → 0805
   - Keep reference as R1 (no reference change)
3. Import KiCad back to Python
4. Validate Python code has updated value and footprint
5. Regenerate KiCad from updated Python
6. Validate:
   - Position preserved (still at x=100, y=50)
   - Value is 4.7k
   - Footprint is 0805

Validation uses kicad-sch-api and AST parsing.
"""
import ast
import re
import shutil
import subprocess
from pathlib import Path

import pytest


def test_08_modify_value(request):
    """Test modifying component attributes in KiCad → syncs to Python with position preservation.

    Workflow:
    1. Generate KiCad with R1 (10k, 0603)
    2. Edit schematic: move R1, change value to 4.7k, footprint to 0805
    3. Import to Python
    4. Validate Python has new attributes
    5. Regenerate KiCad
    6. Validate position preserved and attributes match

    NOTE: Reference changes not tested (issue #369).
    This tests value/footprint changes + position preservation.

    Level 2 Semantic Validation:
    - kicad-sch-api for schematic validation
    - AST parsing for Python code validation
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "single_resistor.py"
    output_dir = test_dir / "single_resistor"
    schematic_file = output_dir / "single_resistor.kicad_sch"

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
        # STEP 1: Generate KiCad with R1 (10k, 0603)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate KiCad with R1 (10k, 0603)")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "single_resistor.py"],
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

        # Validate initial state
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        assert len(components) == 1
        r1_initial = components[0]
        assert r1_initial.reference == "R1"
        assert r1_initial.value == "10k"
        assert "0603" in r1_initial.footprint

        initial_pos = r1_initial.position
        print(f"✅ Step 1: Initial KiCad generated")
        print(f"   - Reference: {r1_initial.reference}")
        print(f"   - Value: {r1_initial.value}")
        print(f"   - Footprint: {r1_initial.footprint}")
        print(f"   - Initial position: {initial_pos}")

        # =====================================================================
        # STEP 2: Edit KiCad - move + change attributes
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Edit KiCad - move R1 and change attributes")
        print("="*70)

        # Read schematic file
        with open(schematic_file, 'r') as f:
            sch_content = f.read()

        # Find R1 symbol block
        r1_ref_pos = sch_content.find('(property "Reference" "R1"')
        assert r1_ref_pos != -1, "Could not find R1 in schematic"

        # Find symbol block start
        symbol_start = sch_content.rfind('(symbol', 0, r1_ref_pos)
        assert symbol_start != -1

        # Find matching closing parenthesis
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

        assert symbol_end != -1, "Could not find closing parenthesis for R1"

        # Extract R1 symbol block
        r1_block = sch_content[symbol_start:symbol_end]

        # Modify position to (100, 50)
        # Pattern: (symbol (lib_id ...) (at X Y ANGLE) ...)
        r1_block_modified = re.sub(
            r'\(at\s+[\d.]+\s+[\d.]+\s+[\d.]+\)',
            '(at 100 50 0)',
            r1_block,
            count=1
        )

        # Change value: 10k → 4.7k
        r1_block_modified = re.sub(
            r'\(property "Value" "10k"',
            '(property "Value" "4.7k"',
            r1_block_modified
        )

        # Change footprint: 0603 → 0805
        r1_block_modified = re.sub(
            r'R_0603_1608Metric',
            'R_0805_2012Metric',
            r1_block_modified
        )

        # Replace in schematic
        sch_content_modified = (
            sch_content[:symbol_start] +
            r1_block_modified +
            sch_content[symbol_end:]
        )

        # Write modified schematic
        with open(schematic_file, 'w') as f:
            f.write(sch_content_modified)

        # Verify modifications
        sch_modified = Schematic.load(str(schematic_file))
        r1_modified = sch_modified.components[0]
        modified_pos = r1_modified.position

        assert r1_modified.reference == "R1", "Reference should not change"
        assert r1_modified.value == "4.7k", "Value should be 4.7k"
        assert "0805" in r1_modified.footprint, "Footprint should be 0805"
        assert modified_pos.x == 100.0 and modified_pos.y == 50.0, f"Position should be (100, 50), got {modified_pos}"

        print(f"✅ Step 2: KiCad schematic modified")
        print(f"   - Position moved to: {modified_pos}")
        print(f"   - Value changed to: {r1_modified.value}")
        print(f"   - Footprint changed to: {r1_modified.footprint}")

        # =====================================================================
        # STEP 3: Import KiCad → Python
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Import KiCad → Python (sync attributes)")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "kicad-to-python", "single_resistor", "single_resistor.py"],
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
        # STEP 4: Validate Python has updated attributes
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 4: Validate Python code has updated attributes")
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

        # Find Component assignment
        component_assigns = {}
        for node in ast.walk(circuit_function):
            if isinstance(node, ast.Assign):
                if isinstance(node.value, ast.Call):
                    if isinstance(node.value.func, ast.Name):
                        if node.value.func.id == "Component":
                            if node.targets and isinstance(node.targets[0], ast.Name):
                                var_name = node.targets[0].id
                                component_assigns[var_name] = node.value

        assert len(component_assigns) == 1, f"Expected 1 Component, found {len(component_assigns)}"

        # Get the Component call node
        component_call = list(component_assigns.values())[0]

        # Extract keyword arguments
        kwargs = {kw.arg: kw.value for kw in component_call.keywords}

        # Validate value changed to 4.7k
        assert 'value' in kwargs
        value_node = kwargs['value']
        assert isinstance(value_node, ast.Constant)
        assert value_node.value == "4.7k", f"Expected value='4.7k', got '{value_node.value}'"

        # Validate footprint changed to 0805
        assert 'footprint' in kwargs
        footprint_node = kwargs['footprint']
        assert isinstance(footprint_node, ast.Constant)
        assert "0805" in footprint_node.value, f"Expected footprint with 0805, got '{footprint_node.value}'"

        print(f"✅ Step 4: Python code validated")
        print(f"   - Value: {value_node.value}")
        print(f"   - Footprint: {footprint_node.value}")

        # =====================================================================
        # STEP 5: Regenerate KiCad from updated Python
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 5: Regenerate KiCad from updated Python")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "single_resistor.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 5 failed: Regeneration\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # =====================================================================
        # STEP 6: Validate position preserved and attributes match
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 6: Validate position preserved and attributes match")
        print("="*70)

        sch_final = Schematic.load(str(schematic_file))
        components_final = sch_final.components

        assert len(components_final) == 1
        r1_final = components_final[0]
        final_pos = r1_final.position

        # Validate position preserved
        assert final_pos.x == 100.0 and final_pos.y == 50.0, (
            f"Position not preserved! Expected (100, 50), got {final_pos}"
        )

        # Validate attributes match
        assert r1_final.reference == "R1"
        assert r1_final.value == "4.7k"
        assert "0805" in r1_final.footprint

        print(f"✅ Step 6: Full round-trip successful!")
        print(f"   - Position preserved: {final_pos} ✓")
        print(f"   - Reference: {r1_final.reference} ✓")
        print(f"   - Value: {r1_final.value} ✓")
        print(f"   - Footprint: {r1_final.footprint} ✓")
        print(f"\n🎉 Test passed: Attributes synced and position preserved!")

    finally:
        # Restore original Python file
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
