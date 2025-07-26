#!/usr/bin/env python3
"""
List all available KiCad footprint libraries.

This script discovers and lists all footprint libraries found in the system,
showing statistics about each library.
"""

import sys
from pathlib import Path
from collections import defaultdict

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from circuit_synth.kicad_api.pcb import PCBBoard
from circuit_synth.kicad_api.pcb.footprint_library import get_footprint_cache


def main():
    """List all available footprint libraries with statistics."""
    print("KiCad Footprint Libraries")
    print("=" * 60)
    
    # Get the footprint cache directly
    cache = get_footprint_cache()
    
    # Get all libraries
    libraries = cache.list_libraries()
    print(f"\nFound {len(libraries)} footprint libraries")
    
    # Gather statistics for each library
    library_stats = defaultdict(lambda: {
        'footprint_count': 0,
        'smd_count': 0,
        'tht_count': 0,
        'mixed_count': 0,
        'total_pads': 0,
        'sizes': set()
    })
    
    # Search all footprints to gather stats
    all_footprints = cache.search_footprints("")  # Empty query returns all
    
    for fp in all_footprints:
        stats = library_stats[fp.library]
        stats['footprint_count'] += 1
        stats['total_pads'] += fp.pad_count
        
        if fp.is_smd:
            stats['smd_count'] += 1
        elif fp.is_tht:
            stats['tht_count'] += 1
        elif fp.is_mixed:
            stats['mixed_count'] += 1
        
        # Track unique sizes (rounded to 1 decimal)
        size_str = f"{fp.body_size[0]:.1f}x{fp.body_size[1]:.1f}"
        stats['sizes'].add(size_str)
    
    # Display library information
    print("\nLibrary Statistics:")
    print("-" * 60)
    print(f"{'Library':<30} {'Total':<8} {'SMD':<8} {'THT':<8} {'Mixed':<8}")
    print("-" * 60)
    
    # Sort by footprint count
    sorted_libs = sorted(library_stats.items(), 
                        key=lambda x: x[1]['footprint_count'], 
                        reverse=True)
    
    for lib_name, stats in sorted_libs[:20]:  # Show top 20
        print(f"{lib_name:<30} "
              f"{stats['footprint_count']:<8} "
              f"{stats['smd_count']:<8} "
              f"{stats['tht_count']:<8} "
              f"{stats['mixed_count']:<8}")
    
    if len(sorted_libs) > 20:
        print(f"\n... and {len(sorted_libs) - 20} more libraries")
    
    # Show some interesting statistics
    print("\nOverall Statistics:")
    print("-" * 40)
    total_footprints = sum(s['footprint_count'] for s in library_stats.values())
    total_smd = sum(s['smd_count'] for s in library_stats.values())
    total_tht = sum(s['tht_count'] for s in library_stats.values())
    total_mixed = sum(s['mixed_count'] for s in library_stats.values())
    
    print(f"Total footprints: {total_footprints:,}")
    print(f"SMD footprints: {total_smd:,} ({total_smd/total_footprints*100:.1f}%)")
    print(f"THT footprints: {total_tht:,} ({total_tht/total_footprints*100:.1f}%)")
    print(f"Mixed footprints: {total_mixed:,} ({total_mixed/total_footprints*100:.1f}%)")
    
    # Find libraries with specific characteristics
    print("\nSpecialized Libraries:")
    print("-" * 40)
    
    # Connector libraries
    connector_libs = [lib for lib in sorted_libs 
                     if 'connector' in lib[0].lower() or 'conn' in lib[0].lower()]
    if connector_libs:
        print(f"\nConnector libraries ({len(connector_libs)}):")
        for lib, stats in connector_libs[:5]:
            print(f"  - {lib}: {stats['footprint_count']} footprints")
    
    # SMD-only libraries
    smd_only_libs = [(lib, stats) for lib, stats in sorted_libs 
                     if stats['smd_count'] == stats['footprint_count'] and stats['footprint_count'] > 0]
    if smd_only_libs:
        print(f"\nSMD-only libraries ({len(smd_only_libs)}):")
        for lib, stats in smd_only_libs[:5]:
            print(f"  - {lib}: {stats['footprint_count']} footprints")
    
    # THT-only libraries
    tht_only_libs = [(lib, stats) for lib, stats in sorted_libs 
                     if stats['tht_count'] == stats['footprint_count'] and stats['footprint_count'] > 0]
    if tht_only_libs:
        print(f"\nTHT-only libraries ({len(tht_only_libs)}):")
        for lib, stats in tht_only_libs[:5]:
            print(f"  - {lib}: {stats['footprint_count']} footprints")
    
    # Show library paths
    print("\nLibrary Search Paths:")
    print("-" * 40)
    for path in cache._library_paths:
        print(f"  {path}")
        # Count .pretty directories in this path
        if path.exists():
            pretty_dirs = list(path.glob("*.pretty"))
            if pretty_dirs:
                print(f"    Contains {len(pretty_dirs)} .pretty directories")


if __name__ == "__main__":
    main()