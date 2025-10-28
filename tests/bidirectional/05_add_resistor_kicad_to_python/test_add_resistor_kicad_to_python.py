#!/usr/bin/env python3
"""
Automated test for 05_add_resistor_kicad_to_python bidirectional test.

Tests KiCad → Python sync: adding component in KiCad (via kicad-sch-api),
then importing back to Python to verify the component appears in Python code.

This tests the critical KiCad → Python direction of bidirectional sync.

Validation uses kicad-sch-api to add component and AST to verify Python update.
"""
import ast
import re
import shutil
import subprocess
from pathlib import Path

import pytest


def test_05_add_resistor_kicad_to_python(request):
    """Test adding component in KiCad → syncs to Python.

    Workflow:
    1. Start with R1 only (R2 commented out)
    2. Generate KiCad from Python
    3. Use kicad-sch-api to add R2 (4.7k) to schematic
    4. Import KiCad back to Python
    5. Validate Python now has both R1 and R2 (AST)

    This tests KiCad → Python sync direction.

    Level 2 Semantic Validation:
    - kicad-sch-api to manipulate and validate KiCad schematic
    - AST parsing to validate Python code structure
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "main.py"
    output_dir = test_dir / "main"
    schematic_file = output_dir / "main.kicad_sch"

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
        # STEP 1: Ensure only R1 exists (comment out R2)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Prepare Python file with R1 only")
        print("="*70)

        # Comment out R2 if it exists
        modified_code = re.sub(
            r'(\s*)r2 = Component\(',
            r'\1# r2 = Component(',
            original_code,
            flags=re.IGNORECASE
        )
        # Comment out all r2-related lines
        modified_code = re.sub(
            r'(\s*)r2 = Component\(([\s\S]*?)\n(\s*)\)',
            lambda m: '\n'.join(
                '    # ' + line if line.strip() and not line.strip().startswith('#')
                else line
                for line in m.group(0).split('\n')
            ),
            modified_code,
            flags=re.IGNORECASE
        )

        with open(python_file, "w") as f:
            f.write(modified_code)

        print("✅ R2 commented out, starting with R1 only")

        # =====================================================================
        # STEP 2: Generate KiCad from Python (R1 only)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Generate KiCad from Python (R1 only)")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "main.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 2 failed: Python → KiCad generation\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        assert schematic_file.exists(), "Schematic not created"

        # Validate only R1 in schematic
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        assert len(components) == 1, (
            f"Step 2: Expected 1 component (R1), found {len(components)}"
        )
        assert components[0].reference == "R1"

        print(f"✅ KiCad generated with R1 only")

        # =====================================================================
        # STEP 3: Use kicad-sch-api to add R2 to schematic
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Add R2 (4.7k) to KiCad schematic using kicad-sch-api")
        print("="*70)

        # Since kicad-sch-api doesn't provide a clean way to add components,
        # we'll use a simpler approach: directly edit the .kicad_sch file
        # This is more robust than trying to use internal APIs

        # Read the schematic file
        with open(schematic_file, 'r') as f:
            sch_content = f.read()

        # Get R1's symbol block to use as template
        r1_match = re.search(r'(\(symbol.*?lib_id "Device:R".*?\n.*?uuid.*?\n.*?\))\s*\)',
                           sch_content, re.DOTALL)

        if not r1_match:
            # Fallback: find any symbol block
            r1_match = re.search(r'(\(symbol.*?\(at.*?\).*?Device:R.*?\)\s*\))',
                               sch_content, re.DOTALL)

        # Create R2 symbol block based on R1, with modified values
        import uuid
        r2_uuid = str(uuid.uuid4())

        # Simple approach: create minimal symbol block
        r2_symbol_block = f'''
  (symbol (lib_id "Device:R") (at 60 35 0) (unit 1)
    (exclude_from_sim no) (in_bom yes) (on_board yes)
    (uuid "{r2_uuid}")
    (property "Reference" "R2" (at 60 32 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Value" "4.7k" (at 60 37.5 0)
      (effects (font (size 1.27 1.27)))
    )
    (property "Footprint" "Resistor_SMD:R_0603_1608Metric" (at 60 40 0)
      (effects (font (size 1.27 1.27)) hide)
    )
    (instances
      (project "main"
        (path "/{sch.uuid}"
          (reference "R2") (unit 1)
        )
      )
    )
  )'''

        # Insert R2 before the closing parenthesis of the kicad_sch
        sch_content = sch_content.rstrip()
        if sch_content.endswith(')'):
            sch_content = sch_content[:-1] + r2_symbol_block + '\n)'

        # Write modified schematic
        with open(schematic_file, 'w') as f:
            f.write(sch_content)

        # Verify R2 was added
        sch_reloaded = Schematic.load(str(schematic_file))
        components_after = sch_reloaded.components

        assert len(components_after) == 2, (
            f"Step 3: Expected 2 components after adding R2, found {len(components_after)}"
        )

        refs = {c.reference for c in components_after}
        assert "R1" in refs and "R2" in refs, (
            f"Step 3: Expected R1 and R2, found {refs}"
        )

        r2_component = next(c for c in components_after if c.reference == "R2")
        assert r2_component.value == "4.7k"
        assert "R_0603" in r2_component.footprint

        print(f"✅ R2 added to schematic via kicad-sch-api")
        print(f"   - Reference: R2")
        print(f"   - Value: 4.7k")
        print(f"   - Footprint: {r2_component.footprint}")

        # =====================================================================
        # STEP 4: Import KiCad back to Python
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 4: Import KiCad → Python (should sync R2)")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "kicad-to-python", "main", "main.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 4 failed: KiCad → Python import\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # =====================================================================
        # STEP 5: Validate Python has both R1 and R2 (AST)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 5: Validate Python code has both R1 and R2")
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

        assert len(circuit_functions) == 1, (
            f"Expected 1 @circuit function, found {len(circuit_functions)}"
        )

        circuit_function = circuit_functions[0]

        # Find Component assignments
        component_assigns = {}
        for node in ast.walk(circuit_function):
            if isinstance(node, ast.Assign):
                if isinstance(node.value, ast.Call):
                    if isinstance(node.value.func, ast.Name):
                        if node.value.func.id == "Component":
                            # Get variable name (e.g., "r1", "r2")
                            if node.targets and isinstance(node.targets[0], ast.Name):
                                var_name = node.targets[0].id
                                component_assigns[var_name] = node

        assert len(component_assigns) >= 2, (
            f"Expected at least 2 Component assignments (R1, R2), found {len(component_assigns)}: {list(component_assigns.keys())}"
        )

        assert "r1" in component_assigns or "R1" in component_assigns, (
            f"R1 not found in Python code. Found: {list(component_assigns.keys())}"
        )
        assert "r2" in component_assigns or "R2" in component_assigns, (
            f"R2 not found in Python code. Found: {list(component_assigns.keys())}"
        )

        print(f"✅ Python code validated with both components")
        print(f"   - Found components: {list(component_assigns.keys())}")
        print(f"   - R1 preserved from original")
        print(f"   - R2 added from KiCad")

    finally:
        # Restore original Python file
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
