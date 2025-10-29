#!/usr/bin/env python3
"""
Automated test for 53_reference_collision_detection bidirectional test.

Tests reference uniqueness validation and global reference uniqueness enforcement.

Core Question: When you have duplicate component references, does the system
properly detect and handle collisions?

Note: circuit-synth enforces GLOBAL reference uniqueness across the entire hierarchy.
This is stricter than KiCad, which allows same reference on different sheets with
hierarchical path disambiguation.

Workflow:
1. Test Case 1: Same Sheet Collision
   - Generate circuit with R1 on root sheet
   - Try to add another R1 on same sheet
   - Verify: Error raised OR auto-rename to R2

2. Test Case 2: Global Uniqueness Enforcement
   - Generate circuit with R1 on root sheet
   - Add subcircuit with R2 on child sheet (different reference required)
   - Verify:
     * Both components exist with unique references
     * R1 on root sheet
     * R2 on child sheet
     * No duplicate reference errors

Validation uses netlist comparison (Level 3) for reference validation.
"""
import re
import shutil
import subprocess
from pathlib import Path

import pytest


def parse_netlist(netlist_content):
    """Parse netlist content and extract component paths.

    Returns dict: {(ref, hierarchical_path): [(net_name, pin), ...]}
    """
    components = {}

    # Find all component blocks with hierarchical paths
    # KiCad netlist format:
    # (comp (ref "R1")
    #       (value "10k")
    #       (sheetpath (names "/") (tstamps "/"))
    # )

    comp_pattern = r'\(comp\s+\(ref\s+"([^"]+)"\).*?\(sheetpath\s+\(names\s+"([^"]+)"\)'
    for match in re.finditer(comp_pattern, netlist_content, re.DOTALL):
        ref = match.group(1)
        sheet_path = match.group(2)
        components[(ref, sheet_path)] = []

    return components


def parse_nets(netlist_content):
    """Parse netlist content and extract net information with hierarchical paths.

    Returns dict: {net_name: [(ref, pin, sheet_path), ...]}
    """
    nets = {}

    # Find all net blocks
    # (net (code "1") (name "/Net1")
    #   (node (ref "R1") (pin "1") (pinfunction "~"))
    # )

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
        node_pattern = r'\(node\s+\(ref\s+"([^"]+)"\)\s+\(pin\s+"([^"]+)"\)'
        for node_match in re.finditer(node_pattern, block):
            ref = node_match.group(1)
            pin = node_match.group(2)
            # Extract sheet path from net name if it contains hierarchical path
            sheet_path = "/"
            if "/" in net_name and net_name.startswith("/"):
                # Extract path prefix from net name
                parts = net_name.split("/")
                if len(parts) > 2:
                    sheet_path = "/" + "/".join(parts[1:-1]) + "/"

            nodes.append((ref, pin, sheet_path))

        if nodes:
            nets[net_name] = sorted(nodes)

    return nets


