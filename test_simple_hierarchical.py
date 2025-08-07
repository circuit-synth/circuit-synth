#!/usr/bin/env python3
"""
Simple hierarchical circuit test with Rust backend
"""

from circuit_synth import *
from pathlib import Path
import shutil

@circuit(name="PowerSupply")
def power_supply(gnd, vin, vout):
    """Simple power supply subcircuit"""
    r1 = Component(symbol="Device:R", ref="R1", value="10k")
    r2 = Component(symbol="Device:R", ref="R2", value="20k")
    c1 = Component(symbol="Device:C", ref="C1", value="100nF")
    
    # Voltage divider
    r1[1] += vin
    r1[2] += vout
    r2[1] += vout
    r2[2] += gnd
    
    # Bypass cap
    c1[1] += vout
    c1[2] += gnd

@circuit(name="LED_Circuit")
def led_circuit(gnd, power):
    """Simple LED subcircuit"""
    led_net = Net("LED_NET")
    
    d1 = Component(symbol="Device:LED", ref="D1")
    r3 = Component(symbol="Device:R", ref="R3", value="330")
    
    d1[1] += gnd
    d1[2] += led_net
    r3[1] += power
    r3[2] += led_net

@circuit(name="Main")
def main_circuit():
    """Main circuit with two subcircuits"""
    gnd = Net("GND")
    vin = Net("VIN")
    vout = Net("VOUT")
    
    # Instantiate subcircuits
    power = power_supply(gnd, vin, vout)
    led = led_circuit(gnd, vout)

if __name__ == "__main__":
    # Clean previous output
    if Path("test_hierarchical").exists():
        shutil.rmtree("test_hierarchical")
    
    circuit = main_circuit()
    circuit.generate_kicad_project(project_name="test_hierarchical")
    print("\n✅ Hierarchical circuit generation complete!")
    print("Generated files in test_hierarchical/")