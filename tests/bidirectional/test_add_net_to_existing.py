#!/usr/bin/env python3
"""
Test for Issue #344: Adding Net() to existing unconnected components

This test reproduces the bug where adding a Net() connection in Python
and regenerating does NOT create hierarchical labels in the KiCad schematic.
"""

import tempfile
from pathlib import Path

from circuit_synth import Component, Net, circuit


def test_add_net_to_unconnected_components():
    """
    Test Issue #344: Adding Net() to existing unconnected components should create labels.

    Steps:
    1. Generate circuit with two unconnected resistors (no Net)
    2. Verify no labels in schematic
    3. Add Net() connecting the resistors
    4. Regenerate (sync mode)
    5. Verify hierarchical labels appear
    """

    with tempfile.TemporaryDirectory() as tmpdir:
        tmpdir_path = Path(tmpdir)

        # Step 1: Create circuit WITHOUT net
        @circuit(name="two_resistors")
        def circuit_no_net():
            r1 = Component(
                symbol="Device:R",
                ref="R1",
                value="1k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            r2 = Component(
                symbol="Device:R",
                ref="R2",
                value="10k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            # NO Net connections!

        # Generate initial schematic
        circuit_obj = circuit_no_net()
        # Change to temporary directory for output
        import os
        original_dir = os.getcwd()
        os.chdir(tmpdir_path)
        try:
            result = circuit_obj.generate_kicad_project(
                project_name="two_resistors",
                generate_pcb=False,
            )
        finally:
            os.chdir(original_dir)

        project_dir = Path(result["project_path"])
        sch_file = project_dir / "two_resistors.kicad_sch"

        # Verify no labels initially
        with open(sch_file, "r") as f:
            initial_content = f.read()

        # Count labels (should be 0 or very few - just component labels)
        initial_label_count = initial_content.count("(label")
        print(f"🔍 Initial label count: {initial_label_count}")

        # Step 2: Create circuit WITH net
        @circuit(name="two_resistors")
        def circuit_with_net():
            r1 = Component(
                symbol="Device:R",
                ref="R1",
                value="1k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            r2 = Component(
                symbol="Device:R",
                ref="R2",
                value="10k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )

            # NOW add a net connection!
            net1 = Net(name="NET1")
            net1 += r1[1]
            net1 += r2[1]

        # Regenerate (this should trigger sync)
        circuit_obj2 = circuit_with_net()
        os.chdir(tmpdir_path)
        try:
            result2 = circuit_obj2.generate_kicad_project(
                project_name="two_resistors",
                generate_pcb=False,
            )
        finally:
            os.chdir(original_dir)

        # Read updated schematic
        with open(sch_file, "r") as f:
            updated_content = f.read()

        # Count labels after adding net
        updated_label_count = updated_content.count("(label")
        print(f"🔍 Updated label count: {updated_label_count}")

        # Count hierarchical labels specifically
        hierarchical_label_count = updated_content.count("(hierarchical_label")
        print(f"🔍 Hierarchical label count: {hierarchical_label_count}")

        # Check if NET1 appears in the schematic
        net1_in_schematic = "NET1" in updated_content
        net1_label_count = updated_content.count('"NET1"')
        print(f"🔍 NET1 in schematic: {net1_in_schematic}")
        print(f"🔍 NET1 label occurrences: {net1_label_count}")

        # EXPECTED: At least 2 labels (one per pin connected to NET1)
        # Can be either hierarchical or local labels

        print("\n📋 Test Results:")
        print(f"  Initial labels: {initial_label_count}")
        print(f"  Updated labels: {updated_label_count}")
        print(f"  Hierarchical labels: {hierarchical_label_count}")
        print(f"  NET1 present: {net1_in_schematic}")
        print(f"  NET1 labels: {net1_label_count}")

        # This assertion SHOULD pass - check for NET1 appearing at least twice
        # (once for each pin connection, can be either label type)
        assert net1_label_count >= 2, (
            f"Expected at least 2 NET1 labels (one per pin), "
            f"but found {net1_label_count}. This is bug #344!"
        )

        assert net1_in_schematic, "NET1 should appear in schematic"


if __name__ == "__main__":
    test_add_net_to_unconnected_components()
    print("✅ Test passed!")
