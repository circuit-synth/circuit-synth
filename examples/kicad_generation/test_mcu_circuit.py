#!/usr/bin/env python3
"""
Test script creating a microcontroller circuit with various components.
This demonstrates using extended symbols and multi-unit components.
"""

import rust_kicad_schematic_writer as kicad
import subprocess

def main():
    print("Creating MCU Circuit with STM32 and Op-Amp...")
    print("=" * 50)
    
    # Create base schematic
    schematic = kicad.create_minimal_schematic()
    
    # Component list with positions
    components = [
        # Microcontroller (extended symbol)
        ("U1", "MCU_ST_STM32F1:STM32F103C8Tx", "STM32F103C8T6", 100, 60),
        
        # Voltage regulator (extended symbol)
        ("U2", "Regulator_Linear:AMS1117-3.3", "AMS1117-3.3", 50, 40),
        
        # Op-amp (multi-unit component)
        ("U3", "Amplifier_Operational:LM358", "LM358", 150, 40),
        
        # Crystal oscillator
        ("Y1", "Device:Crystal", "8MHz", 60, 80),
        
        # Decoupling capacitors
        ("C1", "Device:C", "100nF", 50, 60),
        ("C2", "Device:C", "10uF", 50, 70),
        
        # Pull-up resistors
        ("R1", "Device:R", "10k", 140, 80),
        ("R2", "Device:R", "10k", 150, 80),
        
        # USB connector
        ("J1", "Connector:USB_B_Micro", "USB", 30, 100),
    ]
    
    print("\nAdding components:")
    for ref, lib_id, value, x, y in components:
        try:
            schematic = kicad.add_component_to_schematic(
                schematic,
                reference=ref,
                lib_id=lib_id,
                value=value,
                x=float(x),
                y=float(y),
                rotation=0.0,
                footprint=""
            )
            print(f"  ✓ {ref}: {value}")
        except Exception as e:
            print(f"  ✗ {ref}: Failed - {e}")
    
    # Add hierarchical labels
    labels = [
        ("3V3", "output", 70, 30, 90),
        ("GND", "passive", 100, 100, 270),
        ("RESET", "input", 80, 50, 0),
        ("BOOT0", "input", 80, 70, 0),
        ("USB_D+", "bidirectional", 50, 90, 0),
        ("USB_D-", "bidirectional", 50, 95, 0),
        ("ANALOG_IN", "input", 130, 30, 90),
        ("ANALOG_OUT", "output", 170, 50, 0),
    ]
    
    print("\nAdding labels:")
    for name, shape, x, y, rotation in labels:
        try:
            schematic = kicad.add_hierarchical_label_to_schematic(
                schematic,
                name=name,
                shape=shape,
                x=float(x),
                y=float(y),
                rotation=float(rotation)
            )
            print(f"  ✓ {name} ({shape})")
        except Exception as e:
            print(f"  ✗ {name}: Failed - {e}")
    
    # Save file
    output_file = "mcu_circuit.kicad_sch"
    with open(output_file, 'w') as f:
        f.write(schematic)
    print(f"\n✓ Saved to {output_file}")
    
    # Try to validate
    try:
        result = subprocess.run(
            ["kicad-cli", "sch", "export", "pdf", output_file, "--output", "mcu_circuit.pdf"],
            capture_output=True,
            text=True,
            timeout=10
        )
        if result.returncode == 0:
            print("✓ KiCad validation passed!")
            print("✓ PDF exported to mcu_circuit.pdf")
        else:
            print(f"✗ KiCad validation failed: {result.stderr[:100]}")
    except FileNotFoundError:
        print("⚠️  kicad-cli not found - skipping validation")
    except Exception as e:
        print(f"⚠️  Validation error: {e}")
    
    print("\n" + "=" * 50)
    print("Circuit created successfully!")
    print(f"Components: {len(components)}")
    print(f"Labels: {len(labels)}")
    print(f"Output: {output_file}")
    print("=" * 50)

if __name__ == "__main__":
    main()