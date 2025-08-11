from circuit_synth import *
from power_supply import power_supply
from mcu import mcu
from imu_1 import imu_1

@circuit(name="makeacircuitboardwithstm3_main")
def main():
    """make a circuit board with stm32 with 3 spi peripherals and 1 imu on each spi"""
    
    # Power nets
    vcc_5v = Net('VCC_5V')
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')
    
    # Instantiate subcircuits
    power_supply(vcc_5v, vcc_3v3, gnd)
    mcu(vcc_3v3, gnd)
    imu_1(vcc_3v3, gnd)

if __name__ == '__main__':
    circuit = main()
    circuit.generate_kicad_project("makeacircuitboardwithstm3")
    print("✅ KiCad project generated successfully!")
