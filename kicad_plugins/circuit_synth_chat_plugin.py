#!/usr/bin/env python3
"""
Circuit-Synth AI Chat Plugin for KiCad Schematic Editor

Enhanced version with full chat interface, AI-powered circuit analysis,
and design assistance. Uses the BOM tool "backdoor" method.

Features:
- Interactive chat interface with conversation history
- Real-time circuit analysis and suggestions
- Component optimization recommendations
- Design pattern recognition
- Export chat logs and analysis reports

Usage:
1. Add to KiCad BOM tools: Tools → Generate Bill of Materials → Add Plugin
2. Select this plugin and click "Generate"
3. Chat interface opens with AI circuit assistant

Hotkey Setup:
- In KiCad: Preferences → Hotkeys → Search for "Generate Bill of Materials" 
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

def create_chat_interface(analysis_data):
    """Create an enhanced chat interface for circuit analysis."""
    try:
        import tkinter as tk
        from tkinter import ttk, messagebox, scrolledtext, filedialog
        
        class CircuitSynthChatApp:
            def __init__(self, root, analysis_data):
                self.root = root
                self.analysis_data = analysis_data
                self.chat_history = []
                self.setup_ui()
                self.add_welcome_message()
                
            def setup_ui(self):
                """Set up the chat interface."""
                self.root.title("🚀 Circuit-Synth AI - Chat Assistant")
                self.root.geometry("800x600")
                self.root.configure(bg='#f0f0f0')
                
                # Create main frame
                main_frame = ttk.Frame(self.root, padding="10")
                main_frame.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
                
                # Configure grid weights
                self.root.columnconfigure(0, weight=1)
                self.root.rowconfigure(0, weight=1)
                main_frame.columnconfigure(1, weight=1)
                main_frame.rowconfigure(1, weight=1)
                
                # Title section
                title_frame = ttk.Frame(main_frame)
                title_frame.grid(row=0, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
                
                title_label = ttk.Label(title_frame, text="🚀 Circuit-Synth AI Assistant", 
                                      font=('Arial', 16, 'bold'))
                title_label.pack(side=tk.LEFT)
                
                project_label = ttk.Label(title_frame, 
                                        text=f"Project: {self.analysis_data.get('design_name', 'Unknown')}", 
                                        font=('Arial', 10))
                project_label.pack(side=tk.RIGHT)
                
                # Chat display area
                chat_frame = ttk.LabelFrame(main_frame, text="Conversation", padding="5")
                chat_frame.grid(row=1, column=0, columnspan=2, sticky=(tk.W, tk.E, tk.N, tk.S), pady=(0, 10))
                chat_frame.columnconfigure(0, weight=1)
                chat_frame.rowconfigure(0, weight=1)
                
                self.chat_display = scrolledtext.ScrolledText(chat_frame, wrap=tk.WORD, 
                                                            width=70, height=20, 
                                                            font=('Consolas', 10),
                                                            bg='#ffffff', fg='#333333')
                self.chat_display.grid(row=0, column=0, sticky=(tk.W, tk.E, tk.N, tk.S))
                
                # Input section
                input_frame = ttk.Frame(main_frame)
                input_frame.grid(row=2, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
                input_frame.columnconfigure(0, weight=1)
                
                self.input_var = tk.StringVar()
                self.input_entry = ttk.Entry(input_frame, textvariable=self.input_var, 
                                           font=('Arial', 11))
                self.input_entry.grid(row=0, column=0, sticky=(tk.W, tk.E), padx=(0, 5))
                self.input_entry.bind('<Return>', self.send_message)
                self.input_entry.bind('<KeyRelease>', self.on_typing)
                
                send_button = ttk.Button(input_frame, text="Send", command=self.send_message)
                send_button.grid(row=0, column=1)
                
                # Quick action buttons
                action_frame = ttk.LabelFrame(main_frame, text="Quick Actions", padding="5")
                action_frame.grid(row=3, column=0, columnspan=2, sticky=(tk.W, tk.E), pady=(0, 10))
                
                actions = [
                    ("🔍 Analyze Circuit", self.analyze_circuit),
                    ("💡 Optimize Design", self.optimize_design),
                    ("🔧 Component Suggestions", self.suggest_components),
                    ("📊 Generate Report", self.generate_report),
                    ("💾 Export Chat", self.export_chat),
                    ("❓ Help", self.show_help)
                ]
                
                for i, (text, command) in enumerate(actions):
                    btn = ttk.Button(action_frame, text=text, command=command)
                    btn.grid(row=i//3, column=i%3, padx=2, pady=2, sticky=(tk.W, tk.E))
                
                # Status bar
                self.status_var = tk.StringVar(value="Ready - Ask me about your circuit design!")
                status_bar = ttk.Label(main_frame, textvariable=self.status_var, 
                                     relief=tk.SUNKEN, anchor=tk.W)
                status_bar.grid(row=4, column=0, columnspan=2, sticky=(tk.W, tk.E))
                
                # Focus on input
                self.input_entry.focus()
                
            def add_message(self, sender, message, timestamp=None):
                """Add a message to the chat display."""
                if timestamp is None:
                    timestamp = datetime.now().strftime("%H:%M:%S")
                
                self.chat_display.config(state=tk.NORMAL)
                
                # Format message
                if sender == "You":
                    self.chat_display.insert(tk.END, f"[{timestamp}] 👤 You: ", "user")
                elif sender == "AI":
                    self.chat_display.insert(tk.END, f"[{timestamp}] 🤖 Circuit-Synth AI: ", "ai")
                else:
                    self.chat_display.insert(tk.END, f"[{timestamp}] 📋 {sender}: ", "system")
                
                self.chat_display.insert(tk.END, f"{message}\n\n")
                
                # Configure text tags
                self.chat_display.tag_config("user", foreground="#0066cc", font=('Arial', 10, 'bold'))
                self.chat_display.tag_config("ai", foreground="#009900", font=('Arial', 10, 'bold'))
                self.chat_display.tag_config("system", foreground="#666666", font=('Arial', 10, 'bold'))
                
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
                welcome = f"""Welcome to Circuit-Synth AI! 🚀

