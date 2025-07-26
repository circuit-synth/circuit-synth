#!/usr/bin/env python3
"""
Create a PCB using footprints from the KiCad library.

This example demonstrates:
1. Searching for appropriate footprints
2. Adding footprints from the library with full pad information
3. Creating connections between components
4. Using the placement algorithm
5. Running DRC on the result
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from circuit_synth.kicad_api.pcb import PCBBoard


def create_simple_circuit():
    """Create a simple voltage regulator circuit using library footprints."""
    print("Creating PCB with Library Footprints")
    print("=" * 50)
    
    # Create new PCB
    pcb = PCBBoard()
    
    # Set board outline
    pcb.set_board_outline_rect(0, 0, 80, 60)
    
    print("\n1. Searching for appropriate footprints...")
    
    # Search for voltage regulator footprint (TO-220)
    vreg_results = pcb.search_footprints("TO-220", filters={"pad_count": 3})
    if vreg_results:
        vreg_footprint = f"{vreg_results[0].library}:{vreg_results[0].name}"
        print(f"   Found voltage regulator footprint: {vreg_footprint}")
    else:
        # Fallback to manual footprint
        vreg_footprint = "Package_TO_SOT_THT:TO-220-3_Vertical"
        print(f"   Using default: {vreg_footprint}")
    
    # Search for capacitor footprints
    cap_results = pcb.search_footprints("CP_Radial", filters={"footprint_type": "THT"})
    if cap_results:
        cap_footprint = f"{cap_results[0].library}:{cap_results[0].name}"
        print(f"   Found capacitor footprint: {cap_footprint}")
    else:
        cap_footprint = "Capacitor_THT:CP_Radial_D5.0mm_P2.50mm"
        print(f"   Using default: {cap_footprint}")
    
    # Search for resistor footprint
    res_results = pcb.search_footprints("0603", filters={"footprint_type": "SMD"})
    if res_results:
        res_footprint = f"{res_results[0].library}:{res_results[0].name}"
        print(f"   Found resistor footprint: {res_footprint}")
    else:
        res_footprint = "Resistor_SMD:R_0603_1608Metric"
        print(f"   Using default: {res_footprint}")
    
    # Search for LED footprint
    led_results = pcb.search_footprints("LED", filters={"footprint_type": "SMD", "pad_count": 2})
    if led_results:
        led_footprint = f"{led_results[0].library}:{led_results[0].name}"
        print(f"   Found LED footprint: {led_footprint}")
    else:
        led_footprint = "LED_SMD:LED_0603_1608Metric"
        print(f"   Using default: {led_footprint}")
    
    # Search for connector footprint
    conn_results = pcb.search_footprints("PinHeader_1x03", filters={"footprint_type": "THT"})
    if conn_results:
        conn_footprint = f"{conn_results[0].library}:{conn_results[0].name}"
        print(f"   Found connector footprint: {conn_footprint}")
    else:
        conn_footprint = "Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical"
        print(f"   Using default: {conn_footprint}")
    
    print("\n2. Adding components from library...")
    
    # Add components using library footprints
    # These will include full pad information from the library
    
    # Power connector
    j1 = pcb.add_footprint_from_library(conn_footprint, "J1", 10, 30, value="POWER")
    if j1:
        print(f"   Added J1 (Power connector) with {len(j1.pads)} pads")
    
    # Voltage regulator (LM7805)
    u1 = pcb.add_footprint_from_library(vreg_footprint, "U1", 30, 30, value="LM7805")
    if u1:
        print(f"   Added U1 (Voltage regulator) with {len(u1.pads)} pads")
    
    # Input capacitor
    c1 = pcb.add_footprint_from_library(cap_footprint, "C1", 20, 20, value="100uF")
    if c1:
        print(f"   Added C1 (Input capacitor) with {len(c1.pads)} pads")
    
    # Output capacitor
    c2 = pcb.add_footprint_from_library(cap_footprint, "C2", 40, 20, value="10uF")
    if c2:
        print(f"   Added C2 (Output capacitor) with {len(c2.pads)} pads")
    
    # LED current limiting resistor
    r1 = pcb.add_footprint_from_library(res_footprint, "R1", 50, 30, value="330")
    if r1:
        print(f"   Added R1 (LED resistor) with {len(r1.pads)} pads")
    
    # Power indicator LED
    d1 = pcb.add_footprint_from_library(led_footprint, "D1", 60, 30, value="PWR")
    if d1:
        print(f"   Added D1 (Power LED) with {len(d1.pads)} pads")
    
    # Output connector
    j2 = pcb.add_footprint_from_library(conn_footprint, "J2", 70, 30, value="OUTPUT")
    if j2:
        print(f"   Added J2 (Output connector) with {len(j2.pads)} pads")
    
    print("\n3. Creating electrical connections...")
    
    # Create nets and connections
    # Power input
    pcb.connect_pads("J1", "1", "U1", "1", "VIN")  # +12V input
    pcb.connect_pads("J1", "2", "U1", "2", "GND")  # Ground
    pcb.connect_pads("J1", "3", "U1", "2", "GND")  # Ground (redundant)
    
    # Input capacitor
    pcb.connect_pads("C1", "1", "U1", "1", "VIN")  # C1 positive to VIN
    pcb.connect_pads("C1", "2", "U1", "2", "GND")  # C1 negative to GND
    
    # Output
    pcb.connect_pads("U1", "3", "C2", "1", "VOUT")  # Regulator output
    pcb.connect_pads("U1", "3", "J2", "1", "VOUT")  # To output connector
    pcb.connect_pads("U1", "3", "R1", "1", "VOUT")  # To LED resistor
    
    # Output capacitor
    pcb.connect_pads("C2", "2", "U1", "2", "GND")  # C2 negative to GND
    
    # LED circuit
    pcb.connect_pads("R1", "2", "D1", "1", "LED_NET")  # Resistor to LED anode
    pcb.connect_pads("D1", "2", "U1", "2", "GND")      # LED cathode to GND
    
    # Output connector ground
    pcb.connect_pads("J2", "2", "U1", "2", "GND")  # Output ground
    pcb.connect_pads("J2", "3", "U1", "2", "GND")  # Output ground (redundant)
    
    print("   Created all electrical connections")
    
    print("\n4. Optimizing component placement...")
    
    # Use hierarchical placement to arrange components
    pcb.auto_place_components(
        algorithm="hierarchical",
        component_spacing=2.0,
        group_spacing=5.0
    )
    
    # Get final board size
    bbox = pcb.get_placement_bbox()
    if bbox:
        width = bbox[2] - bbox[0]
        height = bbox[3] - bbox[1]
        print(f"   Optimized board size: {width:.1f} x {height:.1f} mm")
        
        # Update board outline to fit components
        margin = 5.0
        pcb.set_board_outline_rect(
            bbox[0] - margin,
            bbox[1] - margin,
            width + 2 * margin,
            height + 2 * margin
        )
    
    print("\n5. Adding copper zones...")
    
    # Add ground plane on bottom layer
    board_outline = pcb.get_board_outline()
    if board_outline:
        # Get board corners (assuming rectangular)
        min_x = min_y = float('inf')
        max_x = max_y = float('-inf')
        
        for item in board_outline:
            if hasattr(item, 'start'):
                min_x = min(min_x, item.start.x)
                min_y = min(min_y, item.start.y)
                max_x = max(max_x, item.start.x)
                max_y = max(max_y, item.start.y)
            if hasattr(item, 'end'):
                min_x = min(min_x, item.end.x)
                min_y = min(min_y, item.end.y)
                max_x = max(max_x, item.end.x)
                max_y = max(max_y, item.end.y)
        
        # Create ground plane with 1mm margin from board edge
        margin = 1.0
        ground_polygon = [
            (min_x + margin, min_y + margin),
            (max_x - margin, min_y + margin),
            (max_x - margin, max_y - margin),
            (min_x + margin, max_y - margin)
        ]
        
        pcb.add_zone(ground_polygon, "B.Cu", "GND", filled=True)
        print("   Added ground plane on bottom layer")
    
    print("\n6. Checking ratsnest...")
    
    # Show unrouted connections
    ratsnest = pcb.get_ratsnest()
    print(f"   Unrouted connections: {len(ratsnest)}")
    for conn in ratsnest[:5]:  # Show first 5
        print(f"     - {conn['from']['ref']}.{conn['from']['pad']} to "
              f"{conn['to']['ref']}.{conn['to']['pad']} "
              f"({conn['net']}, {conn['distance']:.1f}mm)")
    if len(ratsnest) > 5:
        print(f"     ... and {len(ratsnest) - 5} more")
    
    # Save the PCB
    output_dir = Path(__file__).parent / "library_footprint_output"
    output_dir.mkdir(exist_ok=True)
    output_file = output_dir / "voltage_regulator.kicad_pcb"
    
    pcb.save(output_file)
    print(f"\n7. Saved PCB to: {output_file}")
    
    # Run basic DRC
    print("\n8. Running basic design rule check...")
    violations = pcb.check_basic_rules()
    
    if violations:
        print("   Found violations:")
        for category, items in violations.items():
            if items:
                print(f"   - {category}: {len(items)} issues")
    else:
        print("   No basic rule violations found!")
    
    print("\nDone! You can open the PCB file in KiCad to view the result.")
    print("The footprints include full pad information from the KiCad libraries.")


if __name__ == "__main__":
    create_simple_circuit()