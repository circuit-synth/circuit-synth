"""
Schematic Utilities for Circuit-Synth AI Plugin

Since KiCad's eeschema doesn't have ActionPlugin support, this module provides
utilities to work with schematic files directly.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Tuple


class SchematicParser:
    """Parser for KiCad schematic files (.kicad_sch)."""
    
    def __init__(self, schematic_path: str):
        self.schematic_path = Path(schematic_path)
        self.schematic_data = None
        
    def load_schematic(self) -> bool:
        """Load and parse the schematic file."""
        if not self.schematic_path.exists():
            return False
            
        try:
            with open(self.schematic_path, 'r', encoding='utf-8') as f:
                self.schematic_data = f.read()
            return True
        except Exception as e:
            print(f"Error loading schematic: {e}")
            return False
    
    def get_components(self) -> List[Dict]:
        """Extract components from the schematic."""
        if not self.schematic_data:
            return []
            
        components = []
        
        # Parse symbols using regex (simplified approach)
        symbol_pattern = r'\(symbol\s+\(lib_id\s+"([^"]+)"\)\s+\(at\s+([^)]+)\)\s+\(unit\s+\d+\)\s*(?:\(in_bom\s+yes\)\s+\(on_board\s+yes\)\s*)?\(uuid\s+([^)]+)\)[^(]*(?:\(property\s+"Reference"\s+"([^"]+)"[^)]*\))?[^(]*(?:\(property\s+"Value"\s+"([^"]+)"[^)]*\))?'
        
        matches = re.findall(symbol_pattern, self.schematic_data, re.DOTALL)
        
        for match in matches:
            lib_id, position, uuid, reference, value = match
            components.append({
                'lib_id': lib_id,
                'position': position.strip(),
                'uuid': uuid,
                'reference': reference or 'Unknown',
                'value': value or 'Unknown'
            })
            
        return components
    
    def get_nets(self) -> List[Dict]:
        """Extract net information from the schematic."""
        if not self.schematic_data:
            return []
            
        nets = []
        
        # Look for wire connections and labels
        wire_pattern = r'\(wire\s+\(pts\s+\(xy\s+([^)]+)\)\s+\(xy\s+([^)]+)\)\)'
        wire_matches = re.findall(wire_pattern, self.schematic_data)
        
        for i, (start, end) in enumerate(wire_matches):
            nets.append({
                'type': 'wire',
                'id': f'wire_{i}',
                'start': start.strip(),
                'end': end.strip()
            })
            
        # Look for labels
        label_pattern = r'\(label\s+"([^"]+)"\s+\(at\s+([^)]+)\)'
        label_matches = re.findall(label_pattern, self.schematic_data)
        
        for label_text, position in label_matches:
            nets.append({
                'type': 'label',
                'name': label_text,
                'position': position.strip()
            })
            
        return nets
    
    def get_schematic_stats(self) -> Dict:
        """Get basic statistics about the schematic."""
        if not self.load_schematic():
            return {}
            
        components = self.get_components()
        nets = self.get_nets()
        
        # Count component types
        component_types = {}
        for comp in components:
            lib_id = comp['lib_id']
            if ':' in lib_id:
                lib_name = lib_id.split(':')[0]
            else:
                lib_name = 'Unknown'
            component_types[lib_name] = component_types.get(lib_name, 0) + 1
        
        return {
            'total_components': len(components),
            'total_nets': len([n for n in nets if n['type'] == 'wire']),
            'total_labels': len([n for n in nets if n['type'] == 'label']),
            'component_types': component_types,
            'filename': self.schematic_path.name
        }


def find_project_schematic(pcb_path: str) -> Optional[str]:
    """Find the corresponding schematic file for a PCB."""
    pcb_path = Path(pcb_path)
    
    if not pcb_path.exists():
        return None
    
    # Look for .kicad_sch file with same base name
    schematic_path = pcb_path.with_suffix('.kicad_sch')
    if schematic_path.exists():
        return str(schematic_path)
    
    # Look for .kicad_sch files in the same directory
    project_dir = pcb_path.parent
    schematic_files = list(project_dir.glob('*.kicad_sch'))
    
    if schematic_files:
        return str(schematic_files[0])  # Return the first one found
        
    return None


def analyze_schematic_for_pcb(pcb_path: str) -> Dict:
    """Analyze the schematic associated with a PCB file."""
    schematic_path = find_project_schematic(pcb_path)
    
    if not schematic_path:
        return {
            'error': 'No schematic file found',
            'pcb_path': pcb_path
        }
    
    parser = SchematicParser(schematic_path)
    stats = parser.get_schematic_stats()
    
    if not stats:
        return {
            'error': 'Could not parse schematic file',
            'schematic_path': schematic_path
        }
    
    return {
        'success': True,
        'schematic_path': schematic_path,
        'stats': stats,
        'components': parser.get_components()[:10],  # First 10 components as examples
    }