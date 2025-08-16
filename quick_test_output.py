from circuit_synth import *

@circuit(name="ESP32_MPU6050_Circuit")
def esp32_mpu6050_circuit():
    # Create nets
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')
    scl_net = Net('SCL_NET')
    sda_net = Net('SDA_NET')

    # Create components
    esp32 = Component(
        symbol="RF_Module:ESP32-C6-MINI-1",
        ref="U1",
        footprint="RF_Module:ESP32-C6-MINI-1"
    )

    mpu6050 = Component(
        symbol="Sensor_Motion:MPU-6050",
        ref="U2",
        footprint="Package_LGA:LGA-24_4x4mm_P0.5mm" # Common footprint for MPU-6050
    )

    r_pullup_scl = Component(
        symbol="Device:R",
        ref="R1",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    r_pullup_sda = Component(
        symbol="Device:R",
        ref="R2",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )

    c_decoupling_esp32 = Component(
        symbol="Device:C",
        ref="C1",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )

    c_decoupling_mpu6050 = Component(
        symbol="Device:C",
        ref="C2",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )

    # Connect ESP32 power
    esp32["3V3"] += vcc_3v3
    esp32["GND"] += gnd
    c_decoupling_esp32["1"] += vcc_3v3
    c_decoupling_esp32["2"] += gnd

    # Connect MPU-6050 power
    mpu6050["VDD"] += vcc_3v3
    mpu6050["VLOGIC"] += vcc_3v3 # VLOGIC typically connected to VDD for 3.3V operation
    mpu6050["GND"] += gnd
    c_decoupling_mpu6050["1"] += vcc_3v3
    c_decoupling_mpu6050["2"] += gnd

    # Connect I2C bus (ESP32 IO8 as SCL, IO9 as SDA)
    esp32["IO8"] += scl_net
    esp32["IO9"] += sda_net

    mpu6050["SCL"] += scl_net
    mpu6050["SDA"] += sda_net

    # I2C Pull-up resistors
    r_pullup_scl["1"] += vcc_3v3
    r_pullup_scl["2"] += scl_net

    r_pullup_sda["1"] += vcc_3v3
    r_pullup_sda["2"] += sda_net

    # MPU-6050 AD0 pin (set to GND for default I2C address 0x68)
    mpu6050["AD0"] += gnd

if __name__ == "__main__":
    circuit_obj = esp32_mpu6050_circuit()
    circuit_obj.generate_kicad_project(
        project_name="ESP32_MPU6050_Project",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )
    print("✅ KiCad project generated!")