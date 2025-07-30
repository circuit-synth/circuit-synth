#!/usr/bin/env python3
"""
Test script for the unified pin access interface.

This script demonstrates and validates the new component.pins.VCC syntax.
"""

from circuit_synth import Component, Net, circuit


@circuit
def test_unified_pin_access():
    """Test the unified pin access interface."""
    
    # Create some nets for testing
    vcc_3v3 = Net('VCC_3V3')
    gnd = Net('GND')
    
    print("🔧 Testing Unified Pin Access Interface")
    print("=" * 50)
    
    # Test 1: STM32 microcontroller (complex component with named pins)
    print("\n1. Testing STM32 Component (Named Pins)")
    print("-" * 40)
    
    try:
        stm32 = Component(
            symbol="MCU_ST_STM32G0:STM32G030C8T6",
            ref="U1",
            footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm"
        )
        
        print(f"✅ Created STM32 component: {stm32}")
        print(f"📊 Pin count: {len(stm32.pins)}")
        
        # Test dot notation access
        print("\n🔍 Testing dot notation access:")
        try:
            vdd_pin = stm32.pins.VDD
            print(f"✅ stm32.pins.VDD = {vdd_pin}")
        except Exception as e:
            print(f"❌ stm32.pins.VDD failed: {e}")
            
        try:
            vss_pin = stm32.pins.VSS  
            print(f"✅ stm32.pins.VSS = {vss_pin}")
        except Exception as e:
            print(f"❌ stm32.pins.VSS failed: {e}")
        
        # Test case-insensitive aliases
        print("\n🔍 Testing case-insensitive aliases:")
        try:
            gnd_pin = stm32.pins.gnd  # Should map to VSS
            print(f"✅ stm32.pins.gnd = {gnd_pin}")
        except Exception as e:
            print(f"❌ stm32.pins.gnd failed: {e}")
            
        try:
            vcc_pin = stm32.pins.vcc  # Should map to VDD
            print(f"✅ stm32.pins.vcc = {vcc_pin}")
        except Exception as e:
            print(f"❌ stm32.pins.vcc failed: {e}")
        
        # Test bracket notation
        print("\n🔍 Testing bracket notation:")
        try:
            pin1 = stm32.pins["VDD"]
            print(f"✅ stm32.pins['VDD'] = {pin1}")
        except Exception as e:
            print(f"❌ stm32.pins['VDD'] failed: {e}")
            
        # Test connection with dot notation
        print("\n🔌 Testing net connections:")
        try:
            stm32.pins.VDD += vcc_3v3
            stm32.pins.VSS += gnd
            print("✅ Connected VDD and VSS using dot notation")
        except Exception as e:
            print(f"❌ Connection failed: {e}")
            
        # Show pin listing
        print("\n📋 Available pins:")
        print(stm32.pins.list_all())
        
    except Exception as e:
        print(f"❌ STM32 test failed: {e}")
    
    # Test 2: Simple resistor (numbered pins)
    print("\n2. Testing Resistor Component (Numbered Pins)")
    print("-" * 45)
    
    try:
        resistor = Component(
            symbol="Device:R",
            ref="R1", 
            value="10K",
            footprint="Resistor_SMD:R_0603_1608Metric"
        )
        
        print(f"✅ Created resistor component: {resistor}")
        print(f"📊 Pin count: {len(resistor.pins)}")
        
        # Test numbered pin access
        print("\n🔍 Testing numbered pin access:")
        try:
            pin1 = resistor.pins[1]
            pin2 = resistor.pins[2]
            print(f"✅ resistor.pins[1] = {pin1}")
            print(f"✅ resistor.pins[2] = {pin2}")
        except Exception as e:
            print(f"❌ Numbered pin access failed: {e}")
            
        # Test connections
        print("\n🔌 Testing net connections:")
        try:
            resistor.pins[1] += vcc_3v3
            resistor.pins[2] += gnd
            print("✅ Connected pins 1 and 2 using bracket notation")
        except Exception as e:
            print(f"❌ Connection failed: {e}")
        
        # Show pin listing  
        print("\n📋 Available pins:")
        print(resistor.pins.list_all())
        
    except Exception as e:
        print(f"❌ Resistor test failed: {e}")
    
    # Test 3: Backward compatibility
    print("\n3. Testing Backward Compatibility")
    print("-" * 35)
    
    try: 
        capacitor = Component(
            symbol="Device:C",
            ref="C1",
            value="10uF", 
            footprint="Capacitor_SMD:C_0805_2012Metric"
        )
        
        # Test old-style access still works
        print("🔍 Testing backward compatibility:")
        try:
            old_pin1 = capacitor[1]
            new_pin1 = capacitor.pins[1]
            print(f"✅ capacitor[1] = {old_pin1}")
            print(f"✅ capacitor.pins[1] = {new_pin1}")
            print(f"✅ Same pin object: {old_pin1 is new_pin1}")
        except Exception as e:
            print(f"❌ Backward compatibility failed: {e}")
            
    except Exception as e:
        print(f"❌ Backward compatibility test failed: {e}")
    
    print("\n" + "=" * 50)
    print("🎉 Unified Pin Access Interface Test Complete!")


if __name__ == "__main__":
    test_unified_pin_access()