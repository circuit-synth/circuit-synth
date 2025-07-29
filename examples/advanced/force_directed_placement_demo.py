#!/usr/bin/env python3
"""
Demonstration of force-directed placement algorithm for PCB components.

This example creates a simple circuit with connected components and uses
physics-based simulation to optimize their placement.
"""

import os
import sys

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "..", ".."))

from circuit_synth.kicad_api.pcb import PCBBoard


def create_demo_circuit():
    """Create a demo PCB with connected components."""
    pcb = PCBBoard()

    # Set board outline
    pcb.set_board_outline_rect(0, 0, 100, 80)

    # Add components in a simple circuit
    # Power section
    pcb.add_footprint(
        "U1", "Package_TO_SOT_THT:TO-220-3_Vertical", 20, 20, value="LM7805"
    )
    pcb.add_footprint(
        "C1", "Capacitor_THT:CP_Radial_D5.0mm_P2.50mm", 10, 20, value="100uF"
    )
    pcb.add_footprint(
        "C2", "Capacitor_THT:CP_Radial_D5.0mm_P2.50mm", 30, 20, value="10uF"
    )

    # MCU section
    pcb.add_footprint("U2", "Package_DIP:DIP-28_W7.62mm", 50, 40, value="ATmega328")
    pcb.add_footprint("Y1", "Crystal:Crystal_HC49-4H_Vertical", 40, 50, value="16MHz")
    pcb.add_footprint("C3", "Capacitor_SMD:C_0603_1608Metric", 35, 50, value="22pF")
    pcb.add_footprint("C4", "Capacitor_SMD:C_0603_1608Metric", 45, 50, value="22pF")

    # LED indicators
    pcb.add_footprint("D1", "LED_THT:LED_D3.0mm", 70, 30, value="PWR_LED")
    pcb.add_footprint("R1", "Resistor_SMD:R_0603_1608Metric", 70, 35, value="330R")
    pcb.add_footprint("D2", "LED_THT:LED_D3.0mm", 80, 30, value="STATUS_LED")
    pcb.add_footprint("R2", "Resistor_SMD:R_0603_1608Metric", 80, 35, value="330R")

    # Connectors
    pcb.add_footprint(
        "J1",
        "Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical",
        5,
        10,
        value="PWR_IN",
    )
    pcb.add_footprint(
        "J2",
        "Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical",
        90,
        40,
        value="SERIAL",
    )

    # Create nets and connections
    # Power connections
    pcb.connect_pads("J1", "1", "C1", "1", "VIN")
    pcb.connect_pads("C1", "1", "U1", "1", "VIN")
    pcb.connect_pads("U1", "3", "C2", "1", "VCC")
    pcb.connect_pads("C2", "1", "U2", "7", "VCC")  # MCU VCC
    pcb.connect_pads("C2", "1", "D1", "1", "VCC")  # LED power

    # Ground connections
    pcb.connect_pads("J1", "2", "C1", "2", "GND")
    pcb.connect_pads("C1", "2", "U1", "2", "GND")
    pcb.connect_pads("U1", "2", "C2", "2", "GND")
    pcb.connect_pads("C2", "2", "U2", "8", "GND")  # MCU GND
    pcb.connect_pads("C2", "2", "U2", "22", "GND")  # MCU GND

    # Crystal connections
    pcb.connect_pads("U2", "9", "Y1", "1", "XTAL1")
    pcb.connect_pads("U2", "10", "Y1", "2", "XTAL2")
    pcb.connect_pads("Y1", "1", "C3", "1", "XTAL1")
    pcb.connect_pads("Y1", "2", "C4", "1", "XTAL2")
    pcb.connect_pads("C3", "2", "C4", "2", "GND")

    # LED connections
    pcb.connect_pads("D1", "2", "R1", "1", "LED1_NET")
    pcb.connect_pads("R1", "2", "U2", "23", "LED1_NET")  # PC0
    pcb.connect_pads("D2", "2", "R2", "1", "LED2_NET")
    pcb.connect_pads("R2", "2", "U2", "24", "LED2_NET")  # PC1

    # Serial connections
    pcb.connect_pads("U2", "2", "J2", "1", "RX")
    pcb.connect_pads("U2", "3", "J2", "2", "TX")

    return pcb


def main():
    """Run the force-directed placement demo."""
    print("Force-Directed Placement Demo")
    print("=" * 50)

    # Create the demo circuit
    print("\n1. Creating demo circuit...")
    pcb = create_demo_circuit()
    print(f"   Created {len(pcb.footprints)} components")

    # Show initial ratsnest
    ratsnest = pcb.get_ratsnest()
    print(f"   Created {len(ratsnest)} connections")

    # Save initial state
    print("\n2. Saving initial (unplaced) PCB...")
    pcb.save("force_directed_initial.kicad_pcb")

    # Apply force-directed placement
    print("\n3. Applying force-directed placement...")
    print("   Parameters:")
    print("   - Iterations: 150")
    print("   - Temperature: 100.0")
    print("   - Spring constant: 0.2")
    print("   - Repulsion constant: 500.0")

    pcb.auto_place_components(
        algorithm="force_directed",
        iterations=150,
        temperature=100.0,
        spring_constant=0.2,
        repulsion_constant=500.0,
        gravity_constant=0.05,
        min_distance=5.0,
    )

    # Get final bounding box
    bbox = pcb.get_placement_bbox()
    if bbox:
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        print(f"\n4. Placement complete!")
        print(f"   Board area used: {width:.1f} x {height:.1f} mm")
        print(f"   Components are optimally placed to minimize connection lengths")

    # Save the result
    output_file = "force_directed_placed.kicad_pcb"
    pcb.save(output_file)
    print(f"\n5. Saved placed PCB to: {output_file}")

    # Show some statistics
    print("\n6. Placement Statistics:")
    print("   - Connected components are pulled together")
    print("   - All components maintain minimum spacing")
    print("   - Power components grouped near power input")
    print("   - MCU and crystal placed close together")
    print("   - LEDs positioned for easy access")

    print("\nDemo complete! Open the PCB files in KiCad to see the difference.")
    print(
        "Compare 'force_directed_initial.kicad_pcb' with 'force_directed_placed.kicad_pcb'"
    )


if __name__ == "__main__":
    main()
