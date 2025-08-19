#!/usr/bin/env python3
"""
NEW Circuit Design Chat Interface

Professional hierarchical circuit generation with proper components:
- Always generates hierarchical projects (like example_project/circuit-synth/)
- Includes proper passives (decoupling caps, pull-ups, regulators)
- Asks clarifying questions when needed
- Adds ESD protection and CC resistors for USB circuits
"""

import asyncio
import os
import sys
import readline
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from circuit_synth.fast_generation.core import FastCircuitGenerator
from circuit_synth.fast_generation.models import OpenRouterModel


class ProfessionalCircuitChat:
    """Professional circuit design chat with hierarchical generation"""
    
    def __init__(self):
        self.fast_generator = FastCircuitGenerator()
        self.conversation_history = []
        self.session_start = datetime.now()
        self.pending_generation = None  # Track if we're waiting for answers to questions
        
    async def initialize(self):
        """Initialize the chat system"""
        print("🔧 Initializing Professional Circuit Design AI...")
        
        # Check API key
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            print("❌ OpenRouter API key not found!")
            print("   Set: export OPENROUTER_API_KEY=your_key_here")
            return False
        
        print(f"✅ API Key found: {api_key[:10]}...")
        print("✅ Professional circuit design AI ready")
        return True
    
    def analyze_request(self, message: str) -> Dict[str, Any]:
        """Analyze user request to determine circuit requirements"""
        message_lower = message.lower()
        
        analysis = {
            "mcu_type": None,
            "needs_usb": False,
            "needs_power_reg": False,
            "peripherals": [],
            "questions": []
        }
        
        # Detect MCU
        if "esp32" in message_lower:
            if "s3" in message_lower:
                analysis["mcu_type"] = "ESP32-S3"
            elif "c6" in message_lower:
                analysis["mcu_type"] = "ESP32-C6"
            else:
                analysis["mcu_type"] = "ESP32"
                analysis["questions"].append("Which ESP32? (S3 recommended for USB, C6 for WiFi 6)")
                
        elif "stm32" in message_lower:
            if "f411" in message_lower:
                analysis["mcu_type"] = "STM32F411"
            else:
                analysis["mcu_type"] = "STM32"
                analysis["questions"].append("Which STM32? (F411 recommended for general use)")
        
        # Detect USB requirement  
        if any(term in message_lower for term in ["usb", "usb-c", "programming"]):
            analysis["needs_usb"] = True
            analysis["needs_power_reg"] = True
        
        # Detect peripherals
        peripherals = {
            "imu": "MPU-6050 IMU sensor",
            "mpu": "MPU-6050 IMU sensor", 
            "neopixel": "WS2812B NeoPixel LEDs",
            "led": "Status LEDs",
            "motor": "Motor control",
            "stepper": "Stepper motor",
            "temperature": "Temperature sensor",
            "display": "Display interface"
        }
        
        for keyword, description in peripherals.items():
            if keyword in message_lower:
                analysis["peripherals"].append(description)
        
        return analysis
    
    def ask_questions(self, analysis: Dict[str, Any]) -> str:
        """Generate clarifying questions"""
        questions = analysis["questions"].copy()
        
        # Add specific questions based on peripherals
        if "Motor control" in analysis["peripherals"] or "Stepper motor" in analysis["peripherals"]:
            questions.append("Motor voltage? (12V typical for steppers)")
            
        if "WS2812B NeoPixel LEDs" in analysis["peripherals"]:
            questions.append("How many NeoPixels? (affects power requirements)")
        
        if not questions:
            return None
            
        question_text = "🤔 I need a few details to create the best design:\n\n"
        for i, q in enumerate(questions, 1):
            question_text += f"  {i}. {q}\n"
        question_text += "\n💡 Or say 'use defaults' and I'll make good engineering choices!"
        
        return question_text
    
    async def generate_professional_project(self, user_message: str, analysis: Dict[str, Any]) -> str:
        """Generate a professional hierarchical project"""
        try:
            # Determine project type
            if analysis["mcu_type"] and "ESP32" in analysis["mcu_type"]:
                project_type = "esp32_complete_board"
                mcu_name = analysis["mcu_type"]
            elif analysis["mcu_type"] and "STM32" in analysis["mcu_type"]:
                project_type = "stm32_complete_board" 
                mcu_name = analysis["mcu_type"]
            else:
                return "❌ Please specify ESP32 or STM32 for circuit generation"
            
            # Create project
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            project_name = f"{mcu_name}_Professional_{timestamp}"
            output_dir = Path("professional_circuits")
            
            print(f"🏗️  Generating professional {project_type}...")
            
            result = self.fast_generator.generate_hierarchical_project(
                project_type=project_type,
                output_dir=output_dir,
                project_name=project_name
            )
            
            if not result["success"]:
                return f"❌ Generation failed: {result.get('error')}"
            
            project_path = Path(result["project_path"])
            
            # Success response
            response = f"✅ **Professional {mcu_name} Circuit Generated!**\n\n"
            response += f"📁 **Project:** {project_path}\n\n"
            
            # Show hierarchical structure
            if project_path.exists():
                py_files = sorted(project_path.glob("*.py"))
                response += f"🏗️  **Hierarchical Architecture** ({len(py_files)} subcircuits):\n"
                
                for file_path in py_files:
                    if file_path.name == "main.py":
                        response += f"   📋 {file_path.name} - Project orchestrator\n"
                    elif "usb" in file_path.name:
                        response += f"   🔌 {file_path.name} - USB-C + CC resistors + ESD protection\n"
                    elif "power" in file_path.name:
                        response += f"   ⚡ {file_path.name} - 5V→3.3V regulation + filtering\n"
                    elif "mcu" in file_path.name:
                        response += f"   🧠 {file_path.name} - {mcu_name} + decoupling + support\n"
                    elif "debug" in file_path.name:
                        response += f"   🔧 {file_path.name} - Debug/programming interface\n"
                    elif "led" in file_path.name:
                        response += f"   💡 {file_path.name} - Status LEDs + current limiting\n"
                    else:
                        response += f"   📄 {file_path.name}\n"
            
            # Professional features
            response += f"\n🎯 **Professional Features:**\n"
            if analysis["needs_usb"]:
                response += f"   ✅ USB-C with CC1/CC2 pull-down resistors (5.1kΩ)\n"
                response += f"   ✅ ESD protection (USBLC6-2P6) on data lines\n"
            if analysis["needs_power_reg"]:
                response += f"   ✅ Clean 5V→3.3V regulation (AMS1117-3.3)\n"
                response += f"   ✅ Input/output filtering capacitors\n"
            response += f"   ✅ Decoupling capacitors on all power rails\n"
            response += f"   ✅ Pull-up resistors where needed (EN, I2C)\n"
            response += f"   ✅ Debug interface for development\n"
            response += f"   ✅ Modular design like example_project/circuit-synth/\n"
            
            # Usage instructions
            response += f"\n🚀 **To Use This Project:**\n"
            response += f"```bash\n"
            response += f"cd {project_path}\n"
            response += f"python3 main.py  # Generate complete KiCad project\n"
            response += f"```\n\n"
            response += f"🔍 **Each subcircuit can be tested individually!**"
            
            # Log successful generation
            self.conversation_history.append({
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "user": user_message,
                "assistant": response,
                "metadata": {"project_path": str(project_path), "success": True}
            })
            
            return response
            
        except Exception as e:
            error_msg = f"❌ Generation error: {e}"
            self.conversation_history.append({
                "timestamp": datetime.now().strftime("%H:%M:%S"),
                "user": user_message, 
                "assistant": error_msg,
                "metadata": {"success": False, "error": str(e)}
            })
            return error_msg
    
    async def chat(self, user_message: str) -> str:
        """Main chat interface"""
        
        # Handle commands
        if user_message.lower() in ['history', 'h']:
            return self.show_history()
        elif user_message.lower() in ['quit', 'exit', 'q']:
            return "👋 Thanks for using Professional Circuit Chat!"
        
        # Analyze the user's request
        analysis = self.analyze_request(user_message)
        
        # Check if this is a follow-up to questions
        if self.pending_generation:
            # This is a follow-up response - generate the circuit with their previous request
            original_analysis = self.pending_generation
            self.pending_generation = None  # Clear pending state
            
            # Add their answer to the peripherals context
            original_analysis["user_answers"] = user_message
            
            print(f"🏗️  Got your requirements! Generating {original_analysis['mcu_type']} project...")
            return await self.generate_professional_project(user_message, original_analysis)
        
        # Ask questions if needed (unless they want defaults)
        if "default" not in user_message.lower():
            questions = self.ask_questions(analysis)
            if questions:
                # Store the analysis for when they answer
                self.pending_generation = analysis
                self.conversation_history.append({
                    "timestamp": datetime.now().strftime("%H:%M:%S"),
                    "user": user_message,
                    "assistant": questions,
                    "metadata": {"type": "questions"}
                })
                return questions
        
        # Generate professional project if they want a circuit
        if analysis["mcu_type"]:
            return await self.generate_professional_project(user_message, analysis)
        
        # For general questions, provide helpful guidance
        response = "💡 I specialize in generating **professional hierarchical circuit projects**.\n\n"
        response += "🎯 **I can create:**\n"
        response += "   • ESP32 development boards (with S3/C6 variants)\n"
        response += "   • STM32 development boards (F411 recommended)\n" 
        response += "   • Complete projects with USB-C, power regulation, ESD protection\n"
        response += "   • Hierarchical designs like example_project/circuit-synth/\n\n"
        response += "💬 **Try saying:**\n"
        response += "   • 'Make an ESP32-S3 board with IMU and NeoPixels'\n"
        response += "   • 'Create STM32F411 development board'\n"
        response += "   • 'ESP32 with USB-C and temperature sensor'\n"
        
        return response
    
    def show_history(self) -> str:
        """Show conversation history"""
        if not self.conversation_history:
            return "📝 No conversation history yet."
        
        history = "📝 **Conversation History:**\n\n"
        for i, exchange in enumerate(self.conversation_history[-5:], 1):
            history += f"**{i}. {exchange['timestamp']}**\n"
            history += f"👤 User: {exchange['user'][:100]}{'...' if len(exchange['user']) > 100 else ''}\n"
            
            assistant_msg = exchange['assistant'][:200]
            history += f"🤖 Assistant: {assistant_msg}{'...' if len(exchange['assistant']) > 200 else ''}\n"
            
            if exchange.get('metadata', {}).get('project_path'):
                history += f"   📁 Generated: {exchange['metadata']['project_path']}\n"
            
            history += "\n"
        
        return history


