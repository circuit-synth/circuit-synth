#!/usr/bin/env python3
"""
Circuit with Non-Sequential Reference Designators for Test Case 14
Intentionally messy numbering to test renumbering in KiCad
"""

from circuit_synth import Component, Net, circuit

@circuit
def refdes_reorg():
    """Create circuit with randomly ordered reference designators"""
    
    # Create nets
    vcc = Net("VCC")
    gnd = Net("GND")
    sig1 = Net("SIG1")
    sig2 = Net("SIG2")
    sig3 = Net("SIG3")
    
    # Resistors with non-sequential numbering
    r7 = Component(
        "Device:R",
        ref="R7",
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    r2 = Component(
        "Device:R",
        ref="R2",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    r15 = Component(
        "Device:R",
        ref="R15",
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    r1 = Component(
        "Device:R",
        ref="R1",
        value="100k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Capacitors with gaps in numbering
    c3 = Component(
        "Device:C",
        ref="C3",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    c8 = Component(
        "Device:C",
        ref="C8",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    c1 = Component(
        "Device:C",
        ref="C1",
        value="1uF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    # ICs with random numbering
    u5 = Component(
        "Amplifier_Operational:LM358",
        ref="U5",
        value="LM358",
        footprint="Package_SO:SOIC-8_3.9x4.9mm_P1.27mm"
    )
    u2 = Component(
        "74xx:74HC00",
        ref="U2",
        value="74HC00",
        footprint="Package_SO:SOIC-14_3.9x8.7mm_P1.27mm"
    )
    
    # Diodes out of order
    d3 = Component(
        "Device:LED",
        ref="D3",
        value="RED",
        footprint="LED_SMD:LED_0603_1608Metric"
    )
    d1 = Component(
        "Device:D",
        ref="D1",
        value="1N4148",
        footprint="Diode_SMD:D_SOD-123"
    )
    
    # Connectors with gaps
    j4 = Component(
        "Connector:Conn_01x03_Pin",
        ref="J4",
        value="PWR",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x03_P2.54mm_Vertical"
    )
    j1 = Component(
        "Connector:Conn_01x02_Pin",
        ref="J1",
        value="IN",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical"
    )
    
    # Build the circuit connections
    # Power connections
    j4["1"] += vcc
    j4["2"] += gnd
    j4["3"] += gnd  # Extra ground
    
    # Input circuit
    j1["1"] += r7["1"]
    j1["2"] += gnd
    r7["2"] += sig1
    r2["1"] += sig1
    r2["2"] += gnd
    
    # Filter
    r15["1"] += sig1
    r15["2"] += sig2
    c3["1"] += sig2
    c3["2"] += gnd
    
    # Op-amp circuit
    u5["3"] += sig2      # Non-inverting
    u5["2"] += sig3      # Inverting
    u5["1"] += sig3      # Output
    u5["8"] += vcc       # Power
    u5["4"] += gnd       # Ground
    
    # Digital logic
    u2["1"] += sig3      # Input A1
    u2["2"] += gnd       # Input B1
    u2["3"] += u2["4"]   # Output Y1 to Input A2
    u2["14"] += vcc      # Power
    u2["7"] += gnd       # Ground
    
    # Output indicators
    r1["1"] += u2["3"]
    r1["2"] += d3["1"]   # LED anode
    d3["2"] += gnd       # LED cathode
    
    # Protection diode
    d1["1"] += sig1      # Anode
    d1["2"] += vcc       # Cathode (clamp to VCC)
    
    # Bypass capacitors
    c8["1"] += vcc
    c8["2"] += gnd
    c1["1"] += vcc
    c1["2"] += gnd

if __name__ == "__main__":
    print("Circuit with non-sequential reference designators generated!")
    print("\nCurrent messy numbering:")
    print("- Resistors: R7, R2, R15, R1")
    print("- Capacitors: C3, C8, C1")
    print("- ICs: U5, U2")
    print("- Diodes: D3, D1")
    print("- Connectors: J4, J1")
    print("\nThese should be renumbered sequentially in KiCad!")