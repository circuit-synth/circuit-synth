"""
Enhanced Chat Dialog with Claude Code Integration

This module provides a comprehensive chat interface for KiCad PCB editor
that bridges directly to Claude Code for real AI assistance.
"""

import wx
import wx.richtext
import pcbnew
import threading
import json
from typing import Optional, List, Dict, Any
from datetime import datetime
import logging
from pathlib import Path

# Import our Claude Bridge
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from claude_bridge import ClaudeBridge, KiCadDataExtractor, get_claude_bridge

logger = logging.getLogger(__name__)


class ClaudeChatDialog(wx.Dialog):
    """
    Enhanced chat dialog with Claude Code integration for PCB editor.
    
    Features:
    - Real-time AI chat with Claude Code
    - Circuit context awareness
    - Conversation history
    - Export capabilities
    - Quick action buttons
    - Professional UI with rich text
    """
    
    def __init__(self, parent: wx.Window, board: pcbnew.BOARD):
        super().__init__(
            parent,
            title="🚀 Circuit-Synth AI - Claude Chat Assistant",
            size=(800, 700),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER | wx.MAXIMIZE_BOX
        )
        
        self.board = board
        self.claude_bridge = get_claude_bridge()
        self.conversation_history: List[Dict] = []
        self.is_claude_available = False
        
        # Initialize UI
        self.init_ui()
        self.center_on_parent()
        
        # Try to connect to Claude
        self.connect_to_claude()
        
        # Extract and set circuit context
        self.update_circuit_context()
    
    def init_ui(self):
        """Initialize the user interface."""
        # Main sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Header section
        self.create_header(main_sizer)
        
        # Chat display area
        self.create_chat_area(main_sizer)
        
        # Input section
        self.create_input_section(main_sizer)
        
        # Quick actions
        self.create_quick_actions(main_sizer)
        
        # Status and control section
        self.create_status_section(main_sizer)
        
        self.SetSizer(main_sizer)
        
        # Set initial focus
        self.input_text.SetFocus()
    
    def create_header(self, parent_sizer):
        """Create the header section."""
        header_panel = wx.Panel(self)
        header_panel.SetBackgroundColour(wx.Colour(240, 240, 250))
        header_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Title and subtitle
        title_sizer = wx.BoxSizer(wx.VERTICAL)
        
        title = wx.StaticText(header_panel, label="🚀 Circuit-Synth AI - Claude Assistant")
        title_font = title.GetFont()
        title_font.SetPointSize(16)
        title_font.SetWeight(wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        title_sizer.Add(title, 0, wx.ALL, 5)
        
        subtitle = wx.StaticText(header_panel, label="Real-time AI assistance powered by Claude Code")
        subtitle_font = subtitle.GetFont()
        subtitle_font.SetPointSize(10)
        subtitle.SetFont(subtitle_font)
        subtitle.SetForegroundColour(wx.Colour(100, 100, 100))
        title_sizer.Add(subtitle, 0, wx.LEFT, 5)
        
        header_sizer.Add(title_sizer, 1, wx.EXPAND | wx.ALL, 10)
        
        # Connection status
        self.connection_status = wx.StaticText(header_panel, label="🔴 Not Connected")
        status_font = self.connection_status.GetFont()
        status_font.SetPointSize(12)
        status_font.SetWeight(wx.FONTWEIGHT_BOLD)
        self.connection_status.SetFont(status_font)
        header_sizer.Add(self.connection_status, 0, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 10)
        
        header_panel.SetSizer(header_sizer)
        parent_sizer.Add(header_panel, 0, wx.EXPAND | wx.ALL, 5)
    
    def create_chat_area(self, parent_sizer):
        """Create the main chat display area."""
        # Chat area with rich text support
        self.chat_area = wx.richtext.RichTextCtrl(
            self,
            style=wx.richtext.RE_MULTILINE | wx.richtext.RE_READONLY
        )
        
        # Set up text styles
        self.setup_text_styles()
        
        parent_sizer.Add(self.chat_area, 1, wx.EXPAND | wx.ALL, 5)
    
    def setup_text_styles(self):
        """Set up rich text styles for the chat area."""
        # Check if style sheet exists, create if needed
        style_sheet = self.chat_area.GetStyleSheet()
        if style_sheet is None:
            # Create a new style sheet
            style_sheet = wx.richtext.RichTextStyleSheet()
            self.chat_area.SetStyleSheet(style_sheet)
        
        # User style - create proper RichTextCharacterStyleDefinition
        user_style_def = wx.richtext.RichTextCharacterStyleDefinition("user")
        user_style = wx.richtext.RichTextAttr()
        user_style.SetBackgroundColour(wx.Colour(230, 245, 255))
        user_style.SetTextColour(wx.Colour(0, 80, 150))
        user_style.SetFontWeight(wx.FONTWEIGHT_BOLD)
        user_style_def.SetStyle(user_style)
        style_sheet.AddCharacterStyle(user_style_def)
        
        # Claude style
        claude_style_def = wx.richtext.RichTextCharacterStyleDefinition("claude")
        claude_style = wx.richtext.RichTextAttr()
        claude_style.SetBackgroundColour(wx.Colour(240, 255, 240))
        claude_style.SetTextColour(wx.Colour(0, 120, 0))
        claude_style.SetFontWeight(wx.FONTWEIGHT_NORMAL)
        claude_style_def.SetStyle(claude_style)
        style_sheet.AddCharacterStyle(claude_style_def)
        
        # System style
        system_style_def = wx.richtext.RichTextCharacterStyleDefinition("system")
        system_style = wx.richtext.RichTextAttr()
        system_style.SetTextColour(wx.Colour(120, 120, 120))
        system_style.SetFontStyle(wx.FONTSTYLE_ITALIC)
        system_style_def.SetStyle(system_style)
        style_sheet.AddCharacterStyle(system_style_def)
    
    def create_input_section(self, parent_sizer):
        """Create the message input section."""
        input_panel = wx.Panel(self)
        input_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Input label
        input_label = wx.StaticText(input_panel, label="Ask Claude about your circuit design:")
        input_sizer.Add(input_label, 0, wx.ALL, 5)
        
        # Input area
        input_row = wx.BoxSizer(wx.HORIZONTAL)
        
        self.input_text = wx.TextCtrl(
            input_panel,
            style=wx.TE_MULTILINE | wx.TE_PROCESS_ENTER,
            size=(-1, 60)
        )
        self.input_text.SetHint("Type your question here... Press Ctrl+Enter to send")
        input_row.Add(self.input_text, 1, wx.EXPAND | wx.ALL, 2)
        
        # Send button
        self.send_button = wx.Button(input_panel, label="Send\n(Ctrl+Enter)")
        self.send_button.SetMinSize((100, 60))
        input_row.Add(self.send_button, 0, wx.ALL, 2)
        
        input_sizer.Add(input_row, 0, wx.EXPAND | wx.ALL, 5)
        
        input_panel.SetSizer(input_sizer)
        parent_sizer.Add(input_panel, 0, wx.EXPAND | wx.ALL, 5)
        
        # Bind events
        self.input_text.Bind(wx.EVT_KEY_DOWN, self.on_input_key)
        self.send_button.Bind(wx.EVT_BUTTON, self.on_send_message)
    
    def create_quick_actions(self, parent_sizer):
        """Create quick action buttons."""
        actions_panel = wx.Panel(self)
        actions_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Action buttons
        actions = [
            ("🔍 Analyze PCB", self.on_analyze_pcb),
            ("🔧 Component Help", self.on_component_help),
            ("📐 Layout Review", self.on_layout_review),
            ("⚡ Optimization", self.on_optimization_help),
            ("🐛 Debug Issues", self.on_debug_help),
            ("💾 Export Chat", self.on_export_chat)
        ]
        
        for label, handler in actions:
            btn = wx.Button(actions_panel, label=label)
            btn.Bind(wx.EVT_BUTTON, handler)
            actions_sizer.Add(btn, 0, wx.ALL, 3)
        
        actions_panel.SetSizer(actions_sizer)
        parent_sizer.Add(actions_panel, 0, wx.CENTER | wx.ALL, 5)
    
    def create_status_section(self, parent_sizer):
        """Create the status and control section."""
        status_panel = wx.Panel(self)
        status_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Status text
        self.status_text = wx.StaticText(status_panel, label="Ready")
        status_sizer.Add(self.status_text, 1, wx.ALL | wx.ALIGN_CENTER_VERTICAL, 5)
        
        # Control buttons
        refresh_btn = wx.Button(status_panel, label="🔄 Refresh Context")
        connect_btn = wx.Button(status_panel, label="🔌 Reconnect Claude")
        
        refresh_btn.Bind(wx.EVT_BUTTON, self.on_refresh_context)
        connect_btn.Bind(wx.EVT_BUTTON, self.on_reconnect_claude)
        
        status_sizer.Add(refresh_btn, 0, wx.ALL, 2)
        status_sizer.Add(connect_btn, 0, wx.ALL, 2)
        
        status_panel.SetSizer(status_sizer)
        parent_sizer.Add(status_panel, 0, wx.EXPAND | wx.ALL, 5)
    
    def connect_to_claude(self):
        """Connect to Claude Code in a separate thread."""
        def connect():
            self.set_status("Connecting to Claude Code...")
            success = self.claude_bridge.connect()
            
            wx.CallAfter(self.on_claude_connection_result, success)
        
        threading.Thread(target=connect, daemon=True).start()
    
    def on_claude_connection_result(self, success: bool):
        """Handle Claude connection result."""
        if success:
            self.is_claude_available = True
            self.connection_status.SetLabel("🟢 Claude Connected")
            self.connection_status.SetForegroundColour(wx.Colour(0, 150, 0))
            self.set_status("Connected to Claude Code - Ready for AI assistance!")
            self.add_system_message("✅ Successfully connected to Claude Code")
            self.add_claude_message("Hello! I'm Claude, your AI circuit design assistant. I can help you with:\n\n• PCB layout analysis and optimization\n• Component selection and placement\n• Routing strategies and best practices\n• Design rule checking and validation\n• Troubleshooting and debugging\n\nWhat would you like to know about your current PCB design?")
        else:
            self.is_claude_available = False
            self.connection_status.SetLabel("🔴 Claude Unavailable")
            self.connection_status.SetForegroundColour(wx.Colour(200, 0, 0))
            self.set_status("Claude Code not available - Install Claude CLI for AI assistance")
            self.add_system_message("❌ Could not connect to Claude Code. Please install the Claude CLI tool for AI assistance.")
        
        self.Layout()
    
    def update_circuit_context(self):
        """Update the circuit context for Claude."""
        try:
            circuit_data = KiCadDataExtractor.extract_pcb_data(self.board)
            self.claude_bridge.set_circuit_context(circuit_data)
            
            # Show circuit summary
            summary = f"📋 PCB Context Updated: {circuit_data.project_name}\n"
            summary += f"• Components: {len(circuit_data.components)}\n"
            summary += f"• Tracks: {len(circuit_data.tracks)}\n"
            if circuit_data.board_info:
                summary += f"• Board Size: {circuit_data.board_info.get('width_mm', 0):.1f} x {circuit_data.board_info.get('height_mm', 0):.1f} mm"
            
            self.add_system_message(summary)
            
        except Exception as e:
            logger.error(f"Error updating circuit context: {e}")
            self.add_system_message(f"⚠️ Error updating circuit context: {str(e)}")
    
    def add_message(self, sender: str, message: str, style: str = "normal"):
        """Add a message to the chat area."""
        timestamp = datetime.now().strftime("%H:%M:%S")
        
        # Add to conversation history
        self.conversation_history.append({
            'timestamp': timestamp,
            'sender': sender,
            'message': message
        })
        
        # Add to chat display
        self.chat_area.BeginSuppressUndo()
        
        # Add sender header
        if sender == "You":
            self.chat_area.BeginStyle(self.chat_area.GetStyleSheet().FindCharacterStyle("user"))
            self.chat_area.WriteText(f"[{timestamp}] 👤 You:\n")
            self.chat_area.EndStyle()
        elif sender == "Claude":
            self.chat_area.BeginStyle(self.chat_area.GetStyleSheet().FindCharacterStyle("claude"))
            self.chat_area.WriteText(f"[{timestamp}] 🤖 Claude:\n")
            self.chat_area.EndStyle()
        else:
            self.chat_area.BeginStyle(self.chat_area.GetStyleSheet().FindCharacterStyle("system"))
            self.chat_area.WriteText(f"[{timestamp}] 📋 {sender}:\n")
            self.chat_area.EndStyle()
        
        # Add message content
        self.chat_area.WriteText(f"{message}\n\n")
        
        self.chat_area.EndSuppressUndo()
        
        # Scroll to bottom
        self.chat_area.ShowPosition(self.chat_area.GetLastPosition())
    
    def add_system_message(self, message: str):
        """Add a system message."""
        self.add_message("System", message, "system")
    
    def add_claude_message(self, message: str):
        """Add a Claude message."""
        self.add_message("Claude", message, "claude")
    
    def set_status(self, status: str):
        """Update the status text."""
        wx.CallAfter(lambda: self.status_text.SetLabel(status))
    
    def on_input_key(self, event):
        """Handle input key events."""
        if event.GetKeyCode() == wx.WXK_RETURN and event.ControlDown():
            self.on_send_message(None)
        else:
            event.Skip()
    
    def on_send_message(self, event):
        """Handle sending a message to Claude."""
        message = self.input_text.GetValue().strip()
        if not message:
            return
        
        if not self.is_claude_available:
            self.add_system_message("❌ Claude is not available. Please check your Claude CLI installation.")
            return
        
        # Clear input and add user message
        self.input_text.Clear()
        self.add_message("You", message)
        
        # Send to Claude in background
        def send_to_claude():
            self.set_status("🤖 Claude is thinking...")
            
            try:
                # Get current circuit context
                circuit_data = KiCadDataExtractor.extract_pcb_data(self.board)
                
                # Send to Claude
                response = self.claude_bridge.send_message(message, circuit_data)
                
                # Update UI
                wx.CallAfter(self.add_claude_message, response)
                wx.CallAfter(self.set_status, "Ready")
                
            except Exception as e:
                error_msg = f"❌ Error communicating with Claude: {str(e)}"
                wx.CallAfter(self.add_system_message, error_msg)
                wx.CallAfter(self.set_status, "Error occurred")
        
        threading.Thread(target=send_to_claude, daemon=True).start()
    
    def on_analyze_pcb(self, event):
        """Analyze the current PCB."""
        self.input_text.SetValue("Please analyze my current PCB design. Look at component placement, routing, and provide optimization suggestions.")
        self.on_send_message(None)
    
    def on_component_help(self, event):
        """Get component help."""
        self.input_text.SetValue("Help me understand the components in my design. Are there any missing decoupling capacitors or other issues?")
        self.on_send_message(None)
    
    def on_layout_review(self, event):
        """Request layout review."""
        self.input_text.SetValue("Review my PCB layout for best practices. Check trace routing, component spacing, and thermal considerations.")
        self.on_send_message(None)
    
    def on_optimization_help(self, event):
        """Get optimization suggestions."""
        self.input_text.SetValue("What optimizations can I make to improve this PCB design? Consider signal integrity, EMI, and manufacturability.")
        self.on_send_message(None)
    
    def on_debug_help(self, event):
        """Get debugging help."""
        self.input_text.SetValue("Help me identify potential issues with this PCB design that could cause problems during testing or operation.")
        self.on_send_message(None)
    
    def on_export_chat(self, event):
        """Export the chat conversation."""
        with wx.FileDialog(
            self,
            "Export Chat Conversation",
            wildcard="Text files (*.txt)|*.txt|Markdown files (*.md)|*.md",
            style=wx.FD_SAVE | wx.FD_OVERWRITE_PROMPT
        ) as file_dialog:
            
            if file_dialog.ShowModal() == wx.ID_CANCEL:
                return
            
            file_path = file_dialog.GetPath()
            
            try:
                success = self.claude_bridge.export_conversation(file_path)
                if success:
                    self.add_system_message(f"✅ Conversation exported to: {file_path}")
                else:
                    self.add_system_message("❌ Failed to export conversation")
            except Exception as e:
                self.add_system_message(f"❌ Export error: {str(e)}")
    
    def on_refresh_context(self, event):
        """Refresh the circuit context."""
        self.update_circuit_context()
        self.add_system_message("🔄 Circuit context refreshed")
    
    def on_reconnect_claude(self, event):
        """Reconnect to Claude."""
        self.connect_to_claude()
    
    def center_on_parent(self):
        """Center the dialog on the parent window."""
        parent = self.GetParent()
        if parent:
            parent_pos = parent.GetPosition()
            parent_size = parent.GetSize()
            size = self.GetSize()
            
            x = parent_pos.x + (parent_size.width - size.width) // 2
            y = parent_pos.y + (parent_size.height - size.height) // 2
            
            self.SetPosition((x, y))