#!/usr/bin/env python3
"""
Circuit-Synth PCB Claude Chat Plugin for KiCad PCB Editor

Provides full Claude AI chat interface with PCB context awareness.
Uses the same proven architecture as the working schematic plugin.
"""

import pcbnew
import wx
import sys
import os
import subprocess
import logging
import tempfile
import threading
import queue
import time
import re
from pathlib import Path

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class KiCadPCBClaudeBridge:
    """Claude bridge for KiCad PCB design discussions and analysis."""
    
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
            test_message = "Hello! Please respond with just 'KICAD PCB CHAT READY' to confirm you're working for KiCad PCB integration."
            
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
                stdout, stderr = process.communicate(input=message, timeout=180)  # Extended timeout for analysis
                
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

def analyze_pcb_board(board):
    """Analyze KiCad PCB board and extract key information."""
    try:
        # Basic board info
        board_name = board.GetFileName() if board.GetFileName() else "Untitled"
        
        # Get components
        footprints = list(board.GetFootprints())
        components = []
        component_types = {}
        
        for fp in footprints[:20]:  # Limit to first 20 for performance
            ref = fp.GetReference()
            value = fp.GetValue()
            # Fix the GetUniString error - use str() instead
            footprint_name = str(fp.GetFPID().GetLibItemName())
            
            components.append({
                'ref': ref,
                'value': value,
                'footprint': footprint_name
            })
            
            # Count component types
            prefix = ref.rstrip('0123456789')
            component_types[prefix] = component_types.get(prefix, 0) + 1
        
        # Get tracks and routing info
        tracks = list(board.GetTracks())
        vias = sum(1 for t in tracks if t.Type() == pcbnew.PCB_VIA_T)
        track_segments = len(tracks) - vias
        
        # Get nets
        netinfo = board.GetNetInfo()
        net_count = netinfo.GetNetCount() if netinfo else 0
        
        # Get board dimensions
        try:
            bbox = board.GetBoardEdgesBoundingBox()
            width_mm = pcbnew.ToMM(bbox.GetWidth())
            height_mm = pcbnew.ToMM(bbox.GetHeight())
            board_size = f"{width_mm:.1f}mm x {height_mm:.1f}mm"
        except:
            board_size = "Unknown"
        
        return {
            'board_name': Path(board_name).stem,
            'component_count': len(footprints),
            'components': components,
            'component_types': component_types,
            'track_count': len(tracks),
            'track_segments': track_segments,
            'via_count': vias,
            'net_count': net_count,
            'board_size': board_size,
            'success': True
        }
        
    except Exception as e:
        logger.error(f"PCB Analysis error: {e}")
        return {
            'error': str(e),
            'success': False
        }

def create_pcb_context_message(analysis, user_message):
    """Create context message optimized for KiCad PCB design discussions."""
    if not analysis.get('success'):
        context_message = f"""I'm working in KiCad PCB Editor and have a question about PCB design.

IMPORTANT: Please provide text-only responses. Do not try to execute code, use tools, or generate files. Just give PCB design advice and explanations.

Question: {user_message}"""
        return context_message
    
    # Build context message
    context_message = f"""I'm working in KiCad PCB Editor on a PCB design project and need your help.

PCB PROJECT CONTEXT:
- Board Name: {analysis['board_name']}
- Components: {analysis['component_count']}
- Board Size: {analysis['board_size']}
- Routing: {analysis['track_segments']} tracks, {analysis['via_count']} vias
- Nets: {analysis['net_count']}

CURRENT PCB:"""
    
    # Show key components
    if analysis['components']:
        context_message += "\nComponents on PCB:"
        for comp in analysis['components'][:8]:  # Show first 8 components
            context_message += f"\n- {comp['ref']}: {comp['value']} ({comp['footprint']})"
        
        if len(analysis['components']) > 8:
            context_message += f"\n- ... and {len(analysis['components']) - 8} more components"
    else:
        context_message += "\n- No components placed yet"
    
    # Show component type summary
    if analysis['component_types']:
        context_message += "\n\nComponent Types:"
        for comp_type, count in sorted(analysis['component_types'].items())[:5]:
            context_message += f"\n- {comp_type}: {count} components"
    
    # Show routing status
    if analysis['track_count'] > 0:
        context_message += f"\n\nRouting Status:"
        context_message += f"\n- Track segments: {analysis['track_segments']}"
        context_message += f"\n- Vias: {analysis['via_count']}"
        context_message += f"\n- Total nets: {analysis['net_count']}"
    else:
        context_message += "\n- No routing completed yet"
    
    context_message += f"""

IMPORTANT INSTRUCTIONS FOR YOUR RESPONSE:
- Provide text-only responses about PCB design
- Do not try to execute code or use tools
- Give specific, actionable PCB design advice
- Focus on layout, routing, component placement, and manufacturing
- Consider signal integrity, power delivery, and thermal management
- If suggesting design rules, include typical values and rationale
- Focus on practical KiCad PCB Editor guidance

QUESTION: {user_message}"""
    
    return context_message

