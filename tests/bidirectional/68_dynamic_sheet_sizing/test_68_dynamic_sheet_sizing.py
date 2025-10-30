#!/usr/bin/env python3
"""
Automated test for 68_dynamic_sheet_sizing bidirectional test.

Tests CRITICAL usability feature: Automatic sheet size adjustment.

This validates that:
1. Initial generation chooses appropriate sheet size (A4 for 10 components)
2. Adding components triggers sheet resize (A4 → A3 for 60 components)
3. All components remain visible within sheet boundaries
4. Works for both generation and synchronization

This is essential for iterative circuit development.

Workflow:
1. Generate with 10 resistors → should fit on A4 sheet
2. Verify sheet size is A4 (297×210mm)
3. Add 50 more resistors (total 60)
4. Regenerate → sheet should auto-resize to A3 (420×297mm)
5. Verify all components visible within new sheet boundaries

Validation uses:
- kicad-sch-api for schematic structure
- Sheet size detection from .kicad_sch file
- Component bounding box calculation
"""

import re
import shutil
import subprocess
from pathlib import Path

import pytest


def get_sheet_size(schematic_file):
    """Extract sheet size from KiCad schematic file.

    Returns tuple: (width_mm, height_mm, paper_name)
    Example: (297.0, 210.0, "A4")
    """
    with open(schematic_file, 'r') as f:
        content = f.read()

    # Look for paper size in KiCad 7+ format
    # (paper "A4")
    paper_match = re.search(r'\(paper\s+"([^"]+)"\)', content)

    if not paper_match:
        return None, None, "Unknown"

    paper_name = paper_match.group(1)

    # Standard KiCad paper sizes (width×height in mm)
    paper_sizes = {
        "A5": (210.0, 148.0),
        "A4": (297.0, 210.0),
        "A3": (420.0, 297.0),
        "A2": (594.0, 420.0),
        "A1": (841.0, 594.0),
        "A0": (1189.0, 841.0),
        "A": (279.4, 215.9),  # US Letter equivalent
        "B": (431.8, 279.4),  # US Tabloid
        "C": (558.8, 431.8),
        "D": (863.6, 558.8),
        "E": (1117.6, 863.6),
    }

    if paper_name in paper_sizes:
        width, height = paper_sizes[paper_name]
        return width, height, paper_name

    return None, None, paper_name


