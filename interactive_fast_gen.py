#!/usr/bin/env python3
"""
Interactive Fast Circuit Generation Terminal

Terminal-based chat interface for generating circuits with full conversation visibility.
"""

import asyncio
import os
import sys
import readline  # For better input handling
from datetime import datetime
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from circuit_synth.fast_generation import FastCircuitGenerator, PatternType


class InteractiveFastGen:
    """Interactive terminal interface for fast circuit generation"""
    
    def __init__(self):
        self.generator = None
        self.conversation_history = []
        self.session_start = datetime.now()
        
    def log_message(self, role: str, message: str):
        """Log a message to conversation history"""
        timestamp = datetime.now().strftime("%H:%M:%S")
        self.conversation_history.append({
            "timestamp": timestamp,
            "role": role,
            "message": message
        })
        
    def print_header(self):
        """Print the terminal header"""
        print("=" * 80)
        print("🚀 FAST CIRCUIT GENERATION - Interactive Terminal")
        print("=" * 80)
        print("Available patterns:")
        patterns = [
            "esp32_basic      - ESP32-S3 development board",
            "esp32_sensor     - ESP32 + IMU sensor",
            "stm32_basic      - STM32F4 microcontroller", 
            "stm32_motor      - STM32 + motor control",
            "motor_stepper    - DRV8825/A4988 stepper driver",
            "sensor_imu       - MPU-6050 IMU module",
            "sensor_temp      - DS18B20 temperature sensor",
            "led_neopixel     - NeoPixel with level shifter",
            "usb_power        - USB-C power input",
            "encoder_quad     - Quadrature encoder"
        ]
        for pattern in patterns:
            print(f"  {pattern}")
        print()
        print("Commands:")
        print("  generate <pattern>     - Generate a circuit")
        print("  show <pattern>         - Show pattern details")
        print("  history               - Show conversation history")
        print("  stats                 - Show generation statistics")
        print("  help                  - Show this help")
        print("  quit                  - Exit")
        print("=" * 80)
        
    def print_conversation_history(self):
        """Print the full conversation history"""
        print("\n" + "=" * 60)
        print("📜 CONVERSATION HISTORY")
        print("=" * 60)
        
        for entry in self.conversation_history:
            role_icon = "🤖" if entry["role"] == "assistant" else "👤"
            print(f"[{entry['timestamp']}] {role_icon} {entry['role'].upper()}:")
            print(f"  {entry['message']}")
            print()
            
    async def initialize_generator(self):
        """Initialize the fast circuit generator"""
        print("🔧 Initializing Fast Circuit Generator...")
        
        # Check for API key
        api_key = os.getenv("OPENROUTER_API_KEY")
        if not api_key:
            print("❌ OPENROUTER_API_KEY not set!")
            print("   Set it with: export OPENROUTER_API_KEY=your_key_here")
            return False
            
        print(f"✅ API Key found: {api_key[:10]}...")
        
        try:
            self.generator = FastCircuitGenerator(openrouter_key=api_key)
            print("✅ Generator initialized successfully")
            self.log_message("system", "Fast circuit generator initialized")
            return True
        except Exception as e:
            print(f"❌ Failed to initialize generator: {e}")
            return False
    
    async def generate_circuit(self, pattern_name: str, requirements: dict = None):
        """Generate a circuit pattern"""
        if not self.generator:
            print("❌ Generator not initialized")
            return
            
        # Parse pattern type
        try:
            pattern_type = PatternType(pattern_name)
        except ValueError:
            print(f"❌ Unknown pattern: {pattern_name}")
            print("   Use 'help' to see available patterns")
            return
            
        print(f"🔄 Generating {pattern_name}...")
        self.log_message("user", f"Generate {pattern_name}")
        
        start_time = asyncio.get_event_loop().time()
        
        try:
            # Generate the circuit
            result = await self.generator.generate_circuit(
                pattern_type, 
                requirements=requirements or {}
            )
            
            end_time = asyncio.get_event_loop().time()
            actual_time = (end_time - start_time) * 1000
            
            if result["success"]:
                print(f"✅ SUCCESS! Generated in {actual_time:.0f}ms")
                print(f"🎯 Model: {result['model_used']}")
                print(f"📊 Tokens: {result['tokens_used']}")
                print(f"⚡ API Latency: {result['latency_ms']:.0f}ms")
                
                # Clean up the generated code (remove markdown fences)
                code = result['circuit_code']
                if code.startswith('```python'):
                    code = '\n'.join(code.split('\n')[1:])
                if code.endswith('```'):
                    code = '\n'.join(code.split('\n')[:-1])
                code = code.strip()
                
                # Save the file
                filename = f"{pattern_name}_generated.py"
                with open(filename, 'w') as f:
                    f.write(code)
                
                print(f"💾 Circuit saved to: {filename}")
                
                # Show validation results
                validation = result.get("validation_results", {})
                print("🔍 Validation:")
                print(f"  Syntax: {'✅' if validation.get('syntax_valid', False) else '❌'}")
                print(f"  Components: {'✅' if validation.get('components_verified', False) else '❌'}")
                print(f"  Connections: {'✅' if validation.get('connections_valid', False) else '❌'}")
                
                # Show code preview
                print(f"\n📋 Generated Code Preview ({filename}):")
                print("-" * 60)
                lines = code.split('\n')[:15]  # First 15 lines
                for i, line in enumerate(lines, 1):
                    print(f"{i:3}: {line}")
                if len(code.split('\n')) > 15:
                    print("  ... (truncated)")
                print("-" * 60)
                
                self.log_message("assistant", f"Generated {pattern_name} successfully in {actual_time:.0f}ms")
                
            else:
                error_msg = result.get('error', 'Unknown error')
                print(f"❌ Generation failed: {error_msg}")
                self.log_message("assistant", f"Generation failed: {error_msg}")
                
        except Exception as e:
            print(f"❌ Error during generation: {e}")
            self.log_message("system", f"Error: {e}")
    
    def show_pattern_details(self, pattern_name: str):
        """Show details about a specific pattern"""
        try:
            pattern_type = PatternType(pattern_name)
            if self.generator:
                pattern = self.generator.patterns.get_pattern(pattern_type)
                
                print(f"\n📋 PATTERN DETAILS: {pattern.name}")
                print("=" * 60)
                print(f"Description: {pattern.description}")
                print(f"Complexity: {pattern.estimated_complexity}/5")
                print(f"Power Rails: {', '.join(pattern.power_rails)}")
                print(f"Components: {len(pattern.components)}")
                print()
                print("Components:")
                for comp in pattern.components:
                    print(f"  - {comp.symbol} ({comp.ref_prefix}) - {comp.description}")
                print()
                print("Design Notes:")
                for note in pattern.design_notes:
                    print(f"  - {note}")
                print()
                
                self.log_message("user", f"Viewed details for {pattern_name}")
            else:
                print("❌ Generator not initialized")
                
        except ValueError:
            print(f"❌ Unknown pattern: {pattern_name}")
    
    def show_stats(self):
        """Show generation statistics"""
        if not self.generator:
            print("❌ Generator not initialized")
            return
            
        stats = self.generator.get_stats()
        
        print("\n📊 GENERATION STATISTICS")
        print("=" * 40)
        print(f"Total Generated: {stats['total_generated']}")
        print(f"Success Rate: {stats['success_rate']:.1%}")
        print(f"Average Latency: {stats['avg_latency_ms']:.0f}ms")
        print()
        
        if stats.get('pattern_usage'):
            print("Pattern Usage:")
            for pattern, count in stats['pattern_usage'].items():
                print(f"  {pattern}: {count}")
        print()
        
        # Session info
        session_duration = datetime.now() - self.session_start
        print(f"Session Duration: {session_duration}")
        print(f"Messages in History: {len(self.conversation_history)}")
        print()
        
        self.log_message("user", "Viewed statistics")
    
    async def run(self):
        """Main interactive loop"""
        self.print_header()
        
        # Initialize generator
        if not await self.initialize_generator():
            print("Failed to initialize. Exiting.")
            return
        
        print("\n💬 Ready! Type a command or 'help' for assistance.")
        print("Example: generate esp32_basic")
        
        while True:
            try:
                # Get user input
                user_input = input("\n> ").strip()
                
                if not user_input:
                    continue
                    
                # Parse command
                parts = user_input.split()
                command = parts[0].lower()
                args = parts[1:] if len(parts) > 1 else []
                
                # Handle commands
                if command == "quit" or command == "exit":
                    print("👋 Goodbye!")
                    self.log_message("user", "Exited session")
                    break
                    
                elif command == "help":
                    self.print_header()
                    self.log_message("user", "Requested help")
                    
                elif command == "history":
                    self.print_conversation_history()
                    
                elif command == "stats":
                    self.show_stats()
                    
                elif command == "generate":
                    if not args:
                        print("❌ Usage: generate <pattern>")
                        print("   Example: generate esp32_basic")
                    else:
                        pattern = args[0]
                        # Parse requirements if provided (simple JSON-like)
                        requirements = {}
                        await self.generate_circuit(pattern, requirements)
                        
                elif command == "show":
                    if not args:
                        print("❌ Usage: show <pattern>")
                        print("   Example: show esp32_basic")
                    else:
                        self.show_pattern_details(args[0])
                        
                else:
                    print(f"❌ Unknown command: {command}")
                    print("   Type 'help' for available commands")
                    
            except KeyboardInterrupt:
                print("\n👋 Goodbye!")
                break
            except EOFError:
                print("\n👋 Goodbye!")
                break
            except Exception as e:
                print(f"❌ Error: {e}")
                self.log_message("system", f"Error: {e}")


async def main():
    """Main entry point"""
    terminal = InteractiveFastGen()
    await terminal.run()


if __name__ == "__main__":
    asyncio.run(main())