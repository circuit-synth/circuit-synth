#!/usr/bin/env python3
"""
Test 04: Multiple Components - Simple Visual Verification

Tests circuits with multiple components (resistors, capacitors, etc).
Just run and inspect the generated files!
"""

import subprocess
from pathlib import Path


def test_01_multiple_resistors():
    """
    Test 4.1: Circuit with 3+ resistors.

    What to check manually:
    - Run this test
    - Open generated_kicad/multi_resistor/multi_resistor.kicad_pro in KiCad
    - Verify: See 3 or more resistors with different values
    """
    test_dir = Path(__file__).parent
    output_dir = test_dir / "generated_kicad"

    if output_dir.exists():
        import shutil
        shutil.rmtree(output_dir)
    output_dir.mkdir()

    print("\n" + "="*60)
    print("TEST 1: Multiple resistors circuit...")
    print("="*60)

    import shutil
    py_file = output_dir / "multi_resistor.py"
    shutil.copy(test_dir / "04_python_ref.py", py_file)

    result = subprocess.run(
        ["uv", "run", "python", "multi_resistor.py"],
        cwd=output_dir,
        capture_output=True,
        text=True
    )

    print(f"Exit code: {result.returncode}")
    if result.stderr:
        print(f"Errors:\n{result.stderr}")

    kicad_dir = list(output_dir.glob("*/"))
    if kicad_dir:
        kicad_pro = list(kicad_dir[0].glob("*.kicad_pro"))[0]
        print(f"\n✅ KiCad project: {kicad_pro}")
        print(f"\n👀 MANUAL CHECK: Open in KiCad and verify multiple components")
    else:
        print("❌ No KiCad project generated")
        assert False

    print("="*60 + "\n")


def test_02_round_trip():
    """
    Test 4.2: Round-trip with multiple components.

    What to check manually:
    - Compare original vs round-trip Python files
    - All components should be present in both
    """
    test_dir = Path(__file__).parent
    output_dir = test_dir / "generated_roundtrip"

    if output_dir.exists():
        import shutil
        shutil.rmtree(output_dir)
    output_dir.mkdir()

    print("\n" + "="*60)
    print("TEST 2: Round-trip with multiple components...")
    print("="*60)

    # Generate → Import → Compare
    import shutil
    step1_py = output_dir / "step1_original.py"
    shutil.copy(test_dir / "04_python_ref.py", step1_py)

    # Generate KiCad
    result = subprocess.run(
        ["uv", "run", "python", "step1_original.py"],
        cwd=output_dir,
        capture_output=True,
        text=True
    )
    print(f"Step 1: Generated KiCad (exit code: {result.returncode})")

    # Find the generated project
    kicad_dirs = list(output_dir.glob("*/"))
    if not kicad_dirs:
        print("❌ No KiCad directory")
        assert False

    kicad_pro = list(kicad_dirs[0].glob("*.kicad_pro"))[0]

    # Import back
    step3_py = output_dir / "step3_roundtrip.py"
    result = subprocess.run(
        ["uv", "run", "kicad-to-python", str(kicad_pro), str(step3_py)],
        capture_output=True,
        text=True
    )
    print(f"Step 2: Imported back (exit code: {result.returncode})")

    if step3_py.exists():
        print(f"\n✅ Round-trip completed")
        print(f"\n📁 Compare:")
        print(f"   Original:   {step1_py}")
        print(f"   Round-trip: {step3_py}")
        print(f"\n👀 MANUAL CHECK: All components present in both files")
    else:
        print("❌ Round-trip failed")
        assert False

    print("="*60 + "\n")


if __name__ == "__main__":
    import pytest
    pytest.main([__file__, "-v", "-s"])
