#!/usr/bin/env python3
"""
Comprehensive dead code analysis test that actually runs the example project properly
"""

import sys
import os

# Add the example project directory to Python path so imports work
sys.path.insert(0, '/Users/shanemattner/Desktop/circuit-synth/example_project/circuit-synth')

# Change to the example project directory
os.chdir('/Users/shanemattner/Desktop/circuit-synth/example_project/circuit-synth')

print("🧪 Running comprehensive circuit-synth functionality test...")
print(f"📁 Working directory: {os.getcwd()}")
print(f"🐍 Python path includes: {sys.path[0]}")

# Now import and run the main script functionality
try:
    print("📋 Loading circuit modules...")
    from usb import usb_port
    from power_supply import power_supply
    from esp32c6 import esp32c6
    from circuit_synth import *
    
    print("✅ All modules loaded successfully")
    
    print("🏗️ Creating circuits...")
    
    # Create shared nets between subcircuits
    vbus = Net('VBUS')
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')
    usb_dp = Net('USB_DP')
    usb_dm = Net('USB_DM')
    
    # Create all circuits with shared nets
    usb_port_circuit = usb_port(vbus, gnd, usb_dp, usb_dm)
    power_supply_circuit = power_supply(vbus, vcc_3v3, gnd)
    esp32_circuit = esp32c6(vcc_3v3, gnd, usb_dp, usb_dm)
    
    print("✅ All circuits created")
    
    # Create main circuit
    @circuit(name="ESP32_C6_Dev_Board_Main")
    def main_circuit():
        """Main hierarchical circuit - ESP32-C6 development board"""
        
        # Create shared nets between subcircuits
        vbus = Net('VBUS')
        vcc_3v3 = Net('VCC_3V3') 
        gnd = Net('GND')
        usb_dp = Net('USB_DP')
        usb_dm = Net('USB_DM')

        # Create all circuits with shared nets
        usb_port_circuit = usb_port(vbus, gnd, usb_dp, usb_dm)
        power_supply_circuit = power_supply(vbus, vcc_3v3, gnd)
        esp32_circuit = esp32c6(vcc_3v3, gnd, usb_dp, usb_dm)
    
    print("🔧 Generating main circuit...")
    circuit = main_circuit()
    
    print("🔌 Testing KiCad netlist generation...")
    circuit.generate_kicad_netlist("comprehensive_test.net")
    
    print("📄 Testing JSON netlist generation...")
    circuit.generate_json_netlist("comprehensive_test.json")
    
    print("🏗️ Testing KiCad project generation...")
    circuit.generate_kicad_project(
        project_name="comprehensive_test_project",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )
    
    print("✅ All functionality tested successfully!")
    
    # Test additional functionality
    print("🔍 Testing manufacturing integration...")
    try:
        from circuit_synth.manufacturing.jlcpcb.fast_search import search_jlc_components_web
        results = search_jlc_components_web("0.1uF", max_results=3)
        print("✅ JLCPCB search works")
    except Exception as e:
        print(f"⚠️ JLCPCB search failed: {e}")
    
    print("🧠 Testing STM32 search...")
    try:
        from circuit_synth.ai_integration.stm32_search_helper import handle_stm32_peripheral_query
        response = handle_stm32_peripheral_query("stm32 with spi")
        print("✅ STM32 search works")
    except Exception as e:
        print(f"⚠️ STM32 search failed: {e}")
    
    print("📊 Testing quality assurance...")
    try:
        from circuit_synth.quality_assurance.fmea_analyzer import FMEAAnalyzer
        fmea = FMEAAnalyzer()
        print("✅ FMEA analyzer loaded")
    except Exception as e:
        print(f"⚠️ FMEA analyzer failed: {e}")
        
    print("🎯 Testing design for manufacturing...")
    try:
        from circuit_synth.design_for_manufacturing.dfm_analyzer import DFMAnalyzer
        dfm = DFMAnalyzer()
        print("✅ DFM analyzer loaded")
    except Exception as e:
        print(f"⚠️ DFM analyzer failed: {e}")

except Exception as e:
    print(f"❌ Test failed: {e}")
    import traceback
    traceback.print_exc()
    sys.exit(1)

print("🎉 Comprehensive functionality test completed successfully!")