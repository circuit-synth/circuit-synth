#!/usr/bin/env python3
"""
Automated test for 27_multiple_power_domains bidirectional test.

Tests CRITICAL real-world workflow: circuits with multiple power rails
(VCC, 3V3, 5V, GND) where each component connects to the correct power domain.

This validates that you can:
1. Generate circuit with 4 resistors on different power domains
2. Validate netlist shows 4 separate power nets
3. Verify each resistor connected to correct power domain
4. Modify Python to move R2 from 3V3 to 5V
5. Regenerate → netlist updated correctly
6. Positions preserved during iterative development

This is foundational for real-world embedded systems that commonly use
multiple voltage rails (3.3V logic, 5V peripherals, 12V power, GND).

Workflow:
1. Generate with R1→VCC, R2→3V3, R3→5V, R4→GND
2. Verify 4 separate nets in schematic (hierarchical labels)
3. Export netlist and verify component-to-domain mappings
4. Modify R2 from 3V3 to 5V in Python
5. Regenerate
6. Validate:
   - Netlist shows R2 now on 5V net
   - R2 and R3 both on 5V net
   - 3V3 net now empty or removed
   - All component positions preserved

Validation uses:
- kicad-sch-api for schematic structure
- Netlist parsing for power domain assignments
- Position comparison for preservation
"""

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


