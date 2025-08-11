from circuit_synth import *

@circuit(name="esp32_iot_controller")
def main():
    '''Simple ESP32-based IoT controller with USB-C power and basic decoupling.'''

    # Power nets
    vcc_5v = Net('VCC_5V')
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')

    # --- Power Input (USB-C) ---
    usb_c_conn = Component(
        symbol="Connector:USB_C_Receptacle_USB2.0",
        ref="J1",
        footprint="Connector_USB:USB_C_Receptacle_USB2.0_16P_TopMount_Horizontal"
    )
    usb_c_conn['VBUS'] += vcc_5v
    usb_c_conn['GND'] += gnd
    usb_c_conn['CC1'] += gnd  # Required for USB-C DFP
    usb_c_conn['CC2'] += gnd  # Required for USB-C DFP
    # Data lines not connected for power-only
    usb_c_conn['D+1'] += Net('USB_DP')
    usb_c_conn['D-1'] += Net('USB_DM')
    usb_c_conn['D+2'] += Net('USB_DP')
    usb_c_conn['D-2'] += Net('USB_DM')

    # --- 5V to 3.3V Regulator ---
    regulator_3v3 = Component(
        symbol="Regulator_Linear:AMS1117-3.3",
        ref="U1",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )
    regulator_3v3['VIN'] += vcc_5v
    regulator_3v3['GND'] += gnd
    regulator_3v3['VOUT'] += vcc_3v3

    # Decoupling for 5V input to regulator
    cap_in_10uF = Component(symbol="Device:C", ref="C1", footprint="Capacitor_SMD:C_0603_1608Metric")
    cap_in_10uF[1] += vcc_5v
    cap_in_10uF[2] += gnd

    cap_in_100nF = Component(symbol="Device:C", ref="C2", footprint="Capacitor_SMD:C_0603_1608Metric")
    cap_in_100nF[1] += vcc_5v
    cap_in_100nF[2] += gnd

    # Decoupling for 3.3V output from regulator
    cap_out_10uF = Component(symbol="Device:C", ref="C3", footprint="Capacitor_SMD:C_0603_1608Metric")
    cap_out_10uF[1] += vcc_3v3
    cap_out_10uF[2] += gnd

    cap_out_100nF = Component(symbol="Device:C", ref="C4", footprint="Capacitor_SMD:C_0603_1608Metric")
    cap_out_100nF[1] += vcc_3v3
    cap_out_100nF[2] += gnd

    # --- ESP32 Module ---
    esp32 = Component(
        symbol="RF_Module:ESP32-S3-MINI-1", # Using S3-MINI-1 as a placeholder for a generic ESP32 module
        ref="U2",
        footprint="RF_Module:ESP32-S2-MINI-1" # Footprint for S2-MINI-1, assuming similar form factor for S3-MINI-1
    )

    # ESP32 Power Connections (referencing common ESP32 module pinouts)
    esp32['VCC'] += vcc_3v3
    esp32['GND'] += gnd

    # Decoupling for ESP32 VCC
    esp32_cap_10uF = Component(symbol="Device:C", ref="C5", footprint="Capacitor_SMD:C_0603_1608Metric")
    esp32_cap_10uF[1] += vcc_3v3
    esp32_cap_10uF[2] += gnd

    esp32_cap_100nF = Component(symbol="Device:C", ref="C6", footprint="Capacitor_SMD:C_0603_1608Metric")
    esp32_cap_100nF[1] += vcc_3v3
    esp32_cap_100nF[2] += gnd

    # Basic ESP32 GPIOs (example connections, can be expanded)
    # Assuming a module with exposed GPIOs
    esp32['GPIO1'] += Net('ESP_GPIO_1') # Example GPIO for sensor/actuator
    esp32['GPIO2'] += Net('ESP_GPIO_2') # Example GPIO for sensor/actuator
    esp32['EN'] += vcc_3v3 # Enable pin pulled high for continuous operation

    # --- Status LED (example) ---
    led_status = Component(symbol="Device:LED", ref="D1", footprint="LED_SMD:LED_0603_1608Metric")
    res_led = Component(symbol="Device:R", ref="R1", footprint="Resistor_SMD:R_0603_1608Metric")

    # Connect LED to an ESP32 GPIO (e.g., GPIO2)
    led_status['K'] += gnd
    led_status['A'] += res_led[2]
    res_led[1] += esp32['GPIO2'] # Connect to an ESP32 GPIO
    res_led.value = "330R" # Current limiting resistor for 3.3V LED

    return circuit

if __name__ == '__main__':
    circuit = main()
    circuit.generate_kicad_project("esp32_iot_controller", force_regenerate=True)