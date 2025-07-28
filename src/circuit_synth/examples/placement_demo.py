#!/usr/bin/env python3
"""
Simple demonstration of PCB component placement functionality.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from circuit_synth.kicad_api.pcb import PCBBoard


def main():
    # Create a new PCB board
    board = PCBBoard()

    # Add some components using the standard add_footprint method
    print("Adding components to the board...")

    # Power supply section
    board.add_footprint(
        "U1", "Package_TO_SOT_THT:TO-220-3_Vertical", 50, 50, value="LM7805"
    )
    board.add_footprint(
        "C1", "Capacitor_THT:CP_Radial_D5.0mm_P2.50mm", 60, 50, value="100uF"
    )
    board.add_footprint("C2", "Capacitor_SMD:C_0805_2012Metric", 70, 50, value="0.1uF")

    # MCU section
    board.add_footprint(
        "U2", "Package_QFP:TQFP-32_7x7mm_P0.8mm", 80, 60, value="ATmega328P"
    )
    board.add_footprint("Y1", "Crystal:Crystal_HC49-4H_Vertical", 90, 60, value="16MHz")
    board.add_footprint("C3", "Capacitor_SMD:C_0603_1608Metric", 100, 60, value="22pF")
    board.add_footprint("C4", "Capacitor_SMD:C_0603_1608Metric", 105, 60, value="22pF")

    # Interface section
    board.add_footprint(
        "J1", "Connector_USB:USB_B_OST_USB-B1HSxx_Horizontal", 110, 70, value="USB_B"
    )
    board.add_footprint("R1", "Resistor_SMD:R_0805_2012Metric", 120, 70, value="10k")

    # Status LED
    board.add_footprint("D1", "LED_SMD:LED_0805_2012Metric", 130, 80, value="LED")
    board.add_footprint("R2", "Resistor_SMD:R_0603_1608Metric", 135, 80, value="330")

    print(f"Added {len(board.pcb_data['footprints'])} components")

    # Get initial bounding box
    initial_bbox = board.get_placement_bbox()
    if initial_bbox:
        print(
            f"\nInitial layout size: {initial_bbox[2]-initial_bbox[0]:.2f} x {initial_bbox[3]-initial_bbox[1]:.2f} mm"
        )

    # Apply hierarchical placement
    print("\nApplying hierarchical placement...")
    board.auto_place_components(
        algorithm="hierarchical",
        component_spacing=1.0,  # 1mm between components
        group_spacing=5.0,  # 5mm between groups
    )

    # Get new bounding box
    new_bbox = board.get_placement_bbox()
    if new_bbox:
        print(
            f"Optimized layout size: {new_bbox[2]-new_bbox[0]:.2f} x {new_bbox[3]-new_bbox[1]:.2f} mm"
        )
        print(
            f"Board area reduced by {((initial_bbox[2]-initial_bbox[0])*(initial_bbox[3]-initial_bbox[1]) - (new_bbox[2]-new_bbox[0])*(new_bbox[3]-new_bbox[1])) / ((initial_bbox[2]-initial_bbox[0])*(initial_bbox[3]-initial_bbox[1])) * 100:.1f}%"
        )

    # Save the board
    output_file = "placement_demo_output.kicad_pcb"
    board.save(output_file)
    print(f"\nSaved optimized board to: {output_file}")

    # Show final component positions
    print("\nFinal component positions:")
    for fp in board.pcb_data["footprints"]:
        print(
            f"  {fp.reference} ({fp.value}) at ({fp.position.x:.2f}, {fp.position.y:.2f})"
        )


if __name__ == "__main__":
    main()
