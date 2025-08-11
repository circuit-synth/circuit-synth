#!/usr/bin/env python3
"""
Ultra-Fast Circuit Generation using OpenRouter + Gemini-2.5-Flash

Direct OpenRouter implementation without Google ADK dependencies.
"""

import sys
import os
import asyncio
import argparse
import logging
import json
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    import aiohttp
except ImportError:
    logger.error("aiohttp not installed. Install with: uv add aiohttp")
    sys.exit(1)

# Circuit generation system prompt with complete expertise
CIRCUIT_EXPERT_PROMPT = """You are an expert circuit design engineer with complete circuit-synth knowledge. Generate working, manufacturable circuits rapidly.

CRITICAL REQUIREMENTS:
1. Generate ONLY complete, syntactically correct circuit-synth Python code
2. Use proper @circuit decorators and component definitions  
3. Include all necessary imports
4. Use verified KiCad symbols and footprints
5. Implement proper net connections with correct pin numbers

CIRCUIT-SYNTH SYNTAX TEMPLATE:
```python
from circuit_synth import *

@circuit(name="project_name")
def main():
    '''Circuit description'''
    
    # Power nets - use descriptive names
    vcc_5v = Net('VCC_5V')
    vcc_3v3 = Net('VCC_3V3') 
    gnd = Net('GND')
    
    # Components with full symbol/footprint specification
    component = Component(
        symbol="Library:SymbolName",
        ref="U1", 
        footprint="Package:FootprintName"
    )
    
    # Pin connections (use datasheet pin numbers)
    component[1] += gnd      # Pin 1 to ground
    component[2] += vcc_3v3  # Pin 2 to 3.3V
    
    return circuit

if __name__ == '__main__':
    circuit = main()
    circuit.generate_kicad_project("project_name", force_regenerate=True)
```

COMPONENT LIBRARY REFERENCE:
- ESP32: symbol="RF_Module:ESP32-S3-MINI-1", footprint="RF_Module:ESP32-S2-MINI-1"
- STM32F4: symbol="MCU_ST_STM32F4:STM32F407VETx", footprint="Package_LQFP:LQFP-100_14x14mm_P0.5mm"
- Resistors: symbol="Device:R", footprint="Resistor_SMD:R_0603_1608Metric"
- Capacitors: symbol="Device:C", footprint="Capacitor_SMD:C_0603_1608Metric"
- LEDs: symbol="Device:LED", footprint="LED_SMD:LED_0603_1608Metric"
- Linear regulators: symbol="Regulator_Linear:AMS1117-3.3", footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
- USB-C: symbol="Connector:USB_C_Receptacle_USB2.0", footprint="Connector_USB:USB_C_Receptacle_USB2.0_16P_TopMount_Horizontal"

POWER DISTRIBUTION RULES:
- Always include proper power nets (VCC_5V, VCC_3V3, GND)
- Add decoupling capacitors (10uF, 100nF) for all ICs
- Use linear regulators for clean voltage conversion
- Include proper current limiting resistors for LEDs (330R for 3.3V)

OUTPUT FORMAT:
Respond with ONLY the complete Python code. No explanations, no markdown blocks, no additional text. Start with 'from circuit_synth import *' and end with the if __name__ block."""


