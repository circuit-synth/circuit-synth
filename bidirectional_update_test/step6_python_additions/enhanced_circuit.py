#!/usr/bin/env python3
"""
Step 6: Python Circuit Additions - Enhanced ESP32 Development Board

This circuit extends the existing ESP32 + capacitor from previous steps by adding:
1. 3.3V LDO voltage regulator with input/output capacitors
2. USB-C connector for power and programming
3. Status LED with current limiting resistor
4. Additional decoupling capacitors

This tests the bidirectional workflow's ability to integrate:
- Original components (ESP32 + C1 from Steps 1-4)
- Manual KiCad edits (component positions from Step 3)
- New Python components (power supply, USB, LED - from Step 6)

Expected behavior with force_regenerate=False:
- Preserve existing component positions from manual KiCad edits
- Add new components with intelligent placement
- Maintain all circuit topology and connections
"""

from circuit_synth import *

@circuit(name="enhanced_esp32_board")
def enhanced_esp32_development_board():
    """
    Enhanced ESP32 development board with power management and connectivity.
    
    Features:
    - ESP32-C6-MINI-1 microcontroller module
    - USB-C connector for power and programming
    - 3.3V LDO voltage regulator (AMS1117-3.3)
    - Input/output filtering capacitors
    - Power status LED indicator
    - Additional decoupling capacitors
    """
    
    # ====== EXISTING COMPONENTS (preserve from Steps 1-4) ======
    # These components should match what exists in KiCad from previous steps
    
    # Power nets
    _3v3 = Net('+3V3')
    gnd = Net('GND')
    
    # Existing components - MUST match references from previous steps
    c1 = Component(
        symbol="Device:C", 
        ref="C1", 
        value="C", 
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    u1 = Component(
        symbol="RF_Module:ESP32-C6-MINI-1", 
        ref="U1", 
        value="ESP32-C6-MINI-1", 
        footprint="RF_Module:ESP32-C6-MINI-1"
    )
    
    # Existing connections - preserve from previous steps
    c1[1] += _3v3
    u1[3] += _3v3  # ESP32 3V3 power pin
    c1[2] += gnd
    
    # All ESP32 ground connections from previous steps
    u1[1] += gnd
    u1[11] += gnd
    u1[14] += gnd
    u1[2] += gnd
    u1[36] += gnd
    u1[37] += gnd
    u1[38] += gnd
    u1[39] += gnd
    u1[40] += gnd
    u1[41] += gnd
    u1[42] += gnd
    u1[43] += gnd
    u1[44] += gnd
    u1[45] += gnd
    u1[46] += gnd
    u1[47] += gnd
    u1[48] += gnd
    u1[49] += gnd
    u1[50] += gnd
    u1[51] += gnd
    u1[52] += gnd
    u1[53] += gnd
    
    # ====== NEW COMPONENTS ADDED IN STEP 6 ======
    # These should be intelligently placed by the update system
    
    # Additional power nets
    vbus_5v = Net('VBUS_5V')  # USB 5V input
    led_anode = Net('LED_ANODE')  # LED connection
    
    # 1. USB-C Connector for power and programming
    usb_connector = Component(
        symbol="Connector:USB_C_Receptacle_USB2.0_16P",
        ref="J1",
        value="USB-C",
        footprint="Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12"
    )
    
    # 2. 3.3V LDO Voltage Regulator
    voltage_regulator = Component(
        symbol="Regulator_Linear:AMS1117-3.3",
        ref="U2",
        value="AMS1117-3.3", 
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )
    
    # 3. Input capacitor for voltage regulator (10uF)
    cap_input = Component(
        symbol="Device:C",
        ref="C2",
        value="10uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    
    # 4. Output capacitor for voltage regulator (22uF)
    cap_output = Component(
        symbol="Device:C", 
        ref="C3",
        value="22uF",
        footprint="Capacitor_SMD:C_0805_2012Metric"
    )
    
    # 5. Power status LED (green)
    status_led = Component(
        symbol="Device:LED",
        ref="D1", 
        value="Green LED",
        footprint="LED_SMD:LED_0603_1608Metric"
    )
    
    # 6. Current limiting resistor for LED (330 ohms)
    led_resistor = Component(
        symbol="Device:R",
        ref="R1",
        value="330R", 
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # 7. Additional ESP32 decoupling capacitor (100nF)
    cap_decouple = Component(
        symbol="Device:C",
        ref="C4",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    
    # ====== NEW COMPONENT CONNECTIONS ======
    
    # USB-C power input connections
    usb_connector["VBUS"] += vbus_5v    # USB 5V power
    usb_connector["GND"] += gnd         # USB ground
    # Note: USB data lines not connected in this simple power-only design
    
    # Voltage regulator power conversion: 5V USB → 3.3V regulated
    voltage_regulator["VI"] += vbus_5v   # Input: 5V from USB
    voltage_regulator["VO"] += _3v3      # Output: 3.3V to existing net
    voltage_regulator["GND"] += gnd      # Ground reference
    
    # Input capacitor: filters 5V USB power
    cap_input[1] += vbus_5v
    cap_input[2] += gnd
    
    # Output capacitor: stabilizes 3.3V regulated output  
    cap_output[1] += _3v3
    cap_output[2] += gnd
    
    # Power status LED circuit: indicates 3.3V rail is active
    led_resistor[1] += _3v3              # LED resistor from 3.3V
    led_resistor[2] += led_anode         # To LED anode
    status_led["A"] += led_anode         # LED anode
    status_led["K"] += gnd               # LED cathode to ground
    
    # Additional ESP32 decoupling: improves power supply noise rejection
    cap_decouple[1] += _3v3
    cap_decouple[2] += gnd


# Test the enhanced circuit generation
if __name__ == '__main__':
    circuit = enhanced_esp32_development_board()
    
    print("🔌 Step 6: Enhanced ESP32 Development Board")
    print("=" * 50)
    print("📋 Circuit Components:")
    print("   EXISTING (from Steps 1-4):")
    print("     - C1: Existing capacitor (preserve position)")
    print("     - U1: ESP32-C6-MINI-1 (preserve position)")
    print("   NEW (added in Step 6):")
    print("     - J1: USB-C connector")
    print("     - U2: 3.3V LDO regulator (AMS1117-3.3)")
    print("     - C2: Input capacitor (10uF)")
    print("     - C3: Output capacitor (22uF)")  
    print("     - D1: Power status LED (green)")
    print("     - R1: LED current limiting resistor (330R)")
    print("     - C4: Additional decoupling capacitor (100nF)")
    print()
    print("🔄 Testing UPDATE mode (should preserve existing positions)")
    print("   force_regenerate=False → preserve manual KiCad edits")
    print()
    
    # First generate the enhanced circuit into the existing project with manual edits
    # This tests true bidirectional integration: existing + manual + new components
    circuit.generate_kicad_project(
        project_name="enhanced_esp32_board_integration",
        force_regenerate=False  # CRITICAL: Use update mode to preserve existing work!
    )
    
    print("✅ Enhanced circuit generated successfully!")
    print("📍 Expected behavior:")
    print("   - C1, U1 positions preserved from Step 3 manual edits")
    print("   - New components (J1, U2, C2, C3, D1, R1, C4) placed intelligently")
    print("   - All connections maintained and extended")
    print("   - Power supply circuit fully integrated")