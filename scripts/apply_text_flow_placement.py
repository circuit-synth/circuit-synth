#!/usr/bin/env python3
"""
Apply text-flow placement algorithm to a layout JSON file.

Usage:
    python apply_text_flow_placement.py <layout.json> [output.json]
"""

import sys
import json
from pathlib import Path

# Add parent src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from circuit_synth.kicad.schematic.text_flow_placement import TextFlowPlacer


def main():
    if len(sys.argv) < 2:
        print("Usage: python apply_text_flow_placement.py <layout.json> [output.json]")
        sys.exit(1)

    input_path = Path(sys.argv[1])
    if not input_path.exists():
        print(f"Error: JSON file not found: {input_path}")
        sys.exit(1)

    # Determine output path
    if len(sys.argv) >= 3:
        output_path = Path(sys.argv[2])
    else:
        output_path = input_path.parent / f"{input_path.stem}_placed.json"

    print(f"📖 Reading layout from: {input_path}")

    # Load layout data
    with open(input_path, 'r') as f:
        layout_data = json.load(f)

    metadata = layout_data.get("metadata", {})
    components = layout_data.get("components", [])

    # Create placer with parameters from metadata
    placer = TextFlowPlacer(
        sheet_width=210.0,  # Start with A4
        sheet_height=297.0,
        margin=metadata.get("margin_mm", 25.4),
        spacing=metadata.get("spacing_mm", 5.08),
    )

    # Calculate placements
    placements, selected_sheet = placer.place_components(components)

    # Update components with new positions
    updated_components = placer.update_json_with_placements(components, placements)

    # Update metadata
    metadata["algorithm"] = "text_flow"
    metadata["selected_sheet_size"] = selected_sheet

    # Save updated layout
    output_data = {
        "metadata": metadata,
        "components": updated_components,
    }

    with open(output_path, 'w') as f:
        json.dump(output_data, f, indent=2)

    print(f"✅ Placed layout saved to: {output_path}")
    print(f"   Sheet size: {selected_sheet}")
    print(f"   Components: {len(updated_components)}")


if __name__ == "__main__":
    main()
