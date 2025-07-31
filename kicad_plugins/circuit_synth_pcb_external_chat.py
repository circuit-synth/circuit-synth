#!/usr/bin/env python3
"""
Circuit-Synth PCB External Chat Plugin for KiCad PCB Editor

Uses external process approach like the BOM plugin to avoid tkinter issues.
Launches the same Claude chat interface as the working schematic plugin.
"""

import pcbnew
import wx
import sys
import os
import subprocess
import tempfile
import json
from pathlib import Path

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
        return {
            'error': str(e),
            'success': False
        }

def launch_external_pcb_chat(analysis_data):
    """Launch external PCB chat interface using the BOM plugin approach."""
    try:
        print("🚀 Launching external PCB chat interface...")
        
        # Create temporary file with PCB analysis data
        with tempfile.NamedTemporaryFile(mode='w', suffix='.json', delete=False) as f:
            json.dump(analysis_data, f, indent=2)
            temp_file = f.name
        
        # Find the BOM plugin to use as launcher
        bom_plugin_path = Path.home() / "Documents" / "KiCad" / "9.0" / "scripting" / "plugins" / "circuit_synth_bom_plugin.py"
        
        if not bom_plugin_path.exists():
            print(f"❌ BOM plugin not found at: {bom_plugin_path}")
            return False
        
        print(f"✅ Using BOM plugin launcher: {bom_plugin_path}")
        
        # Launch using Python with the BOM plugin but in PCB mode
        cmd = [
            sys.executable,  # Use same Python as KiCad
            str(bom_plugin_path),
            temp_file,  # PCB analysis data file
            "/tmp/pcb_output.txt",  # Dummy output file
            "--pcb-mode"  # Special flag to indicate PCB mode
        ]
        
        print(f"🔧 Launching command: {' '.join(cmd)}")
        
        # Launch in background
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL
        )
        
        print(f"✅ External chat launched with PID: {process.pid}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to launch external chat: {e}")
        return False

