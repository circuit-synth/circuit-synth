from circuit_synth import *

@circuit(name="imu_1")  
def imu_1(vcc_3v3, gnd):
    """IMU sensor 1 circuit"""
    
    # IMU sensor
    imu = Component(
        symbol="Sensor_Motion:MPU-6050",
        ref="U3",
        footprint="Sensor_Motion:InvenSense_QFN-24_4x4mm_P0.5mm"
    )
    
    # Decoupling capacitor
    cap = Component(
        symbol="Device:C",
        ref="C5",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    # Pull-up resistors for I2C
    r_sda = Component(
        symbol="Device:R",
        ref="R3",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    r_scl = Component(
        symbol="Device:R", 
        ref="R4",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # I2C signals
    sda = Net(f'I2C_SDA_1')
    scl = Net(f'I2C_SCL_1')
    
    # Power connections
    imu[8] += vcc_3v3    # VDD
    imu[13] += gnd       # GND
    
    # I2C connections
    imu[23] += sda       # SDA
    imu[24] += scl       # SCL
    
    # Address pin
    imu[9] += gnd        # AD0 = 0
    
    # Decoupling
    cap[1] += vcc_3v3
    cap[2] += gnd
    
    # Pull-up resistors
    r_sda[1] += vcc_3v3
    r_sda[2] += sda
    r_scl[1] += vcc_3v3
    r_scl[2] += scl
