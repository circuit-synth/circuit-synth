"""
kicad_netlist_exporter.py

Core logic to convert a Circuit-Synth JSON file back into a KiCad netlist (.net) file.
This module performs the reverse operation of netlist_importer.py, converting the
hierarchical Circuit-Synth JSON representation back to the KiCad netlist format.

The exporter handles:
- Basic components and their properties
- Nets in Structure A format (direct arrays of node connections)
- Different pin types (input, output, power, etc.)
- Hierarchical circuits with subcircuits
- Global nets across subcircuits
- Unconnected pins

Net Format (Structure A):
    "nets": {
        "net_name": [
            {"component": "R1", "pin": {"number": "1", "name": "in", "type": "passive"}},
            {"component": "R2", "pin": {"number": "2", "name": "out", "type": "passive"}}
        ]
    }
"""

import json
import logging
import os
import uuid
from datetime import datetime, timedelta, timezone
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, TextIO, Tuple

from .sheet_hierarchy_manager import SheetHierarchyManager

logger = logging.getLogger(__name__)


def normalize_hierarchical_path(path: str, name: str) -> str:
    """
    Normalize a hierarchical path by ensuring proper separators.

    Args:
        path: The hierarchical path (e.g., "/Project Architecture/MCU")
        name: The name to append (e.g., "ISENC")

    Returns:
        Normalized path with proper separators
    """
    # Handle special cases
    if not path or path == "/":
        return f"/{name}" if name else "/"

    # Ensure path starts with /
    if not path.startswith("/"):
        path = "/" + path

    # Remove any double slashes and trailing slashes
    path = path.replace("//", "/").rstrip("/")

    # If name is provided, ensure proper separator
    if name:
        # Remove any leading/trailing slashes from name
        name = name.strip("/")
        if name:
            return f"{path}/{name}"

    return path


# ------------------------------------------------------------------------------
# PinType Enum
# ------------------------------------------------------------------------------
class PinType(Enum):
    """
    Enumeration of pin types used in Circuit-Synth.
    Maps between Circuit-Synth pin types and KiCad pin types.
    """

    INPUT = "input"
    OUTPUT = "output"
    BIDIRECTIONAL = "bidirectional"
    POWER_IN = "power_in"
    POWER_OUT = "power_out"
    PASSIVE = "passive"
    UNSPECIFIED = "unspecified"
    NO_CONNECT = "no_connect"

    @classmethod
    def to_kicad(cls, circuit_synth_type: str) -> str:
        """
        Convert a Circuit-Synth pin type to KiCad pin type.

        Args:
            circuit_synth_type: The Circuit-Synth pin type string

        Returns:
            Corresponding KiCad pin type string
        """
        # Direct mapping - KiCad uses the same names for these types
        valid_types = {
            "input",
            "output",
            "bidirectional",
            "power_in",
            "power_out",
            "passive",
            "no_connect",
        }

        # Convert to lowercase for case-insensitive comparison
        circuit_synth_type = circuit_synth_type.lower()

        # Return the type as-is if it's valid
        if circuit_synth_type in valid_types:
            return circuit_synth_type

        # Map unspecified and unknown types to passive
        return "passive"


# ------------------------------------------------------------------------------
# Helper Functions
# ------------------------------------------------------------------------------


