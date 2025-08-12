"""
Simple atomic operations for KiCad schematic files.

Provides minimal functions to add/remove components from existing schematic files
without affecting other parts of the schematic.
"""

import logging
import shutil
import uuid
from pathlib import Path
from typing import Dict, Tuple, Union

import sexpdata

logger = logging.getLogger(__name__)


def add_component_to_schematic(
    file_path: Union[str, Path], 
    lib_id: str,
    reference: str,
    value: str = "",
    position: Tuple[float, float] = (100, 100),
    footprint: str = "",
    **properties
) -> bool:
    """
    Add a component to an existing KiCad schematic file.
    
    Args:
        file_path: Path to the .kicad_sch file
        lib_id: Library identifier (e.g., "Device:R")
        reference: Component reference (e.g., "R1")
        value: Component value (e.g., "10k")
        position: (x, y) position in mm
        footprint: Footprint identifier
        **properties: Additional component properties
        
    Returns:
        True if component was added successfully, False otherwise
    """
    file_path = Path(file_path)
    
    # Create backup
    backup_path = file_path.with_suffix('.kicad_sch.bak')
    try:
        shutil.copy2(file_path, backup_path)
        
        # Read the file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Create component data
        component_data = {
            'lib_id': lib_id,
            'reference': reference,
            'value': value,
            'position': position,
            'footprint': footprint,
            'uuid': str(uuid.uuid4()),
            **properties
        }
        
        # Add component using existing logic
        component_sexp = _create_component_sexp(component_data)
        
        # Parse S-expression
        data = sexpdata.loads(content)
        
        # Insert component before sheet_instances or symbol_instances
        insert_index = len(data)
        for i, item in enumerate(data):
            if (isinstance(item, list) and len(item) > 0 and 
                isinstance(item[0], sexpdata.Symbol) and 
                str(item[0]) in ["sheet_instances", "symbol_instances"]):
                insert_index = i
                break
        
        data.insert(insert_index, component_sexp)
        
        # Write back to file using standard sexpdata formatting
        formatted_content = sexpdata.dumps(data)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(formatted_content)
        
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


def remove_component_from_schematic(
    file_path: Union[str, Path],
    reference: str
) -> bool:
    """
    Remove a component from an existing KiCad schematic file.
    
    Args:
        file_path: Path to the .kicad_sch file
        reference: Component reference to remove (e.g., "R1")
        
    Returns:
        True if component was removed successfully, False otherwise
    """
    file_path = Path(file_path)
    
    # Create backup
    backup_path = file_path.with_suffix('.kicad_sch.bak')
    try:
        shutil.copy2(file_path, backup_path)
        
        # Read the file content
        with open(file_path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Parse S-expression
        data = sexpdata.loads(content)
        
        # Find and remove component
        removed = False
        for i, item in enumerate(data):
            if _is_symbol_with_reference(item, reference):
                del data[i]
                removed = True
                break
        
        if not removed:
            logger.warning(f"Component {reference} not found in {file_path}")
            return False
        
        # Write back to file using standard sexpdata formatting
        formatted_content = sexpdata.dumps(data)
        with open(file_path, 'w', encoding='utf-8') as f:
            f.write(formatted_content)
        
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


def _create_component_sexp(component_data: Dict) -> list:
    """Create S-expression for a component with proper KiCad formatting."""
    position = component_data.get('position', (100, 100))
    rotation = component_data.get('rotation', 0)
    
    # Create basic symbol structure with proper quoting
    symbol_sexp = [
        sexpdata.Symbol("symbol"),
        [sexpdata.Symbol("lib_id"), component_data['lib_id']],  # This will be quoted by sexpdata
        [sexpdata.Symbol("at"), position[0], position[1], rotation],
        [sexpdata.Symbol("unit"), component_data.get('unit', 1)],
        [sexpdata.Symbol("exclude_from_sim"), sexpdata.Symbol("no")],
        [sexpdata.Symbol("in_bom"), sexpdata.Symbol("yes")],
        [sexpdata.Symbol("on_board"), sexpdata.Symbol("yes")],
        [sexpdata.Symbol("dnp"), sexpdata.Symbol("no")],
        [sexpdata.Symbol("fields_autoplaced"), sexpdata.Symbol("yes")],
        [sexpdata.Symbol("uuid"), component_data['uuid']],
    ]
    
    # Add Reference property
    if component_data.get('reference'):
        ref_prop = [
            sexpdata.Symbol("property"), "Reference", component_data['reference'],
            [sexpdata.Symbol("at"), position[0], position[1] - 5, 0],
            [
                sexpdata.Symbol("effects"),
                [sexpdata.Symbol("font"), [sexpdata.Symbol("size"), 1.27, 1.27]],
                [sexpdata.Symbol("justify"), sexpdata.Symbol("left")]
            ]
        ]
        symbol_sexp.append(ref_prop)
    
    # Add Value property
    if component_data.get('value'):
        val_prop = [
            sexpdata.Symbol("property"), "Value", str(component_data['value']),
            [sexpdata.Symbol("at"), position[0], position[1] + 5, 0],
            [
                sexpdata.Symbol("effects"),
                [sexpdata.Symbol("font"), [sexpdata.Symbol("size"), 1.27, 1.27]],
                [sexpdata.Symbol("justify"), sexpdata.Symbol("left")]
            ]
        ]
        symbol_sexp.append(val_prop)
    
    # Add Footprint property
    if component_data.get('footprint'):
        fp_prop = [
            sexpdata.Symbol("property"), "Footprint", component_data['footprint'],
            [sexpdata.Symbol("at"), position[0], position[1], 0],
            [
                sexpdata.Symbol("effects"),
                [sexpdata.Symbol("font"), [sexpdata.Symbol("size"), 1.27, 1.27]],
                [sexpdata.Symbol("hide"), sexpdata.Symbol("yes")]
            ]
        ]
        symbol_sexp.append(fp_prop)
    
    return symbol_sexp


def _is_symbol_with_reference(item, reference: str) -> bool:
    """Check if an S-expression item is a symbol with the given reference."""
    if not (isinstance(item, list) and len(item) > 0):
        return False
        
    # Check if this is a symbol
    if not (isinstance(item[0], sexpdata.Symbol) and str(item[0]) == "symbol"):
        return False
        
    # Look for property with Reference
    for subitem in item[1:]:
        if (isinstance(subitem, list) and len(subitem) >= 3 and
            isinstance(subitem[0], sexpdata.Symbol) and 
            str(subitem[0]) == "property" and
            len(subitem) >= 3 and str(subitem[1]) == "Reference" and
            str(subitem[2]) == reference):
            return True
    
    return False


