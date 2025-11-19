"""
Generate empty_test.kicad_sch test fixture.

Scenario: Edge case - completely empty schematic.
Tests that audit logic doesn't crash on empty files.
Compliance: N/A (no components)
"""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parents[3] / "submodules" / "kicad-sch-api"))

import kicad_sch_api as ksa


def main():
    """Generate empty_test test fixture."""
    print("Generating empty_test.kicad_sch...")

    # Create empty schematic (no components)
    sch = ksa.create_schematic("EmptyTest")

    # Don't add any components - intentionally empty

    # Save schematic
    output_path = Path(__file__).parent / "empty_test.kicad_sch"
    sch.save(str(output_path))

    print(f"✓ Generated: {output_path}")
    print(f"  Components: 0")
    print(f"  Purpose: Edge case testing (empty schematic)")


if __name__ == "__main__":
    main()
