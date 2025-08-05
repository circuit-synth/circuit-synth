#!/usr/bin/env python3
"""Test sheet parsing to debug hierarchical detection."""

from circuit_synth.kicad_api.core.s_expression import SExpressionParser

# Parse the main schematic
parser = SExpressionParser()
sch_file = "hierarchical_resistors_test/hierarchical_resistors_test.kicad_sch"
schematic = parser.parse_file(sch_file)

print(f"Schematic has {len(schematic.components)} components")
print(f"Schematic attributes: {dir(schematic)}")

# Look for sheet components
sheet_count = 0
for i, comp in enumerate(schematic.components):
    if hasattr(comp, 'properties'):
        for prop in comp.properties:
            if prop.name == 'Sheetfile':
                sheet_count += 1
                print(f"\nFound sheet component #{i}:")
                print(f"  Reference: {comp.reference}")
                for p in comp.properties:
                    print(f"  {p.name}: {p.value}")
                break

print(f"\nTotal sheet components found: {sheet_count}")

# Check if schematic has 'sheets' attribute
if hasattr(schematic, 'sheets'):
    print(f"\nSchematic has 'sheets' attribute with {len(schematic.sheets)} sheets")
    for i, sheet in enumerate(schematic.sheets):
        print(f"\nSheet #{i}:")
        print(f"  Type: {type(sheet)}")
        print(f"  Attributes: {[attr for attr in dir(sheet) if not attr.startswith('_')]}")
        
        # Try to get sheet info
        if hasattr(sheet, 'file'):
            print(f"  File: {sheet.file}")
        if hasattr(sheet, 'name'):
            print(f"  Name: {sheet.name}")
        if hasattr(sheet, 'at'):
            print(f"  At: {sheet.at}")
        if hasattr(sheet, 'size'):
            print(f"  Size: {sheet.size}")
        if hasattr(sheet, 'properties'):
            print(f"  Properties: {sheet.properties}")
else:
    print("\nSchematic does NOT have 'sheets' attribute")