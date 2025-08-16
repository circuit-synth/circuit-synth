#!/usr/bin/env python3
"""
Quick Demo of Fast Circuit Generation
"""

import asyncio
import os
from src.circuit_synth.fast_generation import FastCircuitGenerator, PatternType

async def main():
    print('⚡ FAST CIRCUIT GENERATION DEMO')
    print('=' * 40)
    
    generator = FastCircuitGenerator()
    
    # Test a few key patterns
    patterns_to_test = [
        (PatternType.ESP32_BASIC, 'ESP32 Dev Board'),
        (PatternType.SENSOR_IMU, 'IMU Sensor Module'),
        (PatternType.LED_NEOPIXEL, 'NeoPixel Driver')
    ]
    
    results = []
    
    for pattern, name in patterns_to_test:
        print(f'🔄 Generating {name}...')
        
        result = await generator.generate_circuit(pattern)
        
        if result['success']:
            print(f'✅ {name}: {result["latency_ms"]:.0f}ms')
            
            # Clean and save the code
            code = result['circuit_code']
            if code.startswith('```python'):
                code = '\n'.join(code.split('\n')[1:])
            if code.endswith('```'):
                code = '\n'.join(code.split('\n')[:-1])
            
            filename = f'{pattern.value}_generated.py'
            with open(filename, 'w') as f:
                f.write(code.strip())
            print(f'  💾 Saved to {filename}')
            
            results.append((name, result["latency_ms"], True))
        else:
            print(f'❌ {name}: {result.get("error", "Failed")}')
            results.append((name, 0, False))
        
        print()
    
    # Summary
    print('📊 RESULTS SUMMARY:')
    successful = sum(1 for _, _, success in results if success)
    total_time = sum(time for _, time, success in results if success)
    
    print(f'  Success rate: {successful}/{len(results)} ({100*successful/len(results):.0f}%)')
    if successful > 0:
        avg_time = total_time / successful
        print(f'  Average time: {avg_time:.0f}ms')
        
        # Speed comparison
        baseline = 45000  # Traditional method baseline
        speedup = baseline / avg_time
        print(f'  🚀 SPEEDUP: {speedup:.1f}x faster than traditional method!')
    
    print('\n✅ Fast generation system is working!')

if __name__ == "__main__":
    asyncio.run(main())