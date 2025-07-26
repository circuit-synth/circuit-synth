#!/usr/bin/env python3
"""Test script for PCB component placement functionality."""

import sys
import os
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from circuit_synth.kicad_api.pcb import PCBBoard
from circuit_synth.kicad_api.pcb.types import Footprint, Pad, Point
import logging

# Set up logging
logging.basicConfig(level=logging.DEBUG, format='%(levelname)s - %(name)s - %(message)s')
logger = logging.getLogger(__name__)

def create_test_board():
    """Create a test PCB board with multiple components."""
    board = PCBBoard()
    
    # Create test footprints with different hierarchical paths
    test_footprints = [
        # Power supply components
        Footprint(
            library="Package_TO_SOT_THT",
            name="TO-220-3_Vertical",
            reference="U1",
            value="LM7805",
            position=Point(x=50.0, y=50.0),
            layer="F.Cu",
            path="/power_supply/",
            pads=[
                Pad(number="1", type="thru_hole", shape="circle", position=Point(x=0, y=0), size=(1.5, 1.5), drill=0.8),
                Pad(number="2", type="thru_hole", shape="circle", position=Point(x=2.54, y=0), size=(1.5, 1.5), drill=0.8),
                Pad(number="3", type="thru_hole", shape="circle", position=Point(x=5.08, y=0), size=(1.5, 1.5), drill=0.8),
            ]
        ),
        Footprint(
            library="Capacitor_THT",
            name="CP_Radial_D5.0mm_P2.50mm",
            reference="C1",
            value="100uF",
            position=Point(x=60.0, y=50.0),
            layer="F.Cu",
            path="/power_supply/",
            pads=[
                Pad(number="1", type="thru_hole", shape="circle", position=Point(x=0, y=0), size=(1.5, 1.5), drill=0.8),
                Pad(number="2", type="thru_hole", shape="circle", position=Point(x=2.5, y=0), size=(1.5, 1.5), drill=0.8),
            ]
        ),
        Footprint(
            library="Capacitor_SMD",
            name="C_0805_2012Metric",
            reference="C2",
            value="0.1uF",
            position=Point(x=70.0, y=50.0),
            layer="F.Cu",
            path="/power_supply/",
            pads=[
                Pad(number="1", type="smd", shape="rect", position=Point(x=0, y=0), size=(0.8, 1.2)),
                Pad(number="2", type="smd", shape="rect", position=Point(x=1.6, y=0), size=(0.8, 1.2)),
            ]
        ),
        
        # MCU components
        Footprint(
            library="Package_QFP",
            name="TQFP-32_7x7mm_P0.8mm",
            reference="U2",
            value="ATmega328P",
            position=Point(x=80.0, y=60.0),
            layer="F.Cu",
            path="/mcu/",
            pads=[
                Pad(number=str(i+1), type="smd", shape="rect", position=Point(x=(i%8)*0.8-2.8, y=2.8 if i<8 else -2.8),
                    size=(0.4, 1.2))
                for i in range(16)
            ] + [
                Pad(number=str(i+17), type="smd", shape="rect", position=Point(x=2.8 if i<8 else -2.8, y=(i%8)*0.8-2.8),
                    size=(1.2, 0.4))
                for i in range(16)
            ]
        ),
        Footprint(
            library="Crystal",
            name="Crystal_HC49-4H_Vertical",
            reference="Y1",
            value="16MHz",
            position=Point(x=90.0, y=60.0),
            layer="F.Cu",
            path="/mcu/",
            pads=[
                Pad(number="1", type="thru_hole", shape="circle", position=Point(x=0, y=0), size=(1.5, 1.5), drill=0.8),
                Pad(number="2", type="thru_hole", shape="circle", position=Point(x=4.88, y=0), size=(1.5, 1.5), drill=0.8),
            ]
        ),
        Footprint(
            library="Capacitor_SMD",
            name="C_0603_1608Metric",
            reference="C3",
            value="22pF",
            position=Point(x=100.0, y=60.0),
            layer="F.Cu",
            path="/mcu/",
            pads=[
                Pad(number="1", type="smd", shape="rect", position=Point(x=0, y=0), size=(0.6, 0.9)),
                Pad(number="2", type="smd", shape="rect", position=Point(x=1.2, y=0), size=(0.6, 0.9)),
            ]
        ),
        Footprint(
            library="Capacitor_SMD",
            name="C_0603_1608Metric",
            reference="C4",
            value="22pF",
            position=Point(x=105.0, y=60.0),
            layer="F.Cu",
            path="/mcu/",
            pads=[
                Pad(number="1", type="smd", shape="rect", position=Point(x=0, y=0), size=(0.6, 0.9)),
                Pad(number="2", type="smd", shape="rect", position=Point(x=1.2, y=0), size=(0.6, 0.9)),
            ]
        ),
        
        # Interface components
        Footprint(
            library="Connector_USB",
            name="USB_B_OST_USB-B1HSxx_Horizontal",
            reference="J1",
            value="USB_B",
            position=Point(x=110.0, y=70.0),
            layer="F.Cu",
            path="/interface/",
            pads=[
                Pad(number="1", type="thru_hole", shape="rect", position=Point(x=0, y=0), size=(1.5, 1.5), drill=0.8),
                Pad(number="2", type="thru_hole", shape="rect", position=Point(x=2.5, y=0), size=(1.5, 1.5), drill=0.8),
                Pad(number="3", type="thru_hole", shape="rect", position=Point(x=5.0, y=0), size=(1.5, 1.5), drill=0.8),
                Pad(number="4", type="thru_hole", shape="rect", position=Point(x=7.5, y=0), size=(1.5, 1.5), drill=0.8),
            ]
        ),
        Footprint(
            library="Resistor_SMD",
            name="R_0805_2012Metric",
            reference="R1",
            value="10k",
            position=Point(x=120.0, y=70.0),
            layer="F.Cu",
            path="/interface/",
            pads=[
                Pad(number="1", type="smd", shape="rect", position=Point(x=0, y=0), size=(0.8, 1.2)),
                Pad(number="2", type="smd", shape="rect", position=Point(x=1.6, y=0), size=(0.8, 1.2)),
            ]
        ),
        
        # Components without hierarchical path
        Footprint(
            library="LED_SMD",
            name="LED_0805_2012Metric",
            reference="D1",
            value="LED",
            position=Point(x=130.0, y=80.0),
            layer="F.Cu",
            path="/",
            pads=[
                Pad(number="1", type="smd", shape="rect", position=Point(x=0, y=0), size=(0.8, 1.2)),
                Pad(number="2", type="smd", shape="rect", position=Point(x=1.6, y=0), size=(0.8, 1.2)),
            ]
        ),
        Footprint(
            library="Resistor_SMD",
            name="R_0603_1608Metric",
            reference="R2",
            value="330",
            position=Point(x=135.0, y=80.0),
            layer="F.Cu",
            path="/",
            pads=[
                Pad(number="1", type="smd", shape="rect", position=Point(x=0, y=0), size=(0.6, 0.9)),
                Pad(number="2", type="smd", shape="rect", position=Point(x=1.2, y=0), size=(0.6, 0.9)),
            ]
        ),
    ]
    
    # Add all footprints to the board
    for footprint in test_footprints:
        board.add_footprint_object(footprint)
    
    return board

