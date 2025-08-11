from circuit_synth import *

@circuit(name="LED_Blinker")
def main():
    '''Simple LED blinker circuit with a 330 ohm resistor.'''
    
    # Power nets
    vcc_3v3 = Net('VCC_3V3') 
    gnd = Net('GND')
    
    # Components
    # Microcontroller (e.g., ESP32 for simplicity, though any MCU could be used)
    # Using ESP32-S3-MINI-1 as an example, assuming we'll use a GPIO pin for the LED
    mcu = Component(
        symbol="RF_Module:ESP32-S3-MINI-1",
        ref="U1", 
        footprint="RF_Module:ESP32-S2-MINI-1" # Footprint for S3-MINI-1 is similar to S2-MINI-1
    )
    
    # Decoupling capacitors for MCU
    cap_mcu_10u = Component(
        symbol="Device:C",
        ref="C1", 
        footprint="Capacitor_SMD:C_0603_1608Metric" # Or larger if needed for 10uF
    )
    cap_mcu_100n = Component(
        symbol="Device:C",
        ref="C2", 
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )

    # LED
    led = Component(
        symbol="Device:LED",
        ref="D1", 
        footprint="LED_SMD:LED_0603_1608Metric"
    )
    
    # Current limiting resistor for LED
    resistor_led = Component(
        symbol="Device:R",
        ref="R1", 
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Pin connections
    # MCU Power and Ground (using actual ESP32-S3-MINI-1 numeric pin numbers)
    mcu[3] += vcc_3v3  # Pin 3 = 3.3V power
    mcu[1] += gnd      # Pin 1 = Ground

    # Decoupling caps for MCU
    cap_mcu_10u[1] += vcc_3v3
    cap_mcu_10u[2] += gnd
    cap_mcu_100n[1] += vcc_3v3
    cap_mcu_100n[2] += gnd

    # LED connection
    # Using GPIO IO2 (pin number from example: pin 10 for IO2 is common)
    # Connect MCU GPIO to resistor
    mcu[10] += resistor_led[1] # GPIO pin connected to resistor

    # Connect resistor to LED anode
    resistor_led[2] += led[1] # Pin 2 of resistor connected to LED Anode

    # Connect LED cathode to ground
    led[2] += gnd # Pin 2 of LED (cathode) connected to GND

if __name__ == '__main__':
    circuit = main()
    circuit.generate_kicad_project("LED_Blinker", force_regenerate=True)