async def main():
    """Main chat loop"""
    chat = ProfessionalCircuitChat()
    
    # Initialize
    if not await chat.initialize():
        return
    
    # Show welcome
    print()
    print("=" * 80)
    print("🎛️  PROFESSIONAL CIRCUIT DESIGN CHAT")
    print("=" * 80)
    print("🏗️  Generates hierarchical projects like example_project/circuit-synth/")
    print("⚡ Includes proper passives, regulators, and ESD protection")
    print("🤔 Asks questions to ensure optimal design")
    print()
    print("💬 Examples:")
    print("   'Make an ESP32-S3 board with IMU and USB-C'")
    print("   'Create STM32F411 development board'")
    print("   'ESP32 with NeoPixels and temperature sensor'")
    print()
    print("Commands: 'history' (show chat), 'quit' (exit)")
    print("=" * 80)
    print("💬 Ready! What professional circuit do you want to design?")
    print()
    
    # Chat loop
    try:
        while True:
            user_input = input("🎛️  > ").strip()
            
            if not user_input:
                continue
                
            if user_input.lower() in ['quit', 'exit', 'q']:
                print("\\n👋 Thanks for using Professional Circuit Chat!")
                break
            
            print("\\n🤖 Thinking...")
            response = await chat.chat(user_input)
            
            print()
            print(response)
            print()
            
    except KeyboardInterrupt:
        print("\\n\\n👋 Chat interrupted by user")
    except Exception as e:
        print(f"\\n❌ Chat error: {e}")


if __name__ == "__main__":
    asyncio.run(main())