#!/usr/bin/env python3
"""
Circuit-Synth AI Plugin for KiCad 9
Main entry point using the new KiCad 9 IPC API architecture.
"""

import sys
import os
import json
import logging
from pathlib import Path

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)

def setup_plugin_environment():
    """Set up the plugin environment and dependencies."""
    try:
        # Add plugin directory to Python path
        plugin_dir = Path(__file__).parent
        if str(plugin_dir) not in sys.path:
            sys.path.insert(0, str(plugin_dir))
        
        logger.info(f"Plugin directory: {plugin_dir}")
        return True
    except Exception as e:
        logger.error(f"Failed to setup plugin environment: {e}")
        return False

def check_dependencies():
    """Check if required dependencies are available."""
    missing_deps = []
    
    # Check for wx (GUI framework)
    try:
        import wx
        logger.info(f"wxPython version: {wx.version()}")
    except ImportError:
        missing_deps.append("wxPython")
    
    # Check for kicad-python (if available)
    try:
        import kicad
        logger.info("kicad-python library available")
    except ImportError:
        logger.info("kicad-python library not available (using IPC API)")
    
    if missing_deps:
        logger.warning(f"Missing dependencies: {missing_deps}")
        return False
    
    return True

def show_simple_dialog():
    """Show a simple test dialog to verify the plugin works."""
    try:
        import wx
        
        app = wx.App()
        
        with wx.MessageDialog(
            None, 
            "Circuit-Synth AI Plugin is working!\n\nThis is a test dialog to verify the plugin installation.",
            "Circuit-Synth AI - Test",
            wx.OK | wx.ICON_INFORMATION
        ) as dialog:
            result = dialog.ShowModal()
        
        app.MainLoop()
        logger.info("Simple dialog test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error showing simple dialog: {e}")
        return False

def show_main_interface():
    """Show the main Circuit-Synth AI interface."""
    try:
        from ui.main_dialog import CircuitSynthDialog
        import wx
        
        app = wx.App()
        
        # Create a basic parent frame
        parent = wx.Frame(None, title="KiCad")
        
        # For now, use a mock board object since we're testing
        class MockBoard:
            def GetFileName(self):
                return "test_board.kicad_pcb"
            def GetFootprints(self):
                return []
            def GetTracks(self):
                return []
            def GetBoundingBox(self):
                class MockBox:
                    def GetWidth(self): return 100000000  # 100mm in nm
                    def GetHeight(self): return 80000000  # 80mm in nm
                return MockBox()
        
        mock_board = MockBoard()
        
        # Create and show the main dialog
        dialog = CircuitSynthDialog(parent, mock_board)
        dialog.ShowModal()
        
        app.MainLoop()
        logger.info("Main interface test completed successfully")
        return True
        
    except Exception as e:
        logger.error(f"Error showing main interface: {e}")
        return False

def main():
    """Main entry point for the plugin."""
    logger.info("Starting Circuit-Synth AI Plugin for KiCad 9")
    
    # Setup environment
    if not setup_plugin_environment():
        logger.error("Failed to setup plugin environment")
        sys.exit(1)
    
    # Check dependencies
    if not check_dependencies():
        logger.error("Missing required dependencies")
        # Show simple dialog even if dependencies are missing for testing
        try:
            show_simple_dialog()
        except:
            pass
        sys.exit(1)
    
    # Parse command line arguments
    if len(sys.argv) > 1:
        action = sys.argv[1]
        logger.info(f"Running action: {action}")
        
        if action == "test":
            success = show_simple_dialog()
        elif action == "main":
            success = show_main_interface()
        else:
            logger.error(f"Unknown action: {action}")
            success = False
        
        sys.exit(0 if success else 1)
    else:
        # Default action - show main interface
        logger.info("No action specified, showing main interface")
        success = show_main_interface()
        sys.exit(0 if success else 1)

if __name__ == "__main__":
    main()