#!/usr/bin/env python3
"""
Pre-made Circuit: stm32
Description: stm32 + imu + usb-c
Category: microcontrollers
Generated: 2025-07-30 16:22:15
"""

from circuit_synth import Component, Net, circuit


@circuit
def stm32():
    """
    stm32 + imu + usb-c
    
    Components:
    - DEMO_STM32_001: Demo component for stm32
    - DEMO_LSM6DS3_001: Demo component for LSM6DS3
    - DEMO_MPU6050_001: Demo component for MPU6050
    - TYPE-C-31-M-12: USB-C Receptacle, SMT
    """
    
    # Power nets
    vcc_3v3 = Net("VCC_3V3")
    gnd = Net("GND")
    
    # Demo component for stm32
    comp_1 = Component(
        symbol="Device:R",
        ref="U1",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Demo component for LSM6DS3
    comp_2 = Component(
        symbol="Sensor_Motion:LSM6DS3TR-C",
        ref="U2",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Demo component for MPU6050
    comp_3 = Component(
        symbol="Sensor_Motion:LSM6DS3TR-C",
        ref="U3",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # USB-C Receptacle, SMT
    comp_4 = Component(
        symbol="Device:R",
        ref="U4",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Basic power connections
    # TODO: Add specific net connections based on circuit requirements
    
    print("✅ stm32 circuit created successfully!")
    return locals()  # Return all local variables for inspection


if __name__ == "__main__":
    stm32()