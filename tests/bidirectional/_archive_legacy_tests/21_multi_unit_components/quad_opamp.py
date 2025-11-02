#!/usr/bin/env python3
"""
Fixture: Quad op-amp circuit with all 4 units connected.

Multi-unit component (TL074 quad op-amp) with 4 operational amplifier units,
each with independent pin connections.

Used for testing multi-unit component preservation during regeneration.
"""

from circuit_synth import circuit, Component, Net


@circuit(name="quad_opamp")
def quad_opamp():
    """Circuit with quad op-amp (TL074) using all 4 units.

    TL074 is a quad op-amp with:
    - Unit A: pins 1 (out), 2 (inv), 3 (non-inv)
    - Unit B: pins 7 (out), 6 (inv), 5 (non-inv)
    - Unit C: pins 8 (out), 9 (inv), 10 (non-inv)
    - Unit D: pins 14 (out), 13 (inv), 12 (non-inv)
    - Pins 4 and 11: power (V- and V+)
    """
    # Create quad op-amp component
    u1 = Component(
        symbol="Amplifier_Operational:TL074",
        ref="U1",
        value="TL074",
        footprint="Package_DIP:DIP-14_W7.62mm",
    )

    # Input signals for each unit
    input_a_pos = Component(
        symbol="Connector:Conn_01x01_Pin",
        ref="J1",
        value="INPUT_A",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x01_P2.54mm_Vertical",
    )

    input_b_pos = Component(
        symbol="Connector:Conn_01x01_Pin",
        ref="J2",
        value="INPUT_B",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x01_P2.54mm_Vertical",
    )

    input_c_pos = Component(
        symbol="Connector:Conn_01x01_Pin",
        ref="J3",
        value="INPUT_C",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x01_P2.54mm_Vertical",
    )

    input_d_pos = Component(
        symbol="Connector:Conn_01x01_Pin",
        ref="J4",
        value="INPUT_D",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x01_P2.54mm_Vertical",
    )

    # Output connectors for each unit
    output_a = Component(
        symbol="Connector:Conn_01x01_Pin",
        ref="J5",
        value="OUTPUT_A",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x01_P2.54mm_Vertical",
    )

    output_b = Component(
        symbol="Connector:Conn_01x01_Pin",
        ref="J6",
        value="OUTPUT_B",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x01_P2.54mm_Vertical",
    )

    output_c = Component(
        symbol="Connector:Conn_01x01_Pin",
        ref="J7",
        value="OUTPUT_C",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x01_P2.54mm_Vertical",
    )

    output_d = Component(
        symbol="Connector:Conn_01x01_Pin",
        ref="J8",
        value="OUTPUT_D",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x01_P2.54mm_Vertical",
    )

    # Power supply
    vcc = Component(
        symbol="Connector:Conn_01x01_Pin",
        ref="J9",
        value="VCC",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x01_P2.54mm_Vertical",
    )

    gnd = Component(
        symbol="Connector:Conn_01x01_Pin",
        ref="J10",
        value="GND",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x01_P2.54mm_Vertical",
    )

    # Create nets for each unit
    # Unit A: input -> non-inverting input (pin 3)
    net_in_a = Net("IN_A")
    net_in_a += input_a_pos[1]
    net_in_a += u1[3]  # TL074 unit A non-inverting input

    # Unit A: output (pin 1)
    net_out_a = Net("OUT_A")
    net_out_a += u1[1]  # TL074 unit A output
    net_out_a += output_a[1]

    # Unit A: feedback (inverting to ground for buffer configuration)
    net_fb_a = Net("GND_A")
    net_fb_a += u1[2]  # TL074 unit A inverting input
    net_fb_a += gnd[1]

    # Unit B: input -> non-inverting input (pin 5)
    net_in_b = Net("IN_B")
    net_in_b += input_b_pos[1]
    net_in_b += u1[5]  # TL074 unit B non-inverting input

    # Unit B: output (pin 7)
    net_out_b = Net("OUT_B")
    net_out_b += u1[7]  # TL074 unit B output
    net_out_b += output_b[1]

    # Unit B: feedback (inverting to ground)
    net_fb_b = Net("GND_B")
    net_fb_b += u1[6]  # TL074 unit B inverting input
    net_fb_b += gnd[1]

    # Unit C: input -> non-inverting input (pin 10)
    net_in_c = Net("IN_C")
    net_in_c += input_c_pos[1]
    net_in_c += u1[10]  # TL074 unit C non-inverting input

    # Unit C: output (pin 8)
    net_out_c = Net("OUT_C")
    net_out_c += u1[8]  # TL074 unit C output
    net_out_c += output_c[1]

    # Unit C: feedback (inverting to ground)
    net_fb_c = Net("GND_C")
    net_fb_c += u1[9]  # TL074 unit C inverting input
    net_fb_c += gnd[1]

    # Unit D: input -> non-inverting input (pin 12)
    net_in_d = Net("IN_D")
    net_in_d += input_d_pos[1]
    net_in_d += u1[12]  # TL074 unit D non-inverting input

    # Unit D: output (pin 14)
    net_out_d = Net("OUT_D")
    net_out_d += u1[14]  # TL074 unit D output
    net_out_d += output_d[1]

    # Unit D: feedback (inverting to ground)
    net_fb_d = Net("GND_D")
    net_fb_d += u1[13]  # TL074 unit D inverting input
    net_fb_d += gnd[1]

    # Power connections (shared across all units)
    net_vcc = Net("VCC")
    net_vcc += u1[11]  # TL074 V+ (pin 11)
    net_vcc += vcc[1]

    net_gnd = Net("GND")
    net_gnd += u1[4]  # TL074 V- (pin 4)
    net_gnd += gnd[1]


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = quad_opamp()

    circuit_obj.generate_kicad_project(
        project_name="quad_opamp",
        placement_algorithm="simple",
        generate_pcb=True,
    )

    print("✅ Quad op-amp circuit generated successfully!")
    print("📁 Open in KiCad: quad_opamp/quad_opamp.kicad_pro")
    print("📋 Components: TL074 quad op-amp with 4 units (U1A, U1B, U1C, U1D)")
    print("🔌 Each unit has independent connections to input/output connectors")
