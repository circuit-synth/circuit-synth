from circuit_synth import *
from power_supply import power_supply
from mcu import mcu_circuit
from imu_1 import imu_1
from motor_driver import motor_driver_circuit
from leds import led_circuit
from audio import audio_circuit

@circuit(name="bb8droidcontroller_main")
def main():
    """BB-8 droid controller"""
    
    # Power nets
    vcc_5v = Net('VCC_5V')
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')
    
    # Instantiate subcircuits
    power_supply(vcc_5v, vcc_3v3, gnd)
    mcu_circuit(vcc_3v3, gnd)
    imu_1(vcc_3v3, gnd)
    motor_driver_circuit(vcc_3v3, gnd)
    led_circuit(vcc_3v3, gnd)
    audio_circuit(vcc_3v3, gnd)

if __name__ == '__main__':
    circuit = main()
    circuit.generate_kicad_project("bb8droidcontroller")
    print("✅ KiCad project generated successfully!")
