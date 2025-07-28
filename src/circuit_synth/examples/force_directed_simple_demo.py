#!/usr/bin/env python3
"""
Simple demonstration of force-directed placement algorithm.

This example creates a basic circuit using library footprints and
demonstrates physics-based component placement.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

from circuit_synth.kicad_api.pcb import PCBBoard


def main():
    """Run the simple force-directed placement demo."""
    print("Simple Force-Directed Placement Demo")
    print("=" * 50)

    # Create a new PCB
    pcb = PCBBoard()

    # Set board outline
    pcb.set_board_outline_rect(0, 0, 100, 80)

    print("\n1. Adding components from library...")

    # Add components using library footprints (these have proper pads)
    # Resistors
    pcb.add_footprint_from_library(
        "Resistor_SMD:R_0603_1608Metric", "R1", 20, 20, value="10k"
    )
    pcb.add_footprint_from_library(
        "Resistor_SMD:R_0603_1608Metric", "R2", 30, 20, value="10k"
    )
    pcb.add_footprint_from_library(
        "Resistor_SMD:R_0603_1608Metric", "R3", 40, 20, value="1k"
    )
    pcb.add_footprint_from_library(
        "Resistor_SMD:R_0603_1608Metric", "R4", 50, 20, value="1k"
    )

    # Capacitors
    pcb.add_footprint_from_library(
        "Capacitor_SMD:C_0603_1608Metric", "C1", 20, 30, value="100nF"
    )
    pcb.add_footprint_from_library(
        "Capacitor_SMD:C_0603_1608Metric", "C2", 30, 30, value="100nF"
    )
    pcb.add_footprint_from_library(
        "Capacitor_SMD:C_0805_2012Metric", "C3", 40, 30, value="10uF"
    )

    # ICs
    pcb.add_footprint_from_library(
        "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", "U1", 25, 50, value="LM358"
    )
    pcb.add_footprint_from_library(
        "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm", "U2", 45, 50, value="74HC00"
    )

    # Connectors
    pcb.add_footprint_from_library(
        "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
        "J1",
        10,
        40,
        value="INPUT",
    )
    pcb.add_footprint_from_library(
        "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical",
        "J2",
        70,
        40,
        value="OUTPUT",
    )

    print(f"   Added {len(pcb.footprints)} components")

    # Create some connections
    print("\n2. Creating connections...")

    # Power net
    pcb.connect_pads("J1", "1", "C3", "1", "VCC")
    pcb.connect_pads("C3", "1", "U1", "8", "VCC")
    pcb.connect_pads("U1", "8", "U2", "14", "VCC")
    pcb.connect_pads("U2", "14", "C1", "1", "VCC")
    pcb.connect_pads("C1", "1", "R1", "1", "VCC")

    # Ground net
    pcb.connect_pads("J1", "3", "C3", "2", "GND")
    pcb.connect_pads("C3", "2", "U1", "4", "GND")
    pcb.connect_pads("U1", "4", "U2", "7", "GND")
    pcb.connect_pads("U2", "7", "C1", "2", "GND")
    pcb.connect_pads("C1", "2", "C2", "2", "GND")

    # Signal connections
    pcb.connect_pads("J1", "2", "R1", "2", "INPUT")
    pcb.connect_pads("R1", "2", "U1", "3", "INPUT")
    pcb.connect_pads("U1", "1", "R2", "1", "OPAMP_OUT")
    pcb.connect_pads("R2", "2", "U2", "1", "OPAMP_OUT")
    pcb.connect_pads("U2", "3", "R3", "1", "LOGIC_OUT")
    pcb.connect_pads("R3", "2", "J2", "2", "LOGIC_OUT")

    # Feedback
    pcb.connect_pads("U1", "1", "U1", "2", "FEEDBACK")
    pcb.connect_pads("U1", "2", "R4", "1", "FEEDBACK")
    pcb.connect_pads("R4", "2", "C2", "1", "FEEDBACK")

    ratsnest = pcb.get_ratsnest()
    print(f"   Created {len(ratsnest)} connections")

    # Save initial state
    print("\n3. Saving initial layout...")
    pcb.save("force_directed_before.kicad_pcb")

    # Apply force-directed placement
    print("\n4. Applying force-directed placement...")
    print("   This simulates physical forces:")
    print("   - Connected components attract (springs)")
    print("   - All components repel (avoid overlap)")
    print("   - Components gravitate toward center")

    pcb.auto_place_components(
        algorithm="force_directed",
        iterations=200,
        temperature=80.0,
        spring_constant=0.15,
        repulsion_constant=800.0,
        gravity_constant=0.02,
        min_distance=3.0,
    )

    # Get placement statistics
    bbox = pcb.get_placement_bbox()
    if bbox:
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        print(f"\n5. Placement complete!")
        print(f"   Board area: {width:.1f} x {height:.1f} mm")
        print(f"   Components arranged to minimize wire lengths")

    # Save result
    output_file = "force_directed_after.kicad_pcb"
    pcb.save(output_file)
    print(f"\n6. Saved optimized layout to: {output_file}")

    print("\n✓ Demo complete!")
    print(
        "  Compare 'force_directed_before.kicad_pcb' and 'force_directed_after.kicad_pcb'"
    )
    print("  Notice how connected components are pulled together!")


if __name__ == "__main__":
    main()
