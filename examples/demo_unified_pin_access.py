#!/usr/bin/env python3
"""
Demo: Unified Pin Access Interface

This demo shows the new component.pins.VCC syntax in action.
"""

from circuit_synth import Component, Net, circuit


@circuit
def demonstrate_unified_pin_access():
    """
    Demonstrate the unified pin access interface with working examples.
    """
    
    # Create some nets
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')
    signal_a = Net('SIGNAL_A')
    signal_b = Net('SIGNAL_B')
    
    print("🚀 Unified Pin Access Interface Demo")
    print("=" * 50)
    
    # 1. Simple components (resistors, capacitors) - numbered pins
    print("\n1. Simple Components (Numbered Pins)")
    print("-" * 40)
    
    # Resistor
    resistor = Component(
        symbol="Device:R",
        ref="R1",
        value="10K",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    print(f"📦 Created: {resistor}")
    print(f"🔌 Pin access: resistor.pins[1], resistor.pins[2]")
    
    # Connect using new syntax
    resistor.pins[1] += signal_a
    resistor.pins[2] += gnd
    print("✅ Connected resistor.pins[1] to SIGNAL_A, resistor.pins[2] to GND")
    
    # Capacitor
    capacitor = Component(
        symbol="Device:C",
        ref="C1",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    print(f"📦 Created: {capacitor}")
    capacitor.pins[1] += vcc_3v3
    capacitor.pins[2] += gnd
    print("✅ Connected capacitor.pins[1] to VCC_3V3, capacitor.pins[2] to GND")
    
    # 2. Show backward compatibility
    print("\n2. Backward Compatibility")
    print("-" * 30)
    
    inductor = Component(
        symbol="Device:L",
        ref="L1", 
        value="10uH",
        footprint="Inductor_SMD:L_0603_1608Metric"
    )
    
    # Both old and new syntax work
    inductor[1] += signal_a         # Old syntax
    inductor.pins[2] += signal_b    # New syntax
    
    print("✅ inductor[1] += signal_a (old syntax)")
    print("✅ inductor.pins[2] += signal_b (new syntax)")
    print("✅ Both syntaxes work together seamlessly!")
    
    # 3. Pin information
    print("\n3. Pin Information and Discovery")
    print("-" * 38)
    
    print(f"📊 Resistor pin count: {len(resistor.pins)}")
    print(f"📊 Capacitor pin count: {len(capacitor.pins)}")
    
    print("\n📋 Resistor pin details:")
    print(resistor.pins.list_all())
    
    # 4. Error handling demo
    print("\n4. Error Handling")
    print("-" * 20)
    
    try:
        resistor.pins[3]  # This will fail
    except Exception as e:
        print(f"✅ Helpful error for invalid pin: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Demo Complete!")
    print("\nKey Benefits:")
    print("• ✨ Intuitive syntax: component.pins[1] or component.pins.VCC")
    print("• 🔄 Full backward compatibility with component[1]")
    print("• 🛡️  Clear error messages for debugging")
    print("• 📋 Pin discovery with .list_all()")
    print("• 🔧 Case-insensitive aliases for common pins")


if __name__ == "__main__":
    demonstrate_unified_pin_access()