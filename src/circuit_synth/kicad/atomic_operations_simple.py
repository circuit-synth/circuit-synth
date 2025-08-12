"""
Simple atomic operations for KiCad schematic files.
Uses string manipulation instead of S-expression parsing for reliability.
"""

import logging
import shutil
import uuid
from pathlib import Path
from typing import Dict, Tuple, Union

logger = logging.getLogger(__name__)


def add_component_to_schematic_simple(
    file_path: Union[str, Path], 
    lib_id: str,
    reference: str,
    value: str = "",
    position: Tuple[float, float] = (100, 100),
    footprint: str = "",
    **properties
) -> bool:
    """
    Add a component to an existing KiCad schematic file using simple string manipulation.
    """
    file_path = Path(file_path)
    
    # Create backup
    backup_path = file_path.with_suffix('.kicad_sch.bak')
    try:
        shutil.copy2(file_path, backup_path)
        
        # Read the file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Create component string
        component_uuid = str(uuid.uuid4())
        component_str = f'''	(symbol
		(lib_id "{lib_id}")
		(at {position[0]} {position[1]} 0)
		(unit 1)
		(exclude_from_sim no)
		(in_bom yes)
		(on_board yes)
		(dnp no)
		(fields_autoplaced yes)
		(uuid "{component_uuid}")'''
        
        # Add Reference property
        if reference:
            component_str += f'''
		(property "Reference" "{reference}"
			(at {position[0]} {position[1] - 5} 0)
			(effects
				(font
					(size 1.27 1.27)
				)
				(justify left)
			)
		)'''
        
        # Add Value property
        if value:
            component_str += f'''
		(property "Value" "{value}"
			(at {position[0]} {position[1] + 5} 0)
			(effects
				(font
					(size 1.27 1.27)
				)
				(justify left)
			)
		)'''
        
        # Add Footprint property
        if footprint:
            component_str += f'''
		(property "Footprint" "{footprint}"
			(at {position[0]} {position[1]} 0)
			(effects
				(font
					(size 1.27 1.27)
				)
				(hide yes)
			)
		)'''
        
        component_str += '\n\t)'
        
        # Find insertion point (before sheet_instances)
        sheet_instances_pos = content.find('\t(sheet_instances')
        if sheet_instances_pos == -1:
            # If no sheet_instances, insert before the last closing paren
            sheet_instances_pos = content.rfind(')')
        
        # Insert component
        new_content = (
            content[:sheet_instances_pos] + 
            component_str + '\n' +
            content[sheet_instances_pos:]
        )
        
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        logger.info(f"Added component {reference} to {file_path}")
        return True
        
    except Exception as e:
        # Restore backup on failure
        if backup_path.exists():
            shutil.copy2(backup_path, file_path)
        logger.error(f"Failed to add component {reference} to {file_path}: {e}")
        return False
    finally:
        # Clean up backup
        if backup_path.exists():
            backup_path.unlink()


def remove_component_from_schematic_simple(
    file_path: Union[str, Path],
    reference: str
) -> bool:
    """
    Remove a component from an existing KiCad schematic file using string manipulation.
    """
    file_path = Path(file_path)
    
    # Create backup
    backup_path = file_path.with_suffix('.kicad_sch.bak')
    try:
        shutil.copy2(file_path, backup_path)
        
        # Read the file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Find the component by looking for the Reference property
        ref_pattern = f'"Reference" "{reference}"'
        ref_pos = content.find(ref_pattern)
        
        if ref_pos == -1:
            logger.warning(f"Component {reference} not found in {file_path}")
            return False
        
        # Find the start of the symbol block (go backwards to find "(symbol")
        symbol_start = content.rfind('\t(symbol', 0, ref_pos)
        if symbol_start == -1:
            logger.error(f"Could not find symbol start for {reference}")
            return False
        
        # Find the end of the symbol block (find matching closing paren)
        # Simple approach: find the next "\t)" that's at the same indentation level
        symbol_end = content.find('\n\t)', symbol_start)
        if symbol_end == -1:
            logger.error(f"Could not find symbol end for {reference}")
            return False
        
        # Include the closing paren and newline
        symbol_end += len('\n\t)')
        
        # Remove the entire symbol block
        new_content = content[:symbol_start] + content[symbol_end:]
        
        # Write back to file
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        logger.info(f"Removed component {reference} from {file_path}")
        return True
        
    except Exception as e:
        # Restore backup on failure
        if backup_path.exists():
            shutil.copy2(backup_path, file_path)
        logger.error(f"Failed to remove component {reference} from {file_path}: {e}")
        return False
    finally:
        # Clean up backup
        if backup_path.exists():
            backup_path.unlink()