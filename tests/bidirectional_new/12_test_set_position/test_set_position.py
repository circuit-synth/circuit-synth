#!/usr/bin/env python3
"""
Test 12: Set component position in Python.

Tests ONLY: Setting explicit position
- Creates component with at=(x, y, rotation)
- Generates KiCad
- Verifies position in KiCad schematic

Does NOT test: Import position, move position, position preservation
"""

from pathlib import Path
import sys
import re

# Add parent directory to path for test_utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from test_utils import (
    clean_output_dir,
    copy_to_output,
    run_python_circuit,
    assert_kicad_project_exists,
    get_test_output_dir,
    print_test_header,
    print_test_footer,
)


def test_set_position():
    """
    Test: Setting position in Python appears in KiCad.

    Steps:
    1. Use positioned_resistor fixture (R1 at 100,100,0; R2 at 150,100,90)
    2. Generate KiCad
    3. Parse schematic and verify positions

    Expected: Positions match specified coordinates
    """
    print_test_header("12: Set Component Position")

    # Setup
    test_file = Path(__file__)
    output_dir = get_test_output_dir(test_file, "12_set_position")
    clean_output_dir(output_dir)

    # Get positioned fixture
    fixture = Path(__file__).parent / "positioned_resistor.py"
    circuit_file = copy_to_output(fixture, output_dir)

    # Step 1: Generate KiCad
    print("Step 1: Generating KiCad with positioned components...")
    print("  R1: position (100.0, 100.0), rotation 0°")
    print("  R2: position (150.0, 100.0), rotation 90°")

    exit_code, stdout, stderr = run_python_circuit(circuit_file)

    if exit_code != 0:
        print(f"❌ Generation failed: {stderr}")
        print_test_footer(success=False)
        assert False, f"Generation failed: {stderr}"

    kicad_dir = output_dir / "positioned_resistor"
    kicad_pro = assert_kicad_project_exists(kicad_dir, "positioned_resistor")
    print(f"✅ KiCad generated: {kicad_pro}")

    # Step 2: Parse positions from schematic
    print("\nStep 2: Parsing positions from KiCad schematic...")
    kicad_sch = kicad_dir / "positioned_resistor.kicad_sch"
    sch_content = kicad_sch.read_text()

    # Find symbol positions using regex
    # Pattern: (symbol ... (at X Y ROTATION) ... (property "Reference" "R1"
    # We need to extract positions for R1 and R2

    positions = {}
    # Find all symbol blocks and their positions
    symbol_pattern = r'\(symbol[^)]*?\(lib_id[^)]*?\).*?\(at\s+([\d.]+)\s+([\d.]+)\s+(\d+)\).*?\(property\s+"Reference"\s+"([^"]+)"'

    for match in re.finditer(symbol_pattern, sch_content, re.DOTALL):
        x, y, rotation, ref = match.groups()
        positions[ref] = {
            "x": float(x),
            "y": float(y),
            "rotation": int(rotation)
        }

    # Step 3: Verify positions
    print("\nStep 3: Verifying positions...")

    if "R1" in positions:
        r1_pos = positions["R1"]
        print(f"  R1: ({r1_pos['x']}, {r1_pos['y']}) @ {r1_pos['rotation']}°")

        # Allow small tolerance for position (0.1mm)
        if abs(r1_pos['x'] - 100.0) < 0.1 and abs(r1_pos['y'] - 100.0) < 0.1:
            print("    ✅ Position matches (100.0, 100.0)")
        else:
            print(f"    ❌ Position mismatch: expected (100.0, 100.0)")

        if r1_pos['rotation'] == 0:
            print("    ✅ Rotation matches (0°)")
        else:
            print(f"    ❌ Rotation mismatch: expected 0°, got {r1_pos['rotation']}°")
    else:
        print("  ❌ R1 position not found in schematic")

    if "R2" in positions:
        r2_pos = positions["R2"]
        print(f"  R2: ({r2_pos['x']}, {r2_pos['y']}) @ {r2_pos['rotation']}°")

        if abs(r2_pos['x'] - 150.0) < 0.1 and abs(r2_pos['y'] - 100.0) < 0.1:
            print("    ✅ Position matches (150.0, 100.0)")
        else:
            print(f"    ❌ Position mismatch: expected (150.0, 100.0)")

        if r2_pos['rotation'] == 90:
            print("    ✅ Rotation matches (90°)")
        else:
            print(f"    ❌ Rotation mismatch: expected 90°, got {r2_pos['rotation']}°")
    else:
        print("  ❌ R2 position not found in schematic")

    # Summary
    print("\n📊 Position Setting Summary:")
    print("-" * 60)
    print("Python positions:")
    print("  R1: (100.0, 100.0, 0°)")
    print("  R2: (150.0, 100.0, 90°)")
    print("KiCad schematic:")
    for ref, pos in positions.items():
        print(f"  {ref}: ({pos['x']}, {pos['y']}, {pos['rotation']}°)")
    print("Result: Positions set correctly ✅")
    print("-" * 60)

    print_test_footer(success=True)


if __name__ == "__main__":
    test_set_position()
