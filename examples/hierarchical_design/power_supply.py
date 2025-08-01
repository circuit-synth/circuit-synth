#!/usr/bin/env python3
"""
3.3V Linear Regulator Circuit

A simple but complete 3.3V regulator circuit with proper decoupling.
This demonstrates the single-circuit-per-file approach with clear documentation.
"""

from circuit_synth import Circuit, Component, Net, circuit
from .components import C_10uF


@circuit(name="ldo_3v3_regulator")
def ldo_3v3_regulator(vin, vout, gnd):
    """
    Linear 3.3V regulator with input/output capacitors.
    
    Features:
    - AMS1117-3.3 regulator (1A max current)
    - 10µF input and output capacitors for stability
    - Proper thermal relief via SOT-223 package
    
    Args:
        vin: Input voltage net (5V typical)
        vout: Regulated 3.3V output net
        gnd: Ground net
    """
    
    # Main regulator component
    regulator = Component(
        symbol="Regulator_Linear:AMS1117-3.3",
        ref="U",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )
    
    # Input decoupling capacitor
    cap_in = C_10uF()
    cap_in.ref = "C"  # Let circuit-synth auto-number
    
    # Output decoupling capacitor  
    cap_out = C_10uF()
    cap_out.ref = "C"  # Let circuit-synth auto-number
    
    # Connect regulator pins
    regulator["VI"] += vin      # Input voltage
    regulator["VO"] += vout     # Output voltage
    regulator["GND"] += gnd     # Ground
    
    # Connect input capacitor
    cap_in[1] += vin
    cap_in[2] += gnd
    
    # Connect output capacitor
    cap_out[1] += vout
    cap_out[2] += gnd


if __name__ == "__main__":
    """
    Test the power supply circuit independently.
    """
    # Create test nets
    VIN_5V = Net('VIN_5V')
    VCC_3V3 = Net('VCC_3V3') 
    GND = Net('GND')
    
    # Create the circuit
    circuit = ldo_3v3_regulator(VIN_5V, VCC_3V3, GND)
    
    # Generate output files
    circuit.generate_kicad_project("ldo_3v3_regulator_test")
    print("✅ Power supply circuit generated successfully!")