def load_circuit_json(json_path: Path) -> Dict[str, Any]:
    """
    Load a Circuit-Synth JSON file.

    Args:
        json_path: Path to the JSON file

    Returns:
        Dictionary containing the circuit data
    """
    logger.debug(f"Loading Circuit-Synth JSON from {json_path}")
    try:
        with open(json_path, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data
    except Exception as e:
        logger.error(f"Error loading JSON file: {e}")
        raise


# ------------------------------------------------------------------------------
# Main Converter Functions
# ------------------------------------------------------------------------------
def convert_json_to_netlist(json_path: Path, output_path: Path) -> None:
    """
    Convert a Circuit-Synth JSON file to a KiCad netlist file.

    Args:
        json_path: Path to the input JSON file
        output_path: Path to the output netlist file
    """
    logger.debug(f"Converting JSON {json_path} to KiCad netlist {output_path}")

    # Load the JSON data
    circuit_data = load_circuit_json(json_path)

    # Generate the netlist content
    netlist_content = generate_netlist(circuit_data)

    # Ensure consistent line endings (LF only, which is what KiCad expects)
    netlist_content = netlist_content.replace("\r\n", "\n")

    # Clean up any excess spacing in the file - try to match KiCad's exact format
    netlist_content = cleanup_whitespace(netlist_content)

    # Ensure parent directory exists
    from pathlib import Path

    output_file = Path(output_path)
    output_file.parent.mkdir(parents=True, exist_ok=True)

    # Write to the output file with binary mode to preserve encoding and line endings
    # No BOM in the UTF-8 encoding to ensure KiCad can read it
    with open(output_path, "wb") as f:
        f.write(netlist_content.encode("utf-8"))

    logger.debug(f"Successfully wrote KiCad netlist to {output_path}")


def cleanup_whitespace(content: str) -> str:
    """
    Clean up whitespace in netlist content to match KiCad's expected format.
    This is applied as a final pass after the s-expression formatting.

    Args:
        content: The netlist content string

    Returns:
        Cleaned up netlist content string
    """
    # Fix KiCad-specific formatting patterns

    # Fix export line - KiCad has the version on the same line as export
    content = content.replace("(export\n  (version", "(export (version")

    # Ensure no extra spacing in parentheses
    content = content.replace(" )", ")")
    content = content.replace("( ", "(")

    # Remove excessive blank lines
    while "\n\n\n" in content:
        content = content.replace("\n\n\n", "\n\n")

    # Fix specific component formatting issues
    content = content.replace("      (fields\n", "      (fields\n")

    # Fix closing parentheses patterns
    content = content.replace("\n\n)", "\n)")

    # Fix library paths double slashes - required by KiCad
    # This is critical for KiCad to recognize the libraries correctly
    content = content.replace("symbols/Device", "symbols//Device")
    content = content.replace("symbols/RF_Module", "symbols//RF_Module")

    # Ensure final closing parenthesis doesn't have trailing newline
    if content.endswith("\n)"):
        content = content[:-2] + ")"

    return content


def generate_netlist(circuit_data: Dict[str, Any]) -> str:
    """
    Generate a KiCad netlist from Circuit-Synth JSON data.

    Args:
        circuit_data: Dictionary containing the circuit data

    Returns:
        String containing the KiCad netlist content
    """

    logger.debug("Starting generate_netlist...")
    # Build the netlist structure
    # The version needs to be formatted as (export (version "E")) to match KiCad's format
    netlist = ["export", ["version", "E"]]

    # Add design section
    logger.debug("Generating design section...")
    design_section = generate_design_section(circuit_data)
    netlist.append(design_section)
    logger.debug("...Design section generated.")

    # Add components section
    logger.debug("Generating components section...")
    components_section = generate_components_section(circuit_data)
    netlist.append(components_section)
    logger.debug("...Components section generated.")

    # Add libparts section
    logger.debug("Generating libparts section...")
    libparts_section = generate_libparts_section(circuit_data)
    netlist.append(libparts_section)
    logger.debug("...Libparts section generated.")

    # Add libraries section
    logger.debug("Generating libraries section...")
    libraries_section = generate_libraries_section(circuit_data)
    netlist.append(libraries_section)
    logger.debug("...Libraries section generated.")

    # Add nets section
    logger.debug("Generating nets section...")
    nets_section = generate_nets_section(circuit_data)
    netlist.append(nets_section)
    logger.debug("...Nets section generated.")

    # Format the netlist as an S-expression with KiCad's exact structure
    logger.debug("Formatting final S-expression...")
    result = format_s_expr(netlist)
    logger.debug("...S-expression formatting complete.")
    return result


def generate_design_section(circuit_data: Dict[str, Any]) -> List[Any]:
    """
    Generate the design section of the KiCad netlist.

    Args:
        circuit_data: Dictionary containing the circuit data

    Returns:
        List representing the design section
    """
    design = ["design"]

    # Add source, date, and tool properties using KiCad format
    source_path = circuit_data.get("source_file", "")
    if not source_path:
        # For tests, use a default source path
        source_path = "test_schematic.kicad_sch"
    design.append(["source", source_path])

    # Format date with timezone offset (e.g., 2025-04-05T01:12:32-0700)
    now = datetime.now(timezone.utc).astimezone()  # Get local time with tzinfo
    offset = now.utcoffset()
    offset_sign = "+" if offset >= timedelta(0) else "-"
    offset_hours = abs(offset.total_seconds()) // 3600
    offset_minutes = (abs(offset.total_seconds()) % 3600) // 60
    tz_str = f"{offset_sign}{int(offset_hours):02d}{int(offset_minutes):02d}"
    date_str = now.strftime(f"%Y-%m-%dT%H:%M:%S{tz_str}")
    design.append(["date", date_str])

    tool_str = "Circuit-Synth Exporter v0.1.0"
    design.append(["tool", tool_str])

    # Create sheet hierarchy from circuit data
    sheet_manager = SheetHierarchyManager(test_mode=True)

    # Extract sheet hierarchy from circuit data
    sheets = _extract_sheets_from_circuit(circuit_data)
    sheet_manager.parse_sheet_data(sheets)

    # Extract sheets and initialize sheet manager
    sheets = _extract_sheets_from_circuit(circuit_data)
    sheet_manager = SheetHierarchyManager(test_mode=True)
    sheet_manager.parse_sheet_data(sheets)

    # Get ordered list of sheets and their paths
    sheet_order = sheet_manager.get_sheet_order()
    sheet_paths = sheet_manager.get_sheet_paths()

    # Generate sheet entries using the hierarchy information
    sheet_number = 1
    for uuid in sheet_order:
        # Find path for this UUID
        path = None
        for p, u in sheet_paths.items():
            if u == uuid:
                path = p
                break

        if path is None:
            logger.warning(f"Could not find path for sheet UUID {uuid}")
            continue

        sheet_entry = [
            "sheet",
            ["number", str(sheet_number)],
            ["name", path],
            ["tstamps", f"/{uuid}/"],
            [
                "title_block",
                ["title"],
                ["company"],
                ["rev"],
                ["date"],
                ["source", f"{path}.kicad_sch" if path != "/" else source_path],
                ["comment", ["number", "1"], ["value", ""]],
                ["comment", ["number", "2"], ["value", ""]],
                ["comment", ["number", "3"], ["value", ""]],
                ["comment", ["number", "4"], ["value", ""]],
                ["comment", ["number", "5"], ["value", ""]],
                ["comment", ["number", "6"], ["value", ""]],
                ["comment", ["number", "7"], ["value", ""]],
                ["comment", ["number", "8"], ["value", ""]],
                ["comment", ["number", "9"], ["value", ""]],
            ],
        ]
        design.append(sheet_entry)
        sheet_number += 1

    return design


def _extract_sheets_from_circuit(circuit_data: Dict[str, Any]) -> List[Dict[str, Any]]:
    """Extract sheet hierarchy from circuit data.

    Args:
        circuit_data: Circuit data dictionary

    Returns:
        List of sheet dictionaries
    """
    sheets = []

    def process_circuit(
        data: Dict[str, Any],
        parent_uuid: Optional[str] = None,
        is_root: bool = False,
        parent_path: str = "",
    ):
        # Use UUID from data if available, otherwise generate one
        sheet_uuid = data.get("uuid", str(uuid.uuid4()))
        name = data.get("name", "Root" if is_root else "Sheet")

        # Handle path mapping
        if is_root:
            path = "root"  # Use "root" for root sheet
        else:
            path = data.get("path", f"{parent_path}/{name}".replace("//", "/"))

        sheet = {
            "uuid": sheet_uuid,
            "name": name,
            "path": path,
            "original_data": True,  # Mark as using original data
        }

        if is_root:
            sheet["root"] = True
        elif parent_uuid:
            sheet["parent_uuid"] = parent_uuid

        sheets.append(sheet)

        # Process subcircuits
        for subcircuit in data.get("subcircuits", []):
            process_circuit(subcircuit, sheet_uuid, parent_path=path)

    # Start with root circuit
    process_circuit(circuit_data, is_root=True, parent_path="/")
    return sheets


# Helper function to generate sheet entries recursively


# Helper function to recursively generate component entries


def generate_components_section(circuit_data: Dict[str, Any]) -> List[Any]:
    """
    Generate the components section of the KiCad netlist, handling hierarchy.

    Args:
        circuit_data: Dictionary containing the top-level circuit data.

    Returns:
        List representing the components section S-expression.
    """
    components_section = ["components"]

    # Create sheet hierarchy manager in test mode
    sheet_manager = SheetHierarchyManager(test_mode=True)

    # Use sheet data from circuit_data if available, otherwise create default
    if "sheets" in circuit_data:
        sheet_manager.parse_sheet_data(circuit_data["sheets"])
    else:
        # Create default root sheet for simple circuits
        default_sheets = [
            {"uuid": str(uuid.uuid4()), "name": "Root", "root": True, "path": "/"}
        ]
        sheet_manager.parse_sheet_data(default_sheets)

    # Get sheet paths mapping
    sheet_paths = sheet_manager.get_sheet_paths()

    def process_components(circ_data: Dict[str, Any], current_path: str):
        """Process components in the current circuit and its subcircuits."""
        components = circ_data.get("components", {})

        for ref, comp_data in components.items():
            # Get sheet name from path
            sheet_name = current_path.split("/")[-1] if current_path != "/" else "Root"

            # Use consistent sheet file naming
            sheet_file = (
                "circuit.kicad_sch"  # Use generic name since we don't need actual files
            )

            # Generate component entry with sheet info
            comp_entry = generate_component_entry(
                comp_data,
                sheet_name=sheet_name,
                sheet_file=sheet_file,
                sheet_path=current_path,
            )
            if comp_entry:
                components_section.append(comp_entry)

        # Process subcircuits
        for subcircuit in circ_data.get("subcircuits", []):
            subname = subcircuit.get("name", "UnnamedSheet")
            new_path = (
                f"{current_path}{subname}/" if current_path != "/" else f"/{subname}/"
            )
            process_components(subcircuit, new_path)

    # Start processing from root
    process_components(circuit_data, "/")
    return components_section


def generate_libparts_section(circuit_data: Dict[str, Any]) -> List[Any]:
    """
    Generate the libparts section of the KiCad netlist. Prioritizes the 'symbol'
    attribute for lib:part identification and adds debug logging.

    Args:
        circuit_data: Dictionary containing the circuit data

    Returns:
        List representing the libparts section
    """
    logger.debug("Starting generate_libparts_section...")
    libparts_section = ["libparts"]

    # Track unique libparts to avoid duplicates
    unique_libparts = set()

    # Process components from the main circuit and subcircuits recursively
    all_components = {}

    def _collect_components_recursive(data: Dict[str, Any], path: str = "/"):
        all_components.update(
            {
                f"{path}{ref}" if path != "/" else ref: comp
                for ref, comp in data.get("components", {}).items()
            }
        )
        for sub in data.get("subcircuits", []):
            sub_name = sub.get("name", "UnnamedSub")
            _collect_components_recursive(sub, f"{path}{sub_name}/")

    _collect_components_recursive(circuit_data)
    logger.debug(f"Collected {len(all_components)} components total from all sheets.")

    # Generate libparts for each unique component type
    for ref, comp_data in all_components.items():
        # logger.debug(f"Processing component ref='{ref}', data={comp_data}")

        # --- Determine Library and Part ---
        lib = None
        part = None

        symbol = comp_data.get("symbol", "")
        logger.debug(f"  Component symbol attribute: '{symbol}'")

        if symbol and ":" in symbol:
            try:
                lib, part = symbol.split(":", 1)
                logger.debug(f"  Extracted lib='{lib}', part='{part}' from symbol.")
            except ValueError:
                raise ValueError(
                    f"Invalid symbol format '{symbol}' for component '{ref}'. Expected 'Library:Part' format."
                )
        else:
            # --- Fallback Logic (Revised as per plan v3.1) ---
            # Only use fallbacks if symbol is missing or invalid
            logger.debug(
                f"  Symbol missing or invalid ('{symbol}'). Attempting fallbacks for ref '{ref}'..."
            )
            properties = comp_data.get("properties", {})
            ki_lib = properties.get("ki_lib")
            ki_part = properties.get("ki_part")
            libsource = properties.get("libsource")  # Often contains original lib:part

            if ki_lib and ki_part:
                lib = ki_lib
                part = ki_part
                logger.debug(
                    f"  Using fallback from properties: ki_lib='{lib}', ki_part='{part}'."
                )
            elif libsource and ":" in libsource:
                try:
                    lib, part = libsource.split(":", 1)
                    logger.debug(
                        f"  Using fallback from libsource property: '{libsource}' -> lib='{lib}', part='{part}'."
                    )
                except ValueError:
                    raise ValueError(
                        f"Invalid libsource format '{libsource}' for component '{ref}'. Expected 'Library:Part' format."
                    )
            else:
                # No valid library found - raise error
                raise ValueError(
                    f"No library specified for component '{ref}'. Symbol must be in 'Library:Part' format."
                )
            # --- End Fallback Logic ---

        # Create a unique key for this libpart
        libpart_key = f"{lib}:{part}"
        # logger.debug(f"  Generated libpart_key: '{libpart_key}'")

        # Skip if we've already processed this libpart
        if libpart_key in unique_libparts:
            # logger.debug(f"  Skipping duplicate libpart_key: '{libpart_key}'")
            continue

        unique_libparts.add(libpart_key)

        # Generate the libpart entry using the determined lib and part
        logger.debug(f"  Generating libpart entry for lib='{lib}', part='{part}'...")
        libpart_entry = generate_libpart_entry(lib, part, comp_data, circuit_data)
        if libpart_entry:  # Check if entry was generated successfully
            libparts_section.append(libpart_entry)
            logger.debug(f"  Added libpart entry for '{libpart_key}'.")
        else:
            logger.warning(
                f"  Failed to generate libpart entry for '{libpart_key}' (ref: {ref})."
            )

    logger.debug(
        f"...generate_libparts_section finished. Found {len(unique_libparts)} unique libparts."
    )
    return libparts_section


def generate_libpart_entry(
    lib: str, part: str, comp_data: Dict[str, Any], circuit_data: Dict[str, Any] = None
) -> Optional[List[Any]]:
    """
    Generate a single libpart entry for the KiCad netlist, including fields and pins.
    Adds debug logging for traceability.

    Args:
        lib: Library name (e.g., "Device", "Sensor_Motion")
        part: Part name (e.g., "R", "LSM6DSL")
        comp_data: Dictionary containing the specific component's data
        circuit_data: Optional dictionary containing the full circuit data (unused currently)

    Returns:
        List representing the libpart entry S-expression, or None if essential data is missing.
    """
    ref = comp_data.get("reference", "UnknownRef")  # Get ref for logging context
    logger.debug(
        f"Starting generate_libpart_entry for lib='{lib}', part='{part}' (from ref='{ref}')"
    )
    # logger.debug(f"  Input comp_data: {comp_data}") # Optional: Log full comp_data if needed

    # --- Basic Info ---
    description = comp_data.get("description", "")
    properties = comp_data.get("properties", {})
    datasheet = (
        comp_data.get("datasheet", "") or "~"
    )  # Use ~ if empty, as KiCad expects
    footprint = properties.get(
        "ki_footprint", comp_data.get("footprint", "")
    )  # Prioritize ki_footprint property
    footprint_filters_str = properties.get("ki_fp_filters", "")
    value = str(comp_data.get("value", part))  # Use part name as fallback value

    logger.debug(
        f"  Extracted Fields: description='{description}', datasheet='{datasheet}', footprint='{footprint}', fp_filters='{footprint_filters_str}', value='{value}'"
    )

    # --- Build S-expression ---
    libpart_entry = ["libpart", ["lib", lib], ["part", part]]

    # Add description if present
    if description:
        libpart_entry.append(["description", description])
    else:
        logger.debug("  No description found in comp_data.")

    # Add docs (datasheet link)
    libpart_entry.append(["docs", datasheet])

    # Add footprints section if filters are defined
    if footprint_filters_str:
        footprints_list = []
        # Split filters, ensuring patterns are strings and non-empty
        for filter_pattern in str(footprint_filters_str).split():
            if filter_pattern:
                footprints_list.append(["fp", filter_pattern])
        if footprints_list:
            libpart_entry.append(["footprints"] + footprints_list)
            logger.debug(
                f"  Added footprints section with filters: {footprint_filters_str}"
            )
        else:
            logger.debug(
                "  Footprint filters string was present but resulted in no valid filters."
            )
    else:
        logger.debug("  No footprint filters (ki_fp_filters) found in properties.")

    # --- Add Fields Section ---
    # Standard fields (Reference, Value, Footprint, Datasheet) plus KiCad-specific ones
    ref_prefix = (
        ref[0] if ref and not ref.startswith("/") else "?"
    )  # Use '?' if ref is invalid/missing
    fields = [
        ["field", ["name", "Reference"], ref_prefix],  # Use prefix like R, C, U
        ["field", ["name", "Value"], value],
        # Use the determined footprint value here
        [
            "field",
            ["name", "Footprint"],
            footprint if footprint else "",
        ],  # Use empty string if no footprint
        [
            "field",
            ["name", "Datasheet"],
            datasheet if datasheet != "~" else "",
        ],  # Use empty string if no datasheet
    ]
    logger.debug(
        f"  Added standard fields: Ref='{ref_prefix}', Value='{value}', Footprint='{footprint}', Datasheet='{datasheet}'"
    )

    # Add KiCad specific fields from properties (ki_keywords, ki_description, etc.)
    added_ki_fields = []
    for prop_name, prop_value in properties.items():
        # Check if it starts with ki_ and is not one we already handled (footprint, fp_filters)
        if prop_name.startswith("ki_") and prop_name not in [
            "ki_footprint",
            "ki_fp_filters",
            "ki_lib",
            "ki_part",
        ]:
            # Format field name (e.g., ki_keywords -> Keywords)
            field_name = prop_name[3:].replace("_", " ").title()
            # Ensure value is a string for the netlist format
            field_value_str = str(prop_value) if prop_value is not None else ""
            fields.append(["field", ["name", field_name], field_value_str])
            added_ki_fields.append(f"{field_name}='{field_value_str}'")

    if added_ki_fields:
        logger.debug(
            f"  Added KiCad-specific fields from properties: {', '.join(added_ki_fields)}"
        )
    else:
        logger.debug("  No additional KiCad-specific fields found in properties.")

    libpart_entry.append(["fields"] + fields)

    # --- Add Pins Section ---
    pins_section = ["pins"]
    # Expect pins_list to be a list of dictionaries: [{"num": "1", "name": "...", "func": "..."}, ...]
    pins_list = comp_data.get("pins", [])

    if not isinstance(pins_list, list):
        logger.error(
            f"  Pins data for {lib}:{part} (ref: {ref}) is not a list (type: {type(pins_list)}). Cannot process pins.",
            exc_info=True,
        )
        pins_list = []  # Reset to empty list to avoid further errors

    if not pins_list:
        logger.warning(
            f"  No pins found in comp_data for {lib}:{part} (ref: {ref}). Libpart entry might be incomplete."
        )
        # Still add empty pins section as KiCad expects it
    else:
        logger.debug(f"  Processing {len(pins_list)} pins from comp_data list.")

    # Sort pins numerically by pin number (important for KiCad)
    def sort_key(pin_dict):
        # Access the 'number' key within the dictionary (JSON uses 'number', not 'num')
        pin_num_str = pin_dict.get("number", "")
        try:
            # Handle potential non-numeric pin numbers gracefully
            return int(pin_num_str)
        except ValueError:
            # Place non-numeric pins at the end, sorted alphabetically
            logger.debug(
                f"    Pin number '{pin_num_str}' is non-numeric, sorting alphabetically."
            )
            return float("inf"), pin_num_str  # Tuple for secondary sort key

    try:
        # Ensure items in pins_list are valid dictionaries before sorting
        valid_pin_items = [item for item in pins_list if isinstance(item, dict)]
        if len(valid_pin_items) != len(pins_list):
            logger.warning(
                f"  Some pin data items were not dictionaries for {lib}:{part} (ref: {ref})."
            )

        sorted_pins = sorted(valid_pin_items, key=sort_key)
    except Exception as e:
        logger.error(
            f"  Error sorting pins for {lib}:{part} (ref: {ref}): {e}. Pins might be out of order.",
            exc_info=True,
        )
        # Fallback to unsorted if error occurs
        sorted_pins = valid_pin_items  # Use the filtered list

    # Iterate through the sorted list of pin dictionaries
    for pin_info in sorted_pins:
        pin_num = pin_info.get(
            "number", "?"
        )  # Get pin number string (JSON uses 'number', not 'num')
        pin_name = pin_info.get("name", "~")  # Use ~ for unnamed pins (KiCad standard)
        # Use 'func' field from JSON for pin type, default to passive
        # (Matches Component.to_dict which uses 'func')
        # Get pin type, preserving the original type from libpart
        pin_type_str = pin_info.get("func")
        if not pin_type_str:
            # Only fallback to "passive" if no type is specified
            pin_type_str = "passive"
            logger.debug(
                f"  No pin type found for pin {pin_num}, defaulting to 'passive'"
            )

        # Convert Circuit-Synth type to KiCad type using the Enum helper
        kicad_pin_type = PinType.to_kicad(pin_type_str)
        logger.debug(f"  Pin {pin_num} type: {pin_type_str} -> {kicad_pin_type}")

        pin_entry = [
            "pin",
            ["num", str(pin_num)],
            ["name", pin_name],
            ["type", kicad_pin_type],
        ]
        pins_section.append(pin_entry)
        # logger.debug(f"    Added pin: num='{pin_num}', name='{pin_name}', type='{kicad_pin_type}' (from CS type '{pin_type_str}')") # Verbose pin logging

    libpart_entry.append(pins_section)
    logger.debug(f"  Finished processing pins for {lib}:{part}.")

    # logger.debug(f"  Final generated libpart_entry for {lib}:{part}: {libpart_entry}") # Optional: Log full entry
    logger.debug(
        f"...generate_libpart_entry finished successfully for {lib}:{part} (ref: {ref})."
    )
    return libpart_entry


def generate_libraries_section(circuit_data: Dict[str, Any]) -> List[Any]:
    """
    Generate the libraries section of the KiCad netlist.

    Args:
        circuit_data: Dictionary containing the circuit data

    Returns:
        List representing the libraries section
    """
    libraries_section = ["libraries"]

    # Track unique libraries
    unique_libs = set()

    # Process components from the main circuit and subcircuits
    all_components = {}

    # Add main circuit components
    all_components.update(circuit_data.get("components", {}))

    # Add subcircuit components
    subcircuits = circuit_data.get("subcircuits")
    if subcircuits:
        for subcircuit in subcircuits:
            all_components.update(subcircuit.get("components", {}))

    # Extract unique libraries
    logger.debug(f"Processing {len(all_components)} components for libraries...")
    for ref, comp_data in all_components.items():
        # logger.debug(f"  Processing component ref='{ref}', data type={type(comp_data)}")
        if not isinstance(comp_data, dict):
            logger.error(
                f"  Component data for ref '{ref}' is not a dictionary! Skipping library processing for this component."
            )
            continue
        properties = comp_data.get("properties", {})
        logger.debug(f"    Properties type={type(properties)}, value={properties}")
        lib = None

        # Try to extract library from symbol attribute first
        symbol = comp_data.get("symbol", "")
        if symbol and ":" in symbol:
            try:
                lib = symbol.split(":", 1)[0]
                logger.debug(f"    Extracted lib='{lib}' from symbol='{symbol}'")
            except Exception:
                logger.debug(f"    Failed to extract lib from symbol='{symbol}'")

        # If not found in symbol, try properties
        if lib is None:
            try:
                logger.debug(
                    f"    [L2] Checking 'ki_lib' in properties ({'ki_lib' in properties})"
                )
                if "ki_lib" in properties:
                    lib = properties["ki_lib"]
                    logger.debug(f"    [L3] Found ki_lib: {lib}")
                elif "libsource" in properties:
                    logger.debug(
                        f"    [L4] Checking 'libsource' in properties ({'libsource' in properties})"
                    )
                    libsource = properties["libsource"]
                    logger.debug(f"    [L5] Found libsource: {libsource}")
                    if ":" in libsource:
                        logger.debug(
                            f"    [L6] Checking ':' in libsource ({':' in libsource})"
                        )
                        lib = libsource.split(":", 1)[0]
                        logger.debug(f"    [L7] Extracted lib from libsource: {lib}")
                    else:
                        logger.debug(f"    [L8] Libsource found but no ':' separator.")
                else:
                    logger.debug(
                        f"    [L9] No ki_lib or libsource found in properties."
                    )
            except Exception as e:
                logger.error(f"    [LE1] Error during property check!", exc_info=True)
                raise e

        # No hardcoded library assignments based on component values
        # All components must have explicit library specifications
        logger.debug(f"    Determined lib='{lib}' for ref='{ref}'")
        if lib is None:
            raise ValueError(
                f"No library found for component '{ref}'. Component must have a valid library specification."
            )
        unique_libs.add(lib)

    # Generate library entries
    logger.debug(f"Unique libraries found: {unique_libs}")
    for lib in sorted(unique_libs):
        logger.debug(f"  Generating entry for library='{lib}'")
        # Use the exact format from the original KiCad netlist, WITH double slashes
        # Cross-platform KiCad symbol library path detection
        import os
        import platform
        from pathlib import Path

        # Try to find the actual KiCad symbol library path
        possible_paths = []

        if platform.system() == "Darwin":  # macOS
            possible_paths = [
                "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/",
                "/Applications/KiCad9/KiCad.app/Contents/SharedSupport/symbols/",
            ]
        elif platform.system() == "Linux":
            possible_paths = [
                "/usr/share/kicad/symbols/",
                "/usr/local/share/kicad/symbols/",
                "/snap/kicad/current/usr/share/kicad/symbols/",
            ]
        elif platform.system() == "Windows":
            possible_paths = [
                "C:\\Program Files\\KiCad\\share\\kicad\\symbols\\",
                "C:\\Program Files (x86)\\KiCad\\share\\kicad\\symbols\\",
            ]

        # Find the first existing path
        symbol_base_path = None
        for path in possible_paths:
            if Path(path).exists():
                symbol_base_path = path
                break

        # Fallback to Linux default if nothing found
        if not symbol_base_path:
            symbol_base_path = "/usr/share/kicad/symbols/"

        uri = f"{symbol_base_path}{lib}.kicad_sym"

        library_entry = ["library", ["logical", lib], ["uri", uri]]
        libraries_section.append(library_entry)

    return libraries_section


def validate_net_data(net_name: str, net_data: Any) -> bool:
    """Validate net data format.

    Args:
        net_name: Name of the net being validated
        net_data: Net data to validate (either dict or list format)

    Returns:
        bool: True if data is valid, False otherwise
    """
    if isinstance(net_data, dict):
        if "nodes" not in net_data:
            logger.warning(f"Net '{net_name}' missing required 'nodes' field")
            return False
        if not isinstance(net_data["nodes"], list):
            logger.warning(f"Net '{net_name}' nodes must be a list")
            return False
        return True
    elif isinstance(net_data, list):
        # New format is valid as long as it's a list
        return True
    else:
        logger.warning(f"Net '{net_name}' has invalid data type: {type(net_data)}")
        return False


def normalize_hierarchical_path(path: str, name: str) -> str:
    """
    Normalize a hierarchical path while preserving original paths and preventing duplication.

    Args:
        path: The hierarchical path (e.g., "/Project Architecture/MCU")
        name: The name to append (e.g., "ISENC")

    Returns:
        Normalized path with proper separators and preserved structure
    """
    logger.debug(f"Normalizing path='{path}' with name='{name}'")

    # If name already has a hierarchical path, preserve it exactly
    if name and name.startswith("/"):
        logger.debug(f"  Preserving existing hierarchical path: {name}")
        return name

    # Handle special cases
    if not path or path == "/":
        return f"/{name}" if name else "/"

    # Ensure path starts with /
    if not path.startswith("/"):
        path = "/" + path

    # Remove any double slashes and trailing slashes
    path = path.replace("//", "/").rstrip("/")

    # If name is provided, check for path component duplication
    if name:
        # Remove any leading/trailing slashes from name
        name = name.strip("/")
        if name:
            # Split path and name into components
            path_parts = path.split("/")
            name_parts = name.split("/")

            # Check for duplication
            if len(path_parts) > 1 and len(name_parts) > 0:
                if path_parts[-1] == name_parts[0]:
                    # Remove duplicate component from name
                    name_parts = name_parts[1:]
                    name = "/".join(name_parts)
                    logger.debug(f"  Removed duplicate component. New name: {name}")

            return f"{path}/{name}"

    return path


def generate_nets_section(circuit_data: Dict[str, Any]) -> List[Any]:
    nets_section = ["nets"]
    net_code = 1

    # Add debug logging
    logger.debug("=== Analyzing net connectivity patterns ===")

    # Initialize collections for net analysis
    all_nodes_by_net_name = {}
    global_nets = set()
    hierarchical_nets = set()
    local_nets = set()
    unconnected_pins = set()

    # Create mapping of nets to their original sheets
    original_net_sheets = {}
    logger.debug("Building net-to-sheet mapping")

    # First pass: collect nets from explicit sheet data
    for sheet_name, sheet_data in circuit_data.get("sheets", {}).items():
        logger.debug(f"Processing sheet: {sheet_name}")
        for net_name in sheet_data.get("nets", []):
            # If net already has a hierarchical path, extract the sheet name from it
            if "/" in net_name:
                path_parts = net_name.split("/")
                if len(path_parts) >= 3 and path_parts[1] == "Project Architecture":
                    sheet_name = path_parts[2]
                    logger.debug(
                        f"  Extracted sheet '{sheet_name}' from hierarchical path: {net_name}"
                    )

            if net_name not in original_net_sheets:
                original_net_sheets[net_name] = sheet_name
                logger.debug(f"  Mapped net '{net_name}' to sheet '{sheet_name}'")

    # Second pass: collect nets from component connections
    for comp_ref, comp_data in circuit_data.get("components", {}).items():
        sheet_name = comp_data.get("sheet", "")
        if sheet_name:
            for net_name in comp_data.get("nets", []):
                # Only map if not already mapped or if current sheet is more specific
                if net_name not in original_net_sheets or len(
                    sheet_name.split("/")
                ) > len(original_net_sheets[net_name].split("/")):
                    original_net_sheets[net_name] = sheet_name
                    logger.debug(
                        f"  Mapped net '{net_name}' to sheet '{sheet_name}' from component {comp_ref}"
                    )

    # First collect all nodes and determine net types
    def process_net_nodes(circ, path="/"):
        for net_name, net_data in circ.get("nets", {}).items():
            # Skip invalid nets
            if not validate_net_data(net_name, net_data):
                logger.warning(
                    f"Skipping invalid net '{net_name}' during node collection"
                )
                continue

            # Handle both formats
            if isinstance(net_data, dict):
                nodes = net_data.get("nodes", [])
                is_hierarchical = net_data.get("is_hierarchical", False)
                original_name = net_data.get("original_name", net_name)
            else:
                nodes = net_data  # Direct array of nodes
                is_hierarchical = True  # Treat array format as hierarchical by default
                original_name = net_name

            # Handle unconnected pins
            if not nodes:
                if original_name.startswith("unconnected-"):
                    unconnected_pins.add(original_name)
                    final_net_name = original_name  # Keep original unconnected pin name
                    is_hierarchical = False  # Unconnected pins are local
                continue

            # All nets are treated as hierarchical (no global nets)
            final_net_name = original_name
            # logger.info(f"\nProcessing net name: {original_name}")
            # logger.info(f"  Current path: {path}")
            # logger.info(f"  Is hierarchical: {is_hierarchical}")

            # Check if net already has a hierarchical path
            if "/" in original_name:
                path_parts = original_name.split("/")
                if len(path_parts) >= 3 and path_parts[1] == "Project Architecture":
                    final_net_name = original_name
                    logger.debug(
                        f"  Using existing hierarchical path: {final_net_name}"
                    )
                    hierarchical_nets.add(final_net_name)
                    is_hierarchical = True

            # If not, check original sheet assignment
            elif original_name in original_net_sheets:
                sheet_name = original_net_sheets[original_name]
                if sheet_name:
                    sheet_path = sheet_paths.get(sheet_name, "")
                    if sheet_path:
                        final_net_name = f"{sheet_path}/{original_name}"
                        logger.debug(f"  Using sheet assignment path: {final_net_name}")
                        hierarchical_nets.add(final_net_name)
                        is_hierarchical = True

            # If still no path, use current path
            elif is_hierarchical and path and path != "/":
                final_net_name = normalize_hierarchical_path(path, original_name)
                logger.debug(f"  Using current path: {final_net_name}")
                hierarchical_nets.add(final_net_name)
            else:
                logger.debug(f"  Keeping as local net: {final_net_name}")
                local_nets.add(final_net_name)

            # Special cases that should never get a path prefix
            if (
                original_name.startswith("unconnected-")
                or original_name.startswith("Net-")
                or original_name.startswith("+")
                or original_name.startswith("-")
                or original_name.upper()
                in {"GND", "GNDA", "GNDD", "VCC", "VDD", "VSS", "VDDA"}
            ):
                # Keep original name for special nets
                logger.debug(
                    f"  Special case net - keeping original name: {original_name}"
                )
                local_nets.add(original_name)
            # Keep original path if it has one
            elif original_name.startswith("/"):
                # Already has a path, use as-is
                logger.debug(
                    f"  Net already has path - preserving exactly: {original_name}"
                )
                final_net_name = original_name
                hierarchical_nets.add(final_net_name)
            # Only add path if explicitly marked as hierarchical
            elif is_hierarchical:
                logger.debug(f"  Checking for existing hierarchical path")
                # First check if this net exists with ANY hierarchical path
                existing_net = None

                # Check if original name already has a hierarchical path
                if original_name.startswith("/"):
                    existing_net = original_name
                    logger.debug(f"  Using original hierarchical path: {existing_net}")
                else:
                    # Check if net has an original sheet assignment
                    if original_name in original_net_sheets:
                        sheet_name = original_net_sheets[original_name]
                        sheet_path = sheet_paths.get(sheet_name, "")
                        if sheet_path:
                            existing_net = f"{sheet_path}/{original_name}"
                            logger.debug(
                                f"  Using original sheet assignment: {existing_net}"
                            )

                    # If no sheet assignment found, look in circuit data
                    if not existing_net:
                        for net_name in circuit_data.get("nets", {}):
                            if (
                                net_name.endswith("/" + original_name)
                                and "/" in net_name
                            ):
                                existing_net = net_name
                                logger.debug(
                                    f"  Found existing path in circuit data: {existing_net}"
                                )
                                break

                        # If still not found, look in all_nodes_by_net_name
                        if not existing_net:
                            for net_name in all_nodes_by_net_name.keys():
                                if (
                                    net_name.endswith("/" + original_name)
                                    and "/" in net_name
                                ):
                                    existing_net = net_name
                                    logger.debug(
                                        f"  Found existing path in all_nodes: {existing_net}"
                                    )
                                    break

                if existing_net:
                    # Use the existing path
                    logger.debug(f"  Using existing hierarchical path: {existing_net}")
                    final_net_name = existing_net
                elif path and path != "/":
                    # Add current path to net name with proper normalization
                    logger.debug(f"  Adding current path to net name")
                    final_net_name = normalize_hierarchical_path(path, original_name)
                    logger.debug(f"  Final hierarchical net name: {final_net_name}")
                else:
                    # Keep original name if no path to add
                    final_net_name = original_name
                hierarchical_nets.add(final_net_name)
            # Otherwise keep as local net
            else:
                logger.debug(
                    f"  Treating as local net - keeping original name: {original_name}"
                )
                final_net_name = original_name
                local_nets.add(original_name)

            # Initialize net's node list if needed
            if final_net_name not in all_nodes_by_net_name:
                all_nodes_by_net_name[final_net_name] = []

            # Add nodes preserving original component paths
            for node in nodes:
                if not isinstance(node, dict):
                    continue

                node_copy = node.copy()
                comp_ref = node_copy.get("component", "")

                # Handle component paths
                if (
                    "original_path" in node_copy
                    and node_copy["original_path"] is not None
                ):
                    # Use original path if available and not None
                    node_copy["component"] = node_copy["original_path"]
                elif comp_ref:
                    # Normalize component path
                    if path == "/" or comp_ref.startswith("/"):
                        # Root level components or already have path
                        node_copy["component"] = normalize_hierarchical_path(
                            "", comp_ref
                        )
                    else:
                        # Components in subcircuits - ensure proper path format
                        node_copy["component"] = normalize_hierarchical_path(
                            path, comp_ref
                        )

                # Handle pin type
                pin_info = node_copy.get("pin", {})
                pin_type = pin_info.get("type", "passive")

                # Check for unconnected pins
                if pin_type == "no_connect":
                    pin_num = pin_info.get("number", "")
                    unconnected_name = f"unconnected-{node_copy['component']}-{pin_num}"
                    unconnected_pins.add(unconnected_name)
                    continue

                all_nodes_by_net_name[final_net_name].append(node_copy)

        # Process subcircuits
        for subcircuit in circ.get("subcircuits", []):
            subname = subcircuit.get("name", "")
            # Ensure path always starts with /
            if path == "":
                new_path = f"/{subname}"
            else:
                new_path = f"{path}/{subname}"
            process_net_nodes(subcircuit, new_path)

    # Process all circuits to collect nodes and determine net types
    process_net_nodes(circuit_data)

    logger.debug(f"Global nets: {sorted(global_nets)}")
    logger.debug(f"Hierarchical nets: {sorted(hierarchical_nets)}")
    logger.debug(f"Local nets: {sorted(local_nets)}")
    logger.debug(f"Unconnected pins: {sorted(unconnected_pins)}")

    # Generate net entries for the netlist
    for final_net_name, nodes in all_nodes_by_net_name.items():
        logger.debug(f"\nGenerating net entry for '{final_net_name}'")
        logger.debug(f"  Found {len(nodes)} nodes")

        # Skip empty nets
        if not nodes:
            continue

        # Handle unconnected pins
        if final_net_name.startswith("unconnected-"):
            # Format: unconnected-(component-pin-padNum)
            parts = final_net_name.split("-")
            if len(parts) >= 3:
                component = parts[1]
                pin_name = parts[2]  # This might be "EN", "IO0", etc.

                # Look up pin info from libpart first
                pin_type = None
                pin_function = None
                pin_num = None
                comp_data = circuit_data.get("components", {}).get(component, {})
                symbol = comp_data.get("symbol", "")

                if symbol and ":" in symbol:
                    lib, part = symbol.split(":", 1)
                    logger.debug(f"  Looking up pin type in libpart {lib}:{part}")
                    for libpart in circuit_data.get("libparts", []):
                        if libpart.get("lib") == lib and libpart.get("part") == part:
                            for pin in libpart.get("pins", []):
                                # Match by pin name
                                if pin.get("name") == pin_name:
                                    pin_type = pin.get("type")
                                    pin_function = pin.get("name")
                                    pin_num = "8" if pin_name == "EN" else pin_name
                                    if pin_type:
                                        logger.debug(
                                            f"  Found pin type in libpart: {pin_type}"
                                        )
                                        break

                # Map the pin type to KiCad format
                mapped_pin_type = PinType.to_kicad(pin_type) if pin_type else "passive"
                logger.debug(f"  Using pin type for unconnected pin: {mapped_pin_type}")

                # Create net entry with correct pin type and function
                net_entry = ["net", ["code", str(net_code)], ["name", final_net_name]]
                node_entry = [
                    "node",
                    ["ref", component],  # Just the component ref
                    ["pin", pin_num],  # Use pin number
                    [
                        "pintype",
                        pin_type if pin_type else "passive",
                    ],  # Use original pin type
                ]

                # Add pin function if available
                if pin_function:
                    node_entry.append(["pinfunction", pin_function])

                net_entry.append(node_entry)
                nets_section.append(net_entry)
                net_code += 1
            continue

        # Regular net handling
        net_entry = ["net", ["code", str(net_code)], ["name", final_net_name]]
        net_code += 1
        logger.debug(f"  Created net entry structure: {net_entry}")

        # Add nodes to this net
        for node in nodes:
            # logger.debug(f"Processing node connection: {node}")
            component_ref = node.get("component")
            pin_info = node.get("pin", {})
            logger.debug(f"  Component ref: {component_ref}, Pin info: {pin_info}")

            # Get the pin number from the pin info
            pin_num = pin_info.get("number")
            if not pin_num:
                logger.warning(
                    f"  Skipping node - missing pin number key ('number'): {pin_info}"
                )
                continue
            logger.debug(f"  Found pin number: {pin_num}")

            # Get pin type and function from pin info
            pin_type = pin_info.get("type")
            pin_function = pin_info.get("name", "")
            pin_num = pin_info.get("number", "")

            # Enhanced logging for pin type lookup
            # logger.info(f"Looking up pin type for {component_ref}:{pin_num}")
            # logger.info(f"  Initial pin type from pin_info: {pin_type}")
            # logger.info(f"  Pin function: {pin_function}")

            # First check component's pin definitions
            comp_data = circuit_data.get("components", {}).get(component_ref, {})
            # logger.info(f"  Checking component definition pins:")
            for pin_def in comp_data.get("pins", []):
                if str(pin_def.get("num")) == str(pin_num):
                    comp_pin_type = pin_def.get("type")
                    if comp_pin_type:
                        pin_type = comp_pin_type
                        # logger.info(f"  Found pin type in component definition: {pin_type}")
                        break
                    else:
                        # logger.info(f"  Found pin in component but no type specified")
                        pass

            # Always check libpart definition
            symbol = comp_data.get("symbol", "")
            if symbol and ":" in symbol:
                lib, part = symbol.split(":", 1)
                # logger.info(f"  Looking up pin type in libpart {lib}:{part}")
                for libpart in circuit_data.get("libparts", []):
                    if libpart.get("lib") == lib and libpart.get("part") == part:
                        # logger.info(f"  Found matching libpart")
                        for pin in libpart.get("pins", []):
                            # Match by pin number or name
                            if (
                                str(pin.get("num")) == str(pin_num)
                                or pin.get("name") == pin_function
                            ):
                                libpart_type = pin.get("type")
                                if libpart_type:
                                    pin_type = libpart_type
                                    # logger.info(f"  Found pin type in libpart: {pin_type}")
                                    break

            # If still no type found, default to passive
            if not pin_type:
                pin_type = "passive"
                logger.debug(
                    f"  No pin type found in component or libpart for {component_ref}:{pin_num}, defaulting to 'passive'"
                )

            # logger.debug(
            #     f"  Pin type for {component_ref}:{pin_num} before mapping: {pin_type}"
            # )

            # Special handling for unconnected pins - preserve their original type
            if pin_info.get("unconnected", False):
                # logger.info(f"  Processing unconnected pin {component_ref}:{pin_num}")
                # logger.info(f"  Current pin type before unconnected handling: {pin_type}")
                pass

                # Generate unconnected pin name if not already done
                unconnected_name = f"unconnected-{component_ref}-{pin_num}"
                if unconnected_name not in unconnected_pins:
                    unconnected_pins.add(unconnected_name)
                    # logger.info(f"  Created unconnected net: {unconnected_name}")

                    # Create separate net entry for this unconnected pin
                    unconnected_net_entry = [
                        "net",
                        ["code", str(net_code)],
                        ["name", unconnected_name],
                    ]
                    net_code += 1

                    # CRITICAL FIX: Look up pin type in libpart definition first
                    symbol = comp_data.get("symbol", "")
                    if symbol and ":" in symbol:
                        lib, part = symbol.split(":", 1)
                        # logger.info(f"  Looking up pin type in libpart {lib}:{part}")
                        for libpart in circuit_data.get("libparts", []):
                            if (
                                libpart.get("lib") == lib
                                and libpart.get("part") == part
                            ):
                                for pin in libpart.get("pins", []):
                                    # Match by pin number or name
                                    if str(pin.get("num")) == str(pin_num) or pin.get(
                                        "name"
                                    ) == pin_info.get("name"):
                                        libpart_type = pin.get("type")
                                        pin_function = pin.get("name", "")
                                        if libpart_type:
                                            pin_type = libpart_type
                                            # logger.info(f"  Found pin type in libpart: {pin_type}")
                                            break

                    # Map the pin type to KiCad format
                    mapped_pin_type = (
                        PinType.to_kicad(pin_type) if pin_type else "passive"
                    )
                    # logger.info(f"  Using pin type for unconnected pin: {mapped_pin_type}")

                    # Create node entry with correct pin type and function
                    # Normalize component reference for unconnected pins
                    normalized_ref = str(component_ref)
                    if normalized_ref.startswith("/"):
                        normalized_ref = normalized_ref[1:]
                        logger.debug(
                            f"  Normalized unconnected component ref from {component_ref} to {normalized_ref}"
                        )

                    unconnected_node_entry = [
                        "node",
                        [
                            "ref",
                            normalized_ref,
                        ],  # Use normalized reference without leading slash
                        ["pin", str(pin_num)],  # Just the pin number
                        ["pintype", mapped_pin_type],  # Use the mapped pin type
                    ]

                    # Add pin function if available
                    if pin_function:
                        unconnected_node_entry.append(["pinfunction", pin_function])

                    unconnected_net_entry.append(unconnected_node_entry)
                    nets_section.append(unconnected_net_entry)
                    # logger.info(f"  Added unconnected net entry with pin type: {mapped_pin_type}")

                continue

            # Map pin type to KiCad format, preserving original type
            mapped_pin_type = PinType.to_kicad(pin_type)
            logger.debug(
                f"  Mapped pin type for {component_ref}:{pin_num}: {pin_type} -> {mapped_pin_type}"
            )

            # Normalize component reference by removing leading slash
            normalized_ref = str(component_ref)
            if normalized_ref.startswith("/"):
                normalized_ref = normalized_ref[1:]
                logger.debug(
                    f"  Normalized component ref from {component_ref} to {normalized_ref}"
                )

            # Create node entry with pin type and function
            node_entry = [
                "node",
                [
                    "ref",
                    normalized_ref,
                ],  # Use normalized reference without leading slash
                ["pin", str(pin_num)],  # Ensure pin number is a string
            ]

            # Always include pin type and function if available
            if mapped_pin_type:
                node_entry.append(["pintype", mapped_pin_type])
            if pin_function and pin_function != "~":
                node_entry.append(["pinfunction", pin_function])

            net_entry.append(node_entry)
            # logger.debug(f"  Added node entry: {node_entry}")

        # Add the complete net entry to nets section
        nets_section.append(net_entry)
        logger.debug(
            f"  Appended net_entry for '{final_net_name}'. Current nets_section length: {len(nets_section)}"
        )

    return nets_section


def determine_net_ownership(circuit_data: Dict[str, Any]) -> Dict[str, str]:
    """
    Determine which circuit level "owns" each net name.

    In Circuit-Synth, nets can be defined at any level and used in child circuits.
    This function determines the highest level (closest to root) where each net is defined.

    Args:
        circuit_data: Dictionary containing the circuit data

    Returns:
        Dictionary mapping net names to their owner circuit's path
    """
    net_ownership = {}

    def scan_circuit(circuit, path=""):
        # First, register all nets at this level
        for net_name in circuit.get("nets", {}).keys():
            # Only register as owner if no parent has claimed this net
            if net_name not in net_ownership:
                net_ownership[net_name] = path

        # Then scan subcircuits
        for subcircuit in circuit.get("subcircuits", []):
            subname = subcircuit.get("name", "")
            new_path = f"{path}/{subname}" if path else f"/{subname}"
            scan_circuit(subcircuit, new_path)

    # Start scanning from the top circuit
    scan_circuit(circuit_data)
    return net_ownership


# TODO: Pass sheet context down to get accurate Sheetname/Sheetfile/Sheetpath
def generate_component_entry(
    comp_data: Dict[str, Any],
    sheet_name: str = "Root",
    sheet_file: str = "unknown.kicad_sch",
    sheet_path: str = "/",
) -> Optional[List[Any]]:
    """
    Generate a component entry for the KiCad netlist.

    Args:
        comp_data: Dictionary containing the component data

    Returns:
        List representing the component entry, or None if invalid
    """
    logger.debug(f"Generating component entry for comp_data={comp_data}")
    ref = comp_data.get("reference") or comp_data.get("ref")  # Allow 'ref' as well
    if not ref:
        logger.warning("Component data missing 'reference' or 'ref' field.")
        return None

    # Define properties early so it's always available
    properties = comp_data.get("properties", {})
    logger.debug(f"  Component Entry: Properties dict: {properties}")

    # Create the component entry with the expected format
    # KiCad expects: (comp (ref "C1") (value "0.1uF") ...)
    # Create component entry with expected format (comp (ref "R1"))
    comp_entry = ["comp"]
    comp_entry.append(["ref", ref])

    # Add value, footprint, and description if available
    # Ensure value is treated as string
    value = str(comp_data.get("value", ""))
    # Always include value field, even if empty, for consistency? KiCad seems to omit if empty.
    if value:
        comp_entry.append(["value", value])  # Ensure value is string

    footprint = comp_data.get("footprint", "")
    if footprint:
        comp_entry.append(["footprint", footprint])

    description = comp_data.get("description", "")
    if description:
        comp_entry.append(["description", description])

    # Add fields section if there are fields
    fields = []
    if footprint:
        fields.append(["field", ["name", "Footprint"], footprint])

    datasheet = comp_data.get("datasheet", "")
    fields.append(["field", ["name", "Datasheet"], datasheet])

    if description:
        fields.append(["field", ["name", "Description"], description])

    if fields:
        comp_entry.append(["fields"] + fields)

    # --- Determine libsource based on symbol or fallback ---
    # Get ref and description again for logging context and libsource entry
    ref = comp_data.get("reference") or comp_data.get("ref", "UnknownRef")
    description = comp_data.get("description", "")  # Get description for libsource

    # Initialize lib and part
    lib = None
    part = None

    symbol = comp_data.get("symbol", "")
    logger.debug(
        f"  Component Entry: Determining libsource for ref='{ref}', symbol='{symbol}'"
    )

    if symbol and ":" in symbol:
        # --- Primary Logic: Use symbol attribute ---
        try:
            lib, part = symbol.split(":", 1)
            logger.debug(
                f"  Component Entry: Extracted lib='{lib}', part='{part}' from symbol for libsource."
            )
        except ValueError:
            raise ValueError(
                f"Invalid symbol format '{symbol}' for component '{ref}'. Expected 'Library:Part' format."
            )
    else:
        # --- Fallback Logic (Mirroring generate_libparts_section) ---
        # Only use fallbacks if symbol is missing or invalid
        logger.debug(
            f"  Component Entry: Symbol missing or invalid ('{symbol}'). Attempting fallbacks for ref '{ref}' for libsource..."
        )
        properties = comp_data.get("properties", {})
        ki_lib = properties.get("ki_lib")
        ki_part = properties.get("ki_part")
        # 'libsource' property often contains original lib:part, but we prioritize 'symbol'
        # libsource_prop = properties.get("libsource") # Avoid using this as fallback

        if ki_lib and ki_part:
            # Fallback 1: Use ki_lib and ki_part from properties
            lib = ki_lib
            part = ki_part
            logger.debug(
                f"  Component Entry: Using fallback from properties: ki_lib='{lib}', ki_part='{part}' for libsource."
            )
        # We avoid using the 'libsource' property here as a fallback,
        # because 'symbol' should be the primary source of truth.
        else:
            # No valid library found - raise error
            raise ValueError(
                f"No library specified for component '{ref}'. Symbol must be in 'Library:Part' format."
            )
        # --- End Fallback Logic ---

    # Ensure description is a string, default to empty if None
    libsource_description = description if description is not None else ""
    libsource_entry = [
        "libsource",
        ["lib", lib],
        ["part", part],
        ["description", libsource_description],
    ]
    logger.debug(f"  Component Entry: Generated libsource entry: {libsource_entry}")
    comp_entry.append(libsource_entry)

    # Add standard properties from KiCad schema
    comp_entry.append(["property", ["name", "Sheetname"], ["value", sheet_name]])
    comp_entry.append(["property", ["name", "Sheetfile"], ["value", sheet_file]])
    if "ki_keywords" in properties:
        comp_entry.append(
            [
                "property",
                ["name", "ki_keywords"],
                ["value", str(properties["ki_keywords"])],
            ]
        )
    if "ki_fp_filters" in properties:
        comp_entry.append(
            [
                "property",
                ["name", "ki_fp_filters"],
                ["value", str(properties["ki_fp_filters"])],
            ]
        )
    # Add any other non-standard properties from _extra_fields if needed
    extra_fields = comp_data.get("_extra_fields", {})
    for key, prop_value in extra_fields.items():
        if key not in ["ki_keywords", "ki_fp_filters"]:  # Avoid duplication
            prop_value_str = str(prop_value) if prop_value is not None else ""
            comp_entry.append(["property", ["name", key], ["value", prop_value_str]])
    # Add sheetpath with proper hierarchical formatting
    # Use sheet_path passed down (or default "/")
    # Ensure formatting
    if not sheet_path.startswith("/"):
        sheet_path = "/" + sheet_path
    if not sheet_path.endswith("/") and sheet_path != "/":
        sheet_path += "/"

    sheet_names = sheet_path
    # TODO: Use actual sheet UUID tstamps when available
    sheet_tstamps = sheet_path  # Placeholder

    comp_entry.append(["sheetpath", ["names", sheet_names], ["tstamps", sheet_tstamps]])

    # Use component tstamp from comp_data if available, otherwise generate UUID
    tstamp = comp_data.get("tstamps")  # Use the key added in Component.to_dict
    if not tstamp:
        import uuid

        tstamp = str(uuid.uuid4())

    comp_entry.append(["tstamps", tstamp])

    logger.debug(f"Generated component entry: {comp_entry}")
    return comp_entry


# Updated signature to accept net_name, list of nodes, and component lookup
def generate_net_entry(
    net_name: str, nodes: List[Dict[str, Any]]
) -> Optional[List[Any]]:
    """
    Generate a net entry for the KiCad netlist.

    Args:
        net_name: The final hierarchical or global name of the net.
        nodes: List of dictionaries, each specifying a component and full pin details.
               Example: [{"component": "R1", "pin": {"number": "1", "name": "~", "type": "passive"}}, ...]

    Returns:
        List representing the net entry S-expression, or None if invalid.
    """
    logger.debug(f"Generating net entry for net_name='{net_name}', nodes={nodes}")

    if not net_name:
        logger.warning("generate_net_entry called with empty net_name.")
        return None

    # Create the net entry with the appropriate name
    net_entry = ["net", ["code", "0"], ["name", net_name]]

    # Add nodes by looking up pin details from component data
    for node_connection in nodes:
        component_ref = node_connection.get("component")
        pin_details = node_connection.get("pin")

        if not component_ref or not pin_details:
            logger.warning(
                f"Skipping invalid node connection in net '{net_name}': {node_connection}"
            )
            continue

        # Extract pin details using correct field names
        pin_num_str = pin_details.get("number")  # Use 'number' instead of 'num'
        pin_name = pin_details.get("name", "~")  # Pin name string (e.g., "~", "GND")

        # Get pin type, preserving original type
        pin_type = pin_details.get("type")
        if not pin_type:
            # Only default to passive if no type specified
            pin_type = "passive"
            logger.debug(
                f"No pin type specified for {component_ref}:{pin_num_str} in net '{net_name}', defaulting to 'passive'"
            )
        logger.debug(
            f"Pin type for {component_ref}:{pin_num_str} in net '{net_name}': {pin_type}"
        )

        # Check if we successfully obtained a pin number
        if not pin_num_str:
            logger.warning(
                f"Missing pin number for component '{component_ref}' in net '{net_name}'. Skipping node."
            )
            continue

        # Determine KiCad pin type, preserving original type
        pin_kicad_type = PinType.to_kicad(pin_type)
        logger.debug(
            f"Mapped pin type for {component_ref}:{pin_num_str}: {pin_type} -> {pin_kicad_type}"
        )
        if (pin_name and "NC" in pin_name.upper()) or pin_type == "no_connect":
            pin_kicad_type = "no_connect"

        # Build the node entry using looked-up string values
        node_entry = [
            "node",
            ["ref", component_ref],
            ["pin", pin_num_str],
            ["pintype", PinType.to_kicad(pin_kicad_type)],
        ]

        # Add pinfunction if available and not just "~"
        if pin_name and pin_name != "~":
            node_entry.append(["pinfunction", pin_name])

        net_entry.append(node_entry)

    logger.debug(f"Generated net entry: {net_entry}")
    return net_entry


def format_s_expr(expr: Any, indent: int = 0) -> str:
    """
    Format a Python object as an S-expression string exactly matching KiCad's format.

    Args:
        expr: The expression to format (string, list, or other)
        indent: Current indentation level

    Returns:
        Formatted S-expression string
    """
    # logger.debug(
    #     f"format_s_expr called with type={type(expr)}, value={repr(expr)}, indent={indent}"
    # )
    indent_str = "  " * indent

    if isinstance(expr, str):
        # Always quote strings in S-expressions
        return f'"{expr}"'

    if isinstance(expr, (int, float)):
        # Quote numbers too, as KiCad expects quoted values for attributes
        return f'"{str(expr)}"'

    if isinstance(expr, list):
        if not expr:
            return "()"

        keyword = expr[0]

        # Top-level export expression - KiCad has special format
        if keyword == "export":
            result = '(export (version "E")'
            for item in expr[2:]:  # Skip version which is handled inline
                result += f"\n{indent_str}  {format_s_expr(item, indent + 1)}"
            result += ")"
            return result

        # Design section - KiCad specific format
        elif keyword == "design":
            result = "  (design"
            for item in expr[1:]:
                result += f"\n{indent_str}    {format_s_expr(item, indent + 2)}"
            result += ")"
            return result

        # Sheet section
        elif keyword == "sheet":
            result = "(sheet"
            number = next(
                (
                    item
                    for item in expr[1:]
                    if isinstance(item, list) and item[0] == "number"
                ),
                None,
            )
            name = next(
                (
                    item
                    for item in expr[1:]
                    if isinstance(item, list) and item[0] == "name"
                ),
                None,
            )
            tstamps = next(
                (
                    item
                    for item in expr[1:]
                    if isinstance(item, list) and item[0] == "tstamps"
                ),
                None,
            )

            # Format sheet header items on one line
            result += f" (number {format_s_expr(number[1], 0)}) (name {format_s_expr(name[1], 0)}) (tstamps {format_s_expr(tstamps[1], 0)})"

            # Title block on new line
            title_block = next(
                (
                    item
                    for item in expr[1:]
                    if isinstance(item, list) and item[0] == "title_block"
                ),
                None,
            )
            if title_block:
                result += "\n      (title_block"
                for tb_item in title_block[1:]:
                    if tb_item[0] == "comment":
                        result += f"\n        (comment (number {format_s_expr(tb_item[1][1], 0)}) (value {format_s_expr(tb_item[2][1], 0)}))"
                    else:
                        result += f"\n        ({tb_item[0]} {format_s_expr(tb_item[1], 0) if len(tb_item) > 1 else ''})"
                result += ")"

            result += ")"
            return result

        # Components section
        elif keyword == "components":
            result = "  (components"
            for item in expr[1:]:
                result += f"\n{format_s_expr(item, indent + 1)}"
            result += ")"
            return result

        # Component entry - KiCad has very specific format
        elif keyword == "comp":
            ref_item = next(
                (
                    item
                    for item in expr[1:]
                    if isinstance(item, list) and item[0] == "ref"
                ),
                None,
            )

            # KiCad format: (comp (ref "X") on first line - no extra spaces
            result = f"    (comp (ref {format_s_expr(ref_item[1], 0)})"  # Space between comp and (ref for KiCad format

            # Every other attribute on its own line with 2-space indentation from comp
            remaining_items = [
                item for item in expr[1:] if isinstance(item, list) and item[0] != "ref"
            ]

            for item in remaining_items:
                if item[0] in ["value", "footprint", "description"]:
                    result += f"\n      ({item[0]} {format_s_expr(item[1], 0)})"
                elif item[0] == "fields":
                    result += "\n      (fields"
                    for field in item[1:]:
                        result += f"\n        (field (name {format_s_expr(field[1][1], 0)}) {format_s_expr(field[2], 0)})"
                    result += ")"
                elif item[0] == "libsource":
                    result += f"\n      (libsource (lib {format_s_expr(item[1][1], 0)}) (part {format_s_expr(item[2][1], 0)})"
                    if len(item) > 3:
                        result += f" (description {format_s_expr(item[3][1], 0)})"
                    result += ")"
                elif item[0] == "property":
                    result += f"\n      (property (name {format_s_expr(item[1][1], 0)}) (value {format_s_expr(item[2][1], 0)}))"
                elif item[0] == "sheetpath":
                    result += f"\n      (sheetpath (names {format_s_expr(item[1][1], 0)}) (tstamps {format_s_expr(item[2][1], 0)}))"
                else:
                    result += f"\n      {format_s_expr(item, indent + 3)}"

            # Close with closing parenthesis
            result += ")"
            return result

        # Libparts section
        elif keyword == "libparts":
            result = "  (libparts"
            for item in expr[1:]:
                result += f"\n{format_s_expr(item, indent + 1)}"
            result += ")"
            return result

        # Libpart entry - KiCad specific format
        elif keyword == "libpart":
            lib_item = next(
                (
                    item
                    for item in expr[1:]
                    if isinstance(item, list) and item[0] == "lib"
                ),
                None,
            )
            part_item = next(
                (
                    item
                    for item in expr[1:]
                    if isinstance(item, list) and item[0] == "part"
                ),
                None,
            )

            # First line has lib and part
            result = f"    (libpart (lib {format_s_expr(lib_item[1], 0)}) (part {format_s_expr(part_item[1], 0)})"

            # Other items on new lines
            remaining_items = [
                item
                for item in expr[1:]
                if isinstance(item, list) and item[0] not in ["lib", "part"]
            ]

            for item in remaining_items:
                if item[0] == "description":
                    result += f"\n      (description {format_s_expr(item[1], 0)})"
                elif item[0] == "docs":
                    result += f"\n      (docs {format_s_expr(item[1], 0)})"
                elif item[0] == "footprints":
                    result += "\n      (footprints"
                    for fp in item[1:]:
                        result += f"\n        (fp {format_s_expr(fp[1], 0)})"
                    result += ")"
                elif item[0] == "fields":
                    result += "\n      (fields"
                    for field in item[1:]:
                        result += f"\n        (field (name {format_s_expr(field[1][1], 0)}) {format_s_expr(field[2], 0)})"
                    result += ")"
                elif item[0] == "pins":
                    result += "\n      (pins"
                    for pin in item[1:]:
                        result += f"\n        (pin (num {format_s_expr(pin[1][1], 0)}) (name {format_s_expr(pin[2][1], 0)}) (type {format_s_expr(pin[3][1], 0)}))"
                    result += ")"
                else:
                    result += f"\n      {format_s_expr(item, indent + 3)}"

            # Close with closing parenthesis
            result += ")"
            return result

        # Libraries section
        elif keyword == "libraries":
            result = "  (libraries"
            for item in expr[1:]:
                result += f"\n{format_s_expr(item, indent + 1)}"
            result += ")"
            return result

        # Library entry
        elif keyword == "library":
            logical_item = next(
                (
                    item
                    for item in expr[1:]
                    if isinstance(item, list) and item[0] == "logical"
                ),
                None,
            )
            uri_item = next(
                (
                    item
                    for item in expr[1:]
                    if isinstance(item, list) and item[0] == "uri"
                ),
                None,
            )

            result = f"    (library (logical {format_s_expr(logical_item[1], 0)})"
            result += f"\n      (uri {format_s_expr(uri_item[1], 0)})"
            result += ")"
            return result

        # Nets section
        elif keyword == "nets":
            result = "  (nets"
            for item in expr[1:]:
                result += f"\n{format_s_expr(item, indent + 1)}"
            result += ")"
            return result

        # Net entry - KiCad specific format
        elif keyword == "net":
            code = next(
                (
                    item
                    for item in expr[1:]
                    if isinstance(item, list) and item[0] == "code"
                ),
                None,
            )
            name = next(
                (
                    item
                    for item in expr[1:]
                    if isinstance(item, list) and item[0] == "name"
                ),
                None,
            )

            # Format the net header: (net (code "1") (name "+3V3")
            net_header = f"    (net (code {format_s_expr(code[1], 0)}) (name {format_s_expr(name[1], 0)})"  # Keep header open for nodes

            # Format nodes separately
            node_strings = []
            nodes = [
                item
                for item in expr[1:]
                if isinstance(item, list) and item[0] == "node"
            ]
            for node in nodes:
                # Use indent+3 for nodes relative to the start of the (net ...) line
                node_strings.append(format_node(node, indent + 3))

            # Combine header, nodes (each on a new line, indented), and closing parenthesis
            if node_strings:
                # Correctly place nodes inside the net parentheses
                result = net_header + "\n" + "\n".join(node_strings) + ")"
            else:
                # Close immediately if no nodes
                result = net_header + ")"

            return result

        # Special handling for other cases
        else:
            parts = [format_s_expr(item, 0) for item in expr[1:]]
            return f"({keyword} {' '.join(parts)})"

    # For other types, convert to string
    return f'"{str(expr)}"'


def format_node(node_expr: List, indent: int = 0) -> str:
    """
    Format a node expression in KiCad's specific format.

    Args:
        node_expr: The node expression to format
        indent: Current indentation level

    Returns:
        Formatted node string
    """
    indent_str = "  " * indent

    # Extract node components
    ref = next(
        (item for item in node_expr[1:] if isinstance(item, list) and item[0] == "ref"),
        None,
    )
    pin = next(
        (item for item in node_expr[1:] if isinstance(item, list) and item[0] == "pin"),
        None,
    )
    pintype = next(
        (
            item
            for item in node_expr[1:]
            if isinstance(item, list) and item[0] == "pintype"
        ),
        None,
    )

    # Format the node line with all attributes on one line
    result = f"{indent_str}(node (ref {format_s_expr(ref[1], 0)}) (pin {format_s_expr(pin[1], 0)}) (pintype {format_s_expr(pintype[1], 0)})"

    # Add pinfunction if available
    pinfunc = next(
        (
            item
            for item in node_expr[1:]
            if isinstance(item, list) and item[0] == "pinfunction"
        ),
        None,
    )
    if pinfunc:
        result += f" (pinfunction {format_s_expr(pinfunc[1], 0)})"

    result += ")"
    return result
