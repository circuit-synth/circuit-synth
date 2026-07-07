"""Voltage Regulator - 5V to 3.3V Linear Regulator

This example demonstrates:
- Using IC components (3-pin voltage regulator)
- Decoupling capacitor placement and purpose
- Power supply circuit design
- Multiple components working together
- Named pin connections on ICs

Circuit: AMS1117-3.3 linear regulator
- Input voltage: 5V (from USB or other source)
- Output voltage: 3.3V regulated (±2% tolerance)
- Maximum current: 1A continuous
- Dropout voltage: ~1.2V (minimum Vin-Vout difference)
- Package: SOT-223 (common 3-pin SMD package)

Decoupling capacitors (CRITICAL for stability):
- Input cap (C1): 10µF - stabilizes input voltage, filters noise
- Output cap (C2): 22µF - reduces output ripple, improves transient response
- Place capacitors as close as possible to regulator pins!
"""

from circuit_synth import Component, Net, circuit


@circuit(name="Voltage_Regulator")
def voltage_regulator():
    """5V to 3.3V linear voltage regulator circuit

    This circuit provides clean, regulated 3.3V power for microcontrollers
    and other digital logic. Common applications:
    - Power supply for ESP32, STM32, Arduino
    - USB-powered 3.3V projects
    - Sensor power rails
    - Battery-powered devices (with 5V source)

    Circuit topology:
         VIN_5V               VOUT_3V3
           │                     │
           │                     │
          ┌┴┐ C1                ┌┴┐ C2
       10µF│ │             22µF │ │
          └┬┘                  └┬┘
           │                     │
           ├─────┬──────┬────────┤
           │   ┌─┴─┐    │        │
      VIN ─┤   │AMS│    ├─ VOUT  │
           │   │1117    │        │
      GND ─┤   │3.3 │   ├─ GND   │
           │   └─┬─┘    │        │
           │     │      │        │
          GND   GND    TAB      GND

    Note: The tab on SOT-223 package is also connected to GND
    """

    # Voltage regulator IC - AMS1117-3.3
    # This is a low-dropout (LDO) linear regulator
    # "3.3" in the part number means fixed 3.3V output
    vreg = Component(
        symbol="Regulator_Linear:AMS1117-3.3",  # Fixed 3.3V version
        ref="U",  # Reference prefix for ICs (U1, U2, etc.)
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2",  # SOT-223 with tab
    )
    # Note: TabPin2 means the tab is connected to pin 2 (GND in this case)

    # Input decoupling capacitor - 10µF
    # Purpose: Stabilizes input voltage, prevents oscillation
    # Placement: As close as possible to VIN pin (<5mm recommended)
    cap_in = Component(
        symbol="Device:C",  # Generic capacitor symbol
        ref="C",  # Reference prefix for capacitors
        value="10uF",  # 10 microfarads
        footprint="Capacitor_SMD:C_0805_2012Metric",  # 0805 SMD (bigger for µF range)
    )
    # Note: Use 0805 or larger for µF capacitors (0603 typically maxes at 1µF)

    # Output decoupling capacitor - 22µF
    # Purpose: Reduces output ripple, improves load transient response
    # Placement: As close as possible to VOUT pin
    cap_out = Component(
        symbol="Device:C",
        ref="C",
        value="22uF",  # 22 microfarads (larger than input for better filtering)
        footprint="Capacitor_SMD:C_0805_2012Metric",
    )
    # Larger output cap helps when load current changes quickly (e.g., WiFi bursts)

    # Define power nets
    vin_5v = Net("VIN_5V")  # Input: 5V unregulated (can have ripple/noise)
    vout_3v3 = Net("VOUT_3V3")  # Output: 3.3V regulated (clean, stable)
    gnd = Net("GND")  # Ground plane (0V reference)

    # Connect voltage regulator
    # AMS1117 pinout (SOT-223):
    #   Pin 1: GND (also connected to tab)
    #   Pin 2: VOUT (3.3V output)
    #   Pin 3: VIN (5V input)
    vreg["GND"] += gnd  # Ground pin (and tab)
    vreg["VOUT"] += vout_3v3  # 3.3V regulated output
    vreg["VIN"] += vin_5v  # 5V input from source

    # Connect input capacitor
    # Placed between VIN and GND to filter input voltage
    cap_in[1] += vin_5v  # Positive terminal to VIN
    cap_in[2] += gnd  # Negative terminal to GND

    # Connect output capacitor
    # Placed between VOUT and GND to filter output voltage
    cap_out[1] += vout_3v3  # Positive terminal to VOUT
    cap_out[2] += gnd  # Negative terminal to GND

    # PCB Layout Tips:
    # 1. Keep capacitors within 5mm of regulator pins
    # 2. Use wide traces for VIN, VOUT, GND (>0.5mm for 1A)
    # 3. Use ground plane if possible
    # 4. Add thermal vias under SOT-223 tab for heat dissipation


if __name__ == "__main__":
    # This code runs when you execute: uv run python circuit-synth/main.py

    # Generate the circuit
    circuit_obj = voltage_regulator()

    # Export to KiCad project files
    circuit_obj.generate_kicad_project(
        project_name="voltage_regulator",
        placement_algorithm="hierarchical",
        generate_pcb=False,
    )

    print("Voltage regulator circuit generated!")
    print("Open in KiCad: voltage_regulator/voltage_regulator.kicad_pro")
    print()

    # Generate manufacturing files (BOM and PDF)
    print("Generating manufacturing files...")
    print()

    # Generate BOM for component ordering
    bom_result = circuit_obj.generate_bom(project_name="voltage_regulator")
    if bom_result["success"]:
        print(f"BOM generated: {bom_result['file']}")
        print(f"   Components: {bom_result['component_count']}")
    else:
        print(f"BOM generation failed: {bom_result.get('error')}")
    print()

    # Generate PDF schematic for documentation
    pdf_result = circuit_obj.generate_pdf_schematic(project_name="voltage_regulator")
    if pdf_result["success"]:
        print(f"PDF schematic generated: {pdf_result['file']}")
    else:
        print(f"PDF generation failed: {pdf_result.get('error')}")
    print()

    # NOTE: Gerber/PCB export is not available in this build (licensed feature
    # of upstream circuit-synth). Tracked as a wishlist item in TODO.md.
    print()

    print("Circuit Specifications:")
    print("   Input voltage:     5.0V (4.5-6.5V operating range)")
    print("   Output voltage:    3.3V (±2% regulation)")
    print("   Maximum current:   1.0A continuous")
    print("   Dropout voltage:   1.2V (min Vin-Vout)")
    print("   Efficiency:        ~66% (linear regulator)")
    print()
    print("Thermal Analysis (at 1A load):")
    print("   Power dissipated:  1.7W ((5V - 3.3V) × 1A)")
    print("   Junction temp rise: ~85°C (without heatsinking)")
    print("   Recommendation:    Add heatsink or limit current for continuous use")
    print()
    print("Important Notes:")
    print("   • Capacitors are REQUIRED - circuit won't work properly without them")
    print("   • Input voltage must be at least 4.5V (3.3V + 1.2V dropout)")
    print("   • For >500mA continuous, add thermal relief or heatsink")
    print("   • For switching loads (WiFi, motors), increase C_out to 47µF")
    print()
    print("Next Steps:")
    print("   1. Open the KiCad project")
    print("   2. Note the capacitor placement near the regulator")
    print("   3. Consider adding a power LED to indicate output")
    print(
        "   4. For battery projects, consider a buck converter instead (higher efficiency)"
    )