def show_pcb_claude_chat_gui(analysis_data):
    """Show the main KiCad PCB-Claude chat interface."""
    try:
        import tkinter as tk
        from tkinter import scrolledtext, messagebox
        
        # Initialize Claude bridge
        claude = KiCadPCBClaudeBridge()
        response_queue = queue.Queue()
        
        # Create main window
        root = tk.Tk()
        root.title("💬 KiCad PCB-Claude Chat")
        root.geometry("1000x800")
        root.configure(bg='#2b2b2b')
        
        # Status frame
        status_frame = tk.Frame(root, bg='#2b2b2b')
        status_frame.pack(fill=tk.X, padx=10, pady=5)
        
        status_label = tk.Label(status_frame, text="Starting connection test...", 
                               bg='#2b2b2b', fg='orange', font=('Arial', 10, 'bold'))
        status_label.pack(side=tk.LEFT)
        
        # Reconnect button
        def reconnect():
            status_label.config(text="🔍 Finding Claude CLI & Testing Connection...", fg='orange')
            send_btn.config(state='disabled')
            root.update()
            
            if claude.connect():
                status_label.config(text="✅ Claude Connected for PCB Design", fg='green')
                send_btn.config(state='normal')
            else:
                status_label.config(text="❌ Connection Failed - Check Claude Installation", fg='red') 
                send_btn.config(state='disabled')
                # Add error message to chat
                chat_display.config(state=tk.NORMAL)
                chat_display.insert(tk.END, "\n\n🚨 System: Claude connection failed. Install Claude Code: https://claude.ai/code")
                chat_display.config(state=tk.DISABLED)
                chat_display.see(tk.END)
        
        reconnect_btn = tk.Button(status_frame, text="🔄 Reconnect", command=reconnect,
                                 bg='#4a4a4a', fg='white')
        reconnect_btn.pack(side=tk.RIGHT, padx=5)
        
        # Chat display
        chat_display = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=('Consolas', 10),
                                                bg='#1e1e1e', fg='#e0e0e0', insertbackground='white')
        chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
        
        # Welcome message
        welcome_msg = f"""💬 KiCad PCB-Claude Chat Interface
{'='*60}

📋 PCB Project: {analysis_data.get('board_name', 'Unknown')}
🔧 Components: {analysis_data.get('component_count', 0)}
📏 Board Size: {analysis_data.get('board_size', 'Unknown')}
🔗 Routing: {analysis_data.get('track_segments', 0)} tracks, {analysis_data.get('via_count', 0)} vias

🎯 I can help with PCB design advice and guidance!

PCB DESIGN ASSISTANCE:
• Component placement optimization
• Routing strategies and best practices
• Signal integrity and power delivery
• Manufacturing considerations (DFM)
• Thermal management and cooling
• EMI/EMC design guidelines
• Design rule checking (DRC) guidance
• Layer stackup recommendations

Ask me anything about your PCB design!

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
        
        def check_responses():
            """Check for responses from Claude."""
            try:
                response = response_queue.get_nowait()
                
                # Add response to chat
                chat_display.config(state=tk.NORMAL)
                chat_display.insert(tk.END, f"\n\n🤖 Claude: {response}")
                chat_display.config(state=tk.DISABLED)
                chat_display.see(tk.END)
                
                # Reset UI
                send_btn.config(state='normal', text='Send')
                status_label.config(text="✅ Claude Connected for PCB Design", fg='green')
                message_entry.focus()
                
            except queue.Empty:
                # No response yet, check again
                root.after(100, check_responses)
        
        def send_message():
            message = message_entry.get().strip()
            if not message:
                return
            
            # Update UI
            send_btn.config(state='disabled', text='Thinking...')
            status_label.config(text="🤔 Claude analyzing your PCB question...", fg='blue')
            
            # Clear input and add user message
            message_entry.delete(0, tk.END)
            chat_display.config(state=tk.NORMAL)
            chat_display.insert(tk.END, f"\n\n🧑 You: {message}")
            chat_display.config(state=tk.DISABLED)
            chat_display.see(tk.END)
            
            # Send in background thread
            def send_worker():
                context_message = create_pcb_context_message(analysis_data, message)
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

class CircuitSynthPCBClaudeChat(pcbnew.ActionPlugin):
    """
    Circuit-Synth PCB Claude Chat Plugin for KiCad PCB Editor.
    
    Provides full Claude AI chat interface with PCB context awareness.
    """

    def defaults(self):
        """Set up plugin defaults."""
        self.name = "Circuit-Synth PCB Chat"
        self.category = "Circuit Design"
        self.description = "Full Claude AI chat interface for PCB design assistance"
        self.show_toolbar_button = True
        
    def Run(self):
        """Execute the plugin."""
        try:
            # Get the current board
            board = pcbnew.GetBoard()
            if board is None:
                wx.MessageBox(
                    "No PCB board found. Please open a PCB file first.",
                    "Circuit-Synth PCB Chat",
                    wx.OK | wx.ICON_WARNING
                )
                return

            print("💬 Circuit-Synth PCB Chat Starting...")
            
            # Analyze the board
            analysis = analyze_pcb_board(board)
            
            if analysis.get('success'):
                print(f"✅ Found {analysis['component_count']} components on board")
                
                # Show Claude chat interface
                if show_pcb_claude_chat_gui(analysis):
                    print("✅ Claude chat interface launched")
                else:
                    wx.MessageBox(
                        "Failed to launch Claude chat interface. Check console for details.",
                        "Plugin Error",
                        wx.OK | wx.ICON_ERROR
                    )
            else:
                error_msg = f"Board analysis failed: {analysis.get('error', 'Unknown error')}"
                print(f"❌ {error_msg}")
                wx.MessageBox(error_msg, "Analysis Error", wx.OK | wx.ICON_ERROR)

        except Exception as e:
            error_msg = f"Plugin error: {str(e)}"
            print(f"❌ {error_msg}")
            wx.MessageBox(error_msg, "Plugin Error", wx.OK | wx.ICON_ERROR)

# Register the plugin
CircuitSynthPCBClaudeChat().register()