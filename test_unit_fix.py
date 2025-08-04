#!/usr/bin/env python3
"""
Test script to verify that the unit fix resolves the KiCad "R?" display issue.
"""

import sys
import os
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def test_unit_fix():
    """Test that components now have (unit 1) in the schematic."""
    print("🧪 Testing unit fix for KiCad display issue...")
    
    try:
        from circuit_synth.kicad_api.core.types import SchematicSymbol, Point
        from circuit_synth.kicad_api.core.s_expression import SExpressionParser
        import sexpdata
        
        # Create a test symbol
        symbol = SchematicSymbol(
            reference="R1",
            value="10k",
            lib_id="Device:R",
            position=Point(50.0, 50.0),
            uuid="test-uuid-123"
        )
        
        print(f"✅ Created test symbol: {symbol.reference} with unit={symbol.unit}")
        
        # Format to S-expression
        parser = SExpressionParser()
        sexp = parser._symbol_to_sexp(symbol)
        
        # Convert to string to check
        sexp_str = sexpdata.dumps(sexp, pretty_print=True)
        print("📄 Generated S-expression:")
        print(sexp_str)
        
        # Check if (unit 1) is present
        if "(unit 1)" in sexp_str:
            print("✅ SUCCESS: (unit 1) is present in the S-expression!")
            return True
        else:
            print("❌ FAILURE: (unit 1) is missing from the S-expression!")
            return False
            
    except Exception as e:
        print(f"❌ ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = test_unit_fix()
    if success:
        print("\n🎉 Unit fix test PASSED - KiCad should now display 'R1' instead of 'R?'")
        sys.exit(0)
    else:
        print("\n💥 Unit fix test FAILED - More work needed")
        sys.exit(1)