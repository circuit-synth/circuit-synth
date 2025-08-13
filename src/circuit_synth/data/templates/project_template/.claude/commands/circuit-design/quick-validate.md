---
name: quick-validate
description: Quickly validate a list of components for circuit-synth compatibility
category: circuit-design
---

I'll quickly validate multiple KiCad components to ensure they exist and get basic pin information. Perfect for checking components before generating circuit-synth code.

**Usage:** `/quick-validate <symbol1> <symbol2> <symbol3>...`

```python
from circuit_synth.kicad.kicad_symbol_cache import SymbolLibCache
import sys

def quick_validate_components(*symbols):
    """Quickly validate multiple KiCad symbols"""
    if not symbols:
        print("Please provide at least one symbol name")
        return
    
    print("🔍 Quick Component Validation")
    print("=" * 50)
    
    results = {}
    
    for symbol_name in symbols:
        symbol_name = symbol_name.strip()
        if not symbol_name:
            continue
            
        try:
            # Check if symbol exists
            symbol_data = SymbolLibCache.get_symbol_data(symbol_name)
            
            if symbol_data:
                # Get basic info
                pin_count = len(symbol_data.get('pins', {}))
                
                # Find power pins quickly
                power_pins = []
                if 'pins' in symbol_data:
                    for pin_num, pin_info in symbol_data['pins'].items():
                        pin_name = pin_info.get('name', '')
                        if any(kw in pin_name.upper() for kw in ['VDD', 'VCC', 'VSS', 'GND', 'VBAT']):
                            power_pins.append(pin_name)
                
                results[symbol_name] = {
                    'status': 'FOUND',
                    'pin_count': pin_count,
                    'power_pins': power_pins[:3]  # First 3 power pins
                }
                
                print(f"✅ {symbol_name}")
                print(f"   Pins: {pin_count}, Power: {', '.join(power_pins[:3])}")
                
            else:
                results[symbol_name] = {'status': 'NOT_FOUND'}
                print(f"❌ {symbol_name} - NOT FOUND")
                
        except Exception as e:
            results[symbol_name] = {'status': 'ERROR', 'error': str(e)}
            print(f"⚠️  {symbol_name} - ERROR: {str(e)[:50]}...")
    
    # Summary
    found = sum(1 for r in results.values() if r['status'] == 'FOUND')
    total = len(results)
    
    print(f"\n📊 Summary: {found}/{total} components found")
    
    if found < total:
        print("\n💡 For missing components:")
        print("   - Use /find-symbol to search for alternatives")
        print("   - Check symbol name format (Library:SymbolName)")
        print("   - Verify KiCad library installation")
    
    if found > 0:
        print("\n🔧 Next steps:")
        print("   - Use /find-pins <symbol> for exact pin names")
        print("   - Use /component-info <symbol> for detailed information")
    
    return results

# Parse command line arguments or prompt for input
if len(sys.argv) > 1:
    symbols = sys.argv[1:]
else:
    symbols_input = input("Enter symbol names separated by spaces: ")
    symbols = symbols_input.split()

if symbols:
    quick_validate_components(*symbols)
else:
    print("No symbols provided!")
```

**Example usage:**
```bash
/quick-validate MCU_ST_STM32WB:STM32WB55CCU6 Device:C Device:R Connector:USB_B_Micro
```

**Common component patterns to validate:**
- **Microcontrollers**: `MCU_ST_STM32F4:STM32F407VETx`
- **Basic passives**: `Device:C Device:R Device:L`  
- **Regulators**: `Regulator_Linear:AMS1117-3.3`
- **Connectors**: `Connector:USB_B_Micro`
- **Crystals**: `Device:Crystal`

This command helps you quickly verify all components in your design before generating circuit-synth code, preventing pin name errors!