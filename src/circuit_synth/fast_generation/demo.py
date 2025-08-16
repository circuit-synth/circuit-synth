"""
Fast Generation Demo Script

Simple demo to test the fast circuit generation system.
"""

import asyncio
import os
import json
from pathlib import Path
from dotenv import load_dotenv

from .core import FastCircuitGenerator
from .patterns import PatternType

# Load environment variables
load_dotenv()


async def demo_single_pattern():
    """Demo generating a single circuit pattern"""
    print("🚀 Fast Circuit Generation Demo")
    print("=" * 50)
    
    try:
        # Initialize generator
        generator = FastCircuitGenerator()
        
        # Generate ESP32 basic board
        print("🔄 Generating ESP32 basic board...")
        result = await generator.generate_circuit(
            PatternType.ESP32_BASIC,
            requirements={
                "add_wifi": True,
                "include_leds": True,
                "debug_interface": "SWD"
            }
        )
        
        if result["success"]:
            print(f"✅ Generated in {result['latency_ms']:.1f}ms")
            print(f"🎯 Model: {result['model_used']}")
            print(f"📊 Tokens: {result['tokens_used']}")
            
            # Save result
            output_dir = Path("demo_output")
            output_dir.mkdir(exist_ok=True)
            
            output_file = output_dir / "esp32_basic_demo.py"
            output_file.write_text(result["circuit_code"])
            print(f"💾 Saved to: {output_file}")
            
        else:
            print(f"❌ Generation failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Demo failed: {e}")


async def demo_all_patterns():
    """Demo generating circuits for all available patterns"""
    print("🚀 Fast Circuit Generation - All Patterns Demo")
    print("=" * 60)
    
    try:
        # Initialize generator
        generator = FastCircuitGenerator()
        
        # List available patterns
        patterns = generator.list_available_patterns()
        print(f"📋 Found {len(patterns)} available patterns:")
        
        for pattern in patterns:
            print(f"  - {pattern['name']} (complexity: {pattern['complexity']}/5)")
        
        print("\n🔄 Generating demo circuits...")
        
        # Generate demo circuits
        results = await generator.generate_demo_circuits()
        
        # Process results
        successful = 0
        total_latency = 0
        
        output_dir = Path("demo_output")
        output_dir.mkdir(exist_ok=True)
        
        for pattern_name, result in results.items():
            if result["success"]:
                successful += 1
                total_latency += result["latency_ms"]
                
                # Save circuit code
                output_file = output_dir / f"{pattern_name}_demo.py"
                output_file.write_text(result["circuit_code"])
                
                print(f"✅ {pattern_name}: {result['latency_ms']:.1f}ms")
            else:
                print(f"❌ {pattern_name}: {result.get('error', 'Failed')}")
        
        # Summary
        print("\n📊 Generation Summary:")
        print(f"  Success rate: {successful}/{len(results)} ({100*successful/len(results):.1f}%)")
        if successful > 0:
            avg_latency = total_latency / successful
            print(f"  Average latency: {avg_latency:.1f}ms")
        
        # Save summary
        summary_file = output_dir / "generation_summary.json"
        summary = {
            "timestamp": str(asyncio.get_event_loop().time()),
            "total_patterns": len(results),
            "successful": successful,
            "success_rate": successful / len(results),
            "average_latency_ms": total_latency / successful if successful > 0 else 0,
            "results": results
        }
        
        summary_file.write_text(json.dumps(summary, indent=2))
        print(f"💾 Summary saved to: {summary_file}")
        
        # Generator statistics
        stats = generator.get_stats()
        print(f"\n📈 Generator Statistics:")
        print(f"  Total generated: {stats['total_generated']}")
        print(f"  Success rate: {stats['success_rate']:.1%}")
        print(f"  Average latency: {stats['avg_latency_ms']:.1f}ms")
        
    except Exception as e:
        print(f"❌ Demo failed: {e}")


async def demo_performance_test():
    """Performance test - generate same pattern multiple times"""
    print("⚡ Fast Circuit Generation - Performance Test")
    print("=" * 50)
    
    try:
        generator = FastCircuitGenerator()
        
        test_pattern = PatternType.ESP32_BASIC
        num_iterations = 5
        
        print(f"🔄 Generating {test_pattern.value} {num_iterations} times...")
        
        latencies = []
        successes = 0
        
        for i in range(num_iterations):
            result = await generator.generate_circuit(test_pattern)
            latencies.append(result["latency_ms"])
            
            if result["success"]:
                successes += 1
                print(f"  ✅ Iteration {i+1}: {result['latency_ms']:.1f}ms")
            else:
                print(f"  ❌ Iteration {i+1}: Failed")
        
        # Performance analysis
        if latencies:
            avg_latency = sum(latencies) / len(latencies)
            min_latency = min(latencies) 
            max_latency = max(latencies)
            
            print(f"\n📊 Performance Results:")
            print(f"  Success rate: {successes}/{num_iterations} ({100*successes/num_iterations:.1f}%)")
            print(f"  Average latency: {avg_latency:.1f}ms")
            print(f"  Min latency: {min_latency:.1f}ms")
            print(f"  Max latency: {max_latency:.1f}ms")
            
            # Speed comparison (assuming old system takes 30-60s)
            old_system_avg = 45000  # 45 seconds
            speedup = old_system_avg / avg_latency
            print(f"  🚀 Speedup: {speedup:.1f}x faster than baseline")
            
    except Exception as e:
        print(f"❌ Performance test failed: {e}")


def check_environment():
    """Check if environment is properly configured"""
    print("🔍 Environment Check")
    print("=" * 30)
    
    # Check API keys
    openrouter_key = os.getenv("OPENROUTER_API_KEY")
    if openrouter_key:
        print("✅ OPENROUTER_API_KEY found")
    else:
        print("⚠️  OPENROUTER_API_KEY not set")
        print("   Set via: export OPENROUTER_API_KEY=your_key_here")
    
    google_project = os.getenv("GOOGLE_CLOUD_PROJECT")
    if google_project:
        print(f"✅ Google Cloud project: {google_project}")
    else:
        print("ℹ️  GOOGLE_CLOUD_PROJECT not set (optional)")
    
    # Check required packages
    try:
        import openai
        print("✅ OpenAI package available")
    except ImportError:
        print("❌ OpenAI package missing: pip install openai")
    
    try:
        from google.adk.agents import Agent
        print("✅ Google ADK available")
    except ImportError:
        print("ℹ️  Google ADK not available (optional)")
    
    print()


async def main():
    """Main demo function"""
    check_environment()
    
    # Run demos
    await demo_single_pattern()
    print()
    await demo_performance_test() 
    print()
    await demo_all_patterns()


def main_cli():
    """CLI entry point for main demo"""
    asyncio.run(main())


if __name__ == "__main__":
    asyncio.run(main())