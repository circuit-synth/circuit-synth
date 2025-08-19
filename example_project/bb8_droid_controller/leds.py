from circuit_synth import *

@circuit(name="led_circuit")
def led_circuit(vcc_3v3, gnd):
    """LED indicator circuits"""
    
    # Status LEDs
    led1 = Component(
        symbol="Device:LED",
        ref="D2",
        footprint="LED_SMD:LED_0603_1608Metric"
    )
    
    led2 = Component(
        symbol="Device:LED", 
        ref="D3",
        footprint="LED_SMD:LED_0603_1608Metric"
    )
    
    led3 = Component(
        symbol="Device:LED",
        ref="D4",
        footprint="LED_SMD:LED_0603_1608Metric"
    )
    
    # Current limiting resistors
    r1 = Component(
        symbol="Device:R",
        ref="R10",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    r2 = Component(
        symbol="Device:R",
        ref="R11", 
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    r3 = Component(
        symbol="Device:R",
        ref="R12",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Control signals from MCU
    led1_ctrl = Net('LED1_CTRL')
    led2_ctrl = Net('LED2_CTRL')
    led3_ctrl = Net('LED3_CTRL')
    
    # LED 1 connections
    r1[1] += led1_ctrl
    r1[2] += led1[1]  # Anode
    led1[2] += gnd    # Cathode
    
    # LED 2 connections
    r2[1] += led2_ctrl
    r2[2] += led2[1]  # Anode
    led2[2] += gnd    # Cathode
    
    # LED 3 connections
    r3[1] += led3_ctrl
    r3[2] += led3[1]  # Anode
    led3[2] += gnd    # Cathode