def test_hierarchical_placement():
    """Test the hierarchical placement algorithm."""
    print("\n=== Testing Hierarchical Placement ===\n")
    
    # Create test board
    board = create_test_board()
    print(f"Created test board with {len(board.pcb_data['footprints'])} components")
    
    # Show initial positions
    print("\nInitial component positions:")
    for fp in board.pcb_data['footprints']:
        print(f"  {fp.reference} ({fp.value}) at ({fp.position.x:.2f}, {fp.position.y:.2f}) - path: {fp.path}")
    
    # Get initial bounding box
    initial_bbox = board.get_placement_bbox()
    if initial_bbox:
        print(f"\nInitial bounding box: ({initial_bbox[0]:.2f}, {initial_bbox[1]:.2f}) to ({initial_bbox[2]:.2f}, {initial_bbox[3]:.2f})")
        print(f"Initial size: {initial_bbox[2]-initial_bbox[0]:.2f} x {initial_bbox[3]-initial_bbox[1]:.2f} mm")
    
    # Apply hierarchical placement
    print("\nApplying hierarchical placement...")
    board.auto_place_components(
        algorithm="hierarchical",
        component_spacing=1.0,  # 1mm between components
        group_spacing=5.0       # 5mm between groups
    )
    
    # Show new positions
    print("\nNew component positions:")
    for fp in board.pcb_data['footprints']:
        print(f"  {fp.reference} ({fp.value}) at ({fp.position.x:.2f}, {fp.position.y:.2f}) - path: {fp.path}")
    
    # Get new bounding box
    new_bbox = board.get_placement_bbox()
    if new_bbox:
        print(f"\nNew bounding box: ({new_bbox[0]:.2f}, {new_bbox[1]:.2f}) to ({new_bbox[2]:.2f}, {new_bbox[3]:.2f})")
        print(f"New size: {new_bbox[2]-new_bbox[0]:.2f} x {new_bbox[3]-new_bbox[1]:.2f} mm")
    
    # Verify grouping
    print("\nVerifying hierarchical grouping:")
    groups = {}
    for fp in board.pcb_data['footprints']:
        path = fp.path
        if path not in groups:
            groups[path] = []
        groups[path].append(fp)
    
    for path, components in groups.items():
        print(f"\n  Group '{path}':")
        for comp in components:
            print(f"    {comp.reference} at ({comp.position.x:.2f}, {comp.position.y:.2f})")
    
    # Save the board
    output_file = "test_placement_output.kicad_pcb"
    board.save(output_file)
    print(f"\nSaved placed board to: {output_file}")
    
    return board

