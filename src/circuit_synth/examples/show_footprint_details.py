#!/usr/bin/env python3
"""
Show detailed information about a specific footprint.

This script demonstrates how to retrieve and display comprehensive
information about a footprint from the library.
"""

import argparse
import sys
from pathlib import Path

# Add parent directory to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from circuit_synth.kicad_api.pcb import PCBBoard
from circuit_synth.kicad_api.pcb.footprint_library import get_footprint_cache


def show_footprint_details(footprint_id: str):
    """Display detailed information about a footprint."""
    cache = get_footprint_cache()

    # Get basic info
    info = cache.get_footprint(footprint_id)
    if not info:
        print(f"Error: Footprint '{footprint_id}' not found")
        print("\nHint: Use format 'Library:FootprintName'")
        print("Example: Resistor_SMD:R_0603_1608Metric")
        return

    print(f"Footprint Details: {footprint_id}")
    print("=" * 60)

    # Basic information
    print("\nBasic Information:")
    print("-" * 40)
    print(f"Library: {info.library}")
    print(f"Name: {info.name}")
    print(f"Description: {info.description}")
    print(f"Tags: {info.tags}")
    print(f"Keywords: {info.keywords}")

    # Physical characteristics
    print("\nPhysical Characteristics:")
    print("-" * 40)
    print(f"Pad count: {info.pad_count}")
    print(f"Pad types: {', '.join(sorted(info.pad_types))}")
    print(f"Body size: {info.body_size[0]:.2f} x {info.body_size[1]:.2f} mm")
    print(f"Courtyard area: {info.courtyard_area:.2f} mm²")
    print(
        f"Bounding box: ({info.bbox[0]:.2f}, {info.bbox[1]:.2f}) to ({info.bbox[2]:.2f}, {info.bbox[3]:.2f}) mm"
    )

    # Type classification
    print("\nType Classification:")
    print("-" * 40)
    print(f"Is SMD: {info.is_smd}")
    print(f"Is THT: {info.is_tht}")
    print(f"Is Mixed: {info.is_mixed}")

    # 3D models
    if info.models_3d:
        print("\n3D Models:")
        print("-" * 40)
        for model in info.models_3d:
            print(f"  - {model}")

    # File information
    if info.file_path:
        print("\nFile Information:")
        print("-" * 40)
        print(f"File path: {info.file_path}")
        if info.last_modified:
            print(f"Last modified: {info.last_modified.strftime('%Y-%m-%d %H:%M:%S')}")

    # Get detailed pad information
    data = cache.get_footprint_data(footprint_id)
    if data and "pad" in data:
        print("\nPad Details:")
        print("-" * 40)
        print(
            f"{'Pad':<6} {'Type':<10} {'Shape':<10} {'Size (mm)':<15} {'Position (mm)':<15} {'Layers'}"
        )
        print("-" * 80)

        pads = []
        for pad_data in data["pad"]:
            pad_info = cache._parse_pad(pad_data)
            if pad_info:
                pads.append(pad_info)

        # Sort pads by number (handle both numeric and alphanumeric)
        def pad_sort_key(pad):
            num = pad["number"]
            # Try to extract numeric part for sorting
            try:
                return (0, int(num))
            except ValueError:
                # For alphanumeric, separate letters and numbers
                import re

                match = re.match(r"([A-Za-z]*)(\d*)", num)
                if match:
                    letters, numbers = match.groups()
                    return (1, letters, int(numbers) if numbers else 0)
                return (2, num)

        pads.sort(key=pad_sort_key)

        for pad in pads:
            pad_type = pad.get("type", "unknown")
            pad_shape = pad.get("shape", "unknown")
            size = f"{pad.get('width', 0):.2f} x {pad.get('height', 0):.2f}"
            pos = f"({pad.get('x', 0):.2f}, {pad.get('y', 0):.2f})"

            # Truncate long layer lists
            layers = ", ".join(pad.get("layers", []))
            if len(layers) > 30:
                layers = layers[:27] + "..."

            print(
                f"{pad['number']:<6} {pad_type:<10} {pad_shape:<10} {size:<15} {pos:<15} {layers}"
            )

    # Show similar footprints
    print("\nSimilar Footprints:")
    print("-" * 40)

    # Search for footprints with similar characteristics
    similar = cache.search_footprints(
        info.name.split("_")[0],
        filters={
            "pad_count": info.pad_count,
            "footprint_type": (
                "SMD" if info.is_smd else ("THT" if info.is_tht else None)
            ),
        },
    )

    # Remove the current footprint and show up to 5 similar ones
    similar = [fp for fp in similar if f"{fp.library}:{fp.name}" != footprint_id][:5]

    if similar:
        for fp in similar:
            print(f"  - {fp.library}:{fp.name}")
            print(f"    {fp.description}")
    else:
        print("  No similar footprints found")


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Show detailed information about a KiCad footprint",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s Resistor_SMD:R_0603_1608Metric
  %(prog)s Package_SO:SOIC-8_3.9x4.9mm_P1.27mm
  %(prog)s Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical
        """,
    )

    parser.add_argument(
        "footprint_id", help='Footprint ID in format "Library:FootprintName"'
    )

    args = parser.parse_args()

    show_footprint_details(args.footprint_id)


if __name__ == "__main__":
    main()
