#!/usr/bin/env python3
"""
Demonstration of connectivity-driven placement algorithm.

This example creates a circuit with components that have varying connectivity
patterns and demonstrates how the algorithm optimizes placement based on:
- Connection density
- Critical nets (power, ground)
- Minimizing crossings
"""

import sys
import os
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', '..', '..'))

from circuit_synth.kicad_api.pcb import PCBBoard


def main():
    """Run the connectivity-driven placement demo."""
    print("Connectivity-Driven Placement Demo")
    print("=" * 50)
    
    # Create a new PCB
    pcb = PCBBoard()
    
    # Set board outline
    pcb.set_board_outline_rect(0, 0, 120, 100)
    
    print("\n1. Adding components with varying connectivity...")
    
    # Power supply section - highly connected
    pcb.add_footprint_from_library("Package_TO_SOT_THT:TO-220-3_Vertical", "U1", 20, 20, value="LM7805")
    pcb.add_footprint_from_library("Capacitor_SMD:C_0805_2012Metric", "C1", 30, 20, value="10uF")
    pcb.add_footprint_from_library("Capacitor_SMD:C_0805_2012Metric", "C2", 40, 20, value="100nF")
    pcb.add_footprint_from_library("Diode_SMD:D_SMA", "D1", 50, 20, value="1N4007")
    
    # Microcontroller section - central hub
    pcb.add_footprint_from_library("Package_QFP:TQFP-32_7x7mm_P0.8mm", "U2", 60, 50, value="ATmega328")
    pcb.add_footprint_from_library("Crystal:Crystal_SMD_HC49-SD", "Y1", 70, 50, value="16MHz")
    pcb.add_footprint_from_library("Capacitor_SMD:C_0603_1608Metric", "C3", 80, 50, value="22pF")
    pcb.add_footprint_from_library("Capacitor_SMD:C_0603_1608Metric", "C4", 90, 50, value="22pF")
    
    # Peripheral ICs
    pcb.add_footprint_from_library("Package_SO:SOIC-8_3.9x4.9mm_P1.27mm", "U3", 30, 70, value="MAX232")
    pcb.add_footprint_from_library("Package_SO:SOIC-16_3.9x9.9mm_P1.27mm", "U4", 50, 70, value="74HC595")
    
    # Connectors - edge components
    pcb.add_footprint_from_library("Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical", "J1", 10, 40, value="UART")
    pcb.add_footprint_from_library("Connector_PinHeader_2.54mm:PinHeader_2x05_P2.54mm_Vertical", "J2", 100, 40, value="ISP")
    pcb.add_footprint_from_library("Connector_USB:USB_B_OST_USB-B1HSxx_Horizontal", "J3", 10, 80, value="USB")
    
    # Decoupling capacitors - need to be near ICs
    pcb.add_footprint_from_library("Capacitor_SMD:C_0603_1608Metric", "C5", 25, 30, value="100nF")
    pcb.add_footprint_from_library("Capacitor_SMD:C_0603_1608Metric", "C6", 35, 30, value="100nF")
    pcb.add_footprint_from_library("Capacitor_SMD:C_0603_1608Metric", "C7", 45, 30, value="100nF")
    pcb.add_footprint_from_library("Capacitor_SMD:C_0603_1608Metric", "C8", 55, 30, value="100nF")
    
    # Pull-up resistors
    pcb.add_footprint_from_library("Resistor_SMD:R_0603_1608Metric", "R1", 65, 30, value="10k")
    pcb.add_footprint_from_library("Resistor_SMD:R_0603_1608Metric", "R2", 75, 30, value="10k")
    pcb.add_footprint_from_library("Resistor_SMD:R_0603_1608Metric", "R3", 85, 30, value="10k")
    pcb.add_footprint_from_library("Resistor_SMD:R_0603_1608Metric", "R4", 95, 30, value="10k")
    
    print(f"   Added {len(pcb.footprints)} components")
    
    # Create connections with varying criticality
    print("\n2. Creating connections with critical nets...")
    
    # Power net (critical) - star topology from regulator
    pcb.connect_pads("U1", "3", "C1", "1", "VCC")  # Regulator output to bulk cap
    pcb.connect_pads("C1", "1", "C2", "1", "VCC")  # Bulk to ceramic
    pcb.connect_pads("C2", "1", "U2", "7", "VCC")  # Power to MCU
    pcb.connect_pads("U2", "7", "C5", "1", "VCC")  # MCU decoupling
    pcb.connect_pads("C5", "1", "U3", "16", "VCC") # Power to MAX232
    pcb.connect_pads("U3", "16", "C6", "1", "VCC") # MAX232 decoupling
    pcb.connect_pads("C6", "1", "U4", "16", "VCC") # Power to shift register
    pcb.connect_pads("U4", "16", "C7", "1", "VCC") # Shift register decoupling
    pcb.connect_pads("C7", "1", "R1", "1", "VCC")  # Pull-ups
    pcb.connect_pads("R1", "1", "R2", "1", "VCC")
    pcb.connect_pads("R2", "1", "R3", "1", "VCC")
    pcb.connect_pads("R3", "1", "R4", "1", "VCC")
    
    # Ground net (critical) - also star topology
    pcb.connect_pads("U1", "2", "C1", "2", "GND")  # Regulator ground
    pcb.connect_pads("C1", "2", "C2", "2", "GND")
    pcb.connect_pads("C2", "2", "U2", "8", "GND")  # MCU ground
    pcb.connect_pads("U2", "8", "U2", "22", "GND") # MCU multiple grounds
    pcb.connect_pads("U2", "22", "C5", "2", "GND")
    pcb.connect_pads("C5", "2", "U3", "15", "GND")
    pcb.connect_pads("U3", "15", "C6", "2", "GND")
    pcb.connect_pads("C6", "2", "U4", "8", "GND")
    pcb.connect_pads("U4", "8", "C7", "2", "GND")
    pcb.connect_pads("C7", "2", "J3", "4", "GND")  # USB ground
    
    # Crystal connections (high-speed, critical)
    pcb.connect_pads("U2", "9", "Y1", "1", "XTAL1")
    pcb.connect_pads("Y1", "1", "C3", "1", "XTAL1")
    pcb.connect_pads("U2", "10", "Y1", "2", "XTAL2")
    pcb.connect_pads("Y1", "2", "C4", "1", "XTAL2")
    pcb.connect_pads("C3", "2", "C4", "2", "GND")
    
    # UART connections
    pcb.connect_pads("U2", "2", "U3", "11", "RXD")
    pcb.connect_pads("U2", "3", "U3", "10", "TXD")
    pcb.connect_pads("U3", "14", "J1", "2", "RS232_RX")
    pcb.connect_pads("U3", "13", "J1", "3", "RS232_TX")
    
    # ISP connections
    pcb.connect_pads("U2", "17", "J2", "1", "MOSI")
    pcb.connect_pads("U2", "18", "J2", "2", "MISO")
    pcb.connect_pads("U2", "19", "J2", "3", "SCK")
    pcb.connect_pads("U2", "1", "J2", "5", "RESET")
    pcb.connect_pads("J2", "5", "R1", "2", "RESET")  # Pull-up on reset
    
    # Shift register connections
    pcb.connect_pads("U2", "23", "U4", "14", "SR_DATA")
    pcb.connect_pads("U2", "24", "U4", "11", "SR_CLK")
    pcb.connect_pads("U2", "25", "U4", "12", "SR_LATCH")
    
    # USB connections
    pcb.connect_pads("J3", "2", "U2", "4", "USB_D+")
    pcb.connect_pads("J3", "3", "U2", "5", "USB_D-")
    
    ratsnest = pcb.get_ratsnest()
    print(f"   Created {len(ratsnest)} connections")
    print(f"   Critical nets: VCC, GND, XTAL1/2, USB_D+/-")
    
    # Save initial state
    print("\n3. Saving initial layout...")
    pcb.save("connectivity_driven_before.kicad_pcb")
    
    # Apply connectivity-driven placement
    print("\n4. Applying connectivity-driven placement...")
    print("   Algorithm features:")
    print("   - Analyzes connectivity patterns")
    print("   - Prioritizes critical nets (power, ground, clocks)")
    print("   - Clusters highly connected components")
    print("   - Minimizes connection crossings")
    
    pcb.auto_place_components(
        algorithm="connectivity_driven",
        component_spacing=1.5,      # Tighter spacing for connected components
        cluster_spacing=4.0,        # Space between clusters
        critical_net_weight=2.5,    # Higher weight for critical nets
        crossing_penalty=1.8        # Penalty for crossing connections
    )
    
    # Get placement statistics
    bbox = pcb.get_placement_bbox()
    if bbox:
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        print(f"\n5. Placement complete!")
        print(f"   Board area: {width:.1f} x {height:.1f} mm")
        print(f"   Components arranged by connectivity patterns")
        print(f"   Critical nets optimized for short paths")
    
    # Save result
    output_file = "connectivity_driven_after.kicad_pcb"
    pcb.save(output_file)
    print(f"\n6. Saved optimized layout to: {output_file}")
    
    # Analyze the placement
    print("\n7. Placement analysis:")
    print("   - Power components clustered together")
    print("   - MCU centrally located as main hub")
    print("   - Decoupling caps near their ICs")
    print("   - Connectors at board edges")
    print("   - Crystal close to MCU with short traces")
    
    print("\n✓ Demo complete!")
    print("  Compare 'connectivity_driven_before.kicad_pcb' and 'connectivity_driven_after.kicad_pcb'")
    print("  Notice how components are grouped by their connectivity!")


if __name__ == "__main__":
    main()