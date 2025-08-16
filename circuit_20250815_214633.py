from circuit_synth import *

@circuit(name="ESP32_IMU_USB_C")
def esp32_imu_usb_c_circuit():
    # Nets
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')
    usb_dp = Net('USB_DP')
    usb_dm = Net('USB_DM')
    usb_vbus = Net('USB_VBUS')
    usb_gnd = Net('USB_GND')
    imu_scl = Net('IMU_SCL')
    imu_sda = Net('IMU_SDA')

    # Components
    esp32 = Component(
        symbol="MCU_Espressif:ESP32-S3",
        ref="U1",
        footprint="Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP5.6x5.6mm"
    )

    # Note: A generic IMU symbol is used as specific IMU symbols are not in the verified list.
    # For a real design, you would use a specific IMU part (e.g., MPU6050, LSM6DS3)
    # and its corresponding KiCad symbol/footprint.
    imu = Component(
        symbol="Sensor_Motion:MPU-6050", # Using a common IMU symbol, verify in KiCad library
        ref="U2",
        footprint="Package_LGA:LGA-24_4x4mm_P0.5mm" # Example footprint, verify for chosen IMU
    )

    usb_c_conn = Component(
        symbol="Connector:USB_C_Receptacle", # Using a common USB-C symbol, verify in KiCad library
        ref="J1",
        footprint="Connector_USB:USB_C_Receptacle_USB2.0" # Example footprint, verify for chosen connector
    )

    # Resistors for USB D+/D- pull-ups (if needed for host detection, ESP32-S3 has internal)
    # R1 = Component(symbol="Device:R", ref="R1", footprint="Resistor_SMD:R_0603_1608Metric")
    # R2 = Component(symbol="Device:R", ref="R2", footprint="Resistor_SMD:R_0603_1608Metric")

    # Capacitors for decoupling
    C1 = Component(symbol="Device:C", ref="C1", footprint="Capacitor_SMD:C_0603_1608Metric")
    C2 = Component(symbol="Device:C", ref="C2", footprint="Capacitor_SMD:C_0603_1608Metric")

    # Connections
    # ESP32 Power
    esp32["VDD"] += vcc_3v3
    esp32["VSS"] += gnd
    esp32["VDDA"] += vcc_3v3 # Analog VDD
    esp32["VSSA"] += gnd     # Analog VSS

    # Decoupling Capacitors
    C1[1] += vcc_3v3
    C1[2] += gnd
    C2[1] += vcc_3v3
    C2[2] += gnd

    # USB-C Connector
    usb_c_conn["VBUS"] += usb_vbus
    usb_c_conn["GND"] += usb_gnd
    usb_c_conn["D+"] += usb_dp
    usb_c_conn["D-"] += usb_dm
    # USB-C CC pins typically need pull-down resistors for DFP (Device) mode,
    # but for a simple circuit, they might be omitted or handled by the host.
    # For a full design, add R_CC1 and R_CC2 to GND.

    # USB to ESP32 (ESP32-S3 has native USB)
    esp32["USB_DP"] += usb_dp
    esp32["USB_DM"] += usb_dm
    # ESP32-S3 VBUS detection pin (optional, but good practice)
    # esp32["GPIO20"] += usb_vbus # Example, check datasheet for specific VBUS pin

    # IMU I2C Connection to ESP32
    # Assuming IMU uses I2C and ESP32 uses default I2C pins (GPIO8/GPIO9 for ESP32-S3)
    imu["SCL"] += imu_scl
    imu["SDA"] += imu_sda
    imu["VCC"] += vcc_3v3
    imu["GND"] += gnd

    esp32["IO8"] += imu_scl # ESP32-S3 default I2C SCL
    esp32["IO9"] += imu_sda # ESP32-S3 default I2C SDA

    # Power net connections
    usb_vbus += vcc_3v3 # Assuming VBUS directly powers 3V3 via a regulator (not shown)
                        # For a real design, you'd add a 3.3V LDO regulator here.
    usb_gnd += gnd

if __name__ == "__main__":
    circuit_obj = esp32_imu_usb_c_circuit()
    circuit_obj.generate_kicad_project(
        project_name="ESP32_IMU_USB_C_Project",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )
    print("✅ KiCad project generated!")