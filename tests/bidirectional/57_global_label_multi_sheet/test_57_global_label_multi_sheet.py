#!/usr/bin/env python3
"""
Automated test for 57_global_label_multi_sheet bidirectional test.

Tests CRITICAL multi-sheet connectivity: Using global labels to connect
peer subcircuits (NOT parent-child hierarchy) sharing signals like SPI bus.

This validates whether circuit-synth supports:
1. Global labels (not hierarchical labels) for cross-sheet connectivity
2. Peer sheets (flat design, not hierarchical parent-child)
3. Multiple sheets connected via matching global label names
4. Adding additional peer sheets maintaining connectivity

**Critical Context:**
- Test 24 found circuit-synth creates hierarchical_label (not global_label)
- This test validates the DESIRED behavior for flat multi-sheet designs
- May XFAIL initially if circuit-synth doesn't support global labels

Workflow:
1. Generate with 2 peer sheets using global label "SPI_CLK"
2. Validate global_label entries in .kicad_sch files (NOT hierarchical_label)
3. Validate netlist shows cross-sheet connectivity via SPI_CLK
4. Add third peer sheet with same SPI_CLK global label
5. Regenerate and validate all three sheets connected

Validation uses:
- Text search for "global_label" in .kicad_sch files (Level 2)
- Netlist comparison for cross-sheet connectivity (Level 3)
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
            nodes.append((ref, pin))

        if nodes:
            nets[net_name] = sorted(nodes)

    return nets


@pytest.mark.xfail(
    reason="circuit-synth uses hierarchical_label by design (see test 24), "
    "may not support global_label for peer sheet connectivity. "
    "This test documents DESIRED behavior for flat multi-sheet designs."
)
def test_57_global_label_multi_sheet(request):
    """Test global labels connecting multiple peer subcircuits.

    CRITICAL MULTI-SHEET CONNECTIVITY TEST:
    Validates whether circuit-synth supports global labels for connecting
    peer subcircuits without parent-child hierarchy.

    Architecture:
    - Main sheet: MCU with SPI master
    - Display sheet (peer): Display controller
    - Sensor sheet (peer): Sensor module (added later)

    Global labels "SPI_CLK", "SPI_MOSI", "SPI_MISO" should connect all sheets.

    This differs from hierarchical labels (test 22, 24) which require
    parent-child relationships and hierarchical pins.

    XFAIL EXPECTED:
    Test 24 found circuit-synth creates hierarchical_label (not global_label).
    If this test fails, it documents a gap in multi-sheet peer connectivity.

    Level 2 + Level 3 Validation:
    - Text search for "global_label" in .kicad_sch files
    - Netlist comparison for cross-sheet connectivity
    - Validates peer sheet architecture (not hierarchical)
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "spi_bus.py"
    output_dir = test_dir / "spi_bus"
    schematic_file = output_dir / "spi_bus.kicad_sch"

    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    # Clean any existing output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    # Read original Python file (2 sheets, sensor commented out)
    with open(python_file, "r") as f:
        original_code = f.read()

    try:
        # =====================================================================
        # STEP 1: Generate with 2 peer sheets (Main + Display)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Generate with 2 peer sheets using global labels")
        print("="*70)

        result = subprocess.run(
            ["uv", "run", "spi_bus.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=60  # Longer timeout for MCU symbol
        )

        assert result.returncode == 0, (
            f"Step 1 failed: Initial generation\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        assert schematic_file.exists(), "Root schematic not created"

        # Check how many schematic files were created
        sch_files = sorted(output_dir.glob("*.kicad_sch"))
        print(f"\n✅ Step 1: Schematic files generated")
        print(f"   - Total .kicad_sch files: {len(sch_files)}")
        for sch_file in sch_files:
            print(f"     * {sch_file.name}")

        # =====================================================================
        # STEP 2: Validate global_label entries in schematic files
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Validate global_label entries (Level 2)")
        print("="*70)

        global_label_count = 0
        hierarchical_label_count = 0
        files_with_global_labels = []
        files_with_hierarchical_labels = []

        for sch_file in sch_files:
            with open(sch_file, 'r') as f:
                sch_content = f.read()

            # Search for global_label entries (DESIRED)
            global_labels = len(re.findall(r'\(global_label\s+"([^"]+)"', sch_content))
            if global_labels > 0:
                global_label_count += global_labels
                files_with_global_labels.append((sch_file.name, global_labels))

            # Search for hierarchical_label entries (CURRENT behavior per test 24)
            hierarchical_labels = len(re.findall(r'\(hierarchical_label\s+"([^"]+)"', sch_content))
            if hierarchical_labels > 0:
                hierarchical_label_count += hierarchical_labels
                files_with_hierarchical_labels.append((sch_file.name, hierarchical_labels))

        print(f"\n📊 Label analysis:")
        print(f"   - Global labels (desired): {global_label_count}")
        if files_with_global_labels:
            for fname, count in files_with_global_labels:
                print(f"     * {fname}: {count} global labels")

        print(f"   - Hierarchical labels (current per test 24): {hierarchical_label_count}")
        if files_with_hierarchical_labels:
            for fname, count in files_with_hierarchical_labels:
                print(f"     * {fname}: {count} hierarchical labels")

        # CRITICAL ASSERTION: Test expects global labels (not hierarchical)
        assert global_label_count >= 2, (
            f"Expected at least 2 global_label entries (SPI_CLK on 2 sheets), "
            f"found {global_label_count}.\n\n"
            f"Found {hierarchical_label_count} hierarchical_label entries instead.\n"
            f"This indicates circuit-synth uses hierarchical labels by design.\n\n"
            f"Test XFAIL reason: circuit-synth doesn't support global labels for "
            f"peer sheet connectivity (flat multi-sheet designs)."
        )

        print(f"\n✅ Step 2: Global labels found in schematic files")

        # Search for specific SPI signal global labels
        spi_signals = ["SPI_CLK", "SPI_MOSI", "SPI_MISO"]
        for signal in spi_signals:
            signal_found = False
            for sch_file in sch_files:
                with open(sch_file, 'r') as f:
                    if f'global_label "{signal}"' in f.read():
                        signal_found = True
                        break

            print(f"   - Global label '{signal}': {'✓ Found' if signal_found else '✗ Not found'}")

        # =====================================================================
        # STEP 3: Validate netlist shows cross-sheet connectivity
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Validate cross-sheet connectivity (Level 3 - Netlist)")
        print("="*70)

        # Export netlist using kicad-cli
        kicad_netlist_file = output_dir / "spi_bus_kicad.net"

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

        # Parse netlist
        with open(kicad_netlist_file, 'r') as f:
            kicad_netlist_content = f.read()

        nets = parse_netlist(kicad_netlist_content)

        print(f"\n📊 KiCad-exported netlist:")
        print(f"   Nets found: {len(nets)}")
        for net_name in sorted(nets.keys()):
            nodes = nets[net_name]
            print(f"   - {net_name}: {nodes}")

        # Validate SPI_CLK connects components from different sheets
        assert "SPI_CLK" in nets, (
            f"SPI_CLK net not found in netlist! Found: {list(nets.keys())}"
        )

        spi_clk_nodes = nets["SPI_CLK"]
        spi_clk_components = {node[0] for node in spi_clk_nodes}

        # Should have at least MCU (U1) and Display (R1)
        assert "U1" in spi_clk_components, "MCU (U1) not connected to SPI_CLK"
        assert "R1" in spi_clk_components, "Display (R1) not connected to SPI_CLK"

        print(f"\n✅ Step 3: Cross-sheet connectivity VALIDATED!")
        print(f"   - SPI_CLK connects: {spi_clk_components}")
        print(f"   - Components from multiple sheets electrically connected")

        # =====================================================================
        # STEP 4: Add third peer sheet (Sensor)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 4: Add third peer sheet (Sensor)")
        print("="*70)

        # Uncomment sensor sheet section
        modified_code = original_code.replace(
            '    # sensor_sheet = Circuit("SensorSheet")\n'
            '    #\n'
            '    # sensor = Component(\n'
            '    #     symbol="Device:R",  # Simplified - using resistor as placeholder\n'
            '    #     ref="R2",\n'
            '    #     value="4.7k",\n'
            '    #     footprint="Resistor_SMD:R_0603_1608Metric",\n'
            '    # )\n'
            '    #\n'
            '    # sensor_sheet.add_component(sensor)\n'
            '    #\n'
            '    # # Connect sensor to same global label nets\n'
            '    # sensor[1] += spi_clk   # Sensor CLK pin\n'
            '    # sensor[2] += spi_miso  # Sensor MISO pin\n'
            '    #\n'
            '    # # Add sensor sheet as PEER (not parent-child hierarchy)\n'
            '    # root.add_subcircuit(sensor_sheet)',
            '    sensor_sheet = Circuit("SensorSheet")\n'
            '\n'
            '    sensor = Component(\n'
            '        symbol="Device:R",  # Simplified - using resistor as placeholder\n'
            '        ref="R2",\n'
            '        value="4.7k",\n'
            '        footprint="Resistor_SMD:R_0603_1608Metric",\n'
            '    )\n'
            '\n'
            '    sensor_sheet.add_component(sensor)\n'
            '\n'
            '    # Connect sensor to same global label nets\n'
            '    sensor[1] += spi_clk   # Sensor CLK pin\n'
            '    sensor[2] += spi_miso  # Sensor MISO pin\n'
            '\n'
            '    # Add sensor sheet as PEER (not parent-child hierarchy)\n'
            '    root.add_subcircuit(sensor_sheet)'
        )

        # Write modified Python file
        with open(python_file, "w") as f:
            f.write(modified_code)

        print(f"✅ Step 4: Third peer sheet (Sensor) added to Python code")

        # =====================================================================
        # STEP 5: Regenerate with three sheets
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 5: Regenerate with three peer sheets")
        print("="*70)

        # Remove old output
        if output_dir.exists():
            shutil.rmtree(output_dir)

        result = subprocess.run(
            ["uv", "run", "spi_bus.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=60
        )

        assert result.returncode == 0, (
            f"Step 5 failed: Regeneration with 3 sheets\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        # Check schematic files
        sch_files_final = sorted(output_dir.glob("*.kicad_sch"))
        print(f"\n✅ Step 5: Regenerated with 3 peer sheets")
        print(f"   - Total .kicad_sch files: {len(sch_files_final)}")
        for sch_file in sch_files_final:
            print(f"     * {sch_file.name}")

        # =====================================================================
        # STEP 6: Validate third sheet connectivity
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 6: Validate third sheet connectivity")
        print("="*70)

        # Export netlist again
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

        assert result.returncode == 0, "kicad-cli netlist export failed"

        with open(kicad_netlist_file, 'r') as f:
            kicad_netlist_content = f.read()

        nets_final = parse_netlist(kicad_netlist_content)

        print(f"\n📊 Final netlist with 3 sheets:")
        for net_name in sorted(nets_final.keys()):
            nodes = nets_final[net_name]
            print(f"   - {net_name}: {nodes}")

        # Validate SPI_CLK now connects all three components
        assert "SPI_CLK" in nets_final, "SPI_CLK net not found after adding third sheet"

        spi_clk_nodes_final = nets_final["SPI_CLK"]
        spi_clk_components_final = {node[0] for node in spi_clk_nodes_final}

        # Should have MCU (U1), Display (R1), and Sensor (R2)
        assert "U1" in spi_clk_components_final, "MCU (U1) not connected to SPI_CLK"
        assert "R1" in spi_clk_components_final, "Display (R1) not connected to SPI_CLK"
        assert "R2" in spi_clk_components_final, "Sensor (R2) not connected to SPI_CLK"

        print(f"\n🎉 GLOBAL LABEL MULTI-SHEET CONNECTIVITY WORKS!")
        print(f"   ✓ Three peer sheets generated")
        print(f"   ✓ Global labels connect sheets (not hierarchical)")
        print(f"   ✓ SPI_CLK connects: {spi_clk_components_final}")
        print(f"   ✓ Flat multi-sheet design pattern supported!")
        print(f"   ✓ Modular subsystem architecture validated!")

    finally:
        # Restore original Python file
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
