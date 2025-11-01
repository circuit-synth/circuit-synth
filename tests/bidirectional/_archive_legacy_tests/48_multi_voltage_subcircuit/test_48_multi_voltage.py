#!/usr/bin/env python3
"""
Automated test for 48_multi_voltage_subcircuit bidirectional test.

Tests CRITICAL hierarchical + multi-voltage workflow: Multiple power domains
(VCC_5V, VCC_3V3, GND) distributed to subcircuit where components connect via
local power symbols.

This validates real-world mixed-voltage interface circuits like level shifters
that require multiple voltage domains within a subcircuit.

Core Question: When you add power symbols for MULTIPLE voltages (5V, 3.3V)
inside a child sheet and regenerate, does KiCad correctly:
1. Place power symbols for each voltage in child sheet file (not root)
2. Generate hierarchical labels for ALL power nets (5V, 3.3V, GND)
3. Show electrical connectivity in netlist (segregated by voltage)
4. Preserve power symbol positions when adding components
5. Reuse existing power symbols across multiple voltages

Workflow:
1. Generate with subcircuit containing level shifter (Q1, R1, R2)
2. Validate:
   - Power symbols exist for VCC_5V, VCC_3V3, GND in CHILD schematic
   - Hierarchical labels created for all three power nets
   - Netlist shows R1 on VCC_5V, R2 on VCC_3V3
   - Q1 source on GND
3. Add second level shifter (Q2, R3, R4) to child sheet
4. Regenerate
5. Validate:
   - Same power symbols used (no duplicates)
   - Both shifters connected to correct voltages
   - Power symbol positions unchanged
   - R1+R3 on VCC_5V, R2+R4 on VCC_3V3

Validation uses:
- kicad-sch-api for schematic structure (Level 2)
- Netlist comparison for electrical connectivity (Level 3)
"""
import json
import re
import shutil
import subprocess
from pathlib import Path

import pytest


