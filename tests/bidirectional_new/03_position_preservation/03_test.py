#!/usr/bin/env python3
"""
Test 03: Position Preservation - Simple Visual Verification

CRITICAL: Tests that component positions survive sync operations.
This is crucial - if positions reset, the tool is unusable!

Just run and manually verify positions are preserved.
"""

import subprocess
from pathlib import Path


def test_01_positions_survive_roundtrip():
    """
    Test 3.1: Component positions preserved through Python → KiCad → Python.

    What to check manually:
    1. Run this test
    2. Open generated_roundtrip/step2_kicad/two_resistors/two_resistors.kicad_pro in KiCad
    3. Note the X,Y positions of R1 and R2
    4. Run the circuit generation again from step3_roundtrip.py
    5. Open the new KiCad project
    6. Verify: R1 and R2 are in the SAME positions (not moved!)
    """
    test_dir = Path(__file__).parent
    output_dir = test_dir / "generated_roundtrip"

    # Clean previous output
    if output_dir.exists():
        import shutil
        shutil.rmtree(output_dir)
    output_dir.mkdir()

    print("\n" + "="*60)
    print("TEST 1: Position preservation through round-trip...")
    print("="*60)

    # Step 1: Start with reference Python circuit
    import shutil
    step1_py = output_dir / "step1_original.py"
    shutil.copy(test_dir / "03_python_ref.py", step1_py)
    print("\nStep 1: Copied original circuit (2 resistors)")

    # Step 2: Generate KiCad from Python
    kicad_output = output_dir / "step2_kicad"
    kicad_output.mkdir()
    shutil.copy(step1_py, kicad_output / "two_resistors.py")

    result = subprocess.run(
        ["uv", "run", "python", "two_resistors.py"],
        cwd=kicad_output,
        capture_output=True,
        text=True
    )
    print(f"Step 2: Generated KiCad (exit code: {result.returncode})")

    if result.returncode != 0:
        print(f"❌ Generation failed:\n{result.stderr}")
        assert False

    # Step 3: Import back to Python
    kicad_dir = kicad_output / "two_resistors"
    kicad_pro = kicad_dir / "two_resistors.kicad_pro"

    if not kicad_pro.exists():
        print(f"❌ KiCad project not found at: {kicad_pro}")
        assert False

    step3_py = output_dir / "step3_roundtrip.py"
    result = subprocess.run(
        ["uv", "run", "kicad-to-python", str(kicad_pro), str(step3_py)],
        capture_output=True,
        text=True
    )
    print(f"Step 3: Imported back to Python (exit code: {result.returncode})")

    if not step3_py.exists():
        print(f"❌ Round-trip Python not created")
        print(result.stderr)
        assert False

    print(f"\n✅ Round-trip completed!")
    print(f"\n📁 MANUAL VERIFICATION STEPS:")
    print(f"   1. Open: {kicad_pro}")
    print(f"      - Note R1 position (X, Y coordinates)")
    print(f"      - Note R2 position")
    print(f"")
    print(f"   2. Run the round-trip Python again:")
    print(f"      cd {output_dir}")
    print(f"      uv run python step3_roundtrip.py")
    print(f"")
    print(f"   3. Open the newly generated KiCad project")
    print(f"      Compare R1 and R2 positions")
    print(f"")
    print(f"   4. ✅ PASS if positions are IDENTICAL")
    print(f"      ❌ FAIL if positions changed/reset")

    print("="*60 + "\n")


