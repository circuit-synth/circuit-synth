#!/usr/bin/env python3
"""
CIRCUIT: Basic 3.3V LDO Regulator
PURPOSE: Convert 5V input to stable 3.3V output with 1A capacity
COMPONENTS: NCP1117 LDO + input/output capacitors
COMPLEXITY: Beginner
DOMAIN: Power Management
"""

from circuit_synth import Circuit, Component, Net, circuit


@circuit
def basic_ldo_3v3():
    """
    3.3V LDO regulator with proper decoupling.

    Design Notes:
    - NCP1117 can handle 1A output current
    - 10µF input cap reduces input ripple
    - 22µF output cap improves transient response
    - SOT-223 package provides good thermal dissipation

    Power Dissipation: P = (VIN - VOUT) × IOUT = (5V - 3.3V) × 1A = 1.7W
    Thermal Rise: 1.7W × 2°C/W = 3.4°C above ambient
    """
    # Create power nets with descriptive names
    vin_5v = Net("VIN_5V")  # 5V input from USB or external supply
    vout_3v3 = Net("VOUT_3V3")  # Regulated 3.3V output
    gnd = Net("GND")  # Common ground reference

    # Main regulator - NCP1117 in SOT-223 package
    # Pin 1: GND, Pin 2: VOUT, Pin 3: VIN (per datasheet)
    regulator = Component(
        symbol="Regulator_Linear:NCP1117-3.3_SOT223",
        ref="U1",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2",
    )

    # Input decoupling capacitor - 10µF ceramic
    # Placed close to VIN pin to reduce input voltage ripple
    cap_input = Component(
        symbol="Device:C",
        ref="C1",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric",
    )

    # Output decoupling capacitor - 22µF ceramic
    # Larger value improves transient response and load regulation
    cap_output = Component(
        symbol="Device:C",
        ref="C2",
        value="22uF",
        footprint="Capacitor_SMD:C_0805_2012Metric",
    )

    # Regulator pin connections (using integer pin access)
    regulator[1] += gnd  # Pin 1: GND terminal
    regulator[2] += vout_3v3  # Pin 2: VOUT (regulated 3.3V)
    regulator[3] += vin_5v  # Pin 3: VIN (unregulated 5V input)

    # Input capacitor connections
    cap_input[1] += vin_5v  # Positive terminal to input voltage
    cap_input[2] += gnd  # Negative terminal to ground

    # Output capacitor connections
    cap_output[1] += vout_3v3  # Positive terminal to output voltage
    cap_output[2] += gnd  # Negative terminal to ground
