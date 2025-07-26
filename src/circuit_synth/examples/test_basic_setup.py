"""
Basic test script to verify KiCad API setup.

This script tests the basic functionality of the new KiCad API structure.
"""

import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent))

from circuit_synth.kicad_api.core import (
    Schematic, SchematicSymbol, Wire, Label, Point,
    SExpressionParser, get_symbol_cache,
    WireRoutingStyle, LabelType
)


def test_basic_types():
    """Test basic data types."""
    print("Testing basic types...")
    
    # Create a point
    p = Point(10.0, 20.0)
    print(f"  Point: ({p.x}, {p.y})")
    
    # Create a schematic
    schematic = Schematic()
    print(f"  Schematic UUID: {schematic.uuid}")
    
    # Create a symbol
    symbol = SchematicSymbol(
        reference="R1",
        value="10k",
        lib_id="Device:R",
        position=Point(50.0, 50.0)
    )
    print(f"  Symbol: {symbol.reference} = {symbol.value}")
    
    # Add to schematic
    schematic.add_component(symbol)
    print(f"  Components in schematic: {len(schematic.components)}")
    
    # Create a wire
    wire = Wire(points=[Point(0, 0), Point(10, 0)])
    schematic.add_wire(wire)
    print(f"  Wires in schematic: {len(schematic.wires)}")
    
    # Create a label
    label = Label(
        text="VCC",
        position=Point(5, 0),
        label_type=LabelType.GLOBAL
    )
    schematic.add_label(label)
    print(f"  Labels in schematic: {len(schematic.labels)}")
    
    print("✓ Basic types test passed")
    return True


def test_symbol_cache():
    """Test symbol cache."""
    print("\nTesting symbol cache...")
    
    cache = get_symbol_cache()
    
    # Test getting a resistor symbol
    resistor = cache.get_symbol("Device:R")
    if resistor:
        print(f"  Found resistor: {resistor.name}")
        print(f"  Reference prefix: {resistor.reference_prefix}")
        print(f"  Number of pins: {len(resistor.pins)}")
        for pin in resistor.pins:
            print(f"    Pin {pin.number}: {pin.name} ({pin.type}) at ({pin.position.x}, {pin.position.y})")
    else:
        print("  ✗ Failed to find resistor symbol")
        return False
    
    # Test reference prefix
    prefix = cache.get_reference_prefix("Device:C")
    print(f"  Capacitor prefix: {prefix}")
    
    print("✓ Symbol cache test passed")
    return True


def test_s_expression_basic():
    """Test basic S-expression functionality."""
    print("\nTesting S-expression parser...")
    
    parser = SExpressionParser()
    
    # Test parsing a simple S-expression
    test_sexp = '(test "hello" 123 (nested "world"))'
    try:
        result = parser.parse_string(test_sexp)
        print(f"  Parsed: {result}")
        
        # Test converting back
        output = parser.dumps(result)
        print(f"  Dumped: {output}")
        
        print("✓ S-expression parser test passed")
        return True
    except Exception as e:
        print(f"  ✗ S-expression parser failed: {e}")
        return False


def test_schematic_conversion():
    """Test schematic to/from S-expression conversion."""
    print("\nTesting schematic conversion...")
    
    # Create a simple schematic
    schematic = Schematic()
    schematic.title = "Test Schematic"
    schematic.date = "2025-06-08"
    schematic.revision = "1.0"
    
    # Add a component
    symbol = SchematicSymbol(
        reference="R1",
        value="10k",
        lib_id="Device:R",
        position=Point(50.0, 50.0),
        rotation=90.0
    )
    schematic.add_component(symbol)
    
    # Convert to S-expression
    parser = SExpressionParser()
    sexp = parser.from_schematic(schematic)
    print(f"  Generated S-expression with {len(sexp)} elements")
    
    # Convert back
    schematic2 = parser.to_schematic(sexp)
    print(f"  Parsed schematic: {schematic2.title}")
    print(f"  Components: {len(schematic2.components)}")
    if schematic2.components:
        comp = schematic2.components[0]
        print(f"    {comp.reference} = {comp.value} at ({comp.position.x}, {comp.position.y})")
    
    print("✓ Schematic conversion test passed")
    return True


def main():
    """Run all tests."""
    print("KiCad API Basic Setup Test")
    print("=" * 50)
    
    tests = [
        test_basic_types,
        test_symbol_cache,
        test_s_expression_basic,
        test_schematic_conversion
    ]
    
    passed = 0
    for test in tests:
        try:
            if test():
                passed += 1
        except Exception as e:
            print(f"✗ Test {test.__name__} failed with exception: {e}")
            import traceback
            traceback.print_exc()
    
    print("\n" + "=" * 50)
    print(f"Tests passed: {passed}/{len(tests)}")
    
    return passed == len(tests)


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)