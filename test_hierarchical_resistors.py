#!/usr/bin/env python3
"""
Multi-hierarchical test circuit with resistor dividers on every sheet.
This will be used to test preservation of manual KiCad edits.

Structure:
- Main circuit
  - Power input subcircuit (resistor divider)
  - Signal processing subcircuit
    - Filter stage (resistor divider)
    - Amplifier stage (resistor divider)
  - Output stage (resistor divider)
"""

from circuit_synth import Circuit, Component, Net, circuit

# Level 3: Filter stage with resistor divider
@circuit(name="filter_stage")
def filter_stage(vcc, gnd, signal_in, signal_out):
    """Simple RC filter with resistor divider biasing"""
    # Bias resistor divider
    R1 = Component("Device:R", ref="R", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    R2 = Component("Device:R", ref="R", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    
    # Filter components
    R3 = Component("Device:R", ref="R", value="1k", footprint="Resistor_SMD:R_0603_1608Metric")
    C1 = Component("Device:C", ref="C", value="100nF", footprint="Capacitor_SMD:C_0603_1608Metric")
    
    # Bias divider
    R1[1] += vcc
    R1[2] += signal_out
    R2[1] += signal_out
    R2[2] += gnd
    
    # Filter
    R3[1] += signal_in
    R3[2] += signal_out
    C1[1] += signal_out
    C1[2] += gnd

# Level 3: Amplifier stage with resistor divider
@circuit(name="amplifier_stage")
def amplifier_stage(vcc, gnd, amp_in, amp_out):
    """Simple amplifier with gain-setting resistor divider"""
    # Gain resistor divider
    R1 = Component("Device:R", ref="R", value="100k", footprint="Resistor_SMD:R_0603_1608Metric")
    R2 = Component("Device:R", ref="R", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    
    # Input resistor
    R3 = Component("Device:R", ref="R", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    
    # Feedback divider (sets gain)
    R1[1] += amp_out
    R1[2] += amp_in
    R2[1] += amp_in
    R2[2] += gnd
    
    # Input coupling
    R3[1] += vcc
    R3[2] += amp_out

# Level 2: Signal processing subcircuit
@circuit(name="signal_processing")
def signal_processing(vcc, gnd, proc_in, proc_out):
    """Signal processing with filter and amplifier stages"""
    # Internal nets
    filtered = Net("FILTERED")
    
    # Instantiate subcircuits
    filter_stage(vcc, gnd, proc_in, filtered)
    amplifier_stage(vcc, gnd, filtered, proc_out)

# Level 2: Power input subcircuit
@circuit(name="power_input")
def power_input(vin, vcc, gnd):
    """Power input with voltage divider for monitoring"""
    # Voltage monitoring divider
    R1 = Component("Device:R", ref="R", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    R2 = Component("Device:R", ref="R", value="1k", footprint="Resistor_SMD:R_0603_1608Metric")
    
    # Monitor point
    monitor = Net("V_MONITOR")
    
    # Divider for voltage monitoring
    R1[1] += vin
    R1[2] += monitor
    R2[1] += monitor
    R2[2] += gnd
    
    # Direct connection (in real circuit would have regulator)
    # For testing, just connect vin to vcc
    vin += vcc

# Level 2: Output stage
@circuit(name="output_stage")
def output_stage(vcc, gnd, stage_in, stage_out):
    """Output stage with resistor divider for level shifting"""
    # Output level shifter divider
    R1 = Component("Device:R", ref="R", value="2.2k", footprint="Resistor_SMD:R_0603_1608Metric")
    R2 = Component("Device:R", ref="R", value="3.3k", footprint="Resistor_SMD:R_0603_1608Metric")
    
    # Output coupling
    R3 = Component("Device:R", ref="R", value="100", footprint="Resistor_SMD:R_0603_1608Metric")
    
    # Level shifter
    R1[1] += vcc
    R1[2] += stage_out
    R2[1] += stage_out
    R2[2] += gnd
    
    # Coupling
    R3[1] += stage_in
    R3[2] += stage_out

# Level 1: Main circuit
@circuit(name="main_circuit")
def main_circuit():
    """Main circuit that ties everything together"""
    # Power nets
    vin = Net("VIN")
    vcc = Net("VCC")
    gnd = Net("GND")
    
    # Signal nets
    input_signal = Net("INPUT")
    processed = Net("PROCESSED")
    output = Net("OUTPUT")
    
    # Power connector
    J1 = Component("Connector:Barrel_Jack_Switch", ref="J", 
                   footprint="Connector_BarrelJack:BarrelJack_Horizontal")
    J1[1] += vin
    J1[2] += gnd
    J1[3] += gnd
    
    # Input connector
    J2 = Component("Connector_Generic:Conn_01x02", ref="J",
                   footprint="Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical")
    J2[1] += input_signal
    J2[2] += gnd
    
    # Output connector  
    J3 = Component("Connector_Generic:Conn_01x02", ref="J",
                   footprint="Connector_PinHeader_2.54mm:PinHeader_1x02_P2.54mm_Vertical")
    J3[1] += output
    J3[2] += gnd
    
    # Instantiate all subcircuits
    power_input(vin, vcc, gnd)
    signal_processing(vcc, gnd, input_signal, processed)
    output_stage(vcc, gnd, processed, output)
    
    # Add some decoupling capacitors at the top level
    C1 = Component("Device:C", ref="C", value="10uF", footprint="Capacitor_SMD:C_0805_2012Metric")
    C2 = Component("Device:C", ref="C", value="100nF", footprint="Capacitor_SMD:C_0603_1608Metric")
    
    C1[1] += vcc
    C1[2] += gnd
    C2[1] += vcc
    C2[2] += gnd

if __name__ == "__main__":
    import os
    
    # Create the main circuit
    circuit = main_circuit()
    
    # Check if project already exists
    project_exists = os.path.exists("hierarchical_resistors_test/hierarchical_resistors_test.kicad_pro")
    
    if not project_exists:
        # First run - create new project
        print("Generating NEW multi-hierarchical KiCad project...")
        circuit.generate_kicad_project("hierarchical_resistors_test", force_regenerate=True)
        print("\n✅ Initial project generated!")
        print("\n📝 Next steps:")
        print("1. Open hierarchical_resistors_test/hierarchical_resistors_test.kicad_pro in KiCad")
        print("2. Make manual edits:")
        print("   - Move components around")
        print("   - Route wires manually")
        print("   - Add text annotations")
        print("   - Change component orientations")
        print("3. Save your changes in KiCad")
        print("4. Run this script again to test preservation")
    else:
        # Second run - update existing project WITHOUT regenerating
        print("🔄 UPDATING existing KiCad project (preserving manual edits)...")
        print("Using force_regenerate=False to preserve your manual work")
        circuit.generate_kicad_project("hierarchical_resistors_test", force_regenerate=False)
        print("\n✅ Project updated!")
        print("\n⚠️  IMPORTANT: Check that your manual edits were preserved:")
        print("- Component positions should be unchanged")
        print("- Manual wire routing should be preserved")
        print("- Text annotations should still be there")
        print("- Any other manual changes should remain")