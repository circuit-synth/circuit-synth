#!/usr/bin/env python3
"""
Simple test script for Rust KiCad S-expression generation.
This creates a minimal schematic with a resistor and capacitor.
"""

import sys
import os

# Add the path to find the rust module
sys.path.insert(0, '/Users/shanemattner/Desktop/circuit-synth3/.venv/lib/python3.12/site-packages')

try:
    import rust_kicad_schematic_writer
    print("✅ Rust module loaded successfully")
except ImportError as e:
    print(f"❌ Failed to import rust module: {e}")
    print("Make sure the Rust module is compiled and installed")
    sys.exit(1)

def create_simple_circuit():
    """Create a simple test circuit with a resistor and capacitor."""
    
    # Define circuit data dictionary
    circuit_data = {
        "name": "test_circuit",
        "components": [
            {
                "reference": "R1",
                "lib_id": "Device:R",
                "value": "10k",
                "position": {"x": 100.0, "y": 100.0},
                "rotation": 0.0,
                "pins": [
                    {"number": "1", "name": "~", "x": 0.0, "y": 3.81, "orientation": 270.0},
                    {"number": "2", "name": "~", "x": 0.0, "y": -3.81, "orientation": 90.0},
                ]
            },
            {
                "reference": "C1",
                "lib_id": "Device:C",
                "value": "100nF",
                "position": {"x": 150.0, "y": 100.0},
                "rotation": 0.0,
                "pins": [
                    {"number": "1", "name": "~", "x": 0.0, "y": 0.95, "orientation": 270.0},
                    {"number": "2", "name": "~", "x": 0.0, "y": -0.95, "orientation": 90.0},
                ]
            }
        ],
        "nets": [
            {
                "name": "VCC",
                "connected_pins": [
                    {"component_ref": "R1", "pin_id": "1"},
                    {"component_ref": "C1", "pin_id": "1"}
                ]
            },
            {
                "name": "GND",
                "connected_pins": [
                    {"component_ref": "R1", "pin_id": "2"},
                    {"component_ref": "C1", "pin_id": "2"}
                ]
            }
        ],
        "subcircuits": []  # No subcircuits for this simple test
    }
    
    # Optional configuration
    config = {
        "uuid": "test-schematic-uuid",
        "paper_size": "A4"
    }
    
    return circuit_data, config

def main():
    """Main test function."""
    print("\n=== Testing Rust KiCad S-expression Generation ===\n")
    
    # Create test circuit
    circuit_data, config = create_simple_circuit()
    print(f"📊 Created circuit with {len(circuit_data['components'])} components")
    
    try:
        # Method 1: Using the writer class
        print("\n--- Method 1: Using PyRustSchematicWriter ---")
        writer = rust_kicad_schematic_writer.PyRustSchematicWriter(circuit_data, config)
        print("✅ Writer created successfully")
        
        # Generate hierarchical labels
        labels = writer.generate_hierarchical_labels()
        print(f"📍 Generated {len(labels)} hierarchical labels")
        
        # Generate S-expression
        sexp = writer.generate_schematic_sexp()
        print(f"📝 Generated S-expression: {len(sexp)} characters")
        
        # Save to file
        output_file = "test_schematic_rust.kicad_sch"
        writer.write_to_file(output_file)
        print(f"💾 Saved to {output_file}")
        
        # Show first 30 lines
        print("\n--- First 30 lines of generated schematic ---")
        lines = sexp.split('\n')
        for i, line in enumerate(lines[:30], 1):
            print(f"{i:3}: {line}")
        
        if len(lines) > 30:
            print(f"... ({len(lines) - 30} more lines)")
        
        # Method 2: Using standalone function
        print("\n--- Method 2: Using standalone function ---")
        sexp2 = rust_kicad_schematic_writer.generate_schematic_from_python(circuit_data, config)
        print(f"📝 Generated S-expression: {len(sexp2)} characters")
        
        # Verify both methods produce same result
        if sexp == sexp2:
            print("✅ Both methods produce identical output")
        else:
            print("⚠️  Methods produce different output!")
        
        # Check for proper format
        print("\n--- Format Validation ---")
        print(f"✅ Starts with (kicad_sch: {sexp.startswith('(kicad_sch')}")
        print(f"✅ Contains Device:R: {('Device:R' in sexp)}")
        print(f"✅ Contains Device:C: {('Device:C' in sexp)}")
        print(f"✅ No dotted pairs: {('. \"' not in sexp)}")
        print(f"✅ Has hierarchical labels: {('hierarchical_label' in sexp)}")
        
        print("\n✨ Test completed successfully!")
        print(f"\n📄 You can now open '{output_file}' in KiCad to verify it works.")
        
    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0

if __name__ == "__main__":
    sys.exit(main())