def launch_standalone_pcb_chat(analysis_data):
    """Launch standalone PCB chat using system Python."""
    try:
        print("🔄 Trying standalone PCB chat launcher...")
        
        # Create the standalone chat script
        chat_script = f'''#!/usr/bin/env python3
import sys
import json
import tkinter as tk
from tkinter import scrolledtext, messagebox
import subprocess
import threading
import queue
import os
import logging

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Load PCB analysis data
analysis_data = {json.dumps(analysis_data, indent=2)}

class KiCadPCBClaudeBridge:
    """Claude bridge for PCB chat."""
    
    def __init__(self):
        self.is_connected = False
        self.claude_path = None
        self.node_env = None
        
    def find_claude_path(self):
        """Find Claude CLI."""
        try:
            result = subprocess.run(['which', 'claude'], capture_output=True, text=True)
            if result.returncode == 0:
                return result.stdout.strip(), {{}}
        except:
            pass
        
        # Try NVM locations
        home = os.path.expanduser("~")
        nvm_locations = [
            f"{{home}}/.nvm/versions/node/v23.7.0/bin/claude",
            f"{{home}}/.nvm/versions/node/v22.0.0/bin/claude",
        ]
        
        for claude_path in nvm_locations:
            if os.path.exists(claude_path):
                node_bin_dir = os.path.dirname(claude_path)
                env = os.environ.copy()
                env['PATH'] = f"{{node_bin_dir}}:{{env.get('PATH', '')}}"
                return claude_path, env
        
        return None, None
        
    def connect(self):
        """Test Claude connection."""
        self.claude_path, self.node_env = self.find_claude_path()
        if not self.claude_path:
            return False
            
        try:
            result = subprocess.run(
                [self.claude_path, "--version"], 
                capture_output=True, text=True, timeout=10,
                env=self.node_env if self.node_env else None
            )
            
            if result.returncode == 0:
                self.is_connected = True
                return True
            return False
        except:
            return False
    
    def send_message(self, message):
        """Send message to Claude."""
        if not self.is_connected:
            return "❌ Not connected to Claude"
        
        try:
            process = subprocess.Popen(
                [self.claude_path],
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                env=self.node_env if self.node_env else None
            )
            
            stdout, stderr = process.communicate(input=message, timeout=180)
            
            if process.returncode == 0:
                return stdout.strip() if stdout.strip() else "❌ Empty response"
            else:
                return f"❌ Claude error: {{stderr}}"
        except Exception as e:
            return f"❌ Error: {{e}}"

def create_pcb_context_message(analysis, user_message):
    """Create PCB context message."""
    context = f"""I'm working in KiCad PCB Editor and need help with PCB design.

PCB PROJECT CONTEXT:
- Board Name: {{analysis['board_name']}}
- Components: {{analysis['component_count']}}
- Board Size: {{analysis['board_size']}}
- Routing: {{analysis['track_segments']}} tracks, {{analysis['via_count']}} vias
- Nets: {{analysis['net_count']}}

CURRENT PCB:"""
    
    if analysis['components']:
        context += "\\nComponents on PCB:"
        for comp in analysis['components'][:8]:
            context += f"\\n- {{comp['ref']}}: {{comp['value']}} ({{comp['footprint']}})"
        
        if len(analysis['components']) > 8:
            context += f"\\n- ... and {{len(analysis['components']) - 8}} more components"
    
    if analysis['component_types']:
        context += "\\n\\nComponent Types:"
        for comp_type, count in sorted(analysis['component_types'].items())[:5]:
            context += f"\\n- {{comp_type}}: {{count}} components"
    
    context += f"""

Please provide PCB design advice focusing on:
- Component placement optimization
- Routing strategies and best practices  
- Signal integrity and power delivery
- Manufacturing considerations (DFM)
- Thermal management
- EMI/EMC design guidelines

QUESTION: {{user_message}}"""
    
    return context

def main():
    """Main PCB chat interface."""
    claude = KiCadPCBClaudeBridge()
    
    root = tk.Tk()
    root.title("💬 KiCad PCB-Claude Chat")
    root.geometry("1000x800")
    root.configure(bg='#2b2b2b')
    
    # Status label
    status_label = tk.Label(root, text="Connecting to Claude...", 
                           bg='#2b2b2b', fg='orange', font=('Arial', 10, 'bold'))
    status_label.pack(pady=5)
    
    # Chat display
    chat_display = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=('Consolas', 10),
                                            bg='#1e1e1e', fg='#e0e0e0')
    chat_display.pack(fill=tk.BOTH, expand=True, padx=10, pady=5)
    
    # Welcome message
    welcome = f"""💬 KiCad PCB-Claude Chat Interface
{{'='*60}}

📋 PCB Project: {{analysis_data['board_name']}}
🔧 Components: {{analysis_data['component_count']}}
📏 Board Size: {{analysis_data['board_size']}}
🔗 Routing: {{analysis_data['track_segments']}} tracks, {{analysis_data['via_count']}} vias

🎯 I can help with PCB design advice and guidance!

Ask me anything about your PCB design!
"""
    
    chat_display.insert(tk.END, welcome)
    chat_display.config(state=tk.DISABLED)
    
    # Input frame
    input_frame = tk.Frame(root, bg='#2b2b2b')
    input_frame.pack(fill=tk.X, padx=10, pady=5)
    
    message_entry = tk.Entry(input_frame, font=('Arial', 12), bg='#3a3a3a', fg='white')
    message_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
    
    def send_message():
        message = message_entry.get().strip()
        if not message:
            return
        
        message_entry.delete(0, tk.END)
        
        # Add user message
        chat_display.config(state=tk.NORMAL)
        chat_display.insert(tk.END, f"\\n\\n🧑 You: {{message}}")
        chat_display.config(state=tk.DISABLED)
        chat_display.see(tk.END)
        
        # Send to Claude
        context_message = create_pcb_context_message(analysis_data, message)
        response = claude.send_message(context_message)
        
        # Add Claude response
        chat_display.config(state=tk.NORMAL)
        chat_display.insert(tk.END, f"\\n\\n🤖 Claude: {{response}}")
        chat_display.config(state=tk.DISABLED)
        chat_display.see(tk.END)
    
    send_btn = tk.Button(input_frame, text="Send", command=send_message, 
                        font=('Arial', 12), bg='#0066cc', fg='white')
    send_btn.pack(side=tk.RIGHT)
    
    message_entry.bind('<Return>', lambda e: send_message())
    
    # Connect to Claude
    def connect():
        if claude.connect():
            status_label.config(text="✅ Claude Connected for PCB Design", fg='green')
            send_btn.config(state='normal')
        else:
            status_label.config(text="❌ Claude Connection Failed", fg='red')
            send_btn.config(state='disabled')
    
    root.after(1000, connect)
    message_entry.focus()
    
    root.mainloop()

if __name__ == "__main__":
    main()
'''
        
        # Write the script to a temporary file
        with tempfile.NamedTemporaryFile(mode='w', suffix='.py', delete=False) as f:
            f.write(chat_script)
            script_path = f.name
        
        # Make it executable
        os.chmod(script_path, 0o755)
        
        # Launch using system Python (not KiCad's Python)
        cmd = ["/usr/bin/python3", script_path]
        
        print(f"🔧 Launching standalone chat: {' '.join(cmd)}")
        
        # Launch in background
        process = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL
        )
        
        print(f"✅ Standalone PCB chat launched with PID: {process.pid}")
        return True
        
    except Exception as e:
        print(f"❌ Failed to launch standalone chat: {e}")
        import traceback
        print(f"   Traceback: {traceback.format_exc()}")
        return False

