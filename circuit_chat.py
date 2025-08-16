#!/usr/bin/env python3
"""
Circuit Design Chat Interface

Natural conversation interface for circuit design with ESP32/STM32 expertise.
No pre-made patterns - just smart circuit generation through conversation.
"""

import asyncio
import os
import sys
import readline
from datetime import datetime
from pathlib import Path
from typing import List

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from circuit_synth.fast_generation.models import OpenRouterModel
from circuit_synth.fast_generation.pin_finder import pin_finder


class CircuitChat:
    """Conversational circuit design assistant"""
    
    def __init__(self):
        self.model = None
        self.conversation_history = []
        self.session_start = datetime.now()
        
    def log_exchange(self, user_msg: str, assistant_msg: str, metadata: dict = None):
        """Log a complete conversation exchange"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.conversation_history.append({
            "timestamp": timestamp,
            "user": user_msg,
            "assistant": assistant_msg,
            "metadata": metadata or {}
        })
    
    def build_context(self) -> str:
        """Build comprehensive context for circuit design"""
        context = """You are a professional circuit design engineer specializing in ESP32 and STM32 circuits using circuit-synth.

## CIRCUIT-SYNTH SYNTAX (CRITICAL):
```python
from circuit_synth import *

@circuit(name="CircuitName")
def my_circuit():
    # Create nets first
    vcc_3v3 = Net('VCC_3V3')  
    gnd = Net('GND')
    
    # Create components with EXACT verified symbols
    mcu = Component(
        symbol="RF_Module:ESP32-C6-MINI-1",
        ref="U",
        footprint="RF_Module:ESP32-C6-MINI-1"
    )
    
    # Connect pins - NO .pin() method!
    mcu["3V3"] += vcc_3v3
    mcu["GND"] += gnd
    
if __name__ == "__main__":
    circuit = my_circuit()
    circuit.generate_kicad_project(
        project_name="MyProject",
        placement_algorithm="hierarchical",
        generate_pcb=True
    )
    print("✅ KiCad project generated!")
```

## VERIFIED WORKING COMPONENTS:

### ESP32 Family:
- **ESP32-C6**: symbol="RF_Module:ESP32-C6-MINI-1", footprint="RF_Module:ESP32-C6-MINI-1"
  - Pins: "3V3", "GND", "IO0"-"IO23", "TXD0", "RXD0", "EN", "IO18"(USB_D+), "IO19"(USB_D-)
  - Features: WiFi 6, Bluetooth 5, Thread/Zigbee, USB support
- **ESP32-S3**: symbol="MCU_Espressif:ESP32-S3", footprint="Package_DFN_QFN:QFN-56-1EP_7x7mm_P0.4mm_EP5.6x5.6mm"
  - Pins: "VDD", "VSS", "EN", "IO0"-"IO48", "USB_DM", "USB_DP", "XTAL_P", "XTAL_N"
  - Features: Dual-core, AI acceleration, camera support

### STM32 Family:
- **STM32F411**: symbol="MCU_ST_STM32F4:STM32F411CEUx", footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm"
  - Pins: "VDD", "VSS", "PA0"-"PA15", "PB0"-"PB15", "PC13"-"PC15", "NRST", "BOOT0"
  - Features: 100MHz ARM Cortex-M4, USB OTG, low power
- **STM32F407**: symbol="MCU_ST_STM32F4:STM32F407VETx", footprint="Package_QFP:LQFP-100_14x14mm_P0.5mm"
  - Pins: "VDD", "VDDA", "VSS", "VSSA", "PA0"-"PA15", "PB0"-"PB15", etc.
  - Features: 168MHz, FPU, Ethernet, CAN

### Common Components:
- **Resistor**: symbol="Device:R", footprint="Resistor_SMD:R_0603_1608Metric"
- **Capacitor**: symbol="Device:C", footprint="Capacitor_SMD:C_0603_1608Metric"
- **LED**: symbol="Device:LED", footprint="LED_SMD:LED_0603_1608Metric"
- **Crystal**: symbol="Device:Crystal", footprint="Crystal:Crystal_SMD_3225-4Pin_3.2x2.5mm"
- **USB-C**: symbol="Connector:USB_C_Receptacle_USB2.0_16P", footprint="Connector_USB:USB_C_Receptacle_GCT_USB4085"
- **Header**: symbol="Connector_Generic:Conn_01x10", footprint="Connector_PinHeader_2.54mm:PinHeader_1x10_P2.54mm_Vertical"

## DESIGN PATTERNS:

### ESP32 Development Board:
- USB-C connector with CC resistors (5.1k to GND)
- 3.3V LDO regulator (AMS1117-3.3 or similar)  
- Crystal oscillator (40MHz for ESP32-S3, internal for ESP32-C6)
- Reset button, boot button
- Status LED on GPIO pin
- Debug header (UART, power, EN, GPIO0)
- Decoupling capacitors (100nF, 10uF)