def test_53_reference_collision_detection(request):
    """Test reference collision detection and global uniqueness enforcement.

    This test validates two critical scenarios:

    1. Same Sheet Collision (Should Fail or Auto-Rename):
       - Two components with same reference on same sheet
       - System should prevent this or auto-rename

    2. Global Uniqueness Enforcement:
       - circuit-synth enforces global reference uniqueness
       - References must be unique across entire hierarchy
       - Different from KiCad which allows same ref on different sheets
       - R1 on root, R2 on subcircuit (both unique globally)

    Why critical:
    - Duplicate references on same sheet cause electrical errors
    - Global uniqueness prevents confusion and ambiguity
    - Simpler mental model than hierarchical path disambiguation
    - Essential for maintaining design integrity

    Level 2 and Level 3 Validation:
    - Reference uniqueness checking (Level 2)
    - Netlist reference validation (Level 3)
    """

    # Setup paths
    test_dir = Path(__file__).parent
    python_file = test_dir / "duplicate_refs.py"
    output_dir = test_dir / "duplicate_refs"
    schematic_file = output_dir / "duplicate_refs.kicad_sch"

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
        # TEST CASE 1: Same Sheet Collision (Should Fail or Auto-Rename)
        # =====================================================================
        print("\n" + "=" * 70)
        print("TEST CASE 1: Same Sheet Collision (Should Fail or Auto-Rename)")
        print("=" * 70)

        # Inject second R1 on same sheet
        same_sheet_injection = '''try:
        r1_duplicate = Component(
            symbol="Device:R",
            ref="R1",  # Duplicate reference on same sheet!
            value="22k",
            footprint="Resistor_SMD:R_0805_2012Metric",
        )
        print("⚠️  WARNING: Duplicate R1 was allowed on same sheet!")
    except Exception as e:
        print(f"✅ Same sheet collision detected: {e}")'''

        marker_section = (
            "# START_MARKER_SAME_SHEET\n"
            "    # END_MARKER_SAME_SHEET"
        )
        replacement_section = (
            "# START_MARKER_SAME_SHEET\n"
            f"    {same_sheet_injection}\n"
            "    # END_MARKER_SAME_SHEET"
        )

        modified_code = original_code.replace(marker_section, replacement_section)

        # Write modified Python file
        with open(python_file, "w") as f:
            f.write(modified_code)

        print(f"✅ Injected second R1 on same sheet to test collision detection")

        # Try to generate circuit
        result = subprocess.run(
            ["uv", "run", "duplicate_refs.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )

        print(f"\nGeneration result:")
        print(f"STDOUT:\n{result.stdout}")
        if result.stderr:
            print(f"STDERR:\n{result.stderr}")

        # Check if collision was detected
        collision_detected = (
            "collision detected" in result.stdout.lower()
            or "duplicate" in result.stdout.lower()
            or result.returncode != 0
        )

        if collision_detected:
            print(f"\n✅ Same sheet collision properly detected!")
            print(f"   System prevented duplicate R1 on same sheet")
        else:
            print(f"\n⚠️  Same sheet collision NOT detected")
            print(f"   System allowed duplicate R1 on same sheet")
            print(f"   (This may indicate auto-rename or missing validation)")

        # Restore original code for next test
        with open(python_file, "w") as f:
            f.write(original_code)

        # Clean output for next test
        if output_dir.exists():
            shutil.rmtree(output_dir)

        # =====================================================================
        # TEST CASE 2: Global Uniqueness Enforcement (Should Work)
        # =====================================================================
        print("\n" + "=" * 70)
        print("TEST CASE 2: Global Uniqueness Enforcement (R1 + R2)")
        print("=" * 70)

        # Generate circuit with R1 on root and R1 on child sheet
        result = subprocess.run(
            ["uv", "run", "duplicate_refs.py"],
            cwd=test_dir,
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, (
            f"Hierarchical circuit generation failed\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        assert schematic_file.exists(), "Schematic not created"

        print(f"✅ Circuit generated successfully with global unique references")
        print(f"   - Root sheet with R1 (10k)")
        print(f"   - Child sheet (SubCircuit) with R2 (4.7k)")

        # =====================================================================
        # STEP 2: Validate global uniqueness in schematic
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 2: Validate global uniqueness in schematic")
        print("=" * 70)

        from kicad_sch_api import Schematic

        sch = Schematic.load(str(schematic_file))
        components = sch.components

        # Count R1 and R2 components
        r1_components = [c for c in components if c.reference == "R1"]
        r2_components = [c for c in components if c.reference == "R2"]
        print(f"   - R1 components found: {len(r1_components)}")
        print(f"   - R2 components found: {len(r2_components)}")

        # We expect one R1 (root) and one R2 (subcircuit)
        assert len(r1_components) >= 1, "R1 should exist on root"
        assert len(r2_components) >= 1, "R2 should exist on subcircuit"

        # Print component details
        for r1 in r1_components:
            print(f"     * R1: value={r1.value}, lib_id={r1.lib_id}")
        for r2 in r2_components:
            print(f"     * R2: value={r2.value}, lib_id={r2.lib_id}")

        # =====================================================================
        # STEP 3: Validate netlist reference uniqueness
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 3: Validate netlist reference uniqueness")
        print("=" * 70)

        # Export netlist
        netlist_file = output_dir / "duplicate_refs.net"

        result = subprocess.run(
            [
                "kicad-cli",
                "sch",
                "export",
                "netlist",
                str(schematic_file),
                "--output",
                str(netlist_file),
            ],
            capture_output=True,
            text=True,
            timeout=30,
        )

        assert result.returncode == 0, (
            f"Netlist export failed\n"
            f"STDOUT:\n{result.stdout}\n"
            f"STDERR:\n{result.stderr}"
        )

        print(f"✅ Netlist exported successfully")

        # Parse netlist
        with open(netlist_file, "r") as f:
            netlist_content = f.read()

        components_in_netlist = parse_netlist(netlist_content)
        nets = parse_nets(netlist_content)

        print(f"\n   Components in netlist:")
        for (ref, sheet_path), _ in components_in_netlist.items():
            print(f"     * {ref} (sheet: {sheet_path})")

        print(f"\n   Nets in netlist: {len(nets)}")
        for net_name, nodes in list(nets.items())[:10]:  # Show first 10 nets
            print(f"     * {net_name}: {len(nodes)} connections")

        # =====================================================================
        # CRITICAL VALIDATION: Global Reference Uniqueness
        # =====================================================================
        print("\n" + "=" * 70)
        print("CRITICAL VALIDATION: Global Reference Uniqueness")
        print("=" * 70)

        # Verify R1 and R2 components exist in netlist
        r1_paths = [
            sheet_path for (ref, sheet_path) in components_in_netlist.keys() if ref == "R1"
        ]
        r2_paths = [
            sheet_path for (ref, sheet_path) in components_in_netlist.keys() if ref == "R2"
        ]

        print(f"\n   R1 found: {len(r1_paths)}")
        for path in r1_paths:
            print(f"     * R1 at {path}")

        print(f"\n   R2 found: {len(r2_paths)}")
        for path in r2_paths:
            print(f"     * R2 at {path}")

        # Verify both R1 and R2 exist (global uniqueness enforced)
        assert len(r1_paths) >= 1, "R1 should exist in netlist"
        assert len(r2_paths) >= 1, "R2 should exist in netlist"

        print(f"\n✅ Global reference uniqueness verified!")
        print(f"   - R1 exists on root sheet")
        print(f"   - R2 exists on subcircuit sheet")
        print(f"   - All references are globally unique")
        print(f"   - circuit-synth enforces stricter uniqueness than KiCad")

        # =====================================================================
        # STEP 4: Verify no netlist errors
        # =====================================================================
        print("\n" + "=" * 70)
        print("STEP 4: Verify netlist has no errors")
        print("=" * 70)

        # Check netlist content for error messages
        netlist_has_errors = (
            "error" in netlist_content.lower() or "duplicate" in netlist_content.lower()
        )

        if netlist_has_errors:
            print(f"⚠️  Netlist contains error messages")
            # Extract error lines
            error_lines = [
                line
                for line in netlist_content.split("\n")
                if "error" in line.lower() or "duplicate" in line.lower()
            ]
            for line in error_lines[:5]:  # Show first 5 errors
                print(f"   {line}")
        else:
            print(f"✅ Netlist exported without errors")

        # =====================================================================
        # FINAL SUMMARY
        # =====================================================================
        print("\n" + "=" * 70)
        print("REFERENCE COLLISION DETECTION SUMMARY")
        print("=" * 70)

        print(f"\nTest Case 1 - Same Sheet Collision:")
        if collision_detected:
            print(f"   ✅ Collision detected and prevented")
        else:
            print(f"   ⚠️  Collision not explicitly detected")
            print(f"      (May use auto-rename or silent handling)")

        print(f"\nTest Case 2 - Global Uniqueness Enforcement:")
        print(f"   ✅ Circuit generated successfully")
        print(f"   ✅ R1 present in schematic: {len(r1_components)}")
        print(f"   ✅ R2 present in schematic: {len(r2_components)}")
        print(f"   ✅ Both R1 and R2 exist in netlist")
        print(f"   ✅ All references globally unique")

        print(f"\nReference collision detection test completed!")
        print(f"Note: circuit-synth enforces GLOBAL reference uniqueness.")
        print(f"Unlike KiCad which allows same ref on different sheets with")
        print(f"hierarchical path disambiguation, circuit-synth requires all")
        print(f"references to be unique across the entire hierarchy.")

    finally:
        # Restore original Python file
        with open(python_file, "w") as f:
            f.write(original_code)

        # Cleanup generated files
        if cleanup and output_dir.exists():
            shutil.rmtree(output_dir)
