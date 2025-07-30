"""
Circuit-Synth AI Plugin for KiCad Schematic Editor

A KiCad plugin that provides AI-powered schematic design assistance.
"""

try:
    # Try importing eeschema for schematic editor
    import eeschema
    import os
    import sys
    import wx
    from pathlib import Path

    class CircuitSynthSchematicAI(eeschema.ActionPlugin):
        """
        Circuit-Synth AI Plugin for KiCad Schematic Editor.
        """

        def defaults(self):
            """Set up plugin defaults - this is required by KiCad."""
            self.name = "Circuit-Synth AI (Schematic)"
            self.category = "Circuit Design" 
            self.description = "AI-powered schematic design assistance"
            self.show_toolbar_button = True
            
            # Set up icon path
            self.icon_file_name = os.path.join(os.path.dirname(__file__), "icon.png")
            self.dark_icon_file_name = self.icon_file_name

        def Run(self):
            """Execute the plugin - this is called when user clicks the plugin."""
            try:
                # Try to get the current schematic
                schematic = eeschema.GetSchematic()
                if schematic is None:
                    wx.MessageBox(
                        "No schematic found. Please open a schematic file first.",
                        "Circuit-Synth AI (Schematic)",
                        wx.OK | wx.ICON_WARNING
                    )
                    return

                # Analyze schematic
                message = f"""Circuit-Synth AI Schematic Plugin Working! ✅

📐 Schematic Analysis:
• Plugin successfully loaded in Eeschema
• Schematic access: Available
• Ready for AI-powered schematic design assistance!

This confirms the schematic plugin is working."""

                wx.MessageBox(
                    message,
                    "Circuit-Synth AI - Schematic Success!",
                    wx.OK | wx.ICON_INFORMATION
                )

            except Exception as e:
                wx.MessageBox(
                    f"Error in Circuit-Synth AI schematic plugin: {str(e)}",
                    "Schematic Plugin Error", 
                    wx.OK | wx.ICON_ERROR
                )

    # Register the plugin
    CircuitSynthSchematicAI().register()

except ImportError as e:
    # eeschema not available - try alternative approach
    try:
        import pcbnew
        import os
        import wx

        class CircuitSynthSchematicAI(pcbnew.ActionPlugin):
            """
            Circuit-Synth AI Plugin - Alternative approach for schematic functionality.
            """

            def defaults(self):
                """Set up plugin defaults."""
                self.name = "Circuit-Synth AI (Schematic)"
                self.category = "Circuit Design" 
                self.description = "AI-powered schematic design assistance"
                self.show_toolbar_button = True
                
                # Set up icon path
                self.icon_file_name = os.path.join(os.path.dirname(__file__), "icon.png")
                self.dark_icon_file_name = self.icon_file_name

            def Run(self):
                """Execute the plugin."""
                try:
                    message = f"""Circuit-Synth AI Schematic Plugin ⚠️

📐 Schematic Plugin Status:
• Plugin loaded using pcbnew ActionPlugin framework
• Eeschema API not available in this KiCad version
• This is a fallback implementation

Note: This plugin is designed for schematic analysis but KiCad's 
schematic editor may not fully support ActionPlugins yet.

For schematic analysis, use the standalone analyzer tool or 
the enhanced PCB plugin that includes schematic analysis."""

                    wx.MessageBox(
                        message,
                        "Circuit-Synth AI - Schematic (Fallback)",
                        wx.OK | wx.ICON_INFORMATION
                    )

                except Exception as e:
                    wx.MessageBox(
                        f"Error in schematic plugin: {str(e)}",
                        "Plugin Error", 
                        wx.OK | wx.ICON_ERROR
                    )

        # Register the fallback plugin
        CircuitSynthSchematicAI().register()
        
    except ImportError:
        # Neither eeschema nor pcbnew available
        pass

except Exception as e:
    # Log any other errors
    import logging
    logging.getLogger(__name__).error(f"Circuit-Synth AI Schematic Plugin error: {e}")