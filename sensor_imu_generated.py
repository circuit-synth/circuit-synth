from circuitsynth import *

# Define power rails
VCC_3V3 = Net("VCC_3V3")
GND = Net("GND")

# --- Component Definitions and Pin Finding ---

# 1. MPU-6050 IMU Sensor
# /find-pins Sensor_Motion:MPU-6050
# Found pins for Sensor_Motion:MPU-6050:
# VDD, GND, SCL, SDA, AD0, INT, CLKIN, CLKOUT, RESV1, RESV2, RESV3, RESV4, RESV5, RESV6, RESV7, RESV8, RESV9, RESV10, RESV11, RESV12, RESV13, RESV14, RESV15, RESV16
U1 = Component(
    "U1",
    symbol="Sensor_Motion:MPU-6050",
    footprint="Sensor_Motion:InvenSense_QFN-24_4x4mm_P0.5mm",
    description="MPU-6050 6-axis IMU sensor"
)

# 2. Decoupling Capacitor
# /find-pins Device:C
# Found pins for Device:C:
# 1, 2
C1 = Component(
    "C1",
    symbol="Device:C",
    footprint="Capacitor_SMD:C_0603_1608Metric",
    value="0.1uF",
    description="Power supply decoupling capacitor"
)

# 3. I2C Breakout Connector
# /find-pins Connector:Conn_01x06_Pin
# Found pins for Connector:Conn_01x06_Pin:
# 1, 2, 3, 4, 5, 6
J1 = Component(
    "J1",
    symbol="Connector:Conn_01x06_Pin",
    footprint="Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical",
    description="I2C Breakout Header"
)

# --- Net Connections ---

# Power and Ground for MPU-6050
U1.pin.VDD += VCC_3V3
U1.pin.GND += GND

# Decoupling Capacitor for MPU-6050
C1.pin['1'] += VCC_3V3
C1.pin['2'] += GND

# I2C Connections
U1.pin.SCL += J1.pin['3']  # SCL
U1.pin.SDA += J1.pin['4']  # SDA

# Power and Ground to Breakout Connector
J1.pin['1'] += VCC_3V3  # VCC
J1.pin['2'] += GND      # GND

# Unused MPU-6050 pins (connect to GND or leave floating based on datasheet, here we float for simplicity)
# For production, AD0 should be pulled high/low for address selection.
# U1.pin.AD0 += GND # Example: connect AD0 to GND for default I2C address 0x68

# --- Board Definition ---
board = Board(
    title="MPU-6050 IMU Sensor Module",
    description="A compact module featuring the MPU-6050 IMU sensor with I2C interface.",
    components=[U1, C1, J1],
    nets=[VCC_3V3, GND]
)

# --- Export to KiCad ---
if __name__ == "__main__":
    board.export_kicad(
        output_dir="kicad_project_mpu6050_imu",
        create_project=True,
        open_kicad=False
    )
    print("KiCad project for MPU-6050 IMU Sensor Module generated successfully.")
    print("Check 'kicad_project_mpu6050_imu' directory.")