---
name: find-pins
description: Find exact pin names for a KiCad component symbol
category: circuit-design
---

I'll help you find the exact pin names for a KiCad component symbol. This is essential for accurate circuit-synth code generation.

**Usage:** `/find-pins <symbol_name>`

Examples:
- `/find-pins Device:C` - Find capacitor pin names
- `/find-pins MCU_ST_STM32WB:STM32WB55CCU6` - Find STM32WB55 pin names  
- `/find-pins Connector:USB_B_Micro` - Find USB connector pin names

Let me search for pin information for your component:

```python
from circuit_synth.kicad.kicad_symbol_cache import SymbolLibCache
import json

def find_component_pins(symbol_name):
    """Find exact pin names and numbers for a KiCad symbol"""
    try:
        # Get symbol data from KiCad libraries
        symbol_data = SymbolLibCache.get_symbol_data(symbol_name)
        
        if symbol_data and 'pins' in symbol_data:
            pins = symbol_data['pins']
            
            print(f"📍 Pin information for {symbol_name}:")
            print("=" * 50)
            
            # Sort pins by number for easier reading
            sorted_pins = sorted(pins.items(), 
                               key=lambda x: int(x[0]) if x[0].isdigit() else float('inf'))
            
            for pin_num, pin_info in sorted_pins:
                pin_name = pin_info.get('name', 'Unknown')
                pin_type = pin_info.get('type', 'Unknown')
                print(f"Pin {pin_num:>3}: {pin_name:<20} ({pin_type})")
            
            # Generate example circuit-synth code
            print(f"\n🔧 Example circuit-synth usage:")
            print(f'component = Component(symbol="{symbol_name}", ref="U1")')
            for pin_num, pin_info in list(sorted_pins)[:5]:  # Show first 5 pins
                pin_name = pin_info.get('name', 'Unknown')
                if pin_name not in ['Unknown', '']:
                    print(f'component["{pin_name}"] += some_net  # Pin {pin_num}')
            
            return True
        else:
            print(f"❌ No pin information found for {symbol_name}")
            return False
            
    except Exception as e:
        print(f"❌ Error finding pins for {symbol_name}: {e}")
        return False

# Execute the search
symbol_name = input("Enter symbol name (e.g., 'Device:C' or 'MCU_ST_STM32WB:STM32WB55CCU6'): ")
if symbol_name.strip():
    find_component_pins(symbol_name.strip())
else:
    print("Please provide a symbol name")
```

**Common pin naming patterns to watch for:**
- Power pins: `VDD`, `VCC`, `V_{DD}`, `V_{CC}`, `VSS`, `GND`
- Crystal pins: `OSC_IN`/`OSC_OUT` or `XTAL1`/`XTAL2` or `PH0`/`PH1`
- USB pins: `VBUS`, `GND`, `D+`, `D-`, `Shield` (not `SHIELD`)
- Debug pins: `SWDIO`, `SWCLK` or `SWD_IO`, `SWD_CLK`

This command helps you get exact pin names before writing circuit-synth code, preventing the pin name errors you've been seeing.