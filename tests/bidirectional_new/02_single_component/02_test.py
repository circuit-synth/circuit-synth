#!/usr/bin/env python3
"""
Test 02: Single Component - Simple Visual Verification

Tests basic operations with a single resistor component.
Much simpler - just run and inspect the generated files!
"""

import subprocess
from pathlib import Path


def test_01_python_to_kicad():
    """
    Test 2.1: Generate KiCad from single resistor circuit.

    What to check manually:
    - Run this test
    - Open generated_kicad/single_resistor/ folder
    - Open single_resistor.kicad_pro in KiCad
    - Verify: One resistor R1 with value 10k
    """
    test_dir = Path(__file__).parent
    output_dir = test_dir / "generated_kicad"

    # Clean previous output
    if output_dir.exists():
        import shutil
        shutil.rmtree(output_dir)
    output_dir.mkdir()

    print("\n" + "="*60)
    print("TEST 1: Generating KiCad from single resistor circuit...")
    print("="*60)

    # Copy the Python file to output dir
    import shutil
    py_file = output_dir / "single_resistor.py"
    shutil.copy(test_dir / "02_python_ref.py", py_file)

    # Run it
    result = subprocess.run(
        ["uv", "run", "python", "single_resistor.py"],
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
    kicad_dir = output_dir / "single_resistor"
    if kicad_dir.exists():
        print(f"\n✅ KiCad project generated at: {kicad_dir}")
        print("\nGenerated files:")
        for f in sorted(kicad_dir.glob("*")):
            if f.is_file():
                print(f"  - {f.name} ({f.stat().st_size} bytes)")

        # Show snippet of schematic
        sch_file = kicad_dir / "single_resistor.kicad_sch"
        if sch_file.exists():
            content = sch_file.read_text()
            if "(symbol" in content:
                print("\n✅ Schematic contains components")
            else:
                print("\n⚠️ Schematic appears empty")

        print("\n👀 MANUAL CHECK: Open single_resistor.kicad_pro in KiCad")
        print("   Should see: 1 resistor labeled R1 with value 10k")
    else:
        print(f"\n❌ ERROR: KiCad directory not created")
        assert False, "Generation failed"

    print("="*60 + "\n")


def test_02_kicad_to_python():
    """
    Test 2.2: Import Python from single resistor KiCad project.

    What to check manually:
    - Run this test
    - Look at generated_python/imported_resistor.py
    - Verify: Has Component with ref="R1", value="10k"
    """
    test_dir = Path(__file__).parent
    kicad_ref = test_dir / "02_kicad_ref" / "02_kicad_ref.kicad_pro"
    output_dir = test_dir / "generated_python"

    # Clean previous output
    if output_dir.exists():
        import shutil
        shutil.rmtree(output_dir)
    output_dir.mkdir()

    print("\n" + "="*60)
    print("TEST 2: Importing Python from single resistor KiCad...")
    print("="*60)

    # Import using kicad-to-python command
    output_py = output_dir / "imported_resistor.py"
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
        content = output_py.read_text()

        print("\nGenerated Python code preview:")
        print("-" * 60)
        print(content[:800])  # Show first 800 chars
        print("-" * 60)

        # Quick checks
        if "R1" in content:
            print("\n✅ Found R1 component reference")
        if "10k" in content or "10000" in content:
            print("✅ Found resistor value")

        print("\n👀 MANUAL CHECK: Open imported_resistor.py")
        print("   Should see: Component(ref='R1', value='10k', ...)")
    else:
        print(f"\n❌ ERROR: Python file not created")
        assert False, "Import failed"

    print("="*60 + "\n")


def test_03_round_trip():
    """
    Test 2.3: Round-trip single resistor Python → KiCad → Python.

    What to check manually:
    - Run this test
    - Compare step1_original.py with step3_roundtrip.py
    - Verify: Both define same resistor R1 10k
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
    shutil.copy(test_dir / "02_python_ref.py", step1_py)
    print("\nStep 1: Copied original Python")

    # Step 2: Generate KiCad
    result = subprocess.run(
        ["uv", "run", "python", "step1_original.py"],
        cwd=output_dir,
        capture_output=True,
        text=True
    )
    print(f"Step 2: Generated KiCad (exit code: {result.returncode})")

    kicad_dir = output_dir / "single_resistor"
    if not kicad_dir.exists():
        print("❌ KiCad generation failed")
        print(result.stderr)
        assert False

    # Step 3: Import back to Python
    kicad_pro = kicad_dir / "single_resistor.kicad_pro"
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

        # Show snippet
        print("\nRound-trip Python preview:")
        print("-" * 60)
        print(step3_py.read_text()[:600])
        print("-" * 60)

        print("\n👀 MANUAL CHECK: Compare the two Python files")
        print("   Both should define resistor R1 with 10k value")
    else:
        print(f"\n❌ ERROR: Round-trip Python not created")
        print(result.stderr)
        assert False

    print("="*60 + "\n")


if __name__ == "__main__":
    """
    Run all tests with: python 02_test.py

    Or run individually:
        pytest 02_test.py::test_01_python_to_kicad -v -s
        pytest 02_test.py::test_02_kicad_to_python -v -s
        pytest 02_test.py::test_03_round_trip -v -s
    """
    import pytest
    pytest.main([__file__, "-v", "-s"])
