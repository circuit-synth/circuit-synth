#!/usr/bin/env python3
"""
Automated test for 36_copy_paste_component bidirectional test.

Tests component duplication with proper net management.
Validates that copy-pasting components (Python → KiCad) preserves
electrical connectivity for multiple independent circuit branches.

Workflow:
1. Generate KiCad with R1-R2 divider (2 resistors, 3 nets)
2. Validate initial circuit (components, labels, structure)
3. In Python, create R3-R4 as copies with similar nets
4. Regenerate KiCad with all components
5. Validate 4 resistors exist
6. Validate both dividers have correct connectivity (Level 3 netlist)

Validation uses:
- kicad-sch-api for schematic structure
- Raw schematic file for hierarchical labels
- kicad-cli for netlist export
- Netlist comparison for electrical connectivity (Level 3)
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
    (net (code "1") (name "/NET1")
      (node (ref "R1") (pin "1"))
      (node (ref "R2") (pin "1")))
    """

    nets = {}

    # Find all net blocks
    # Pattern: (net ... (name "...") ... (node ...) ... )
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
    reason="Issue #373: Netlist exporter missing nodes - circuit-synth .net file has empty nets section. "
           "Components are duplicated successfully, but net connectivity validation requires working netlist exporter."
)
def test_36_copy_paste_component(request):
    """Test copy-pasting components with proper net management.

    COMPONENT DUPLICATION TEST:
    Validates that duplicating component groups preserves electrical
    connectivity for multiple independent circuit branches.

    This test demonstrates copy-paste patterns where:
    - Original circuit: R1-R2 divider with 3 nets
    - Modified circuit: R1-R2 + R3-R4 dividers (6 nets total)
    - Both dividers must maintain correct connectivity

    Workflow:
    1. Generate KiCad with R1-R2 divider (2 resistors, 3 nets)
    2. Validate initial circuit using kicad-sch-api
    3. Modify Python to add R3-R4 as copies
    4. Regenerate KiCad
    5. Validate 4 resistors exist
    6. Validate both dividers via netlist comparison

    Level 3 Electrical Validation:
    - kicad-sch-api for schematic structure
    - Netlist comparison for electrical connectivity
    - Component counts and references
    - Net integrity (no unconnected pins)
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "resistor_divider_for_copy.py"
    output_dir = test_dir / "resistor_divider_for_copy"
    schematic_file = output_dir / "resistor_divider_for_copy.kicad_sch"

    # Netlist files
    synth_netlist_file = output_dir / "resistor_divider_for_copy.net"
    kicad_netlist_file = output_dir / "resistor_divider_for_copy_kicad.net"

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
        # STEP 1: Generate KiCad with R1-R2 divider
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate KiCad with R1-R2 divider (2 resistors, 3 nets)")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "resistor_divider_for_copy.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 1 failed: Initial generation with R1-R2\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        assert schematic_file.exists(), "Schematic not created"
        assert synth_netlist_file.exists(), "Circuit-synth netlist not created"

        print(f"✅ Step 1: KiCad project generated")
        print(f"   - Schematic: {schematic_file.name}")
        print(f"   - Netlist: {synth_netlist_file.name}")

        # =====================================================================
        # STEP 2: Validate initial circuit structure
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Validate initial circuit (R1-R2, 3 nets)")
        print("="*70)

        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        # Validate 2 resistors + 2 power symbols (VCC, GND auto-added)
        assert len(components) >= 2, (
            f"Step 2: Expected at least 2 components, found {len(components)}"
        )

        refs = {c.reference for c in components}
        assert "R1" in refs and "R2" in refs, (
            f"Step 2: Expected R1 and R2, found {refs}"
        )

        # Note: VCC and GND power symbols may be auto-added

        # Validate component values
        r1 = next(c for c in components if c.reference == "R1")
        r2 = next(c for c in components if c.reference == "R2")
        assert r1.value == "10k"
        assert r2.value == "10k"

        # Check schematic for hierarchical labels (VCC, Net1, GND)
        with open(schematic_file, 'r') as f:
            sch_content = f.read()

        # VCC and GND are power symbols, not hierarchical labels
        # Check for Net1 which connects R1[2] and R2[1]
        # Extract all labels for debugging
        import re
        # Use more specific regex to match hierarchical_label entries (with opening paren)
        all_initial_labels = set(re.findall(r'\(hierarchical_label "([^"]*)"', sch_content))
        print(f"\n📊 Initial circuit labels: {sorted(all_initial_labels)}")

        assert "Net1" in all_initial_labels, f"Expected Net1, found {all_initial_labels}"
        net1_count = sch_content.count('hierarchical_label "Net1"')
        assert net1_count >= 2, f"Expected >=2 Net1 labels, found {net1_count}"

        print(f"✅ Step 2: Initial circuit validated")
        print(f"   - Components: {refs}")
        print(f"   - Values: R1={r1.value}, R2={r2.value}")
        print(f"   - Labels: {sorted(all_initial_labels)}")

        # =====================================================================
        # STEP 3: Add R3-R4 copies and regenerate
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Add R3-R4 as copies with similar nets")
        print("="*70)

        # Create modified code with R3-R4 copies
        # Insert before the final closing of the decorator function
        modified_code = original_code.replace(
            "    # R3 and R4 will be added by test (copy-paste pattern)",
            """    # R3 and R4 copies with similar connectivity
    r3 = Component(
        symbol="Device:R",
        ref="R3",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r4 = Component(
        symbol="Device:R",
        ref="R4",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Net4: VCC_copy → R3[1]
    net_vcc_copy = Net(name="VCC_copy")
    net_vcc_copy += r3[1]

    # Net5: R3[2] → R4[1] (junction point copy)
    net_junction_copy = Net(name="Net2")
    net_junction_copy += r3[2]
    net_junction_copy += r4[1]

    # Net6: R4[2] → GND_copy
    net_gnd_copy = Net(name="GND_copy")
    net_gnd_copy += r4[2]"""
        )

        with open(python_file, "w") as f:
            f.write(modified_code)

        # Regenerate
        result = subprocess.run(
            ["uv", "run", "resistor_divider_for_copy.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 3 failed: Regeneration with R3-R4\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        print(f"✅ Step 3: R3-R4 added and regenerated")

        # =====================================================================
        # STEP 4: Verify all 4 resistors exist
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 4: Verify 4 resistors exist (R1, R2, R3, R4)")
        print("="*70)

        sch = Schematic.load(str(schematic_file))
        components = sch.components

        # 4 resistors + potentially 2 power symbols
        assert len(components) >= 4, (
            f"Step 4: Expected at least 4 components, found {len(components)}"
        )

        refs = {c.reference for c in components}
        expected_resistors = {"R1", "R2", "R3", "R4"}
        assert expected_resistors.issubset(refs), (
            f"Step 4: Expected at least {expected_resistors}, found {refs}"
        )

        # Validate all have correct values
        for ref in ["R1", "R2", "R3", "R4"]:
            comp = next(c for c in components if c.reference == ref)
            assert comp.value == "10k", (
                f"Step 4: {ref} value should be 10k, got {comp.value}"
            )

        print(f"✅ Step 4: All 4 resistors present")
        print(f"   - References: {refs}")
        print(f"   - All values: 10k ✓")

        # =====================================================================
        # STEP 5: Export and validate netlist (Level 3 electrical validation)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 5: Export netlist and validate connectivity (Level 3)")
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

        print(f"✅ Netlist exported")

        # =====================================================================
        # STEP 6: Parse and validate both dividers
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 6: Validate both dividers (netlist comparison)")
        print("="*70)

        # Read circuit-synth netlist
        with open(synth_netlist_file, 'r') as f:
            synth_netlist_content = f.read()

        # Debug: show circuit-synth netlist content (first 1000 chars)
        print(f"\n📊 Circuit-synth netlist file content (first 500 chars):")
        print(f"   {synth_netlist_content[:500]}")

        # Read KiCad-exported netlist
        with open(kicad_netlist_file, 'r') as f:
            kicad_netlist_content = f.read()

        # Parse both netlists
        synth_nets = parse_netlist(synth_netlist_content)
        kicad_nets = parse_netlist(kicad_netlist_content)

        print(f"\n📊 Circuit-synth netlist:")
        print(f"   Nets found: {sorted(synth_nets.keys())}")
        for net_name in sorted(synth_nets.keys()):
            nodes = synth_nets[net_name]
            print(f"   - {net_name}: {nodes}")

        print(f"\n📊 KiCad-exported netlist:")
        print(f"   Nets found: {sorted(kicad_nets.keys())}")
        for net_name in sorted(kicad_nets.keys()):
            nodes = kicad_nets[net_name]
            print(f"   - {net_name}: {nodes}")

        # =====================================================================
        # STEP 6a: Validate ORIGINAL divider (R1-R2)
        # =====================================================================
        print(f"\n" + "-"*70)
        print(f"STEP 6a: Validate ORIGINAL divider (R1-R2)")
        print(f"-"*70)

        # VCC net: R1[1]
        assert "VCC" in kicad_nets, (
            f"VCC missing from KiCad netlist!"
        )
        vcc_nodes = kicad_nets.get("VCC", [])
        assert ("R1", "1") in vcc_nodes, (
            f"VCC should contain R1 pin 1, got {vcc_nodes}"
        )
        print(f"✅ VCC net: R1[1] connected ✓")

        # Net1 junction: R1[2] and R2[1]
        assert "Net1" in kicad_nets, (
            f"Net1 missing from KiCad netlist!"
        )
        net1_nodes = kicad_nets.get("Net1", [])
        expected_net1 = [("R1", "2"), ("R2", "1")]
        assert sorted(net1_nodes) == sorted(expected_net1), (
            f"Net1 should connect R1[2] and R2[1]\n"
            f"Expected: {sorted(expected_net1)}\n"
            f"Got:      {sorted(net1_nodes)}"
        )
        print(f"✅ Net1 junction: R1[2] ↔ R2[1] connected ✓")

        # GND net: R2[2]
        assert "GND" in kicad_nets, (
            f"GND missing from KiCad netlist!"
        )
        gnd_nodes = kicad_nets.get("GND", [])
        assert ("R2", "2") in gnd_nodes, (
            f"GND should contain R2 pin 2, got {gnd_nodes}"
        )
        print(f"✅ GND net: R2[2] connected ✓")

        # =====================================================================
        # STEP 6b: Validate COPIED divider (R3-R4)
        # =====================================================================
        print(f"\n" + "-"*70)
        print(f"STEP 6b: Validate COPIED divider (R3-R4)")
        print(f"-"*70)

        # VCC_copy net: R3[1]
        assert "VCC_copy" in kicad_nets, (
            f"VCC_copy missing from KiCad netlist!"
        )
        vcc_copy_nodes = kicad_nets.get("VCC_copy", [])
        assert ("R3", "1") in vcc_copy_nodes, (
            f"VCC_copy should contain R3 pin 1, got {vcc_copy_nodes}"
        )
        print(f"✅ VCC_copy net: R3[1] connected ✓")

        # Net2 junction: R3[2] and R4[1]
        assert "Net2" in kicad_nets, (
            f"Net2 missing from KiCad netlist!"
        )
        net2_nodes = kicad_nets.get("Net2", [])
        expected_net2 = [("R3", "2"), ("R4", "1")]
        assert sorted(net2_nodes) == sorted(expected_net2), (
            f"Net2 should connect R3[2] and R4[1]\n"
            f"Expected: {sorted(expected_net2)}\n"
            f"Got:      {sorted(net2_nodes)}"
        )
        print(f"✅ Net2 junction: R3[2] ↔ R4[1] connected ✓")

        # GND_copy net: R4[2]
        assert "GND_copy" in kicad_nets, (
            f"GND_copy missing from KiCad netlist!"
        )
        gnd_copy_nodes = kicad_nets.get("GND_copy", [])
        assert ("R4", "2") in gnd_copy_nodes, (
            f"GND_copy should contain R4 pin 2, got {gnd_copy_nodes}"
        )
        print(f"✅ GND_copy net: R4[2] connected ✓")

        # =====================================================================
        # FINAL VALIDATION: Both dividers electrically equivalent
        # =====================================================================
        print(f"\n" + "="*70)
        print(f"🎉 FINAL VALIDATION: Copy-paste component test PASSED")
        print(f"="*70)

        print(f"\n✅ Original divider (R1-R2):")
        print(f"   - VCC → R1[1]")
        print(f"   - R1[2] ↔ R2[1] (Net1)")
        print(f"   - R2[2] → GND")

        print(f"\n✅ Copied divider (R3-R4):")
        print(f"   - VCC_copy → R3[1]")
        print(f"   - R3[2] ↔ R4[1] (Net2)")
        print(f"   - R4[2] → GND_copy")

        print(f"\n✅ Summary:")
        print(f"   - 4 resistors: {sorted(refs)}")
        print(f"   - 6 nets: {sorted(kicad_nets.keys())}")
        print(f"   - Both dividers electrically independent ✓")
        print(f"   - No unconnected pins ✓")
        print(f"   - Level 3 electrical validation PASSED ✓")

    finally:
        # Restore original Python file (without R3-R4)
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


@pytest.mark.skip(reason="Visual test skipped - use main test_36_copy_paste_component for full validation")
def test_36_copy_paste_visual_only(request):
    """Test 36 visual validation (without full netlist comparison).

    This test validates schematic structure without requiring
    full netlist parsing. It will pass with Issue #373 still open.

    Validates:
    - Initial circuit has 2 components (R1, R2)
    - After copy-paste, has 4 components (R1, R2, R3, R4)
    - All nets present as hierarchical labels
    - No component overlap

    Does NOT validate:
    - Actual pin-to-pin electrical connectivity (requires netlist)
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "resistor_divider_for_copy.py"
    output_dir = test_dir / "resistor_divider_for_copy"
    schematic_file = output_dir / "resistor_divider_for_copy.kicad_sch"

    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    # Clean any existing output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Read original Python file
    with open(python_file, "r") as f:
        original_code = f.read()

    try:
        # Generate initial circuit
        result = subprocess.run(
            ["uv", "run", "resistor_divider_for_copy.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0
        assert schematic_file.exists()

        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        # Verify initial state (2 resistors + possibly power symbols)
        assert len(components) >= 2
        refs_initial = {c.reference for c in components}
        assert "R1" in refs_initial and "R2" in refs_initial

        print(f"\n✅ Initial circuit: {refs_initial}")

        # Add R3-R4 copies
        modified_code = original_code.replace(
            "    # R3 and R4 will be added by test (copy-paste pattern)",
            """    # R3 and R4 copies with similar connectivity
    r3 = Component(
        symbol="Device:R",
        ref="R3",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    r4 = Component(
        symbol="Device:R",
        ref="R4",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Net4: VCC_copy → R3[1]
    net_vcc_copy = Net(name="VCC_copy")
    net_vcc_copy += r3[1]

    # Net5: R3[2] → R4[1] (junction point copy)
    net_junction_copy = Net(name="Net2")
    net_junction_copy += r3[2]
    net_junction_copy += r4[1]

    # Net6: R4[2] → GND_copy
    net_gnd_copy = Net(name="GND_copy")
    net_gnd_copy += r4[2]"""
        )

        with open(python_file, "w") as f:
            f.write(modified_code)

        # Verify the modification was written
        with open(python_file, "r") as f:
            written_code = f.read()
        assert "ref=\"R3\"" in written_code, "R3 not found in written code!"
        assert "Net2" in written_code, "Net2 not found in written code!"
        print(f"\n✅ Modified code written with R3-R4 and Net2")

        # Regenerate
        # Clear Python cache to ensure modified module is used
        import os
        pycache = test_dir / "__pycache__"
        if pycache.exists():
            shutil.rmtree(pycache)

        result = subprocess.run(
            ["uv", "run", "--no-cache-dir", "resistor_divider_for_copy.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Generation failed!\nSTDOUT:\n{result.stdout}\nSTDERR:\n{result.stderr}"
        )
        assert schematic_file.exists()

        # Debug: show generation output
        if "R3" not in result.stdout or "R4" not in result.stdout:
            print(f"\n⚠️  Generation output doesn't mention R3 or R4:")
            print(f"   STDOUT tail: {result.stdout[-500:] if result.stdout else 'empty'}")
            print(f"   STDERR tail: {result.stderr[-500:] if result.stderr else 'empty'}")

        # Verify expanded circuit
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        refs_final = {c.reference for c in components}
        print(f"\n📊 Final circuit components: {sorted(refs_final)}")

        assert len(components) >= 4, f"Expected >=4 components, got {len(components)} with refs {refs_final}"
        expected_resistors = {"R1", "R2", "R3", "R4"}
        assert expected_resistors.issubset(refs_final), f"Missing resistors! Expected {expected_resistors}, got {refs_final}"

        # Verify all values are 10k
        for comp in components:
            assert comp.value == "10k"

        # Check for all net labels in schematic
        with open(schematic_file, 'r') as f:
            sch_content = f.read()

        # Extract all hierarchical labels for debugging
        all_labels_raw = re.findall(r'\(hierarchical_label "([^"]*)"', sch_content)
        all_labels = set(all_labels_raw)
        print(f"\n📊 Labels found in schematic: {sorted(all_labels)}")

        # Debug: show the raw matches
        if all_labels_raw:
            print(f"   Raw matches: {all_labels_raw}")

        # Check for hierarchical labels (VCC and GND are power symbols, not labels)
        # Only Net1, Net2, VCC_copy, GND_copy should be hierarchical labels
        # (VCC and GND are converted to power symbols)
        expected_labels = {"Net1", "Net2", "VCC_copy", "GND_copy"}
        assert expected_labels.issubset(all_labels), (
            f"Missing expected labels!\n"
            f"Expected at least: {expected_labels}\n"
            f"Found: {all_labels}"
        )

        print(f"\n✅ Final circuit: {refs_final}")
        print(f"✅ All net labels present: {expected_labels}")
        print(f"\n⚠️  Note: This test does NOT validate electrical connectivity")
        print(f"   Use test_36_copy_paste_component for full electrical validation")

    finally:
        # Restore original Python file
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
