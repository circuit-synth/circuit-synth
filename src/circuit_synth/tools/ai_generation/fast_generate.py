#!/usr/bin/env python3
"""
Fast Circuit Generation CLI - cs-generate-fast command

Ultra-fast circuit generation using OpenRouter + Gemini-2.5-Flash.
"""

import sys
import os
import asyncio
import argparse
import logging
import json
from pathlib import Path
from datetime import datetime

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

try:
    import aiohttp
except ImportError:
    logger.error("aiohttp not installed. This should be included with circuit-synth.")
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
    vcc_5v = Net('5V')
    vcc_3v3 = Net('3V3') 
    gnd = Net('GND')
    
    # Components with full symbol/footprint specification
    component = Component(
        symbol="Library:SymbolName",
        ref="U1", 
        footprint="Package:FootprintName"
    )
    
    # Pin connections (use numeric pin numbers)
    component[1] += gnd      # Pin 1 to ground
    component[2] += vcc_3v3  # Pin 2 to 3.3V
    
    # NO return statement - @circuit decorator handles this

if __name__ == '__main__':
    circuit = main()
    circuit.generate_kicad_project("project_name", force_regenerate=True)
```

COMPONENT LIBRARY REFERENCE:
- ESP32: symbol="RF_Module:ESP32-S3-MINI-1", footprint="RF_Module:ESP32-S2-MINI-1"
  ESP32 Pin Reference: esp32[1]=GND, esp32[3]=3V3, esp32[10]=GPIO, esp32[11-16]=GPIO pins
- STM32F4: symbol="MCU_ST_STM32F4:STM32F407VETx", footprint="Package_LQFP:LQFP-100_14x14mm_P0.5mm"  
- Resistors: symbol="Device:R", footprint="Resistor_SMD:R_0603_1608Metric"
- Capacitors: symbol="Device:C", footprint="Capacitor_SMD:C_0603_1608Metric"
- LEDs: symbol="Device:LED", footprint="LED_SMD:LED_0603_1608Metric"
- Linear regulators: symbol="Regulator_Linear:NCP1117-3.3_SOT223", footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
  Regulator pins: reg[1]=GND, reg[2]=VOUT, reg[3]=VIN
- USB-C: symbol="Connector:USB_C_Plug_USB2.0", footprint="Connector_USB:USB_C_Receptacle_GCT_USB4105-xx-A_16P_TopMnt_Horizontal"

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
        self.conversation_history = []
        logger.info(f"Fast generator initialized with model: {model}")
    
    async def chat_with_user(self, message: str) -> str:
        """Interactive chat about circuit requirements."""
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://circuit-synth.com",
            "X-Title": "Circuit Synth Chat"
        }
        
        # Add user message to history
        self.conversation_history.append({"role": "user", "content": message})
        
        # Chat prompt for understanding requirements
        chat_prompt = """You are a circuit design expert helping refine circuit requirements. 
        
Ask clarifying questions about:
- Specific components or chip families
- Power requirements (voltage, current)
- Interface needs (USB, SPI, I2C, etc.)
- Physical constraints (size, connectors)
- Performance requirements
- Manufacturing preferences (SMD vs through-hole)

Be conversational and helpful. Ask 1-2 focused questions at a time."""
        
        # Build conversation with context
        messages = [{"role": "system", "content": chat_prompt}] + self.conversation_history
        
        data = {
            "model": self.model,
            "messages": messages,
            "temperature": 0.3,
            "max_tokens": 2048
        }
        
        try:
            async with aiohttp.ClientSession() as session:
                async with session.post(
                    f"{self.base_url}/chat/completions",
                    headers=headers,
                    json=data,
                    timeout=aiohttp.ClientTimeout(total=30)
                ) as response:
                    if response.status != 200:
                        error_text = await response.text()
                        raise Exception(f"OpenRouter chat error {response.status}: {error_text}")
                    
                    result = await response.json()
                    
                    if "choices" not in result or not result["choices"]:
                        raise Exception("No chat response from OpenRouter")
                    
                    assistant_response = result["choices"][0]["message"]["content"]
                    
                    # Add assistant response to history
                    self.conversation_history.append({"role": "assistant", "content": assistant_response})
                    
                    return assistant_response
                    
        except Exception as e:
            logger.error(f"❌ Chat failed: {e}")
            raise

    async def generate_circuit(self, description: str, multi_file: bool = False) -> dict:
        """Generate circuit code from description.
        
        Returns:
            dict with 'main_file' and optionally 'subcircuits' keys
        """
        start_time = datetime.now()
        
        logger.info(f"🚀 Generating circuit: {description}")
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://circuit-synth.com",
            "X-Title": "Circuit Synth Fast Generation"
        }
        
        # Include conversation history for context
        context = ""
        if self.conversation_history:
            context = "\n\nContext from our conversation:\n"
            for msg in self.conversation_history:
                if msg["role"] == "user":
                    context += f"User: {msg['content']}\n"
                else:
                    context += f"Assistant: {msg['content']}\n"
        
        # Create the generation prompt
        base_prompt = f"""Generate complete circuit-synth Python code for: {description}{context}

Requirements:
- Include all imports and proper syntax
- Use verified KiCad symbols and footprints from the library reference
- Add proper decoupling capacitors where needed  
- Implement correct pin connections with datasheet pin numbers
- Make it ready to execute and generate KiCad files
- Use descriptive net names"""

        if multi_file:
            prompt = f"""{base_prompt}

MULTI-FILE HIERARCHICAL DESIGN:
Generate a hierarchical circuit design with separate files for complex subcircuits.

OUTPUT FORMAT - JSON with files:
{{
  "main_file": {{
    "filename": "main.py",
    "content": "from circuit_synth import *\\n\\n# Main circuit code here..."
  }},
  "subcircuits": [
    {{
      "filename": "power_supply.py", 
      "content": "from circuit_synth import *\\n\\n# Power supply subcircuit..."
    }},
    {{
      "filename": "mcu_module.py",
      "content": "from circuit_synth import *\\n\\n# MCU module subcircuit..."
    }}
  ]
}}

Create separate subcircuit files for:
- Power supplies/regulators (power_supply.py)
- MCU modules (mcu_module.py) 
- Interface circuits (interfaces.py)
- Sensor modules (sensors.py)
- Communication modules (comm_module.py)

{CIRCUIT_EXPERT_PROMPT}

Generate the JSON structure with all files now:"""
        else:
            prompt = f"""{base_prompt}

{CIRCUIT_EXPERT_PROMPT}

Generate the complete Python code now:"""
        
        data = {
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "temperature": 0.1,
            "max_tokens": 8192  # Increased for complex circuits
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
                    
                    circuit_response = result["choices"][0]["message"]["content"]
                    
                    end_time = datetime.now()
                    duration = (end_time - start_time).total_seconds()
                    
                    logger.info(f"✅ Circuit generated in {duration:.2f} seconds")
                    
                    if multi_file:
                        # Try to parse JSON response
                        try:
                            import re
                            # Extract JSON from response
                            json_match = re.search(r'\{.*\}', circuit_response, re.DOTALL)
                            if json_match:
                                circuit_data = json.loads(json_match.group())
                                return circuit_data
                            else:
                                # Fallback to single file if JSON parsing fails
                                logger.warning("Failed to parse multi-file JSON, falling back to single file")
                                return {"main_file": {"filename": "main.py", "content": circuit_response}}
                        except json.JSONDecodeError:
                            logger.warning("Failed to decode multi-file JSON, falling back to single file")
                            return {"main_file": {"filename": "main.py", "content": circuit_response}}
                    else:
                        return {"main_file": {"filename": "main.py", "content": circuit_response}}
                    
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


async def interactive_chat_session(generator: FastCircuitGenerator, initial_description: str):
    """Interactive chat session to refine circuit requirements."""
    print("\n🗣️  INTERACTIVE CIRCUIT DESIGN CHAT")
    print("=" * 50)
    print("💡 Let's discuss your circuit requirements!")
    print("💬 Type your questions/requirements below")
    print("⌨️  Type 'generate' when ready to create the circuit")
    print("⌨️  Type 'quit' to exit\n")
    
    # Start with initial description
    print(f"🎯 Initial request: {initial_description}")
    
    try:
        # Get initial AI response about the circuit
        response = await generator.chat_with_user(initial_description)
        print(f"\n🤖 Assistant: {response}\n")
        
        while True:
            # Get user input
            try:
                user_input = input("👤 You: ").strip()
            except (EOFError, KeyboardInterrupt):
                print("\n⏹️  Chat session ended")
                return False
            
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("👋 Chat session ended")
                return False
            elif user_input.lower() in ['generate', 'gen', 'create']:
                print("✅ Ready to generate circuit!")
                return True
            elif user_input:
                # Continue conversation
                try:
                    response = await generator.chat_with_user(user_input)
                    print(f"\n🤖 Assistant: {response}\n")
                except Exception as e:
                    print(f"❌ Chat error: {e}")
                    continue
    
    except Exception as e:
        logger.error(f"💥 Chat session failed: {e}")
        return False

def save_multi_file_circuit(circuit_data: dict, base_name: str) -> list:
    """Save multi-file circuit data to files."""
    saved_files = []
    
    # Save main file
    main_file = circuit_data.get("main_file", {})
    main_filename = main_file.get("filename", f"{base_name}_main.py")
    main_content = clean_generated_code(main_file.get("content", ""))
    
    main_path = Path(main_filename)
    with open(main_path, 'w') as f:
        f.write(main_content)
    saved_files.append(main_path)
    logger.info(f"✅ Main circuit saved to: {main_path.absolute()}")
    
    # Save subcircuit files
    subcircuits = circuit_data.get("subcircuits", [])
    for sub in subcircuits:
        sub_filename = sub.get("filename", f"{base_name}_subcircuit.py")
        sub_content = clean_generated_code(sub.get("content", ""))
        
        sub_path = Path(sub_filename)
        with open(sub_path, 'w') as f:
            f.write(sub_content)
        saved_files.append(sub_path)
        logger.info(f"✅ Subcircuit saved to: {sub_path.absolute()}")
    
    return saved_files

async def async_main(args):
    """Async main function."""
    
    # Check for OpenRouter API key
    api_key = os.getenv("OPENROUTER_API_KEY")
    if not api_key:
        logger.error("❌ OPENROUTER_API_KEY not set!")
        logger.info("Set your API key: export OPENROUTER_API_KEY=your_key_here")
        logger.info("Get your key at: https://openrouter.ai/keys")
        return 1
    
    try:
        # Create generator
        generator = FastCircuitGenerator(api_key, args.model)
        
        # Interactive chat if enabled
        if args.chat:
            should_generate = await interactive_chat_session(generator, args.description)
            if not should_generate:
                logger.info("🚫 Generation cancelled by user")
                return 0
        
        # Generate circuit (single or multi-file)
        multi_file_mode = getattr(args, 'multi_file', False)
        circuit_data = await generator.generate_circuit(args.description, multi_file_mode)
        
        # Create base name for files
        if not args.output:
            safe_name = "".join(c if c.isalnum() or c in "_ " else "" for c in args.description[:30])
            base_name = safe_name.replace(" ", "_").lower().strip("_")
        else:
            base_name = Path(args.output).stem
        
        if multi_file_mode and "subcircuits" in circuit_data:
            # Multi-file generation
            saved_files = save_multi_file_circuit(circuit_data, base_name)
            
            print("\n" + "="*60)
            print("🏗️  MULTI-FILE CIRCUIT PROJECT GENERATED")
            print("="*60)
            
            for file_path in saved_files:
                print(f"📁 {file_path.name}")
                # Show first few lines of each file
                with open(file_path, 'r') as f:
                    lines = f.readlines()[:5]
                    for line in lines:
                        print(f"   {line.rstrip()}")
                    if len(lines) >= 5:
                        print("   ...")
                print()
            
            print("="*60)
            print(f"🎯 Total files generated: {len(saved_files)}")
            print(f"🚀 To generate KiCad files, run the main file:")
            print(f"   python {saved_files[0].name}")
            
        else:
            # Single file generation
            main_file = circuit_data.get("main_file", {})
            final_code = clean_generated_code(main_file.get("content", ""))
            
            output_filename = args.output or f"{base_name}_circuit.py"
            output_path = Path(output_filename)
            
            with open(output_path, 'w') as f:
                f.write(final_code)
            logger.info(f"✅ Circuit code saved to: {output_path.absolute()}")
            
            # Print the generated code
            print("\n" + "="*60)
            print("🎛️  GENERATED CIRCUIT CODE")
            print("="*60)
            print(final_code)
            print("="*60)
            print(f"\n📁 Saved to: {output_path.absolute()}")
            print(f"📋 To generate KiCad files: python {output_filename}")
        
        return 0
        
    except KeyboardInterrupt:
        logger.info("⏹️  Generation cancelled by user")
        return 1
        
    except Exception as e:
        logger.error(f"💥 Fatal error: {e}")
        return 1


def main():
    """Main CLI entry point."""
    
    parser = argparse.ArgumentParser(
        description="Ultra-fast circuit generation using OpenRouter + Gemini-2.5-Flash",
        epilog="""
Examples:
  cs-generate-fast "LED blinker with 330 ohm resistor"
  cs-generate-fast "ESP32 board with USB-C" -o esp32_board.py
  cs-generate-fast "3.3V linear regulator circuit" --verbose
  cs-generate-fast "BB-8 droid controller" --chat --multi-file
  cs-generate-fast "IoT sensor node" -c -m --verbose
""",
        formatter_class=argparse.RawDescriptionHelpFormatter
    )
    
    parser.add_argument(
        "description", 
        help="Natural language description of the circuit"
    )
    
    parser.add_argument(
        "-o", "--output", 
        help="Output file for generated circuit code (auto-generated if not provided)"
    )
    
    parser.add_argument(
        "--model",
        default="google/gemini-2.5-flash",
        help="OpenRouter model to use (default: google/gemini-2.5-flash)"
    )
    
    parser.add_argument(
        "--chat", "-c",
        action="store_true",
        help="Enable interactive chat before circuit generation"
    )
    
    parser.add_argument(
        "--multi-file", "-m",
        action="store_true",
        help="Generate multiple files for hierarchical circuits"
    )
    
    parser.add_argument(
        "--verbose", "-v", 
        action="store_true",
        help="Enable verbose logging"
    )
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Run the async main
    exit_code = asyncio.run(async_main(args))
    sys.exit(exit_code)


if __name__ == "__main__":
    main()