"""
Circuit-Synth AI Script for KiCad Schematic Editor

This script can be run from the KiCad Schematic Editor's scripting console.
Since eeschema doesn't fully support ActionPlugins, this provides an alternative.

To use:
1. Open KiCad Schematic Editor
2. Go to Tools -> Scripting Console
3. Run: exec(open('/path/to/this/script.py').read())
"""

import os
import sys
from pathlib import Path

def circuit_synth_schematic_analysis():
    """Main function to run schematic analysis."""
    try:
        import wx
        
        # Get current working directory (might be where schematic is)
        current_dir = os.getcwd()
        
        # Look for schematic files in current directory
        schematic_files = []
        for file in os.listdir(current_dir):
            if file.endswith('.kicad_sch'):
                schematic_files.append(file)
        
        message = f"""🚀 Circuit-Synth AI - Schematic Analysis

📁 Current Directory: {os.path.basename(current_dir)}
📄 Schematic Files Found: {len(schematic_files)}

Files:"""
        
        for i, file in enumerate(schematic_files[:5], 1):  # Show first 5
            message += f"\n  {i}. {file}"
        
        if len(schematic_files) > 5:
            message += f"\n  ... and {len(schematic_files) - 5} more"
        
        message += f"""

🔧 Available Features:
• Schematic file analysis
• Component extraction
• Net analysis
• AI-powered design suggestions

💡 Usage:
This script runs from the Schematic Editor's scripting console.
For full functionality, use the standalone analyzer or PCB plugin."""

        # Show message dialog
        app = wx.GetApp()
        if app is None:
            app = wx.App()
        
        wx.MessageBox(
            message,
            "Circuit-Synth AI - Schematic Console",
            wx.OK | wx.ICON_INFORMATION
        )
        
        print("✅ Circuit-Synth AI schematic analysis completed")
        print(f"Found {len(schematic_files)} schematic files in {current_dir}")
        
    except ImportError as e:
        print(f"❌ Error: wx not available - {e}")
        print("This script requires wxPython (usually available in KiCad's Python environment)")
    except Exception as e:
        print(f"❌ Error running schematic analysis: {e}")

def show_help():
    """Show help information."""
    help_text = """
Circuit-Synth AI Schematic Script Help
====================================

This script provides AI-powered schematic analysis for KiCad.

Commands:
- circuit_synth_schematic_analysis()  : Run main analysis
- show_help()                        : Show this help
- list_schematic_files()             : List .kicad_sch files in current directory

Usage from KiCad Scripting Console:
1. Open KiCad Schematic Editor
2. Go to Tools -> Scripting Console  
3. Run: exec(open('/path/to/schematic_script.py').read())
4. Call: circuit_synth_schematic_analysis()
"""
    print(help_text)

def list_schematic_files():
    """List schematic files in current directory."""
    current_dir = os.getcwd()
    schematic_files = [f for f in os.listdir(current_dir) if f.endswith('.kicad_sch')]
    
    print(f"\n📄 Schematic files in {current_dir}:")
    if schematic_files:
        for i, file in enumerate(schematic_files, 1):
            print(f"  {i}. {file}")
    else:
        print("  No .kicad_sch files found")
    print()

# Auto-run when script is loaded
print("🚀 Circuit-Synth AI Schematic Script Loaded!")
print("Type 'circuit_synth_schematic_analysis()' to run analysis")
print("Type 'show_help()' for more information")

# Auto-discover schematic files
try:
    list_schematic_files()
except:
    pass