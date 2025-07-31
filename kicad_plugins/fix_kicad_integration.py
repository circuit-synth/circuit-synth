#!/usr/bin/env python3
"""
Fix KiCad BOM Integration Issues

This script helps diagnose and fix issues with KiCad BOM plugin integration.
The main issue is usually with the command line format or file paths.
"""

import os
import sys
from pathlib import Path
import stat


def create_kicad_compatible_plugins():
    """Create KiCad-compatible versions of our plugins with better error handling."""
    
    plugins_dir = Path.home() / "Documents" / "KiCad" / "9.0" / "scripting" / "plugins"
    
    # Create a simple, reliable BOM plugin for KiCad
    simple_plugin_content = '''#!/usr/bin/env python3
"""
Circuit-Synth AI Simple Plugin - KiCad Compatible Version

This version is specifically designed to work reliably with KiCad's BOM system.
"""

import sys
import os
import xml.etree.ElementTree as ET
from pathlib import Path
import argparse

def analyze_netlist(netlist_file):
    """Analyze the netlist and return results.""" 
    try:
        tree = ET.parse(netlist_file)
        root = tree.getroot()
        
        # Extract basic info
        design_element = root.find('.//design')
        design_name = "Unknown"
        if design_element is not None:
            source_element = design_element.find('source')
            if source_element is not None:
                design_name = Path(source_element.text).stem
        
        # Count components
        components = root.findall('.//components/comp')
        component_count = len(components)
        
        # Count nets
        nets = root.findall('.//nets/net')
        net_count = len(nets)
        
        return {
            'design_name': design_name,
            'component_count': component_count,
            'net_count': net_count,
            'components': components,
            'nets': nets
        }
        
    except Exception as e:
        return {'error': str(e)}

def show_analysis_gui(analysis):
    """Show analysis in a GUI window."""
    try:
        import tkinter as tk
        from tkinter import scrolledtext
        
        root = tk.Tk()
        root.title("🚀 Circuit-Synth AI - Circuit Analysis")
        root.geometry("600x400")
        
        # Force window to front and make it visible
        root.lift()
        root.attributes('-topmost', True)
        root.after(100, lambda: root.attributes('-topmost', False))
        
        # Create content
        text_widget = scrolledtext.ScrolledText(root, wrap=tk.WORD, font=('Consolas', 10))
        text_widget.pack(fill=tk.BOTH, expand=True, padx=10, pady=10)
        
        if 'error' in analysis:
            content = f"❌ Analysis Error: {analysis['error']}"
        else:
            content = f"""🚀 Circuit-Synth AI - Analysis Results
{'='*50}

📋 Project: {analysis['design_name']}
🔧 Components: {analysis['component_count']}
🔗 Nets: {analysis['net_count']}

Component Breakdown:
"""
            # Add component details
            for i, comp in enumerate(analysis['components'][:10]):  # Show first 10
                ref = comp.get('ref', 'Unknown')
                value_elem = comp.find('value')
                value = value_elem.text if value_elem is not None else 'N/A'
                content += f"  {i+1:2d}. {ref}: {value}\\n"
            
            if len(analysis['components']) > 10:
                content += f"  ... and {len(analysis['components']) - 10} more components\\n"
        
        text_widget.insert(tk.END, content)
        text_widget.config(state=tk.DISABLED)
        
        # Add close button
        close_btn = tk.Button(root, text="Close", command=root.destroy, font=('Arial', 12))
        close_btn.pack(pady=5)
        
        root.mainloop()
        return True
        
    except Exception as e:
        print(f"GUI Error: {e}")
        return False

def write_bom_output(analysis, output_file):
    """Write a traditional BOM output to satisfy KiCad."""
    try:
        output_path = Path(output_file)
        
        if 'error' in analysis:
            content = f"Circuit-Synth AI Analysis Error: {analysis['error']}\\n"
        else:
            content = f"""Circuit-Synth AI Analysis Report
{'='*40}

Project: {analysis['design_name']}
Components: {analysis['component_count']}
Nets: {analysis['net_count']}

Component List:
"""
            for comp in analysis['components']:
                ref = comp.get('ref', 'Unknown')
                value_elem = comp.find('value')
                value = value_elem.text if value_elem is not None else 'N/A'
                libsource = comp.find('libsource')
                lib = libsource.get('lib', 'Unknown') if libsource is not None else 'Unknown'
                content += f"{ref}\\t{value}\\t{lib}\\n"
        
        output_path.write_text(content)
        return True
        
    except Exception as e:
        print(f"Output Error: {e}")
        return False

def main():
    """Main plugin entry point."""
    parser = argparse.ArgumentParser(description='Circuit-Synth AI KiCad Plugin')
    parser.add_argument('netlist_file', help='Input netlist XML file from KiCad')
    parser.add_argument('output_file', help='Output file for BOM results')
    
    args = parser.parse_args()
    
    print("🚀 Circuit-Synth AI Starting...")
    print(f"📄 Input: {args.netlist_file}")
    print(f"📝 Output: {args.output_file}")
    
    # Analyze the netlist
    analysis = analyze_netlist(args.netlist_file)
    
    # Always write output file first (this prevents the "Failed to create file" error)
    if write_bom_output(analysis, args.output_file):
        print("✅ BOM output file created")
    
    # Then show GUI
    if show_analysis_gui(analysis):
        print("✅ GUI displayed")
    else:
        print("⚠️  GUI failed, but analysis completed")
    
    print("✅ Plugin completed successfully")

if __name__ == "__main__":
    main()
'''
    
    # Write the simple plugin
    simple_plugin_path = plugins_dir / "circuit_synth_simple.py"
    simple_plugin_path.write_text(simple_plugin_content)
    simple_plugin_path.chmod(simple_plugin_path.stat().st_mode | stat.S_IEXEC)
    
    print(f"✅ Created simple KiCad plugin: {simple_plugin_path}")
    
    return simple_plugin_path


