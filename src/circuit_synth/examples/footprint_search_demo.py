#!/usr/bin/env python3
"""
Demonstration of footprint library search functionality.

This script shows how to search for footprints using various filters
and display detailed information about the results.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from circuit_synth.kicad_api.pcb import PCBBoard


def main():
    """Demonstrate footprint search capabilities."""
    print("KiCad Footprint Library Search Demo")
    print("=" * 50)
    
    # Create a PCB board instance (just for accessing footprint search)
    pcb = PCBBoard()
    
    # Example 1: Search for 0603 SMD components
    print("\n1. Searching for 0603 SMD components:")
    print("-" * 40)
    results = pcb.search_footprints("0603", filters={"footprint_type": "SMD"})
    
    print(f"Found {len(results)} footprints")
    for i, fp in enumerate(results[:5]):  # Show first 5
        print(f"  {i+1}. {fp.library}:{fp.name}")
        print(f"     Description: {fp.description}")
        print(f"     Pads: {fp.pad_count}, Size: {fp.body_size[0]:.2f}x{fp.body_size[1]:.2f}mm")
    
    if len(results) > 5:
        print(f"  ... and {len(results) - 5} more")
    
    # Example 2: Search for 8-pin SOIC packages
    print("\n2. Searching for 8-pin SOIC packages:")
    print("-" * 40)
    results = pcb.search_footprints("SOIC", filters={"pad_count": 8})
    
    print(f"Found {len(results)} footprints")
    for i, fp in enumerate(results[:5]):
        print(f"  {i+1}. {fp.library}:{fp.name}")
        print(f"     Tags: {fp.tags}")
    
    # Example 3: Search for through-hole connectors
    print("\n3. Searching for through-hole connectors:")
    print("-" * 40)
    results = pcb.search_footprints("connector", filters={"footprint_type": "THT"})
    
    print(f"Found {len(results)} footprints")
    for i, fp in enumerate(results[:5]):
        print(f"  {i+1}. {fp.library}:{fp.name}")
        print(f"     Pads: {fp.pad_count}")
    
    # Example 4: Search by size constraints
    print("\n4. Searching for small SMD components (max 5x5mm):")
    print("-" * 40)
    results = pcb.search_footprints("", filters={
        "footprint_type": "SMD",
        "max_size": (5.0, 5.0)
    })
    
    print(f"Found {len(results)} footprints")
    # Group by size
    size_groups = {}
    for fp in results:
        size_key = f"{fp.body_size[0]:.1f}x{fp.body_size[1]:.1f}"
        if size_key not in size_groups:
            size_groups[size_key] = []
        size_groups[size_key].append(fp)
    
    print("Size distribution:")
    for size, footprints in sorted(size_groups.items())[:10]:
        print(f"  {size}mm: {len(footprints)} footprints")
    
    # Example 5: Get detailed info about a specific footprint
    print("\n5. Detailed footprint information:")
    print("-" * 40)
    
    footprint_id = "Resistor_SMD:R_0603_1608Metric"
    info = pcb.get_footprint_info(footprint_id)
    
    if info:
        print(f"Footprint: {footprint_id}")
        print(f"  Description: {info.description}")
        print(f"  Tags: {info.tags}")
        print(f"  Pad count: {info.pad_count}")
        print(f"  Pad types: {', '.join(info.pad_types)}")
        print(f"  Body size: {info.body_size[0]}x{info.body_size[1]}mm")
        print(f"  Courtyard area: {info.courtyard_area:.2f}mm²")
        print(f"  Is SMD: {info.is_smd}")
        print(f"  Is THT: {info.is_tht}")
        if info.models_3d:
            print(f"  3D models: {len(info.models_3d)}")
    else:
        print(f"Footprint {footprint_id} not found")
    
    # Example 6: List available libraries
    print("\n6. Available footprint libraries:")
    print("-" * 40)
    libraries = pcb.list_available_libraries()
    print(f"Found {len(libraries)} libraries:")
    for lib in sorted(libraries)[:10]:
        print(f"  - {lib}")
    if len(libraries) > 10:
        print(f"  ... and {len(libraries) - 10} more")


if __name__ == "__main__":
    main()