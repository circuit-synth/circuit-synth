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

        uuid_pattern = (
            r'\(uuid "([0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12})"\)'
        )
        match = re.search(uuid_pattern, content)
        if match:
            return match.group(1)
        else:
            return "00000000-0000-0000-0000-000000000000"
    except:
        return "00000000-0000-0000-0000-000000000000"


# Full Device:R symbol definition matching reference exactly
def manage_lib_symbols(content: str, lib_id: str, operation: str) -> str:
    """
    Intelligent management of lib_symbols section.

    Args:
        content: The schematic file content
        lib_id: The library ID (e.g., "Device:R")
        operation: "add" or "remove"

    Returns:
        Updated content with proper lib_symbols management
    """
    # Count how many instances of this lib_id exist in the content
    lib_usage_count = content.count(f'lib_id "{lib_id}"')

    # Check if lib_symbols definition exists
    lib_symbols_start = content.find("\t(lib_symbols")
    if lib_symbols_start == -1:
        return content

    lib_symbols_end = content.find("\n\t)", lib_symbols_start)
    if lib_symbols_end == -1:
        return content

    lib_symbols_content = content[lib_symbols_start:lib_symbols_end]
    has_definition = f'"{lib_id}"' in lib_symbols_content

    if operation == "add":
        # Add definition if this is the first instance and definition doesn't exist
        if lib_usage_count >= 1 and not has_definition and lib_id == "Device:R":
            # Insert Device:R definition
            updated_content = (
                content[:lib_symbols_end]
                + "\n"
                + DEVICE_R_SYMBOL_DEF
                + content[lib_symbols_end:]
            )
            return updated_content

    elif operation == "remove":
        # Remove definition if no more instances exist and definition exists
        if lib_usage_count == 0 and has_definition and lib_id == "Device:R":
            # Find and remove the Device:R symbol definition
            symbol_def_start = lib_symbols_content.find('\t\t(symbol "Device:R"')
            if symbol_def_start != -1:
                # Adjust for absolute position in content
                abs_symbol_start = lib_symbols_start + symbol_def_start

                # Find the end of this symbol definition using bracket counting
                paren_count = 0
                pos = abs_symbol_start
                in_symbol = False

                while pos < len(content):
                    if content[pos] == "(":
                        paren_count += 1
                        in_symbol = True
                    elif content[pos] == ")" and in_symbol:
                        paren_count -= 1
                        if paren_count == 0:
                            # Found the end, include newline
                            pos += 1
                            if pos < len(content) and content[pos] == "\n":
                                pos += 1
                            break
                    pos += 1

                if paren_count == 0:
                    # Remove the definition
                    updated_content = content[:abs_symbol_start] + content[pos:]
                    return updated_content

    return content


DEVICE_R_SYMBOL_DEF = """		(symbol "Device:R"
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
		)"""