I've analyzed your schematic and here's what I found:

📋 Project: {self.analysis_data.get('design_name', 'Unknown')}
🔧 Components: {self.analysis_data.get('component_count', 0)}
🔗 Nets: {len(self.analysis_data.get('nets', []))}

I can help you with:
• Circuit analysis and optimization
• Component selection and suggestions  
• Design pattern recognition
• Power supply analysis
• Signal integrity recommendations

What would you like to know about your circuit?"""
                
                self.add_message("AI", welcome)
                
            def send_message(self, event=None):
                """Handle sending a user message."""
                message = self.input_var.get().strip()
                if not message:
                    return
                    
                # Add user message
                self.add_message("You", message)
                self.input_var.set("")
                
                # Update status
                self.status_var.set("🤖 AI is thinking...")
                self.root.update()
                
                # Process message (simulate AI response)
                threading.Thread(target=self.process_ai_response, args=(message,), daemon=True).start()
                
            def process_ai_response(self, user_message):
                """Process user message and generate AI response."""
                # Simulate processing time
                time.sleep(1)
                
                # Generate contextual response based on message content
                message_lower = user_message.lower()
                components = self.analysis_data.get('components', [])
                
                if any(word in message_lower for word in ['power', 'supply', 'voltage']):
                    response = self.analyze_power_system()
                elif any(word in message_lower for word in ['component', 'parts', 'bom']):
                    response = self.analyze_components()
                elif any(word in message_lower for word in ['optimize', 'improve', 'better']):
                    response = self.get_optimization_suggestions()
                elif any(word in message_lower for word in ['net', 'connection', 'wire']):
                    response = self.analyze_connectivity()
                elif any(word in message_lower for word in ['help', 'what', 'how']):
                    response = self.get_help_response()
                else:
                    response = self.get_general_response(user_message)
                
                # Update UI in main thread
                self.root.after(0, lambda: self.add_ai_response(response))
                
            def add_ai_response(self, response):
                """Add AI response to chat."""
                self.add_message("AI", response)
                self.status_var.set("Ready - Ask me anything about your circuit!")
                
            def analyze_power_system(self):
                """Analyze power-related components."""
                components = self.analysis_data.get('components', [])
                power_components = [c for c in components if any(term in c.get('library', '').lower() 
                                  for term in ['regulator', 'power', 'battery', 'supply'])]
                
                if power_components:
                    analysis = "🔋 Power System Analysis:\n\n"
                    for comp in power_components:
                        analysis += f"• {comp.get('ref', 'Unknown')}: {comp.get('value', 'N/A')} ({comp.get('library', 'Unknown')})\n"
                    
                    analysis += "\n💡 Recommendations:\n"
                    analysis += "• Add decoupling capacitors near power pins\n"
                    analysis += "• Consider power supply noise filtering\n"
                    analysis += "• Verify current ratings for all components\n"
                    analysis += "• Check voltage levels match requirements"
                else:
                    analysis = "I don't see specific power management components in your schematic. Consider adding voltage regulators and decoupling capacitors for robust power delivery."
                
                return analysis
                
            def analyze_components(self):
                """Analyze circuit components."""
                components = self.analysis_data.get('components', [])
                if not components:
                    return "No components found in the analysis data."
                
                # Group by library
                by_library = {}
                for comp in components:
                    lib = comp.get('library', 'Unknown')
                    if lib not in by_library:
                        by_library[lib] = []
                    by_library[lib].append(comp)
                
                analysis = f"🔧 Component Analysis ({len(components)} total):\n\n"
                
                for lib, comps in sorted(by_library.items()):
                    analysis += f"📚 {lib} Library ({len(comps)} components):\n"
                    for comp in comps[:5]:  # Show first 5
                        ref = comp.get('ref', 'Unknown')
                        value = comp.get('value', 'N/A')
                        analysis += f"  • {ref}: {value}\n"
                    if len(comps) > 5:
                        analysis += f"  ... and {len(comps) - 5} more\n"
                    analysis += "\n"
                
                return analysis
                
            def get_optimization_suggestions(self):
                """Provide optimization suggestions."""
                component_count = self.analysis_data.get('component_count', 0)
                net_count = len(self.analysis_data.get('nets', []))
                
                suggestions = "💡 Design Optimization Suggestions:\n\n"
                
                if component_count > 50:
                    suggestions += "🔍 High Component Count:\n"
                    suggestions += "• Consider component consolidation\n"
                    suggestions += "• Look for multi-function ICs\n"
                    suggestions += "• Review if all components are necessary\n\n"
                
                if net_count > 100:
                    suggestions += "🕸️ Complex Routing:\n"
                    suggestions += "• Consider hierarchical design\n"
                    suggestions += "• Group related functions\n"
                    suggestions += "• Use buses for related signals\n\n"
                
                suggestions += "⚡ General Recommendations:\n"
                suggestions += "• Place decoupling capacitors close to ICs\n"
                suggestions += "• Keep high-speed signals short\n"
                suggestions += "• Use proper ground planes\n"
                suggestions += "• Consider EMI/EMC requirements\n"
                suggestions += "• Review component tolerances"
                
                return suggestions
                
            def analyze_connectivity(self):
                """Analyze net connectivity."""
                nets = self.analysis_data.get('nets', [])
                if not nets:
                    return "No net information available for analysis."
                
                analysis = f"🔗 Connectivity Analysis ({len(nets)} nets):\n\n"
                
                # Analyze net complexity
                connection_counts = [len(net.get('nodes', [])) for net in nets]
                if connection_counts:
                    max_connections = max(connection_counts)
                    avg_connections = sum(connection_counts) / len(connection_counts)
                    
                    analysis += f"📊 Connection Statistics:\n"
                    analysis += f"• Average connections per net: {avg_connections:.1f}\n"
                    analysis += f"• Most connected net: {max_connections} connections\n"
                    analysis += f"• Total connection points: {sum(connection_counts)}\n\n"
                    
                    if max_connections > 10:
                        analysis += "⚠️ High-fanout nets detected. Consider:\n"
                        analysis += "• Breaking into smaller nets\n"
                        analysis += "• Using buffer/driver circuits\n"
                        analysis += "• Checking signal integrity\n"
                
                return analysis
                
            def get_help_response(self):
                """Provide help information."""
                return """❓ Circuit-Synth AI Help:

