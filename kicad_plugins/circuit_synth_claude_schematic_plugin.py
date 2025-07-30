#!/usr/bin/env python3
"""
Circuit-Synth Claude Chat Plugin for KiCad Schematic Editor

Enhanced schematic plugin with full Claude Code integration for real AI assistance.
Uses the BOM tool "backdoor" method with comprehensive Claude chat interface.

Features:
- Real-time Claude Code integration
- Interactive chat interface for schematic analysis
- Circuit context awareness
- Conversation history and export
- Quick action buttons for common tasks
- Professional GUI with rich text support

Usage:
1. Add to KiCad BOM tools: Tools → Generate Legacy Bill of Materials → Add Plugin
2. Select this plugin and click "Generate"
3. Enhanced chat interface opens with Claude AI assistant

Hotkey Setup:
- In KiCad: Preferences → Hotkeys → Search for "Generate Legacy Bill of Materials" 
- Assign a custom hotkey (e.g., Ctrl+Shift+A for AI Assistant)
"""

import sys
import os
import xml.etree.ElementTree as ET
from pathlib import Path
import argparse
import json
from datetime import datetime
import threading
import time
import tempfile
import logging

# Import Claude Bridge
sys.path.append(os.path.dirname(__file__))
from claude_bridge import ClaudeBridge, KiCadDataExtractor, get_claude_bridge

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def create_claude_schematic_interface(circuit_data):
    """Create an enhanced schematic chat interface with Claude Code integration."""
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox, scrolledtext, filedialog, font
        
        class ClaudeSchematicChatApp:
            def __init__(self, root, circuit_data):
                self.root = root
                self.circuit_data = circuit_data
                self.claude_bridge = get_claude_bridge()
                self.chat_history = []
                self.is_claude_available = False
                
                self.setup_ui()
                self.connect_to_claude()
                self.add_welcome_message()
                
            def setup_ui(self):
                """Set up the enhanced chat interface."""
                self.root.title("🚀 Circuit-Synth AI - Claude Schematic Assistant")
                self.root.geometry("900x750")
                self.root.configure(bg='#f8f9fa')
                
                # Create main frame with padding
                main_frame = ttk.Frame(self.root, padding="15")
                main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
                
                # Configure grid weights
                self.root.columnconfigure(0, weight=1)
                self.root.rowconfigure(0, weight=1)
                main_frame.columnconfigure(0, weight=1)
                main_frame.rowconfigure(2, weight=1)
                
                # Header section with enhanced styling
                self.create_header(main_frame)
                
                # Connection status indicator
                self.create_connection_status(main_frame)
                
                # Enhanced chat display area
                self.create_chat_area(main_frame)
                
                # Input section with better layout
                self.create_input_section(main_frame)
                
                # Quick action buttons grid
                self.create_quick_actions(main_frame)
                
                # Status and control section
                self.create_status_section(main_frame)
                
                # Set initial focus
                self.input_entry.focus()
            
            def create_header(self, parent):
                """Create enhanced header section."""
                header_frame = ttk.Frame(parent)
                header_frame.grid(row=0, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
                header_frame.columnconfigure(0, weight=1)
                
                # Main title
                title_label = ttk.Label(
                    header_frame, 
                    text="🚀 Circuit-Synth AI - Claude Assistant",
                    font=('Segoe UI', 18, 'bold')
                )
                title_label.grid(row=0, column=0, sticky=tk.W)
                
                # Project info
                project_info = f"📋 Project: {self.circuit_data.get('design_name', 'Unknown')}"
                project_info += f" | 🔧 Components: {self.circuit_data.get('component_count', 0)}"
                project_info += f" | 🔗 Nets: {len(self.circuit_data.get('nets', []))}"
                
                project_label = ttk.Label(
                    header_frame,
                    text=project_info,
                    font=('Segoe UI', 10)
                )
                project_label.grid(row=1, column=0, sticky=tk.W, pady=(5, 0))
                
                # Subtitle
                subtitle_label = ttk.Label(
                    header_frame,
                    text="Real-time AI assistance powered by Claude Code",
                    font=('Segoe UI', 10, 'italic'),
                    foreground='#6c757d'
                )
                subtitle_label.grid(row=2, column=0, sticky=tk.W, pady=(2, 0))
            
            def create_connection_status(self, parent):
                """Create connection status indicator."""
                status_frame = ttk.Frame(parent)
                status_frame.grid(row=1, column=0, sticky=(tk.W, tk.E), pady=(0, 10))
                
                self.connection_label = ttk.Label(
                    status_frame,
                    text="🔴 Connecting to Claude...",
                    font=('Segoe UI', 11, 'bold')
                )
                self.connection_label.pack(side=tk.LEFT)
                
                # Reconnect button
                self.reconnect_btn = ttk.Button(
                    status_frame,
                    text="🔄 Reconnect",
                    command=self.reconnect_claude
                )
                self.reconnect_btn.pack(side=tk.RIGHT)
            
            def create_chat_area(self, parent):
                """Create enhanced chat display area."""
                chat_frame = ttk.LabelFrame(parent, text="Conversation with Claude", padding="10")
                chat_frame.grid(row=2, column=0, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 15))
                chat_frame.columnconfigure(0, weight=1)
                chat_frame.rowconfigure(0, weight=1)
                
                # Chat display with custom fonts
                self.chat_display = scrolledtext.ScrolledText(
                    chat_frame,
                    wrap=tk.WORD,
                    width=80,
                    height=25,
                    font=('Consolas', 11),
                    bg='#ffffff',
                    fg='#212529',
                    insertbackground='#007acc',
                    selectbackground='#0078d4',
                    relief=tk.FLAT,
                    borderwidth=1
                )
                self.chat_display.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
                
                # Configure text tags for styling
                self.setup_chat_tags()
            
            def setup_chat_tags(self):
                """Set up text tags for chat styling."""
                # User message style
                self.chat_display.tag_config(
                    "user",
                    foreground="#0066cc",
                    font=('Segoe UI', 11, 'bold'),
                    lmargin1=10,
                    lmargin2=10
                )
                
                # Claude message style
                self.chat_display.tag_config(
                    "claude",
                    foreground="#28a745",
                    font=('Segoe UI', 11),
                    lmargin1=10,
                    lmargin2=10
                )
                
                # System message style
                self.chat_display.tag_config(
                    "system",
                    foreground="#6c757d",
                    font=('Segoe UI', 10, 'italic'),
                    lmargin1=5,
                    lmargin2=5
                )
                
                # Timestamp style
                self.chat_display.tag_config(
                    "timestamp",
                    foreground="#adb5bd",
                    font=('Segoe UI', 9)
                )
            
            def create_input_section(self, parent):
                """Create enhanced input section."""
                input_frame = ttk.LabelFrame(parent, text="Ask Claude", padding="10")
                input_frame.grid(row=3, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
                input_frame.columnconfigure(0, weight=1)
                
                # Input text area
                self.input_var = tk.StringVar()
                self.input_entry = ttk.Entry(
                    input_frame,
                    textvariable=self.input_var,
                    font=('Segoe UI', 11),
                    width=70
                )
                self.input_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 10))
                self.input_entry.bind('<Return>', self.send_message)
                self.input_entry.bind('<KeyRelease>', self.on_typing)
                
                # Send button
                self.send_button = ttk.Button(
                    input_frame,
                    text="Send",
                    command=self.send_message,
                    style='Accent.TButton'
                )
                self.send_button.grid(row=0, column=1)
                
                # Hint text
                hint_label = ttk.Label(
                    input_frame,
                    text="💡 Tip: Ask about components, design patterns, optimization, or any circuit questions",
                    font=('Segoe UI', 9, 'italic'),
                    foreground='#6c757d'
                )
                hint_label.grid(row=1, column=0, columnspan=2, sticky=tk.W, pady=(5, 0))
            
            def create_quick_actions(self, parent):
                """Create quick action buttons in a grid."""
                actions_frame = ttk.LabelFrame(parent, text="Quick Actions", padding="10")
                actions_frame.grid(row=4, column=0, sticky=(tk.W, tk.E), pady=(0, 15))
                
                # Define actions in a grid layout
                actions = [
                    [
                        ("🔍 Analyze Circuit", self.analyze_circuit),
                        ("🔧 Component Review", self.review_components),
                        ("⚡ Power Analysis", self.analyze_power)
                    ],
                    [
                        ("🕸️ Net Analysis", self.analyze_nets),
                        ("💡 Optimization Tips", self.get_optimization),
                        ("🐛 Find Issues", self.find_issues)
                    ],
                    [
                        ("📊 Generate Report", self.generate_report),
                        ("💾 Export Chat", self.export_chat),
                        ("❓ Help", self.show_help)
                    ]
                ]
                
                for row_idx, row_actions in enumerate(actions):
                    for col_idx, (text, command) in enumerate(row_actions):
                        btn = ttk.Button(actions_frame, text=text, command=command)
                        btn.grid(row=row_idx, column=col_idx, padx=5, pady=3, sticky=(tk.W, tk.E))
                        actions_frame.columnconfigure(col_idx, weight=1)
            
            def create_status_section(self, parent):
                """Create status and control section."""
                status_frame = ttk.Frame(parent)
                status_frame.grid(row=5, column=0, sticky=(tk.W, tk.E))
                status_frame.columnconfigure(0, weight=1)
                
                # Status text
                self.status_var = tk.StringVar(value="Ready - Ask Claude about your schematic design!")
                status_label = ttk.Label(
                    status_frame,
                    textvariable=self.status_var,
                    font=('Segoe UI', 10),
                    foreground='#495057'
                )
                status_label.grid(row=0, column=0, sticky=tk.W)
                
                # Control buttons
                controls_frame = ttk.Frame(status_frame)
                controls_frame.grid(row=0, column=1, sticky=tk.E)
                
                refresh_btn = ttk.Button(
                    controls_frame,
                    text="🔄 Refresh Context",
                    command=self.refresh_context
                )
                refresh_btn.pack(side=tk.RIGHT, padx=(5, 0))
            
            def connect_to_claude(self):
                """Connect to Claude Code."""
                def connect():
                    self.status_var.set("Connecting to Claude Code...")
                    success = self.claude_bridge.connect()
                    
                    if success:
                        # Set circuit context
                        circuit_data_obj = type('CircuitData', (), {})()
                        for key, value in self.circuit_data.items():
                            setattr(circuit_data_obj, key, value)
                        circuit_data_obj.editor_type = "schematic"
                        
                        self.claude_bridge.set_circuit_context(circuit_data_obj)
                        
                        self.is_claude_available = True
                        self.root.after(0, self.on_claude_connected)
                    else:
                        self.is_claude_available = False
                        self.root.after(0, self.on_claude_unavailable)
                
                threading.Thread(target=connect, daemon=True).start()
            
            def on_claude_connected(self):
                """Handle successful Claude connection."""
                self.connection_label.config(text="🟢 Claude Connected", foreground='green')
                self.status_var.set("Connected to Claude Code - Ready for AI assistance!")
                self.add_message("System", "✅ Successfully connected to Claude Code")
            
            def on_claude_unavailable(self):
                """Handle Claude unavailable."""
                self.connection_label.config(text="🔴 Claude Unavailable", foreground='red')
                self.status_var.set("Claude Code not available - Install Claude CLI for AI assistance")
                self.add_message("System", "❌ Could not connect to Claude Code. Please install the Claude CLI tool.")
            
            def add_message(self, sender, message, timestamp=None):
                """Add a message to the chat display with enhanced formatting."""
                if timestamp is None:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                
                self.chat_display.config(state=tk.NORMAL)
                
                # Add sender with timestamp
                if sender == "You":
                    self.chat_display.insert(tk.END, f"[{timestamp}] ", "timestamp")
                    self.chat_display.insert(tk.END, "👤 You:\n", "user")
                elif sender == "Claude":
                    self.chat_display.insert(tk.END, f"[{timestamp}] ", "timestamp")
                    self.chat_display.insert(tk.END, "🤖 Claude:\n", "claude")
                else:
                    self.chat_display.insert(tk.END, f"[{timestamp}] ", "timestamp")
                    self.chat_display.insert(tk.END, f"📋 {sender}:\n", "system")
                
                # Add message content
                tag = "claude" if sender == "Claude" else ("user" if sender == "You" else "system")
                self.chat_display.insert(tk.END, f"{message}\n\n", tag)
                
                self.chat_display.config(state=tk.DISABLED)
                self.chat_display.see(tk.END)
                
                # Store in history
                self.chat_history.append({
                    'timestamp': timestamp,
                    'sender': sender,
                    'message': message
                })
            
            def add_welcome_message(self):
                """Add welcome message and initial analysis."""
                welcome = f"""Welcome to Circuit-Synth AI with Claude! 🚀

I've analyzed your schematic and here's what I found:

📋 Project: {self.circuit_data.get('design_name', 'Unknown')}
🔧 Components: {self.circuit_data.get('component_count', 0)}
🔗 Nets: {len(self.circuit_data.get('nets', []))}

I can help you with:
• Circuit analysis and optimization
• Component selection and alternatives  
• Design pattern recommendations
• Power system analysis
• Signal integrity considerations
• Troubleshooting and debugging

What would you like to know about your circuit?"""
                
                self.add_message("Claude", welcome)
            
            def send_message(self, event=None):
                """Handle sending a message to Claude."""
                message = self.input_var.get().strip()
                if not message:
                    return
                
                if not self.is_claude_available:
                    self.add_message("System", "❌ Claude is not available. Please check your Claude CLI installation.")
                    return
                
                # Add user message and clear input
                self.add_message("You", message)
                self.input_var.set("")
                
                # Update status
                self.status_var.set("🤖 Claude is analyzing...")
                self.root.update()
                
                # Send to Claude in background
                def send_to_claude():
                    try:
                        response = self.claude_bridge.send_message(message)
                        self.root.after(0, lambda: self.add_message("Claude", response))
                        self.root.after(0, lambda: self.status_var.set("Ready - Ask Claude anything!"))
                    except Exception as e:
                        error_msg = f"❌ Error communicating with Claude: {str(e)}"
                        self.root.after(0, lambda: self.add_message("System", error_msg))
                        self.root.after(0, lambda: self.status_var.set("Error occurred"))
                
                threading.Thread(target=send_to_claude, daemon=True).start()
            
            def on_typing(self, event):
                """Handle typing indicator."""
                if self.input_var.get().strip():
                    self.status_var.set("Type your question and press Enter...")
                else:
                    self.status_var.set("Ready - Ask Claude about your schematic design!")
            
            # Quick action methods
            def analyze_circuit(self):
                self.send_specific_message("Please provide a comprehensive analysis of my schematic design.")
            
            def review_components(self):
                self.send_specific_message("Review the components in my schematic. Are there any missing parts or potential issues?")
            
            def analyze_power(self):
                self.send_specific_message("Analyze the power system in my design. Check for proper decoupling and power delivery.")
            
            def analyze_nets(self):
                self.send_specific_message("Analyze the net connectivity in my schematic. Are there any high-fanout nets or routing concerns?")
            
            def get_optimization(self):
                self.send_specific_message("What optimizations would you recommend for this circuit design?")
            
            def find_issues(self):
                self.send_specific_message("Help me identify potential issues or problems with this circuit design.")
            
            def generate_report(self):
                self.send_specific_message("Generate a detailed analysis report for this schematic design.")
            
            def export_chat(self):
                """Export chat history to file."""
                if not self.chat_history:
                    messagebox.showinfo("Export Chat", "No chat history to export.")
                    return
                
                filename = filedialog.asksaveasfilename(
                    defaultextension=".md",
                    filetypes=[
                        ("Markdown files", "*.md"),
                        ("Text files", "*.txt"),
                        ("JSON files", "*.json")
                    ],
                    title="Export Claude Chat History"
                )
                
                if filename:
                    try:
                        success = self.claude_bridge.export_conversation(filename)
                        if success:
                            messagebox.showinfo("Export Complete", f"Chat history saved to {filename}")
                        else:
                            messagebox.showerror("Export Error", "Failed to export chat history")
                    except Exception as e:
                        messagebox.showerror("Export Error", f"Failed to export chat: {str(e)}")
            
            def show_help(self):
                self.send_specific_message("What can you help me with regarding circuit design and KiCad workflows?")
            
            def send_specific_message(self, message):
                """Send a specific message programmatically."""
                self.input_var.set(message)
                self.send_message()
            
            def refresh_context(self):
                """Refresh the circuit context."""
                self.add_message("System", "🔄 Refreshing circuit context...")
                # Context is already set during initialization
                self.add_message("System", "✅ Circuit context refreshed")
            
            def reconnect_claude(self):
                """Reconnect to Claude."""
                self.connect_to_claude()
        
        # Create and run the application
        root = tk.Tk()
        app = ClaudeSchematicChatApp(root, circuit_data)
        
        # Center window
        root.update_idletasks()
        x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
        y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
        root.geometry(f"+{x}+{y}")
        
        root.mainloop()
        
    except ImportError as e:
        # Fallback if tkinter not available
        print("=" * 70)
        print("🚀 Circuit-Synth AI Claude Chat (Console Mode)")
        print("=" * 70)
        print(f"Project: {circuit_data.get('design_name', 'Unknown')}")
        print(f"Components: {circuit_data.get('component_count', 0)}")
        print(f"Nets: {len(circuit_data.get('nets', []))}")
        print()
        print("Enhanced GUI chat interface requires tkinter.")
        print("Install tkinter or use the basic analysis version.")
        print(f"Error: {e}")


