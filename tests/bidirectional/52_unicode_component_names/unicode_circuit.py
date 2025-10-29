#!/usr/bin/env python3
"""
Test circuit with Unicode characters in various elements.

Tests Unicode support in:
- Component references (Greek: π)
- Component values (Greek: Ω)
- Net names (Chinese: 信号)
- Text annotations (Japanese: 温度センサー)
"""

from circuit_synth import circuit, Component, Net


@circuit(name="unicode_test")
def unicode_circuit():
    """Circuit with unicode in multiple elements.

    Tests Unicode support in:
    - Component reference: R_π (Greek pi)
    - Component values: 1kΩ, 10kΩ (Greek omega), 100μF (Greek mu)
    - Net name: 信号 (Chinese for "signal")

    Note: Text annotations not included as Text API is not yet available.
    """

    # Component with Greek pi in reference
    r_pi = Component(
        symbol="Device:R",
        ref="R_π1",  # Greek pi in reference
        value="1kΩ",  # Greek omega in value
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Component with standard reference but unicode value
    r2 = Component(
        symbol="Device:R",
        ref="R2",
        value="10kΩ",  # Greek omega in value
        footprint="Resistor_SMD:R_0603_1608Metric",
    )

    # Capacitor with unicode value
    c1 = Component(
        symbol="Device:C",
        ref="C1",
        value="100μF",  # Greek mu in value
        footprint="Capacitor_SMD:C_0603_1608Metric",
    )

    # Connect with net that has Chinese name
    signal_net = Net(name="信号")  # Chinese for "signal"
    signal_net += r_pi[2]  # Pin 2 of R_π
    signal_net += r2[1]    # Pin 1 of R2

    # Connect output
    output_net = Net(name="output")
    output_net += r2[2]    # Pin 2 of R2
    output_net += c1[1]    # Pin 1 of C1

    # Add ground connections
    gnd_net = Net(name="GND")
    gnd_net += r_pi[1]
    gnd_net += c1[2]


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = unicode_circuit()

    circuit_obj.generate_kicad_project(project_name="unicode_circuit")

    print("✅ Circuit created with unicode elements:")
    print(f"  - Component reference with π: R_π")
    print(f"  - Values with Ω: 1kΩ, 10kΩ")
    print(f"  - Value with μ: 100μF")
    print(f"  - Net name (Chinese): 信号")
    print("📁 Open in KiCad: unicode_circuit/unicode_test.kicad_pro")
