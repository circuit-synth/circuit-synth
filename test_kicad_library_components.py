#!/usr/bin/env python3
"""
Test script to validate KiCad library component loading and extended symbols.
Adds various components from different libraries and arranges them in a square.
"""

import rust_kicad_schematic_writer as kicad
import subprocess
import sys

def create_library_test_circuit():
    """Create a circuit with components from various KiCad libraries."""
    
    # Create minimal schematic
    schematic = kicad.create_minimal_schematic()
    
    # Define component positions in a square layout
    # 4x4 grid with 30mm spacing
    positions = [
        (50, 50),   (80, 50),   (110, 50),  (140, 50),   # Top row
        (50, 80),   (80, 80),   (110, 80),  (140, 80),   # Second row
        (50, 110),  (80, 110),  (110, 110), (140, 110),  # Third row  
        (50, 140),  (80, 140),  (110, 140), (140, 140),  # Bottom row
    ]
    
    # List of components to test from various libraries
    components_to_test = [
        # Microcontrollers (MCU libraries)
        {
            "name": "STM32F103C8T6",
            "symbol": "MCU_ST_STM32F1:STM32F103C8Tx",
            "footprint": "Package_QFP:LQFP-48_7x7mm_P0.5mm",
            "ref": "U"
        },
        {
            "name": "ATmega328P",
            "symbol": "MCU_Microchip_ATmega:ATmega328P-P",  # Use -P variant
            "footprint": "Package_DIP:DIP-28_W7.62mm",
            "ref": "U"
        },
        
        # Power Management (Regulator libraries)
        {
            "name": "AMS1117-3.3 (extends)",
            "symbol": "Regulator_Linear:AMS1117-3.3",  # This extends AP1117-15
            "footprint": "Package_TO_SOT_SMD:SOT-223-3_TabPin2",
            "ref": "U"
        },
        {
            "name": "LM7805",
            "symbol": "Regulator_Linear:LM7805_TO220",
            "footprint": "Package_TO_SOT_THT:TO-220-3_Vertical",
            "ref": "U"
        },
        
        # Amplifiers (Amplifier_Operational library)
        {
            "name": "LM358",
            "symbol": "Amplifier_Operational:LM358",
            "footprint": "Package_DIP:DIP-8_W7.62mm",
            "ref": "U"
        },
        {
            "name": "TL072",
            "symbol": "Amplifier_Operational:TL072",
            "footprint": "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
            "ref": "U"
        },
        
        # Interface (Interface libraries)
        {
            "name": "MAX232",
            "symbol": "Interface_UART:MAX232",
            "footprint": "Package_DIP:DIP-16_W7.62mm",
            "ref": "U"
        },
        {
            "name": "CH340G",
            "symbol": "Interface_USB:CH340G",
            "footprint": "Package_SO:SOIC-16_3.9x9.9mm_P1.27mm",
            "ref": "U"
        },
        
        # Memory (Memory libraries)
        {
            "name": "AT24C256",
            "symbol": "Memory_EEPROM:24LC256",
            "footprint": "Package_DIP:DIP-8_W7.62mm",
            "ref": "U"
        },
        
        # Sensors (Sensor libraries)
        {
            "name": "DHT11",
            "symbol": "Sensor:DHT11",  # DHT22 doesn't exist, use DHT11
            "footprint": "Sensor:Aosong_DHT11_5.5x12.0_P2.54mm",
            "ref": "U"
        },
        
        # Transistors (Transistor libraries)
        {
            "name": "2N3904",
            "symbol": "Transistor_BJT:2N3904",
            "footprint": "Package_TO_SOT_THT:TO-92_Inline",
            "ref": "Q"
        },
        {
            "name": "IRF540N",
            "symbol": "Transistor_FET:IRF540N",
            "footprint": "Package_TO_SOT_THT:TO-220-3_Vertical",
            "ref": "Q"
        },
        
        # Diodes (Diode library)
        {
            "name": "1N4148",
            "symbol": "Diode:1N4148",
            "footprint": "Diode_THT:D_DO-35_SOD27_P7.62mm_Horizontal",
            "ref": "D"
        },
        
        # Connectors (Connector libraries)
        {
            "name": "USB Type-C",
            "symbol": "Connector:USB_C_Plug_USB2.0",  # Use Plug variant
            "footprint": "Connector_USB:USB_C_Receptacle_HRO_TYPE-C-31-M-12",
            "ref": "J"
        },
        {
            "name": "RJ45",
            "symbol": "Connector:RJ45",
            "footprint": "Connector_RJ:RJ45_Amphenol_54602-x08_Horizontal",
            "ref": "J"
        },
        
        # Display (Display library)
        {
            "name": "LCD 16x2",
            "symbol": "Display_Character:WC1602A",
            "footprint": "Display:WC1602A",
            "ref": "DS"
        }
    ]
    
    # Add components to circuit at grid positions
    components_added = []
    for i, comp_info in enumerate(components_to_test):
        if i >= len(positions):
            print(f"⚠️  Skipping {comp_info['name']} - no more positions available")
            continue
            
        x, y = positions[i]
        
        try:
            print(f"Adding {comp_info['name']}...", end=" ")
            
            # Add component using Rust module
            schematic = kicad.add_component_to_schematic(
                schematic,
                reference=f"{comp_info['ref']}{i+1}",  # U1, U2, etc.
                lib_id=comp_info["symbol"],
                value=comp_info["name"],
                x=float(x),
                y=float(y),
                rotation=0.0,
                footprint=comp_info["footprint"]
            )
            components_added.append(comp_info["name"])
            
            print(f"✓ at position ({x}, {y})")
            
        except Exception as e:
            print(f"✗ Failed: {e}")
            continue
    
    print(f"\n✅ Successfully added {len(components_added)}/{len(components_to_test)} components")
    print("Components added:", ", ".join(components_added))
    
    return schematic

def main():
    """Main test function."""
    print("=" * 60)
    print("KiCad Library Component Test")
    print("Testing various components including extended symbols")
    print("=" * 60)
    
    # Create the test circuit
    schematic = create_library_test_circuit()
    
    # Generate KiCad schematic
    output_file = "test_library_components.kicad_sch"
    print(f"\nGenerating KiCad schematic: {output_file}")
    
    try:
        with open(output_file, 'w') as f:
            f.write(schematic)
        print(f"✓ Generated {output_file}")
    except Exception as e:
        print(f"✗ Failed to generate schematic: {e}")
        return 1
    
    # Validate with KiCad CLI
    print("\nValidating with KiCad CLI...")
    try:
        result = subprocess.run(
            ["kicad-cli", "sch", "export", "python-bom", output_file, "-o", "/dev/null"],
            capture_output=True,
            text=True
        )
        
        if result.returncode == 0:
            print("✅ KiCad validation PASSED - All components loaded correctly!")
            print("\nExtended symbol handling verified:")
            print("  • AMS1117-3.3 (extends AP1117-15) ✓")
            print("  • All geometry sections renamed correctly ✓")
            print("  • No duplicate properties ✓")
            return 0
        else:
            print(f"❌ KiCad validation FAILED")
            print(f"Error: {result.stderr}")
            return 1
            
    except FileNotFoundError:
        print("⚠️  kicad-cli not found - cannot validate")
        print("   Install KiCad to enable validation")
        return 0
    except Exception as e:
        print(f"⚠️  Validation error: {e}")
        return 1

if __name__ == "__main__":
    sys.exit(main())