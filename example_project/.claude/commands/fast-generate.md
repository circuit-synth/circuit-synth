---
name: fast-generate
description: Generate circuit using fast generation patterns with Google ADK/OpenRouter
category: circuit-design
---

# Fast Circuit Generation

Generate production-ready circuits in seconds using pre-defined patterns and high-speed AI models.

## Usage

```bash
/fast-generate <pattern_type> [requirements]
```

## Available Patterns

### Microcontroller Boards
- `esp32_basic` - Basic ESP32-S3 development board
- `esp32_sensor` - ESP32 with IMU sensor integration
- `stm32_basic` - STM32F4 microcontroller board
- `stm32_motor` - STM32 with motor control peripherals

### Sensor Circuits
- `sensor_imu` - Standalone IMU sensor module
- `sensor_temp` - Temperature sensor circuit
- `encoder_quad` - Quadrature encoder interface

### Motor Control
- `motor_stepper` - Stepper motor driver with DRV8825/A4988

### LED & Display
- `led_neopixel` - NeoPixel LED strip with level shifter

### Power & Connectivity
- `usb_power` - USB-C power input circuit

## Examples

### Basic ESP32 Board
```bash
/fast-generate esp32_basic
```

### ESP32 with Custom Requirements
```bash
/fast-generate esp32_basic --requirements '{"wifi_enabled": true, "debug_interface": "SWD", "include_leds": true}'
```

### Stepper Motor Driver
```bash
/fast-generate motor_stepper --requirements '{"motor_voltage": "12V", "current_limit": "2A"}'
```

### IMU Sensor Module
```bash
/fast-generate sensor_imu --requirements '{"sensor_type": "MPU-6050", "interface": "I2C"}'
```

## Implementation

```python
# This command uses the fast generation system
import asyncio
import json
from circuit_synth.fast_generation import FastCircuitGenerator, PatternType

async def generate_fast_circuit(pattern: str, requirements: str = "{}"):
    """Generate circuit using fast generation system"""
    try:
        # Parse requirements
        reqs = json.loads(requirements) if requirements != "{}" else {}
        
        # Initialize generator
        generator = FastCircuitGenerator()
        
        # Generate circuit
        result = await generator.generate_circuit(
            PatternType(pattern),
            requirements=reqs
        )
        
        if result["success"]:
            print(f"✅ Generated {pattern} in {result['latency_ms']:.1f}ms")
            print(f"🎯 Model: {result['model_used']}")
            
            # Save circuit code
            output_file = f"{pattern}_generated.py"
            with open(output_file, 'w') as f:
                f.write(result["circuit_code"])
            
            print(f"💾 Circuit saved to: {output_file}")
            
            # Show validation results
            validation = result["validation_results"]
            print(f"🔍 Validation:")
            print(f"  - Syntax: {'✅' if validation['syntax_valid'] else '❌'}")
            print(f"  - Components: {'✅' if validation['components_verified'] else '❌'}")
            print(f"  - Connections: {'✅' if validation['connections_valid'] else '❌'}")
            
        else:
            print(f"❌ Generation failed: {result.get('error', 'Unknown error')}")
            
    except Exception as e:
        print(f"❌ Fast generation error: {e}")

# Execute based on user input
pattern = input("Enter pattern type: ").strip()
requirements = input("Enter requirements (JSON, optional): ").strip() or "{}"

if pattern:
    asyncio.run(generate_fast_circuit(pattern, requirements))
else:
    print("Please specify a pattern type")
```

## Performance

- **Target Speed**: 3-5 seconds per circuit (vs 30-60s traditional)
- **Accuracy**: 95%+ success rate for verified patterns
- **Models**: OpenRouter Gemini-2.5-Flash, Google ADK agents
- **Components**: Only verified KiCad library components

## Setup Requirements

1. Set OpenRouter API key:
   ```bash
   export OPENROUTER_API_KEY=your_key_here
   ```

2. Install fast generation dependencies:
   ```bash
   pip install circuit_synth[fast_generation]
   ```

3. Test with demo:
   ```bash
   cs-fast-gen-demo
   ```

## Circuit Patterns Included

All patterns use verified KiCad components and follow electrical engineering best practices:

- **Power distribution** with proper decoupling
- **Debug interfaces** (SWD, UART, etc.)
- **Protection circuits** where applicable
- **Standard footprints** for manufacturability
- **Component alternatives** for sourcing flexibility

Each pattern generates complete circuit-synth Python code ready for KiCad export.