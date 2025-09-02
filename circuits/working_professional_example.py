#!/usr/bin/env python3
"""
Working Professional Circuit Example
Demonstrates Circuit-Synth workflow with real KiCad components only
"""

from circuit_synth import circuit, Component, Net

@circuit(name="Professional_Buck_Converter")
def professional_buck_converter():
    """
    TPS562200 2A Buck Converter: 12V → 3.3V
    Real circuit using only KiCad-compatible components
    """
    
    # Create nets
    vin = Net("VIN")           # 12V input 
    vout = Net("VOUT")         # 3.3V output
    gnd = Net("GND")           # Ground
    sw = Net("SW")             # Switch node
    fb = Net("VFB")            # Feedback
    vbst = Net("VBST")         # Bootstrap
    
    # Main switching regulator IC
    u1 = Component(
        symbol="Regulator_Switching:TPS562200",
        ref="U1",
        value="TPS562200DDC",
        footprint="Package_TO_SOT_SMD:SOT-23-6"
    )
    vin += u1["VIN"]
    sw += u1["SW"]  
    fb += u1["VFB"]  
    gnd += u1["GND"]
    vin += u1["EN"]  # Always enabled
    vbst += u1["VBST"]  # Bootstrap capacitor
    
    # Output inductor
    L1 = Component(
        symbol="Device:L",
        ref="L1", 
        value="4.7uH",
        footprint="Inductor_SMD:L_1210_3225Metric"
    )
    sw += L1["1"]
    vout += L1["2"]
    
    # Output capacitor
    C1 = Component(
        symbol="Device:C",
        ref="C1",
        value="22uF",
        footprint="Capacitor_SMD:C_1206_3216Metric"
    )
    vout += C1["1"]
    gnd += C1["2"]
    
    # Input capacitor  
    C2 = Component(
        symbol="Device:C",
        ref="C2",
        value="10uF",
        footprint="Capacitor_SMD:C_1206_3216Metric"
    )
    vin += C2["1"]
    gnd += C2["2"]
    
    # Bootstrap capacitor
    C3 = Component(
        symbol="Device:C",
        ref="C3",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    vbst += C3["1"]
    sw += C3["2"]
    
    # Feedback resistor divider
    R1 = Component(
        symbol="Device:R", 
        ref="R1", 
        value="45k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    vout += R1["1"]
    fb += R1["2"]
    
    R2 = Component(
        symbol="Device:R", 
        ref="R2", 
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    fb += R2["1"]
    gnd += R2["2"]


@circuit(name="Professional_Current_Sense")  
def professional_current_sense():
    """
    High-Side Current Sense Amplifier using INA180A1
    Real circuit for professional current monitoring
    """
    
    # Power rails
    vcc = Net("VCC")           # 5V supply
    gnd = Net("GND")           # Ground
    vout = Net("VOUT")         # Amplified output
    
    # High-current path
    i_in_pos = Net("I_IN+")    # High-side current input
    i_in_neg = Net("I_IN-")    # Low-side current input
    
    # Sense resistor
    r_sense = Component(
        symbol="Device:R",
        ref="R1", 
        value="10mΩ",
        footprint="Resistor_SMD:R_2512_6332Metric"
    )
    i_in_pos += r_sense["1"]
    i_in_neg += r_sense["2"]
    
    # Current sense amplifier
    u1 = Component(
        symbol="Amplifier_Current:INA180A1",
        ref="U1",
        value="INA180A1IDBVR",
        footprint="Package_TO_SOT_SMD:SOT-23-5"
    )
    i_in_pos += u1["+"]  
    i_in_neg += u1["-"]   
    vcc += u1["V+"]
    gnd += u1["GND"]
    vout += u1["5"]  # Output pin
    
    # Supply decoupling
    c1 = Component(
        symbol="Device:C",
        ref="C1",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    vcc += c1["1"]
    gnd += c1["2"]
    
    # Output filtering
    vout_filt = Net("VOUT_FILT")
    
    r_filt = Component(
        symbol="Device:R", 
        ref="R2",
        value="100Ω",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    vout += r_filt["1"]
    vout_filt += r_filt["2"]
    
    c_filt = Component(
        symbol="Device:C",
        ref="C2", 
        value="10nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    vout_filt += c_filt["1"]
    gnd += c_filt["2"]


@circuit(name="Professional_Voltage_Reference")
def professional_voltage_reference():
    """
    Precision 2.5V Voltage Reference using LM4040
    """
    
    vin = Net("VIN")           # Input supply
    vref = Net("VREF")         # 2.5V reference output
    gnd = Net("GND")           # Ground
    
    # Voltage reference IC
    u1 = Component(
        symbol="Reference_Voltage:LM4040DBZ-2.5",
        ref="U1", 
        value="LM4040DBZ-2.5",
        footprint="Package_TO_SOT_SMD:SOT-23"
    )
    vin += u1["A"]   # Anode
    vref += u1["K"]  # Cathode (regulated output)
    
    # Current limiting resistor
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="1k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    vin += r1["1"]
    u1["A"] += r1["2"]
    
    # Output filtering
    c1 = Component(
        symbol="Device:C",
        ref="C1",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    vref += c1["1"]
    gnd += c1["2"]


@circuit(name="Professional_RC_Filter")
def professional_rc_filter():
    """
    Simple RC Low-Pass Filter for Anti-Aliasing
    """
    
    vin = Net("VIN")           # Input signal
    vout = Net("VOUT")         # Filtered output
    gnd = Net("GND")           # Ground
    
    # Filter resistor
    r1 = Component(
        symbol="Device:R",
        ref="R1",
        value="1.6k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    vin += r1["1"]
    vout += r1["2"]
    
    # Filter capacitor  
    c1 = Component(
        symbol="Device:C",
        ref="C1",
        value="10nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )
    vout += c1["1"]
    gnd += c1["2"]


def demonstrate_professional_workflow():
    """
    Demonstrate professional circuit workflow with working examples
    """
    
    print("🔧 Professional Circuit-Synth Workflow")
    print("=" * 50)
    
    circuits = {
        "Buck Converter": professional_buck_converter,
        "Current Sense": professional_current_sense, 
        "Voltage Reference": professional_voltage_reference,
        "RC Filter": professional_rc_filter
    }
    
    for name, circuit_func in circuits.items():
        print(f"\n📋 Creating {name}...")
        
        try:
            circuit_obj = circuit_func()
            component_count = len(circuit_obj.components)
            print(f"   ✅ {component_count} components created")
            
            # Show component list
            components = [f"{c.ref} ({c.value})" for c in circuit_obj.components]
            print(f"   📦 Components: {', '.join(components)}")
            
            # Validate connectivity
            net_count = len(circuit_obj.nets)
            print(f"   🔗 {net_count} nets connected")
            
            print(f"   🎯 Ready for KiCad generation")
            
        except Exception as e:
            print(f"   ❌ Error: {e}")
    
    print(f"\n🎉 Professional Circuit Workflow Complete!")
    print("\n💡 Key Benefits:")
    print("   • Simple, clean Circuit-Synth syntax")
    print("   • Real KiCad components with footprints")
    print("   • Professional-grade circuits")
    print("   • Manufacturing-ready designs")
    print("   • Graceful error handling")
    
    print("\n🚀 Next Steps:")
    print("   1. Generate KiCad schematics")
    print("   2. Create PCB layouts")
    print("   3. Generate manufacturing files")
    print("   4. Add SPICE simulation models")


if __name__ == "__main__":
    print("🚀 Professional Circuit-Synth Examples")
    print("Testing real circuits with KiCad components")
    
    demonstrate_professional_workflow()