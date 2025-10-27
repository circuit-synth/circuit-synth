#!/usr/bin/env python3
"""Test 01: Blank circuit generation"""

from pathlib import Path
import sys
import shutil
sys.path.insert(0, str(Path(__file__).parent.parent))

from test_utils import (
    run_python_circuit,
    assert_kicad_project_exists,
    print_test_header,
    print_test_footer
)


def test_blank():
    """Test: Blank circuit generates KiCad files."""
    print_test_header("01: Blank Circuit")

    test_dir = Path(__file__).parent
    blank_py = test_dir / "blank.py"
    output_dir = test_dir / "output"

    # Clean output directory
    if output_dir.exists():
        shutil.rmtree(output_dir)
    output_dir.mkdir()

    # Step 1: Generate KiCad from blank.py
    print("Step 1: Generating KiCad from blank.py...")

    # Copy blank.py to output and run it there
    blank_copy = output_dir / "blank.py"
    shutil.copy(blank_py, blank_copy)

    exit_code, stdout, stderr = run_python_circuit(blank_copy)

    if exit_code != 0:
        print(f"❌ Generation failed with exit code {exit_code}")
        print(f"STDERR: {stderr}")
        print_test_footer(success=False)
        assert False, f"Circuit generation failed: {stderr}"

    print(f"✅ Generation completed (exit code: {exit_code})")

    # Step 2: Verify KiCad project exists
    print("\nStep 2: Verifying KiCad project exists...")
    kicad_dir = output_dir / "blank"
    kicad_pro = assert_kicad_project_exists(kicad_dir, "blank")
    print(f"✅ KiCad project found: {kicad_pro}")

    # Step 3: Verify essential files exist
    print("\nStep 3: Checking essential files...")
    essential_files = [
        "blank.kicad_pro",
        "blank.kicad_sch",
        "blank.kicad_pcb",
    ]

    for filename in essential_files:
        filepath = kicad_dir / filename
        if not filepath.exists():
            print(f"❌ Missing file: {filename}")
            print_test_footer(success=False)
            assert False, f"Missing essential file: {filename}"
        print(f"  ✅ {filename}")

    # Success
    print(f"\n📁 Generated project: {kicad_dir}")
    print("\n🔍 Manual verification:")
    print(f"   cd {kicad_dir}")
    print(f"   open blank.kicad_pro")
    print_test_footer(success=True)


if __name__ == "__main__":
    test_blank()