class CircuitSynthPCBExternalChat(pcbnew.ActionPlugin):
    """
    Circuit-Synth PCB External Chat Plugin for KiCad PCB Editor.
    
    Launches external Claude chat interface to avoid tkinter issues.
    """

    def defaults(self):
        """Set up plugin defaults."""
        self.name = "Circuit-Synth PCB Chat (External)"
        self.category = "Circuit Design"
        self.description = "External Claude AI chat interface for PCB design assistance"
        self.show_toolbar_button = True
        
    def Run(self):
        """Execute the plugin."""
        try:
            print("💬 Circuit-Synth PCB External Chat Starting...")
            
            # Get the current board
            board = pcbnew.GetBoard()
            if board is None:
                error_msg = "No PCB board found. Please open a PCB file first."
                print(f"❌ {error_msg}")
                wx.MessageBox(error_msg, "Circuit-Synth PCB Chat", wx.OK | wx.ICON_WARNING)
                return

            print("✅ PCB board found, analyzing...")
            
            # Analyze the board
            analysis = analyze_pcb_board(board)
            
            if analysis.get('success'):
                print(f"✅ Board analysis complete: {analysis['component_count']} components")
                print(f"   Board: {analysis['board_name']}")
                print(f"   Size: {analysis['board_size']}")
                print(f"   Routing: {analysis['track_segments']} tracks, {analysis['via_count']} vias")
                
                # Try standalone approach first (most likely to work)
                print("🚀 Launching standalone PCB chat interface...")
                if launch_standalone_pcb_chat(analysis):
                    print("✅ Standalone PCB chat launched successfully")
                    wx.MessageBox(
                        f"PCB Chat Launched!\\n\\n" +
                        f"Board: {analysis['board_name']}\\n" +
                        f"Components: {analysis['component_count']}\\n" +
                        f"Size: {analysis['board_size']}\\n\\n" +
                        f"The Claude chat interface should appear in a separate window.",
                        "PCB Chat Launched",
                        wx.OK | wx.ICON_INFORMATION
                    )
                else:
                    print("❌ Standalone chat failed, trying BOM plugin approach...")
                    if launch_external_pcb_chat(analysis):
                        print("✅ External chat launched via BOM plugin")
                    else:
                        error_msg = "Failed to launch external chat interface.\\n\\n" + \
                                   "This usually means:\\n" + \
                                   "• Python tkinter not available on system\\n" + \
                                   "• Claude CLI not installed\\n" + \
                                   "• System permissions issue\\n\\n" + \
                                   "Try using the working Schematic BOM plugin instead."
                        print("❌ All external launch methods failed")
                        wx.MessageBox(error_msg, "Launch Failed", wx.OK | wx.ICON_ERROR)
            else:
                error_msg = f"Board analysis failed: {analysis.get('error', 'Unknown error')}"
                print(f"❌ {error_msg}")
                wx.MessageBox(error_msg, "Analysis Error", wx.OK | wx.ICON_ERROR)

        except Exception as e:
            error_msg = f"Plugin error: {str(e)}"
            print(f"❌ Plugin exception: {error_msg}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            wx.MessageBox(f"Plugin error: {error_msg}\\n\\nCheck scripting console for details.", 
                         "Plugin Error", wx.OK | wx.ICON_ERROR)

# Register the plugin
CircuitSynthPCBExternalChat().register()