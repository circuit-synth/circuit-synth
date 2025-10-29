#!/usr/bin/env python3
"""
Automated test for 43_differential_pairs bidirectional test.

Tests CRITICAL real-world pattern: USB differential pairs with D+ and D- signals.

This validates that you can:
1. Generate circuit with USB differential pair (USB_DP and USB_DM)
2. Both nets created and connected properly
3. Verify correct pins are connected (Level 3 netlist analysis)
4. Modify one differential signal in Python
5. Regenerate → only modified signal changes
6. Other differential signal unaffected, pair relationship preserved

This is essential for USB, LVDS, HDMI, and other high-speed communication designs.

Workflow:
1. Generate with USB connector and transceiver connected via differential pair
2. Verify both USB_DP and USB_DM nets in schematic and netlist
3. Verify correct pin connections via Level 3 netlist parsing
4. Modify one differential signal (e.g., change transceiver pin)
5. Regenerate
6. Validate:
   - USB_DP has modified connections
   - USB_DM has original connections (unchanged)
   - Both nets present and valid
   - Positions preserved
   - Netlist comparison confirms modification

Validation uses:
- kicad-sch-api for schematic structure
- Netlist parsing for connection verification
- Pin-to-pin electrical connectivity analysis
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
    (net (code "1") (name "/USB_DP")
      (node (ref "J1") (pin "3"))
      (node (ref "U1") (pin "3")))
    """
    import re

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


