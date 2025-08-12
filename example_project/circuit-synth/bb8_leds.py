#!/usr/bin/env python3
"""
BB-8 LED Control System
RGB LED control for lighting effects
"""

from circuit_synth import *

@circuit(name="bb8_led_control")
def led_control():
    """
    LED control system for BB-8 lighting effects
    
    Features:
    - WS2812B addressable RGB LEDs
    - Level shifter for 5V LED data
    - Power distribution for LED strips
    - Multiple LED zones (head, body)
    """
    
    # Power nets
    vcc_5v = Net('VCC_5V')
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')
    
    # LED control signals
    led_data_in = Net('LED_DATA_IN')   # From ESP32 (3.3V)
    led_data_out = Net('LED_DATA_OUT') # To LEDs (5V)
    
    # 74HCT125 Level Shifter
    level_shifter = Component(
        ref="U1", 
        symbol="74xx:74HCT125",
        footprint="Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
        value="74HCT125"
    )
    
    # Power for level shifter
    level_shifter['VCC'] += vcc_5v
    level_shifter['GND'] += gnd
    
    # Level shift LED data from 3.3V to 5V
    level_shifter['1A'] += led_data_in
    level_shifter['1Y'] += led_data_out
    level_shifter['1OE'] += gnd  # Output enable (active low)
    
    # Tie unused inputs
    level_shifter['2OE'] += vcc_5v  # Disable unused buffers
    level_shifter['3OE'] += vcc_5v
    level_shifter['4OE'] += vcc_5v
    level_shifter['2A'] += gnd
    level_shifter['3A'] += gnd
    level_shifter['4A'] += gnd
    
    # LED power filtering
    c_led_power = Component(
        ref="C1",
        symbol="Device:C",
        footprint="Capacitor_SMD:C_1210_3225Metric",
        value="1000uF"
    )
    c_led_power[1] += vcc_5v
    c_led_power[2] += gnd
    
    c_led_ceramic = Component(
        ref="C2",
        symbol="Device:C",
        footprint="Capacitor_SMD:C_0603_1608Metric",
        value="100nF"
    )
    c_led_ceramic[1] += vcc_5v
    c_led_ceramic[2] += gnd
    
    # LED data protection resistor
    r_data_protect = Component(
        ref="R1",
        symbol="Device:R",
        footprint="Resistor_SMD:R_0603_1608Metric",
        value="330"
    )
    
    led_data_protected = Net('LED_DATA_PROTECTED')
    r_data_protect[1] += led_data_out
    r_data_protect[2] += led_data_protected
    
    # Head LED connector
    led_head_conn = Component(
        ref="J1",
        symbol="Connector:Conn_01x03_Male",
        footprint="Connector_JST:JST_PH_B3B-PH-K_1x03_P2.00mm_Vertical",
        value="LED_HEAD"
    )
    
    led_head_conn[1] += vcc_5v
    led_head_conn[2] += gnd
    led_head_conn[3] += led_data_protected
    
    # Body LED connector (chained from head)
    led_body_conn = Component(
        ref="J2", 
        symbol="Connector:Conn_01x03_Male",
        footprint="Connector_JST:JST_PH_B3B-PH-K_1x03_P2.00mm_Vertical",
        value="LED_BODY"
    )
    
    led_data_chain = Net('LED_DATA_CHAIN')
    led_body_conn[1] += vcc_5v
    led_body_conn[2] += gnd  
    led_body_conn[3] += led_data_chain
    
    # Base LED connector (chained from body)
    led_base_conn = Component(
        ref="J3",
        symbol="Connector:Conn_01x03_Male",
        footprint="Connector_JST:JST_PH_B3B-PH-K_1x03_P2.00mm_Vertical",
        value="LED_BASE"
    )
    
    led_data_chain2 = Net('LED_DATA_CHAIN2')
    led_base_conn[1] += vcc_5v
    led_base_conn[2] += gnd
    led_base_conn[3] += led_data_chain2
    
    # LED power status indicator
    led_power_status = Component(
        ref="D1",
        symbol="Device:LED",
        footprint="LED_SMD:LED_0603_1608Metric",
        value="BLUE"
    )
    
    r_power_status = Component(
        ref="R2",
        symbol="Device:R",
        footprint="Resistor_SMD:R_0603_1608Metric",
        value="1k"
    )
    
    r_power_status[1] += vcc_5v
    r_power_status[2] += led_power_status[1]  # Anode
    led_power_status[2] += gnd  # Cathode
    
    # LED data activity indicator
    led_activity = Component(
        ref="D2",
        symbol="Device:LED", 
        footprint="LED_SMD:LED_0603_1608Metric",
        value="GREEN"
    )
    
    r_activity = Component(
        ref="R3",
        symbol="Device:R",
        footprint="Resistor_SMD:R_0603_1608Metric",
        value="1k"
    )
    
    r_activity[1] += led_data_out
    r_activity[2] += led_activity[1]
    led_activity[2] += gnd
    
    # Current monitoring (optional)
    r_current_sense = Component(
        ref="R4",
        symbol="Device:R",
        footprint="Resistor_SMD:R_1206_3216Metric",
        value="0.1"
    )
    
    led_power_monitored = Net('LED_POWER_MON')
    r_current_sense[1] += vcc_5v
    r_current_sense[2] += led_power_monitored
    
    # Update LED connectors to use monitored power
    led_head_conn[1] += led_power_monitored
    led_body_conn[1] += led_power_monitored  
    led_base_conn[1] += led_power_monitored
    
    return {
        'led_nets': {
            'LED_DATA_IN': led_data_in
        }
    }