def test_18_multiple_power_domains(request):
    """Test multi-voltage circuit with multiple independent power rails.

    CRITICAL REAL-WORLD WORKFLOW:
    Validates that circuits can use multiple power domains correctly.
    Multi-voltage designs are universal in embedded systems:
    - Microcontroller at 3.3V
    - Peripherals at 5V
    - Power supply at 12V+
    - GND as reference

    This ensures each component connects to the correct power domain
    and modifications don't break the circuit.

    Workflow:
    1. Generate with R1→VCC, R2→3V3, R3→5V, R4→GND (4 domains)
    2. Verify 4 hierarchical labels in schematic (no cross-connections)
    3. Export netlist and verify power domain assignments
    4. Modify R2 from 3V3 to 5V
    5. Regenerate → labels and nets updated
    6. Validate:
       - Netlist shows R2 now on 5V net with R3
       - 3V3 net is empty
       - All positions preserved

    Level 3 Electrical Validation:
    - kicad-sch-api for schematic structure
    - Netlist comparison for electrical connectivity
    - Power domain segregation verification
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "multi_voltage_circuit.py"
    output_dir = test_dir / "multi_voltage_circuit"
    schematic_file = output_dir / "multi_voltage_circuit.kicad_sch"

    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    # Clean any existing output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Read original Python file (initial configuration)
    with open(python_file, "r") as f:
        original_code = f.read()

    try:
        # =====================================================================
        # STEP 1: Generate initial multi-voltage circuit
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate circuit with 4 power domains")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "multi_voltage_circuit.py"],
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

        # Validate components (4 resistors + 4 power symbols)
        from kicad_sch_api import Schematic
        sch = Schematic.load(str(schematic_file))
        components = sch.components

        # Filter out power symbols to get just the resistors
        resistors = [c for c in components if not c.reference.startswith("#PWR")]
        power_symbols = [c for c in components if c.reference.startswith("#PWR")]

        assert len(resistors) == 4, f"Expected 4 resistors, found {len(resistors)}"
        assert len(power_symbols) == 4, f"Expected 4 power symbols, found {len(power_symbols)}"

        refs = {c.reference for c in resistors}
        assert "R1" in refs and "R2" in refs and "R3" in refs and "R4" in refs

        # Store initial positions
        r1_initial = next(c for c in components if c.reference == "R1")
        r2_initial = next(c for c in components if c.reference == "R2")
        r3_initial = next(c for c in components if c.reference == "R3")
        r4_initial = next(c for c in components if c.reference == "R4")

        r1_initial_pos = r1_initial.position
        r2_initial_pos = r2_initial.position
        r3_initial_pos = r3_initial.position
        r4_initial_pos = r4_initial.position

        # Verify power symbols for power domains (not hierarchical labels)
        with open(schematic_file, 'r') as f:
            sch_content = f.read()

        # Count power symbols for each power domain
        vcc_symbols = sch_content.count('lib_id "power:VCC"')
        v3v3_symbols = sch_content.count('lib_id "power:+3V3"')
        v5v_symbols = sch_content.count('lib_id "power:+5V"')
        gnd_symbols = sch_content.count('lib_id "power:GND"')

        print(f"✅ Step 1: Initial multi-voltage circuit generated")
        print(f"   - Resistors: {refs}")
        print(f"   - R1 position: {r1_initial_pos} (VCC)")
        print(f"   - R2 position: {r2_initial_pos} (3V3)")
        print(f"   - R3 position: {r3_initial_pos} (5V)")
        print(f"   - R4 position: {r4_initial_pos} (GND)")
        print(f"\n   Power symbols:")
        print(f"   - VCC: {vcc_symbols} symbol(s)")
        print(f"   - 3V3: {v3v3_symbols} symbol(s)")
        print(f"   - 5V: {v5v_symbols} symbol(s)")
        print(f"   - GND: {gnd_symbols} symbol(s)")

        assert vcc_symbols == 1, f"Expected 1 VCC power symbol, found {vcc_symbols}"
        assert v3v3_symbols == 1, f"Expected 1 3V3 power symbol, found {v3v3_symbols}"
        assert v5v_symbols == 1, f"Expected 1 5V power symbol, found {v5v_symbols}"
        assert gnd_symbols == 1, f"Expected 1 GND power symbol, found {gnd_symbols}"

        # =====================================================================
        # STEP 2: Export and validate initial netlist
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Export and validate initial netlist")
        print("="*70)

        kicad_netlist_file_1 = output_dir / "multi_voltage_circuit_initial.net"

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

        print(f"\n📊 Initial netlist (4 power domains):")
        print(f"   Nets found: {sorted(nets_initial.keys())}")
        for net_name in sorted(nets_initial.keys()):
            nodes = nets_initial[net_name]
            print(f"   - {net_name}: {nodes}")

        # Validate initial power domain assignments
        assert "VCC" in nets_initial, "VCC net not found in netlist"
        assert "3V3" in nets_initial, "3V3 net not found in netlist"
        assert "5V" in nets_initial, "5V net not found in netlist"
        assert "GND" in nets_initial, "GND net not found in netlist"

        # Verify initial connections
        vcc_nodes = nets_initial["VCC"]
        v3v3_nodes = nets_initial["3V3"]
        v5v_nodes = nets_initial["5V"]
        gnd_nodes = nets_initial["GND"]

        assert ("R1", "1") in vcc_nodes, (
            f"R1 pin 1 not on VCC net. Found: {vcc_nodes}"
        )
        assert ("R2", "1") in v3v3_nodes, (
            f"R2 pin 1 not on 3V3 net. Found: {v3v3_nodes}"
        )
        assert ("R3", "1") in v5v_nodes, (
            f"R3 pin 1 not on 5V net. Found: {v5v_nodes}"
        )
        assert ("R4", "1") in gnd_nodes, (
            f"R4 pin 1 not on GND net. Found: {gnd_nodes}"
        )

        print(f"\n✅ Step 2: Initial netlist VALIDATED!")
        print(f"   - VCC: {vcc_nodes}")
        print(f"   - 3V3: {v3v3_nodes}")
        print(f"   - 5V: {v5v_nodes}")
        print(f"   - GND: {gnd_nodes}")

        # =====================================================================
        # STEP 3: Modify R2 from 3V3 to 5V
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Move R2 from 3V3 to 5V (modify Python)")
        print("="*70)

        # Modify Python: remove R2 from 3V3, add to 5V
        modified_code = original_code.replace(
            '    # 3V3 net (3.3V logic supply) - R2 connects here\n'
            '    net_3v3 = Net(name="3V3")\n'
            '    net_3v3 += r2[1]  # R2 pin 1 to 3V3\n'
            '\n'
            '    # 5V net (5V supply) - R3 connects here\n'
            '    net_5v = Net(name="5V")\n'
            '    net_5v += r3[1]  # R3 pin 1 to 5V',
            '    # 3V3 net (3.3V logic supply) - originally had R2\n'
            '    net_3v3 = Net(name="3V3")\n'
            '    # Note: R2 moved to 5V domain below\n'
            '\n'
            '    # 5V net (5V supply) - R2 and R3 connect here\n'
            '    net_5v = Net(name="5V")\n'
            '    net_5v += r2[1]  # R2 pin 1 to 5V (moved from 3V3)\n'
            '    net_5v += r3[1]  # R3 pin 1 to 5V'
        )

        # Write modified Python file
        with open(python_file, "w") as f:
            f.write(modified_code)

        print(f"✅ Step 3: Python modified")
        print(f"   - R2 moved from 3V3 to 5V")
        print(f"   - R2 and R3 now share 5V domain")

        # =====================================================================
        # STEP 4: Regenerate with modified power domains
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 4: Regenerate with modified power domains")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "multi_voltage_circuit.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        assert result.returncode == 0, (
            f"Step 4 failed: Regeneration with modified power domains\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # =====================================================================
        # STEP 5: Validate modified netlist
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 5: Validate modified netlist (R2 on 5V)")
        print("="*70)

        sch_final = Schematic.load(str(schematic_file))
        components_final = sch_final.components

        # Filter to just resistors (exclude power symbols)
        resistors_final = [c for c in components_final if not c.reference.startswith("#PWR")]
        power_symbols_final = [c for c in components_final if c.reference.startswith("#PWR")]

        assert len(resistors_final) == 4, f"Expected 4 resistors, found {len(resistors_final)}"
        # After moving R2 from 3V3 to 5V, we should have: VCC, 5V, 5V, GND = 4 power symbols
        # But one 3V3 power symbol should be removed, so we might have 3 power symbols
        assert len(power_symbols_final) >= 3, f"Expected at least 3 power symbols, found {len(power_symbols_final)}"

        r1_final = next(c for c in components_final if c.reference == "R1")
        r2_final = next(c for c in components_final if c.reference == "R2")
        r3_final = next(c for c in components_final if c.reference == "R3")
        r4_final = next(c for c in components_final if c.reference == "R4")

        r1_final_pos = r1_final.position
        r2_final_pos = r2_final.position
        r3_final_pos = r3_final.position
        r4_final_pos = r4_final.position

        # Validate positions preserved
        assert r1_final_pos == r1_initial_pos, (
            f"R1 position changed!\n"
            f"Initial: {r1_initial_pos}\n"
            f"Final: {r1_final_pos}"
        )
        assert r2_final_pos == r2_initial_pos, (
            f"R2 position changed!\n"
            f"Initial: {r2_initial_pos}\n"
            f"Final: {r2_final_pos}"
        )
        assert r3_final_pos == r3_initial_pos, (
            f"R3 position changed!\n"
            f"Initial: {r3_initial_pos}\n"
            f"Final: {r3_final_pos}"
        )
        assert r4_final_pos == r4_initial_pos, (
            f"R4 position changed!\n"
            f"Initial: {r4_initial_pos}\n"
            f"Final: {r4_final_pos}"
        )

        # Validate power symbol changes - R2 should now have 5V (not 3V3)
        with open(schematic_file, 'r') as f:
            sch_content_final = f.read()

        # Count power symbols after modification
        vcc_symbols_final = sch_content_final.count('lib_id "power:VCC"')
        v3v3_symbols_final = sch_content_final.count('lib_id "power:+3V3"')
        v5v_symbols_final = sch_content_final.count('lib_id "power:+5V"')
        gnd_symbols_final = sch_content_final.count('lib_id "power:GND"')

        print(f"✅ Step 5: Positions preserved during modification")
        print(f"   - R1 position: {r1_final_pos} (unchanged)")
        print(f"   - R2 position: {r2_final_pos} (unchanged)")
        print(f"   - R3 position: {r3_final_pos} (unchanged)")
        print(f"   - R4 position: {r4_final_pos} (unchanged)")
        print(f"\n   Power symbols (after modification):")
        print(f"   - VCC: {vcc_symbols_final} symbol(s) (unchanged)")
        print(f"   - 3V3: {v3v3_symbols_final} symbol(s) (removed - was 1)")
        print(f"   - 5V: {v5v_symbols_final} symbol(s) (increased - was 1)")
        print(f"   - GND: {gnd_symbols_final} symbol(s) (unchanged)")

        # 3V3 power symbol should be gone
        # 5V power symbols should increase (now has R2 and R3)
        assert vcc_symbols_final == 1, (
            f"VCC power symbol count changed! Expected 1, got {vcc_symbols_final}"
        )
        assert v3v3_symbols_final == 0, (
            f"3V3 power symbol should be removed! Expected 0, got {v3v3_symbols_final}"
        )
        assert v5v_symbols_final == 2, (
            f"5V power symbols should be 2 (R2 + R3)! Expected 2, got {v5v_symbols_final}"
        )
        assert gnd_symbols_final == 1, (
            f"GND power symbol count changed! Expected 1, got {gnd_symbols_final}"
        )

        # =====================================================================
        # STEP 6: Export and validate modified netlist
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 6: Export and validate modified netlist")
        print("="*70)

        kicad_netlist_file_2 = output_dir / "multi_voltage_circuit_modified.net"

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

        assert result.returncode == 0, (
            f"kicad-cli netlist export failed\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # Parse modified netlist
        with open(kicad_netlist_file_2, 'r') as f:
            kicad_netlist_2 = f.read()

        nets_final = parse_netlist(kicad_netlist_2)

        print(f"\n📊 Modified netlist (R2 moved to 5V):")
        print(f"   Nets found: {sorted(nets_final.keys())}")
        for net_name in sorted(nets_final.keys()):
            nodes = nets_final[net_name]
            print(f"   - {net_name}: {nodes}")

        # Validate modified power domain assignments
        assert "VCC" in nets_final, "VCC net not found in modified netlist"
        assert "5V" in nets_final, "5V net not found in modified netlist"
        assert "GND" in nets_final, "GND net not found in modified netlist"

        # R2 should now be on 5V, not 3V3
        v5v_nodes_final = nets_final["5V"]

        assert ("R2", "1") in v5v_nodes_final, (
            f"R2 pin 1 not on 5V net after modification.\n"
            f"5V net contains: {v5v_nodes_final}"
        )

        assert ("R3", "1") in v5v_nodes_final, (
            f"R3 pin 1 not on 5V net.\n"
            f"5V net contains: {v5v_nodes_final}"
        )

        # Verify 5V net now has both R2 and R3
        expected_5v_nodes = [("R2", "1"), ("R3", "1")]
        actual_5v_nodes = sorted(v5v_nodes_final)

        assert actual_5v_nodes == sorted(expected_5v_nodes), (
            f"5V net doesn't have expected nodes!\n"
            f"Expected: {sorted(expected_5v_nodes)}\n"
            f"Got: {actual_5v_nodes}"
        )

        # Verify VCC and GND unchanged
        vcc_nodes_final = nets_final["VCC"]
        gnd_nodes_final = nets_final["GND"]

        assert ("R1", "1") in vcc_nodes_final, (
            f"R1 pin 1 not on VCC net. Found: {vcc_nodes_final}"
        )
        assert ("R4", "1") in gnd_nodes_final, (
            f"R4 pin 1 not on GND net. Found: {gnd_nodes_final}"
        )

        print(f"\n✅ Step 6: Modified netlist VALIDATED!")
        print(f"   - VCC: {vcc_nodes_final} (unchanged)")
        print(f"   - 5V: {v5v_nodes_final} (R2 and R3)")
        print(f"   - GND: {gnd_nodes_final} (unchanged)")
        print(f"\n🎉 Multi-voltage circuit modification works!")
        print(f"   R2 successfully moved from 3V3 to 5V!")
        print(f"   All positions preserved during modification!")

    finally:
        # Restore original Python file
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
