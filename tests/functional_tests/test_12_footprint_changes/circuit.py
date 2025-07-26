#!/usr/bin/env python3
"""
Circuit with Small Footprints for Test Case 12
Uses 0402 components that will be changed to larger sizes in KiCad
"""

from circuit_synth import Component, Net, circuit

@circuit
def footprint_changes():
    """Create circuit with small SMD components"""
    
    # Create nets
    vcc = Net("VCC")
    gnd = Net("GND")
    signal = Net("SIGNAL")
    filtered = Net("FILTERED")
    
    # Small 0402 resistors (will change to 0603)
    r1 = Component(
        "Device:R",
        ref="R1",
        value="1k",
        footprint="Resistor_SMD:R_0402_1005Metric"
    )
    r2 = Component(
        "Device:R",
        ref="R2",
        value="10k",
        footprint="Resistor_SMD:R_0402_1005Metric"
    )
    r3 = Component(
        "Device:R",
        ref="R3",
        value="100k",
        footprint="Resistor_SMD:R_0402_1005Metric"
    )
    
    # Small capacitors (will change to 0805 for voltage rating)
    c1 = Component(
        "Device:C",
        ref="C1",
        value="100nF",
        footprint="Capacitor_SMD:C_0402_1005Metric"
    )
    c2 = Component(
        "Device:C",
        ref="C2",
        value="1uF",
        footprint="Capacitor_SMD:C_0402_1005Metric"
    )
    
    # THT LED (will change to SMD)
    led1 = Component(
        "Device:LED",
        ref="D1",
        value="RED",
        footprint="LED_THT:LED_D3.0mm"
    )
    
    # THT connector (will change to SMD)
    j1 = Component(
        "Connector:Conn_01x04_Pin",
        ref="J1",
        value="CONN",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical"
    )
    
    # Op-amp with fine pitch (will change to wider pitch)
    u1 = Component(
        "Amplifier_Operational:LM358",
        ref="U1",
        value="LM358",
        footprint="Package_SO:MSOP-8_3x3mm_P0.65mm"
    )
    
    # Build the circuit
    # Voltage divider
    r1["1"] += vcc
    r1["2"] += signal
    r2["1"] += signal
    r2["2"] += gnd
    
    # Filter
    r3["1"] += signal
    r3["2"] += filtered
    c1["1"] += filtered
    c1["2"] += gnd
    
    # Power bypass
    c2["1"] += vcc
    c2["2"] += gnd
    
    # LED indicator
    led1["1"] += r1["2"]  # Anode to signal
    led1["2"] += gnd      # Cathode to ground
    
    # Op-amp buffer
    u1["3"] += filtered   # Non-inverting input
    u1["2"] += u1["1"]    # Voltage follower
    u1["8"] += vcc        # Power
    u1["4"] += gnd        # Ground
    
    # Connector
    j1["1"] += vcc
    j1["2"] += signal
    j1["3"] += u1["1"]    # Buffered output
    j1["4"] += gnd

if __name__ == "__main__":
    print("Circuit with small footprints generated!")
    print("\nComponents to change in KiCad:")
    print("- R1, R2, R3: 0402 → 0603 (easier hand assembly)")
    print("- C1, C2: 0402 → 0805 (higher voltage rating)")
    print("- D1: THT LED → SMD LED_0603")
    print("- J1: THT header → SMD header")
    print("- U1: MSOP-8 → SOIC-8 (wider pitch)")