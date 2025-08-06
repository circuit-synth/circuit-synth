"""
Direct KiCad schematic file manipulation.

This module provides functions to directly modify KiCad .kicad_sch files,
adding/removing components and nets while preserving manual edits.
"""

import re
from pathlib import Path
from typing import Dict, List, Tuple, Optional, Any
import uuid
from dataclasses import dataclass
from ..core._logger import context_logger


@dataclass
class ComponentDef:
    """Minimal component definition for canonical matching."""
    ref: str
    symbol: str  # e.g. "Device:R"
    value: str
    footprint: str
    nets: Dict[str, str]  # pin -> net mapping, e.g. {"1": "+5V", "2": "GND"}


@dataclass  
class NetDef:
    """Minimal net definition."""
    name: str
    connections: List[Tuple[str, str]]  # List of (component_ref, pin) tuples


class KiCadSchematicUpdater:
    """Direct manipulation of KiCad schematic files."""
    
    def __init__(self, sch_path: Path):
        """Initialize with path to .kicad_sch file."""
        self.sch_path = sch_path
        self.content = ""
        self.modified = False
        
    def load(self) -> bool:
        """Load the schematic file."""
        try:
            with open(self.sch_path, 'r', encoding='utf-8') as f:
                self.content = f.read()
            return True
        except Exception as e:
            context_logger.error(f"Failed to load schematic: {e}", component="SCH_UPDATER")
            return False
            
    def save(self) -> bool:
        """Save the schematic file if modified."""
        if not self.modified:
            return True
            
        try:
            with open(self.sch_path, 'w', encoding='utf-8') as f:
                f.write(self.content)
            self.modified = False
            context_logger.info(f"Saved schematic: {self.sch_path}", component="SCH_UPDATER")
            return True
        except Exception as e:
            context_logger.error(f"Failed to save schematic: {e}", component="SCH_UPDATER")
            return False
    
    def extract_canonical_state(self) -> Tuple[Dict[str, ComponentDef], Dict[str, NetDef]]:
        """
        Extract the canonical state (components and nets) from the schematic.
        
        Returns:
            Tuple of (components_dict, nets_dict)
        """
        components = {}
        nets = {}
        
        # Extract components with their connections
        # Pattern to match symbol blocks
        symbol_pattern = r'\(symbol\s+\(lib_id\s+"([^"]+)"\).*?\(property\s+"Reference"\s+"([^"]+)".*?\(property\s+"Value"\s+"([^"]+)".*?\(property\s+"Footprint"\s+"([^"]+)".*?\(uuid\s+"([^"]+)"\)'
        
        for match in re.finditer(symbol_pattern, self.content, re.DOTALL):
            lib_id = match.group(1)
            ref = match.group(2)
            value = match.group(3)
            footprint = match.group(4)
            comp_uuid = match.group(5)
            
            # For now, we'll extract net connections separately
            components[ref] = ComponentDef(
                ref=ref,
                symbol=lib_id,
                value=value,
                footprint=footprint,
                nets={}  # Will be filled from wire analysis
            )
            
        # Extract net connections from wires/labels
        # This is simplified - real implementation would parse the full structure
        
        context_logger.info(
            f"Extracted {len(components)} components from schematic",
            component="SCH_UPDATER",
            refs=list(components.keys())
        )
        
        return components, nets
    
    def add_component(self, component: ComponentDef, position: Tuple[float, float] = (50.0, 50.0)) -> bool:
        """
        Add a new component to the schematic.
        
        Args:
            component: Component definition
            position: (x, y) position in mm
            
        Returns:
            True if component was added successfully
        """
        # Check if component already exists
        if f'"Reference" "{component.ref}"' in self.content:
            context_logger.warning(
                f"Component {component.ref} already exists",
                component="SCH_UPDATER"
            )
            return False
            
        # Generate a new UUID for the component
        comp_uuid = str(uuid.uuid4())
        
        # Build the symbol S-expression
        symbol_sexpr = f'''
\t(symbol
\t\t(lib_id "{component.symbol}")
\t\t(at {position[0]} {position[1]} 0)
\t\t(unit 1)
\t\t(exclude_from_sim no)
\t\t(in_bom yes)
\t\t(on_board yes)
\t\t(dnp no)
\t\t(fields_autoplaced yes)
\t\t(uuid "{comp_uuid}")
\t\t(property "Reference" "{component.ref}"
\t\t\t(at {position[0]} {position[1] - 5} 0)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t\t(justify left)
\t\t\t)
\t\t)
\t\t(property "Value" "{component.value}"
\t\t\t(at {position[0]} {position[1] + 5} 0)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t\t(justify left)
\t\t\t)
\t\t)
\t\t(property "Footprint" "{component.footprint}"
\t\t\t(at {position[0]} {position[1] + 10} 0)
\t\t\t(effects
\t\t\t\t(font
\t\t\t\t\t(size 1.27 1.27)
\t\t\t\t)
\t\t\t\t(hide yes)
\t\t\t)
\t\t)
\t)'''
        
        # Find insertion point (before sheet_instances)
        insertion_point = self.content.rfind('\t(sheet_instances')
        
        if insertion_point == -1:
            context_logger.error("Could not find insertion point in schematic", component="SCH_UPDATER")
            return False
            
        # Insert the new component
        self.content = (
            self.content[:insertion_point] + 
            symbol_sexpr + '\n' +
            self.content[insertion_point:]
        )
        
        self.modified = True
        context_logger.info(
            f"Added component {component.ref} at position {position}",
            component="SCH_UPDATER"
        )
        return True
    
    def remove_component(self, ref: str) -> bool:
        """
        Remove a component from the schematic.
        
        Args:
            ref: Component reference (e.g. "R1")
            
        Returns:
            True if component was removed
        """
        # Find and remove the symbol block for this reference
        pattern = r'\t\(symbol\s+.*?\(property\s+"Reference"\s+"' + re.escape(ref) + r'".*?\n\t\)'
        
        new_content, count = re.subn(pattern, '', self.content, flags=re.DOTALL)
        
        if count > 0:
            self.content = new_content
            self.modified = True
            context_logger.info(f"Removed component {ref}", component="SCH_UPDATER")
            return True
        else:
            context_logger.warning(f"Component {ref} not found", component="SCH_UPDATER")
            return False
    
    def update_component_position(self, ref: str, new_position: Tuple[float, float]) -> bool:
        """
        Update the position of an existing component.
        
        Args:
            ref: Component reference
            new_position: New (x, y) position
            
        Returns:
            True if position was updated
        """
        # Pattern to find and update position for this reference
        pattern = (
            r'(\(symbol\s+\(lib_id\s+"[^"]+"\)\s+\(at\s+)'
            r'[\d.]+\s+[\d.]+'  # Current position
            r'(\s+[\d.]+)?'  # Optional rotation
            r'(\)[^)]*?'
            r'\(property\s+"Reference"\s+"' + re.escape(ref) + r'")'
        )
        
        replacement = rf'\g<1>{new_position[0]} {new_position[1]}\g<2>\g<3>'
        
        new_content, count = re.subn(pattern, replacement, self.content, flags=re.DOTALL)
        
        if count > 0:
            self.content = new_content
            self.modified = True
            context_logger.info(
                f"Updated position for {ref} to {new_position}",
                component="SCH_UPDATER"
            )
            return True
        else:
            context_logger.warning(f"Could not find component {ref}", component="SCH_UPDATER")
            return False
    
    def update_component_value(self, ref: str, new_value: str) -> bool:
        """
        Update the value of a component.
        
        Args:
            ref: Component reference
            new_value: New value
            
        Returns:
            True if value was updated
        """
        # Find the component and update its Value property
        # This pattern finds the Value property within a component with the given reference
        pattern = (
            r'(\(symbol\s+.*?'
            r'\(property\s+"Reference"\s+"' + re.escape(ref) + r'".*?'
            r'\(property\s+"Value"\s+")'
            r'[^"]+'  # Current value
            r'(")'
        )
        
        replacement = rf'\g<1>{new_value}\g<2>'
        
        new_content, count = re.subn(pattern, replacement, self.content, flags=re.DOTALL)
        
        if count > 0:
            self.content = new_content
            self.modified = True
            context_logger.info(
                f"Updated value for {ref} to {new_value}",
                component="SCH_UPDATER"
            )
            return True
        else:
            context_logger.warning(f"Could not find component {ref}", component="SCH_UPDATER")
            return False
    
    def add_wire(self, start: Tuple[float, float], end: Tuple[float, float]) -> bool:
        """
        Add a wire between two points.
        
        Args:
            start: (x, y) start position
            end: (x, y) end position
            
        Returns:
            True if wire was added
        """
        wire_uuid = str(uuid.uuid4())
        
        wire_sexpr = f'''
\t(wire
\t\t(pts
\t\t\t(xy {start[0]} {start[1]}) (xy {end[0]} {end[1]})
\t\t)
\t\t(stroke
\t\t\t(width 0)
\t\t\t(type default)
\t\t)
\t\t(uuid "{wire_uuid}")
\t)'''
        
        # Insert before sheet_instances
        insertion_point = self.content.rfind('\t(sheet_instances')
        
        if insertion_point == -1:
            return False
            
        self.content = (
            self.content[:insertion_point] + 
            wire_sexpr + '\n' +
            self.content[insertion_point:]
        )
        
        self.modified = True
        context_logger.info(f"Added wire from {start} to {end}", component="SCH_UPDATER")
        return True
    
    def add_label(self, net_name: str, position: Tuple[float, float]) -> bool:
        """
        Add a net label at a position.
        
        Args:
            net_name: Name of the net
            position: (x, y) position
            
        Returns:
            True if label was added
        """
        label_uuid = str(uuid.uuid4())
        
        label_sexpr = f'''
\t(label "{net_name}"
\t\t(at {position[0]} {position[1]} 0)
\t\t(effects
\t\t\t(font
\t\t\t\t(size 1.27 1.27)
\t\t\t)
\t\t\t(justify left)
\t\t)
\t\t(uuid "{label_uuid}")
\t)'''
        
        # Insert before sheet_instances
        insertion_point = self.content.rfind('\t(sheet_instances')
        
        if insertion_point == -1:
            return False
            
        self.content = (
            self.content[:insertion_point] + 
            label_sexpr + '\n' +
            self.content[insertion_point:]
        )
        
        self.modified = True
        context_logger.info(f"Added label {net_name} at {position}", component="SCH_UPDATER")
        return True