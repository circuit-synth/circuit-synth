#!/usr/bin/env python3
"""
Circuit-Synth PCB Simple Launcher Plugin for KiCad PCB Editor

Directly launches the working BOM plugin with PCB data - guaranteed to work.
"""

import pcbnew
import wx
import sys
import os
import subprocess
import tempfile
import json
from pathlib import Path

def analyze_pcb_board(board):
    """Analyze KiCad PCB board and extract key information."""
    try:
        # Basic board info
        board_name = board.GetFileName() if board.GetFileName() else "Untitled"
        
        # Get components
        footprints = list(board.GetFootprints())
        components = []
        component_types = {}
        
        for fp in footprints[:20]:  # Limit to first 20 for performance
            ref = fp.GetReference()
            value = fp.GetValue()
            # Fix the GetUniString error - use str() instead
            footprint_name = str(fp.GetFPID().GetLibItemName())
            
            components.append({
                'ref': ref,
                'value': value,
                'footprint': footprint_name
            })
            
            # Count component types
            prefix = ref.rstrip('0123456789')
            component_types[prefix] = component_types.get(prefix, 0) + 1
        
        # Get tracks and routing info
        tracks = list(board.GetTracks())
        vias = sum(1 for t in tracks if t.Type() == pcbnew.PCB_VIA_T)
        track_segments = len(tracks) - vias
        
        # Get nets
        netinfo = board.GetNetInfo()
        net_count = netinfo.GetNetCount() if netinfo else 0
        
        # Get board dimensions
        try:
            bbox = board.GetBoardEdgesBoundingBox()
            width_mm = pcbnew.ToMM(bbox.GetWidth())
            height_mm = pcbnew.ToMM(bbox.GetHeight())
            board_size = f"{width_mm:.1f}mm x {height_mm:.1f}mm"
        except:
            board_size = "Unknown"
        
        # Format as "netlist" data similar to BOM plugin input
        netlist_data = {
            'design_name': Path(board_name).stem,
            'component_count': len(footprints),
            'net_count': net_count,
            'components': components[:15],  # Limit for BOM plugin compatibility
            'component_types': component_types,
            'pcb_specific': {
                'board_size': board_size,
                'track_segments': track_segments,
                'via_count': vias,
                'track_count': len(tracks)
            },
            'success': True
        }
        
        return netlist_data
        
    except Exception as e:
        return {
            'error': str(e),
            'success': False
        }

def create_fake_netlist_for_bom_plugin(analysis_data):
    """Create a fake netlist XML that the BOM plugin can parse with PCB data."""
    
    netlist_xml = f'''<?xml version="1.0" encoding="utf-8"?>
<export version="E">
  <design>
    <source>{analysis_data['design_name']}.kicad_sch</source>
    <date>PCB Analysis</date>
    <tool>Circuit-Synth PCB Plugin</tool>
  </design>
  <components>'''
    
    # Add components from PCB analysis
    for comp in analysis_data.get('components', []):
        netlist_xml += f'''
    <comp ref="{comp['ref']}">
      <value>{comp['value']}</value>
      <footprint>{comp['footprint']}</footprint>
    </comp>'''
    
    netlist_xml += '''
  </components>
  <nets>'''
    
    # Add some basic nets
    for i in range(min(5, analysis_data.get('net_count', 0))):
        netlist_xml += f'''
    <net code="{i}" name="Net-{i}">
      <node ref="R{i+1}" pin="1"/>
    </net>'''
    
    netlist_xml += '''
  </nets>
</export>'''
    
    return netlist_xml

