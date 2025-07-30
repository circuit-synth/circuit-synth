#!/usr/bin/env python3
"""
Test the Circuit Creator Agent

This demonstrates how users can create custom circuits and register them.
"""

from circuit_synth.agents.circuit_creator_agent import create_custom_circuit, register_circuit, list_circuits


def test_create_stm32_imu_circuit():
    """Test creating an STM32 + IMU circuit using the agent."""
    
    print("🎯 Testing Circuit Creator Agent")
    print("=" * 50)
    
    # Define requirements for STM32 + IMU board
    requirements = {
        "name": "STM32 IMU Development Board",
        "description": "Complete development board with STM32 microcontroller, 6-axis IMU sensor, USB-C power input, and programming interface",
        "category": "complete_boards",
        "components": [
            "microcontroller",
            "imu", 
            "usb_connector",
            "voltage_regulator",
            "crystal",
            "capacitor",
            "resistor"
        ]
    }
    
    print(f"📋 Creating circuit with requirements:")
    for key, value in requirements.items():
        if key == "components":
            print(f"   {key}: {', '.join(value)}")
        else:
            print(f"   {key}: {value}")
    
    print(f"\n🔄 Calling Circuit Creator Agent...")
    result = create_custom_circuit(requirements)
    
    if result["success"]:
        print(f"✅ Circuit created successfully!")
        
        # Show component suggestions
        components = result["components"]
        print(f"\n🔍 Found {len(components)} component suggestions:")
        for comp in components:
            stock_status = "✅" if comp["stock"] > 100 else "⚠️" if comp["stock"] > 0 else "❌"
            print(f"  {stock_status} {comp['type']}: {comp['part_number']}")
            print(f"      {comp['description']}")
            print(f"      Stock: {comp['stock']}, Price: {comp['price']}")
            print(f"      Symbol: {comp['suggested_symbol']}")
            print(f"      Footprint: {comp['suggested_footprint']}")
            print()
        
        # Show code preview  
        code_lines = result["circuit_code"].split('\n')
        print(f"📝 Generated Circuit Code ({len(code_lines)} lines):")
        print("```python")
        for line in code_lines[:25]:  # Show first 25 lines
            print(line)
        if len(code_lines) > 25:
            print(f"... ({len(code_lines) - 25} more lines)")
        print("```")
        
        # Show validation results
        validation = result["validation"]
        print(f"\n🔍 Validation Results:")
        print(f"   Valid: {'✅' if validation['valid'] else '❌'}")
        if validation["errors"]:
            print(f"   Errors: {validation['errors']}")
        if validation["warnings"]:
            print(f"   Warnings: {validation['warnings']}")
        if validation["suggestions"]:
            print(f"   Suggestions: {validation['suggestions']}")
        
        return result
    
    else:
        print(f"❌ Circuit creation failed: {result['error']}")
        if "details" in result:
            for detail in result["details"]:
                print(f"   • {detail}")
        return None


def test_register_simple_circuit():
    """Test registering a simple circuit."""
    
    print(f"\n" + "=" * 50)
    print(f"🔧 Testing Simple Circuit Registration")
    
    # Use the convenience function to register a simple power supply
    result = register_circuit(
        name="Basic 3.3V Power Supply",
        description="Simple 3.3V LDO regulator with USB input and filtering",
        category="power",
        components=["voltage_regulator", "capacitor", "usb_connector"]
    )
    
    if result["success"]:
        print(f"✅ Simple circuit registered successfully!")
        reg_result = result["registration_result"]
        print(f"   Circuit ID: {reg_result['circuit_id']}")
        print(f"   File: {reg_result['file_path']}")
        print(f"   Documentation: {reg_result['documentation_path']}")
    else:
        print(f"❌ Simple circuit registration failed")
        print(f"   Error: {result.get('error', 'Unknown error')}")


def test_list_circuits():
    """Test listing registered circuits."""
    
    print(f"\n" + "=" * 50) 
    print(f"📚 Testing Circuit Listing")
    
    circuits = list_circuits()
    
    if circuits:
        print(f"Found {len(circuits)} registered circuits:")
        for circuit in circuits:
            print(f"  🔧 {circuit['name']}")
            print(f"     ID: {circuit['id']}")
            print(f"     Category: {circuit['category']}")
            print(f"     Components: {circuit['component_count']}")
            print(f"     Used: {circuit['usage_count']} times")
            print()
    else:
        print("📭 No circuits registered yet")


if __name__ == "__main__":
    try:
        # Test creating a complex circuit
        stm32_result = test_create_stm32_imu_circuit()
        
        # Test registering a simple circuit
        test_register_simple_circuit()
        
        # Test listing circuits
        test_list_circuits()
        
        print(f"\n🎉 Circuit Creator Agent testing complete!")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()