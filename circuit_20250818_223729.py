from circuit_synth import *

@circuit(name="ESP32_S3_IMU_NeoPixel_USB_C")
def esp32_s3_imu_neopixel_usb_c_circuit():
    # Nets
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')
    vbus = Net('VBUS')
    usb_dp = Net('USB_DP')
    usb_dm = Net('USB_DM')
    scl_net = Net('SCL_IMU')
    sda_net = Net('SDA_IMU')
    neopixel_data = Net('NEOPIXEL_DATA')

    # Components
    esp32_s3 = Component(
        symbol="MCU_Espressif:ESP32-S3",
        ref="U1",
        footprint="Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP5.6x5.6mm"
    )

    mpu6050 = Component(
        symbol="Sensor_Motion:MPU-6050",
        ref="U2",
        footprint="Package_LGA:LGA-24_3x3mm_P0.4mm" # Assuming a common LGA footprint for MPU-6050
    )

    # NeoPixel is typically a single LED with integrated driver, represented as a generic LED for connection
    # For a true NeoPixel, you'd need a specific symbol/footprint if available, or model it as an LED with data pin.
    # Using a generic LED for now, assuming the data line goes to a GPIO.
    neopixel_led = Component(
        symbol="Device:LED",
        ref="D1",
        footprint="LED_SMD:LED_0603_1608Metric" # Placeholder, actual NeoPixel footprint would vary
    )

    usb_c_conn = Component(
        symbol="Connector:USB_C_Receptacle_USB2.0_16P",
        ref="J1",
        footprint="Connector_USB:USB_C_Receptacle_USB2.0_16P_Vertical" # Assuming a vertical mount
    )

    # Power connections (simplified, typically needs regulators, caps, etc.)
    esp32_s3["VDD3P3"] += vcc_3v3
    esp32_s3["VDD3P3_RTC"] += vcc_3v3
    esp32_s3["VDD_SPI"] += vcc_3v3
    esp32_s3["VDD3P3_CPU"] += vcc_3v3
    esp32_s3["VDDA"] += vcc_3v3 # Both VDDA pins
    esp32_s3["GND"] += gnd

    mpu6050["VDD"] += vcc_3v3
    mpu6050["VLOGIC"] += vcc_3v3
    mpu6050["GND"] += gnd

    neopixel_led[1] += neopixel_data # Data in for NeoPixel (simplified as LED anode)
    neopixel_led[2] += gnd # Ground for NeoPixel (simplified as LED cathode)
    # Note: A real NeoPixel would also need VCC, typically 5V or 3.3V depending on type.
    # This example assumes it's powered from 3.3V for simplicity, but a level shifter might be needed for 5V NeoPixels.

    usb_c_conn["VBUS"] += vbus
    usb_c_conn["GND"] += gnd
    usb_c_conn["D+"] += usb_dp
    usb_c_conn["D-"] += usb_dm
    usb_c_conn["SHIELD"] += gnd # Connect shield to ground

    # ESP32-S3 USB connections
    esp32_s3["GPIO20/USB_D+"] += usb_dp
    esp32_s3["GPIO19/USB_D-"] += usb_dm

    # ESP32-S3 I2C connections to MPU-6050
    esp32_s3["GPIO8"] += scl_net # Example I2C SCL pin
    esp32_s3["GPIO9"] += sda_net # Example I2C SDA pin

    mpu6050["SCL"] += scl_net
    mpu6050["SDA"] += sda_net
    mpu6050["AD0"] += gnd # Tie AD0 to GND for default I2C address (0x68)

    # ESP32-S3 NeoPixel data connection
    esp32_s3["GPIO10"] += neopixel_data # Example GPIO for NeoPixel data

if __name__ == "__main__":
    circuit_obj = esp32_s3_imu_neopixel_usb_c_circuit()
    circuit_obj.generate_kicad_project(
        project_name="ESP32_S3_IMU_NeoPixel_USB_C_Board",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )
    print("✅ KiCad project generated!")