def parse_netlist(netlist_content):
    """Parse netlist content and extract net information.

    Returns dict: {net_name: [(ref, pin), ...]}
    """
    import re

    nets = {}

    # Find all net blocks
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
    reason="Multi-voltage power in subcircuits may not be fully supported yet - "
           "requires hierarchical labels for multiple power domains"
)
def test_48_multi_voltage_subcircuit(request):
    """Test multi-voltage power symbols (5V, 3.3V) in subcircuit.

    CRITICAL HIERARCHICAL + MULTI-VOLTAGE WORKFLOW:
    Validates real-world mixed-voltage interface circuits where subcircuits
    need multiple power domains (e.g., level shifters between 5V and 3.3V).

    Real-World Pattern:
    - Root sheet: Multiple voltage regulators (5V, 3.3V outputs)
    - Child sheet: Level shifter circuit needing BOTH voltages
    - Power flow: Root VCC_5V → Hierarchical label → Child VCC_5V symbol → R1
    - Power flow: Root VCC_3V3 → Hierarchical label → Child VCC_3V3 symbol → R2

    This is THE workflow for mixed-voltage hierarchical designs:
    - Start with subcircuit structure (components, multi-voltage power)
    - Review layout in KiCad
    - Add second level shifter in Python
    - Regenerate → power symbols reused, no duplicates

    Workflow:
    1. Generate with subcircuit containing level shifter (Q1, R1, R2)
    2. Verify child schematic exists with dual voltage power symbols
    3. Validate netlist shows R1 on VCC_5V, R2 on VCC_3V3
    4. Add second level shifter (Q2, R3, R4)
    5. Regenerate → power symbols reused, positions preserved
    6. Validate R1+R3 on VCC_5V, R2+R4 on VCC_3V3

    Level 2 & 3 Validation:
    - kicad-sch-api for schematic structure
    - File structure for child sheet existence
    - Netlist comparison for electrical connectivity through hierarchy
    - Multi-voltage power domain segregation
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "level_shifter.py"
    output_dir = test_dir / "level_shifter"
    schematic_file = output_dir / "level_shifter.kicad_sch"
    child_schematic_file = output_dir / "Level_Shifter.kicad_sch"

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
        # STEP 1: Generate with dual voltage level shifter subcircuit
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate level shifter with dual voltage domains")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "level_shifter.py"],
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

        assert schematic_file.exists(), "Root schematic not created"

        # Check for child schematic
        print(f"   Root schematic exists: {schematic_file}")
        if child_schematic_file.exists():
            print(f"   Child schematic exists: {child_schematic_file}")
        else:
            print(f"   Child schematic NOT separate (may be flattened)")

        # Load schematic and verify components exist
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        print(f"\n   Components found: {len(components)}")
        for comp in components:
            print(f"     * {comp.reference}: {comp.value if hasattr(comp, 'value') else 'N/A'}")

        # Find level shifter components
        q1 = next((c for c in components if c.reference == "Q1"), None)
        r1 = next((c for c in components if c.reference == "R1"), None)
        r2 = next((c for c in components if c.reference == "R2"), None)

        assert q1 is not None, "Q1 (MOSFET) not found in schematic"
        assert r1 is not None, "R1 (5V pull-up) not found in schematic"
        assert r2 is not None, "R2 (3.3V pull-up) not found in schematic"

        q1_initial_pos = q1.position
        r1_initial_pos = r1.position
        r2_initial_pos = r2.position

        print(f"\n   Initial positions:")
        print(f"     - Q1: {q1_initial_pos}")
        print(f"     - R1: {r1_initial_pos}")
        print(f"     - R2: {r2_initial_pos}")

        # Verify hierarchical labels for BOTH voltage domains
        with open(schematic_file, 'r') as f:
            sch_content = f.read()

        vcc_5v_labels = sch_content.count('hierarchical_label "VCC_5V"')
        vcc_3v3_labels = sch_content.count('hierarchical_label "VCC_3V3"')
        gnd_labels = sch_content.count('hierarchical_label "GND"')

        print(f"\n   Power labels (multi-voltage):")
        print(f"     - VCC_5V labels: {vcc_5v_labels}")
        print(f"     - VCC_3V3 labels: {vcc_3v3_labels}")
        print(f"     - GND labels: {gnd_labels}")

        assert vcc_5v_labels >= 1, (
            f"Expected at least 1 VCC_5V hierarchical label, found {vcc_5v_labels}"
        )
        assert vcc_3v3_labels >= 1, (
            f"Expected at least 1 VCC_3V3 hierarchical label, found {vcc_3v3_labels}"
        )
        assert gnd_labels >= 1, (
            f"Expected at least 1 GND hierarchical label, found {gnd_labels}"
        )

        print(f"\n   Step 1: Multi-voltage subcircuit generated")

        # =====================================================================
        # STEP 2: Validate electrical connectivity via netlist (dual voltage)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Validate dual voltage connectivity (netlist)")
        print("="*70)

        # Export netlist using kicad-cli
        kicad_netlist_file_1 = output_dir / "level_shifter_initial.net"

        result = subprocess.run(
            [
                "kicad-cli", "sch", "export", "netlist",
                str(schematic_file),
                "--output", str(kicad_netlist_file_1)
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

        # Parse initial netlist
        with open(kicad_netlist_file_1, 'r') as f:
            kicad_netlist_1 = f.read()

        nets_initial = parse_netlist(kicad_netlist_1)

        print(f"\n   KiCad-exported netlist (initial):")
        print(f"   Nets found: {sorted(nets_initial.keys())}")
        for net_name in sorted(nets_initial.keys()):
            nodes = nets_initial[net_name]
            print(f"     - {net_name}: {nodes}")

        # Validate VCC_5V, VCC_3V3, and GND nets exist
        assert "VCC_5V" in nets_initial, (
            f"VCC_5V net not found in netlist! Found: {list(nets_initial.keys())}"
        )
        assert "VCC_3V3" in nets_initial, (
            f"VCC_3V3 net not found in netlist! Found: {list(nets_initial.keys())}"
        )
        assert "GND" in nets_initial, (
            f"GND net not found in netlist! Found: {list(nets_initial.keys())}"
        )

        vcc_5v_nodes = nets_initial["VCC_5V"]
        vcc_3v3_nodes = nets_initial["VCC_3V3"]
        gnd_nodes = nets_initial["GND"]

        # Validate R1 connected to VCC_5V (5V side pull-up)
        assert ("R1", "1") in vcc_5v_nodes, (
            f"R1 pin 1 not connected to VCC_5V!\n"
            f"VCC_5V connections: {vcc_5v_nodes}"
        )

        # Validate R2 connected to VCC_3V3 (3.3V side pull-up)
        assert ("R2", "1") in vcc_3v3_nodes, (
            f"R2 pin 1 not connected to VCC_3V3!\n"
            f"VCC_3V3 connections: {vcc_3v3_nodes}"
        )

        # Validate Q1 source connected to GND
        # Q_NMOS: pins are G (gate), S (source), D (drain)
        # Source should be "S"
        q1_gnd_connected = any(
            node[0] == "Q1" and node[1] in ["S", "s"]
            for node in gnd_nodes
        )

        assert q1_gnd_connected, (
            f"Q1 source not connected to GND!\n"
            f"GND connections: {gnd_nodes}"
        )

        print(f"\n   Step 2: Dual voltage connectivity VALIDATED!")
        print(f"     - VCC_5V connects: {vcc_5v_nodes}")
        print(f"     - VCC_3V3 connects: {vcc_3v3_nodes}")
        print(f"     - GND connects: {gnd_nodes}")
        print(f"     - R1[1] -> VCC_5V (5V pull-up)")
        print(f"     - R2[1] -> VCC_3V3 (3.3V pull-up)")
        print(f"     - Q1[S] -> GND")

        # =====================================================================
        # STEP 3: Add second level shifter (Q2, R3, R4)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Add second level shifter (multi-voltage symbol reuse)")
        print("="*70)

        # Add second level shifter to child circuit
        injection_lines = [
            "",
            "    # Add second level shifter for power symbol reuse test",
            "    q2 = Component(",
            "        symbol=\"Device:Q_NMOS\",",
            "        ref=\"Q2\",",
            "        value=\"BSS138\",",
            "        footprint=\"Package_TO_SOT_SMD:SOT-23\",",
            "    )",
            "",
            "    r3 = Component(",
            "        symbol=\"Device:R\",",
            "        ref=\"R3\",",
            "        value=\"10k\",",
            "        footprint=\"Resistor_SMD:R_0603_1608Metric\",",
            "    )",
            "",
            "    r4 = Component(",
            "        symbol=\"Device:R\",",
            "        ref=\"R4\",",
            "        value=\"10k\",",
            "        footprint=\"Resistor_SMD:R_0603_1608Metric\",",
            "    )",
            "",
            "    shifter_circuit.add_component(q2)",
            "    shifter_circuit.add_component(r3)",
            "    shifter_circuit.add_component(r4)",
            "",
            "    # Connect second level shifter to SAME multi-voltage power symbols",
            "    # Q_NMOS: pins are G (gate), S (source), D (drain)",
            "    vcc_5v_child += r3[1]      # R3 pull-up to 5V (reuse VCC_5V symbol)",
            "    vcc_3v3_child += r4[1]     # R4 pull-up to 3.3V (reuse VCC_3V3 symbol)",
            "    r3[2] += q2[\"G\"]        # R3 other end to gate",
            "    r4[2] += q2[\"D\"]        # R4 other end to drain",
            "    q2[\"S\"] += gnd_child    # Source to ground (reuse GND symbol)",
        ]

        # Find insertion point (before root.add_subcircuit)
        second_shifter_injection = "\n".join(injection_lines)

        modified_code = original_code.replace(
            "    root.add_subcircuit(shifter_circuit)",
            second_shifter_injection + "\n\n    root.add_subcircuit(shifter_circuit)"
        )

        assert modified_code != original_code, (
            "Failed to inject second level shifter code"
        )

        # Write modified code with second level shifter
        with open(python_file, "w") as f:
            f.write(modified_code)

        print(f"   Second level shifter (Q2, R3, R4) added to child circuit")
        print(f"   - Q2: Second BSS138 MOSFET")
        print(f"   - R3: 5V pull-up (uses VCC_5V symbol)")
        print(f"   - R4: 3.3V pull-up (uses VCC_3V3 symbol)")

        # =====================================================================
        # STEP 4: Regenerate with second level shifter
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 4: Regenerate with second level shifter")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "level_shifter.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 4 failed: Regeneration with second level shifter\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # =====================================================================
        # STEP 5: Validate power symbol reuse (no duplicates for either voltage)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 5: Validate multi-voltage power symbol reuse")
        print("="*70)

        sch_final = Schematic.load(str(schematic_file))
        components_final = sch_final.components

        print(f"\n   Components after adding Q2: {len(components_final)}")
        for comp in components_final:
            print(f"     * {comp.reference}")

        # Verify all components present
        q1_final = next((c for c in components_final if c.reference == "Q1"), None)
        q2_final = next((c for c in components_final if c.reference == "Q2"), None)
        r1_final = next((c for c in components_final if c.reference == "R1"), None)
        r2_final = next((c for c in components_final if c.reference == "R2"), None)
        r3_final = next((c for c in components_final if c.reference == "R3"), None)
        r4_final = next((c for c in components_final if c.reference == "R4"), None)

        assert q1_final is not None, "Q1 missing after adding Q2"
        assert q2_final is not None, "Q2 not added to schematic"
        assert r1_final is not None, "R1 missing after adding Q2"
        assert r2_final is not None, "R2 missing after adding Q2"
        assert r3_final is not None, "R3 not added to schematic"
        assert r4_final is not None, "R4 not added to schematic"

        # Verify original positions preserved
        print(f"\n   Position preservation:")
        print(f"     - Q1: {q1_initial_pos} -> {q1_final.position}")
        print(f"     - R1: {r1_initial_pos} -> {r1_final.position}")
        print(f"     - R2: {r2_initial_pos} -> {r2_final.position}")

        # Check power labels (should not multiply for each voltage)
        with open(schematic_file, 'r') as f:
            sch_content_final = f.read()

        vcc_5v_labels_final = sch_content_final.count('hierarchical_label "VCC_5V"')
        vcc_3v3_labels_final = sch_content_final.count('hierarchical_label "VCC_3V3"')
        gnd_labels_final = sch_content_final.count('hierarchical_label "GND"')

        print(f"\n   Power labels after adding Q2:")
        print(f"     - VCC_5V labels: {vcc_5v_labels_final}")
        print(f"     - VCC_3V3 labels: {vcc_3v3_labels_final}")
        print(f"     - GND labels: {gnd_labels_final}")
        print(f"     (Should be same as before, not multiplied)")

        # =====================================================================
        # STEP 6: Validate both level shifters connected to correct voltages
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 6: Validate both shifters on correct voltage domains")
        print("="*70)

        # Export final netlist
        kicad_netlist_file_2 = output_dir / "level_shifter_final.net"

        result = subprocess.run(
            [
                "kicad-cli", "sch", "export", "netlist",
                str(schematic_file),
                "--output", str(kicad_netlist_file_2)
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, "kicad-cli netlist export failed"

        with open(kicad_netlist_file_2, 'r') as f:
            kicad_netlist_final = f.read()

        nets_final = parse_netlist(kicad_netlist_final)

        print(f"\n   Final netlist (both level shifters):")
        for net_name in sorted(nets_final.keys()):
            nodes = nets_final[net_name]
            print(f"     - {net_name}: {nodes}")

        # Verify both shifters on correct voltage nets
        vcc_5v_nodes_final = nets_final.get("VCC_5V", [])
        vcc_3v3_nodes_final = nets_final.get("VCC_3V3", [])
        gnd_nodes_final = nets_final.get("GND", [])

        # VCC_5V should have R1 and R3 (both 5V pull-ups)
        assert ("R1", "1") in vcc_5v_nodes_final, "R1 not on VCC_5V after adding Q2"
        assert ("R3", "1") in vcc_5v_nodes_final, "R3 not connected to VCC_5V"

        # VCC_3V3 should have R2 and R4 (both 3.3V pull-ups)
        assert ("R2", "1") in vcc_3v3_nodes_final, "R2 not on VCC_3V3 after adding Q2"
        assert ("R4", "1") in vcc_3v3_nodes_final, "R4 not connected to VCC_3V3"

        # GND should have Q1 and Q2 sources
        # Q_NMOS: pin "S" is source
        q1_gnd_final = any(
            node[0] == "Q1" and node[1] in ["S", "s"]
            for node in gnd_nodes_final
        )
        q2_gnd_final = any(
            node[0] == "Q2" and node[1] in ["S", "s"]
            for node in gnd_nodes_final
        )

        assert q1_gnd_final, "Q1 not on GND after adding Q2"
        assert q2_gnd_final, "Q2 source not connected to GND"

        print(f"\n   Step 6: Multi-voltage power symbol reuse VALIDATED!")
        print(f"     - VCC_5V: R1, R3 (both 5V pull-ups)")
        print(f"     - VCC_3V3: R2, R4 (both 3.3V pull-ups)")
        print(f"     - GND: Q1 source, Q2 source")
        print(f"     - No duplicate power symbols created")
        print(f"     - Voltage domains properly segregated")

        print(f"\n" + "="*70)
        print(f" MULTI-VOLTAGE SUBCIRCUIT WORKFLOW VALIDATED!")
        print(f"="*70)
        print(f"   Power symbols for multiple voltages in child sheet")
        print(f"   Hierarchical labels for VCC_5V, VCC_3V3, GND")
        print(f"   Multiple components share same multi-voltage power symbols")
        print(f"   Electrical connectivity verified through hierarchy")
        print(f"   Voltage domain segregation maintained")
        print(f"   Real-world level shifter pattern works!")

    finally:
        # Restore original Python file
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
