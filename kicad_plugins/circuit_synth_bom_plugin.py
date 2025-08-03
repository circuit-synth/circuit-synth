#!/usr/bin/env python3
# -*- coding: utf-8 -*-
import sys
import io
import locale

# Force UTF-8 encoding for KiCad's Python environment
if sys.stdout.encoding != 'utf-8':
    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding='utf-8')
if sys.stderr.encoding != 'utf-8':
    sys.stderr = io.TextIOWrapper(sys.stderr.buffer, encoding='utf-8')

# Set locale for proper Unicode handling
try:
    locale.setlocale(locale.LC_ALL, 'en_US.UTF-8')
except locale.Error:
    try:
        locale.setlocale(locale.LC_ALL, 'C.UTF-8')
    except locale.Error:
        pass  # Fallback to default

"""
KiCad-Claude Chat - The Main Plugin for Circuit Design Discussions & Generation
This is the single file we maintain and update for KiCad-Claude integration.
"""

import os
import xml.etree.ElementTree as ET
from pathlib import Path
import argparse
import subprocess
import logging
import tempfile
import threading
import queue
import time
import re

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KiCadClaudeBridge:
    """Main Claude bridge for KiCad schematic design discussions and code generation."""
    
    def __init__(self):
        self.is_connected = False
        self.claude_path = None
        self.node_env = None
        
    def find_claude_path(self):
        """Find Claude CLI with proper Node.js environment."""
        # Strategy 1: Try direct claude command (works if in PATH)
        try:
            result = subprocess.run(['which', 'claude'], capture_output=True, text=True)
            if result.returncode == 0:
                claude_path = result.stdout.strip()
                logger.info(f"✅ Found Claude via PATH: {claude_path}")
                return claude_path, {}
        except:
            pass
        
        # Strategy 2: Try common NVM locations
        home = os.path.expanduser("~")
        nvm_locations = [
            f"{home}/.nvm/versions/node/v23.7.0/bin/claude",
            f"{home}/.nvm/versions/node/v22.0.0/bin/claude", 
            f"{home}/.nvm/versions/node/v21.0.0/bin/claude",
            f"{home}/.nvm/versions/node/v20.0.0/bin/claude"
        ]
        
        for claude_path in nvm_locations:
            if os.path.exists(claude_path):
                # Set up Node.js environment
                node_bin_dir = os.path.dirname(claude_path)
                env = os.environ.copy()
                env['PATH'] = f"{node_bin_dir}:{env.get('PATH', '')}"
                logger.info(f"✅ Found Claude at: {claude_path}")
                return claude_path, env
        
        # Strategy 3: Try to find node and look for claude
        try:
            result = subprocess.run(['which', 'node'], capture_output=True, text=True)
            if result.returncode == 0:
                node_path = result.stdout.strip()
                node_dir = os.path.dirname(node_path)
                claude_path = os.path.join(node_dir, 'claude')
                if os.path.exists(claude_path):
                    logger.info(f"✅ Found Claude via node location: {claude_path}")
                    return claude_path, {}
        except:
            pass
        
        logger.error("❌ Could not find Claude CLI or Node.js")
        return None, None
        
    def connect(self):
        """Test Claude connection with proper environment setup."""
        # Find Claude path and environment
        self.claude_path, self.node_env = self.find_claude_path()
        if not self.claude_path:
            logger.error("❌ Claude CLI not found - install Claude Code first")
            return False
            
        try:
            # Test with --version to verify Claude CLI works
            result = subprocess.run(
                [self.claude_path, "--version"], 
                capture_output=True, 
                text=True, 
                timeout=10,
                stdin=subprocess.DEVNULL,
                env=self.node_env if self.node_env else None
            )
            
            if result.returncode == 0:
                logger.info(f"✅ Claude version check passed: {result.stdout.strip()}")
                
                # Now test actual message sending with a simple test
                test_result = self.send_test_message()
                if test_result:
                    self.is_connected = True
                    logger.info("✅ Claude message test passed - fully connected")
                    return True
                else:
                    logger.error("❌ Claude version OK but message test failed")
                    return False
            else:
                logger.error(f"❌ Claude version check failed: {result.returncode}")
                logger.error(f"Stdout: {result.stdout}")
                logger.error(f"Stderr: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Connection test error: {e}")
            return False
    
    def send_test_message(self):
        """Send a test message to verify Claude is really working."""
        try:
            test_message = "Hello! Please respond with just 'KICAD CHAT READY' to confirm you're working for KiCad integration."
            
            process = subprocess.Popen(
                [self.claude_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=self.node_env if self.node_env else None
            )
            
            stdout, stderr = process.communicate(input=test_message, timeout=30)
            
            if process.returncode == 0 and stdout.strip():
                logger.info(f"✅ Test message succeeded: {stdout[:50]}...")
                return True
            else:
                logger.error(f"❌ Test message failed: code={process.returncode}")
                if stderr:
                    logger.error(f"Stderr: {stderr}")
                return False
                
        except Exception as e:
            logger.error(f"❌ Test message error: {e}")
            return False
    
    def send_message(self, message):
        """Send message with proper error handling and extended timeout."""
        if not self.is_connected:
            return "❌ Not connected to Claude (connection test failed)"
        
        try:
            logger.info(f"📤 Sending message: {message[:50]}...")
            
            process = subprocess.Popen(
                [self.claude_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=self.node_env if self.node_env else None
            )
            
            try:
                stdout, stderr = process.communicate(input=message, timeout=180)  # Extended timeout for code generation
                
                if process.returncode == 0:
                    response = stdout.strip()
                    if response:
                        logger.info(f"📥 Got response: {len(response)} chars")
                        return response
                    else:
                        logger.error("❌ Empty response from Claude")
                        return "❌ Claude returned empty response"
                else:
                    logger.error(f"❌ Claude error: code={process.returncode}")
                    if stderr:
                        logger.error(f"Stderr: {stderr}")
                    return f"❌ Claude error (code {process.returncode}): {stderr}"
                    
            except subprocess.TimeoutExpired:
                logger.error("⏰ Timeout - killing process")
                process.kill()
                process.communicate()
                return "❌ Request timed out (180 seconds). Try a simpler question or break it into smaller parts."
                
        except Exception as e:
            logger.error(f"❌ Send error: {e}")
            return f"❌ Error: {e}"

def execute_circuit_synth_code(code, project_name="generated_circuit"):
    """Execute circuit-synth code safely in a subprocess."""
    try:
        # Create a temporary directory for the project
        with tempfile.TemporaryDirectory() as temp_dir:
            # Write the circuit-synth code to a temporary file
            code_file = Path(temp_dir) / "circuit_code.py"
            code_file.write_text(code)
            
            # Change to circuit-synth directory and execute
            circuit_synth_dir = Path("/Users/shanemattner/Desktop/Circuit_Synth2/submodules/circuit-synth")
            
            if not circuit_synth_dir.exists():
                return {"success": False, "error": "Circuit-synth directory not found"}
            
            # Execute the code using Python - try multiple approaches
            import os
            
            # Expand PATH to include common locations for uv
            env = os.environ.copy()
            additional_paths = [
                "/usr/local/bin",
                "/opt/homebrew/bin", 
                os.path.expanduser("~/.local/bin"),
                os.path.expanduser("~/.cargo/bin")
            ]
            current_path = env.get("PATH", "")
            env["PATH"] = ":".join(additional_paths + [current_path])
            env["PYTHONPATH"] = str(circuit_synth_dir / "src")
            
            try:
                # Try uv run first (preferred for development)
                result = subprocess.run(
                    ["uv", "run", "python", str(code_file)],
                    capture_output=True,
                    text=True,
                    cwd=circuit_synth_dir,
                    timeout=120,
                    env=env
                )
            except FileNotFoundError:
                # Fallback to system python3 if uv not available
                result = subprocess.run(
                    ["python3", str(code_file)],
                    capture_output=True,
                    text=True,
                    cwd=circuit_synth_dir,
                    timeout=120,
                    env=env
                )
            
            if result.returncode == 0:
                # Look for generated files
                generated_files = []
                for pattern in ["*.kicad_pro", "*.kicad_sch", "*.net", "*.json"]:
                    generated_files.extend(list(circuit_synth_dir.glob(pattern)))
                
                return {
                    "success": True,
                    "stdout": result.stdout,
                    "stderr": result.stderr,
                    "generated_files": [str(f) for f in generated_files[-10:]]  # Last 10 files
                }
            else:
                return {
                    "success": False,
                    "error": f"Execution failed (code {result.returncode})",
                    "stdout": result.stdout,
                    "stderr": result.stderr
                }
                
    except subprocess.TimeoutExpired:
        return {"success": False, "error": "Code execution timed out (120 seconds)"}
    except Exception as e:
        return {"success": False, "error": f"Execution error: {e}"}

def analyze_netlist_xml(netlist_file):
    """Analyze KiCad netlist XML."""
    try:
        tree = ET.parse(netlist_file)
        root = tree.getroot()
        
        # Extract design name
        design_element = root.find('.//design')
        design_name = "Unknown"
        if design_element is not None:
            source_element = design_element.find('source')
            if source_element is not None:
                design_name = Path(source_element.text).stem
        
        # Extract components (limited for shorter messages)
        components = []
        for comp in root.findall('.//components/comp')[:15]:
            ref = comp.get('ref', 'Unknown')
            value = comp.find('value')
            value_text = value.text if value is not None else 'N/A'
            
            components.append({
                'ref': ref,
                'value': value_text
            })
        
        # Extract nets (limited)
        nets = []
        for net in root.findall('.//nets/net')[:10]:
            net_name = net.get('name', 'Unknown')
            node_count = len(net.findall('node'))
            nets.append({
                'name': net_name,
                'connections': node_count
            })
        
        return {
            'design_name': design_name,
            'component_count': len(root.findall('.//components/comp')),
            'net_count': len(root.findall('.//nets/net')),
            'components': components,
            'nets': nets,
            'success': True
        }
        
    except Exception as e:
        logger.error(f"Analysis error: {e}")
        return {
            'error': str(e),
            'success': False
        }

def create_circuit_generation_context(analysis, user_message):
    """Create context message for circuit generation with circuit-synth examples."""
    
    circuit_synth_examples = """
FOOLPROOF CIRCUIT-SYNTH TEMPLATE - TESTED AND WORKING:

```python
from circuit_synth import *

@circuit
def main():
    # Create nets
    vcc_3v3 = Net('VCC_3V3')
    vcc_5v = Net('VCC_5V') 
    gnd = Net('GND')
    
    # ESP32 module (TESTED: Pin 1=GND, Pin 3=3V3)
    esp32 = Component("RF_Module:ESP32-S3-MINI-1", ref="U1", footprint="RF_Module:ESP32-S2-MINI-1")
    esp32[1] += gnd         # Pin 1 = GND
    esp32[3] += vcc_3v3     # Pin 3 = 3V3  
    
    # USB-A connector (TESTED: Pin 1=VBUS, Pin 4=GND)
    usb_a = Component("Connector:USB_A", ref="J1", footprint="Connector_USB:USB_A_CNCTech_1001-011-01101_Horizontal")
    usb_a[1] += vcc_5v      # Pin 1 = VBUS
    usb_a[4] += gnd         # Pin 4 = GND
    
    # Voltage regulator (TESTED: Pin 1=GND, Pin 2=OUT, Pin 3=IN)
    regulator = Component("Regulator_Linear:NCP1117-3.3_SOT223", ref="U3", footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2")
    regulator[1] += gnd         # Pin 1 = GND
    regulator[2] += vcc_3v3     # Pin 2 = 3.3V output
    regulator[3] += vcc_5v      # Pin 3 = 5V input
    
    # Capacitors (TESTED: Pin 1 and Pin 2)
    cap_in = Component("Device:C", ref="C1", value="10uF", footprint="Capacitor_SMD:C_0805_2012Metric")
    cap_in[1] += vcc_5v
    cap_in[2] += gnd
    
    cap_out = Component("Device:C", ref="C2", value="10uF", footprint="Capacitor_SMD:C_0805_2012Metric")
    cap_out[1] += vcc_3v3
    cap_out[2] += gnd

if __name__ == '__main__':
    circuit = main()
    circuit.generate_kicad_project("project_name", force_regenerate=True)
```

ABSOLUTE REQUIREMENTS - THESE PIN NUMBERS ARE TESTED AND WORK:
1. ESP32 ESP32-S3-MINI-1: Pin 1=GND, Pin 3=3V3 (verified working)
2. USB_A: Pin 1=VBUS, Pin 4=GND (verified working)
3. NCP1117 regulator: Pin 1=GND, Pin 2=OUT, Pin 3=IN (verified working)
4. Capacitor Device:C: Pin 1 and Pin 2 (passive, verified working)
5. ONLY use @circuit decorator on main() function
6. ALWAYS end with circuit.generate_kicad_project("project_name", force_regenerate=True)
7. NO additional imports, NO debugging, NO complex features - keep it simple!
"""
    
    context_message = f"""CIRCUIT GENERATION MODE - Generate circuit-synth Python code for KiCad.

USER REQUEST: {user_message}

{circuit_synth_examples}

MANDATORY INSTRUCTIONS:
1. Use EXACTLY the template above - don't deviate
2. ONLY use: from circuit_synth import *
3. ONLY use integer pin numbers [1], [2], [3] - never use string pin names
4. Generate a COMPLETE working script that ends with:
   circuit.generate_kicad_project("project_name", force_regenerate=True)
5. Use ONLY these proven KiCad symbols:
   - ESP32: "RF_Module:ESP32-S3-MINI-1"
   - IMU: "Sensor_Motion:MPU-6050" 
   - USB-C: "Connector:USB_C_Receptacle_USB2.0"
   - Resistor: "Device:R"
   - Capacitor: "Device:C"
   - Regulator: "Regulator_Linear:NCP1117-3.3_SOT223"
6. Keep it SIMPLE - no complex features, decorators except @circuit, or extra imports

Generate the COMPLETE Python script now."""
    
    return context_message

def create_context_message(analysis, user_message):
    """Create context message optimized for KiCad circuit design discussions."""
    # Check if this is a request for circuit generation
    generation_keywords = ['generate', 'create', 'design', 'build', 'make', 'code', 'script']
    if any(keyword in user_message.lower() for keyword in generation_keywords):
        return create_circuit_generation_context(analysis, user_message)
    
    # Regular chat context for advice/discussion
    if not analysis.get('success'):
        context_message = f"""I'm working in KiCad and have a question about circuit design.

IMPORTANT: Please provide text-only responses. Do not try to execute code, use tools, or generate files. Just give circuit design advice and explanations.

Question: {user_message}"""
        return context_message
    
    # Build context message
    context_message = f"""I'm working in KiCad on a circuit design project and need your help.

PROJECT CONTEXT:
- Design Name: {analysis['design_name']}
- Components: {analysis['component_count']}
- Nets: {analysis['net_count']}

CURRENT CIRCUIT:"""
    
    # Show key components
    if analysis['components']:
        context_message += "\nComponents:"
        for comp in analysis['components'][:8]:  # Show more components
            context_message += f"\n- {comp['ref']}: {comp['value']}"
        
        if len(analysis['components']) > 8:
            context_message += f"\n- ... and {len(analysis['components']) - 8} more components"
    else:
        context_message += "\n- No components in circuit yet"
    
    # Show key nets
    if analysis['nets']:
        context_message += "\n\nKey Networks:"
        for net in analysis['nets'][:5]:
            context_message += f"\n- {net['name']} ({net['connections']} connections)"
    else:
        context_message += "\n- No nets defined yet"
    
    context_message += f"""

IMPORTANT INSTRUCTIONS FOR YOUR RESPONSE:
- Provide text-only responses about circuit design
- Do not try to execute code or use tools
- Give specific, actionable circuit design advice
- If suggesting components, include part numbers or specifications
- If explaining connections, describe them clearly in text
- Focus on practical KiCad/PCB design guidance

QUESTION: {user_message}"""
    
    return context_message

def show_kicad_claude_chat_gui(analysis_data):
    """Show the main KiCad-Claude chat interface with circuit generation capabilities."""
    try:
        import tkinter as tk
        from tkinter import scrolledtext, messagebox
        
        # Initialize Claude bridge
        claude = KiCadClaudeBridge()
        response_queue = queue.Queue()
        
        # Create main window
        root = tk.Tk()
        root.title("💬 KiCad-Claude Chat & Circuit Generator")
        root.geometry("1000x800")
        root.configure(bg='#2b2b2b')
        
        # Status frame
        status_frame = tk.Frame(root, bg='#2b2b2b')
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        status_label = tk.Label(status_frame, text="Starting connection test...", 
                               bg='#2b2b2b', fg='orange', font=('Arial', 10, 'bold'))
        status_label.pack(side=tk.LEFT)
        
        # Mode toggle frame
        mode_frame = tk.Frame(status_frame, bg='#2b2b2b')
        mode_frame.pack(side=tk.RIGHT)
        
        generation_mode = tk.BooleanVar(value=False)
        mode_toggle = tk.Checkbutton(mode_frame, text="🚀 Circuit Generation Mode", 
                                   variable=generation_mode, bg='#2b2b2b', fg='white',
                                   selectcolor='#4a4a4a', font=('Arial', 9))
        mode_toggle.pack(side=tk.LEFT, padx=5)
        
        # Reconnect button
        def reconnect():
            status_label.config(text="🔍 Finding Claude CLI & Testing Connection...", fg='orange')
            send_btn.config(state='disabled')
            root.update()
            
            if claude.connect():
                status_label.config(text="✅ Claude Connected for Circuit Design", fg='green')
                send_btn.config(state='normal')
            else:
                status_label.config(text="❌ Connection Failed - Check Claude Installation", fg='red') 
                send_btn.config(state='disabled')
                # Add error message to chat
                chat_display.config(state=tk.NORMAL)
                chat_display.insert(tk.END, "\n\n🚨 System: Claude connection failed. Install Claude Code: https://claude.ai/code")
                chat_display.config(state=tk.DISABLED)
                chat_display.see(tk.END)
        
        reconnect_btn = tk.Button(mode_frame, text="🔄 Reconnect", command=reconnect,
                                 bg='#4a4a4a', fg='white')
        reconnect_btn.pack(side=tk.RIGHT, padx=5)
        
        # Chat display
        chat_display = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=('Consolas', 10),
                                                bg='#1e1e1e', fg='#e0e0e0', insertbackground='white')
        chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Welcome message
        welcome_msg = f"""💬 KiCad-Claude Chat & Circuit Generator
{'='*60}

📋 Project: {analysis_data.get('design_name', 'Unknown')}
🔧 Components: {analysis_data.get('component_count', 0)}
🔗 Nets: {analysis_data.get('net_count', 0)}

🎯 I can help with circuit design & generation!

CHAT MODE - Circuit design advice and guidance:
• Circuit topology and component selection
• PCB layout and routing guidance  
• Component specifications and sourcing
• KiCad-specific workflow tips
• Debugging circuit issues

🚀 GENERATION MODE - Create actual circuits:
• Generate complete circuit-synth Python code
• Execute code to create KiCad projects
• ESP32, IMU, power supplies, USB interfaces
• Custom circuits based on your specifications

Ask me anything about your circuit design!

"""
        
        chat_display.insert(tk.END, welcome_msg)
        chat_display.config(state=tk.DISABLED)
        
        # Input frame
        input_frame = tk.Frame(root, bg='#2b2b2b')
        input_frame.pack(fill=tk.X, padx=10, pady=5)
        
        message_entry = tk.Entry(input_frame, font=('Arial', 12), bg='#3a3a3a', fg='white')
        message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
        
        def handle_response(response):
            """Handle response from background thread."""
            response_queue.put(response)
        
        def extract_and_execute_code(response):
            """Extract circuit-synth code from response and execute it."""
            # Look for code blocks in the response
            code_pattern = r'```python\n(.*?)\n```'
            matches = re.findall(code_pattern, response, re.DOTALL)
            
            if matches:
                code = matches[0]  # Take the first code block
                
                # Add to chat that we're executing
                chat_display.config(state=tk.NORMAL)
                chat_display.insert(tk.END, f"\n\n🤖 Executing generated circuit-synth code...")
                chat_display.config(state=tk.DISABLED)
                chat_display.see(tk.END)
                root.update()
                
                # Execute the code
                result = execute_circuit_synth_code(code)
                
                if result["success"]:
                    success_msg = f"\n\n✅ Circuit generation successful!"
                    if result.get("generated_files"):
                        success_msg += f"\n\nGenerated files:"
                        for file in result["generated_files"]:
                            success_msg += f"\n• {file}"
                    
                    chat_display.config(state=tk.NORMAL)
                    chat_display.insert(tk.END, success_msg)
                    chat_display.config(state=tk.DISABLED)
                    chat_display.see(tk.END)
                    
                    messagebox.showinfo("Circuit Generated!", 
                                      f"Circuit successfully generated!\n\nFiles created: {len(result.get('generated_files', []))}")
                else:
                    error_msg = f"\n\n❌ Circuit generation failed: {result['error']}"
                    if result.get("stderr"):
                        error_msg += f"\n\nError details:\n{result['stderr'][:500]}..."
                    
                    chat_display.config(state=tk.NORMAL)
                    chat_display.insert(tk.END, error_msg)
                    chat_display.config(state=tk.DISABLED)
                    chat_display.see(tk.END)
        
        def check_responses():
            """Check for responses from Claude."""
            try:
                response = response_queue.get_nowait()
                
                # Add response to chat
                chat_display.config(state=tk.NORMAL)
                chat_display.insert(tk.END, f"\n\n🤖 Claude: {response}")
                chat_display.config(state=tk.DISABLED)
                chat_display.see(tk.END)
                
                # If in generation mode, try to extract and execute code
                if generation_mode.get():
                    extract_and_execute_code(response)
                
                # Reset UI
                send_btn.config(state='normal', text='Send')
                status_label.config(text="✅ Claude Connected for Circuit Design", fg='green')
                message_entry.focus()
                
            except queue.Empty:
                # No response yet, check again
                root.after(100, check_responses)
        
        def send_message():
            message = message_entry.get().strip()
            if not message:
                return
            
            # Update UI
            mode_text = " (Generation Mode)" if generation_mode.get() else ""
            send_btn.config(state='disabled', text='Thinking...')
            status_label.config(text=f"🤔 Claude analyzing your question{mode_text}...", fg='blue')
            
            # Clear input and add user message
            message_entry.delete(0, tk.END)
            chat_display.config(state=tk.NORMAL)
            chat_display.insert(tk.END, f"\n\n🧑 You: {message}")
            chat_display.config(state=tk.DISABLED)
            chat_display.see(tk.END)
            
            # Send in background thread
            def send_worker():
                context_message = create_context_message(analysis_data, message)
                response = claude.send_message(context_message)
                handle_response(response)
            
            threading.Thread(target=send_worker, daemon=True).start()
            check_responses()
        
        send_btn = tk.Button(input_frame, text="Send", command=send_message, 
                            font=('Arial', 12), bg='#0066cc', fg='white',
                            state='disabled')
        send_btn.pack(side=tk.RIGHT)
        
        message_entry.bind('<Return>', lambda e: send_message())
        
        # Initial connection test
        root.after(1000, reconnect)  # Give GUI time to load first
        message_entry.focus()
        
        root.mainloop()
        return True
        
    except Exception as e:
        logger.error(f"GUI Error: {e}")
        return False

def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(description='KiCad-Claude Chat - Main Plugin')
    parser.add_argument('netlist_file', help='Netlist XML file')
    parser.add_argument('output_file', help='Output file')
    
    args = parser.parse_args()
    
    print("💬 KiCad-Claude Chat & Circuit Generator Starting...")
    
    analysis = analyze_netlist_xml(args.netlist_file)
    
    if analysis.get('success'):
        print(f"✅ Found {analysis['component_count']} components")
        
        if show_kicad_claude_chat_gui(analysis):
            print("✅ GUI displayed")
        
        Path(args.output_file).write_text(f"KiCad-Claude Chat - {analysis['design_name']}")
        
    else:
        print(f"❌ Analysis failed: {analysis.get('error')}")
        sys.exit(1)

if __name__ == "__main__":
    main()