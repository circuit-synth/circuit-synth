from circuit_synth import *

@circuit(name="power_supply")
def power_supply(vcc_5v, vcc_3v3, gnd):
    """3.3V power supply from 5V input"""
    
    # Voltage regulator
    regulator = Component(
        symbol="Regulator_Linear:NCP1117-3.3_SOT223",
        ref="U1",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )
    
    # Input capacitor
    cap_in = Component(
        symbol="Device:C",
        ref="C1", 
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    
    # Output capacitor
    cap_out = Component(
        symbol="Device:C",
        ref="C2",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    
    # Connections
    regulator[1] += gnd        # GND
    regulator[2] += vcc_3v3    # VOUT 
    regulator[3] += vcc_5v     # VIN
    
    cap_in[1] += vcc_5v
    cap_in[2] += gnd
    
    cap_out[1] += vcc_3v3
    cap_out[2] += gnd
