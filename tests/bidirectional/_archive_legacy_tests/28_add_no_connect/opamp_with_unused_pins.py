#!/usr/bin/env python3
"""
Fixture: Op-amp circuit with unused pins.

A basic operational amplifier circuit where some pins are not used.
This simulates a common scenario where an IC has more pins than needed,
and no-connect flags should be applied to unused pins to satisfy ERC checks.

Used for testing no-connect symbol generation and preservation.
"""

from circuit_synth import circuit, Component, Net


@circuit(name="opamp_with_unused_pins")
def opamp_with_unused_pins():
    """Circuit with general-purpose op-amp (LM358) with some unused pins.

    LM358 is a dual op-amp with:
    - Unit A: pins 1 (out), 2 (inv), 3 (non-inv)
    - Unit B: pins 7 (out), 6 (inv), 5 (non-inv)
    - Pins 4 (V-) and 8 (V+): power supplies

    In this circuit:
    - Unit A is configured as a buffer/follower
    - Unit B is left unused (all pins unconnected)
    - Goal: Mark Unit B pins as no-connect to prevent ERC errors
    """

    # Create dual op-amp component
    u1 = Component(
        symbol="Amplifier_Operational:LM358",
        ref="U1",
        value="LM358",
        footprint="Package_DIP:DIP-8_W7.62mm",
    )

    # Input signal for Unit A
    input_signal = Component(
        symbol="Connector:Conn_01x01_Pin",
        ref="J1",
        value="INPUT",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x01_P2.54mm_Vertical",
    )

    # Output for Unit A
    output_signal = Component(
        symbol="Connector:Conn_01x01_Pin",
        ref="J2",
        value="OUTPUT",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x01_P2.54mm_Vertical",
    )

    # Power supply decoupling
    vcc = Component(
        symbol="Connector:Conn_01x01_Pin",
        ref="J3",
        value="VCC_POS",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x01_P2.54mm_Vertical",
    )

    vee = Component(
        symbol="Connector:Conn_01x01_Pin",
        ref="J4",
        value="VCC_NEG",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x01_P2.54mm_Vertical",
    )

    # Unit A buffer configuration:
    # Non-inverting input (pin 3) connected to input signal
    net_in_a = Net("INPUT_A")
    net_in_a += input_signal[1]
    net_in_a += u1[3]

    # Unit A output (pin 1) connected to output connector
    # AND fed back to inverting input (pin 2) for unity gain buffer
    net_out_a = Net("OUTPUT_A")
    net_out_a += u1[1]
    net_out_a += output_signal[1]
    net_out_a += u1[2]  # Feedback for unity gain buffer

    # Power connections
    net_vcc = Net("VCC")
    net_vcc += u1[8]  # Pin 8: V+
    net_vcc += vcc[1]

    net_vee = Net("VEE")
    net_vee += u1[4]  # Pin 4: V-
    net_vee += vee[1]

    # NOTE: Unit B pins (5, 6, 7) are left unconnected
    # These should be marked as NO_CONNECT when the test modifies the fixture


if __name__ == "__main__":
    # Generate KiCad project when run directly
    circuit_obj = opamp_with_unused_pins()

    circuit_obj.generate_kicad_project(
        project_name="opamp_with_unused_pins",
        placement_algorithm="simple",
        generate_pcb=True,
    )

    print("✅ Op-amp circuit with unused pins generated successfully!")
    print("📁 Open in KiCad: opamp_with_unused_pins/opamp_with_unused_pins.kicad_pro")
    print("📋 Components: LM358 dual op-amp (Unit A used, Unit B unused)")
    print("🔌 Unit A configured as unity-gain buffer")
    print("⚠️  Unit B pins (5, 6, 7) are intentionally left unconnected")
    print("   They should be marked as NO_CONNECT to satisfy ERC checks")
