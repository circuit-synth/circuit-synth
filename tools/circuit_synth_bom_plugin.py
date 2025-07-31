#!/usr/bin/env python3
"""
Circuit-Synth AI BOM "Backdoor" Plugin

This plugin uses KiCad's BOM tool as a backdoor to provide AI-powered 
schematic analysis directly from the schematic editor.

How it works:
1. KiCad's schematic editor has a BOM tool that can run Python scripts
2. The BOM tool passes the netlist (XML) as input to any script
3. We use this to analyze the schematic and provide AI assistance
4. Instead of generating a BOM, we show AI analysis results

Installation:
1. Save this file to your KiCad plugins directory
2. In KiCad Schematic Editor: Tools → Generate Bill of Materials
3. Add this script as a "BOM plugin"
4. Run it to get AI circuit analysis instead of a BOM!
"""

import sys
import os
import xml.etree.ElementTree as ET
from pathlib import Path
import argparse
import json
from datetime import datetime

def show_gui_analysis(analysis_data):
    """Show analysis results in a GUI dialog."""
    try:
        import tkinter as tk
        from tkinter import messagebox, scrolledtext
        
        # Create main window
        root = tk.Tk()
        root.title("Circuit-Synth AI - Schematic Analysis")
        root.geometry("600x500")
        
        # Create scrolled text widget
        text_widget = scrolledtext.ScrolledText(root, wrap=tk.WORD, width=70, height=25)
        text_widget.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        
        # Format analysis results
        content = f"""🚀 Circuit-Synth AI - Schematic Analysis Results
{'='*60}

📋 Project Information:
• Design: {analysis_data.get('design_name', 'Unknown')}
• Analysis Time: {analysis_data.get('timestamp', 'Unknown')}
• Components Found: {analysis_data.get('component_count', 0)}

📐 Component Analysis:
"""
        
        components = analysis_data.get('components', [])
        component_types = {}
        
        for comp in components:
            comp_type = comp.get('library', 'Unknown')
            component_types[comp_type] = component_types.get(comp_type, 0) + 1
        
        for comp_type, count in sorted(component_types.items()):
            content += f"• {comp_type}: {count} components\n"
        
        content += f"""

🔧 Component Details:
"""
        
        for i, comp in enumerate(components[:10], 1):  # Show first 10
            ref = comp.get('ref', 'Unknown')
            value = comp.get('value', 'N/A')
            lib = comp.get('library', 'Unknown')
            content += f"{i:2d}. {ref:<8} | {value:<15} | {lib}\n"
        
        if len(components) > 10:
            content += f"    ... and {len(components) - 10} more components\n"
        
        content += f"""

🔗 Net Analysis:
• Total nets: {len(analysis_data.get('nets', []))}
• Connections analyzed: {sum(len(net.get('nodes', [])) for net in analysis_data.get('nets', []))}

🤖 AI Insights:
• This schematic contains {analysis_data.get('component_count', 0)} components
• Component diversity: {len(component_types)} different types
• Design complexity: {'High' if analysis_data.get('component_count', 0) > 50 else 'Medium' if analysis_data.get('component_count', 0) > 20 else 'Low'}

💡 Recommendations:
• Consider component placement optimization
• Review power supply decoupling
• Check signal integrity for high-speed signals
• Verify component ratings match requirements

✨ This analysis was generated using the Circuit-Synth AI BOM backdoor plugin!
   The plugin analyzed your schematic through KiCad's BOM tool interface.
"""
        
        # Insert content
        text_widget.insert(tk.END, content)
        text_widget.config(state=tk.DISABLED)  # Make read-only
        
        # Add close button
        close_btn = tk.Button(root, text="Close", command=root.destroy, font=("Arial", 12))
        close_btn.pack(pady=5)
        
        # Center window
        root.update_idletasks()
        x = (root.winfo_screenwidth() // 2) - (root.winfo_width() // 2)
        y = (root.winfo_screenheight() // 2) - (root.winfo_height() // 2)
        root.geometry(f"+{x}+{y}")
        
        # Run GUI
        root.mainloop()
        
    except ImportError:
        # Fallback to console output if tkinter not available
        print("="*60)
        print("🚀 Circuit-Synth AI - Schematic Analysis")
        print("="*60)
        print(f"Components: {analysis_data.get('component_count', 0)}")
        print(f"Design: {analysis_data.get('design_name', 'Unknown')}")
        print("GUI not available, analysis completed in console.")


def analyze_netlist_xml(netlist_file):
    """Analyze the KiCad netlist XML file."""
    try:
        tree = ET.parse(netlist_file)
        root = tree.getroot()
        
        # Extract design information
        design_element = root.find('.//design')
        design_name = design_element.find('source').text if design_element is not None else "Unknown"
        design_name = Path(design_name).stem if design_name else "Unknown"
        
        # Extract components
        components = []
        libparts = root.find('.//libparts')
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
    """Main entry point for the BOM plugin."""
    parser = argparse.ArgumentParser(description='Circuit-Synth AI BOM Backdoor Plugin')
    parser.add_argument('netlist_file', help='Path to the netlist XML file from KiCad')
    parser.add_argument('output_file', help='Output file (ignored - we show GUI instead)')
    
    args = parser.parse_args()
    
    print("🚀 Circuit-Synth AI BOM Plugin Starting...")
    print(f"📄 Analyzing netlist: {args.netlist_file}")
    
    # Analyze the netlist
    analysis = analyze_netlist_xml(args.netlist_file)
    
    if analysis.get('success'):
        print(f"✅ Analysis complete: {analysis['component_count']} components found")
        
        # Show GUI with results
        show_gui_analysis(analysis)
        
        # Also write a summary file (since KiCad expects output)
        output_path = Path(args.output_file)
        summary = f"""Circuit-Synth AI Analysis Summary
=====================================

Design: {analysis['design_name']}
Components: {analysis['component_count']}
Nets: {len(analysis['nets'])}
Timestamp: {analysis['timestamp']}

This file was generated by Circuit-Synth AI BOM Plugin.
The detailed analysis was shown in the GUI dialog.

For more information about Circuit-Synth AI, visit:
https://github.com/circuit-synth/circuit-synth
"""
        
        output_path.write_text(summary)
        print(f"📝 Summary written to: {args.output_file}")
        
    else:
        error_msg = f"❌ Analysis failed: {analysis.get('error', 'Unknown error')}"
        print(error_msg)
        
        # Write error to output file
        Path(args.output_file).write_text(f"Error: {analysis.get('error', 'Unknown error')}")
        
        sys.exit(1)


if __name__ == "__main__":
    main()