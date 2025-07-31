#!/usr/bin/env python3
"""
JLC Component Finder Demo

Demonstrates how easy it is to find manufacturable components and use them
in circuit-synth designs.
"""

import sys

sys.path.insert(0, "src")

from circuit_synth.jlc_integration import (
    find_component,
    find_components,
    print_component_recommendation,
)


def demo_single_component():
    """Demo finding a single best component."""
    print("🔍 Finding the best STM32G4 microcontroller...")

    recommendation = find_component("STM32G4", "LQFP")

    if recommendation:
        print_component_recommendation(recommendation)

        print("\n🚀 You can now use this component directly in your circuit:")
        print("```python")
        print("from circuit_synth import *")
        print()
        print("@circuit")
        print("def my_circuit():")
        print('    """Example circuit with manufacturable components"""')
        print("    VCC_3V3 = Net('VCC_3V3')")
        print("    GND = Net('GND')")
        print()
        print("    # Component found by JLC integration")
        print("    " + recommendation.circuit_synth_code.replace("\n", "\n    "))
        print()
        print("    # Connect power")
        print("    component['VDD'] += VCC_3V3")
        print("    component['VSS'] += GND")
        print("```")
    else:
        print("❌ No suitable components found")


def demo_multiple_components():
    """Demo finding multiple component options."""
    print("\n" + "=" * 60)
    print("🔍 Finding multiple voltage regulator options...")

    recommendations = find_components("voltage regulator 3.3V", max_results=3)

    if recommendations:
        print(f"\n✅ Found {len(recommendations)} suitable voltage regulators:")

        for i, rec in enumerate(recommendations, 1):
            print(f"\n--- Option {i} ---")
            print_component_recommendation(rec)

        # Show usage example
        best_reg = recommendations[0]
        print(f"\n🎯 Recommended choice: {best_reg.manufacturer_part}")
        print("   Reasons: Highest manufacturability score with good stock levels")

        print("\n📋 Ready-to-use in power supply circuit:")
        print("```python")
        print("@circuit")
        print("def power_supply():")
        print('    """3.3V power supply with high-availability components"""')
        print("    VCC_5V = Net('VCC_5V')")
        print("    VCC_3V3 = Net('VCC_3V3')")
        print("    GND = Net('GND')")
        print()
        print("    # Regulator")
        print("    " + best_reg.circuit_synth_code.replace("\n", "\n    "))
        print("    component['VIN'] += VCC_5V")
        print("    component['VOUT'] += VCC_3V3")
        print("    component['GND'] += GND")
        print("```")
    else:
        print("❌ No suitable voltage regulators found")


def demo_passive_components():
    """Demo finding passive components with values."""
    print("\n" + "=" * 60)
    print("🔍 Finding passive components...")

    # Find resistors
    resistor_rec = find_component("10K resistor", "0603")
    if resistor_rec:
        print("\n📏 Found 10K resistor:")
        print_component_recommendation(resistor_rec)

    # Find capacitors
    cap_rec = find_component("10uF capacitor", "0805")
    if cap_rec:
        print("\n🔋 Found 10uF capacitor:")
        print_component_recommendation(cap_rec)


def demo_connector_search():
    """Demo finding connectors."""
    print("\n" + "=" * 60)
    print("🔍 Finding USB-C connector...")

    usb_rec = find_component("USB-C connector")
    if usb_rec:
        print_component_recommendation(usb_rec)

        print("\n🔌 Perfect for power and data applications:")
        print("```python")
        print("@circuit")
        print("def usb_interface():")
        print('    """USB-C interface with power and data"""')
        print("    USB_5V = Net('USB_5V')")
        print("    USB_DP = Net('USB_DP')")
        print("    USB_DM = Net('USB_DM')")
        print("    GND = Net('GND')")
        print()
        print("    # USB-C connector")
        print("    " + usb_rec.circuit_synth_code.replace("\n", "\n    "))
        print("    component['VBUS'] += USB_5V")
        print("    component['D+'] += USB_DP")
        print("    component['D-'] += USB_DM")
        print("    component['GND'] += GND")
        print("```")


def main():
    """Run all demos."""
    print("=" * 60)
    print("🎯 JLC Component Finder Demo")
    print("   Making component selection effortless!")
    print("=" * 60)

    try:
        demo_single_component()
        demo_multiple_components()
        demo_passive_components()
        demo_connector_search()

        print("\n" + "=" * 60)
        print("✅ Demo Complete!")
        print("💡 Key Benefits Demonstrated:")
        print("   • Real-time JLCPCB stock and pricing data")
        print("   • Automatic KiCad symbol/footprint matching")
        print("   • Ready-to-use circuit-synth code generation")
        print("   • Manufacturability scoring for informed decisions")
        print("   • Multiple options with clear trade-offs")
        print("\n🚀 Start using these components in your circuits today!")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        print("💡 This might be due to network connectivity or JLCPCB rate limits")
        print("   Try running the demo again in a few moments")


if __name__ == "__main__":
    main()
