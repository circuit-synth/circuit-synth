from circuit_synth import *

@circuit(name="ESP32_IMU_USB_C")
def esp32_imu_usb_c_circuit():
    # Nets
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')
    usb_dp = Net('USB_DP')
    usb_dm = Net('USB_DM')
    scl_net = Net('SCL_IMU')
    sda_net = Net('SDA_IMU')

    # Components
    esp32 = Component(
        symbol="RF_Module:ESP32-C6-MINI-1",
        ref="U1",
        footprint="RF_Module:ESP32-C6-MINI-1"
    )

    usb_c = Component(
        symbol="Connector:USB_C_Receptacle_USB2.0_16P",
        ref="J1",
        footprint="Connector_USB:USB_C_Receptacle_USB2.0_16P"
    )

    mpu6050 = Component(
        symbol="Sensor_Motion:MPU-6050",
        ref="U2",
        footprint="Package_LGA:LGA-24_4x4mm_P0.5mm"
    )

    # Connections
    # ESP32-C6 Power
    esp32["3V3"] += vcc_3v3
    esp32["GND"] += gnd

    # USB-C Connections
    usb_c["VBUS"] += vcc_3v3  # Power from USB
    usb_c["GND"] += gnd
    usb_c["D+"] += usb_dp
    usb_c["D-"] += usb_dm

    # ESP32 USB D+/D- (assuming these are the correct pins for USB data on C6)
    # Note: ESP32-C6-MINI-1 does not explicitly list D+/D- pins.
    # For a real design, these would connect to the internal USB peripheral pins.
    # For this example, we'll connect them to generic IO pins as a placeholder.
    # In a real design, you'd connect to the dedicated USB D+/D- pins if available,
    # or use a USB-to-UART bridge if the ESP32 only has UART for programming.
    # For ESP32-C6, USB is typically on IO19/IO20 or internal.
    # We'll use IO19 and IO20 as placeholders for D+/D- for demonstration.
    esp32["IO19"] += usb_dp
    esp32["IO20"] += usb_dm

    # MPU-6050 Power
    mpu6050["VDD"] += vcc_3v3
    mpu6050["VLOGIC"] += vcc_3v3
    mpu6050["GND"] += gnd

    # MPU-6050 I2C to ESP32
    # Assuming ESP32 I2C pins are IO8 (SDA) and IO9 (SCL)
    esp32["IO8"] += sda_net
    esp32["IO9"] += scl_net
    mpu6050["SDA"] += sda_net
    mpu6050["SCL"] += scl_net

    # MPU-6050 AD0 pin (typically pulled low for default I2C address)
    mpu6050["AD0"] += gnd

    # ESP32 EN pin (pull-up to VCC_3V3 for normal operation)
    # A resistor would typically be here, but for simplicity, direct connection.
    esp32["EN"] += vcc_3v3

if __name__ == "__main__":
    circuit_obj = esp32_imu_usb_c_circuit()
    circuit_obj.generate_kicad_project(
        project_name="ESP32_IMU_USB_C_Board",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )
    print("✅ KiCad project generated!")