### STM32 Development Board:
- External crystal (8MHz HSE)
- SWD debug connector (SWDIO, SWCLK, VCC, GND, NRST)
- Reset button with 10k pullup
- BOOT0 jumper/button
- 3.3V regulation from USB or external
- Decoupling on all VDD pins
- User LED and button

### Power Supply Design:
- USB input protection (fuse, ESD)
- 5V to 3.3V regulation (linear or switching)
- Power indicator LED
- Bulk and decoupling capacitors
- Enable/shutdown control

## CONVERSATION STYLE:
- Ask clarifying questions about requirements
- Suggest appropriate components based on needs
- Generate complete working circuit-synth code
- Explain design decisions
- Provide practical engineering advice
- Generate files that actually work when run

## CRITICAL RULES:
1. NEVER use markdown code fences - output raw Python only
2. Use EXACT symbol names from verified list above
3. Use component["pin"] += net syntax (NOT .pin())
4. Always include @circuit decorator and __main__ section
5. Test knowledge - if unsure about pins, say so
6. Focus on practical, manufacturable designs
"""
        return context
    
    async def initialize_model(self):
        """Initialize the OpenRouter model"""
        print("🔧 Initializing Circuit Design AI...")
        
        api_key = os.getenv("OPENROUTER_API_KEY") 
        if not api_key:
            print("❌ OPENROUTER_API_KEY not set!")
            print("   Set it with: export OPENROUTER_API_KEY=your_key_here")
            return False
        
        print(f"✅ API Key found: {api_key[:10]}...")
        
        try:
            self.model = OpenRouterModel(
                api_key=api_key,
                model="google/gemini-2.5-flash"
            )
            print("✅ Circuit design AI ready")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize AI: {e}")
            return False
    
    def _extract_components_from_message(self, message: str) -> List[str]:
        """Extract likely component symbols from user message"""
        components = []
        
        # Common component mappings
        component_map = {
            # ESP32 variants
            "esp32-s3": "MCU_Espressif:ESP32-S3",
            "esp32-c6": "RF_Module:ESP32-C6-MINI-1",
            "esp32": "RF_Module:ESP32-C6-MINI-1",  # Default to C6
            
            # STM32 variants  
            "stm32f411": "MCU_ST_STM32F4:STM32F411CEUx",
            "stm32f407": "MCU_ST_STM32F4:STM32F407VETx",
            "stm32": "MCU_ST_STM32F4:STM32F411CEUx",  # Default to F411
            
            # Common components
            "resistor": "Device:R",
            "capacitor": "Device:C", 
            "led": "Device:LED",
            "crystal": "Device:Crystal",
            "usb-c": "Connector:USB_C_Receptacle_USB2.0_16P",
            "usb_c": "Connector:USB_C_Receptacle_USB2.0_16P",
            "imu": "Sensor_Motion:MPU-6050",
            "temperature": "Sensor_Temperature:DS18B20",
            "temp": "Sensor_Temperature:DS18B20"
        }
        
        message_lower = message.lower()
        for keyword, symbol in component_map.items():
            if keyword in message_lower:
                components.append(symbol)
        
        return list(set(components))  # Remove duplicates

    async def chat(self, user_message: str) -> str:
        """Have a conversation about circuit design"""
        if not self.model:
            return "❌ AI not initialized"
        
        # Extract likely components from user message
        components = self._extract_components_from_message(user_message)
        
        # Build conversation history for context
        conversation_context = ""
        for exchange in self.conversation_history[-5:]:  # Last 5 exchanges
            conversation_context += f"User: {exchange['user']}\nAssistant: {exchange['assistant']}\n\n"
        
        # Build full prompt with pin finding instruction
        full_prompt = f"""Previous conversation:
{conversation_context}

Current user message: {user_message}

INSTRUCTIONS: You are a professional circuit design engineer. 

If the user is asking for a complete circuit design:
1. FIRST identify the components needed
2. Get exact pin information for each component (this is critical!)
3. Generate working circuit-synth Python code with correct pin names
4. Use the @circuit decorator and proper syntax

If they're asking questions or need clarification, provide helpful guidance about ESP32/STM32 circuit design.

