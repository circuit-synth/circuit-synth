#!/usr/bin/env python3
"""
Automated test to reproduce Issue #472: Reference designator becomes "R?" after sync.

This test programmatically:
1. Generates the circuit once → verifies R1 appears correctly
2. Regenerates the circuit → verifies R1 is preserved (NOT R?)
3. Provides detailed logging and debugging output

Usage:
    pytest test_reference_preservation.py -v
    pytest test_reference_preservation.py -v --keep-output  # Keep files for inspection
    pytest test_reference_preservation.py -v -s            # Show all print output
"""

import shutil
import subprocess
from pathlib import Path

import pytest


def test_reference_preserved_across_regeneration(request):
    """
    Test that component reference "R1" is preserved across regenerations.

    BUG: After regeneration, R1 becomes R? in KiCad schematic.

    Steps:
    1. Generate circuit with R1 → Validate R1 in KiCad
    2. Regenerate same circuit → Validate R1 still R1 (not R?)
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "simple_resistor.py"
    output_dir = test_dir / "simple_resistor"
    schematic_file = output_dir / "simple_resistor.kicad_sch"

    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    # Clean any existing output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    try:
        # =====================================================================
        # STEP 1: Generate circuit first time
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 1: Generate circuit (first time)")
        print("=" * 70)

        result = subprocess.run(
            ["uv", "run", str(python_file)],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )

        print(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")

        assert result.returncode == 0, (
            f"Step 1 failed: Initial generation\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        assert schematic_file.exists(), "Schematic not created"

        # Validate R1 in schematic
        from kicad_sch_api import Schematic

        sch = Schematic.load(str(schematic_file))

        # Filter out power symbols
        regular_components = [
            c for c in sch.components if not c.reference.startswith("#PWR")
        ]

        assert len(regular_components) == 1, (
            f"Expected 1 component, found {len(regular_components)}: "
            f"{[c.reference for c in regular_components]}"
        )

        r1_gen1 = regular_components[0]

        print(f"\n✅ Step 1: Circuit generated successfully")
        print(f"   Reference: {r1_gen1.reference}")
        print(f"   Value: {r1_gen1.value}")
        print(f"   Position: ({r1_gen1.position.x}, {r1_gen1.position.y})")
        print(f"   UUID: {r1_gen1.uuid}")

        # Verify R1 (not R?)
        assert r1_gen1.reference == "R1", (
            f"❌ BUG DETECTED in Step 1: Reference is '{r1_gen1.reference}', expected 'R1'"
        )
        assert r1_gen1.value == "4.7k", f"Value should be 4.7k, got {r1_gen1.value}"

        # =====================================================================
        # STEP 2: Regenerate circuit (trigger bug)
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 2: Regenerate circuit (should preserve R1)")
        print("=" * 70)

        result = subprocess.run(
            ["uv", "run", str(python_file)],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )

        print(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")

        assert result.returncode == 0, (
            f"Step 2 failed: Regeneration\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # Reload schematic
        sch = Schematic.load(str(schematic_file))
        regular_components = [
            c for c in sch.components if not c.reference.startswith("#PWR")
        ]

        assert len(regular_components) == 1, (
            f"Expected 1 component after regen, found {len(regular_components)}: "
            f"{[c.reference for c in regular_components]}"
        )

        r1_gen2 = regular_components[0]

        print(f"\n📊 Step 2: Regeneration complete - Comparing states")
        print(f"   Reference: {r1_gen2.reference} (was: {r1_gen1.reference})")
        print(f"   Value: {r1_gen2.value} (was: {r1_gen1.value})")
        print(f"   Position: ({r1_gen2.position.x}, {r1_gen2.position.y}) "
              f"(was: ({r1_gen1.position.x}, {r1_gen1.position.y}))")
        print(f"   UUID: {r1_gen2.uuid} (was: {r1_gen1.uuid})")

        # =====================================================================
        # VERIFICATION: Check for bug
        # =====================================================================
        print("\n" + "=" * 70)
        print("VERIFICATION")
        print("=" * 70)

        # Primary bug check: Reference should be R1, not R?
        if r1_gen2.reference == "R?":
            print(f"\n❌ 🐛 BUG REPRODUCED: Reference changed from 'R1' to 'R?'")
            pytest.fail(
                f"Issue #472 REPRODUCED: Reference designator changed from 'R1' to 'R?'\n"
                f"Generation 1: {r1_gen1.reference}\n"
                f"Generation 2: {r1_gen2.reference}\n"
                f"This is the bug we're fixing!"
            )
        elif r1_gen2.reference != "R1":
            print(f"\n❌ Unexpected reference: {r1_gen2.reference}")
            pytest.fail(
                f"Reference changed unexpectedly: '{r1_gen1.reference}' → '{r1_gen2.reference}'"
            )
        else:
            print(f"\n✅ Reference preserved: R1 → R1")

        # Value should be preserved
        assert r1_gen2.value == "4.7k", (
            f"Value changed: {r1_gen1.value} → {r1_gen2.value}"
        )
        print(f"✅ Value preserved: {r1_gen1.value} → {r1_gen2.value}")

        # Position should be preserved
        assert r1_gen2.position.x == r1_gen1.position.x, (
            f"Position X changed: {r1_gen1.position.x} → {r1_gen2.position.x}"
        )
        assert r1_gen2.position.y == r1_gen1.position.y, (
            f"Position Y changed: {r1_gen1.position.y} → {r1_gen2.position.y}"
        )
        print(f"✅ Position preserved: ({r1_gen1.position.x}, {r1_gen1.position.y})")

        # UUID comparison (informational)
        if r1_gen2.uuid == r1_gen1.uuid:
            print(f"✅ UUID preserved: {r1_gen1.uuid}")
        else:
            print(f"⚠️  UUID changed: {r1_gen1.uuid} → {r1_gen2.uuid}")
            print(f"   (This may be expected behavior or part of the bug)")

        print("\n" + "=" * 70)
        print("✅ TEST PASSED: All preservation checks passed")
        print("=" * 70)

    finally:
        # Cleanup generated files unless --keep-output
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
            print(f"\n🗑️  Cleaned up {output_dir}")
        elif output_dir.exists():
            print(f"\n📁 Output preserved at: {output_dir}")
            print(f"   Open in KiCad: {output_dir / 'simple_resistor.kicad_pro'}")


def test_reference_preserved_three_generations(request):
    """
    Extended test: Verify reference preserved across 3+ generations.

    This tests for progressive degradation or cumulative bugs.
    """

    test_dir = Path(__file__).parent
    python_file = test_dir / "simple_resistor.py"
    output_dir = test_dir / "simple_resistor"
    schematic_file = output_dir / "simple_resistor.kicad_sch"

    cleanup = not request.config.getoption("--keep-output", default=False)

    if output_dir.exists():
        shutil.rmtree(output_dir)

    try:
        from kicad_sch_api import Schematic

        references = []
        uuids = []
        positions = []

        for gen in range(1, 4):
            print(f"\n🔄 Generation {gen}")

            result = subprocess.run(
                ["uv", "run", str(python_file)],
                cwd=test_dir,
                capture_output=True,
                text=True,
                timeout=30,
            )

            assert result.returncode == 0, f"Generation {gen} failed"

            sch = Schematic.load(str(schematic_file))
            regular_components = [
                c for c in sch.components if not c.reference.startswith("#PWR")
            ]
            r1 = regular_components[0]

            references.append(r1.reference)
            uuids.append(r1.uuid)
            positions.append((r1.position.x, r1.position.y))

            print(f"   Reference: {r1.reference}")
            print(f"   UUID: {r1.uuid}")
            print(f"   Position: {positions[-1]}")

        print("\n" + "=" * 70)
        print("Multi-generation verification")
        print("=" * 70)
        print(f"References: {references}")
        print(f"UUIDs: {uuids}")
        print(f"Positions: {positions}")

        # All references should be R1
        for i, ref in enumerate(references, 1):
            assert ref == "R1", (
                f"Generation {i}: Reference is '{ref}', expected 'R1'"
            )

        # All positions should be identical
        for i, pos in enumerate(positions[1:], 2):
            assert pos == positions[0], (
                f"Generation {i}: Position changed from {positions[0]} to {pos}"
            )

        print("\n✅ All 3 generations: Reference and position preserved")

    finally:
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


if __name__ == "__main__":
    # Allow running directly for debugging
    pytest.main([__file__, "-v", "-s"])
