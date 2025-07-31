#!/usr/bin/env python3
"""
Simplest possible PSPICE integration example for circuit-synth.

This example demonstrates basic SPICE simulation capability using a simple
resistor divider circuit. It shows how to:
1. Create a basic circuit with circuit-synth
2. Convert it to SPICE format
3. Run a basic DC analysis
4. Display the results

Usage:
    python simple_pspice_example.py
"""

import sys
import os

# Add the source directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from circuit_synth import Circuit, Component, Net, circuit

# Check if PySpice is available and configure ngspice library path
try:
    import PySpice
    from PySpice.Spice.Netlist import Circuit as SpiceCircuit
    from PySpice.Unit import *
    from PySpice.Spice.NgSpice.Shared import NgSpiceShared
    
    # Configure ngspice library path for macOS homebrew installation
    import os
    import platform
    if platform.system() == 'Darwin':  # macOS
        # Try common homebrew paths
        possible_paths = [
            '/opt/homebrew/lib/libngspice.dylib',  # Apple Silicon
            '/usr/local/lib/libngspice.dylib',     # Intel Mac
        ]
        for path in possible_paths:
            if os.path.exists(path):
                NgSpiceShared.LIBRARY_PATH = path
                break
    
    PSPICE_AVAILABLE = True
    print("✅ PySpice found - simulation enabled")
except ImportError:
    PSPICE_AVAILABLE = False
    print("❌ PySpice not found - install with: pip install PySpice")


@circuit
def simple_resistor_divider():
    """
    Simple resistor divider: VIN -> R1(10k) -> VOUT -> R2(10k) -> GND
    Expected VOUT = 2.5V with VIN = 5V
    
    This creates the circuit topology that will be converted to SPICE.
    The voltage source will be added during SPICE conversion.
    """
    
    # Create resistors only - voltage source added in SPICE conversion
    r1 = Component(
        symbol="Device:R", 
        ref="R", 
        value="10k",
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    r2 = Component(
        symbol="Device:R", 
        ref="R", 
        value="10k", 
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    
    # Create nets
    vin_net = Net('VIN')
    vout_net = Net('VOUT') 
    gnd_net = Net('GND')
    
    # Connect the resistor divider
    r1[1] += vin_net
    r1[2] += vout_net
    
    r2[1] += vout_net
    r2[2] += gnd_net


def create_spice_circuit(circuit_synth_circuit):
    """
    Convert a circuit-synth circuit to PySpice format.
    This is a basic implementation for the resistor divider example.
    """
    if not PSPICE_AVAILABLE:
        raise ImportError("PySpice not available")
    
    # Create PySpice circuit
    spice_circuit = SpiceCircuit('SimpleResistorDivider')
    
    # Add voltage source: 5V DC (GND is implicit in PySpice)
    spice_circuit.V('supply', 'VIN', spice_circuit.gnd, 5@u_V)
    
    # Add resistors: 10k each
    spice_circuit.R('1', 'VIN', 'VOUT', 10@u_kΩ)
    spice_circuit.R('2', 'VOUT', spice_circuit.gnd, 10@u_kΩ)
    
    return spice_circuit


def run_simple_simulation():
    """Run the simplest possible simulation."""
    
    print("\n🔌 Creating circuit-synth resistor divider...")
    
    # Create the circuit
    circuit = simple_resistor_divider()
    
    print("✅ Circuit created successfully")
    print(f"   Components: {len(circuit.components)}")
    print(f"   Nets: {len(circuit.nets)}")
    
    # Generate netlists for verification
    try:
        circuit.generate_json_netlist("simple_resistor_divider.json")
        print("✅ JSON netlist generated: simple_resistor_divider.json")
    except Exception as e:
        print(f"⚠️  JSON netlist generation failed: {e}")
    
    if not PSPICE_AVAILABLE:
        print("\n❌ PySpice not available - cannot run simulation")
        print("Install with: pip install PySpice")
        return
    
    print("\n⚡ Converting to SPICE format...")
    
    try:
        # Convert to PySpice format
        spice_circuit = create_spice_circuit(circuit)
        print("✅ SPICE circuit created")
        
        # Create simulator
        simulator = spice_circuit.simulator(temperature=25, nominal_temperature=25)
        print("✅ Simulator created")
        
        # Run DC operating point analysis
        print("\n📊 Running DC analysis...")
        analysis = simulator.operating_point()
        
        # Display results
        print("\n🎯 Simulation Results:")
        print(f"   VIN = {float(analysis['VIN']):.3f} V")
        print(f"   VOUT = {float(analysis['VOUT']):.3f} V")
        print(f"   Expected VOUT = 2.500 V")
        
        # Verify result
        vout_actual = float(analysis['VOUT'])
        vout_expected = 2.5
        error = abs(vout_actual - vout_expected)
        
        if error < 0.001:
            print(f"✅ Simulation PASSED (error: {error:.6f} V)")
        else:
            print(f"❌ Simulation FAILED (error: {error:.3f} V)")
            
    except Exception as e:
        print(f"❌ Simulation failed: {e}")
        import traceback
        traceback.print_exc()


if __name__ == '__main__':
    print("🚀 Circuit-Synth Simple PSPICE Integration Example")
    print("=" * 50)
    
    run_simple_simulation()
    
    print("\n" + "=" * 50)
    print("🎯 Example completed!")
    
    if PSPICE_AVAILABLE:
        print("\n💡 Next steps:")
        print("   1. Try modifying resistor values")  
        print("   2. Add more complex circuits")
        print("   3. Explore AC and transient analysis")
    else:
        print("\n💡 To enable simulation:")
        print("   pip install PySpice")