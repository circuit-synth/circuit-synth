#!/usr/bin/env python3
"""
Fast Circuit Generation CLI using Google ADK

Usage: python fast_circuit_cli.py "circuit description"
"""

import sys
import os
import asyncio
import argparse
import logging
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

# Add the src directory to the path so we can import circuit_synth modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

try:
    # Import ADK components
    from circuit_synth.intelligence.circuit_synth_intelligence_adk.config.adk_config import get_config
    from circuit_synth.intelligence.llm_analysis.adk_openrouter_patch import apply_openrouter_gemini_patch
    from google.adk.agents import LlmAgent
    from google.adk.models.lite_llm import LiteLLMClient
    
    # Apply the OpenRouter patch
    apply_openrouter_gemini_patch()
    
except ImportError as e:
    logger.error(f"Failed to import ADK or circuit_synth modules: {e}")
    logger.error("Make sure you have Google ADK installed: pip install google-adk")
    logger.error("And OPENROUTER_API_KEY is set")
    sys.exit(1)

# Circuit generation prompt with all the expertise
CIRCUIT_EXPERT_PROMPT = """You are an expert circuit design engineer with complete circuit-synth knowledge. Generate working, manufacturable circuits rapidly.

## CORE CAPABILITIES

### Circuit-Synth Code Generation
- Generate syntactically correct circuit-synth Python code
- Use proper @circuit decorators and component definitions
- Create hierarchical designs with subcircuits for complex projects
- Implement proper net connections and pin mappings

### Component Selection Expertise  
- Prioritize JLCPCB Basic parts for cost and availability
- Use proven, manufactureable components
- Include proper decoupling capacitors for all ICs
- Select appropriate footprints for hand assembly when possible

### Circuit-Synth Syntax Reference
```python
from circuit_synth import *

@circuit(name="project_name")
def main():
    "Circuit description"
    
    # Power nets
    vcc_5v = Net('VCC_5V')
    vcc_3v3 = Net('VCC_3V3') 
    gnd = Net('GND')
    
    # Components with verified symbols/footprints
    mcu = Component(
        symbol="MCU_ST_STM32F4:STM32F407VETx",
        ref="U1",
        footprint="Package_LQFP:LQFP-100_14x14mm_P0.5mm"
    )
    
    # Pin connections (numbers verified from datasheet)
    mcu[1] += gnd      # PE2
    mcu[25] += vcc_3v3 # VDD_1
    
    return circuit

if __name__ == '__main__':
    circuit = main()
    circuit.generate_kicad_project("project_name", force_regenerate=True)
```

Generate complete, working circuit-synth Python code that:
1. Uses proper imports and circuit decorator
2. Has clear net naming and organization  
3. Uses verified KiCad symbols/footprints
4. Includes proper pin connections
5. Is ready to execute and generate KiCad files

Respond ONLY with the complete Python code - no explanations or markdown.
"""


async def generate_circuit_with_adk(description: str, output_file: str = None) -> str:
    """Generate circuit using Google ADK."""
    
    try:
        # Get ADK configuration  
        config = get_config(preset="demo")  # Fast, cheap model for demo
        logger.info(f"Using ADK config with model: {config.default_model}")
        
        # Create LiteLLM client with OpenRouter
        client = LiteLLMClient()
        
        # Create the circuit generation agent
        agent = LlmAgent(
            name="fast_circuit_generator",
            client=client,
            instruction=CIRCUIT_EXPERT_PROMPT,
            model="openrouter/google/gemini-2.5-flash"  # Fast Gemini model
        )
        
        # Generate the circuit
        logger.info(f"🚀 Generating circuit for: {description}")
        prompt = f"Generate circuit-synth Python code for: {description}"
        
        response = await agent.generate(prompt)
        
        # Write to file if specified
        if output_file:
            with open(output_file, 'w') as f:
                f.write(response)
            logger.info(f"✅ Circuit code written to: {output_file}")
        
        return response
        
    except Exception as e:
        logger.error(f"❌ Circuit generation failed: {e}")
        raise


async def main():
    """Main CLI entry point."""
    
    parser = argparse.ArgumentParser(
        description="Fast circuit generation using Google ADK + OpenRouter",
        epilog="""
Examples:
  python fast_circuit_cli.py "ESP32 board with USB-C"
  python fast_circuit_cli.py "LED blinker with 330R resistor" -o led_circuit.py
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
        # Generate the circuit
        circuit_code = await generate_circuit_with_adk(
            description=args.description,
            output_file=args.output
        )
        
        # Print the generated code
        print("\n" + "="*60)
        print("🎛️  GENERATED CIRCUIT CODE")
        print("="*60)
        print(circuit_code)
        print("="*60)
        
        if args.output:
            print(f"\n✅ Code saved to: {args.output}")
            print(f"📋 To generate KiCad files: python {args.output}")
        
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