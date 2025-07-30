"""
Circuit-Synth AI Plugin for KiCad Schematic Editor

Provides AI-powered circuit design assistance in the schematic editor.
"""

try:
    import eeschema
    import pcbnew
    import os
    import wx
    from pathlib import Path
    
    from .ui.schematic_dialog import CircuitSynthSchematicDialog

    class CircuitSynthSchematicAI(eeschema.ActionPlugin):
        """
        Circuit-Synth AI Plugin for KiCad Schematic Editor.
        
        Provides AI-powered circuit design assistance with integration
        to the circuit-synth framework for schematic design.
        """

        def defaults(self):
            """Set up plugin defaults."""
            self.name = "Circuit-Synth AI (Schematic)"
            self.category = "Circuit Design"
            self.description = "AI-powered schematic design assistance"
            self.show_toolbar_button = True
            
            # Set up icon path
            icon_path = Path(__file__).parent / "resources" / "icon.png"
            self.icon_file_name = str(icon_path)
            self.dark_icon_file_name = str(icon_path)
            
            # Dialog reference
            self.dialog_window = None

        def Run(self):
            """Execute the plugin."""
            try:
                # Get the current schematic
                schematic = eeschema.GetSchematic()
                if schematic is None:
                    wx.MessageBox(
                        "No schematic found. Please open a schematic file first.",
                        "Circuit-Synth AI",
                        wx.OK | wx.ICON_WARNING
                    )
                    return

                # Get the main KiCad frame
                app = wx.GetApp()
                if app is None:
                    return
                    
                top_windows = wx.GetTopLevelWindows()
                frame = None
                
                for window in top_windows:
                    if isinstance(window, wx.Frame):
                        frame = window
                        break

                if frame is None:
                    return

                # Create or show the dialog
                if self.dialog_window is None or not isinstance(self.dialog_window, CircuitSynthSchematicDialog):
                    self.dialog_window = CircuitSynthSchematicDialog(frame, schematic)
                    self.dialog_window.Bind(wx.EVT_CLOSE, self.on_close_dialog)

                # Show the dialog
                if self.dialog_window.IsIconized():
                    self.dialog_window.Iconize(False)
                    
                self.dialog_window.Raise()
                self.dialog_window.Show()

            except Exception as e:
                wx.MessageBox(
                    f"Error launching Circuit-Synth AI plugin: {str(e)}",
                    "Plugin Error",
                    wx.OK | wx.ICON_ERROR
                )

        def on_close_dialog(self, event):
            """Handle dialog close event."""
            self.dialog_window = None
            event.Skip()

except ImportError:
    # eeschema module might not be available in all KiCad versions
    class CircuitSynthSchematicAI:
        def __init__(self):
            pass
        def register(self):
            pass