def test_68_dynamic_sheet_sizing(request):
    """Test automatic sheet size adjustment when adding components.

    CRITICAL USABILITY FEATURE:
    Validates that KiCad schematic automatically resizes sheet to fit components:
    - Initial: 10 components fit on A4
    - After adding 50 more: Sheet auto-resizes to A3
    - All components visible within sheet boundaries

    This workflow is essential for:
    - Iterative circuit development (start small, grow over time)
    - Professional tool behavior (like Altium, Eagle)
    - Avoiding manual sheet resizing
    - Preventing components from disappearing off-screen

    Workflow:
    1. Generate with 10 resistors → A4 sheet
    2. Verify sheet size is A4 (297×210mm)
    3. Add 50 more resistors (total 60)
    4. Regenerate → sheet should auto-resize to A3 (420×297mm)
    5. Validate all components visible within new boundaries

    Level 3 Validation:
    - kicad-sch-api for schematic structure
    - Sheet size detection from .kicad_sch
    - Component position validation
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "growing_circuit.py"
    output_dir = test_dir / "growing_circuit"
    schematic_file = output_dir / "growing_circuit.kicad_sch"

    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    # Clean any existing output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Read original Python file (10 resistors only)
    with open(python_file, "r") as f:
        original_code = f.read()

    try:
        # =====================================================================
        # STEP 1: Generate with 10 resistors (should fit on A4)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate with 10 resistors (A4 sheet expected)")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "growing_circuit.py"],
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

        # Validate initial components
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        initial_count = len(components)
        print(f"✅ Step 1: Initial circuit generated")
        print(f"   - Components: {initial_count}")

        assert initial_count == 10, (
            f"Expected 10 components initially, found {initial_count}"
        )

        # =====================================================================
        # STEP 2: Verify initial sheet size is A4
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Verify initial sheet size (A4 expected)")
        print("="*70)

        width, height, paper_name = get_sheet_size(schematic_file)

        print(f"📏 Initial sheet size:")
        print(f"   - Paper: {paper_name}")
        print(f"   - Dimensions: {width}×{height}mm")

        assert paper_name == "A4", (
            f"Expected A4 sheet for 10 components, got {paper_name}"
        )
        assert width == 297.0, f"A4 width should be 297mm, got {width}mm"
        assert height == 210.0, f"A4 height should be 210mm, got {height}mm"

        print(f"✅ Step 2: Initial sheet size correct (A4)")

        # =====================================================================
        # STEP 3: Modify code to add 50 more resistors (R11-R60)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Add 50 more resistors (R11-R60)")
        print("="*70)

        # Uncomment R11-R60 in the Python file
        modified_code = original_code.replace(
            "# r11 = Component(symbol=\"Device:R\", ref=\"R11\",",
            "r11 = Component(symbol=\"Device:R\", ref=\"R11\","
        )
        for i in range(12, 61):
            modified_code = modified_code.replace(
                f"# r{i} = Component(symbol=\"Device:R\", ref=\"R{i}\",",
                f"r{i} = Component(symbol=\"Device:R\", ref=\"R{i}\","
            )

        # Verify modification made
        assert modified_code != original_code, (
            "Modification code failed - original unchanged"
        )

        with open(python_file, "w") as f:
            f.write(modified_code)

        print(f"✅ Step 3: Python code modified")
        print(f"   - Added R11-R60 (50 more resistors)")
        print(f"   - Total components: 60")

        # =====================================================================
        # STEP 4: Regenerate with 60 resistors
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 4: Regenerate with 60 resistors")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "growing_circuit.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 4 failed: Regeneration with 60 components\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # Validate component count
        sch = Schematic.load(str(schematic_file))
        components = sch.components
        final_count = len(components)

        print(f"✅ Step 4: Circuit regenerated")
        print(f"   - Components: {final_count}")

        assert final_count == 60, (
            f"Expected 60 components after modification, found {final_count}"
        )

        # =====================================================================
        # STEP 5: Verify sheet auto-resized to A3 or larger
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 5: Verify sheet auto-resized to A3 or larger")
        print("="*70)

        width_new, height_new, paper_name_new = get_sheet_size(schematic_file)

        print(f"📏 New sheet size:")
        print(f"   - Paper: {paper_name_new}")
        print(f"   - Dimensions: {width_new}×{height_new}mm")

        # CURRENT BEHAVIOR (BUG): Sheet does NOT resize
        # This test will XFAIL until the feature is implemented

        # Expected behavior:
        # assert paper_name_new in ["A3", "A2", "A1", "A0"], (
        #     f"Expected sheet to resize to A3 or larger for 60 components, "
        #     f"got {paper_name_new}"
        # )

        # Current behavior (BUG):
        if paper_name_new == "A4":
            print(f"⚠️  BUG: Sheet did NOT resize (still A4)")
            print(f"   Expected: A3 (420×297mm) or larger")
            print(f"   Got: A4 (297×210mm)")
            print(f"   This test documents the missing feature")
            pytest.xfail("Dynamic sheet sizing not implemented yet (Issue #413)")

        # If it did resize, validate
        assert paper_name_new in ["A3", "A2", "A1", "A0"], (
            f"Sheet resized to unexpected size: {paper_name_new}"
        )

        print(f"✅ Step 5: Sheet automatically resized to {paper_name_new}!")

        # =====================================================================
        # STEP 6: Validate all components within sheet boundaries
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 6: Validate all components within sheet boundaries")
        print("="*70)

        # Calculate component positions and check against sheet size
        margin = 12.7  # KiCad default margin in mm
        max_x = width_new - margin
        max_y = height_new - margin

        overflow_count = 0
        for comp in components:
            x, y = comp.position.x, comp.position.y
            if x < margin or x > max_x or y < margin or y > max_y:
                overflow_count += 1
                print(f"   ⚠️  {comp.reference} overflow: ({x:.1f}, {y:.1f})")

        if overflow_count > 0:
            print(f"\n❌ {overflow_count} components overflow sheet boundaries!")
            print(f"   Sheet: {width_new}×{height_new}mm")
            print(f"   Usable area: ({margin}, {margin}) to ({max_x:.1f}, {max_y:.1f})")
        else:
            print(f"✅ All {final_count} components within sheet boundaries")

        assert overflow_count == 0, (
            f"{overflow_count} components overflow sheet boundaries"
        )

        print(f"\n✅ Dynamic Sheet Sizing Test PASSED!")
        print(f"\n📋 Summary:")
        print(f"   - Initial: 10 components on A4 (297×210mm)")
        print(f"   - Added: 50 components (total 60)")
        print(f"   - Result: Auto-resized to {paper_name_new} ({width_new}×{height_new}mm)")
        print(f"   - All components within boundaries ✓")

    finally:
        # Restore original Python file
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