def test_custom_spacing():
    """Test placement with custom spacing parameters."""
    print("\n=== Testing Custom Spacing ===\n")
    
    board = create_test_board()
    
    # Test with tight spacing
    print("Testing with tight spacing (0.5mm component, 2mm group)...")
    board.auto_place_components(
        algorithm="hierarchical",
        component_spacing=0.5,
        group_spacing=2.0
    )
    
    tight_bbox = board.get_placement_bbox()
    if tight_bbox:
        print(f"Tight spacing size: {tight_bbox[2]-tight_bbox[0]:.2f} x {tight_bbox[3]-tight_bbox[1]:.2f} mm")
    
    # Reset and test with loose spacing
    board = create_test_board()
    print("\nTesting with loose spacing (2mm component, 10mm group)...")
    board.auto_place_components(
        algorithm="hierarchical",
        component_spacing=2.0,
        group_spacing=10.0
    )
    
    loose_bbox = board.get_placement_bbox()
    if loose_bbox:
        print(f"Loose spacing size: {loose_bbox[2]-loose_bbox[0]:.2f} x {loose_bbox[3]-loose_bbox[1]:.2f} mm")

def test_empty_board():
    """Test placement on an empty board."""
    print("\n=== Testing Empty Board ===\n")
    
    board = PCBBoard()
    print("Created empty board")
    
    # Try to get bounding box
    bbox = board.get_placement_bbox()
    print(f"Empty board bounding box: {bbox}")
    
    # Try to place components
    try:
        board.auto_place_components()
        print("Placement completed (no components to place)")
    except Exception as e:
        print(f"Error during placement: {e}")

def test_single_component():
    """Test placement with a single component."""
    print("\n=== Testing Single Component ===\n")
    
    board = PCBBoard()
    
    # Add single component
    footprint = Footprint(
        library="Package_DIP",
        name="DIP-8_W7.62mm",
        reference="U1",
        value="TestChip",
        position=Point(x=100.0, y=100.0),
        layer="F.Cu",
        path="/",
        pads=[
            Pad(number=str(i+1), type="thru_hole", shape="circle", position=Point(x=0, y=i*2.54), size=(1.5, 1.5), drill=0.8)
            for i in range(8)
        ]
    )
    board.add_footprint_object(footprint)
    
    print(f"Initial position: ({footprint.position.x:.2f}, {footprint.position.y:.2f})")
    
    # Place component
    board.auto_place_components()
    
    # Check new position
    placed_fp = board.pcb_data['footprints'][0]
    print(f"Placed position: ({placed_fp.position.x:.2f}, {placed_fp.position.y:.2f})")

if __name__ == "__main__":
    # Run all tests
    test_hierarchical_placement()
    test_custom_spacing()
    test_empty_board()
    test_single_component()
    
    print("\n=== All placement tests completed ===")