def add_component_to_schematic_exact(
    file_path: Union[str, Path],
    lib_id: str,
    reference: str,
    value: str = "",
    position: Tuple[float, float] = (100, 100),
    footprint: str = "",
    **properties,
) -> bool:
    """
    Add a component to an existing KiCad schematic file with exact reference formatting.
    """
    file_path = Path(file_path)

    # Create backup
    backup_path = file_path.with_suffix(".kicad_sch.bak")
    try:
        shutil.copy2(file_path, backup_path)

        # Read the file content
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Generate UUIDs for component
        component_uuid = str(uuid.uuid4())
        pin1_uuid = str(uuid.uuid4())
        pin2_uuid = str(uuid.uuid4())
        schematic_uuid = extract_uuid(content)

        # Create component symbol instance matching reference format exactly
        symbol_instance = f"""	(symbol
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
			(at {position[0] + 2.54} {position[1] - 1.2701} 0)
			(effects
				(font
					(size 1.27 1.27)
				)
				(justify left)
			)
		)
		(property "Value" "{value}"
			(at {position[0] + 2.54} {position[1] + 1.2799} 0)
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
	)"""

        # Find insertion point for symbol instance (before sheet_instances)
        sheet_instances_pos = content.find("\t(sheet_instances")
        if sheet_instances_pos == -1:
            sheet_instances_pos = content.find("\t(embedded_fonts")
        if sheet_instances_pos == -1:
            sheet_instances_pos = content.rfind(")")

        # Insert symbol instance
        new_content = (
            content[:sheet_instances_pos]
            + symbol_instance
            + "\n"
            + content[sheet_instances_pos:]
        )

        # Intelligent lib_symbols management AFTER component is added
        new_content = manage_lib_symbols(new_content, lib_id, "add")

        # Write back to file
        with open(file_path, "w", encoding="utf-8") as f:
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
    file_path: Union[str, Path], reference: str
) -> bool:
    """
    Remove a component from an existing KiCad schematic file.
    Ensures proper lib_symbols and sheet_instances sections remain.
    """
    file_path = Path(file_path)

    # Create backup
    backup_path = file_path.with_suffix(".kicad_sch.bak")
    try:
        shutil.copy2(file_path, backup_path)

        # Read the file content
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        # Find ALL instances of the reference component
        ref_pattern = f'"Reference" "{reference}"'
        remaining_content = content
        components_removed = 0

        while ref_pattern in remaining_content:
            ref_pos = remaining_content.find(ref_pattern)
            if ref_pos == -1:
                break

            # Find the start of the symbol block (go backwards to find "(symbol")
            symbol_start = remaining_content.rfind("\t(symbol", 0, ref_pos)
            if symbol_start == -1:
                logger.error(f"Could not find symbol start for {reference}")
                break

            # Find the end of the symbol block using proper S-expression parsing
            # Count nested parentheses to find the correct closing paren
            paren_count = 0
            symbol_end = symbol_start
            in_symbol = False

            while symbol_end < len(remaining_content):
                if remaining_content[symbol_end] == "(":
                    paren_count += 1
                    in_symbol = True
                elif remaining_content[symbol_end] == ")" and in_symbol:
                    paren_count -= 1
                    if paren_count == 0:
                        # Found the closing paren for this symbol
                        symbol_end += 1
                        break
                symbol_end += 1

            if paren_count != 0:
                logger.error(f"Could not find proper symbol end for {reference}")
                break

            # Remove this symbol block
            remaining_content = (
                remaining_content[:symbol_start] + remaining_content[symbol_end:]
            )
            components_removed += 1

            # Look for any trailing newline after the removed component
            if (
                symbol_start < len(remaining_content)
                and remaining_content[symbol_start] == "\n"
            ):
                remaining_content = (
                    remaining_content[:symbol_start]
                    + remaining_content[symbol_start + 1 :]
                )

        if components_removed == 0:
            logger.warning(f"Component {reference} not found in {file_path}")
            return False

        # Intelligent lib_symbols management after removal
        remaining_content = manage_lib_symbols(remaining_content, "Device:R", "remove")

        # Ensure sheet_instances section exists
        if "\t(sheet_instances" not in remaining_content:
            # Add sheet_instances before embedded_fonts
            embedded_fonts_pos = remaining_content.find("\t(embedded_fonts")
            if embedded_fonts_pos != -1:
                sheet_instances_section = (
                    '\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "1")\n\t\t)\n\t)\n'
                )
                remaining_content = (
                    remaining_content[:embedded_fonts_pos]
                    + sheet_instances_section
                    + remaining_content[embedded_fonts_pos:]
                )
            else:
                # Add before final closing paren
                final_paren = remaining_content.rfind(")")
                if final_paren != -1:
                    sheet_instances_section = '\t(sheet_instances\n\t\t(path "/"\n\t\t\t(page "1")\n\t\t)\n\t)\n\t(embedded_fonts\n\t\tno\n\t)\n'
                    remaining_content = (
                        remaining_content[:final_paren] + sheet_instances_section + ")"
                    )

        # Write back to file
        with open(file_path, "w", encoding="utf-8") as f:
            f.write(remaining_content)

        logger.info(
            f"Removed {components_removed} instances of component {reference} from {file_path}"
        )
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
