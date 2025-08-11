from circuit_synth import *

@circuit(name="simple_led_blinker")
def main():
    '''A simple LED blinker circuit using an ESP32-S3-MINI-1.'''
    
    # Power nets
    vcc_5v = Net('VCC_5V')
    vcc_3v3 = Net('VCC_3V3') 
    gnd = Net('GND')
    
    # --- Power Supply Section ---
    
    # USB-C Connector for 5V input
    usb_c_conn = Component(
        symbol="Connector:USB_C_Plug_USB2.0",
        ref="J1", 
        footprint="Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal"
    )
    usb_c_conn[A9] += vcc_5v  # VBUS
    usb_c_conn[A12] += vcc_5v # VBUS
    usb_c_conn[B9] += vcc_5v  # VBUS
    usb_c_conn[B12] += vcc_5v # VBUS
    usb_c_conn[A1] += gnd     # GND
    usb_c_conn[A4] += gnd     # GND
    usb_c_conn[A5] += gnd     # GND
    usb_c_conn[A8] += gnd     # GND
    usb_c_conn[B1] += gnd     # GND
    usb_c_conn[B4] += gnd     # GND
    usb_c_conn[B5] += gnd     # GND
    usb_c_conn[B8] += gnd     # GND

    # 5V to 3.3V Linear Regulator
    regulator_3v3 = Component(
        symbol="Regulator_Linear:NCP1117-3.3_SOT223",
        ref="U1", 
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )
    regulator_3v3[1] += gnd      # GND
    regulator_3v3[2] += vcc_3v3  # VOUT
    regulator_3v3[3] += vcc_5v   # VIN

    # Decoupling capacitors for 3.3V regulator input
    cap_reg_in_10u = Component(
        symbol="Device:C",
        ref="C1",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    cap_reg_in_10u[1] += vcc_5v
    cap_reg_in_10u[2] += gnd

    cap_reg_in_100n = Component(
        symbol="Device:C",
        ref="C2",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    cap_reg_in_100n[1] += vcc_5v
    cap_reg_in_100n[2] += gnd

    # Decoupling capacitors for 3.3V regulator output
    cap_reg_out_10u = Component(
        symbol="Device:C",
        ref="C3",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    cap_reg_out_10u[1] += vcc_3v3
    cap_reg_out_10u[2] += gnd

    cap_reg_out_100n = Component(
        symbol="Device:C",
        ref="C4",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    cap_reg_out_100n[1] += vcc_3v3
    cap_reg_out_100n[2] += gnd

    # --- ESP32 Section ---

    esp32 = Component(
        symbol="RF_Module:ESP32-S3-MINI-1",
        ref="U2", 
        footprint="RF_Module:ESP32-S2-MINI-1"
    )
    
    # ESP32 Power Connections
    esp32[1] += gnd     # GND
    esp32[3] += vcc_3v3 # 3V3
    
    # Decoupling capacitors for ESP32
    cap_esp32_10u = Component(
        symbol="Device:C",
        ref="C5",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    cap_esp32_10u[1] += vcc_3v3
    cap_esp32_10u[2] += gnd

    cap_esp32_100n = Component(
        symbol="Device:C",
        ref="C6",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    cap_esp32_100n[1] += vcc_3v3
    cap_esp32_100n[2] += gnd

    # --- LED Blinker Section ---

    # LED
    blinker_led = Component(
        symbol="Device:LED",
        ref="D1", 
        footprint="LED_SMD:LED_0603_1608Metric"
    )
    
    # Current limiting resistor for LED (330 Ohm for 3.3V)
    led_resistor = Component(
        symbol="Device:R",
        ref="R1", 
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Connect ESP32 GPIO to LED
    # Using GPIO10 (Pin 10 on ESP32-S3-MINI-1)
    esp32[10] += led_resistor[1]  # ESP32 GPIO to resistor
    led_resistor[2] += blinker_led[A] # Resistor to LED Anode
    blinker_led[K] += gnd         # LED Cathode to GND

if __name__ == '__main__':
    circuit = main()
    circuit.generate_kicad_project("simple_led_blinker", force_regenerate=True)