@pytest.mark.xfail(reason="Issue #373: Netlist exporter missing nodes - circuit-synth .net file has empty nets section")
def test_43_differential_pairs_comprehensive(request):
    """Test USB differential pair generation and modification.

    CRITICAL REAL-WORLD PATTERN:
    Validates that high-speed communication circuits with differential pairs work:
    - Two paired nets (USB_DP and USB_DM) for differential signaling
    - USB connector and transceiver components properly connected
    - Can modify individual differential signals without losing pair
    - Pair relationship and naming preserved through regeneration

    This workflow is essential for:
    - USB circuits (all USB versions require differential pairs)
    - LVDS (Low-Voltage Differential Signaling)
    - HDMI, DisplayPort, and other high-speed protocols
    - Iterative board design with differential routing changes

    Validation covers:
    - Level 1: File generation (schematic exists)
    - Level 2: Schematic structure (components, labels)
    - Level 3: Electrical connectivity (netlist verification)
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "usb_differential_pair.py"
    output_dir = test_dir / "usb_differential_pair"
    schematic_file = output_dir / "usb_differential_pair.kicad_sch"

    # Netlist files
    synth_netlist_file = output_dir / "usb_differential_pair.net"
    kicad_netlist_file = output_dir / "usb_differential_pair_kicad.net"

    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    # Clean any existing output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    try:
        # =====================================================================
        # STEP 1: Generate KiCad with USB differential pair
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate KiCad with USB differential pair (DP and DM)")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "usb_differential_pair.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 1 failed: Initial generation\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        assert schematic_file.exists(), "Schematic not created"
        assert synth_netlist_file.exists(), "Circuit-synth netlist not created"

        print(f"✅ Step 1: KiCad project generated")
        print(f"   - Schematic: {schematic_file.name}")
        print(f"   - Netlist: {synth_netlist_file.name}")

        # =====================================================================
        # STEP 2: Validate schematic structure with kicad-sch-api
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Validate schematic structure (components and labels)")
        print("="*70)

        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        # Validate components exist
        assert len(components) >= 2, (
            f"Expected at least 2 components (USB connector + transceiver), "
            f"found {len(components)}"
        )

        refs = {c.reference for c in components}
        assert "J1" in refs, f"Expected USB connector (J1), found refs: {refs}"
        assert "U1" in refs, f"Expected transceiver (U1), found refs: {refs}"

        # Validate hierarchical labels exist for differential pair
        with open(schematic_file, 'r') as f:
            sch_content = f.read()

        usb_dp_labels = sch_content.count('hierarchical_label "USB_DP"')
        usb_dm_labels = sch_content.count('hierarchical_label "USB_DM"')

        assert usb_dp_labels >= 2, (
            f"Expected at least 2 USB_DP hierarchical labels, found {usb_dp_labels}"
        )
        assert usb_dm_labels >= 2, (
            f"Expected at least 2 USB_DM hierarchical labels, found {usb_dm_labels}"
        )

        print(f"✅ Step 2: Schematic structure validated")
        print(f"   - Components: {refs}")
        print(f"   - USB_DP labels: {usb_dp_labels}")
        print(f"   - USB_DM labels: {usb_dm_labels}")

        # =====================================================================
        # STEP 3: Export netlist using kicad-cli
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Export netlist using kicad-cli")
        print("="*70)

        result = subprocess.run(
            [
                "kicad-cli", "sch", "export", "netlist",
                str(schematic_file),
                "--output", str(kicad_netlist_file)
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"kicad-cli netlist export failed\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        assert kicad_netlist_file.exists(), "KiCad netlist not created"

        print(f"✅ Step 3: KiCad netlist exported")
        print(f"   - File: {kicad_netlist_file.name}")

        # =====================================================================
        # STEP 4: Parse both netlists (LEVEL 3 VALIDATION)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 4: Parse and compare netlists (LEVEL 3 ELECTRICAL VALIDATION)")
        print("="*70)

        # Read circuit-synth netlist
        with open(synth_netlist_file, 'r') as f:
            synth_netlist_content = f.read()

        # Read KiCad-exported netlist
        with open(kicad_netlist_file, 'r') as f:
            kicad_netlist_content = f.read()

        # Parse both netlists
        synth_nets = parse_netlist(synth_netlist_content)
        kicad_nets = parse_netlist(kicad_netlist_content)

        print(f"\n📊 Circuit-synth netlist:")
        print(f"   Nets found: {list(synth_nets.keys())}")
        for net_name in sorted(synth_nets.keys()):
            nodes = synth_nets[net_name]
            print(f"   - {net_name}: {nodes}")

        print(f"\n📊 KiCad-exported netlist:")
        print(f"   Nets found: {list(kicad_nets.keys())}")
        for net_name in sorted(kicad_nets.keys()):
            nodes = kicad_nets[net_name]
            print(f"   - {net_name}: {nodes}")

        # =====================================================================
        # STEP 5: Validate differential pair electrical connectivity
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 5: Validate differential pair connectivity")
        print("="*70)

        # Check that USB_DP exists in circuit-synth netlist
        assert "USB_DP" in synth_nets, (
            f"USB_DP missing from circuit-synth netlist!\n"
            f"Found nets: {list(synth_nets.keys())}\n"
            f"This is Issue #373 - netlist exporter missing nodes"
        )

        # Check that USB_DM exists in circuit-synth netlist
        assert "USB_DM" in synth_nets, (
            f"USB_DM missing from circuit-synth netlist!\n"
            f"Found nets: {list(synth_nets.keys())}\n"
            f"This is Issue #373 - netlist exporter missing nodes"
        )

        # Validate USB_DP pin connections
        # Should connect J1 (USB connector) pin 3 and U1 (transceiver) pin 4
        expected_dp_nodes = [("J1", "3"), ("U1", "4")]
        actual_dp_nodes = synth_nets.get("USB_DP", [])

        assert sorted(actual_dp_nodes) == sorted(expected_dp_nodes), (
            f"USB_DP nodes mismatch!\n"
            f"Expected: {sorted(expected_dp_nodes)}\n"
            f"Got:      {sorted(actual_dp_nodes)}"
        )

        # Validate USB_DM pin connections
        # Should connect J1 (USB connector) pin 2 and U1 (transceiver) pin 6
        expected_dm_nodes = [("J1", "2"), ("U1", "6")]
        actual_dm_nodes = synth_nets.get("USB_DM", [])

        assert sorted(actual_dm_nodes) == sorted(expected_dm_nodes), (
            f"USB_DM nodes mismatch!\n"
            f"Expected: {sorted(expected_dm_nodes)}\n"
            f"Got:      {sorted(actual_dm_nodes)}"
        )

        # Validate KiCad netlist also has the differential pair
        assert "USB_DP" in kicad_nets, (
            f"USB_DP missing from KiCad netlist (unexpected!)"
        )
        assert "USB_DM" in kicad_nets, (
            f"USB_DM missing from KiCad netlist (unexpected!)"
        )

        kicad_dp_nodes = kicad_nets.get("USB_DP", [])
        kicad_dm_nodes = kicad_nets.get("USB_DM", [])

        assert sorted(kicad_dp_nodes) == sorted(expected_dp_nodes), (
            f"KiCad USB_DP nodes unexpected!\n"
            f"Expected: {sorted(expected_dp_nodes)}\n"
            f"Got:      {sorted(kicad_dp_nodes)}"
        )

        assert sorted(kicad_dm_nodes) == sorted(expected_dm_nodes), (
            f"KiCad USB_DM nodes unexpected!\n"
            f"Expected: {sorted(expected_dm_nodes)}\n"
            f"Got:      {sorted(kicad_dm_nodes)}"
        )

        print(f"✅ Step 5: Differential pair connectivity VALIDATED!")
        print(f"   - USB_DP (circuit-synth): {actual_dp_nodes}")
        print(f"   - USB_DM (circuit-synth): {actual_dm_nodes}")
        print(f"   - USB_DP (KiCad):         {kicad_dp_nodes}")
        print(f"   - USB_DM (KiCad):         {kicad_dm_nodes}")

        # =====================================================================
        # STEP 6: Modify one differential signal and regenerate
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 6: Modify USB_DP signal and regenerate")
        print("="*70)

        # Create modified version that changes USB_DP connection
        modified_python = python_file.read_text()
        # Change U1 pin 4 to pin 10 for USB_DP (simulating pin reassignment)
        modified_python = modified_python.replace(
            'usb_dp_net += transceiver[4]   # Transceiver 1Y (output) pin',
            'usb_dp_net += transceiver[10]  # Transceiver 3Y (output) pin (modified)'
        )

        # Write modified version
        modified_file = test_dir / "usb_differential_pair_modified.py"
        modified_file.write_text(modified_python)

        # Regenerate with modified version
        result = subprocess.run(
            ["uv", "run", "usb_differential_pair_modified.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 6 failed: Regeneration with modification\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        print(f"✅ Step 6: Modified circuit regenerated")
        print(f"   - USB_DP now connects to U1 pin 10 (instead of pin 4)")

        # =====================================================================
        # STEP 7: Verify modification preserved pair and updated connection
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 7: Verify modification (USB_DM unchanged, USB_DP updated)")
        print("="*70)

        # Export new netlist
        result = subprocess.run(
            [
                "kicad-cli", "sch", "export", "netlist",
                str(schematic_file),
                "--output", str(kicad_netlist_file)
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, "Failed to export modified netlist"

        # Parse modified netlist
        with open(kicad_netlist_file, 'r') as f:
            modified_netlist_content = f.read()

        modified_nets = parse_netlist(modified_netlist_content)

        # USB_DP should now have different connections (U1 pin 10)
        expected_modified_dp_nodes = [("J1", "3"), ("U1", "10")]
        actual_modified_dp_nodes = modified_nets.get("USB_DP", [])

        assert sorted(actual_modified_dp_nodes) == sorted(expected_modified_dp_nodes), (
            f"USB_DP not modified as expected!\n"
            f"Expected: {sorted(expected_modified_dp_nodes)}\n"
            f"Got:      {sorted(actual_modified_dp_nodes)}"
        )

        # USB_DM should remain unchanged
        actual_modified_dm_nodes = modified_nets.get("USB_DM", [])

        assert sorted(actual_modified_dm_nodes) == sorted(expected_dm_nodes), (
            f"USB_DM was unexpectedly modified!\n"
            f"Expected: {sorted(expected_dm_nodes)}\n"
            f"Got:      {sorted(actual_modified_dm_nodes)}"
        )

        print(f"✅ Step 7: Modification validated!")
        print(f"   - USB_DP modified: {actual_modified_dp_nodes} ✓")
        print(f"   - USB_DM unchanged: {actual_modified_dm_nodes} ✓")
        print(f"   - Differential pair relationship preserved ✓")
        print(f"\n🎉 Differential pair handling confirmed!")
        print(f"   USB_DP and USB_DM form a proper differential pair")
        print(f"   Individual signals can be modified independently")
        print(f"   Pair relationship is preserved through regeneration")

    finally:
        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)

        # Cleanup modified fixture
        modified_file = test_dir / "usb_differential_pair_modified.py"
        if modified_file.exists():
            modified_file.unlink()


def test_43_visual_validation_only(request):
    """Test 43 visual validation (without full netlist comparison).

    This test validates schematic structure without requiring
    working netlist export. It will pass even with Issue #373.

    Validates:
    - USB connector and transceiver components exist
    - USB_DP and USB_DM hierarchical labels exist
    - No component overlap

    Does NOT validate:
    - Actual electrical connectivity (requires netlist comparison)
    - Pin-to-pin connections
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "usb_differential_pair.py"
    output_dir = test_dir / "usb_differential_pair"
    schematic_file = output_dir / "usb_differential_pair.kicad_sch"

    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    # Clean any existing output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    try:
        # Generate
        result = subprocess.run(
            ["uv", "run", "usb_differential_pair.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Generation failed\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        assert schematic_file.exists(), "Schematic not created"

        # Validate schematic structure
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        assert len(components) >= 2, (
            f"Expected at least 2 components, found {len(components)}"
        )

        refs = {c.reference for c in components}
        assert "J1" in refs, f"Expected J1 (USB connector), found: {refs}"
        assert "U1" in refs, f"Expected U1 (transceiver), found: {refs}"

        # Check for hierarchical labels
        with open(schematic_file, 'r') as f:
            sch_content = f.read()

        usb_dp_labels = sch_content.count('hierarchical_label "USB_DP"')
        usb_dm_labels = sch_content.count('hierarchical_label "USB_DM"')

        assert usb_dp_labels >= 2, (
            f"Expected at least 2 USB_DP labels, found {usb_dp_labels}"
        )
        assert usb_dm_labels >= 2, (
            f"Expected at least 2 USB_DM labels, found {usb_dm_labels}"
        )

        print(f"\n✅ Visual validation passed:")
        print(f"   - Components: {refs}")
        print(f"   - USB_DP labels: {usb_dp_labels}")
        print(f"   - USB_DM labels: {usb_dm_labels}")
        print(f"\n⚠️  Note: This test does NOT validate electrical connectivity")
        print(f"   Use test_43_differential_pairs_comprehensive for full validation")

    finally:
        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
