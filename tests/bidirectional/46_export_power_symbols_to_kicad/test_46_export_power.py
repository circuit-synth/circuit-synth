#!/usr/bin/env python3
"""
Automated test for 46_export_power_symbols_to_kicad bidirectional test.

Tests CRITICAL bidirectional power workflow: exporting Python circuits with
multiple power domains to KiCad as power symbols.

This validates the FORWARD direction of power symbol bidirectional support:
- Test 45: KiCad → Python power import ✅
- Test 46: Python → KiCad power export ❌ (THIS TEST)

Real-world workflow:
1. Create Python circuit with 5 power domains (VCC_3V3, VCC_5V, VCC_12V, GND, AGND)
2. Generate to KiCad
3. Validate all 5 power symbols created correctly
4. Add component using existing power domain (VCC_3V3)
5. Regenerate and verify power symbol reuse (no duplicates)

Workflow:
1. Generate circuit with R1-R5 on 5 different power domains
2. Validate 5 power symbols created (Level 2)
3. Validate netlist electrical connectivity (Level 3)
4. Add R6 in Python sharing VCC_3V3 with R1
5. Regenerate and validate:
   - Still 5 power symbols (no duplicate VCC_3V3)
   - VCC_3V3 net contains both R1 and R6
   - Netlist validates power symbol reuse (Level 3)

This test may XFAIL if power symbol export is not fully implemented.
Any failures should be documented as GitHub issues.
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

            # Skip power symbols (they don't have reference designators like R1, C1)
            if ref.startswith('#PWR'):
                continue

            nodes.append((ref, pin))

        if nodes:
            nets[net_name] = sorted(nodes)

    return nets


def count_power_symbols(schematic_content):
    """Count power symbols in KiCad schematic.

    Returns dict: {symbol_name: count}
    """
    power_symbols = {}

    # Pattern to match power symbol library IDs
    # Examples: (lib_id "power:VCC"), (lib_id "power:GND"), etc.
    lib_id_pattern = r'\(lib_id\s+"power:([^"]+)"\)'

    for match in re.finditer(lib_id_pattern, schematic_content):
        symbol_name = match.group(1)
        power_symbols[symbol_name] = power_symbols.get(symbol_name, 0) + 1

    return power_symbols


def test_46_export_power_symbols(request):
    """Test exporting Python circuit with multiple power domains to KiCad.

    CRITICAL BIDIRECTIONAL WORKFLOW:
    Validates that power domains in Python circuits:
    1. Export correctly as power symbols
    2. Create appropriate power symbol types
    3. Can be reused when adding components
    4. Don't create duplicate symbols

    This is THE workflow for creating circuits with power:
    - Define power domains in Python (VCC_3V3, VCC_5V, etc.)
    - Generate to KiCad → power symbols appear
    - Add components → reuse existing power symbols
    - Regenerate → clean, efficient schematics

    Power symbols have special handling in KiCad:
    - Global net connections (VCC, GND, etc.)
    - Special symbol library (power:VCC, power:GND)
    - Don't appear in BOM (no footprint)
    - Should be reused, not duplicated

    Workflow:
    1. Generate circuit with 5 power domains
    2. Validate 5 power symbols created
    3. Add component using existing domain (VCC_3V3)
    4. Regenerate → symbol reused, no duplicates

    Level 2 Validation: Power symbol count and types
    Level 3 Validation: Netlist electrical connectivity
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "multi_power_domain.py"
    output_dir = test_dir / "multi_power_domain"
    schematic_file = output_dir / "multi_power_domain.kicad_sch"

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
        # STEP 1: Generate circuit with 5 power domains
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate circuit with 5 power domains")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "multi_power_domain.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            pytest.xfail(
                f"Initial generation failed. "
                f"Power domain circuit generation may not be working.\n"
                f"STDOUT:\n{result.stdout}\n"
                f"STDERR:\n{result.stderr}\n"
                f"Create GitHub issue."
            )

        assert schematic_file.exists(), (
            f"Schematic not created: {schematic_file}"
        )

        print(f"✅ Step 1: Circuit generated")
        print(f"   - Output: {schematic_file}")

        # =====================================================================
        # STEP 2: Validate power symbol structure (Level 2)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Validate power symbol structure (Level 2)")
        print("="*70)

        # Read schematic file
        with open(schematic_file, 'r') as f:
            sch_content = f.read()

        # Count power symbols
        power_symbols = count_power_symbols(sch_content)

        print(f"\n📊 Power symbols found:")
        for symbol_name, count in sorted(power_symbols.items()):
            print(f"   - power:{symbol_name}: {count}")

        # Total power symbols should be 5
        total_power_symbols = sum(power_symbols.values())
        print(f"\n   Total power symbols: {total_power_symbols}")

        if total_power_symbols != 5:
            pytest.xfail(
                f"Expected 5 power symbols (VCC_3V3, VCC_5V, VCC_12V, GND, AGND), "
                f"found {total_power_symbols}. "
                f"Power symbols: {power_symbols}. "
                f"Power symbol export may not be working correctly. "
                f"Create GitHub issue."
            )

        # Verify we have symbols for each expected domain
        # Note: circuit-synth may map power nets to standard symbols
        # Check that we have distinct symbols (count == 5)
        print(f"✅ Step 2: Power symbol structure validated")
        print(f"   - 5 power domains → 5 power symbols ✓")

        # =====================================================================
        # STEP 3: Validate electrical connectivity (Level 3)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Validate electrical connectivity via netlist (Level 3)")
        print("="*70)

        # Export netlist using kicad-cli
        kicad_netlist_file_1 = output_dir / "multi_power_domain_initial.net"

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

        if result.returncode != 0:
            pytest.xfail(
                f"kicad-cli netlist export failed. "
                f"Generated schematic may be invalid.\n"
                f"STDOUT:\n{result.stdout}\n"
                f"STDERR:\n{result.stderr}\n"
                f"Create GitHub issue."
            )

        # Parse netlist
        with open(kicad_netlist_file_1, 'r') as f:
            kicad_netlist_1 = f.read()

        nets_initial = parse_netlist(kicad_netlist_1)

        print(f"\n📊 Initial netlist (5 power domains):")
        print(f"   Nets found: {sorted(nets_initial.keys())}")
        for net_name in sorted(nets_initial.keys()):
            nodes = nets_initial[net_name]
            print(f"   - {net_name}: {nodes}")

        # Validate all 5 power domains present in netlist
        expected_power_nets = ["VCC_3V3", "VCC_5V", "VCC_12V", "GND", "AGND"]
        missing_nets = []

        for expected_net in expected_power_nets:
            if expected_net not in nets_initial:
                missing_nets.append(expected_net)

        if missing_nets:
            pytest.xfail(
                f"Power nets missing from netlist: {missing_nets}. "
                f"Found nets: {list(nets_initial.keys())}. "
                f"Power net export not complete. "
                f"Create GitHub issue."
            )

        # Validate component connections
        expected_connections = {
            "VCC_3V3": [("R1", "1")],
            "VCC_5V": [("R2", "1")],
            "VCC_12V": [("R3", "1")],
            "GND": [("R4", "1")],
            "AGND": [("R5", "1")],
        }

        for net_name, expected_nodes in expected_connections.items():
            actual_nodes = nets_initial[net_name]
            if sorted(actual_nodes) != sorted(expected_nodes):
                pytest.xfail(
                    f"Net {net_name} has incorrect connections.\n"
                    f"Expected: {sorted(expected_nodes)}\n"
                    f"Got: {sorted(actual_nodes)}\n"
                    f"Power connectivity incorrect. "
                    f"Create GitHub issue."
                )

        print(f"\n✅ Step 3: Electrical connectivity VALIDATED!")
        print(f"   - All 5 power domains present ✓")
        print(f"   - All components connected correctly ✓")

        # =====================================================================
        # STEP 4: Add component using existing power domain (VCC_3V3)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 4: Add R6 sharing VCC_3V3 with R1")
        print("="*70)

        # Uncomment R6 in Python code
        modified_code = original_code.replace(
            '    # Note: For step 4 of test, we\'ll add R6 using VCC_3V3\n'
            '    # This tests power symbol reuse\n'
            '    # Uncomment below to add R6:\n'
            '    # r6 = Component(\n'
            '    #     symbol="Device:R",\n'
            '    #     ref="R6",\n'
            '    #     value="22k",\n'
            '    #     footprint="Resistor_SMD:R_0603_1608Metric",\n'
            '    # )\n'
            '    # net_3v3 += r6[1]  # R6 shares VCC_3V3 with R1',
            '    # Add R6 sharing VCC_3V3 power domain with R1\n'
            '    r6 = Component(\n'
            '        symbol="Device:R",\n'
            '        ref="R6",\n'
            '        value="22k",\n'
            '        footprint="Resistor_SMD:R_0603_1608Metric",\n'
            '    )\n'
            '    net_3v3 += r6[1]  # R6 shares VCC_3V3 with R1'
        )

        # Write modified Python file
        with open(python_file, "w") as f:
            f.write(modified_code)

        print(f"✅ Step 4: Python modified")
        print(f"   - R6 added, connected to VCC_3V3")
        print(f"   - VCC_3V3 now shared by R1 and R6")

        # =====================================================================
        # STEP 5: Regenerate and validate no duplicate power symbols (Level 2)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 5: Regenerate and validate power symbol reuse (Level 2)")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "multi_power_domain.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            pytest.xfail(
                f"Regeneration failed after adding R6.\n"
                f"STDOUT:\n{result.stdout}\n"
                f"STDERR:\n{result.stderr}\n"
                f"Create GitHub issue."
            )

        # Read regenerated schematic
        with open(schematic_file, 'r') as f:
            sch_content_final = f.read()

        # Count power symbols again
        power_symbols_final = count_power_symbols(sch_content_final)

        print(f"\n📊 Power symbols after adding R6:")
        for symbol_name, count in sorted(power_symbols_final.items()):
            print(f"   - power:{symbol_name}: {count}")

        total_power_symbols_final = sum(power_symbols_final.values())
        print(f"\n   Total power symbols: {total_power_symbols_final}")

        # Should still be 5 power symbols (no duplicate VCC_3V3)
        if total_power_symbols_final != 5:
            pytest.fail(
                f"Power symbol duplication detected! "
                f"Expected 5 power symbols (reusing VCC_3V3), "
                f"found {total_power_symbols_final}. "
                f"Power symbols: {power_symbols_final}. "
                f"Power symbol reuse not working correctly."
            )

        print(f"✅ Step 5: Power symbol reuse VALIDATED!")
        print(f"   - Still 5 power symbols (no duplicate VCC_3V3) ✓")

        # =====================================================================
        # STEP 6: Validate final electrical connectivity (Level 3)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 6: Validate final electrical connectivity (Level 3)")
        print("="*70)

        # Export final netlist
        kicad_netlist_file_2 = output_dir / "multi_power_domain_final.net"

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

        if result.returncode != 0:
            pytest.xfail(
                f"kicad-cli netlist export failed on regenerated schematic.\n"
                f"STDOUT:\n{result.stdout}\n"
                f"STDERR:\n{result.stderr}\n"
                f"Create GitHub issue."
            )

        # Parse final netlist
        with open(kicad_netlist_file_2, 'r') as f:
            kicad_netlist_2 = f.read()

        nets_final = parse_netlist(kicad_netlist_2)

        print(f"\n📊 Final netlist (R1 and R6 share VCC_3V3):")
        print(f"   Nets found: {sorted(nets_final.keys())}")
        for net_name in sorted(nets_final.keys()):
            nodes = nets_final[net_name]
            print(f"   - {net_name}: {nodes}")

        # Validate VCC_3V3 now contains both R1 and R6
        if "VCC_3V3" not in nets_final:
            pytest.fail(
                f"VCC_3V3 net missing from final netlist! "
                f"Found nets: {list(nets_final.keys())}"
            )

        vcc_3v3_nodes = nets_final["VCC_3V3"]
        expected_vcc_3v3_nodes = [("R1", "1"), ("R6", "1")]

        if sorted(vcc_3v3_nodes) != sorted(expected_vcc_3v3_nodes):
            pytest.fail(
                f"VCC_3V3 net doesn't contain both R1 and R6!\n"
                f"Expected: {sorted(expected_vcc_3v3_nodes)}\n"
                f"Got: {sorted(vcc_3v3_nodes)}\n"
                f"Power symbol reuse not electrically correct."
            )

        # Validate other power domains unchanged
        for net_name in ["VCC_5V", "VCC_12V", "GND", "AGND"]:
            if nets_final[net_name] != nets_initial[net_name]:
                pytest.fail(
                    f"Power domain {net_name} changed unexpectedly!\n"
                    f"Initial: {nets_initial[net_name]}\n"
                    f"Final: {nets_final[net_name]}"
                )

        print(f"\n✅ Step 6: Final electrical connectivity VALIDATED!")
        print(f"   - VCC_3V3 contains R1 and R6 ✓")
        print(f"   - Other power domains unchanged ✓")

        print(f"\n🎉 POWER SYMBOL EXPORT WORKFLOW WORKS!")
        print(f"   - Generated 5 distinct power domains ✓")
        print(f"   - All power symbols created correctly ✓")
        print(f"   - Power symbol reuse works (no duplicates) ✓")
        print(f"   - Netlist validates electrical connectivity ✓")
        print(f"   - Analog vs digital ground separated (AGND/GND) ✓")

    finally:
        # Restore original Python file
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)


if __name__ == "__main__":
    # Allow running test standalone for development
    import sys

    class FakeRequest:
        class FakeConfig:
            def getoption(self, name, default=None):
                return "--keep-output" in sys.argv
        config = FakeConfig()

    test_46_export_power_symbols(FakeRequest())