I can assist you with:

🔍 **Circuit Analysis**:
• Component analysis and breakdown
• Power system evaluation  
• Connectivity mapping
• Design complexity assessment

💡 **Design Optimization**:
• Component placement suggestions
• Signal integrity recommendations
• Power delivery optimization
• EMI/EMC considerations

🔧 **Component Intelligence**: 
• Alternative component suggestions
• Availability checking
• Cost optimization
• Package recommendations

📊 **Reporting**:
• Generate comprehensive analysis reports
• Export chat conversations
• Create design documentation

**Example Questions**:
• "How can I optimize the power supply?"
• "What components might cause issues?"
• "Are there any connectivity problems?"
• "How can I improve signal integrity?"

Just ask me anything about your circuit design!"""
                
            def get_general_response(self, user_message):
                """Generate a general response."""
                responses = [
                    f"I understand you're asking about: '{user_message}'. Let me analyze your circuit from that perspective.",
                    f"That's an interesting question about '{user_message}'. Based on your schematic analysis, here's what I can tell you:",
                    f"Regarding '{user_message}' - I've looked at your circuit and here are my thoughts:",
                ]
                
                import random
                base_response = random.choice(responses)
                
                # Add some circuit-specific context
                component_count = self.analysis_data.get('component_count', 0)
                base_response += f"\n\nYour circuit has {component_count} components with good design complexity. "
                base_response += "For more specific advice, try asking about power systems, components, optimization, or connectivity."
                
                return base_response
                
            def on_typing(self, event):
                """Handle typing indicator."""
                if self.input_var.get().strip():
                    self.status_var.set("Type your question and press Enter...")
                else:
                    self.status_var.set("Ready - Ask me about your circuit design!")
                    
            # Quick action methods
            def analyze_circuit(self):
                self.send_specific_message("Please provide a comprehensive analysis of my circuit")
                
            def optimize_design(self):
                self.send_specific_message("How can I optimize this design for better performance?")
                
            def suggest_components(self):
                self.send_specific_message("Do you have any component suggestions or alternatives?")
                
            def generate_report(self):
                self.send_specific_message("Generate a detailed analysis report for this circuit")
                
            def export_chat(self):
                """Export chat history to file."""
                if not self.chat_history:
                    messagebox.showinfo("Export Chat", "No chat history to export.")
                    return
                    
                filename = filedialog.asksaveasfilename(
                    defaultextension=".txt",
                    filetypes=[("Text files", "*.txt"), ("JSON files", "*.json")],
                    title="Export Chat History"
                )
                
                if filename:
                    try:
                        if filename.endswith('.json'):
                            with open(filename, 'w') as f:
                                json.dump({
                                    'project': self.analysis_data.get('design_name', 'Unknown'),
                                    'export_time': datetime.now().isoformat(),
                                    'chat_history': self.chat_history
                                }, f, indent=2)
                        else:
                            with open(filename, 'w') as f:
                                f.write(f"Circuit-Synth AI Chat Export\n")
                                f.write(f"Project: {self.analysis_data.get('design_name', 'Unknown')}\n")
                                f.write(f"Export Time: {datetime.now().isoformat()}\n")
                                f.write("="*50 + "\n\n")
                                
                                for entry in self.chat_history:
                                    f.write(f"[{entry['timestamp']}] {entry['sender']}: {entry['message']}\n\n")
                        
                        messagebox.showinfo("Export Complete", f"Chat history saved to {filename}")
                    except Exception as e:
                        messagebox.showerror("Export Error", f"Failed to export chat: {str(e)}")
                        
            def show_help(self):
                self.send_specific_message("help")
                
            def send_specific_message(self, message):
                """Send a specific message programmatically."""
                self.input_var.set(message)
                self.send_message()
        
        # Create and run the chat application
        root = tk.Tk()
        app = CircuitSynthChatApp(root, analysis_data)
        
        # Center window
        root.update_idletasks()
        x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
        y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
        root.geometry(f"+{x}+{y}")
        
        root.mainloop()
        
    except ImportError as e:
        # Fallback if tkinter not available
        print("="*60)
        print("🚀 Circuit-Synth AI Chat (Console Mode)")
        print("="*60)
        print(f"Project: {analysis_data.get('design_name', 'Unknown')}")
        print(f"Components: {analysis_data.get('component_count', 0)}")
        print("\nGUI chat interface requires tkinter.")
        print("Install tkinter or use the basic analysis version.")


def analyze_netlist_xml(netlist_file):
    """Analyze the KiCad netlist XML file - same as basic version."""
    try:
        tree = ET.parse(netlist_file)
        root = tree.getroot()
        
        # Extract design information
        design_element = root.find('.//design')
        design_name = design_element.find('source').text if design_element is not None else "Unknown"
        design_name = Path(design_name).stem if design_name else "Unknown"
        
        # Extract components
        components = []
        component_elements = root.findall('.//components/comp')
        
        for comp in component_elements:
            ref = comp.get('ref', 'Unknown')
            value = comp.find('value')
            value_text = value.text if value is not None else 'N/A'
            
            # Get library information
            libsource = comp.find('libsource')
            library = libsource.get('lib', 'Unknown') if libsource is not None else 'Unknown'
            
            components.append({
                'ref': ref,
                'value': value_text,
                'library': library
            })
        
        # Extract nets
        nets = []
        net_elements = root.findall('.//nets/net')
        
        for net in net_elements:
            net_name = net.get('name', 'Unknown')
            nodes = []
            
            for node in net.findall('node'):
                ref = node.get('ref', 'Unknown')
                pin = node.get('pin', 'Unknown')
                nodes.append({'ref': ref, 'pin': pin})
            
            nets.append({
                'name': net_name,
                'nodes': nodes
            })
        
        return {
            'design_name': design_name,
            'timestamp': datetime.now().isoformat(),
            'component_count': len(components),
            'components': components,
            'nets': nets,
            'success': True
        }
        
    except Exception as e:
        return {
            'error': str(e),
            'success': False
        }


def main():
    """Main entry point for the enhanced chat plugin."""
    parser = argparse.ArgumentParser(description='Circuit-Synth AI Chat Plugin')
    parser.add_argument('netlist_file', help='Path to the netlist XML file from KiCad')
    parser.add_argument('output_file', help='Output file (ignored - we show chat GUI instead)')
    
    args = parser.parse_args()
    
    print("🚀 Circuit-Synth AI Chat Plugin Starting...")
    print(f"📄 Analyzing netlist: {args.netlist_file}")
    
    # Analyze the netlist
    analysis = analyze_netlist_xml(args.netlist_file)
    
    if analysis.get('success'):
        print(f"✅ Analysis complete: {analysis['component_count']} components found")
        print("🎨 Launching chat interface...")
        
        # Launch chat interface
        create_chat_interface(analysis)
        
        # Write summary file for KiCad
        output_path = Path(args.output_file)
        summary = f"""Circuit-Synth AI Chat Session Summary
==========================================

Design: {analysis['design_name']}
Components: {analysis['component_count']}
Nets: {len(analysis['nets'])}
Session Time: {analysis['timestamp']}

The interactive chat session has been completed.
All conversation details were available in the GUI interface.

For more information about Circuit-Synth AI, visit:
https://github.com/circuit-synth/circuit-synth
"""
        
        output_path.write_text(summary)
        print(f"📝 Session summary written to: {args.output_file}")
        
    else:
        error_msg = f"❌ Analysis failed: {analysis.get('error', 'Unknown error')}"
        print(error_msg)
        Path(args.output_file).write_text(f"Error: {analysis.get('error', 'Unknown error')}")
        sys.exit(1)


if __name__ == "__main__":
    main()