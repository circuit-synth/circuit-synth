#!/usr/bin/env python3
"""
Resistor Divider Circuit - Voltage scaling and sensing
Divides input voltage proportionally for ADC inputs, voltage sensing, or reference generation
"""

from circuit_synth import *

@circuit(name="Resistor_Divider")
def resistor_divider(vin, vout, gnd, ratio="2:1"):
    """
    Resistor divider for voltage scaling

    Common use cases:
    - ADC input scaling (measure higher voltages with lower voltage ADC)
    - Voltage sensing/monitoring
    - Reference voltage generation
    - Bias networks

    Args:
        vin: Input voltage net
        vout: Output voltage net (divided voltage)
        gnd: Ground reference
        ratio: Division ratio as string (e.g., "2:1", "3:1", "10:1")
               Output voltage = Vin * (R2/(R1+R2))

    Examples:
        - ratio="2:1" -> Vout = Vin/2 (e.g., 12V -> 6V)
        - ratio="3:1" -> Vout = Vin/3 (e.g., 12V -> 4V)
        - ratio="10:1" -> Vout = Vin/10 (e.g., 12V -> 1.2V for ADC)
    """

    # Parse ratio (e.g., "10:1" means Vout = Vin/10)
    if ":" in ratio:
        r1_mult, r2_mult = ratio.split(":")
        r1_mult = int(r1_mult)
        r2_mult = int(r2_mult)
    else:
        raise ValueError("Ratio must be in format 'R1:R2' (e.g., '10:1')")

    # Standard resistor values for divider
    # Using 10k as base (good balance between current draw and noise immunity)
    base_r2 = 10000  # 10k ohms
    r2_value = base_r2
    r1_value = base_r2 * (r1_mult / r2_mult - 1)

    # Round to nearest standard value
    if r1_value < 1000:
        r1_str = f"{int(r1_value)}"
    else:
        r1_str = f"{int(r1_value/1000)}k"

    if r2_value < 1000:
        r2_str = f"{int(r2_value)}"
    else:
        r2_str = f"{int(r2_value/1000)}k"

    # Top resistor (R1) - from Vin to Vout
    r1 = Component(
        symbol="Device:R",
        ref="R",
        value=r1_str,
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # Bottom resistor (R2) - from Vout to GND
    r2 = Component(
        symbol="Device:R",
        ref="R",
        value=r2_str,
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    # Connections
    r1[1] += vin      # R1 top to input voltage
    r1[2] += vout     # R1 bottom to output (middle point)
    r2[1] += vout     # R2 top to output (middle point)
    r2[2] += gnd      # R2 bottom to ground


# Example usage for ADC voltage sensing
@circuit(name="ADC_Voltage_Sense_12V")
def adc_voltage_sense_example(vbat_12v, adc_input, gnd):
    """
    Example: Sense 12V battery voltage with 3.3V ADC
    Divides 12V down to 1.2V for safe ADC reading
    """
    resistor_divider(vbat_12v, adc_input, gnd, ratio="10:1")


# Example usage for voltage reference
@circuit(name="Voltage_Reference_Half_VCC")
def voltage_reference_example(vcc_3v3, vref_out, gnd):
    """
    Example: Create 1.65V reference from 3.3V supply
    Useful for biasing analog circuits to mid-rail
    """
    resistor_divider(vcc_3v3, vref_out, gnd, ratio="2:1")
