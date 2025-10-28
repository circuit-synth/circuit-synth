#!/usr/bin/env python3
"""
Automated test for 04_roundtrip bidirectional test.

Tests complete round-trip cycle: Python → KiCad → Python → KiCad
Validates that component properties are preserved through the full cycle.

This is a critical test for bidirectional fidelity: users should be able to
move between Python and KiCad repeatedly without data loss.

Validation uses both AST (Level 2) and kicad-sch-api semantic validation.
"""
import ast
import shutil
import subprocess
from pathlib import Path

import pytest


def test_04_roundtrip_cycle(request):
    """Test complete round-trip: Python → KiCad → Python → KiCad.

    Workflow:
    1. Generate KiCad from Python (first generation)
    2. Validate KiCad has R1 with correct properties (kicad-sch-api)
    3. Import KiCad back to Python (overwrites single_resistor.py)
    4. Validate Python has R1 with correct properties (AST)
    5. Generate KiCad again from imported Python (round-trip complete)
    6. Validate KiCad still has R1 with same properties

    This tests bidirectional fidelity: no data loss through full cycle.

    Level 2 Semantic Validation:
    - AST parsing for Python code structure
    - kicad-sch-api for KiCad schematic structure
    - Independent of formatting/positioning
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

    # Read original Python file (for restoration later)
    with open(python_file, "r") as f:
        original_code = f.read()

    try:
        # =====================================================================
        # STEP 1: Generate KiCad from Python (first generation)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Python → KiCad (first generation)")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "single_resistor.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 1 failed: Initial Python → KiCad generation\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        assert schematic_file.exists(), "Schematic not created in step 1"

        # Validate KiCad schematic has R1
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        assert len(components) == 1, (
            f"Step 1: Expected 1 component, found {len(components)}"
        )

        r1_initial = components[0]
        assert r1_initial.reference == "R1"
        assert r1_initial.value == "10k"
        assert "R_0603" in r1_initial.footprint

        print(f"✅ Step 1 complete: KiCad generated with R1")
        print(f"   - Reference: {r1_initial.reference}")
        print(f"   - Value: {r1_initial.value}")
        print(f"   - Footprint: {r1_initial.footprint}")

        # =====================================================================
        # STEP 2: Import KiCad back to Python (overwrites single_resistor.py)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: KiCad → Python (import, overwrites file)")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "kicad-to-python", "single_resistor", "single_resistor.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 2 failed: KiCad → Python import\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # Validate imported Python has R1 via AST
        with open(python_file, "r") as f:
            imported_code = f.read()

        tree = ast.parse(imported_code)

        # Find circuit function (handles both @circuit and @circuit(...))
        circuit_functions = []
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                for decorator in node.decorator_list:
                    # Check for @circuit (Name node)
                    if isinstance(decorator, ast.Name) and decorator.id == "circuit":
                        circuit_functions.append(node)
                        break
                    # Check for @circuit(...) (Call node)
                    elif isinstance(decorator, ast.Call):
                        if isinstance(decorator.func, ast.Name) and decorator.func.id == "circuit":
                            circuit_functions.append(node)
                            break

        assert len(circuit_functions) == 1, (
            f"Step 2: Expected 1 @circuit function, found {len(circuit_functions)}\n"
            f"Imported code preview:\n{imported_code[:500]}"
        )

        circuit_function = circuit_functions[0]

        # Look for Component assignments in function body
        component_assigns = []
        for node in ast.walk(circuit_function):
            if isinstance(node, ast.Assign):
                # Check if RHS is Component() call
                if isinstance(node.value, ast.Call):
                    if isinstance(node.value.func, ast.Name):
                        if node.value.func.id == "Component":
                            component_assigns.append(node)

        assert len(component_assigns) >= 1, (
            f"Step 2: Expected at least 1 Component assignment, found {len(component_assigns)}"
        )

        print(f"✅ Step 2 complete: Python imported with {len(component_assigns)} component(s)")

        # =====================================================================
        # STEP 3: Generate KiCad again (round-trip complete)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Python → KiCad (round-trip generation)")
        print("="*70)

        # Remove existing KiCad output
        if output_dir.exists():
            shutil.rmtree(output_dir)

        result = subprocess.run(
            ["uv", "run", "single_resistor.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 3 failed: Round-trip Python → KiCad generation\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        assert schematic_file.exists(), "Schematic not created in step 3"

        # Validate round-trip KiCad schematic still has R1
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        assert len(components) == 1, (
            f"Step 3: Expected 1 component after round-trip, found {len(components)}"
        )

        r1_roundtrip = components[0]
        assert r1_roundtrip.reference == "R1"
        assert r1_roundtrip.value == "10k"
        assert "R_0603" in r1_roundtrip.footprint

        print(f"✅ Step 3 complete: Round-trip KiCad generated with R1")
        print(f"   - Reference: {r1_roundtrip.reference}")
        print(f"   - Value: {r1_roundtrip.value}")
        print(f"   - Footprint: {r1_roundtrip.footprint}")

        # =====================================================================
        # VALIDATION: Verify properties preserved through round-trip
        # =====================================================================
        print("\n" + "="*70)
        print("VALIDATION: Round-trip fidelity check")
        print("="*70)

        assert r1_initial.reference == r1_roundtrip.reference, (
            f"Reference changed: {r1_initial.reference} → {r1_roundtrip.reference}"
        )
        assert r1_initial.value == r1_roundtrip.value, (
            f"Value changed: {r1_initial.value} → {r1_roundtrip.value}"
        )
        assert r1_initial.footprint == r1_roundtrip.footprint, (
            f"Footprint changed: {r1_initial.footprint} → {r1_roundtrip.footprint}"
        )

        print("✅ Round-trip validation passed:")
        print("   - Reference preserved: R1")
        print("   - Value preserved: 10k")
        print("   - Footprint preserved: R_0603")
        print("   - No data loss through full cycle")

    finally:
        # Restore original Python file
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
