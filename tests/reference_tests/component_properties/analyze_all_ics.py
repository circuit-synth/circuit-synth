"""
Automated IC property positioning analysis script.

This script analyzes all manually placed IC components and extracts their
property positioning patterns for comparison.
"""

import re
import os
from pathlib import Path


def extract_component_data(sch_file):
    """Extract component position and property positions from schematic."""
    print(f"\n=== Analyzing: {sch_file.name} ===")

    with open(sch_file, 'r') as f:
        content = f.read()

    # Find component symbol block
    symbol_match = re.search(r'\(symbol\s*\n\s*\(lib_id "([^"]+)"\)\s*\n\s*\(at ([\d.]+) ([\d.]+) ([\d.]+)\)', content)

    if not symbol_match:
        print("ERROR: Could not find component symbol")
        return None

    lib_id = symbol_match.group(1)
    comp_x = float(symbol_match.group(2))
    comp_y = float(symbol_match.group(3))
    comp_rot = float(symbol_match.group(4))

    print(f"Component: {lib_id}")
    print(f"Position: ({comp_x}, {comp_y}) @ {comp_rot}°")

    # Extract all property positions
    properties = {}
    prop_pattern = r'\(property "([^"]+)"\s+(?:"[^"]*"|[^\s]+)\s*\n\s*\(at ([\d.]+) ([\d.]+) ([\d.]+)\)'

    for match in re.finditer(prop_pattern, content):
        prop_name = match.group(1)
        prop_x = float(match.group(2))
        prop_y = float(match.group(3))
        prop_rot = float(match.group(4))

        offset_x = prop_x - comp_x
        offset_y = prop_y - comp_y

        properties[prop_name] = {
            'position': (prop_x, prop_y, prop_rot),
            'offset': (offset_x, offset_y, prop_rot)
        }

        print(f"  {prop_name}: ({prop_x:.4f}, {prop_y:.4f}, {prop_rot}°) | Offset: ({offset_x:+.4f}, {offset_y:+.4f})")

    return {
        'lib_id': lib_id,
        'component_position': (comp_x, comp_y, comp_rot),
        'properties': properties
    }


def analyze_all_components():
    """Analyze all IC components in test directories."""
    base_path = Path(__file__).parent

    ic_dirs = [
        'RF_Module_ESP32-WROOM-32',
        '74xx_74LS245',
        'Interface_UART_MAX3485',
        'Regulator_Linear_AMS1117-3.3',
        'Regulator_Switching_TPS54202DDC',
        'Transistor_FET_AO3401A',
    ]

    results = {}

    for dir_name in ic_dirs:
        sch_path = base_path / dir_name / 'circuit_synth_generated'

        # Find .kicad_sch file
        sch_files = list(sch_path.glob('*.kicad_sch'))

        if not sch_files:
            print(f"\nWARNING: No schematic found in {dir_name}")
            continue

        data = extract_component_data(sch_files[0])
        if data:
            results[dir_name] = data

    return results


def compare_patterns(results):
    """Compare positioning patterns across all ICs."""
    print("\n" + "="*80)
    print("PATTERN COMPARISON")
    print("="*80)

    print("\n### Reference Property Offsets ###")
    for name, data in results.items():
        if 'Reference' in data['properties']:
            offset = data['properties']['Reference']['offset']
            print(f"{data['lib_id']:40} | Ref: ({offset[0]:+7.4f}, {offset[1]:+7.4f}, {offset[2]:3.0f}°)")

    print("\n### Value Property Offsets ###")
    for name, data in results.items():
        if 'Value' in data['properties']:
            offset = data['properties']['Value']['offset']
            print(f"{data['lib_id']:40} | Val: ({offset[0]:+7.4f}, {offset[1]:+7.4f}, {offset[2]:3.0f}°)")

    print("\n### Footprint Property Offsets ###")
    for name, data in results.items():
        if 'Footprint' in data['properties']:
            offset = data['properties']['Footprint']['offset']
            print(f"{data['lib_id']:40} | Fpt: ({offset[0]:+7.4f}, {offset[1]:+7.4f}, {offset[2]:3.0f}°)")

    # Check for patterns
    print("\n### Pattern Analysis ###")

    # Group by X offset
    x_offsets = {}
    for name, data in results.items():
        if 'Reference' in data['properties']:
            x = round(data['properties']['Reference']['offset'][0], 4)
            if x not in x_offsets:
                x_offsets[x] = []
            x_offsets[x].append(data['lib_id'])

    print("\nComponents grouped by Reference X offset:")
    for x, components in sorted(x_offsets.items()):
        print(f"  X offset {x:+.4f}: {len(components)} components")
        for comp in components:
            print(f"    - {comp}")


if __name__ == "__main__":
    print("IC Property Positioning Analysis")
    print("="*80)

    results = analyze_all_components()

    if results:
        compare_patterns(results)
    else:
        print("\nNo components analyzed. Make sure schematics have been manually placed.")