def test_kicad_bom_setup():
    """Test the KiCad BOM setup with proper paths."""
    print("🔧 KiCad BOM Integration Test")
    print("="*40)
    
    # Check KiCad Python path
    kicad_python_paths = [
        "/Applications/KiCad/KiCad.app/Contents/Frameworks/Python.framework/Versions/Current/bin/python3",
        "/Applications/KiCad/KiCad.app/Contents/MacOS/python",
    ]
    
    kicad_python = None
    for path in kicad_python_paths:
        if Path(path).exists():
            kicad_python = path
            break
    
    if not kicad_python:
        print("❌ KiCad Python not found")
        return
    
    print(f"✅ KiCad Python: {kicad_python}")
    
    # Create the simple plugin
    simple_plugin_path = create_kicad_compatible_plugins()
    
    print(f"\n🚀 RECOMMENDED KiCad BOM SETUP:")
    print(f"="*50)
    print(f"Plugin Name: Circuit-Synth AI Simple")
    print(f"Plugin Path: {simple_plugin_path}")
    print(f"Command Line:")
    print(f'"{kicad_python}" "{simple_plugin_path}" "%I" "%O"')
    
    print(f"\n📋 SETUP INSTRUCTIONS:")
    print(f"1. Open KiCad Schematic Editor")
    print(f"2. Tools → Generate Bill of Materials")
    print(f"3. Click '+' to add plugin")
    print(f"4. Use the command line above")
    print(f"5. Test with a simple schematic")
    
    print(f"\n💡 This simple plugin will:")
    print(f"   • Always create the output file (prevents 'Failed to create file' error)")
    print(f"   • Show GUI analysis window")
    print(f"   • Work reliably with KiCad's BOM system")


def main():
    """Main function."""
    print("🔧 Circuit-Synth AI KiCad Integration Fixer")
    print("="*50)
    
    test_kicad_bom_setup()
    
    print(f"\n🎯 Try the simple plugin first to verify KiCad integration works.")
    print(f"Once that's working, you can add the Claude-integrated versions.")


if __name__ == "__main__":
    main()