#!/usr/bin/env python3
"""
Simple Fast Circuit Generation using Google ADK + OpenRouter

This is a standalone implementation that doesn't rely on the intelligence modules.
"""

import sys
import os
import asyncio
import argparse
import logging
from pathlib import Path
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    # Try to import Google ADK directly
    from google.adk.agents import LlmAgent
    from google.adk.models.lite_llm import LiteLLMClient
    logger.info("✅ Google ADK imported successfully")
except ImportError as e:
    logger.error(f"Google ADK not available: {e}")
    logger.error("Install with: uv add google-adk")
    sys.exit(1)

# Circuit generation prompt with complete circuit-synth expertise
CIRCUIT_EXPERT_SYSTEM = """You are an expert circuit design engineer with complete circuit-synth knowledge. Generate working, manufacturable circuits rapidly.

CRITICAL REQUIREMENTS:
1. Generate ONLY complete, syntactically correct circuit-synth Python code
2. Use proper @circuit decorators and component definitions  
3. Include all necessary imports
4. Use verified KiCad symbols and footprints
5. Implement proper net connections with correct pin numbers

CIRCUIT-SYNTH SYNTAX:
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

COMPONENT GUIDELINES:
- ESP32: "RF_Module:ESP32-S3-MINI-1" with "RF_Module:ESP32-S2-MINI-1"
- STM32: "MCU_ST_STM32F4:STM32F407VETx" with "Package_LQFP:LQFP-100_14x14mm_P0.5mm"
- Resistors: "Device:R" with "Resistor_SMD:R_0603_1608Metric" 
- Capacitors: "Device:C" with "Capacitor_SMD:C_0603_1608Metric"
- LEDs: "Device:LED" with "LED_SMD:LED_0603_1608Metric"
- Linear regulators: "Regulator_Linear:AMS1117-3.3" with "Package_TO_SOT_SMD:SOT-223-3_TabPin2"

POWER DISTRIBUTION:
- Always include proper power nets (VCC_5V, VCC_3V3, GND)
- Add decoupling capacitors for all ICs
- Use linear regulators for voltage conversion
- Include proper current limiting for LEDs

OUTPUT FORMAT:
Respond with ONLY the complete Python code. No explanations, no markdown blocks, no additional text."""


class FastCircuitGenerator:
    """Fast circuit generator using Google ADK."""
    
    def __init__(self):
        """Initialize the generator."""
        self.client = LiteLLMClient()
        self.agent = LlmAgent(
            name="fast_circuit_generator",
            client=self.client,
            instruction=CIRCUIT_EXPERT_SYSTEM,
            model="openrouter/google/gemini-2.5-flash"
        )
        logger.info("Fast circuit generator initialized")
    
    async def generate_circuit(self, description: str) -> str:
        """Generate circuit code from description."""
        start_time = datetime.now()
        
        logger.info(f"🚀 Generating circuit: {description}")
        
        try:
            # Create the generation prompt
            prompt = f"""Generate complete circuit-synth Python code for: {description}

Requirements:
- Include all imports and proper syntax
- Use verified KiCad symbols and footprints  
- Add proper decoupling capacitors
- Implement correct pin connections
- Make it ready to execute

Generate the code now:"""
            
            # Generate the circuit
            response = await self.agent.generate(prompt)
            
            end_time = datetime.now()
            duration = (end_time - start_time).total_seconds()
            
            logger.info(f"✅ Circuit generated in {duration:.2f} seconds")
            
            return response
            
        except Exception as e:
            logger.error(f"❌ Generation failed: {e}")
            raise


async def main():
    """Main CLI entry point."""
    
    parser = argparse.ArgumentParser(
        description="Fast circuit generation using Google ADK + OpenRouter + Gemini",
        epilog="""
Examples:
  python fast_circuit_simple.py "LED blinker with 330 ohm resistor"
  python fast_circuit_simple.py "ESP32 board with USB-C" -o esp32_board.py
  python fast_circuit_simple.py "3.3V linear regulator circuit"
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
        "--verbose", "-v", 
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Check for OpenRouter API key
    if not os.getenv("OPENROUTER_API_KEY"):
        logger.error("❌ OPENROUTER_API_KEY not set!")
        logger.info("Set your API key: export OPENROUTER_API_KEY=your_key_here")
        return 1
    
    try:
        # Create generator and generate circuit
        generator = FastCircuitGenerator()
        circuit_code = await generator.generate_circuit(args.description)
        
        # Clean up the response (remove any markdown or extra text)
        lines = circuit_code.strip().split('\n')
        code_lines = []
        in_code = False
        
        for line in lines:
            if line.strip().startswith('```'):
                in_code = not in_code
                continue
            elif in_code or line.strip().startswith('from ') or line.strip().startswith('@circuit') or '    ' in line:
                code_lines.append(line)
        
        final_code = '\n'.join(code_lines) if code_lines else circuit_code
        
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