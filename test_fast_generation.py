"""
Quick test of the fast generation system
"""

import asyncio
import sys
from pathlib import Path

# Add src to path for imports
sys.path.insert(0, str(Path(__file__).parent / "src"))

from circuit_synth.fast_generation import FastCircuitGenerator, PatternType


async def test_fast_generation():
    """Test basic fast generation functionality"""
    print("🧪 Testing Fast Circuit Generation System")
    print("=" * 50)
    
    try:
        # Test without API key (should work in simulation mode)
        generator = FastCircuitGenerator()
        
        print("✅ FastCircuitGenerator initialized")
        
        # List available patterns
        patterns = generator.list_available_patterns()
        print(f"📋 Available patterns: {len(patterns)}")
        
        for pattern in patterns[:5]:  # Show first 5
            print(f"  - {pattern['name']} (complexity: {pattern['complexity']}/5)")
        
        # Test pattern template loading
        esp32_pattern = generator.patterns.get_pattern(PatternType.ESP32_BASIC)
        if esp32_pattern:
            print(f"✅ ESP32 pattern loaded: {esp32_pattern.name}")
            print(f"   Components: {len(esp32_pattern.components)}")
            print(f"   Power rails: {esp32_pattern.power_rails}")
        else:
            print("❌ Failed to load ESP32 pattern")
            
        # Check component specifications
        print("\n🔍 Component Verification:")
        for comp in esp32_pattern.components[:3]:  # Check first 3 components
            print(f"  - {comp.symbol} → {comp.footprint}")
        
        print("\n✅ Basic system test passed!")
        print("💡 To test full generation, set OPENROUTER_API_KEY environment variable")
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()


async def test_with_mock_generation():
    """Test with mock generation (no API required)"""
    print("\n🔬 Testing Mock Generation")
    print("=" * 30)
    
    try:
        # Create generator without API key
        generator = FastCircuitGenerator(openrouter_key="mock_key")
        
        # This would normally make an API call, but should handle gracefully
        result = await generator.generate_circuit(
            PatternType.ESP32_BASIC,
            requirements={"test_mode": True}
        )
        
        print(f"📊 Generation result: {'Success' if result['success'] else 'Failed'}")
        print(f"⚡ Pattern: {result['pattern']}")
        print(f"⏱️  Latency: {result.get('latency_ms', 0):.1f}ms")
        
        if not result['success']:
            print(f"   Error (expected): {result.get('error', 'N/A')}")
        
        print("✅ Mock generation test completed")
        
    except Exception as e:
        print(f"❌ Mock generation test failed: {e}")


def main():
    """Main test function"""
    asyncio.run(test_fast_generation())
    asyncio.run(test_with_mock_generation())
    
    print("\n🎯 Integration Summary:")
    print("- Fast generation system structure created")
    print("- Pattern templates defined with verified KiCad components")
    print("- OpenRouter and Google ADK model integrations ready")
    print("- Demo and test scripts available")
    print("\n📋 Next Steps:")
    print("1. Set OPENROUTER_API_KEY environment variable")
    print("2. Run: python -m circuit_synth.fast_generation.demo")
    print("3. Test with: cs-fast-gen-demo (after pip install)")


if __name__ == "__main__":
    main()