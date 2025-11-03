#!/usr/bin/env python3
"""
Test for Issue #472: UUID mismatch causing reference to become R?

Hypothesis: If the component UUID doesn't match between generations,
the sync code might fail to recognize it as the same component,
treating it as "unannotated" and showing R?.

This test simulates scenarios where UUID matching might fail.
"""

import shutil
import subprocess
from pathlib import Path

import pytest


def test_uuid_mismatch_scenario(request):
    """
    Simulate a scenario where UUID matching might fail.

    Workflow:
    1. Generate circuit with R1
    2. Manually modify the .kicad_sch file to change the UUID
    3. Regenerate from Python
    4. Check if R1 becomes R? due to UUID mismatch
    """

    test_dir = Path(__file__).parent
    python_file = test_dir / "simple_resistor.py"
    output_dir = test_dir / "simple_resistor"
    schematic_file = output_dir / "simple_resistor.kicad_sch"

    cleanup = not request.config.getoption("--keep-output", default=False)

    if output_dir.exists():
        shutil.rmtree(output_dir)

    try:
        # Step 1: Generate initial circuit
        print("\n" + "=" * 70)
        print("STEP 1: Generate initial circuit with R1")
        print("=" * 70)

        result = subprocess.run(
            ["uv", "run", str(python_file)],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0
        assert schematic_file.exists()

        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        regular_components = [c for c in sch.components if not c.reference.startswith("#PWR")]
        r1_original = regular_components[0]

        print(f"✅ Original R1 generated:")
        print(f"   Reference: {r1_original.reference}")
        print(f"   UUID: {r1_original.uuid}")

        # Step 2: Manually corrupt the UUID in the .kicad_sch file
        print("\n" + "=" * 70)
        print("STEP 2: Manually change UUID in .kicad_sch file")
        print("=" * 70)

        with open(schematic_file, "r") as f:
            sch_content = f.read()

        # Replace the UUID with a different one
        corrupted_uuid = "00000000-0000-0000-0000-000000000000"
        sch_content = sch_content.replace(
            str(r1_original.uuid),
            corrupted_uuid
        )

        with open(schematic_file, "w") as f:
            f.write(sch_content)

        print(f"   Replaced UUID: {r1_original.uuid} → {corrupted_uuid}")

        # Verify corruption
        sch_corrupted = Schematic.load(str(schematic_file))
        regular_components_corrupted = [
            c for c in sch_corrupted.components if not c.reference.startswith("#PWR")
        ]
        r1_corrupted = regular_components_corrupted[0]

        print(f"   Verified corrupted UUID: {r1_corrupted.uuid}")
        assert r1_corrupted.uuid == corrupted_uuid

        # Step 3: Regenerate from Python
        print("\n" + "=" * 70)
        print("STEP 3: Regenerate from Python (UUID mismatch scenario)")
        print("=" * 70)

        result = subprocess.run(
            ["uv", "run", str(python_file)],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0

        # Step 4: Check if reference became R?
        sch_after = Schematic.load(str(schematic_file))
        regular_components_after = [
            c for c in sch_after.components if not c.reference.startswith("#PWR")
        ]
        r1_after = regular_components_after[0]

        print(f"\n📊 After regeneration with UUID mismatch:")
        print(f"   Reference: {r1_after.reference}")
        print(f"   UUID: {r1_after.uuid}")

        # Check for the bug
        if r1_after.reference == "R?":
            print(f"\n❌ 🐛 BUG REPRODUCED: UUID mismatch caused R1 → R?")
            pytest.fail(
                f"Issue #472 REPRODUCED via UUID mismatch!\n"
                f"Original UUID: {r1_original.uuid}\n"
                f"Corrupted UUID: {corrupted_uuid}\n"
                f"After regen: Reference = {r1_after.reference}\n"
                f"UUID mismatch caused component to be treated as unannotated."
            )
        elif r1_after.reference != "R1":
            print(f"\n⚠️  Unexpected reference: {r1_after.reference}")
        else:
            print(f"\n✅ Reference still R1 (UUID mismatch handled correctly)")
            print(f"   New UUID: {r1_after.uuid}")

    finally:
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
