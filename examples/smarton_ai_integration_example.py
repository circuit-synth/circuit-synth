#!/usr/bin/env python3
"""
Smarton AI Integration Example

This example demonstrates how to use the Smarton AI plugin integration
with circuit-synth for intelligent circuit design assistance.
"""

from circuit_synth import Circuit, Component, Net, circuit
from circuit_synth.plugins import SmartonAIBridge


@circuit(name="smarton_ai_example")
def create_example_circuit():
    """
    Example circuit that demonstrates Smarton AI integration.
    
    This creates a simple LED circuit with current limiting resistor.
    The Smarton AI plugin can provide intelligent suggestions for
    component values and layout optimization.
    """
    
    # Create components
    led = Component(
        symbol="Device:LED",
        ref="D",
        footprint="LED_SMD:LED_0603_1608Metric",
        value="Red LED"
    )
    
    resistor = Component(
        symbol="Device:R", 
        ref="R",
        footprint="Resistor_SMD:R_0603_1608Metric",
        value="330R"
    )
    
    # Power connections
    VCC = Net('VCC_3V3')
    GND = Net('GND')
    LED_CATHODE = Net('LED_CATHODE')
    
    # Connect circuit
    VCC += resistor[1]        # VCC to resistor
    resistor[2] += led["A"]   # Resistor to LED anode  
    led["K"] += GND           # LED cathode to ground


def main():
    """Main example function."""
    print("Smarton AI Integration Example")
    print("=" * 40)
    
    # Create the bridge to Smarton AI
    bridge = SmartonAIBridge()
    
    # Check plugin status
    print("\n1. Checking Smarton AI Plugin Status:")
    status = bridge.get_plugin_status()
    
    print(f"   Plugin path exists: {'✓' if status['plugin_exists'] else '✗'}")
    print(f"   KiCad plugin dir: {status['kicad_plugin_dir']}")
    print(f"   Plugin installed: {'✓' if status['plugin_installed'] else '✗'}")
    
    # Install plugin if not already installed
    if not status['plugin_installed']:
        print("\n2. Installing Smarton AI Plugin:")
        if bridge.install_plugin():
            print("   ✓ Plugin installed successfully!")
        else:
            print("   ✗ Plugin installation failed")
            return
    else:
        print("\n2. Plugin already installed ✓")
        
    # Generate circuit with AI hints
    print("\n3. Generating Circuit with AI Assistance:")
    circuit_desc = "Simple LED circuit with current limiting resistor for 3.3V supply"
    ai_result = bridge.generate_circuit_with_ai_hints(circuit_desc)
    
    print(f"   Description: {circuit_desc}")
    print("   AI-suggested circuit code generated ✓")
    
    # Create the actual circuit
    print("\n4. Creating Example Circuit:")
    circuit_instance = create_example_circuit()
    print("   ✓ Circuit created successfully!")
    print(f"   Components: {len(circuit_instance.components)}")
    print(f"   Nets: {len(circuit_instance.nets)}")
    
    print("\n5. Next Steps:")
    print("   • Restart KiCad if it was open")
    print("   • Open PCB editor")
    print("   • Look for 'Basic Operation' and 'Chat' plugins in Tools menu")
    print("   • Use the AI assistant for intelligent design guidance")


if __name__ == "__main__":
    main()