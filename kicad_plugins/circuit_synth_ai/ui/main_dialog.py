"""
Main dialog for Circuit-Synth AI Plugin
"""

import wx
import pcbnew
from typing import Optional


class CircuitSynthDialog(wx.Dialog):
    """
    Main dialog window for Circuit-Synth AI plugin.
    
    Provides a chat-like interface for AI-powered circuit design assistance.
    """
    
    def __init__(self, parent: wx.Window, board: pcbnew.BOARD):
        super().__init__(
            parent, 
            title="Circuit-Synth AI Assistant", 
            size=(600, 500),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        
        self.board = board
        self.init_ui()
        self.Center()
    
    def init_ui(self):
        """Initialize the user interface."""
        # Main sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Header
        header = wx.StaticText(self, label="Circuit-Synth AI Assistant")
        header_font = header.GetFont()
        header_font.SetPointSize(14)
        header_font.SetWeight(wx.FONTWEIGHT_BOLD)
        header.SetFont(header_font)
        main_sizer.Add(header, 0, wx.ALL | wx.CENTER, 10)
        
        # Chat area
        self.chat_area = wx.TextCtrl(
            self, 
            style=wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_WORDWRAP
        )
        self.chat_area.SetFont(wx.Font(10, wx.FONTFAMILY_TELETYPE, wx.FONTSTYLE_NORMAL, wx.FONTWEIGHT_NORMAL))
        main_sizer.Add(self.chat_area, 1, wx.EXPAND | wx.ALL, 5)
        
        # Input area
        input_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        self.input_text = wx.TextCtrl(
            self, 
            style=wx.TE_PROCESS_ENTER,
            hint="Ask about circuit design, components, or layouts..."
        )
        input_sizer.Add(self.input_text, 1, wx.EXPAND | wx.ALL, 2)
        
        send_button = wx.Button(self, label="Send")
        input_sizer.Add(send_button, 0, wx.ALL, 2)
        
        main_sizer.Add(input_sizer, 0, wx.EXPAND | wx.ALL, 5)
        
        # Action buttons
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        generate_btn = wx.Button(self, label="Generate Circuit")
        analyze_btn = wx.Button(self, label="Analyze Board")
        optimize_btn = wx.Button(self, label="Optimize Layout")
        
        button_sizer.Add(generate_btn, 0, wx.ALL, 2)
        button_sizer.Add(analyze_btn, 0, wx.ALL, 2)
        button_sizer.Add(optimize_btn, 0, wx.ALL, 2)
        
        main_sizer.Add(button_sizer, 0, wx.CENTER | wx.ALL, 5)
        
        # Status bar
        self.status_text = wx.StaticText(self, label="Ready - Connected to KiCad PCB Editor")
        status_font = self.status_text.GetFont()
        status_font.SetPointSize(8)
        self.status_text.SetFont(status_font)
        main_sizer.Add(self.status_text, 0, wx.EXPAND | wx.ALL, 5)
        
        self.SetSizer(main_sizer)
        
        # Bind events
        self.input_text.Bind(wx.EVT_TEXT_ENTER, self.on_send_message)
        send_button.Bind(wx.EVT_BUTTON, self.on_send_message)
        generate_btn.Bind(wx.EVT_BUTTON, self.on_generate_circuit)
        analyze_btn.Bind(wx.EVT_BUTTON, self.on_analyze_board)
        optimize_btn.Bind(wx.EVT_BUTTON, self.on_optimize_layout)
        
        # Welcome message
        self.add_message("Circuit-Synth AI", "Welcome! I'm your AI circuit design assistant.")
        self.add_message("System", f"Connected to KiCad board: {self.board.GetFileName()}")
        self.add_message("System", "Ask me about circuit design, component selection, or layout optimization!")
    
    def add_message(self, sender: str, message: str):
        """Add a message to the chat area."""
        current_text = self.chat_area.GetValue()
        if current_text:
            current_text += "\n"
        
        new_message = f"[{sender}]: {message}\n"
        self.chat_area.SetValue(current_text + new_message)
        
        # Scroll to bottom
        self.chat_area.SetInsertionPointEnd()
    
    def on_send_message(self, event):
        """Handle sending a message."""
        message = self.input_text.GetValue().strip()
        if not message:
            return
            
        # Add user message
        self.add_message("You", message)
        self.input_text.Clear()
        
        # Process the message (placeholder for AI integration)
        self.process_user_message(message)
    
    def process_user_message(self, message: str):
        """Process user message and generate AI response."""
        # This is where we would integrate with AI/LLM
        # For now, provide some basic responses
        
        message_lower = message.lower()
        
        if "hello" in message_lower or "hi" in message_lower:
            response = "Hello! How can I help you with your circuit design today?"
        elif "component" in message_lower:
            response = "I can help you select components! What type of component are you looking for? (resistors, capacitors, ICs, etc.)"
        elif "layout" in message_lower:
            response = "For layout optimization, I can analyze trace routing, component placement, and thermal considerations. What specific layout issue are you facing?"
        elif "circuit" in message_lower:
            response = "I can help generate circuit designs! Describe what kind of circuit you need and I'll provide suggestions."
        else:
            response = f"I understand you're asking about: '{message}'. While I'm still learning, I can help with component selection, circuit generation, and layout optimization. Try asking more specific questions!"
            
        self.add_message("Circuit-Synth AI", response)
    
    def on_generate_circuit(self, event):
        """Handle generate circuit button."""
        self.add_message("System", "Circuit generation feature coming soon! This will integrate with circuit-synth to generate Python-based circuit designs.")
    
    def on_analyze_board(self, event):
        """Handle analyze board button."""
        # Get basic board info
        components = self.board.GetFootprints()
        tracks = self.board.GetTracks()
        
        analysis = f"Board Analysis:\n"
        analysis += f"• Components: {len(list(components))}\n"
        analysis += f"• Tracks: {len(list(tracks))}\n"
        analysis += f"• Board size: {self.board.GetBoundingBox().GetWidth()/1000000:.1f} x {self.board.GetBoundingBox().GetHeight()/1000000:.1f} mm"
        
        self.add_message("Analyzer", analysis)
    
    def on_optimize_layout(self, event):
        """Handle optimize layout button."""
        self.add_message("System", "Layout optimization feature coming soon! This will provide intelligent suggestions for component placement and routing.")