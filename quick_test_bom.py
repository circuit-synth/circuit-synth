#!/usr/bin/env python3
"""Quick BOM test to verify the feature works"""

from circuit_synth import circuit, Component

@circuit(name="TestBOM")
def test_board():
    """A simple test circuit with various components"""
    # Resistors
    r1 = Component(symbol="Device:R", value="10k", ref="R1")
    r2 = Component(symbol="Device:R", value="1k", ref="R2")
    r3 = Component(symbol="Device:R", value="4.7k", ref="R3")

    # Capacitors
    c1 = Component(symbol="Device:C", value="100nF", ref="C1")
    c2 = Component(symbol="Device:C", value="10uF", ref="C2")

    # Diodes
    d1 = Component(symbol="Device:LED", value="Red", ref="D1")
    d2 = Component(symbol="Device:D", value="1N4007", ref="D2")

    return locals()

if __name__ == "__main__":
    print("🔧 Creating test circuit...")
    circuit_obj = test_board()

    print(f"✓ Circuit created: {circuit_obj.name}")
    print(f"✓ Components: {len(circuit_obj._components)}")

    print("\n🔧 Generating BOM...")
    result = circuit_obj.generate_bom(project_name="quick_test_bom")

    print(f"\n✅ BOM Generated Successfully!")
    print(f"   File: {result['file']}")
    print(f"   Component count: {result['component_count']}")
    print(f"   Project path: {result['project_path']}")

    print(f"\n📄 CSV Content:")
    print("=" * 80)
    with open(result['file'], 'r') as f:
        content = f.read()
        print(content)
    print("=" * 80)
