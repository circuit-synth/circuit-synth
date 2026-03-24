---
name: validate-symbol
description: Check if a KiCad symbol exists and get its information
category: circuit-design
---

I'll check if a KiCad symbol exists in the libraries and provide detailed information about it.

**Usage:** `/validate-symbol <symbol_name>`

Let me validate the symbol for you:

```python
from circuit_synth.kicad.kicad_symbol_cache import SymbolLibCache
import os

def validate_symbol(symbol_name):
    """Validate if a KiCad symbol exists and get its details"""
    try:
        print(f"🔍 Validating symbol: {symbol_name}")
        print("=" * 50)
        
        # Check if symbol exists
        symbol_data = SymbolLibCache.get_symbol_data(symbol_name)
        
        if symbol_data:
            print("✅ Symbol found!")
            
            # Basic information
            if 'properties' in symbol_data:
                props = symbol_data['properties']
                if 'Reference' in props:
                    print(f"📋 Reference: {props['Reference']}")
                if 'Value' in props:
                    print(f"💡 Default Value: {props['Value']}")
                if 'Footprint' in props:
                    print(f"👣 Default Footprint: {props['Footprint']}")
            
            # Pin count
            if 'pins' in symbol_data:
                pin_count = len(symbol_data['pins'])
                print(f"📍 Pin Count: {pin_count}")
                
                # Show power pins
                power_pins = []
                for pin_num, pin_info in symbol_data['pins'].items():
                    pin_name = pin_info.get('name', '')
                    pin_type = pin_info.get('type', '')
                    if any(keyword in pin_name.upper() for keyword in ['VDD', 'VCC', 'VSS', 'GND', 'VBAT', 'VIN']):
                        power_pins.append(f"Pin {pin_num}: {pin_name}")
                
                if power_pins:
                    print(f"⚡ Power pins found:")
                    for pin in power_pins[:5]:  # Show first 5
                        print(f"   {pin}")
            
            # Suggest circuit-synth usage
            print(f"\n🔧 Circuit-synth usage:")
            lib_name = symbol_name.split(':')[0] if ':' in symbol_name else 'Unknown'
            symbol_part = symbol_name.split(':')[1] if ':' in symbol_name else symbol_name
            print(f'Component(symbol="{symbol_name}", ref="U1", footprint="...")')
            
            return True
        else:
            print("❌ Symbol not found!")
            
            # Suggest alternatives
            if ':' in symbol_name:
                lib_name, part_name = symbol_name.split(':', 1)
                print(f"\n💡 Suggestions:")
                print(f"   1. Check if library '{lib_name}' exists")
                print(f"   2. Search for similar symbols in the library")
                print(f"   3. Try alternative naming (e.g., underscores vs dashes)")
            
            return False
            
    except Exception as e:
        print(f"❌ Error validating symbol: {e}")
        
        # Suggest troubleshooting steps
        print(f"\n🔧 Troubleshooting:")
        print(f"   1. Verify symbol name format: Library:SymbolName")
        print(f"   2. Check KiCad installation and symbol libraries")
        print(f"   3. Try using /find-symbol command to search")
        
        return False

# Execute validation
symbol_name = input("Enter symbol name to validate: ")
if symbol_name.strip():
    validate_symbol(symbol_name.strip())
else:
    print("Please provide a symbol name")
```

**Common symbol naming patterns:**
- **Microcontrollers**: `MCU_ST_STM32F4:STM32F407VETx`
- **Basic components**: `Device:C`, `Device:R`, `Device:L`
- **Connectors**: `Connector:USB_B_Micro`, `Connector:Conn_01x02`
- **Regulators**: `Regulator_Linear:AMS1117-3.3`
- **Crystals**: `Device:Crystal`, `Device:Crystal_GND24`

This helps you verify symbols exist before using them in circuit-synth code!