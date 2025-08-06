"""
KiCad project preservation module.

This module handles preserving manual edits in KiCad projects when regenerating
from Python circuit definitions. It extracts positions, wires, and other manual
changes from existing KiCad files and applies them to newly generated projects.
"""

import re
from pathlib import Path
from typing import Dict, Tuple, Optional, Any
import json
from .._logger import context_logger


class KiCadPreservation:
    """Handles preservation of manual KiCad edits during regeneration."""
    
    @staticmethod
    def extract_component_positions(kicad_sch_path: Path) -> Dict[str, Dict[str, Any]]:
        """
        Extract component positions and other preserved properties from a KiCad schematic file.
        
        Args:
            kicad_sch_path: Path to the .kicad_sch file
            
        Returns:
            Dictionary mapping component references to their KiCad properties:
            {
                "R1": {
                    "position": (38.1, 45.72),
                    "rotation": 0,
                    "uuid": "f83c2365-2cc4-4210-93bf-5c5eff88e58a"
                },
                ...
            }
        """
        if not kicad_sch_path.exists():
            context_logger.debug(
                "KiCad schematic file does not exist, no positions to extract",
                component="PRESERVATION",
                path=str(kicad_sch_path)
            )
            return {}
            
        try:
            with open(kicad_sch_path, 'r', encoding='utf-8') as f:
                content = f.read()
                
            positions = {}
            
            # Pattern to match symbol blocks with position and reference
            # Captures the entire symbol block to extract multiple properties
            symbol_pattern = r'\(symbol\s+\(lib_id\s+"([^"]+)"\)\s+\(at\s+([\d.]+)\s+([\d.]+)(?:\s+([\d.]+))?\)[^)]*?\(uuid\s+([a-f0-9-]+)\).*?\(property\s+"Reference"\s+"([^"]+)"'
            
            matches = re.finditer(symbol_pattern, content, re.DOTALL)
            
            for match in matches:
                lib_id = match.group(1)
                x = float(match.group(2))
                y = float(match.group(3))
                rotation = float(match.group(4)) if match.group(4) else 0
                uuid_val = match.group(5)
                ref = match.group(6)
                
                positions[ref] = {
                    "position": (x, y),
                    "rotation": rotation,
                    "uuid": uuid_val,
                    "lib_id": lib_id
                }
                
                context_logger.debug(
                    f"Extracted component position",
                    component="PRESERVATION",
                    reference=ref,
                    position=(x, y),
                    rotation=rotation
                )
                
            context_logger.info(
                f"Extracted {len(positions)} component positions from KiCad schematic",
                component="PRESERVATION",
                references=list(positions.keys())
            )
            
            return positions
            
        except Exception as e:
            context_logger.error(
                f"Failed to extract component positions: {e}",
                component="PRESERVATION",
                path=str(kicad_sch_path)
            )
            return {}
    
    @staticmethod
    def check_project_exists(project_path: Path) -> bool:
        """
        Check if a KiCad project exists at the given path.
        
        Args:
            project_path: Path to the project directory
            
        Returns:
            True if the project exists with at least a .kicad_sch file
        """
        if not project_path.exists():
            return False
            
        # Check for the main schematic file
        project_name = project_path.name
        sch_file = project_path / f"{project_name}.kicad_sch"
        
        return sch_file.exists()
    
    @staticmethod
    def merge_with_preservation(
        new_json_data: Dict[str, Any],
        existing_positions: Dict[str, Dict[str, Any]]
    ) -> Dict[str, Any]:
        """
        Merge new circuit data with preserved positions from existing KiCad project.
        
        Args:
            new_json_data: The newly generated circuit data in JSON format
            existing_positions: Extracted positions from existing KiCad file
            
        Returns:
            Merged JSON data with preserved positions
        """
        if not existing_positions:
            return new_json_data
            
        # Add a _kicad_preservation section to components
        for comp_ref, comp_data in new_json_data.get("components", {}).items():
            if comp_ref in existing_positions:
                preserved = existing_positions[comp_ref]
                
                # Add preservation data to component
                comp_data["_kicad_preserved"] = {
                    "position": preserved["position"],
                    "rotation": preserved.get("rotation", 0),
                    "uuid": preserved.get("uuid")
                }
                
                context_logger.debug(
                    f"Applied preserved position to component",
                    component="PRESERVATION",
                    reference=comp_ref,
                    position=preserved["position"]
                )
        
        return new_json_data
    
    @staticmethod
    def apply_preserved_positions(
        kicad_sch_path: Path,
        preserved_positions: Dict[str, Dict[str, Any]]
    ) -> bool:
        """
        Apply preserved positions to a newly generated KiCad schematic file.
        
        This modifies the KiCad file in place, updating component positions
        to match the preserved values.
        
        Args:
            kicad_sch_path: Path to the newly generated .kicad_sch file
            preserved_positions: Dictionary of preserved positions to apply
            
        Returns:
            True if positions were successfully applied
        """
        if not preserved_positions:
            context_logger.debug(
                "No preserved positions to apply",
                component="PRESERVATION"
            )
            return True
            
        try:
            with open(kicad_sch_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            modified = False
            
            for ref, preserved in preserved_positions.items():
                # Pattern to find and replace position for this reference
                # Match the symbol block with this reference
                pattern = (
                    r'(\(symbol\s+\(lib_id\s+"[^"]+"\)\s+\(at\s+)'
                    r'[\d.]+\s+[\d.]+'  # Current position
                    r'(\s+[\d.]+)?'  # Optional rotation
                    r'(\)[^)]*?'
                    r'\(property\s+"Reference"\s+"' + re.escape(ref) + r'")'
                )
                
                new_pos = preserved["position"]
                new_rotation = preserved.get("rotation", 0)
                
                # Build replacement with new position
                if new_rotation != 0:
                    replacement = rf'\g<1>{new_pos[0]} {new_pos[1]} {new_rotation}\g<3>'
                else:
                    replacement = rf'\g<1>{new_pos[0]} {new_pos[1]}\g<3>'
                
                new_content, count = re.subn(pattern, replacement, content, flags=re.DOTALL)
                
                if count > 0:
                    content = new_content
                    modified = True
                    context_logger.debug(
                        f"Updated position for component {ref}",
                        component="PRESERVATION",
                        new_position=new_pos,
                        rotation=new_rotation
                    )
                else:
                    context_logger.warning(
                        f"Could not find component {ref} to update position",
                        component="PRESERVATION"
                    )
            
            if modified:
                # Write the modified content back
                with open(kicad_sch_path, 'w', encoding='utf-8') as f:
                    f.write(content)
                    
                context_logger.info(
                    f"Applied preserved positions to {len(preserved_positions)} components",
                    component="PRESERVATION",
                    path=str(kicad_sch_path)
                )
                
            return True
            
        except Exception as e:
            context_logger.error(
                f"Failed to apply preserved positions: {e}",
                component="PRESERVATION",
                path=str(kicad_sch_path)
            )
            return False