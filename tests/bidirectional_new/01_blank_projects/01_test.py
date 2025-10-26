#!/usr/bin/env python3
"""
Test 01: Blank Projects - Simple Visual Verification

Run these tests and manually inspect the output to verify they work.
Much simpler than programmatic assertions - just look at the files!
"""

import subprocess
from pathlib import Path


def test_01_python_to_kicad():
    """
    Test 1.1: Generate KiCad from blank Python circuit.

    What to check manually:
    - Run this test
    - Open generated_kicad/blank/ folder
    - Open blank.kicad_pro in KiCad
    - Verify: Empty schematic with no components
    """
    test_dir = Path(__file__).parent
    output_dir = test_dir / "generated_kicad"

    # Clean previous output
    if output_dir.exists():
        import shutil
        shutil.rmtree(output_dir)
    output_dir.mkdir()

    # Generate KiCad from Python
    print("\n" + "="*60)
    print("TEST 1: Generating KiCad from blank Python circuit...")
    print("="*60)

    # Copy the Python file to output dir so generation happens there
    import shutil
    py_file = output_dir / "blank.py"
    shutil.copy(test_dir / "01_python_ref.py", py_file)

    # Run it
    result = subprocess.run(
        ["uv", "run", "python", "blank.py"],
        cwd=output_dir,
        capture_output=True,
        text=True
    )

    print(f"Exit code: {result.returncode}")
    if result.stdout:
        print(f"Output:\n{result.stdout}")
    if result.stderr:
        print(f"Errors:\n{result.stderr}")

    # Check files exist
    kicad_dir = output_dir / "blank"
    if kicad_dir.exists():
        print(f"\n✅ KiCad project generated at: {kicad_dir}")
        print("\nGenerated files:")
        for f in sorted(kicad_dir.glob("*")):
            if f.is_file():
                print(f"  - {f.name} ({f.stat().st_size} bytes)")
        print("\n👀 MANUAL CHECK: Open blank.kicad_pro in KiCad and verify it's empty")
    else:
        print(f"\n❌ ERROR: KiCad directory not created")
        assert False, "Generation failed"

    print("="*60 + "\n")


def test_02_kicad_to_python():
    """
    Test 1.2: Import Python from blank KiCad project.

    What to check manually:
    - Run this test
    - Look at generated_python/imported_blank.py
    - Verify: Has @circuit decorator, no components
    """
    test_dir = Path(__file__).parent
    kicad_ref = test_dir / "01_kicad_ref" / "01_kicad_ref.kicad_pro"
    output_dir = test_dir / "generated_python"

    # Clean previous output
    if output_dir.exists():
        import shutil
        shutil.rmtree(output_dir)
    output_dir.mkdir()

    print("\n" + "="*60)
    print("TEST 2: Importing Python from blank KiCad project...")
    print("="*60)

    # Import using kicad-to-python command
    output_py = output_dir / "imported_blank.py"
    result = subprocess.run(
        ["uv", "run", "kicad-to-python", str(kicad_ref), str(output_py)],
        capture_output=True,
        text=True
    )

    print(f"Exit code: {result.returncode}")
    if result.stdout:
        print(f"Output:\n{result.stdout}")
    if result.stderr:
        print(f"Errors:\n{result.stderr}")

    if output_py.exists():
        print(f"\n✅ Python file generated at: {output_py}")
        print("\nGenerated Python code preview:")
        print("-" * 60)
        print(output_py.read_text()[:500])  # Show first 500 chars
        print("-" * 60)
        print("\n👀 MANUAL CHECK: Open imported_blank.py and verify it's valid Python")
    else:
        print(f"\n❌ ERROR: Python file not created")
        assert False, "Import failed"

    print("="*60 + "\n")


def test_03_round_trip():
    """
    Test 1.3: Round-trip blank circuit Python → KiCad → Python.

    What to check manually:
    - Run this test
    - Compare generated_roundtrip/step1_original.py with step3_roundtrip.py
    - Verify: Both should define the same blank circuit
    """
    test_dir = Path(__file__).parent
    output_dir = test_dir / "generated_roundtrip"

    # Clean previous output
    if output_dir.exists():
        import shutil
        shutil.rmtree(output_dir)
    output_dir.mkdir()

    print("\n" + "="*60)
    print("TEST 3: Round-trip Python → KiCad → Python...")
    print("="*60)

    # Step 1: Copy original Python
    import shutil
    step1_py = output_dir / "step1_original.py"
    shutil.copy(test_dir / "01_python_ref.py", step1_py)
    print("\nStep 1: Copied original Python")

    # Step 2: Generate KiCad
    result = subprocess.run(
        ["uv", "run", "python", "step1_original.py"],
        cwd=output_dir,
        capture_output=True,
        text=True
    )
    print(f"Step 2: Generated KiCad (exit code: {result.returncode})")

    kicad_dir = output_dir / "blank"
    if not kicad_dir.exists():
        print("❌ KiCad generation failed")
        assert False

    # Step 3: Import back to Python
    kicad_pro = kicad_dir / "blank.kicad_pro"
    step3_py = output_dir / "step3_roundtrip.py"
    result = subprocess.run(
        ["uv", "run", "kicad-to-python", str(kicad_pro), str(step3_py)],
        capture_output=True,
        text=True
    )
    print(f"Step 3: Imported back to Python (exit code: {result.returncode})")

    if step3_py.exists():
        print(f"\n✅ Round-trip completed!")
        print(f"\n📁 Files to compare:")
        print(f"  - Original:   {step1_py}")
        print(f"  - Round-trip: {step3_py}")

        # Show file sizes
        original_size = step1_py.stat().st_size
        roundtrip_size = step3_py.stat().st_size
        print(f"\n📊 File sizes:")
        print(f"  - Original:   {original_size} bytes")
        print(f"  - Round-trip: {roundtrip_size} bytes")
        print(f"  - Ratio:      {roundtrip_size/original_size:.2f}x")

        print("\n👀 MANUAL CHECK: Compare the two Python files - should both define blank circuit")
    else:
        print(f"\n❌ ERROR: Round-trip Python not created")
        assert False

    print("="*60 + "\n")


if __name__ == "__main__":
    """
    Run all tests with: python 01_test.py

    Or run individually:
        pytest 01_test.py::test_01_python_to_kicad -v -s
        pytest 01_test.py::test_02_kicad_to_python -v -s
        pytest 01_test.py::test_03_round_trip -v -s
    """
    import pytest
    pytest.main([__file__, "-v", "-s"])
