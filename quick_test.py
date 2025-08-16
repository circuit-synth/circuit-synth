#!/usr/bin/env python3
"""
Quick test of updated circuit generation with pin finding
"""

import asyncio
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent / "src"))

from circuit_synth.fast_generation.models import OpenRouterModel

async def test_generation():
    print("🧪 Testing Circuit Generation with Pin Finding")
    print("=" * 60)
    
    # Initialize model
    model = OpenRouterModel()
    
    # Test with ESP32 + IMU
    components = [
        "RF_Module:ESP32-C6-MINI-1",
        "Sensor_Motion:MPU-6050", 
        "Device:R",
        "Device:C"
    ]
    
    prompt = "Generate a simple ESP32-C6 with MPU-6050 IMU circuit"
    
    context = {
        "components": components,
        "pattern_type": "ESP32 with IMU"
    }
    
    print(f"🔍 Testing components: {', '.join(components)}")
    print("🤖 Generating circuit...")
    
    try:
        response = await model.generate_circuit(prompt, context, max_tokens=2000)
        
        if response.success:
            print(f"✅ Generated successfully in {response.latency_ms:.0f}ms")
            print(f"📊 Tokens: {response.tokens_used}")
            
            # Check if it uses correct pins
            code = response.content
            if "mpu6050[\"VDD\"]" in code:
                print("✅ Uses correct MPU-6050 pin: VDD")
            elif "mpu6050[\"VCC\"]" in code:
                print("❌ Still using wrong MPU-6050 pin: VCC")
            else:
                print("ℹ️  Could not detect MPU-6050 pin usage in code")
            
            # Save for inspection
            with open("quick_test_output.py", "w") as f:
                f.write(code)
            print("💾 Saved output to quick_test_output.py")
            
            # Show preview
            print("\n📋 Code preview:")
            lines = code.split('\n')[:15]
            for line in lines:
                print(f"   {line}")
            if len(code.split('\n')) > 15:
                print("   ... (truncated)")
        else:
            print(f"❌ Generation failed: {response.error}")
            
    except Exception as e:
        print(f"💥 Test failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_generation())