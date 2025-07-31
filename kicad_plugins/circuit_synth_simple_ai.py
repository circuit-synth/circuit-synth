#!/usr/bin/env python3
"""
Simple Circuit-Synth AI Plugin for KiCad PCB Editor

A minimal, stable plugin that provides AI assistance without complex UI elements.
"""

import pcbnew
import wx
import sys
import os
from pathlib import Path

class CircuitSynthSimpleAI(pcbnew.ActionPlugin):
    """
    Simple Circuit-Synth AI Plugin for KiCad PCB Editor.
    
    Provides basic AI chat functionality without complex styling
    that might cause KiCad crashes.
    """

    def defaults(self):
        """Set up plugin defaults."""
        self.name = "Circuit-Synth AI (Simple)"
        self.category = "Circuit Design"
        self.description = "Simple AI-powered circuit design assistance"
        self.show_toolbar_button = True
        
    def Run(self):
        """Execute the plugin."""
        try:
            # Get the current board
            board = pcbnew.GetBoard()
            if board is None:
                wx.MessageBox(
                    "No PCB board found. Please open a PCB file first.",
                    "Circuit-Synth AI",
                    wx.OK | wx.ICON_WARNING
                )
                return

            # Show simple dialog
            self.show_simple_dialog(board)

        except Exception as e:
            wx.MessageBox(
                f"Error: {str(e)}",
                "Plugin Error", 
                wx.OK | wx.ICON_ERROR
            )

    def show_simple_dialog(self, board):
        """Show a simple dialog without complex styling."""
        
        # Create main dialog
        dialog = wx.Dialog(
            None,
            title="🚀 Circuit-Synth AI Assistant", 
            size=(600, 400),
            style=wx.DEFAULT_DIALOG_STYLE | wx.RESIZE_BORDER
        )
        
        # Main sizer
        main_sizer = wx.BoxSizer(wx.VERTICAL)
        
        # Title
        title = wx.StaticText(dialog, label="Circuit-Synth AI Assistant")
        title_font = title.GetFont()
        title_font.SetPointSize(14)
        title_font.SetWeight(wx.FONTWEIGHT_BOLD)
        title.SetFont(title_font)
        main_sizer.Add(title, 0, wx.ALL | wx.CENTER, 10)
        
        # Board info
        board_name = board.GetFileName() if board.GetFileName() else "Untitled"
        info_text = f"Board: {Path(board_name).name}\n"
        info_text += f"Components: {len(list(board.GetFootprints()))}\n"
        info_text += f"Tracks: {len(list(board.GetTracks()))}"
        
        info_label = wx.StaticText(dialog, label=info_text)
        main_sizer.Add(info_label, 0, wx.ALL | wx.EXPAND, 10)
        
        # Simple text area - using basic TextCtrl instead of RichTextCtrl
        text_area = wx.TextCtrl(
            dialog,
            style=wx.TE_MULTILINE | wx.TE_READONLY,
            value="Welcome to Circuit-Synth AI!\n\n" +
                  "This is a simplified version that avoids complex styling.\n\n" +
                  "Features available:\n" +
                  "• Board analysis and component information\n" +
                  "• Circuit design advice and guidance\n" +
                  "• Component selection recommendations\n\n" +
                  "To get started, click 'Analyze Board' below."
        )
        main_sizer.Add(text_area, 1, wx.ALL | wx.EXPAND, 10)
        
        # Button sizer
        button_sizer = wx.BoxSizer(wx.HORIZONTAL)
        
        # Analyze button
        analyze_btn = wx.Button(dialog, label="Analyze Board")
        analyze_btn.Bind(wx.EVT_BUTTON, lambda evt: self.analyze_board(board, text_area))
        button_sizer.Add(analyze_btn, 0, wx.ALL, 5)
        
        # Close button  
        close_btn = wx.Button(dialog, wx.ID_CLOSE, "Close")
        close_btn.Bind(wx.EVT_BUTTON, lambda evt: dialog.EndModal(wx.ID_CLOSE))
        button_sizer.Add(close_btn, 0, wx.ALL, 5)
        
        main_sizer.Add(button_sizer, 0, wx.ALL | wx.CENTER, 10)
        
        dialog.SetSizer(main_sizer)
        dialog.ShowModal()
        dialog.Destroy()
    
    def analyze_board(self, board, text_area):
        """Analyze the current board and display information."""
        try:
            # Get board information
            footprints = list(board.GetFootprints())
            tracks = list(board.GetTracks())
            
            analysis = f"📊 Board Analysis Results:\n\n"
            analysis += f"Board File: {Path(board.GetFileName()).name if board.GetFileName() else 'Untitled'}\n"
            analysis += f"Total Components: {len(footprints)}\n"
            analysis += f"Total Tracks: {len(tracks)}\n\n"
            
            # Component analysis
            if footprints:
                analysis += "🔧 Components Found:\n"
                component_types = {}
                for fp in footprints[:10]:  # Show first 10
                    ref = fp.GetReference()
                    value = fp.GetValue()
                    footprint = fp.GetFPID().GetLibItemName().GetUniString()
                    
                    # Count component types
                    prefix = ref.rstrip('0123456789')
                    component_types[prefix] = component_types.get(prefix, 0) + 1
                    
                    analysis += f"• {ref}: {value} ({footprint})\n"
                
                if len(footprints) > 10:
                    analysis += f"... and {len(footprints) - 10} more components\n"
                
                analysis += f"\n📈 Component Summary:\n"
                for comp_type, count in sorted(component_types.items()):
                    analysis += f"• {comp_type}: {count} components\n"
            else:
                analysis += "ℹ️  No components found on board\n"
            
            # Track analysis
            if tracks:
                analysis += f"\n🔗 Routing Information:\n"
                analysis += f"• Total track segments: {len(tracks)}\n"
                
                # Count different track types
                vias = sum(1 for t in tracks if t.Type() == pcbnew.PCB_VIA_T)
                track_segments = len(tracks) - vias
                analysis += f"• Track segments: {track_segments}\n"
                analysis += f"• Vias: {vias}\n"
            else:
                analysis += "\n🔗 No routing found\n"
            
            # Design recommendations
            analysis += f"\n💡 Quick Recommendations:\n"
            if len(footprints) == 0:
                analysis += "• Start by adding components to your schematic\n"
            elif len(tracks) == 0:
                analysis += "• Ready for routing - use the router tool\n"
            else:
                analysis += "• Board looks active - consider running DRC\n"
                analysis += "• Check component placement and routing\n"
            
            # Update text area
            text_area.SetValue(analysis)
            
        except Exception as e:
            text_area.SetValue(f"Analysis Error: {str(e)}")

# Register the plugin
CircuitSynthSimpleAI().register()