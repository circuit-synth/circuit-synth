#!/usr/bin/env python3
"""
Test 15: Move component to new position.

Tests ONLY: Changing component position
- Starts with R1 at (100, 100, 0)
- Moves to (200, 150, 45)
- Generates KiCad
- Verifies new position in KiCad

Does NOT test: Initial position setting, position preservation
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


def test_move_component():
    """
    Test: Moving component in Python updates position in KiCad.

    Steps:
    1. Start with positioned_resistor (R1 at 100,100,0)
    2. Modify to move R1 to (200, 150, 45)
    3. Generate KiCad
    4. Verify new position

    Expected: Position updated to new coordinates
    """
    print_test_header("15: Move Component")

    # Setup
    test_file = Path(__file__)
    output_dir = get_test_output_dir(test_file, "15_move_component")
    clean_output_dir(output_dir)

    # Get fixture and copy
    fixture = Path(__file__).parent / "positioned_resistor.py"
    circuit_file = copy_to_output(fixture, output_dir, "circuit_moved.py")

    # Step 1: Modify position
    print("Step 1: Modifying R1 position...")
    print("  Original: (100.0, 100.0, 0°)")
    print("  New:      (200.0, 150.0, 45°)")

    content = circuit_file.read_text()
    # Replace R1's position
    content = content.replace(
        'at=(100.0, 100.0, 0)',
        'at=(200.0, 150.0, 45)'
    )
    circuit_file.write_text(content)
    print("✅ Modified R1 position in Python")

    # Step 2: Generate KiCad
    print("\nStep 2: Generating KiCad with moved component...")
    exit_code, stdout, stderr = run_python_circuit(circuit_file)

    if exit_code != 0:
        print(f"❌ Generation failed: {stderr}")
        print_test_footer(success=False)
        assert False, f"Generation failed: {stderr}"

    kicad_dir = output_dir / "positioned_resistor"
    kicad_pro = assert_kicad_project_exists(kicad_dir, "positioned_resistor")
    print(f"✅ KiCad generated: {kicad_pro}")

    # Step 3: Parse and verify new position
    print("\nStep 3: Verifying new position in KiCad...")
    kicad_sch = kicad_dir / "positioned_resistor.kicad_sch"
    sch_content = kicad_sch.read_text()

    # Find R1 position
    symbol_pattern = r'\(symbol[^)]*?\(lib_id[^)]*?\).*?\(at\s+([\d.]+)\s+([\d.]+)\s+(\d+)\).*?\(property\s+"Reference"\s+"R1"'

    match = re.search(symbol_pattern, sch_content, re.DOTALL)

    if match:
        x, y, rotation = match.groups()
        x, y, rotation = float(x), float(y), int(rotation)

        print(f"  Found R1: ({x}, {y}) @ {rotation}°")

        # Verify new position (with tolerance)
        position_ok = abs(x - 200.0) < 0.1 and abs(y - 150.0) < 0.1
        rotation_ok = rotation == 45

        if position_ok:
            print("    ✅ Position matches (200.0, 150.0)")
        else:
            print(f"    ❌ Position mismatch: expected (200.0, 150.0), got ({x}, {y})")

        if rotation_ok:
            print("    ✅ Rotation matches (45°)")
        else:
            print(f"    ❌ Rotation mismatch: expected 45°, got {rotation}°")

        if not (position_ok and rotation_ok):
            print_test_footer(success=False)
            assert False, "Position or rotation mismatch"

    else:
        print("  ❌ R1 position not found in schematic")
        print_test_footer(success=False)
        assert False, "Could not find R1 position"

    # Summary
    print("\n📊 Component Movement Summary:")
    print("-" * 60)
    print("Original position: (100.0, 100.0, 0°)")
    print("New position:      (200.0, 150.0, 45°)")
    print(f"KiCad schematic:   ({x}, {y}, {rotation}°) ✅")
    print("Result: Component moved successfully ✅")
    print("-" * 60)

    print_test_footer(success=True)


if __name__ == "__main__":
    test_move_component()