class FastCircuitGenerator:
    """Ultra-fast circuit generator using OpenRouter."""
    
    def __init__(self, api_key: str, model: str = "google/gemini-2.5-flash"):
        """Initialize with OpenRouter API key."""
        self.api_key = api_key
        self.model = model
        self.base_url = "https://openrouter.ai/api/v1"
        logger.info(f"Fast generator initialized with model: {model}")
    
    async def generate_circuit(self, description: str) -> str:
        """Generate circuit code from description."""
        start_time = datetime.now()
        
        logger.info(f"🚀 Generating circuit: {description}")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://circuit-synth.com",
            "X-Title": "Circuit Synth Fast Generation"
        }
        
        # Create the generation prompt
        prompt = f"""Generate complete circuit-synth Python code for: {description}

Requirements:
- Include all imports and proper syntax
- Use verified KiCad symbols and footprints from the library reference
- Add proper decoupling capacitors where needed
- Implement correct pin connections with datasheet pin numbers
- Make it ready to execute and generate KiCad files
- Use descriptive net names

{CIRCUIT_EXPERT_PROMPT}

Generate the complete Python code now:"""
        
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 4096
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=60)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"OpenRouter error {response.status}: {error_text}")
                    
                    result = await response.json()
                    
                    if "choices" not in result or not result["choices"]:
                        raise Exception("No response from OpenRouter")
                    
                    circuit_code = result["choices"][0]["message"]["content"]
                    
                    end_time = datetime.now()
                    duration = (end_time - start_time).total_seconds()
                    
                    logger.info(f"✅ Circuit generated in {duration:.2f} seconds")
                    
                    return circuit_code
                    
        except Exception as e:
            logger.error(f"❌ Generation failed: {e}")
            raise


def clean_generated_code(code: str) -> str:
    """Clean up generated code by removing markdown and extra text."""
    lines = code.strip().split('\n')
    cleaned_lines = []
    in_code_block = False
    found_imports = False
    
    for line in lines:
        # Skip markdown code block markers
        if line.strip().startswith('```'):
            in_code_block = not in_code_block
            continue
        
        # Keep lines that look like Python code
        if (line.strip().startswith('from circuit_synth') or 
            line.strip().startswith('from ') or
            line.strip().startswith('@circuit') or
            line.strip().startswith('def ') or
            line.strip().startswith('    ') or
            line.strip().startswith('if __name__') or
            in_code_block):
            cleaned_lines.append(line)
            if line.strip().startswith('from circuit_synth'):
                found_imports = True
        # Also include lines that are part of code structure
        elif found_imports and (line.strip() == '' or line.strip().startswith('#')):
            cleaned_lines.append(line)
    
    return '\n'.join(cleaned_lines) if cleaned_lines else code


async def main():
    """Main CLI entry point."""
    
    parser = argparse.ArgumentParser(
        description="Ultra-fast circuit generation using OpenRouter + Gemini-2.5-Flash",
        epilog="""
Examples:
  python fast_circuit_openrouter.py "LED blinker with 330 ohm resistor"
  python fast_circuit_openrouter.py "ESP32 board with USB-C" -o esp32_board.py
  python fast_circuit_openrouter.py "3.3V linear regulator circuit" --verbose
""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "description", 
        help="Natural language description of the circuit"
    )
    
    parser.add_argument(
        "-o", "--output", 
        help="Output file for generated circuit code"
    )
    
    parser.add_argument(
        "--model",
        default="google/gemini-2.5-flash",
        help="OpenRouter model to use (default: google/gemini-2.5-flash)"
    )
    
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check for OpenRouter API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.error("❌ OPENROUTER_API_KEY not set!")
        logger.info("Set your API key: export OPENROUTER_API_KEY=your_key_here")
        logger.info("Get your key at: https://openrouter.ai/keys")
        return 1
    
    try:
        # Create generator and generate circuit
        generator = FastCircuitGenerator(api_key, args.model)
        raw_code = await generator.generate_circuit(args.description)
        
        # Clean up the generated code
        final_code = clean_generated_code(raw_code)
        
        # Write to file if specified
        if args.output:
            with open(args.output, 'w') as f:
                f.write(final_code)
            logger.info(f"✅ Code saved to: {args.output}")
        
        # Print the generated code
        print("\n" + "="*60)
        print("🎛️  GENERATED CIRCUIT CODE")
        print("="*60)
        print(final_code)
        print("="*60)
        
        if args.output:
            print(f"\n📋 To generate KiCad files: uv run python {args.output}")
        else:
            print(f"\n💡 Tip: Use -o filename.py to save the code")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("⏹️  Generation cancelled by user")
        return 1
        
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(main())
    sys.exit(exit_code)