from circuit_synth import *
from power_supply import power_supply

@circuit(name="simpleledblinkercircuit_main")
def main():
    """Simple LED blinker circuit"""
    
    # Power nets
    vcc_5v = Net('VCC_5V')
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')
    
    # Instantiate subcircuits
    power_supply(vcc_5v, vcc_3v3, gnd)

if __name__ == '__main__':
    circuit = main()
    circuit.generate_kicad_project("simpleledblinkercircuit")
    print("✅ KiCad project generated successfully!")
