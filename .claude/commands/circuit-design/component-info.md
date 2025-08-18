---
name: component-info
description: Get complete component information including pins, footprints, and usage examples
category: circuit-design
---

I'll provide comprehensive information about a KiCad component including pins, suggested footprints, and circuit-synth usage examples.

**Usage:** `/component-info <symbol_name>`

```python
from circuit_synth.kicad.kicad_symbol_cache import SymbolLibCache
import json

def get_component_info(symbol_name):
    """Get comprehensive component information"""
    try:
        print(f"📋 Component Information: {symbol_name}")
        print("=" * 60)
        
        # Validate symbol exists
        symbol_data = SymbolLibCache.get_symbol_data(symbol_name)
        
        if not symbol_data:
            print("❌ Symbol not found!")
            return False
        
        # Basic Properties
        print("📊 BASIC INFORMATION")
        print("-" * 30)
        if 'properties' in symbol_data:
            props = symbol_data['properties']
            for key in ['Reference', 'Value', 'Footprint', 'Datasheet']:
                if key in props:
                    print(f"{key}: {props[key]}")
        
        # Pin Information
        if 'pins' in symbol_data:
            pins = symbol_data['pins']
            print(f"\n📍 PINS ({len(pins)} total)")
            print("-" * 30)
            
            # Categorize pins
            power_pins = []
            signal_pins = []
            io_pins = []
            
            for pin_num, pin_info in pins.items():
                pin_name = pin_info.get('name', 'Unknown')
                pin_type = pin_info.get('type', 'Unknown')
                
                if pin_type in ['power_in', 'power_out'] or any(kw in pin_name.upper() for kw in ['VDD', 'VCC', 'VSS', 'GND', 'VBAT']):
                    power_pins.append((pin_num, pin_name, pin_type))
                elif pin_type in ['input', 'output']:
                    signal_pins.append((pin_num, pin_name, pin_type))
                else:
                    io_pins.append((pin_num, pin_name, pin_type))
            
            # Display categorized pins
            if power_pins:
                print("⚡ Power pins:")
                for pin_num, pin_name, pin_type in sorted(power_pins):
                    print(f"  Pin {pin_num:>3}: {pin_name:<15} ({pin_type})")
            
            if signal_pins:
                print("\n🔄 Signal pins:")
                for pin_num, pin_name, pin_type in sorted(signal_pins)[:10]:  # Limit display
                    print(f"  Pin {pin_num:>3}: {pin_name:<15} ({pin_type})")
                if len(signal_pins) > 10:
                    print(f"  ... and {len(signal_pins) - 10} more signal pins")
            
            if io_pins:
                print(f"\n📡 I/O pins:")
                for pin_num, pin_name, pin_type in sorted(io_pins)[:10]:  # Limit display  
                    print(f"  Pin {pin_num:>3}: {pin_name:<15} ({pin_type})")
                if len(io_pins) > 10:
                    print(f"  ... and {len(io_pins) - 10} more I/O pins")
        
        # Circuit-synth code example
        print(f"\n🔧 CIRCUIT-SYNTH USAGE EXAMPLE")
        print("-" * 40)
        lib_name = symbol_name.split(':')[0] if ':' in symbol_name else 'Unknown'
        
        print(f'# Import circuit-synth')
        print(f'from circuit_synth import *')
        print(f'')
        print(f'# Create component')
        print(f'component = Component(')
        print(f'    symbol="{symbol_name}",')
        print(f'    ref="U1",  # Adjust reference as needed')
        print(f'    footprint="Package_QFP:LQFP-64_10x10mm_P0.5mm",  # Example footprint')
        print(f'    value="ComponentValue"')
        print(f')')
        print(f'')
        
        # Show example connections for power pins
        if 'pins' in symbol_data:
            print(f'# Example pin connections')
            pins = symbol_data['pins']
            example_connections = []
            
            for pin_num, pin_info in list(pins.items())[:8]:  # Show first 8 pins
                pin_name = pin_info.get('name', 'Unknown')
                pin_type = pin_info.get('type', 'Unknown')
                
                if any(kw in pin_name.upper() for kw in ['VDD', 'VCC']):
                    example_connections.append(f'component["{pin_name}"] += VCC_3V3  # Power supply')
                elif any(kw in pin_name.upper() for kw in ['VSS', 'GND']):
                    example_connections.append(f'component["{pin_name}"] += GND  # Ground')
                elif pin_name.upper() in ['RST', 'RESET', 'NRST']:
                    example_connections.append(f'component["{pin_name}"] += reset_net  # Reset signal')
                else:
                    example_connections.append(f'component["{pin_name}"] += some_net  # Pin {pin_num}')
            
            for connection in example_connections:
                print(connection)
        
        print(f'\n💡 Remember to:')
        print(f'   1. Verify pin names with /find-pins {symbol_name}')
        print(f'   2. Choose appropriate footprint for your design')
        print(f'   3. Check component availability with /find-parts')
        
        return True
        
    except Exception as e:
        print(f"❌ Error getting component info: {e}")
        return False

# Execute the command
symbol_name = input("Enter symbol name: ")
if symbol_name.strip():
    get_component_info(symbol_name.strip())
else:
    print("Please provide a symbol name")
```

**Pro Tips:**
- Use this command before writing circuit-synth code to avoid pin name errors
- Check the power pins section carefully - these are critical for proper connections
- The usage example shows the exact syntax needed for circuit-synth
- Always verify footprint compatibility with your PCB requirements