def test_02_manual_moves_preserved():
    """
    Test 3.2: Manually moved components stay in new positions.

    What to check manually:
    1. Run this test
    2. Open generated_manual_move/manual_move/manual_move.kicad_pro
    3. Manually drag R1 to a different position in KiCad
    4. Save the KiCad project
    5. Re-run: uv run python manual_move.py
    6. Open KiCad again
    7. Verify: R1 is still in the position you moved it to (not reset!)
    """
    test_dir = Path(__file__).parent
    output_dir = test_dir / "generated_manual_move"

    # Clean previous output
    if output_dir.exists():
        import shutil
        shutil.rmtree(output_dir)
    output_dir.mkdir()

    print("\n" + "="*60)
    print("TEST 2: Manual position changes preserved...")
    print("="*60)

    # Generate initial circuit
    import shutil
    shutil.copy(test_dir / "03_python_ref.py", output_dir / "manual_move.py")

    result = subprocess.run(
        ["uv", "run", "python", "manual_move.py"],
        cwd=output_dir,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"❌ Generation failed:\n{result.stderr}")
        assert False

    kicad_dir = output_dir / "two_resistors"
    kicad_pro = kicad_dir / "two_resistors.kicad_pro"

    if kicad_pro.exists():
        print(f"✅ Initial KiCad project generated")
        print(f"\n📁 MANUAL TEST PROCEDURE:")
        print(f"   1. Open: {kicad_pro}")
        print(f"   2. Drag R1 to a new position (e.g., far right)")
        print(f"   3. Save (Ctrl+S)")
        print(f"   4. Run: cd {output_dir} && uv run python manual_move.py")
        print(f"   5. Open KiCad again")
        print(f"   6. ✅ PASS if R1 is still where you moved it")
        print(f"      ❌ FAIL if R1 position reset to original")
    else:
        print(f"❌ KiCad project not created")
        assert False

    print("="*60 + "\n")


def test_03_show_position_in_file():
    """
    Test 3.3: Show where positions are stored in KiCad files.

    This test just shows you where to look for position data.
    """
    test_dir = Path(__file__).parent
    output_dir = test_dir / "generated_position_demo"

    # Clean previous output
    if output_dir.exists():
        import shutil
        shutil.rmtree(output_dir)
    output_dir.mkdir()

    print("\n" + "="*60)
    print("TEST 3: Understanding position storage...")
    print("="*60)

    # Generate circuit
    import shutil
    shutil.copy(test_dir / "03_python_ref.py", output_dir / "demo.py")

    result = subprocess.run(
        ["uv", "run", "python", "demo.py"],
        cwd=output_dir,
        capture_output=True,
        text=True
    )

    if result.returncode != 0:
        print(f"❌ Generation failed")
        assert False

    # Find the schematic file
    sch_files = list(output_dir.glob("**/*.kicad_sch"))
    if not sch_files:
        print("❌ No schematic file found")
        assert False

    sch_file = sch_files[0]
    content = sch_file.read_text()

    print(f"\n📁 Schematic file: {sch_file}")
    print(f"\n🔍 Position data example:")
    print("-" * 60)

    # Find symbol definitions and show position info
    import re
    symbols = re.finditer(
        r'\(symbol \(lib_id "[^"]+"\) \(at ([\d.]+) ([\d.]+) (\d+)\)',
        content
    )

    for i, match in enumerate(symbols, 1):
        x, y, rotation = match.groups()
        print(f"Component {i}: at ({x}, {y}) rotation {rotation}°")
        # Show the full match context
        start = max(0, match.start() - 50)
        end = min(len(content), match.end() + 100)
        snippet = content[start:end]
        print(f"Context: ...{snippet}...")
        print()

    print("-" * 60)
    print("\n💡 This shows where position data is stored")
    print("   The 'at' clause contains (X, Y, rotation)")
    print("   These values should stay the same across syncs!")

    print("="*60 + "\n")


if __name__ == "__main__":
    """
    Run all tests with: python 03_test.py

    Or run individually:
        pytest 03_test.py::test_01_positions_survive_roundtrip -v -s
        pytest 03_test.py::test_02_manual_moves_preserved -v -s
        pytest 03_test.py::test_03_show_position_in_file -v -s
    """
    import pytest
    pytest.main([__file__, "-v", "-s"])