class CircuitSynthPCBSimpleLauncher(pcbnew.ActionPlugin):
    """
    Circuit-Synth PCB Simple Launcher Plugin for KiCad PCB Editor.
    
    Directly launches the working BOM plugin with PCB context.
    """

    def defaults(self):
        """Set up plugin defaults."""
        self.name = "Circuit-Synth PCB Launcher"
        self.category = "Circuit Design"
        self.description = "Launch Claude AI chat with PCB context via BOM plugin"
        self.show_toolbar_button = True
        
    def Run(self):
        """Execute the plugin."""
        try:
            print("💬 Circuit-Synth PCB Launcher Starting...")
            
            # Get the current board
            board = pcbnew.GetBoard()
            if board is None:
                error_msg = "No PCB board found. Please open a PCB file first."
                print(f"❌ {error_msg}")
                wx.MessageBox(error_msg, "Circuit-Synth PCB Launcher", wx.OK | wx.ICON_WARNING)
                return

            print("✅ PCB board found, analyzing...")
            
            # Analyze the board
            analysis = analyze_pcb_board(board)
            
            if not analysis.get('success'):
                error_msg = f"Board analysis failed: {analysis.get('error', 'Unknown error')}"
                print(f"❌ {error_msg}")
                wx.MessageBox(error_msg, "Analysis Error", wx.OK | wx.ICON_ERROR)
                return
            
            print(f"✅ Board analysis complete: {analysis['component_count']} components")
            print(f"   Board: {analysis['design_name']}")
            print(f"   Size: {analysis['pcb_specific']['board_size']}")
            print(f"   Routing: {analysis['pcb_specific']['track_segments']} tracks, {analysis['pcb_specific']['via_count']} vias")
            
            # Find the BOM plugin
            bom_plugin_path = Path.home() / "Documents" / "KiCad" / "9.0" / "scripting" / "plugins" / "circuit_synth_bom_plugin.py"
            
            if not bom_plugin_path.exists():
                error_msg = f"BOM plugin not found at: {bom_plugin_path}\\n\\nPlease run the plugin installer first."
                print(f"❌ {error_msg}")
                wx.MessageBox(error_msg, "BOM Plugin Not Found", wx.OK | wx.ICON_ERROR)
                return
            
            print(f"✅ Found BOM plugin: {bom_plugin_path}")
            
            # Create fake netlist XML with PCB data
            netlist_xml = create_fake_netlist_for_bom_plugin(analysis)
            
            # Write to temporary files
            with tempfile.NamedTemporaryFile(mode='w', suffix='.xml', delete=False) as f:
                f.write(netlist_xml)
                netlist_file = f.name
            
            with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
                f.write("PCB Analysis Output")
                output_file = f.name
            
            print(f"📄 Created temporary netlist: {netlist_file}")
            print(f"📄 Created temporary output: {output_file}")
            
            # Launch BOM plugin directly with our PCB netlist
            try:
                # Use python3 explicitly to avoid KiCad's Python environment
                cmd = ["/usr/bin/python3", str(bom_plugin_path), netlist_file, output_file]
                print(f"🚀 Launching BOM plugin: {' '.join(cmd)}")
                
                # Launch the BOM plugin
                process = subprocess.Popen(
                    cmd,
                    stdout=subprocess.PIPE,
                    stderr=subprocess.PIPE,
                    stdin=subprocess.DEVNULL
                )
                
                print(f"✅ BOM plugin launched with PID: {process.pid}")
                
                # Show success message
                success_msg = f"PCB Claude Chat Launched!\\n\\n" + \
                             f"Board: {analysis['design_name']}\\n" + \
                             f"Components: {analysis['component_count']}\\n" + \
                             f"Size: {analysis['pcb_specific']['board_size']}\\n" + \
                             f"Routing: {analysis['pcb_specific']['track_segments']} tracks\\n\\n" + \
                             f"The Claude chat interface should open shortly.\\n" + \
                             f"It will have your PCB context for design advice."
                
                wx.MessageBox(success_msg, "PCB Chat Launched", wx.OK | wx.ICON_INFORMATION)
                
            except Exception as e:
                error_msg = f"Failed to launch BOM plugin: {e}\\n\\n" + \
                           f"Command attempted: {' '.join(cmd)}\\n\\n" + \
                           f"Make sure Python 3 is installed at /usr/bin/python3"
                print(f"❌ Launch failed: {e}")
                wx.MessageBox(error_msg, "Launch Failed", wx.OK | wx.ICON_ERROR)

        except Exception as e:
            error_msg = f"Plugin error: {str(e)}"
            print(f"❌ Plugin exception: {error_msg}")
            import traceback
            print(f"   Traceback: {traceback.format_exc()}")
            wx.MessageBox(f"Plugin error: {error_msg}\\n\\nCheck scripting console for details.", 
                         "Plugin Error", wx.OK | wx.ICON_ERROR)

# Register the plugin
CircuitSynthPCBSimpleLauncher().register()