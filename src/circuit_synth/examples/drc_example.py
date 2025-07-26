#!/usr/bin/env python3
"""
Example of using DRC (Design Rule Check) with the PCB API.

This example creates a simple PCB with potential issues and runs DRC to find them.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from circuit_synth.kicad_api.pcb import PCBBoard, get_kicad_cli, KiCadCLIError


def create_example_pcb():
    """Create a PCB with some common DRC issues."""
    print("Creating example PCB with potential DRC issues...")
    
    pcb = PCBBoard()
    
    # Set board outline
    pcb.set_board_outline_rect(0, 0, 100, 80)
    
    # Add components
    # Power section - using footprints that have automatic pad creation
    pcb.add_footprint("U1", "Package_TO_SOT_THT:TO-220-3_Vertical", 20, 20,
                     value="LM7805")
    pcb.add_footprint("C1", "Capacitor_SMD:C_0805_2012Metric", 35, 20,
                     value="100uF")
    pcb.add_footprint("C2", "Capacitor_SMD:C_0603_1608Metric", 45, 20,
                     value="100nF")
    
    # MCU section - placed too close to edge
    pcb.add_footprint("U2", "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", 95, 40,
                     value="ATtiny85")  # Too close to edge!
    
    # Resistors with one unconnected
    pcb.add_footprint("R1", "Resistor_SMD:R_0603_1608Metric", 50, 40,
                     value="10k")
    pcb.add_footprint("R2", "Resistor_SMD:R_0603_1608Metric", 50, 50,
                     value="10k")
    
    # Create nets and connections
    pcb.add_net("VCC")
    pcb.add_net("GND")
    pcb.add_net("VIN")
    pcb.add_net("SIGNAL1")
    
    # Connect power components
    pcb.connect_pads("U1", "1", "C1", "1", "VIN")    # Input
    pcb.connect_pads("U1", "2", "C1", "2", "GND")    # Ground
    pcb.connect_pads("U1", "2", "C2", "2", "GND")    # Ground
    pcb.connect_pads("U1", "3", "C2", "1", "VCC")    # Output
    
    # Connect MCU power
    pcb.connect_pads("U2", "8", "C2", "1", "VCC")    # VCC
    pcb.connect_pads("U2", "4", "C2", "2", "GND")    # GND
    
    # Connect one resistor, leave R2 floating (DRC issue!)
    pcb.connect_pads("R1", "1", "U2", "2", "SIGNAL1")
    pcb.connect_pads("R1", "2", "U2", "4", "GND")
    # R2 is intentionally left unconnected
    
    # Add some tracks with issues
    # Very thin track (potential DRC violation)
    pcb.add_track(50, 40, 50, 45, width=0.1, layer="F.Cu", net=pcb.get_net_by_name("SIGNAL1"))
    
    # Normal track
    pcb.add_track(20, 25, 35, 25, width=0.5, layer="F.Cu", net=pcb.get_net_by_name("VIN"))
    
    return pcb


def run_basic_checks(pcb):
    """Run basic DRC checks without KiCad CLI."""
    print("\n" + "="*60)
    print("Running basic rule checks (no KiCad CLI required)...")
    print("="*60)
    
    violations = pcb.check_basic_rules()
    
    if violations:
        print("\nFound the following issues:")
        for category, issues in violations.items():
            print(f"\n{category.upper()}:")
            for issue in issues:
                print(f"  ⚠️  {issue}")
    else:
        print("\n✓ No basic rule violations found")
    
    # Additional manual checks
    print("\nAdditional checks:")
    
    # Check component proximity to board edge
    # For rectangular board created with set_board_outline_rect
    edge_clearance = 2.0  # 2mm minimum from edge
    board_width = 100
    board_height = 80
    
    for ref, lib, x, y in pcb.list_footprints():
        if (x < edge_clearance or x > board_width - edge_clearance or
            y < edge_clearance or y > board_height - edge_clearance):
            print(f"  ⚠️  {ref} is too close to board edge")
    
    # Check for very thin tracks
    min_track_width = 0.2  # 0.2mm minimum
    for track in pcb.get_tracks():
        if track.width < min_track_width:
            print(f"  ⚠️  Track at ({track.start.x}, {track.start.y}) has width {track.width}mm (minimum: {min_track_width}mm)")


def run_kicad_drc(pcb):
    """Run full DRC using KiCad CLI if available."""
    print("\n" + "="*60)
    print("Running KiCad DRC...")
    print("="*60)
    
    try:
        cli = get_kicad_cli()
        print(f"✓ Found KiCad CLI: {cli.get_version()}")
    except KiCadCLIError as e:
        print(f"✗ KiCad CLI not available: {e}")
        print("  Install KiCad to use full DRC functionality")
        return
    
    # Save PCB and run DRC
    output_dir = Path("drc_example_output")
    output_dir.mkdir(exist_ok=True)
    
    pcb_file = output_dir / "example_board.kicad_pcb"
    pcb.save(pcb_file)
    print(f"\nSaved PCB to: {pcb_file}")
    
    try:
        # Run DRC (PCB is already saved, so it has a filepath now)
        print("\nRunning DRC...")
        result = pcb.run_drc(
            output_file=output_dir / "drc_report.json",
            format="json",
            severity="warning",  # Show warnings too
            save_before_drc=False  # Already saved
        )
        
        print(f"\nDRC Complete!")
        print(f"  Success: {result.success}")
        print(f"  Total issues: {result.total_issues}")
        
        if result.violations:
            print(f"\n❌ VIOLATIONS ({len(result.violations)}):")
            for v in result.violations:
                print(f"  - {v.get('type', 'Unknown')}: {v.get('description', 'No description')}")
                if 'items' in v:
                    for item in v['items']:
                        print(f"    • {item.get('description', item)}")
        
        if result.warnings:
            print(f"\n⚠️  WARNINGS ({len(result.warnings)}):")
            for w in result.warnings:
                print(f"  - {w.get('type', 'Unknown')}: {w.get('description', 'No description')}")
        
        if result.unconnected_items:
            print(f"\n🔌 UNCONNECTED ({len(result.unconnected_items)}):")
            for item in result.unconnected_items:
                print(f"  - {item.get('description', item)}")
        
        # Also generate a text report
        print("\nGenerating text report...")
        text_result = cli.run_drc(
            pcb_file=pcb_file,
            output_file=output_dir / "drc_report.txt",
            format="report"
        )
        print(f"  Text report saved to: {output_dir / 'drc_report.txt'}")
        
    except KiCadCLIError as e:
        print(f"\n❌ DRC failed: {e}")
        if hasattr(e, 'stderr') and e.stderr:
            print(f"Error details: {e.stderr}")


def main():
    """Run the DRC example."""
    print("PCB Design Rule Check (DRC) Example")
    print("=" * 60)
    
    # Create example PCB
    pcb = create_example_pcb()
    
    # Run basic checks
    run_basic_checks(pcb)
    
    # Run full KiCad DRC
    run_kicad_drc(pcb)
    
    print("\n" + "="*60)
    print("Example completed!")
    print("\nThis example demonstrated:")
    print("  1. Creating a PCB with intentional issues")
    print("  2. Running basic rule checks without KiCad")
    print("  3. Running full DRC with KiCad CLI")
    print("  4. Interpreting DRC results")


if __name__ == "__main__":
    main()