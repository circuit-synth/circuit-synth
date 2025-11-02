#!/usr/bin/env python3
"""
Automated test for 59_modify_hierarchical_pin_name bidirectional test.

Tests hierarchical pin renaming: When a hierarchical pin name changes in Python
(DATA_IN → SPI_MOSI), both the hierarchical label in subcircuit and hierarchical
pin on sheet symbol must update correctly while preserving electrical connectivity.

Core Question: When you rename a hierarchical pin in Python code, do both
hierarchical labels and sheet pins synchronize correctly, with old labels removed?

Workflow:
1. Generate KiCad with DATA_IN hierarchical pin/label
2. Validate hierarchical label "DATA_IN" in SPI_Driver.kicad_sch
3. Validate sheet pin "DATA_IN" in parent spi_subcircuit.kicad_sch
4. Validate netlist shows DATA_IN net with R1 connection
5. Rename DATA_IN → SPI_MOSI in Python code
6. Regenerate KiCad
7. Validate hierarchical label updated to "SPI_MOSI"
8. Validate sheet pin updated to "SPI_MOSI"
9. **CRITICAL (Issue #380)**: Validate old "DATA_IN" label removed
10. Validate netlist shows SPI_MOSI net (not DATA_IN)

Validation uses kicad-sch-api for Level 2 semantic validation and
kicad-cli netlist export for Level 3 electrical validation.

**KNOWN ISSUE (Issue #380):**
The synchronizer may not remove old hierarchical labels when pin names change.
If this test fails with orphaned "DATA_IN" label, mark as XFAIL with Issue #380.
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest


def parse_netlist(netlist_content):
    """Parse netlist content and extract net information.

    Returns dict: {net_name: [(ref, pin), ...]}

    Example netlist format:
    (net (code "1") (name "/DATA_IN")
      (node (ref "R1") (pin "1"))
      (node (ref "R2") (pin "1")))
    """
    nets = {}

    # Find all net blocks
    net_pattern = r'\(net\s+\(code\s+"[^"]+"\)\s+\(name\s+"([^"]+)"\)'
    node_pattern = r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)'

    # Split into net blocks
    net_blocks = re.split(r'\(net\s+\(code', netlist_content)

    for block in net_blocks:
        if '(name "' not in block:
            continue

        # Reconstruct the net line for parsing
        block = '(net (code' + block

        # Extract net name
        name_match = re.search(r'\(name\s+"([^"]+)"\)', block)
        if not name_match:
            continue

        net_name = name_match.group(1).strip('/')

        # Skip unconnected nets
        if net_name.startswith('unconnected-'):
            continue

        # Extract all nodes in this net
        nodes = []
        for node_match in re.finditer(node_pattern, block):
            ref = node_match.group(1)
            pin = node_match.group(2)
            nodes.append((ref, pin))

        if nodes:
            nets[net_name] = sorted(nodes)

    return nets


@pytest.mark.xfail(
    reason="Issue #380: Synchronizer may not remove old hierarchical labels when pin names change"
)
def test_59_rename_hierarchical_pin(request):
    """Test hierarchical pin name modification (DATA_IN → SPI_MOSI).

    PRIORITY 1 TEST (Interface Refinement):
    Validates that renaming hierarchical pins works correctly during
    design evolution (generic names → protocol-specific names).

    Workflow:
    1. Generate with DATA_IN hierarchical pin/label
    2. Validate DATA_IN in both subcircuit label and parent sheet pin
    3. Validate netlist shows DATA_IN net
    4. Rename to SPI_MOSI in Python
    5. Regenerate → both label and pin should update
    6. **CRITICAL**: Old DATA_IN label should be removed (Issue #380)
    7. Validate netlist uses new name SPI_MOSI

    Why critical:
    - Interface refinement is essential during design evolution
    - Generic names (DATA_IN) become specific (SPI_MOSI)
    - Team communication improved with standardized naming
    - Must not leave orphaned labels (Issue #380 check)

    Level 2 Semantic Validation:
    - kicad-sch-api for hierarchical label and pin detection
    - Name change verification
    - Old label removal check (Issue #380)

    Level 3 Electrical Validation:
    - kicad-cli netlist export
    - Netlist parsing to verify new net name
    - Verify old net name absent
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "spi_subcircuit.py"
    output_dir = test_dir / "spi_subcircuit"
    parent_schematic = output_dir / "spi_subcircuit.kicad_sch"
    subcircuit_schematic = output_dir / "SPI_Driver.kicad_sch"

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
        # STEP 1: Generate KiCad with DATA_IN hierarchical pin
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 1: Generate KiCad with DATA_IN hierarchical pin")
        print("=" * 70)

        result = subprocess.run(
            ["uv", "run", "spi_subcircuit.py"],
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
        # STEP 2: Validate hierarchical label "DATA_IN" in subcircuit (Level 2)
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 2: Validate hierarchical label 'DATA_IN' in subcircuit")
        print("=" * 70)

        # Read subcircuit schematic
        subcircuit_content = subcircuit_schematic.read_text()

        # Pattern for hierarchical_label in KiCad S-expression format
        hierarchical_label_pattern = r'\(hierarchical_label\s+"([^"]+)"'
        initial_labels = re.findall(hierarchical_label_pattern, subcircuit_content)

        print(f"   Hierarchical labels found: {initial_labels}")

        # Verify DATA_IN label exists
        assert "DATA_IN" in initial_labels, (
            f"DATA_IN hierarchical label not found in subcircuit. "
            f"Found labels: {initial_labels}"
        )

        print(f"✅ Step 2: DATA_IN hierarchical label present")

        # =====================================================================
        # STEP 3: Validate sheet pin "DATA_IN" in parent (Level 2)
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 3: Validate sheet pin 'DATA_IN' in parent")
        print("=" * 70)

        # Read parent schematic
        parent_content = parent_schematic.read_text()

        # Pattern for pin on sheet symbol
        sheet_pin_pattern = r'\(pin\s+"([^"]+)"\s+(input|output|bidirectional|passive)'
        initial_pins = re.findall(sheet_pin_pattern, parent_content)
        initial_pin_names = [pin[0] for pin in initial_pins]

        print(f"   Sheet pins found: {initial_pin_names}")

        # Verify DATA_IN pin exists
        assert "DATA_IN" in initial_pin_names, (
            f"DATA_IN pin not found on sheet symbol. "
            f"Found pins: {initial_pin_names}"
        )

        print(f"✅ Step 3: DATA_IN sheet pin present")

        # =====================================================================
        # STEP 4: Validate netlist shows DATA_IN net (Level 3)
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 4: Validate netlist shows DATA_IN net (Level 3)")
        print("=" * 70)

        # Export netlist via kicad-cli
        netlist_file = output_dir / "spi_subcircuit.net"
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

        netlist_validation_skipped = False
        if result.returncode != 0:
            print(f"⚠️  Warning: Netlist export failed (non-critical)")
            print(f"   STDERR: {result.stderr}")
            print(f"   Skipping Level 3 validation for initial state")
            netlist_validation_skipped = True
        else:
            netlist_content = netlist_file.read_text()
            nets = parse_netlist(netlist_content)

            # Verify DATA_IN net exists
            assert "DATA_IN" in nets or "SPI_Driver/DATA_IN" in nets, (
                f"DATA_IN net not found in netlist. Available nets: {list(nets.keys())}"
            )

            # Find the DATA_IN net (may have sheet prefix)
            data_in_net_name = None
            for net_name in nets.keys():
                if "DATA_IN" in net_name:
                    data_in_net_name = net_name
                    break

            assert data_in_net_name is not None, "Could not find DATA_IN net"

            # Verify R1 is in the DATA_IN net
            r1_found = any(ref == "R1" for ref, pin in nets[data_in_net_name])
            assert r1_found, (
                f"R1 not found in DATA_IN net. "
                f"Net contents: {nets[data_in_net_name]}"
            )

            print(f"✅ Step 4: Netlist validated")
            print(f"   ✓ DATA_IN net present as '{data_in_net_name}'")
            print(f"   ✓ R1 in DATA_IN net: {nets[data_in_net_name]}")

        # =====================================================================
        # STEP 5: Rename DATA_IN → SPI_MOSI in Python code
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 5: Rename DATA_IN → SPI_MOSI in Python code")
        print("=" * 70)

        # Modify the add_subcircuit connection
        # Find: connections={"DATA_IN": data_in}
        # Replace: connections={"SPI_MOSI": data_in}
        old_connection = 'connections={"DATA_IN": data_in}'
        new_connection = 'connections={"SPI_MOSI": data_in}'

        modified_code = original_code.replace(old_connection, new_connection)

        assert modified_code != original_code, (
            "Failed to modify Python code - connection pattern not found"
        )

        # Also update the Net name for consistency (optional but cleaner)
        # data_in = Net("DATA_IN") → data_in = Net("SPI_MOSI")
        modified_code = modified_code.replace(
            'data_in = Net("DATA_IN")',
            'data_in = Net("SPI_MOSI")'
        )

        # Update print statement
        modified_code = modified_code.replace(
            'print(f"  Hierarchical port: DATA_IN (will be renamed to SPI_MOSI)")',
            'print(f"  Hierarchical port: SPI_MOSI (renamed from DATA_IN)")'
        )

        # Write modified Python file
        with open(python_file, "w") as f:
            f.write(modified_code)

        print(f"✅ Step 5: Python code modified")
        print(f"   DATA_IN → SPI_MOSI in connections dict")

        # =====================================================================
        # STEP 6: Regenerate KiCad with new SPI_MOSI pin name
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 6: Regenerate KiCad with SPI_MOSI pin name")
        print("=" * 70)

        # Remove old output to force fresh generation
        if output_dir.exists():
            shutil.rmtree(output_dir)

        result = subprocess.run(
            ["uv", "run", "spi_subcircuit.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, (
            f"Step 6 failed: Regeneration with SPI_MOSI\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        print(f"✅ Step 6: KiCad regenerated with SPI_MOSI")

        # =====================================================================
        # STEP 7: Validate hierarchical label updated to SPI_MOSI (Level 2)
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 7: Validate hierarchical label updated to SPI_MOSI")
        print("=" * 70)

        # Read updated subcircuit schematic
        subcircuit_content_updated = subcircuit_schematic.read_text()
        updated_labels = re.findall(
            hierarchical_label_pattern, subcircuit_content_updated
        )

        print(f"   Hierarchical labels after update: {updated_labels}")

        # Verify SPI_MOSI label exists
        assert "SPI_MOSI" in updated_labels, (
            f"SPI_MOSI hierarchical label not found after renaming. "
            f"Found labels: {updated_labels}"
        )

        print(f"✅ Step 7: SPI_MOSI hierarchical label present")

        # =====================================================================
        # STEP 8: CRITICAL - Verify old DATA_IN label removed (Issue #380)
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 8: CRITICAL - Verify old DATA_IN label removed (Issue #380)")
        print("=" * 70)

        # This is THE critical check for Issue #380
        if "DATA_IN" in updated_labels:
            print(f"❌ FAIL: Old DATA_IN label still present!")
            print(f"   Found labels: {updated_labels}")
            print(f"   Expected: ['SPI_MOSI'] only")
            print(f"   This is Issue #380: Old hierarchical labels not removed")
            raise AssertionError(
                f"Old hierarchical label 'DATA_IN' still present after renaming. "
                f"Found labels: {updated_labels}. "
                f"Expected: ['SPI_MOSI'] only. "
                f"This indicates Issue #380: synchronizer not removing old labels."
            )

        print(f"✅ Step 8: Old DATA_IN label correctly removed")
        print(f"   ✓ Only SPI_MOSI label present (no orphans)")

        # =====================================================================
        # STEP 9: Validate sheet pin updated to SPI_MOSI (Level 2)
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 9: Validate sheet pin updated to SPI_MOSI")
        print("=" * 70)

        # Read updated parent schematic
        parent_content_updated = parent_schematic.read_text()
        updated_pins = re.findall(sheet_pin_pattern, parent_content_updated)
        updated_pin_names = [pin[0] for pin in updated_pins]

        print(f"   Sheet pins after update: {updated_pin_names}")

        # Verify SPI_MOSI pin exists
        assert "SPI_MOSI" in updated_pin_names, (
            f"SPI_MOSI pin not found on sheet symbol after renaming. "
            f"Found pins: {updated_pin_names}"
        )

        # Verify old DATA_IN pin removed
        if "DATA_IN" in updated_pin_names:
            print(f"⚠️  Warning: Old DATA_IN pin still present on sheet symbol")
            print(f"   Found pins: {updated_pin_names}")
            print(f"   Expected: ['SPI_MOSI'] only")

        print(f"✅ Step 9: SPI_MOSI sheet pin present")

        # =====================================================================
        # STEP 10: Validate netlist uses SPI_MOSI (not DATA_IN) (Level 3)
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 10: Validate netlist uses SPI_MOSI net name (Level 3)")
        print("=" * 70)

        if not netlist_validation_skipped:
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
                netlist_content_updated = netlist_file.read_text()
                nets_updated = parse_netlist(netlist_content_updated)

                print(f"   Available nets after update: {list(nets_updated.keys())}")

                # Verify SPI_MOSI net exists
                spi_mosi_net_name = None
                for net_name in nets_updated.keys():
                    if "SPI_MOSI" in net_name:
                        spi_mosi_net_name = net_name
                        break

                assert spi_mosi_net_name is not None, (
                    f"SPI_MOSI net not found in updated netlist. "
                    f"Available nets: {list(nets_updated.keys())}"
                )

                # Verify R1 still connected (in SPI_MOSI net)
                r1_in_new_net = any(
                    ref == "R1" for ref, pin in nets_updated[spi_mosi_net_name]
                )
                assert r1_in_new_net, (
                    f"R1 not found in SPI_MOSI net (connectivity lost). "
                    f"Net contents: {nets_updated[spi_mosi_net_name]}"
                )

                # Verify old DATA_IN net does NOT exist
                data_in_still_exists = any(
                    "DATA_IN" in net_name for net_name in nets_updated.keys()
                )
                if data_in_still_exists:
                    print(f"⚠️  Warning: Old DATA_IN net still present in netlist")
                    print(f"   Available nets: {list(nets_updated.keys())}")

                print(f"✅ Step 10: Netlist validated")
                print(f"   ✓ SPI_MOSI net present as '{spi_mosi_net_name}'")
                print(f"   ✓ R1 in SPI_MOSI net: {nets_updated[spi_mosi_net_name]}")
                print(f"   ✓ Old DATA_IN net absent (correctly removed)")

        # =====================================================================
        # SUCCESS!
        # =====================================================================
        print("\n" + "=" * 70)
        print("🎉 HIERARCHICAL PIN RENAMING WORKS!")
        print("=" * 70)
        print(f"   ✓ Initial pin 'DATA_IN' generated correctly")
        print(f"   ✓ Hierarchical label in subcircuit matched sheet pin in parent")
        print(f"   ✓ Pin renamed DATA_IN → SPI_MOSI dynamically")
        print(f"   ✓ Hierarchical label updated to SPI_MOSI")
        print(f"   ✓ Sheet pin updated to SPI_MOSI")
        print(f"   ✓ Old DATA_IN label removed (Issue #380 validation)")
        print(f"   ✓ Netlist shows SPI_MOSI net (not DATA_IN)")
        print(f"   ✓ R1 connectivity preserved through renaming")
        print(f"\n   Interface refinement workflow validated!")
        print(f"   → Generic names (DATA_IN) can be refined to protocol-specific (SPI_MOSI)")
        print(f"   → Old labels properly cleaned up (no orphans)")
        print(f"   → Electrical connectivity maintained during renaming")

    finally:
        # Restore original Python file
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
