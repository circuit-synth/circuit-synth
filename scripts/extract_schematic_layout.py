#!/usr/bin/env python3
"""
Extract component bounding boxes from a KiCad schematic file
and save as intermediate JSON format for LLM-assisted layout optimization.

Usage:
    python extract_schematic_layout.py <schematic.kicad_sch> [output.json]
"""

import sys
import json
from pathlib import Path

# Add parent src directory to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))
sys.path.insert(0, str(Path(__file__).parent.parent / "submodules" / "kicad-sch-api"))

from circuit_synth.kicad.schematic.layout_intermediate import LayoutIntermediate
from kicad_sch_api.core.schematic import Schematic


def main():
    if len(sys.argv) < 2:
        print("Usage: python extract_schematic_layout.py <schematic.kicad_sch> [output.json]")
        sys.exit(1)

    schematic_path = Path(sys.argv[1])
    if not schematic_path.exists():
        print(f"Error: Schematic file not found: {schematic_path}")
        sys.exit(1)

    # Determine output path
    if len(sys.argv) >= 3:
        output_path = Path(sys.argv[2])
    else:
        output_path = schematic_path.parent / f"{schematic_path.stem}_layout.json"

    print(f"📖 Reading schematic: {schematic_path}")

    # Load schematic using kicad-sch-api
    schematic = Schematic.load(str(schematic_path))

    # Get components - check for different attribute names
    components = getattr(schematic, 'components', getattr(schematic, 'symbols', []))
    print(f"📦 Found {len(components)} components")

    # Generate intermediate layout
    layout_gen = LayoutIntermediate(schematic)
    metadata = {
        "source_schematic": str(schematic_path),
        "algorithm": "text_flow",  # Target algorithm
        "spacing_mm": 5.08,
        "margin_mm": 25.4,
        "component_count": len(components),
    }

    layout_gen.save_to_file(output_path, metadata)

    print(f"\n✅ Layout intermediate saved to: {output_path}")
    print(f"   Use this file to analyze and optimize component placement")


if __name__ == "__main__":
    main()
