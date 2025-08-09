#!/usr/bin/env python3
"""
Hierarchical circuit test for comprehensive dead code analysis.
Tests complex circuit hierarchies and all related functionality.
"""

# Import at module level
from circuit_synth import *

def test_power_supply_circuit():
    """Complete 5V to 3.3V regulator with protection"""
    
    print("⚡ Testing power supply circuit...")
    
    @circuit(name="power_supply_comprehensive")
    def power_supply():
        vreg = Component(symbol="Regulator_Linear:AMS1117-3.3", ref="U", 
                        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2")
        cap_in = Component(symbol="Device:C", ref="C", value="10uF", 
                          footprint="Capacitor_SMD:C_0805_2012Metric")
        cap_out = Component(symbol="Device:C", ref="C", value="22uF", 
                           footprint="Capacitor_SMD:C_0805_2012Metric")
        
        # Add power indicator LED
        led_power = Component(symbol="Device:LED", ref="D", 
                             footprint="LED_SMD:LED_0603_1608Metric")
        r_led = Component(symbol="Device:R", ref="R", value="1k",
                         footprint="Resistor_SMD:R_0603_1608Metric")
        
        # Create nets
        vin = Net('VIN_5V')
        vout = Net('VCC_3V3')
        gnd = Net('GND')
        
        # Connect regulator
        vreg["VI"] += vin
        vreg["VO"] += vout
        vreg["GND"] += gnd
        
        # Connect capacitors
        cap_in[1] += vin
        cap_in[2] += gnd
        cap_out[1] += vout
        cap_out[2] += gnd
        
        # Power indicator LED
        r_led[1] += vout
        r_led[2] += led_power["A"] 
        led_power["K"] += gnd
    
    circuit = power_supply()
    print("✅ Power supply circuit created")
    return circuit

def test_mcu_circuit():
    """MCU circuit with crystal and decoupling"""
    
    print("🔲 Testing MCU circuit...")
    
    @circuit(name="mcu_comprehensive")
    def mcu_circuit():
        # Use a simpler MCU for testing
        mcu = Component(symbol="MCU_ST_STM32F1:STM32F103C8Tx", ref="U",
                       footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm")
        
        # Crystal circuit
        crystal = Component(symbol="Device:Crystal", ref="Y", value="8MHz",
                           footprint="Crystal:Crystal_SMD_HC49-SD_HandSoldering")
        c1 = Component(symbol="Device:C", ref="C", value="22pF",
                       footprint="Capacitor_SMD:C_0603_1608Metric") 
        c2 = Component(symbol="Device:C", ref="C", value="22pF",
                       footprint="Capacitor_SMD:C_0603_1608Metric")
        
        # Decoupling capacitors
        bypass_caps = []
        for i in range(4):
            cap = Component(symbol="Device:C", ref="C", value="0.1uF",
                           footprint="Capacitor_SMD:C_0603_1608Metric")
            bypass_caps.append(cap)
        
        # Nets
        vcc = Net('VCC_3V3')
        gnd = Net('GND')
        osc_in = Net('OSC_IN')
        osc_out = Net('OSC_OUT')
        
        # Connect crystal
        crystal[1] += osc_in
        crystal[2] += osc_out
        c1[1] += osc_in
        c1[2] += gnd
        c2[1] += osc_out
        c2[2] += gnd
        
        # Connect MCU (simplified connections)
        mcu["VDD"] += vcc
        mcu["VSS"] += gnd
        mcu["PH0-OSC_IN"] += osc_in
        mcu["PH1-OSC_OUT"] += osc_out
        
        # Connect decoupling capacitors
        for cap in bypass_caps:
            cap[1] += vcc
            cap[2] += gnd
    
    circuit = mcu_circuit()
    print("✅ MCU circuit created")
    return circuit

def test_led_driver_circuit():
    """LED driver with current limiting"""
    
    print("💡 Testing LED driver circuit...")
    
    @circuit(name="led_driver_comprehensive")
    def led_driver():
        # Multiple LEDs with different colors
        led_red = Component(symbol="Device:LED", ref="D", 
                           footprint="LED_SMD:LED_0603_1608Metric")
        led_green = Component(symbol="Device:LED", ref="D", 
                             footprint="LED_SMD:LED_0603_1608Metric")
        led_blue = Component(symbol="Device:LED", ref="D", 
                            footprint="LED_SMD:LED_0603_1608Metric")
        
        # Current limiting resistors
        r_red = Component(symbol="Device:R", ref="R", value="330", 
                         footprint="Resistor_SMD:R_0603_1608Metric")
        r_green = Component(symbol="Device:R", ref="R", value="330", 
                           footprint="Resistor_SMD:R_0603_1608Metric")
        r_blue = Component(symbol="Device:R", ref="R", value="330", 
                          footprint="Resistor_SMD:R_0603_1608Metric")
        
        vcc = Net('VCC_3V3')
        gnd = Net('GND')
        
        # Connect red LED
        r_red[1] += vcc
        r_red[2] += led_red[1]
        led_red[2] += gnd
        
        # Connect green LED
        r_green[1] += vcc
        r_green[2] += led_green[1]
        led_green[2] += gnd
        
        # Connect blue LED
        r_blue[1] += vcc
        r_blue[2] += led_blue[1]
        led_blue[2] += gnd
    
    circuit = led_driver()
    print("✅ LED driver circuit created")
    return circuit

def test_complete_hierarchical_system():
    """Complete system integrating all subcircuits"""
    
    print("🏗️ Testing complete hierarchical system...")
    
    @circuit(name="complete_hierarchical_system")
    def complete_system():
        # Create shared nets
        vcc_3v3 = Net('VCC_3V3')
        gnd = Net('GND')
        vin_5v = Net('VIN_5V')
        
        # Instantiate subcircuits
        power = test_power_supply_circuit()
        mcu = test_mcu_circuit()  
        led_driver = test_led_driver_circuit()
        
        # Add connector
        power_connector = Component(symbol="Connector:Barrel_Jack_Switch", ref="J",
                                   footprint="Connector_BarrelJack:BarrelJack_Horizontal")
        
        # Connect power input
        power_connector["1"] += vin_5v
        power_connector["2"] += gnd
    
    system = complete_system()
    print("✅ Complete hierarchical system created")
    
    # Test hierarchical generation with all options
    try:
        system.generate_kicad_project("comprehensive_hierarchical", 
                                     placement_algorithm="hierarchical",
                                     generate_pcb=True)
        print("✅ Hierarchical KiCad project generated")
    except Exception as e:
        print(f"⚠️ Hierarchical KiCad generation failed: {e}")
    
    try:
        system.generate_json_netlist("hierarchical.json")
        print("✅ Hierarchical JSON netlist generated")
    except Exception as e:
        print(f"⚠️ Hierarchical JSON generation failed: {e}")
    
    return system

def test_pcb_placement_hierarchical():
    """Test PCB placement with hierarchical circuits"""
    print("📐 Testing hierarchical PCB placement...")
    
    system = test_complete_hierarchical_system()
    
    placement_algorithms = ["hierarchical", "force_directed", "spiral"]
    
    for algorithm in placement_algorithms:
        try:
            system.generate_kicad_project(f"hierarchical_{algorithm}",
                                         placement_algorithm=algorithm,
                                         generate_pcb=True)
            print(f"✅ Hierarchical placement with {algorithm}")
        except Exception as e:
            print(f"⚠️ Hierarchical placement {algorithm} failed: {e}")

def test_sheet_management():
    """Test hierarchical sheet management"""
    print("📄 Testing sheet management...")
    
    try:
        from circuit_synth.kicad.schematic.sheet_manager import SheetManager
        manager = SheetManager()
        print("✅ Sheet manager")
    except Exception as e:
        print(f"⚠️ Sheet manager failed: {e}")
    
    try:
        from circuit_synth.kicad.sheet_hierarchy_manager import SheetHierarchyManager
        hierarchy_mgr = SheetHierarchyManager()
        print("✅ Sheet hierarchy manager")
    except Exception as e:
        print(f"⚠️ Sheet hierarchy manager failed: {e}")

if __name__ == "__main__":
    print("🧪 Running hierarchical circuit comprehensive tests...")
    print("=" * 60)
    
    test_power_supply_circuit()
    test_mcu_circuit()
    test_led_driver_circuit()
    test_complete_hierarchical_system()
    test_pcb_placement_hierarchical()
    test_sheet_management()
    
    print("=" * 60)
    print("✅ Hierarchical circuit test completed")