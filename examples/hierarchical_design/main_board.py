#!/usr/bin/env python3
"""
Main Board Design

This demonstrates how to compose a complete design from individual circuit modules.
Each subsystem is defined in its own file, promoting code reuse and maintainability.
"""

from circuit_synth import Circuit, Component, Net, circuit
from .power_supply import ldo_3v3_regulator
from .led_indicator import dual_status_leds


@circuit(name="esp32_development_board")
def esp32_development_board():
    """
    Complete ESP32 development board with integrated power supply and status LEDs.
    
    This design demonstrates:
    - Hierarchical circuit composition
    - Module reuse across projects  
    - Clear separation of concerns
    - Professional PCB layout practices
    
    Features:
    - ESP32-S3 microcontroller
    - Integrated 3.3V regulator
    - Dual status LEDs (power + user)
    - USB-C connector for power and programming
    """
    
    # Define main power and ground nets
    VIN_5V = Net('VIN_5V')      # 5V from USB
    VCC_3V3 = Net('VCC_3V3')    # Regulated 3.3V
    GND = Net('GND')            # Ground
    
    # GPIO nets for status indication
    POWER_LED = Net('POWER_LED')     # Always-on power indicator
    USER_LED = Net('USER_LED')       # User-controllable LED
    
    # USB data nets
    USB_DP = Net('USB_DP')
    USB_DM = Net('USB_DM')
    
    # === POWER SUPPLY SUBSYSTEM ===
    # Use our reusable 3.3V regulator circuit
    ldo_3v3_regulator(VIN_5V, VCC_3V3, GND)
    
    # === MICROCONTROLLER SUBSYSTEM ===
    esp32 = Component(
        symbol="RF_Module:ESP32-S3-MINI-1",
        ref="U",
        footprint="RF_Module:ESP32-S2-MINI-1"
    )
    
    # Connect ESP32 power
    esp32["VDD"] += VCC_3V3
    esp32["GND"] += GND
    
    # Connect USB data lines
    esp32["GPIO19"] += USB_DM  # D-
    esp32["GPIO20"] += USB_DP  # D+
    
    # Connect status LED control
    esp32["GPIO2"] += USER_LED  # User-controllable LED
    
    # Power LED is always on (connected to 3.3V)
    POWER_LED += VCC_3V3
    
    # === STATUS LED SUBSYSTEM ===
    # Use our reusable dual LED circuit
    dual_status_leds(VCC_3V3, GND, POWER_LED, USER_LED)
    
    # === USB CONNECTOR SUBSYSTEM ===
    usb_connector = Component(
        symbol="Connector:USB_C_Receptacle_USB2.0",
        ref="J",
        footprint="Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal"
    )
    
    # Connect USB power and data
    usb_connector["VBUS"] += VIN_5V    # 5V power input
    usb_connector["GND"] += GND        # Ground connection
    usb_connector["DP1"] += USB_DP     # D+ data line
    usb_connector["DM1"] += USB_DM     # D- data line
    
    # === DECOUPLING CAPACITORS ===
    # Additional decoupling for the ESP32
    esp32_cap = Component(
        symbol="Device:C",
        ref="C", 
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    esp32_cap[1] += VCC_3V3
    esp32_cap[2] += GND


if __name__ == "__main__":
    """
    Generate the complete development board.
    """
    print("🚀 Generating ESP32 development board...")
    
    # Create the complete circuit
    board = esp32_development_board()
    
    # Generate KiCad project files
    board.generate_kicad_project("esp32_dev_board", force_regenerate=True)
    
    # Generate additional output formats
    board.generate_json_netlist("esp32_dev_board.json")
    board.generate_kicad_netlist("esp32_dev_board.net")
    
    print("✅ ESP32 development board generated successfully!")
    print("📁 Files created:")
    print("   - esp32_dev_board.kicad_pro")
    print("   - esp32_dev_board.kicad_sch") 
    print("   - esp32_dev_board.kicad_pcb")
    print("   - esp32_dev_board.json")
    print("   - esp32_dev_board.net")