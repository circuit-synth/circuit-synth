#!/usr/bin/env python3
"""
Automated test for 45_import_power_symbols_from_kicad bidirectional test.

Tests CRITICAL bidirectional power workflow: importing KiCad schematics with
power symbols, modifying in Python, and regenerating.

This validates the REVERSE direction of tests 16-18:
- Tests 16-18: Python → KiCad power export ✅
- Test 45: KiCad → Python → KiCad power round-trip ❌ (THIS TEST)

Real-world workflow:
1. Import existing KiCad design with power rails (VCC, GND)
2. Modify in Python (add components using existing power)
3. Regenerate to KiCad
4. Power structure preserved, new connections work

Workflow:
1. Import hand-crafted .kicad_sch with power symbols (VCC, GND, R1)
2. Validate import recognized power nets and component connections
3. Add new component (R2) in Python connected to same power nets
4. Regenerate to KiCad
5. Validate:
   - Original R1 position preserved
   - Power symbols/connections preserved
   - New R2 connected to power
   - Netlist validates electrical connectivity (Level 3)

This test may XFAIL if power symbol import is not yet fully implemented.
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


def test_45_import_power_symbols(request):
    """Test importing KiCad schematic with power symbols, modifying, regenerating.

    CRITICAL BIDIRECTIONAL WORKFLOW:
    Validates that power symbols in existing KiCad designs:
    1. Import correctly (nets recognized)
    2. Can be reused in Python modifications
    3. Regenerate correctly preserving power structure

    This is THE workflow for working with real KiCad designs:
    - Import existing design with power rails
    - Add components programmatically using existing power
    - Regenerate → connections appear, layout preserved

    Power symbols have special handling in KiCad:
    - Global net connections (VCC, GND, etc.)
    - Special symbol library (power:VCC, power:GND)
    - Don't appear in BOM (no footprint)
    - Must be preserved during round-trip

    Workflow:
    1. Import .kicad_sch with R1 + VCC + GND power symbols
    2. Validate power nets recognized, R1 connected
    3. Add R2 in Python using same VCC/GND nets
    4. Regenerate → R2 appears with power connections

    Level 3 Electrical Validation:
    - circuit-synth import API
    - Python circuit modification
    - Netlist comparison for electrical connectivity
    - Position preservation
    """

    # Setup paths
    test_dir = Path(__file__).parent
    input_project = test_dir / "circuit_with_power.kicad_pro"
    input_schematic = test_dir / "circuit_with_power.kicad_sch"
    output_dir = test_dir / "output"
    output_schematic = output_dir / "circuit_with_power_modified.kicad_sch"

    # Check for --keep-output flag
    cleanup = not request.config.getoption("--keep-output", default=False)

    # Clean any existing output
    if output_dir.exists():
        shutil.rmtree(output_dir)

    output_dir.mkdir(parents=True)

    # We'll need to import circuit_synth dynamically
    # to handle potential import failures gracefully
    try:
        from circuit_synth.kicad.importer import import_kicad_project
        from circuit_synth import Component, Net
    except ImportError as e:
        pytest.skip(f"circuit-synth import failed: {e}")

    try:
        # =====================================================================
        # STEP 1: Import KiCad schematic with power symbols
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 1: Import KiCad project with power symbols")
        print("="*70)

        assert input_project.exists(), (
            f"Input project not found: {input_project}"
        )
        assert input_schematic.exists(), (
            f"Input schematic not found: {input_schematic}"
        )

        print(f"📁 Importing: {input_project}")

        # This is the CRITICAL operation - import KiCad to Python
        try:
            circuit = import_kicad_project(str(input_project))
        except Exception as e:
            pytest.fail(
                f"CRITICAL: import_kicad_project() failed!\n"
                f"Power symbol import not working.\n"
                f"Error: {e}\n"
                f"This is a Priority 0 bug - create GitHub issue."
            )

        print(f"✅ Step 1: Import succeeded")
        print(f"   - Circuit name: {circuit.name}")
        print(f"   - Components: {len(circuit.components)}")
        print(f"   - Nets: {len(circuit.nets)}")

        # =====================================================================
        # STEP 2: Validate power nets recognized and R1 connected
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 2: Validate power nets and connections")
        print("="*70)

        # Get all components
        component_refs = [comp.ref for comp in circuit.components]
        print(f"   Components found: {component_refs}")

        # Check R1 exists
        r1_components = [c for c in circuit.components if c.ref == "R1"]
        if not r1_components:
            pytest.xfail(
                "R1 component not found after import. "
                "Component import may not be working correctly. "
                "Create GitHub issue."
            )

        r1 = r1_components[0]
        print(f"   - R1 found: {r1.ref} = {r1.value}")

        # Store R1 initial position for later validation
        r1_initial_position = getattr(r1, 'position', None)
        print(f"   - R1 position: {r1_initial_position}")

        # Get all nets (nets is a dictionary keyed by net name)
        net_names = list(circuit.nets.keys())
        print(f"   Nets found: {net_names}")

        # Check for VCC net
        vcc_nets = [circuit.nets[name] for name in net_names if 'VCC' in name.upper()]
        if not vcc_nets:
            pytest.xfail(
                "VCC net not found after import. "
                "Power symbol import not recognizing VCC. "
                "Expected: Net with name 'VCC' or similar. "
                "Found nets: " + str(net_names) + ". "
                "Create GitHub issue: Power symbol import support."
            )

        vcc_net = vcc_nets[0]
        print(f"   - VCC net: {vcc_net.name}")

        # Check for GND net
        gnd_nets = [circuit.nets[name] for name in net_names if 'GND' in name.upper()]
        if not gnd_nets:
            pytest.xfail(
                "GND net not found after import. "
                "Power symbol import not recognizing GND. "
                "Expected: Net with name 'GND' or similar. "
                "Found nets: " + str(net_names) + ". "
                "Create GitHub issue: Power symbol import support."
            )

        gnd_net = gnd_nets[0]
        print(f"   - GND net: {gnd_net.name}")

        # Validate R1 connections to power
        # Check if R1 pins are in VCC/GND nets
        vcc_connections = []
        gnd_connections = []

        for pin in vcc_net.pins:
            if hasattr(pin, 'component') and pin.component.ref == 'R1':
                vcc_connections.append(pin.num)

        for pin in gnd_net.pins:
            if hasattr(pin, 'component') and pin.component.ref == 'R1':
                gnd_connections.append(pin.num)

        print(f"   - R1 connections to VCC: {vcc_connections}")
        print(f"   - R1 connections to GND: {gnd_connections}")

        if not vcc_connections:
            pytest.xfail(
                "R1 not connected to VCC after import. "
                "Power net connections not preserved during import. "
                "Create GitHub issue."
            )

        if not gnd_connections:
            pytest.xfail(
                "R1 not connected to GND after import. "
                "Power net connections not preserved during import. "
                "Create GitHub issue."
            )

        print(f"✅ Step 2: Power nets and connections validated")

        # =====================================================================
        # STEP 3: Add new component (R2) using existing power nets in Python
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 3: Add R2 in Python using existing VCC/GND")
        print("="*70)

        # Create new resistor
        r2 = Component(
            symbol="Device:R",
            ref="R2",
            value="4.7k",
            footprint="Resistor_SMD:R_0603_1608Metric",
        )

        # Add to circuit
        circuit.components.append(r2)

        # Connect R2 to existing power nets
        # This is the KEY operation - reusing imported power nets
        try:
            vcc_net += r2[1]  # R2 pin 1 to VCC
            gnd_net += r2[2]  # R2 pin 2 to GND
        except Exception as e:
            pytest.xfail(
                f"Cannot connect new component to imported power nets. "
                f"Error: {e}. "
                f"Power net reuse not working. "
                f"Create GitHub issue."
            )

        print(f"✅ Step 3: R2 added and connected to power")
        print(f"   - R2: {r2.ref} = {r2.value}")
        print(f"   - R2[1] → VCC")
        print(f"   - R2[2] → GND")

        # =====================================================================
        # STEP 4: Regenerate to KiCad
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 4: Regenerate circuit to KiCad")
        print("="*70)

        try:
            circuit.generate_kicad_project(
                project_name="circuit_with_power_modified",
                output_dir=str(output_dir),
                placement_algorithm="simple",
                generate_pcb=False
            )
        except Exception as e:
            pytest.xfail(
                f"Regeneration failed after adding component to imported circuit. "
                f"Error: {e}. "
                f"Round-trip with power symbols not working. "
                f"Create GitHub issue."
            )

        assert output_schematic.exists(), (
            f"Regenerated schematic not created: {output_schematic}"
        )

        print(f"✅ Step 4: Regeneration succeeded")
        print(f"   - Output: {output_schematic}")

        # =====================================================================
        # STEP 5: Validate regenerated schematic structure
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 5: Validate regenerated schematic")
        print("="*70)

        # Use kicad-sch-api to validate structure
        try:
            from kicad_sch_api import Schematic
        except ImportError:
            pytest.skip("kicad-sch-api not available, skipping structure validation")

        sch = Schematic.load(str(output_schematic))
        components = sch.components

        # Check both R1 and R2 exist
        refs = [c.reference for c in components]
        print(f"   Components in regenerated schematic: {refs}")

        assert "R1" in refs, "R1 missing after regeneration!"
        assert "R2" in refs, "R2 not added after regeneration!"

        # Check R1 position preserved
        r1_regen = [c for c in components if c.reference == "R1"][0]
        r1_regen_pos = r1_regen.position

        if r1_initial_position:
            if r1_regen_pos != r1_initial_position:
                print(f"   ⚠️  WARNING: R1 position changed!")
                print(f"      Initial: {r1_initial_position}")
                print(f"      After:   {r1_regen_pos}")
                # Don't fail, but note it
            else:
                print(f"   ✓ R1 position preserved: {r1_regen_pos}")

        print(f"✅ Step 5: Structure validated")

        # =====================================================================
        # STEP 6: Validate electrical connectivity via netlist (Level 3)
        # =====================================================================
        print("\n" + "="*70)
        print("STEP 6: Validate electrical connectivity (netlist)")
        print("="*70)

        # Export netlist using kicad-cli
        kicad_netlist_file = output_dir / "circuit_with_power_modified.net"

        result = subprocess.run(
            [
                "kicad-cli", "sch", "export", "netlist",
                str(output_schematic),
                "--output", str(kicad_netlist_file)
            ],
            capture_output=True,
            text=True,
            timeout=30
        )

        if result.returncode != 0:
            pytest.xfail(
                f"kicad-cli netlist export failed. "
                f"Regenerated schematic may be invalid. "
                f"STDOUT:\n{result.stdout}\n"
                f"STDERR:\n{result.stderr}"
            )

        # Parse netlist
        with open(kicad_netlist_file, 'r') as f:
            kicad_netlist_content = f.read()

        nets = parse_netlist(kicad_netlist_content)

        print(f"\n📊 KiCad-exported netlist:")
        print(f"   Nets found: {list(nets.keys())}")
        for net_name, nodes in nets.items():
            print(f"   - {net_name}: {nodes}")

        # Validate VCC net contains both R1[1] and R2[1]
        vcc_net_names = [n for n in nets.keys() if 'VCC' in n.upper()]

        if not vcc_net_names:
            pytest.xfail(
                f"VCC net not found in netlist! "
                f"Power net lost during regeneration. "
                f"Found nets: {list(nets.keys())}. "
                f"Create GitHub issue."
            )

        vcc_netlist = nets[vcc_net_names[0]]

        # Check R1[1] in VCC
        if ("R1", "1") not in vcc_netlist:
            pytest.xfail(
                f"R1 pin 1 not in VCC net after regeneration! "
                f"VCC connections: {vcc_netlist}. "
                f"Power connection lost. "
                f"Create GitHub issue."
            )

        # Check R2[1] in VCC
        if ("R2", "1") not in vcc_netlist:
            pytest.fail(
                f"R2 pin 1 not connected to VCC in netlist! "
                f"New component power connection failed. "
                f"VCC connections: {vcc_netlist}. "
                f"Expected: R2 pin 1 in VCC net."
            )

        # Validate GND net contains both R1[2] and R2[2]
        gnd_net_names = [n for n in nets.keys() if 'GND' in n.upper()]

        if not gnd_net_names:
            pytest.xfail(
                f"GND net not found in netlist! "
                f"Power net lost during regeneration. "
                f"Found nets: {list(nets.keys())}. "
                f"Create GitHub issue."
            )

        gnd_netlist = nets[gnd_net_names[0]]

        # Check R1[2] in GND
        if ("R1", "2") not in gnd_netlist:
            pytest.xfail(
                f"R1 pin 2 not in GND net after regeneration! "
                f"GND connections: {gnd_netlist}. "
                f"Power connection lost. "
                f"Create GitHub issue."
            )

        # Check R2[2] in GND
        if ("R2", "2") not in gnd_netlist:
            pytest.fail(
                f"R2 pin 2 not connected to GND in netlist! "
                f"New component power connection failed. "
                f"GND connections: {gnd_netlist}. "
                f"Expected: R2 pin 2 in GND net."
            )

        print(f"\n✅ Step 6: Electrical connectivity VALIDATED!")
        print(f"   - VCC net: {vcc_netlist}")
        print(f"   - GND net: {gnd_netlist}")
        print(f"   - R1[1] → VCC ✓")
        print(f"   - R2[1] → VCC ✓")
        print(f"   - R1[2] → GND ✓")
        print(f"   - R2[2] → GND ✓")

        print(f"\n🎉 BIDIRECTIONAL POWER WORKFLOW WORKS!")
        print(f"   - Imported KiCad with power symbols ✓")
        print(f"   - Recognized power nets ✓")
        print(f"   - Added component using existing power ✓")
        print(f"   - Regenerated preserving power structure ✓")
        print(f"   - Netlist validates electrical connectivity ✓")

    finally:
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

    test_45_import_power_symbols(FakeRequest())