CRITICAL: Never guess pin names - use exact pin names from component datasheets."""

        try:
            # Get pin information for detected components
            pin_info = ""
            if components:
                print(f"🔍 Found components: {', '.join(components)}")
                print("📍 Getting pin information...")
                
                pin_parts = []
                for symbol in components:
                    try:
                        pin_data = pin_finder.get_pin_info_for_ai(symbol)
                        pin_parts.append(pin_data)
                    except Exception as e:
                        pin_parts.append(f"❌ Could not get pins for {symbol}: {e}")
                
                pin_info = "\n\n".join(pin_parts)
            
            # Get AI response with pin information
            context = {
                "conversation_context": conversation_context,
                "components": components,
                "pin_information": pin_info
            }
            
            response = await self.model.generate_circuit(
                full_prompt, 
                context,
                max_tokens=4000
            )
            
            if response.success:
                # Clean up response (remove markdown if present)
                content = response.content.strip()
                
                # Remove code fences more thoroughly
                lines = content.split('\n')
                clean_lines = []
                
                for line in lines:
                    line_clean = line.strip()
                    # Skip markdown fence lines
                    if line_clean in ['```python', '```', '```py']:
                        continue
                    clean_lines.append(line)
                
                content = '\n'.join(clean_lines).strip()
                
                # Log the exchange
                metadata = {
                    "tokens": response.tokens_used,
                    "latency_ms": response.latency_ms,
                    "model": response.model
                }
                self.log_exchange(user_message, content, metadata)
                
                return content
            else:
                error_msg = f"❌ AI Error: {response.error}"
                self.log_exchange(user_message, error_msg)
                return error_msg
                
        except Exception as e:
            error_msg = f"❌ Chat error: {e}"
            self.log_exchange(user_message, error_msg)
            return error_msg
    
    def show_history(self):
        """Show conversation history"""
        print("\n" + "=" * 80)
        print("📜 CONVERSATION HISTORY")
        print("=" * 80)
        
        for i, exchange in enumerate(self.conversation_history, 1):
            print(f"\n[{exchange['timestamp']}] Exchange #{i}")
            print("-" * 40)
            print(f"👤 YOU: {exchange['user']}")
            print()
            print(f"🤖 ASSISTANT:")
            
            # Format assistant response nicely
            assistant_msg = exchange['assistant']
            if len(assistant_msg) > 500:
                lines = assistant_msg.split('\n')
                if len(lines) > 20:
                    # Show first 10 and last 5 lines for code
                    for line in lines[:10]:
                        print(f"   {line}")
                    print("   ... (truncated) ...")
                    for line in lines[-5:]:
                        print(f"   {line}")
                else:
                    for line in lines:
                        print(f"   {line}")
            else:
                for line in assistant_msg.split('\n'):
                    print(f"   {line}")
            
            # Show metadata
            if 'metadata' in exchange and exchange['metadata']:
                meta = exchange['metadata']
                if 'tokens' in meta:
                    print(f"\n   📊 {meta['tokens']} tokens, {meta.get('latency_ms', 0):.0f}ms")
            print()
    
    def save_code_if_present(self, response: str) -> bool:
        """Save code to file if the response contains circuit code"""
        if "from circuit_synth import" in response and "@circuit" in response:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"circuit_{timestamp}.py"
            
            with open(filename, 'w') as f:
                f.write(response)
            
            print(f"\n💾 Circuit code saved to: {filename}")
            print("   Run with: python " + filename)
            return True
        return False
    
    async def run(self):
        """Main chat loop"""
        print("=" * 80)
        print("🎛️  CIRCUIT DESIGN CHAT")
        print("=" * 80)
        print("💬 Natural conversation interface for ESP32/STM32 circuit design")
        print("🎯 Just describe what you want to build!")
        print()
        print("Examples:")
        print("  'I need an ESP32 board with USB-C and a temperature sensor'")
        print("  'Design an STM32F411 development board with SWD debug'")
        print("  'How do I add a crystal oscillator to my ESP32?'")
        print("  'Show me a simple LED blinker circuit'")
        print()
        print("Commands: 'history' (show chat), 'quit' (exit)")
        print("=" * 80)
        
        # Initialize
        if not await self.initialize_model():
            return
        
        print("\n💬 Ready! What circuit do you want to design?")
        
        while True:
            try:
                # Get user input  
                user_input = input("\n🎛️  > ").strip()
                
                if not user_input:
                    continue
                
                # Handle special commands
                if user_input.lower() in ['quit', 'exit', 'bye']:
                    print("\n👋 Happy circuit designing!")
                    break
                
                elif user_input.lower() == 'history':
                    self.show_history()
                    continue
                
                elif user_input.lower() == 'help':
                    print("\n🎯 Just describe your circuit needs naturally!")
                    print("Examples:")
                    print("  - 'ESP32 board with WiFi and temperature sensor'")
                    print("  - 'STM32 motor controller with encoder feedback'")
                    print("  - 'USB-C power supply for 3.3V circuits'")
                    print("  - 'How do I connect an IMU to ESP32?'")
                    continue
                
                # Get AI response
                print("\n🤖 Thinking...")
                response = await self.chat(user_input)
                
                # Show response
                print("\n" + "=" * 80)
                print(response)
                print("=" * 80)
                
                # Save code if generated
                self.save_code_if_present(response)
                
            except KeyboardInterrupt:
                print("\n\n👋 Goodbye!")
                break
            except EOFError:
                print("\n\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"\n❌ Error: {e}")


async def main():
    """Main entry point"""
    chat = CircuitChat()
    await chat.run()


if __name__ == "__main__":
    asyncio.run(main())