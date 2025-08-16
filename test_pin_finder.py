#!/usr/bin/env python3
"""
Test Pin Finder Functionality
"""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from circuit_synth.fast_generation.pin_finder import pin_finder


def test_pin_finder():
    """Test pin finding for common components"""
    print("🔍 Testing Pin Finder Functionality")
    print("=" * 50)
    
    # Test components
    test_components = [
        "MCU_Espressif:ESP32-S3",
        "RF_Module:ESP32-C6-MINI-1", 
        "MCU_ST_STM32F4:STM32F411CEUx",
        "Device:R",
        "Device:C",
        "Device:LED"
    ]
    
    for symbol in test_components:
        print(f"\n🧪 Testing: {symbol}")
        print("-" * 40)
        
        try:
            result = pin_finder.find_pins(symbol)
            
            if result["success"]:
                print(f"✅ Success! Found {len(result['pin_names'])} pins")
                print(f"📍 Pin names: {', '.join(result['pin_names'][:10])}")
                if len(result['pin_names']) > 10:
                    print(f"    ... and {len(result['pin_names']) - 10} more")
                    
                if result["error"]:
                    print(f"ℹ️  Note: {result['error']}")
                    
            else:
                print(f"❌ Failed: {result['error']}")
                
        except Exception as e:
            print(f"💥 Exception: {e}")
    
    print(f"\n📊 Pin finder cache size: {len(pin_finder.cache)}")
    print("✅ Pin finder test complete!")


if __name__ == "__main__":
    test_pin_finder()