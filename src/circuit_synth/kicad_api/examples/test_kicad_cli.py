#!/usr/bin/env python3
"""
Test script for KiCad CLI integration.

This script demonstrates:
1. Automatic kicad-cli detection
2. Running DRC on a PCB
3. Exporting manufacturing files
4. Basic rule checking without CLI
"""

import json
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from circuit_synth.kicad_api.pcb import KiCadCLIError, PCBBoard, get_kicad_cli


def test_cli_detection():
    """Test automatic detection of kicad-cli."""
    print("Testing KiCad CLI detection...")
    try:
        cli = get_kicad_cli()
        print(f"✓ Found kicad-cli at: {cli.kicad_cli_path}")

        # Get version
        version = cli.get_version()
        print(f"✓ KiCad version: {version}")
        return cli
    except Exception as e:
        print(f"✗ Failed to find kicad-cli: {e}")
        return None


def test_basic_drc():
    """Test basic DRC without KiCad CLI."""
    print("\nTesting basic rule checking...")

    # Create a test PCB with some issues
    pcb = PCBBoard()

    # Add components without board outline
    pcb.add_footprint("R1", "Resistor_SMD:R_0603_1608Metric", 50, 50, value="10k")
    pcb.add_footprint(
        "R2", "Resistor_SMD:R_0603_1608Metric", 52, 52, value="10k"
    )  # Very close
    pcb.add_footprint("C1", "Capacitor_SMD:C_0603_1608Metric", 60, 50, value="100nF")

    # Connect some pads but not all
    pcb.connect_pads("R1", "1", "R2", "1", "NET1")
    # R1.2 and C1 remain unconnected

    # Run basic checks
    violations = pcb.check_basic_rules()

    print("\nBasic rule check results:")
    if violations:
        for rule, issues in violations.items():
            print(f"\n{rule}:")
            for issue in issues:
                print(f"  - {issue}")
    else:
        print("  No violations found")

    return pcb


def test_cli_drc(pcb, cli):
    """Test DRC using KiCad CLI."""
    print("\nTesting DRC with KiCad CLI...")

    if not cli:
        print("  Skipping - CLI not available")
        return

    try:
        # Save PCB to temp file and run DRC
        result = pcb.run_drc(temp_file=True, format="json")

        print(f"\nDRC Results:")
        print(f"  Success: {result.success}")
        print(f"  Total issues: {result.total_issues}")
        print(f"  Violations: {len(result.violations)}")
        print(f"  Warnings: {len(result.warnings)}")
        print(f"  Unconnected: {len(result.unconnected_items)}")

        # Show some details
        if result.violations:
            print("\n  Sample violations:")
            for v in result.violations[:3]:
                print(f"    - {v.get('description', 'Unknown violation')}")

        if result.unconnected_items:
            print("\n  Unconnected items:")
            for item in result.unconnected_items[:3]:
                print(f"    - {item.get('description', 'Unknown item')}")

    except KiCadCLIError as e:
        print(f"  DRC failed: {e}")
        if hasattr(e, "stderr"):
            print(f"  Error output: {e.stderr}")


def test_manufacturing_export(pcb, cli):
    """Test exporting manufacturing files."""
    print("\nTesting manufacturing file export...")

    if not cli:
        print("  Skipping - CLI not available")
        return

    # First, let's add a board outline
    pcb.set_board_outline_rect(0, 0, 100, 80)

    # Save the PCB
    output_dir = Path("test_output")
    output_dir.mkdir(exist_ok=True)

    pcb_file = output_dir / "test_board.kicad_pcb"
    pcb.save(pcb_file)
    print(f"  Saved PCB to: {pcb_file}")

    try:
        # Export Gerbers
        print("\n  Exporting Gerbers...")
        gerber_dir = output_dir / "gerbers"
        gerber_files = pcb.export_gerbers(gerber_dir)
        print(f"    Generated {len(gerber_files)} Gerber files:")
        for f in gerber_files[:5]:  # Show first 5
            print(f"      - {f.name}")

        # Export drill files
        print("\n  Exporting drill files...")
        drill_dir = output_dir / "drill"
        plated, non_plated = pcb.export_drill(drill_dir)
        if plated:
            print(f"    Plated holes: {plated.name}")
        if non_plated:
            print(f"    Non-plated holes: {non_plated.name}")

        # Export pick and place
        print("\n  Exporting pick and place...")
        pnp_file = output_dir / "pick_and_place.csv"
        pnp = pcb.export_pick_and_place(pnp_file)
        print(f"    Position file: {pnp.name}")

    except Exception as e:
        print(f"  Export failed: {e}")


def demonstrate_custom_drc_rules():
    """Demonstrate custom DRC rules (informational)."""
    print("\n" + "=" * 60)
    print("Custom DRC Rules Information")
    print("=" * 60)

    print(
        """
KiCad CLI DRC uses rules embedded in the PCB file or project settings.
Custom rules cannot be passed via command line in current versions.

To use custom DRC rules:

1. Define rules in the PCB file's setup section:
   (setup
     (rules
       (rule "Minimum trace width"
         (constraint track_width (min 0.2mm))
       )
       (rule "Via size"
         (constraint via_diameter (min 0.6mm))
       )
     )
   )

2. Or define in a .kicad_dru file in the project directory

3. Or use KiCad's GUI to set up custom rules

The PCB API can programmatically add these rules to the setup section
before running DRC if needed.
"""
    )


def main():
    """Run all tests."""
    print("KiCad CLI Integration Test")
    print("=" * 60)

    # Test CLI detection
    cli = test_cli_detection()

    # Test basic DRC
    pcb = test_basic_drc()

    # Test CLI DRC
    test_cli_drc(pcb, cli)

    # Test manufacturing export
    test_manufacturing_export(pcb, cli)

    # Show custom DRC info
    demonstrate_custom_drc_rules()

    print("\n" + "=" * 60)
    print("Test completed!")


if __name__ == "__main__":
    main()
