#!/usr/bin/env python3
"""
Circuit-Synth SPICE Simulation Demo

This example demonstrates the integrated SPICE simulation capabilities
using the built-in circuit-synth simulation API. Shows multiple analysis
types and proper circuit-synth patterns.

Usage:
    uv run examples/circuit_synth_simulation_demo.py
"""

from circuit_synth import Circuit, Component, Net, circuit

@circuit
def voltage_divider_with_load():
    """
    Voltage divider with load resistor to demonstrate simulation accuracy.
    
    Circuit: VIN (5V) -> R1 (4.7k) -> VOUT -> R2 (10k) || RLOAD (1M) -> GND
    Expected VOUT ≈ 3.37V (loaded divider)
    """
    
    # Create components
    r1 = Component("Device:R", ref="R", value="4.7k")  # Upper divider 
    r2 = Component("Device:R", ref="R", value="10k")   # Lower divider
    rload = Component("Device:R", ref="R", value="1M") # Load resistor
    
    # Create nets
    vin = Net('VIN')    # 5V supply (auto-detected by simulator)
    vout = Net('VOUT')  # Output voltage node
    gnd = Net('GND')    # Ground reference
    
    # Connect circuit
    r1[1] += vin
    r1[2] += vout
    
    r2[1] += vout  
    r2[2] += gnd
    
    rload[1] += vout  # Load in parallel with R2
    rload[2] += gnd


@circuit 
def rc_lowpass_filter():
    """
    Simple RC low-pass filter for AC analysis demonstration.
    
    Circuit: VIN -> R (1k) -> VOUT -> C (100nF) -> GND
    Cutoff frequency: ~1.6kHz
    """
    
    r1 = Component("Device:R", ref="R", value="1k")
    c1 = Component("Device:C", ref="C", value="100nF")
    
    vin = Net('VIN')
    vout = Net('VOUT') 
    gnd = Net('GND')
    
    r1[1] += vin
    r1[2] += vout
    
    c1[1] += vout
    c1[2] += gnd


def demo_dc_analysis():
    """Demonstrate DC operating point and sweep analysis."""
    print("🔌 DC Analysis Demo")
    print("=" * 40)
    
    # Create voltage divider circuit
    circuit = voltage_divider_with_load()
    
    print(f"📋 Circuit created: {len(circuit.components)} components, {len(circuit.nets)} nets")
    
    try:
        # Create simulator using built-in method
        sim = circuit.simulator()
        print("✅ Simulator created successfully")
        
        # Run operating point analysis
        print("\n📊 Running DC operating point analysis...")
        result = sim.operating_point()
        
        # Display results
        vin_voltage = result.get_voltage('VIN')
        vout_voltage = result.get_voltage('VOUT')
        
        print(f"   VIN = {vin_voltage:.3f} V")
        print(f"   VOUT = {vout_voltage:.3f} V")
        
        # Calculate expected result
        # Parallel resistance: R2 || RLOAD = 10k || 1M ≈ 9.90k
        r_parallel = (10e3 * 1e6) / (10e3 + 1e6)  # 9.901 kΩ
        expected_vout = 5.0 * r_parallel / (4.7e3 + r_parallel)
        
        print(f"   Expected VOUT = {expected_vout:.3f} V")
        
        error = abs(vout_voltage - expected_vout)
        if error < 0.01:
            print(f"✅ Analysis PASSED (error: {error:.6f} V)")
        else:
            print(f"❌ Analysis FAILED (error: {error:.3f} V)")
            
    except Exception as e:
        print(f"❌ Simulation failed: {e}")
        return False
    
    return True


def demo_ac_analysis():
    """Demonstrate AC frequency response analysis."""
    print("\n🌊 AC Analysis Demo")  
    print("=" * 40)
    
    # Create RC filter circuit
    circuit = rc_lowpass_filter()
    
    print(f"📋 Filter circuit created: {len(circuit.components)} components")
    
    try:
        sim = circuit.simulator()
        
        # Run AC analysis from 1Hz to 100kHz
        print("📊 Running AC frequency response (1Hz - 100kHz)...")
        result = sim.ac_analysis(1, 100000, 100)
        
        # Calculate theoretical cutoff frequency
        r_value = 1000  # 1kΩ
        c_value = 100e-9  # 100nF
        cutoff_freq = 1 / (2 * 3.14159 * r_value * c_value)
        
        print(f"   Theoretical cutoff frequency: {cutoff_freq:.1f} Hz")
        print("✅ AC analysis completed successfully")
        print("   💡 Use result.plot('VOUT') to visualize frequency response")
        
    except Exception as e:
        print(f"❌ AC simulation failed: {e}")
        return False
    
    return True


def demo_simulation_info():
    """Show circuit and simulation information."""
    print("\n🔧 Simulation Information")
    print("=" * 40)
    
    circuit = voltage_divider_with_load()
    sim = circuit.simulator()
    
    # List circuit components and nodes
    components = sim.list_components()
    nodes = sim.list_nodes()
    
    print(f"📋 Circuit Components: {components}")
    print(f"🔗 Circuit Nodes: {nodes}")
    
    # Show SPICE netlist
    netlist = sim.get_netlist()
    print(f"\n📝 Generated SPICE Netlist:")
    print("-" * 30)
    for line in netlist.split('\n')[:10]:  # First 10 lines
        if line.strip():
            print(f"   {line}")
    print("   ...")


def main():
    """Run all simulation demos."""
    print("🚀 Circuit-Synth SPICE Simulation Demo")
    print("=" * 50)
    
    # Check if simulation is available
    try:
        from circuit_synth.simulation import CircuitSimulator
        print("✅ Circuit-synth simulation module loaded")
    except ImportError as e:
        print(f"❌ Simulation not available: {e}")
        print("Install with: pip install circuit-synth[simulation]")
        return
    
    success_count = 0
    
    # Run DC analysis demo
    if demo_dc_analysis():
        success_count += 1
    
    # Run AC analysis demo  
    if demo_ac_analysis():
        success_count += 1
    
    # Show simulation info
    try:
        demo_simulation_info()
        success_count += 1
    except Exception as e:
        print(f"❌ Info demo failed: {e}")
    
    # Summary
    print("\n" + "=" * 50)
    print(f"🎯 Demo Results: {success_count}/3 tests passed")
    
    if success_count == 3:
        print("🎉 All simulations successful!")
        print("\n💡 Next steps:")
        print("   1. Try different component values")
        print("   2. Add more complex circuits (op-amps, etc.)")
        print("   3. Use result.plot() for visualization")
        print("   4. Explore transient analysis")
    else:
        print("⚠️  Some simulations failed - check dependencies")


if __name__ == '__main__':
    main()