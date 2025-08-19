#!/usr/bin/env python3
"""
Stepper Motor Driver Circuit - Reference Circuit
DRV8825 stepper driver with protection and current limiting
"""

from circuit_synth import *

@circuit(name="Stepper_Motor_Driver")
def motor_stepper(VCC_12V, VCC_5V, VCC_3V3, GND, STEP, DIR, ENABLE):
    """
    DRV8825 stepper motor driver circuit
    - DRV8825 stepper motor driver breakout board
    - Stepper motor connector (4-wire bipolar)
    - Current limiting via potentiometer
    """
    
    # DRV8825 stepper driver (Pololu breakout board)
    drv8825 = Component(
        symbol="Driver_Motor:Pololu_Breakout_DRV8825",
        ref="U",
        footprint="Module:Pololu_Breakout-16_15.2x20.3mm"
    )
    
    # Stepper motor connector (4-pin for bipolar stepper)
    motor_connector = Component(
        symbol="Connector_Generic:Conn_01x04",
        ref="J",
        footprint="Connector_JST:JST_XH_B4B-XH-A_1x04_P2.50mm_Vertical"
    )
    
    # Power input connector
    power_connector = Component(
        symbol="Connector_Generic:Conn_01x02", 
        ref="J",
        footprint="Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical"
    )
    
    # Control input connector (from microcontroller)
    control_connector = Component(
        symbol="Connector_Generic:Conn_01x06",
        ref="J",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x06_P2.54mm_Vertical"
    )
    
    # Current sense resistors (0.1 ohm, 1W)
    rsense_a = Component(
        symbol="Device:R",
        ref="R",
        value="0.1",
        footprint="Resistor_SMD:R_1206_3216Metric"
    )
    
    rsense_b = Component(
        symbol="Device:R", 
        ref="R",
        value="0.1",
        footprint="Resistor_SMD:R_1206_3216Metric"
    )
    
    # Current limiting potentiometer
    current_pot = Component(
        symbol="Device:R_Potentiometer",
        ref="RV",
        value="10k",
        footprint="Potentiometer_THT:Potentiometer_Bourns_3296W_Vertical"
    )
    
    # Power supply decoupling
    cap_vmot = Component(
        symbol="Device:C_Polarized",
        ref="C",
        value="100uF",
        footprint="Capacitor_THT:CP_Radial_D8.0mm_P3.50mm"
    )
    
    cap_logic = Component(
        symbol="Device:C",
        ref="C", 
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    # DRV8825 power connections
    drv8825["VMOT"] += vmot      # Motor supply voltage
    drv8825["GND"] += gnd        # Ground (multiple pins)
    drv8825["VDD"] += vcc_5v     # Logic supply (5V)
    
    # Motor output connections
    drv8825["A2"] += motor_connector["1"]  # Coil A+
    drv8825["A1"] += motor_connector["2"]  # Coil A-  
    drv8825["B1"] += motor_connector["3"]  # Coil B-
    drv8825["B2"] += motor_connector["4"]  # Coil B+
    
    # Control signal connections
    drv8825["STEP"] += step
    drv8825["DIR"] += direction
    drv8825["nENABLE"] += enable
    
    # Current sense resistors
    drv8825["AISENSE"] += rsense_a["1"]
    rsense_a["2"] += gnd
    drv8825["BISENSE"] += rsense_b["1"] 
    rsense_b["2"] += gnd
    
    # Current reference (potentiometer)
    current_pot["1"] += vcc_3v3
    current_pot["2"] += drv8825["VREF"]  # Wiper to VREF
    current_pot["3"] += gnd
    
    # Power input
    power_connector["1"] += vmot
    power_connector["2"] += gnd
    
    # Control interface
    control_connector["1"] += vcc_3v3  # Power for MCU interface
    control_connector["2"] += gnd      # Ground
    control_connector["3"] += step     # Step signal
    control_connector["4"] += direction # Direction signal  
    control_connector["5"] += enable   # Enable signal
    control_connector["6"] += vcc_5v   # 5V logic supply out
    
    # Power supply decoupling
    cap_vmot["1"] += vmot
    cap_vmot["2"] += gnd
    cap_logic["1"] += vcc_5v
    cap_logic["2"] += gnd
    
    # Microstepping configuration (default 1/32 step)
    drv8825["M0"] += gnd    # MS1 = 0
    drv8825["M1"] += vcc_5v # MS2 = 1  
    drv8825["M2"] += vcc_5v # MS3 = 1


if __name__ == "__main__":
    print("🚀 Generating Stepper Motor Driver Circuit...")
    
    circuit_obj = motor_stepper()
    circuit_obj.generate_kicad_project(
        project_name="Stepper_Motor_Driver",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )
    
    print("✅ Stepper Motor Driver KiCad project generated!")
    print("📁 Check Stepper_Motor_Driver/ directory for files")