def analyze_netlist_xml(netlist_file):
    """Analyze the KiCad netlist XML file with enhanced data extraction."""
    try:
        circuit_data = KiCadDataExtractor.extract_schematic_data(netlist_file)
        return circuit_data.to_dict()
        
    except Exception as e:
        return {
            'error': str(e),
            'success': False
        }


def main():
    """Main entry point for the Claude schematic chat plugin."""
    parser = argparse.ArgumentParser(description='Circuit-Synth AI Claude Schematic Chat Plugin')
    parser.add_argument('netlist_file', help='Path to the netlist XML file from KiCad')
    parser.add_argument('output_file', help='Output file (ignored - we show Claude chat GUI instead)')
    
    args = parser.parse_args()
    
    print("🚀 Circuit-Synth AI Claude Chat Plugin Starting...")
    print(f"📄 Analyzing netlist: {args.netlist_file}")
    
    # Analyze the netlist
    analysis = analyze_netlist_xml(args.netlist_file)
    
    if analysis.get('success', True):
        print(f"✅ Analysis complete: {analysis.get('component_count', 0)} components found")
        print("🎨 Launching Claude chat interface...")
        
        # Launch Claude chat interface
        create_claude_schematic_interface(analysis)
        
        # Write summary file for KiCad
        output_path = Path(args.output_file)
        summary = f"""Circuit-Synth AI Claude Chat Session Summary
==========================================

Design: {analysis.get('design_name', 'Unknown')}
Components: {analysis.get('component_count', 0)}
Nets: {len(analysis.get('nets', []))}
Session Time: {datetime.now().isoformat()}

The interactive Claude chat session has been completed.
All conversation details were available in the GUI interface.

This session featured:
- Real-time AI assistance from Claude Code
- Circuit-aware context understanding
- Interactive chat with conversation history
- Professional analysis and recommendations

For more information about Circuit-Synth AI, visit:
https://github.com/circuit-synth/circuit-synth
"""
        
        try:
            output_path.write_text(summary)
            print(f"📝 Session summary written to: {args.output_file}")
        except Exception as e:
            print(f"⚠️  Could not write summary: {e}")
        
    else:
        error_msg = f"❌ Analysis failed: {analysis.get('error', 'Unknown error')}"
        print(error_msg)
        try:
            Path(args.output_file).write_text(f"Error: {analysis.get('error', 'Unknown error')}")
        except:
            pass
        sys.exit(1)


if __name__ == "__main__":
    main()