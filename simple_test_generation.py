#!/usr/bin/env python3
"""
Simple test to generate a fresh project and verify the unit fix.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def main():
    print("🧪 Testing fresh project generation with unit fix...")
    
    try:
        # Import minimal components needed
        from circuit_synth.kicad_api.core.types import SchematicSymbol, Point, Schematic
        from circuit_synth.kicad_api.core.s_expression import SExpressionParser
        import sexpdata
        
        # Create a simple schematic with one component
        schematic = Schematic(
            title="Test Schematic",
            components=[
                SchematicSymbol(
                    reference="R1",
                    value="10k",
                    lib_id="Device:R",
                    position=Point(50.0, 50.0),
                    uuid="test-uuid-123"
                )
            ]
        )
        
        print(f"✅ Created schematic with {len(schematic.components)} components")
        
        # Convert to S-expression
        parser = SExpressionParser()
        sexp = parser.to_schematic(schematic)
        
        # Convert to string
        sexp_str = sexpdata.dumps(sexp, pretty_print=True)
        
        # Write to file
        output_file = "test_output.kicad_sch"
        with open(output_file, 'w') as f:
            f.write(sexp_str)
        
        print(f"✅ Generated schematic file: {output_file}")
        
        # Check for unit presence
        if "(unit 1)" in sexp_str:
            print("✅ SUCCESS: (unit 1) is present in the generated schematic!")
            
            # Show a snippet around the unit
            lines = sexp_str.split('\n')
            for i, line in enumerate(lines):
                if "(unit 1)" in line:
                    print(f"📍 Found at line {i+1}: {line.strip()}")
                    # Show context
                    start = max(0, i-3)
                    end = min(len(lines), i+4)
                    print("Context:")
                    for j in range(start, end):
                        marker = ">>> " if j == i else "    "
                        print(f"{marker}{lines[j]}")
                    break
            
            return True
        else:
            print("❌ FAILURE: (unit 1) is missing from the generated schematic!")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    if success:
        print("\n🎉 Fresh project generation test PASSED!")
        print("The unit fix should resolve the KiCad 'R?' display issue.")
        sys.exit(0)
    else:
        print("\n💥 Fresh project generation test FAILED!")
        sys.exit(1)