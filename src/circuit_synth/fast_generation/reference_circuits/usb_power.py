#!/usr/bin/env python3
"""
USB-C Power Input Circuit - Reference Circuit
USB-C connector with CC resistors and basic power delivery
"""

from circuit_synth import *

@circuit(name="USB_C_Power_Input")
def usb_power():
    """
    USB-C power input circuit with CC configuration
    - USB-C receptacle connector
    - CC1/CC2 pull-down resistors for power negotiation  
    - Power output with protection
    - Optional VBUS voltage divider for monitoring
    """
    
    # Create power nets
    vbus = Net('VBUS')       # USB-C VBUS (5V)
    vcc_out = Net('VCC_OUT') # Regulated output
    gnd = Net('GND')
    
    # USB-C connector signals
    usb_dp = Net('USB_DP')   # USB Data+
    usb_dm = Net('USB_DM')   # USB Data-
    cc1 = Net('CC1')         # Configuration Channel 1
    cc2 = Net('CC2')         # Configuration Channel 2
    
    # USB-C receptacle connector
    usb_c = Component(
        symbol="Connector:USB_C_Receptacle_Palconn_UTC16-G",
        ref="J",
        footprint="Connector_USB:USB_C_Receptacle_Palconn_UTC16-G"
    )
    
    # CC1 pull-down resistor (5.1k for default USB power)
    cc1_resistor = Component(
        symbol="Device:R",
        ref="R",
        value="5.1k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # CC2 pull-down resistor (5.1k for default USB power) 
    cc2_resistor = Component(
        symbol="Device:R",
        ref="R",
        value="5.1k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # VBUS protection fuse (resettable PTC)
    vbus_fuse = Component(
        symbol="Device:Fuse",
        ref="F",
        value="2A",
        footprint="Fuse:Fuse_1206_3216Metric"
    )
    
    # VBUS filtering capacitor
    cap_vbus = Component(
        symbol="Device:C",
        ref="C", 
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    
    # Power output connector
    power_output = Component(
        symbol="Connector_Generic:Conn_01x02",
        ref="J",
        footprint="Connector_JST:JST_XH_B2B-XH-A_1x02_P2.50mm_Vertical"
    )
    
    # USB data output connector (optional)
    usb_data_output = Component(
        symbol="Connector_Generic:Conn_01x04", 
        ref="J",
        footprint="Connector_PinHeader_2.54mm:PinHeader_1x04_P2.54mm_Vertical"
    )
    
    # Optional VBUS voltage divider for monitoring (12k/4.7k = ~3.9V max)
    vbus_divider_high = Component(
        symbol="Device:R",
        ref="R",
        value="12k", 
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    vbus_divider_low = Component(
        symbol="Device:R",
        ref="R", 
        value="4.7k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Voltage monitoring output
    vbus_monitor = Net('VBUS_MONITOR')
    
    # USB-C connector pin assignments
    usb_c["A4"] += vbus      # VBUS (A-side)
    usb_c["A9"] += vbus      # VBUS (A-side) 
    usb_c["B4"] += vbus      # VBUS (B-side)
    usb_c["B9"] += vbus      # VBUS (B-side)
    usb_c["A1"] += gnd       # GND (A-side)
    usb_c["A12"] += gnd      # GND (A-side)
    usb_c["B1"] += gnd       # GND (B-side)
    usb_c["B12"] += gnd      # GND (B-side)
    
    # USB data signals
    usb_c["A6"] += usb_dp    # D+ (A-side)
    usb_c["A7"] += usb_dm    # D- (A-side)
    usb_c["B6"] += usb_dp    # D+ (B-side) 
    usb_c["B7"] += usb_dm    # D- (B-side)
    
    # Configuration channels
    usb_c["A5"] += cc1       # CC1
    usb_c["B5"] += cc2       # CC2
    
    # CC pull-down resistors for 5V/500mA power capability
    cc1_resistor["1"] += cc1
    cc1_resistor["2"] += gnd
    cc2_resistor["1"] += cc2
    cc2_resistor["2"] += gnd
    
    # VBUS protection and filtering
    vbus_fuse["1"] += vbus
    vbus_fuse["2"] += vcc_out
    cap_vbus["1"] += vcc_out
    cap_vbus["2"] += gnd
    
    # Power output
    power_output["1"] += vcc_out  # Protected 5V output
    power_output["2"] += gnd      # Ground
    
    # USB data output (for pass-through to MCU)
    usb_data_output["1"] += vcc_out  # Power
    usb_data_output["2"] += gnd      # Ground
    usb_data_output["3"] += usb_dp   # USB D+
    usb_data_output["4"] += usb_dm   # USB D-
    
    # VBUS voltage monitoring (optional)
    vbus_divider_high["1"] += vcc_out
    vbus_divider_high["2"] += vbus_monitor
    vbus_divider_low["1"] += vbus_monitor  
    vbus_divider_low["2"] += gnd


if __name__ == "__main__":
    print("🚀 Generating USB-C Power Input Circuit...")
    
    circuit_obj = usb_power()
    circuit_obj.generate_kicad_project(
        project_name="USB_C_Power_Input",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )
    
    print("✅ USB-C Power Input KiCad project generated!")
    print("📁 Check USB_C_Power_Input/ directory for files")