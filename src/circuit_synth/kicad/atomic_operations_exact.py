"""
Exact atomic operations for KiCad schematic files.
Generates schematics that exactly match the reference formatting and structure.
"""

import logging
import shutil
import uuid
from pathlib import Path
from typing import Dict, Tuple, Union

logger = logging.getLogger(__name__)

def extract_uuid(content: str) -> str:
    """Extract UUID from KiCad schematic content."""
    try:
        # Look for the main schematic UUID - it's the first UUID in the file
        import re
        uuid_pattern = r'\(uuid ([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})\)'
        match = re.search(uuid_pattern, content)
        if match:
            return match.group(1)
        else:
            return "00000000-0000-0000-0000-000000000000"
    except:
        return "00000000-0000-0000-0000-000000000000"

# Full Device:R symbol definition matching reference exactly
DEVICE_R_SYMBOL_DEF = '''		(symbol "Device:R"
			(pin_numbers
				(hide yes)
			)
			(pin_names
				(offset 0)
			)
			(exclude_from_sim no)
			(in_bom yes)
			(on_board yes)
			(property "Reference" "R"
				(at 2.032 0 90)
				(effects
					(font
						(size 1.27 1.27)
					)
				)
			)
			(property "Value" "R"
				(at 0 0 90)
				(effects
					(font
						(size 1.27 1.27)
					)
				)
			)
			(property "Footprint" ""
				(at -1.778 0 90)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Datasheet" "~"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "Description" "Resistor"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "ki_keywords" "R res resistor"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(property "ki_fp_filters" "R_*"
				(at 0 0 0)
				(effects
					(font
						(size 1.27 1.27)
					)
					(hide yes)
				)
			)
			(symbol "R_0_1"
				(rectangle
					(start -1.016 -2.54)
					(end 1.016 2.54)
					(stroke
						(width 0.254)
						(type default)
					)
					(fill
						(type none)
					)
				)
			)
			(symbol "R_1_1"
				(pin passive line
					(at 0 3.81 270)
					(length 1.27)
					(name "~"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "1"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
				)
				(pin passive line
					(at 0 -3.81 90)
					(length 1.27)
					(name "~"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
					(number "2"
						(effects
							(font
								(size 1.27 1.27)
							)
						)
					)
				)
			)
			(embedded_fonts no)
		)'''


def add_component_to_schematic_exact(
    file_path: Union[str, Path], 
    lib_id: str,
    reference: str,
    value: str = "",
    position: Tuple[float, float] = (100, 100),
    footprint: str = "",
    **properties
) -> bool:
    """
    Add a component to an existing KiCad schematic file with exact reference formatting.
    """
    file_path = Path(file_path)
    
    # Create backup
    backup_path = file_path.with_suffix('.kicad_sch.bak')
    try:
        shutil.copy2(file_path, backup_path)
        
        # Read the file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Generate UUIDs for component
        component_uuid = str(uuid.uuid4())
        pin1_uuid = str(uuid.uuid4())
        pin2_uuid = str(uuid.uuid4())
        schematic_uuid = extract_uuid(content)
        
        # Create component symbol instance with exact reference formatting
        symbol_instance = f'''	(symbol
		(lib_id "{lib_id}")
		(at {position[0]} {position[1]} 0)
		(unit 1)
		(exclude_from_sim no)
		(in_bom yes)
		(on_board yes)
		(dnp no)
		(fields_autoplaced yes)
		(uuid "{component_uuid}")
		(property "Reference" "{reference}"
			(at {position[0] + 2.54} {position[1] - 1.27} 0)
			(effects
				(font
					(size 1.27 1.27)
				)
				(justify left)
			)
		)
		(property "Value" "{value}"
			(at {position[0] + 2.54} {position[1] + 1.27} 0)
			(effects
				(font
					(size 1.27 1.27)
				)
				(justify left)
			)
		)
		(property "Footprint" "{footprint}"
			(at {position[0] - 1.778} {position[1]} 90)
			(effects
				(font
					(size 1.27 1.27)
				)
				(hide yes)
			)
		)
		(property "Datasheet" "~"
			(at {position[0]} {position[1]} 0)
			(effects
				(font
					(size 1.27 1.27)
				)
				(hide yes)
			)
		)
		(property "Description" "Resistor"
			(at {position[0]} {position[1]} 0)
			(effects
				(font
					(size 1.27 1.27)
				)
				(hide yes)
			)
		)
		(pin "2"
			(uuid "{pin2_uuid}")
		)
		(pin "1"
			(uuid "{pin1_uuid}")
		)
		(instances
			(project ""
				(path "/{schematic_uuid}"
					(reference "{reference}")
					(unit 1)
				)
			)
		)
	)'''
        
        # Check if lib_symbols section needs Device:R definition
        if lib_id == "Device:R" and '"Device:R"' not in content:
            # Add Device:R symbol definition to lib_symbols
            lib_symbols_start = content.find('\t(lib_symbols')
            if lib_symbols_start != -1:
                lib_symbols_end = content.find('\n\t)', lib_symbols_start)
                if lib_symbols_end != -1:
                    # Insert Device:R definition
                    new_content = (
                        content[:lib_symbols_end] + 
                        '\n' + DEVICE_R_SYMBOL_DEF + 
                        content[lib_symbols_end:]
                    )
                    content = new_content
        
        # Find insertion point for symbol instance (before sheet_instances)
        sheet_instances_pos = content.find('\t(sheet_instances')
        if sheet_instances_pos == -1:
            sheet_instances_pos = content.find('\t(embedded_fonts')
        if sheet_instances_pos == -1:
            sheet_instances_pos = content.rfind(')')
        
        # Insert symbol instance
        new_content = (
            content[:sheet_instances_pos] + 
            symbol_instance + '\n' +
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


def remove_component_from_schematic_exact(
    file_path: Union[str, Path],
    reference: str
) -> bool:
    """
    Remove a component from an existing KiCad schematic file.
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
        # Look for the closing "\t)" that ends the symbol
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