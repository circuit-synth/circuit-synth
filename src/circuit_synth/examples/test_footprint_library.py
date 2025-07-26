#!/usr/bin/env python3
"""
Test script to verify footprint library functionality.

This script performs basic tests to ensure the footprint library
cache is working correctly.
"""

import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from circuit_synth.kicad_api.pcb import PCBBoard, get_footprint_cache


def test_footprint_library():
    """Run basic tests on the footprint library."""
    print("Testing Footprint Library Integration")
    print("=" * 50)
    
    # Test 1: Get cache instance
    print("\n1. Testing cache initialization...")
    cache = get_footprint_cache()
    print(f"   ✓ Cache initialized")
    print(f"   Library paths: {len(cache._library_paths)}")
    for path in cache._library_paths[:3]:
        print(f"     - {path}")
    
    # Test 2: List libraries
    print("\n2. Testing library discovery...")
    libraries = cache.list_libraries()
    print(f"   ✓ Found {len(libraries)} libraries")
    if libraries:
        print("   Sample libraries:")
        for lib in sorted(libraries)[:5]:
            print(f"     - {lib}")
    
    # Test 3: Search footprints
    print("\n3. Testing footprint search...")
    
    # Search for common footprints
    test_searches = [
        ("0603", {"footprint_type": "SMD"}),
        ("SOIC", {"pad_count": 8}),
        ("connector", {"footprint_type": "THT"}),
    ]
    
    for query, filters in test_searches:
        results = cache.search_footprints(query, filters)
        print(f"   Search '{query}' with filters {filters}:")
        print(f"     Found {len(results)} footprints")
        if results:
            fp = results[0]
            print(f"     Example: {fp.library}:{fp.name}")
            print(f"       Pads: {fp.pad_count}, Size: {fp.body_size[0]:.1f}x{fp.body_size[1]:.1f}mm")
    
    # Test 4: Get specific footprint
    print("\n4. Testing footprint retrieval...")
    test_footprints = [
        "Resistor_SMD:R_0603_1608Metric",
        "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
        "Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical"
    ]
    
    for fp_id in test_footprints:
        info = cache.get_footprint(fp_id)
        if info:
            print(f"   ✓ Found {fp_id}")
            print(f"     Description: {info.description}")
            print(f"     Pads: {info.pad_count}, Type: {', '.join(info.pad_types)}")
        else:
            print(f"   ✗ Not found: {fp_id}")
    
    # Test 5: PCBBoard integration
    print("\n5. Testing PCBBoard integration...")
    pcb = PCBBoard()
    
    # Search through PCBBoard
    results = pcb.search_footprints("0805", filters={"footprint_type": "SMD"})
    print(f"   ✓ PCBBoard search found {len(results)} footprints")
    
    # Get footprint info through PCBBoard
    info = pcb.get_footprint_info("Capacitor_SMD:C_0805_2012Metric")
    if info:
        print(f"   ✓ PCBBoard get_footprint_info working")
        print(f"     Found: {info.name} with {info.pad_count} pads")
    
    # Test adding from library
    footprint = pcb.add_footprint_from_library(
        "Resistor_SMD:R_0603_1608Metric",
        "R1", 50, 50, value="10k"
    )
    if footprint:
        print(f"   ✓ Successfully added footprint from library")
        print(f"     Reference: {footprint.reference}")
        print(f"     Pads: {len(footprint.pads)}")
    
    # Test 6: Performance check
    print("\n6. Testing search performance...")
    import time
    
    start = time.time()
    results = cache.search_footprints("")  # Get all footprints
    elapsed = time.time() - start
    
    print(f"   Total footprints in cache: {len(results)}")
    print(f"   Search time: {elapsed:.3f} seconds")
    
    # Summary
    print("\n" + "=" * 50)
    print("Summary:")
    print(f"  Libraries: {len(libraries)}")
    print(f"  Total footprints: {len(results)}")
    print(f"  Cache working: {'Yes' if len(results) > 0 else 'No'}")
    
    return len(results) > 0


if __name__ == "__main__":
    success = test_footprint_library()
    sys.exit(0 if success else 1)