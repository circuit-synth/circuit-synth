#!/usr/bin/env python3
"""
Test 03: Import Python from KiCad project.

Tests ONLY: KiCad → Python import
- Starts with existing KiCad project
- Imports to Python
- Verifies Python file contains component

Does NOT test: Generation, round-trip, property values
"""

from pathlib import Path
import sys

# Add parent directory to path for test_utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from test_utils import (
    clean_output_dir,
    import_kicad_to_python,
    assert_python_file_exists,
    assert_component_in_python,
    get_test_output_dir,
    print_test_header,
    print_test_footer,
)


def test_import():
    """
    Test: KiCad → Python import with single resistor.

    Steps:
    1. Use reference KiCad project (from 02_single_component/02_kicad_ref)
    2. Import to Python using kicad-to-python
    3. Assert Python file was created
    4. Assert R1 component exists in Python

    Expected: Python file with Component(ref="R1", ...)
    """
    print_test_header("03: Import Python from KiCad")

    # Setup - use shared generated/ directory
    test_file = Path(__file__)
    output_dir = get_test_output_dir(test_file, "03_import")
    clean_output_dir(output_dir)

    # Get reference KiCad project (from legacy test directory)
    kicad_ref = Path(__file__).parent.parent / "02_single_component" / "02_kicad_ref" / "02_kicad_ref.kicad_pro"

    if not kicad_ref.exists():
        print(f"❌ Reference KiCad project not found: {kicad_ref}")
        print("Note: Run test 02_generate first to create reference")
        print_test_footer(success=False)
        assert False, f"Reference KiCad project missing: {kicad_ref}"

    # Step 1: Import KiCad to Python
    print(f"Step 1: Importing KiCad project...")
    print(f"  Source: {kicad_ref}")
    output_py = output_dir / "imported_resistor.py"

    exit_code, stdout, stderr = import_kicad_to_python(kicad_ref, output_py)

    if exit_code != 0:
        print(f"❌ Import failed with exit code {exit_code}")
        print(f"STDERR: {stderr}")
        print_test_footer(success=False)
        assert False, f"KiCad import failed: {stderr}"

    print(f"✅ Import completed (exit code: {exit_code})")

    # Step 2: Verify Python file exists
    print("\nStep 2: Verifying Python file...")
    assert_python_file_exists(output_py)
    print(f"✅ Python file created: {output_py}")

    # Step 3: Verify component in Python
    print("\nStep 3: Verifying component in Python...")
    assert_component_in_python(output_py, "R1")
    print("✅ Component R1 found in Python file")

    # Show preview
    print("\n📄 Python file preview:")
    content = output_py.read_text()
    lines = content.split('\n')
    preview_lines = min(30, len(lines))
    print("-" * 60)
    for line in lines[:preview_lines]:
        print(line)
    if len(lines) > preview_lines:
        print(f"... ({len(lines) - preview_lines} more lines)")
    print("-" * 60)

    # Success
    print(f"\n📁 Imported Python file: {output_py}")
    print_test_footer(success=True)


if __name__ == "__main__":
    test_import()
