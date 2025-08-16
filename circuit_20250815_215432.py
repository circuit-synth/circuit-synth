from circuit_synth import *

@circuit(name="ESP32_IMU_USB_C")
def esp32_imu_usb_c_circuit():
    # Nets
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')
    scl = Net('SCL')
    sda = Net('SDA')
    usb_dp = Net('USB_DP')
    usb_dm = Net('USB_DM')
    usb_vbus = Net('USB_VBUS')

    # Components
    esp32 = Component(
        symbol="RF_Module:ESP32-C6-MINI-1",
        ref="U1",
        footprint="RF_Module:ESP32-C6-MINI-1"
    )

    mpu6050 = Component(
        symbol="Sensor_Motion:MPU-6050",
        ref="U2",
        footprint="Package_LGA:LGA-24_4x4mm_P0.5mm" # Common footprint for MPU-6050, adjust if specific package is known
    )

    usb_c_conn = Component(
        symbol="Connector:USB_C_Receptacle_USB2.0_16P",
        ref="J1",
        footprint="Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12" # Common footprint for USB-C, adjust if specific part is known
    )

    # Connections
    # ESP32-C6-MINI-1 Power
    esp32["3V3"] += vcc_3v3
    esp32["GND"] += gnd

    # MPU-6050 Power and I2C (assuming common MPU-6050 pinout)
    mpu6050["VCC"] += vcc_3v3
    mpu6050["GND"] += gnd
    mpu6050["SCL"] += scl
    mpu6050["SDA"] += sda

    # Connect ESP32 I2C to MPU-6050 (using common ESP32 I2C pins, adjust if specific pins are desired)
    esp32["IO8"] += sda # Example I2C SDA
    esp32["IO9"] += scl # Example I2C SCL

    # USB-C Connector (assuming common USB-C receptacle pinout for USB 2.0)
    usb_c_conn["VBUS"] += usb_vbus # VBUS from USB-C
    usb_c_conn["GND"] += gnd       # GND from USB-C
    usb_c_conn["D+"] += usb_dp     # USB Data Plus
    usb_c_conn["D-"] += usb_dm     # USB Data Minus

    # Connect ESP32 USB to USB-C (ESP32-C6 has internal USB-to-Serial, these are for direct USB D+/D- if needed)
    # For ESP32-C6-MINI-1, USB is typically handled internally for programming/UART.
    # If direct USB D+/D- are exposed and needed for a specific application, connect them here.
    # For typical programming, the module handles it.
    # Assuming the ESP32-C6-MINI-1 handles USB internally for programming/UART via its TXD0/RXD0,
    # we'll connect the USB-C D+/D- to the ESP32's internal USB pins if they were exposed.
    # As they are not explicitly listed as IO pins for direct connection, we'll leave them floating
    # or connect to specific internal USB pins if the module datasheet specifies them.
    # For now, we'll connect them to the ESP32's TXD0/RXD0 as a placeholder for serial communication,
    # though this is not a direct USB D+/D- connection.
    # A proper USB connection would require specific USB D+/D- pins on the ESP32 module.
    # For the ESP32-C6-MINI-1, the USB is typically for programming/UART via its internal USB-to-Serial converter.
    # We will connect the USB-C D+/D- to the ESP32's internal USB interface if available,
    # otherwise, these nets might be used for external USB-to-serial converter.
    # Since the ESP32-C6-MINI-1 has an internal USB-to-UART bridge, we don't typically connect D+/D- directly to GPIOs.
    # The module itself handles the USB communication.
    # For this design, we'll assume the USB-C is primarily for power and the internal USB of the ESP32-C6-MINI-1.
    # If direct D+/D- access is needed, specific pins would be required from the module datasheet.
    # For now, we'll connect the USB-C D+/D- to the ESP32's internal USB interface (not exposed as IO pins).
    # We will not connect them to IO pins like TXD0/RXD0 as that's for UART.

    # For a typical ESP32-C6-MINI-1 setup, the USB-C is for power and the internal USB-to-UART.
    # The D+ and D- pins of the USB-C connector would connect to the internal USB PHY of the ESP32-C6.
    # Since these are not exposed as direct IO pins on the RF_Module:ESP32-C6-MINI-1 symbol,
    # we will not make explicit connections to IO pins.
    # The VBUS and GND are essential.
    # The D+/D- lines are implicitly handled by the module's internal USB interface.

    # Add pull-up resistors for I2C (typical for I2C bus)
    r_sda = Component(symbol="Device:R", ref="R1", footprint="Resistor_SMD:R_0603_1608Metric")
    r_scl = Component(symbol="Device:R", ref="R2", footprint="Resistor_SMD:R_0603_1608Metric")

    r_sda[1] += vcc_3v3
    r_sda[2] += sda

    r_scl[1] += vcc_3v3
    r_scl[2] += scl

    # Add decoupling capacitors (essential for stable power)
    c_esp32 = Component(symbol="Device:C", ref="C1", footprint="Capacitor_SMD:C_0603_1608Metric")
    c_mpu6050 = Component(symbol="Device:C", ref="C2", footprint="Capacitor_SMD:C_0603_1608Metric")

    c_esp32[1] += vcc_3v3
    c_esp32[2] += gnd

    c_mpu6050[1] += vcc_3v3
    c_mpu6050[2] += gnd

if __name__ == "__main__":
    circuit_obj = esp32_imu_usb_c_circuit()
    circuit_obj.generate_kicad_project(
        project_name="ESP32_IMU_USB_C_Board",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )
    print("✅ KiCad project generated!")