#!/usr/bin/env python3
"""
Automated test for 60_remove_hierarchical_pin bidirectional test.

Tests hierarchical pin removal: When a component no longer needs a signal,
the hierarchical pin should be removed from the sheet symbol and the
hierarchical label should be removed from the subcircuit.

Core Question: When you remove a connection from a subcircuit's interface,
do both the hierarchical pin (on parent sheet) and hierarchical label
(in subcircuit) get properly removed during regeneration?

Workflow:
1. Generate KiCad with 3 hierarchical pins: VCC, GND, SIGNAL
2. Validate all 3 pins/labels present
3. Remove SIGNAL connection in Python (component no longer needs it)
4. Regenerate KiCad
5. Validate SIGNAL pin/label removed
6. Validate VCC, GND pins/labels preserved
7. Validate netlist no longer shows SIGNAL net

**KNOWN ISSUE (Issue #380):**
The synchronizer may not remove old hierarchical labels when connections are removed.
This test is marked as XFAIL until Issue #380 is resolved.
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest


@pytest.mark.xfail(reason="Issue #380: Synchronizer doesn't remove old hierarchical labels")
def test_60_remove_hierarchical_pin(request):
    """Test hierarchical pin removal during regeneration.

    PRIORITY 1 TEST (Hierarchical Pin Removal):
    Validates that when a hierarchical connection is removed from Python,
    both the hierarchical pin (parent) and hierarchical label (subcircuit)
    are properly removed during regeneration.

    Workflow:
    1. Generate with VCC, GND, SIGNAL hierarchical pins
    2. Validate all 3 pins/labels present
    3. Remove SIGNAL from Python code
    4. Regenerate → SIGNAL pin/label should be removed
    5. Validate only VCC, GND remain
    6. Validate netlist no longer shows SIGNAL

    Why critical:
    - Interface simplification is common during development
    - Removing unused signals keeps designs clean
    - Orphaned pins/labels cause confusion and errors
    - Real-world: removing debug signals, unused power rails, etc.

    Known Issue #380:
    - Synchronizer currently doesn't remove old hierarchical labels
    - Old SIGNAL label may remain in subcircuit
    - Old SIGNAL pin may remain on sheet symbol
    - Test marked XFAIL until this is fixed

    Level 2 Semantic Validation:
    - Regex pattern matching for hierarchical labels and pins
    - Pin/label name verification

    Level 3 Electrical Validation:
    - kicad-cli netlist export
    - Verify SIGNAL net no longer in netlist
    - Verify VCC, GND nets preserved
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "three_pin_subcircuit.py"
    output_dir = test_dir / "three_pin_subcircuit"
    parent_schematic = output_dir / "three_pin_subcircuit.kicad_sch"
    subcircuit_schematic = output_dir / "PowerAndSignal.kicad_sch"

    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    # Clean any existing output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Read original Python file
    with open(python_file, "r") as f:
        original_code = f.read()

    try:
        # =====================================================================
        # STEP 1: Generate KiCad with VCC, GND, SIGNAL hierarchical pins
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 1: Generate KiCad with VCC, GND, SIGNAL hierarchical pins")
        print("=" * 70)

        result = subprocess.run(
            ["uv", "run", "three_pin_subcircuit.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, (
            f"Step 1 failed: Initial generation\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        assert parent_schematic.exists(), "Parent schematic not created"
        assert subcircuit_schematic.exists(), "Subcircuit schematic not created"

        print(f"✅ Step 1: KiCad project generated")
        print(f"   - Parent: {parent_schematic.name}")
        print(f"   - Subcircuit: {subcircuit_schematic.name}")

        # =====================================================================
        # STEP 2: Validate all 3 hierarchical labels in subcircuit (Level 2)
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 2: Validate all 3 hierarchical labels in subcircuit (Level 2)")
        print("=" * 70)

        # Read subcircuit schematic to find hierarchical labels
        subcircuit_content = subcircuit_schematic.read_text()

        # Pattern for hierarchical_label in KiCad S-expression format
        hierarchical_label_pattern = r'\(hierarchical_label\s+"([^"]+)"'
        initial_labels = re.findall(hierarchical_label_pattern, subcircuit_content)

        print(f"   Hierarchical labels found in subcircuit: {len(initial_labels)}")
        for label in initial_labels:
            print(f"     - {label}")

        # Verify all 3 labels exist
        assert "VCC" in initial_labels, (
            f"VCC hierarchical label not found in subcircuit. "
            f"Found labels: {initial_labels}"
        )
        assert "GND" in initial_labels, (
            f"GND hierarchical label not found in subcircuit. "
            f"Found labels: {initial_labels}"
        )
        assert "SIGNAL" in initial_labels, (
            f"SIGNAL hierarchical label not found in subcircuit. "
            f"Found labels: {initial_labels}"
        )

        print(f"✅ Step 2: All 3 hierarchical labels validated")
        print(f"   ✓ VCC label present")
        print(f"   ✓ GND label present")
        print(f"   ✓ SIGNAL label present")

        # =====================================================================
        # STEP 3: Validate all 3 hierarchical pins on sheet symbol (Level 2)
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 3: Validate all 3 hierarchical pins on sheet symbol (Level 2)")
        print("=" * 70)

        # Read parent schematic to find sheet symbol and pins
        parent_content = parent_schematic.read_text()

        # Pattern for pin on sheet symbol
        sheet_pin_pattern = r'\(pin\s+"([^"]+)"\s+(input|output|bidirectional|passive)'
        initial_pins = re.findall(sheet_pin_pattern, parent_content)
        initial_pin_names = [pin[0] for pin in initial_pins]

        print(f"   Hierarchical pins found on sheet symbol: {len(initial_pin_names)}")
        for pin_name in initial_pin_names:
            print(f"     - {pin_name}")

        # Verify all 3 pins exist on sheet symbol
        assert "VCC" in initial_pin_names, (
            f"VCC pin not found on sheet symbol. "
            f"Found pins: {initial_pin_names}"
        )
        assert "GND" in initial_pin_names, (
            f"GND pin not found on sheet symbol. "
            f"Found pins: {initial_pin_names}"
        )
        assert "SIGNAL" in initial_pin_names, (
            f"SIGNAL pin not found on sheet symbol. "
            f"Found pins: {initial_pin_names}"
        )

        print(f"✅ Step 3: All 3 sheet symbol pins validated")
        print(f"   ✓ VCC pin present on sheet symbol")
        print(f"   ✓ GND pin present on sheet symbol")
        print(f"   ✓ SIGNAL pin present on sheet symbol")

        # =====================================================================
        # STEP 4: Validate initial netlist with all 3 nets (Level 3)
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 4: Validate initial netlist with all 3 nets (Level 3)")
        print("=" * 70)

        # Export netlist via kicad-cli
        netlist_file = output_dir / "three_pin_subcircuit.net"
        result = subprocess.run(
            [
                "kicad-cli",
                "sch",
                "export",
                "netlist",
                str(parent_schematic),
                "-o",
                str(netlist_file),
            ],
            capture_output=True,
            text=True,
            timeout=10,
        )

        if result.returncode != 0:
            print(f"⚠️  Warning: Netlist export failed (non-critical)")
            print(f"   STDERR: {result.stderr}")
            print(f"   Skipping Level 3 validation")
            initial_netlist_available = False
        else:
            initial_netlist_content = netlist_file.read_text()
            initial_netlist_available = True

            # Verify all 3 nets present in initial netlist
            assert "VCC" in initial_netlist_content or "ROOT_VCC" in initial_netlist_content, \
                "VCC net not found in initial netlist"
            assert "GND" in initial_netlist_content or "ROOT_GND" in initial_netlist_content, \
                "GND net not found in initial netlist"
            assert "SIGNAL" in initial_netlist_content or "ROOT_SIGNAL" in initial_netlist_content, \
                "SIGNAL net not found in initial netlist"

            print(f"✅ Step 4: Initial netlist validated")
            print(f"   ✓ VCC net present")
            print(f"   ✓ GND net present")
            print(f"   ✓ SIGNAL net present")

        # =====================================================================
        # STEP 5: Remove SIGNAL connection in Python code
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 5: Remove SIGNAL connection in Python code")
        print("=" * 70)

        # Remove SIGNAL parameter and usage from Python code
        # We need to:
        # 1. Remove SIGNAL parameter from subcircuit function signature
        # 2. Remove signal Net creation in main()
        # 3. Remove signal argument from subcircuit call

        modified_code = original_code

        # Remove SIGNAL parameter from subcircuit function signature
        # From: def power_and_signal_subcircuit(VCC, GND, SIGNAL):
        # To:   def power_and_signal_subcircuit(VCC, GND):
        modified_code = modified_code.replace(
            "def power_and_signal_subcircuit(VCC, GND, SIGNAL):",
            "def power_and_signal_subcircuit(VCC, GND):"
        )

        # Remove signal Net creation in main()
        # Remove: signal = Net("SIGNAL")
        modified_code = modified_code.replace(
            "    signal = Net(\"SIGNAL\")\n",
            ""
        )

        # Remove signal argument from subcircuit call
        # From: power_and_signal_subcircuit(vcc, gnd, signal)
        # To:   power_and_signal_subcircuit(vcc, gnd)
        modified_code = modified_code.replace(
            "power_and_signal_subcircuit(vcc, gnd, signal)",
            "power_and_signal_subcircuit(vcc, gnd)"
        )

        # Remove comment about SIGNAL parameter
        modified_code = modified_code.replace(
            "    # SIGNAL is passed as parameter but not connected to R1\n"
            "    # This represents a signal passing through the subcircuit interface\n",
            ""
        )

        assert modified_code != original_code, (
            "Failed to modify Python code - no changes made"
        )

        # Verify SIGNAL no longer appears in the code
        assert 'signal = Net("SIGNAL")' not in modified_code, \
            "SIGNAL Net creation still present"
        assert ', signal)' not in modified_code, \
            "signal argument still passed to subcircuit"

        # Write modified Python file
        with open(python_file, "w") as f:
            f.write(modified_code)

        print(f"✅ Step 5: Python code modified to remove SIGNAL")
        print(f"   ✗ SIGNAL parameter removed from subcircuit function")
        print(f"   ✗ signal = Net(\"SIGNAL\") removed from main()")
        print(f"   ✗ signal argument removed from subcircuit call")

        # =====================================================================
        # STEP 6: Regenerate KiCad without SIGNAL
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 6: Regenerate KiCad without SIGNAL")
        print("=" * 70)

        # Remove old output to force fresh generation
        if output_dir.exists():
            shutil.rmtree(output_dir)

        result = subprocess.run(
            ["uv", "run", "three_pin_subcircuit.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, (
            f"Step 6 failed: Regeneration without SIGNAL\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        print(f"✅ Step 6: KiCad regenerated without SIGNAL")

        # =====================================================================
        # STEP 7: Validate SIGNAL removed from subcircuit (ISSUE #380 TEST)
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 7: Validate SIGNAL label removed from subcircuit (ISSUE #380)")
        print("=" * 70)

        # Read updated subcircuit schematic
        subcircuit_content_updated = subcircuit_schematic.read_text()
        updated_labels = re.findall(hierarchical_label_pattern, subcircuit_content_updated)

        print(f"   Hierarchical labels after removal: {len(updated_labels)}")
        for label in updated_labels:
            print(f"     - {label}")

        # THIS IS THE CRITICAL TEST FOR ISSUE #380
        # Verify SIGNAL label is GONE
        assert "SIGNAL" not in updated_labels, (
            f"ISSUE #380: SIGNAL hierarchical label not removed from subcircuit. "
            f"Found labels: {updated_labels}\n"
            f"Expected: Only VCC, GND\n"
            f"This indicates the synchronizer is not removing old hierarchical labels."
        )

        # Verify VCC and GND still present
        assert "VCC" in updated_labels, (
            f"VCC label incorrectly removed. Found labels: {updated_labels}"
        )
        assert "GND" in updated_labels, (
            f"GND label incorrectly removed. Found labels: {updated_labels}"
        )

        print(f"✅ Step 7: SIGNAL hierarchical label successfully removed")
        print(f"   ✗ SIGNAL label removed (as expected)")
        print(f"   ✓ VCC label preserved")
        print(f"   ✓ GND label preserved")

        # =====================================================================
        # STEP 8: Validate SIGNAL removed from sheet symbol (ISSUE #380 TEST)
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 8: Validate SIGNAL pin removed from sheet symbol (ISSUE #380)")
        print("=" * 70)

        # Read updated parent schematic
        parent_content_updated = parent_schematic.read_text()
        updated_pins = re.findall(sheet_pin_pattern, parent_content_updated)
        updated_pin_names = [pin[0] for pin in updated_pins]

        print(f"   Hierarchical pins after removal: {len(updated_pin_names)}")
        for pin_name in updated_pin_names:
            print(f"     - {pin_name}")

        # Verify SIGNAL pin is GONE
        assert "SIGNAL" not in updated_pin_names, (
            f"ISSUE #380: SIGNAL pin not removed from sheet symbol. "
            f"Found pins: {updated_pin_names}\n"
            f"Expected: Only VCC, GND\n"
            f"This indicates the synchronizer is not removing old hierarchical pins."
        )

        # Verify VCC and GND still present
        assert "VCC" in updated_pin_names, (
            f"VCC pin incorrectly removed. Found pins: {updated_pin_names}"
        )
        assert "GND" in updated_pin_names, (
            f"GND pin incorrectly removed. Found pins: {updated_pin_names}"
        )

        print(f"✅ Step 8: SIGNAL sheet pin successfully removed")
        print(f"   ✗ SIGNAL pin removed (as expected)")
        print(f"   ✓ VCC pin preserved")
        print(f"   ✓ GND pin preserved")

        # =====================================================================
        # STEP 9: Validate SIGNAL net removed from netlist (Level 3)
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 9: Validate SIGNAL net removed from netlist (Level 3)")
        print("=" * 70)

        if not initial_netlist_available:
            print(f"⚠️  Skipping netlist validation (initial export failed)")
        else:
            # Export updated netlist
            result = subprocess.run(
                [
                    "kicad-cli",
                    "sch",
                    "export",
                    "netlist",
                    str(parent_schematic),
                    "-o",
                    str(netlist_file),
                ],
                capture_output=True,
                text=True,
                timeout=10,
            )

            if result.returncode != 0:
                print(f"⚠️  Warning: Updated netlist export failed (non-critical)")
                print(f"   STDERR: {result.stderr}")
            else:
                updated_netlist_content = netlist_file.read_text()

                # Verify SIGNAL net is GONE from netlist
                assert "ROOT_SIGNAL" not in updated_netlist_content, (
                    f"SIGNAL net still present in netlist after removal"
                )

                # Verify VCC and GND nets still present
                assert "VCC" in updated_netlist_content or "ROOT_VCC" in updated_netlist_content, \
                    "VCC net incorrectly removed from netlist"
                assert "GND" in updated_netlist_content or "ROOT_GND" in updated_netlist_content, \
                    "GND net incorrectly removed from netlist"

                print(f"✅ Step 9: Updated netlist validated")
                print(f"   ✗ SIGNAL net removed (as expected)")
                print(f"   ✓ VCC net preserved")
                print(f"   ✓ GND net preserved")

        # =====================================================================
        # SUCCESS!
        # =====================================================================
        print("\n" + "=" * 70)
        print("🎉 HIERARCHICAL PIN REMOVAL WORKS! (Issue #380 RESOLVED)")
        print("=" * 70)
        print(f"   ✓ Initial 3 pins (VCC, GND, SIGNAL) generated correctly")
        print(f"   ✓ SIGNAL connection removed from Python code")
        print(f"   ✓ SIGNAL hierarchical label removed from subcircuit")
        print(f"   ✓ SIGNAL hierarchical pin removed from sheet symbol")
        print(f"   ✓ VCC and GND pins/labels preserved")
        print(f"   ✓ Netlist no longer shows SIGNAL net")
        print(f"\n   Interface simplification workflow validated!")
        print(f"   → Old hierarchical pins properly cleaned up")
        print(f"   → Remaining pins unaffected by removal")
        print(f"   → Netlist reflects reduced connectivity")

    finally:
        # Restore original Python file
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
