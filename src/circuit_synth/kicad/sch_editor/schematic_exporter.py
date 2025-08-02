"""
KiCad schematic exporter module.

This module handles writing modified schematic data back to KiCad .kicad_sch files.
It ensures proper formatting and validates the output.
"""

import logging
import uuid
from pathlib import Path
from typing import Any, List

# Import the new API's S-expression parser and use the formatter
import sexpdata

from circuit_synth.kicad.sch_gen.kicad_formatter import format_kicad_schematic

from .schematic_reader import (
    HierarchicalLabel,
    SchematicNet,
    SchematicSheet,
    SchematicSymbol,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)

logger = logging.getLogger(__name__)


class SchematicExporter:
    """Exports schematic data to KiCad schematic files."""

    def __init__(self, schematic):
        """Initialize the schematic exporter.

        Args:
            schematic: Modified schematic to export
        """
        self.schematic = schematic
        self.project_name = None  # Will be set from filename

    def export_file(self, filename: str) -> None:
        """Export the schematic to a .kicad_sch file.

        Args:
            filename: Path to write the .kicad_sch file

        Raises:
            OSError: If file cannot be written
            ValueError: If schematic data is invalid
        """
        # Extract project name from filename for instances section
        from pathlib import Path

        file_path = Path(filename)
        # Get the parent directory name as project name
        self.project_name = file_path.parent.name

        # Build the complete schematic S-expression
        # If schematic is a list, create a minimal schematic object with extracted data
        if isinstance(self.schematic, list):

            class MinimalSchematic:
                def __init__(self, data_list):
                    self.version = "20211123"  # Default KiCad version
                    self.uuid = str(uuid.uuid4())
                    # Extract components, nets, and sheets from list data
                    self.components = []
                    self.nets = []
                    self.sheets = []
                    self.hierarchical_labels = []
                    for item in data_list:
                        if isinstance(item, SchematicSymbol):
                            self.components.append(item)
                        elif isinstance(item, SchematicNet):
                            self.nets.append(item)
                        elif isinstance(item, SchematicSheet):
                            self.sheets.append(item)

            schematic_obj = MinimalSchematic(self.schematic)
        else:
            schematic_obj = self.schematic

        # Build the inner content first (everything inside kicad_sch)
        # Convert version to integer (KiCad expects a number, not a string)
        version_str = schematic_obj.version or "20211123"
        version_int = int(version_str) if isinstance(version_str, str) else version_str

        inner_data = [
            [sexpdata.Symbol("version"), version_int],
            [sexpdata.Symbol("generator"), "circuit-synth"],
            [sexpdata.Symbol("uuid"), schematic_obj.uuid],
            [sexpdata.Symbol("paper"), "A4"],
        ]

        # Add lib_symbols section
        lib_symbols_section = [sexpdata.Symbol("lib_symbols")]
        for lib_id, symbol_sexpr in schematic_obj.lib_symbols.items():
            lib_symbols_section.append(symbol_sexpr)
        inner_data.append(lib_symbols_section)

        # Add logging for test points
        for symbol in self.schematic.components:
            if symbol.lib_id == "Connector:TestPoint":
                logging.info(
                    f"Exporting TestPoint symbol: {symbol.uuid}, Lib ID: {symbol.lib_id}, Properties: {symbol.properties}"
                )
                # Log the S-expression of the lib_symbol if available
                lib_symbol_data = self.schematic.lib_symbols.get(symbol.lib_id)
                if lib_symbol_data:
                    logging.info(
                        f"TestPoint lib_symbol S-expression: {lib_symbol_data}"
                    )
                else:
                    logging.warning(
                        f"No lib_symbol data found for TestPoint: {symbol.lib_id}"
                    )

        # Add hierarchical labels directly to root level
        if hasattr(schematic_obj, "hierarchical_labels"):
            for label in schematic_obj.hierarchical_labels:
                inner_data.append(self.write_hierarchical_label(label))

        # Add components directly to root level
        for component in schematic_obj.components:
            inner_data.append(self.write_component(component))

        # Determine the hierarchical path for this schematic
        hierarchical_path = "/"
        if (
            hasattr(schematic_obj, "hierarchical_path")
            and schematic_obj.hierarchical_path
        ):
            hierarchical_path = schematic_obj.hierarchical_path
        elif (
            hasattr(schematic_obj, "sheet_instances") and schematic_obj.sheet_instances
        ):
            # Try to extract the path from preserved sheet_instances
            for item in schematic_obj.sheet_instances:
                if isinstance(item, list) and len(item) > 1 and str(item[0]) == "path":
                    if isinstance(item[1], str) and item[1] != "/":
                        hierarchical_path = item[1]
                        break

        # Add sheet_instances section
        if hierarchical_path != "/":
            # For hierarchical designs, use the correct path
            sheet_instances = [sexpdata.Symbol("sheet_instances")]
            sheet_instances.append(
                [
                    sexpdata.Symbol("path"),
                    hierarchical_path,
                    [sexpdata.Symbol("page"), "1"],
                ]
            )
            inner_data.append(sheet_instances)
        elif (
            hasattr(schematic_obj, "sheet_instances") and schematic_obj.sheet_instances
        ):
            # Use the preserved sheet_instances from the original schematic
            inner_data.append(schematic_obj.sheet_instances)
        else:
            # Fallback to default for flat designs
            sheet_instances = [sexpdata.Symbol("sheet_instances")]
            sheet_instances.append(
                [sexpdata.Symbol("path"), "/", [sexpdata.Symbol("page"), "1"]]
            )
            inner_data.append(sheet_instances)

        # Add symbol_instances section - rebuild from components with correct hierarchical path
        symbol_instances = [sexpdata.Symbol("symbol_instances")]

        # Build symbol_instances with correct hierarchical paths
        for component in schematic_obj.components:
            # Use hierarchical path for components
            component_path = (
                f"{hierarchical_path}/{component.uuid}"
                if hierarchical_path != "/"
                else f"/{component.uuid}"
            )

            instance = [
                sexpdata.Symbol("path"),
                component_path,
                [sexpdata.Symbol("reference"), component.reference],
                [sexpdata.Symbol("unit"), int(component.unit) if component.unit else 1],
                [sexpdata.Symbol("value"), component.value],
                [sexpdata.Symbol("footprint"), component.footprint or ""],
            ]
            symbol_instances.append(instance)
        inner_data.append(symbol_instances)

        # Now wrap everything in the kicad_sch S-expression
        # This creates a single S-expression: (kicad_sch ...)
        # Create the complete schematic S-expression with kicad_sch as the first element
        # followed by all inner elements (not nested)
        data = [sexpdata.Symbol("kicad_sch")] + inner_data

        try:
            # Validate schematic structure
            if not self._validate_schematic(data):
                logger.error("Invalid schematic structure")
                return False

            logger.info(f"Writing schematic to {filename}")

            # Format and write using the new formatter
            formatted_content = format_kicad_schematic(data)
            with open(str(filename), "w", encoding="utf-8") as f:
                f.write(formatted_content)

            logger.info("Schematic written successfully")
            return True

        except Exception as e:
            logger.error(f"Error writing schematic file: {e}")
            return False

    def _validate_schematic(self, data: List[Any]) -> bool:
        """Validate schematic data structure.

        Args:
            data: S-expression data to validate

        Returns:
            True if the structure is valid
        """
        try:
            # Check for required sections
            required_sections = {
                "version": False,
                "generator": False,
                "uuid": False,
                "paper": False,
            }

            # Track what we've found
            for item in data:
                if not isinstance(item, list):
                    continue

                if len(item) < 1:
                    continue

                section_name = (
                    str(item[0])
                    if isinstance(item[0], sexpdata.Symbol)
                    else str(item[0])
                )
                if section_name in required_sections:
                    required_sections[section_name] = True

            # Check if any required sections are missing
            missing = [name for name, found in required_sections.items() if not found]
            if missing:
                logger.error(f"Missing required sections: {', '.join(missing)}")
                return False

            return True

        except Exception as e:
            logger.error(f"Error validating schematic: {e}")
            return False

    def write_hierarchical_label(self, label: HierarchicalLabel) -> List[Any]:
        """Convert a hierarchical label to KiCad format.

        Args:
            label: HierarchicalLabel object to convert

        Returns:
            S-expression list representing the hierarchical label
        """
        # Create hierarchical_label entry matching KiCad format
        hlabel = [
            sexpdata.Symbol("hierarchical_label"),
            label.name,  # Let the formatter handle quoting
            [sexpdata.Symbol("shape"), sexpdata.Symbol(label.shape)],
            [
                sexpdata.Symbol("at"),
                label.position[0],
                label.position[1],
                0,
            ],  # Add rotation angle (0)
        ]

        # Add effects if present
        if label.effects:
            effects = [sexpdata.Symbol("effects")]
            if "font" in label.effects:
                font_data = label.effects["font"]
                font = [sexpdata.Symbol("font")]
                if "size" in font_data:
                    font.append(
                        [
                            sexpdata.Symbol("size"),
                            font_data["size"][0],
                            font_data["size"][1],
                        ]
                    )
                effects.append(font)
            if "justify" in label.effects:
                effects.append(
                    [
                        sexpdata.Symbol("justify"),
                        sexpdata.Symbol(label.effects["justify"]),
                    ]
                )
            hlabel.append(effects)

        # Add UUID
        hlabel.append([sexpdata.Symbol("uuid"), label.uuid])

        return hlabel

    def write_component(self, component: SchematicSymbol) -> List[Any]:
        """Convert a component to KiCad format.

        Args:
            component: Component object to convert

        Returns:
            S-expression list representing the component
        """
        # Create symbol entry matching KiCad format
        # Default position if none provided
        pos = component.position or (127, 88.9, 0)

        symbol = [
            sexpdata.Symbol("symbol"),
            [sexpdata.Symbol("lib_id"), component.lib_id],
            [sexpdata.Symbol("at"), pos[0], pos[1], pos[2]],
            [sexpdata.Symbol("unit"), int(component.unit) if component.unit else 1],
            [
                sexpdata.Symbol("in_bom"),
                sexpdata.Symbol("yes") if component.in_bom else sexpdata.Symbol("no"),
            ],
            [
                sexpdata.Symbol("on_board"),
                sexpdata.Symbol("yes") if component.on_board else sexpdata.Symbol("no"),
            ],
        ]

        if component.fields_autoplaced:
            symbol.append([sexpdata.Symbol("fields_autoplaced")])

        symbol.append([sexpdata.Symbol("uuid"), component.uuid])

        # Add properties in KiCad format with relative positions
        ref_pos = (pos[0] + 2.54, pos[1] - 1.27, pos[2])
        val_pos = (pos[0] + 2.54, pos[1] + 1.27, pos[2])

        symbol.append(
            [
                sexpdata.Symbol("property"),
                "Reference",
                component.reference,
                [sexpdata.Symbol("id"), 0],
                [sexpdata.Symbol("at"), ref_pos[0], ref_pos[1], ref_pos[2]],
                [
                    sexpdata.Symbol("effects"),
                    [sexpdata.Symbol("font"), [sexpdata.Symbol("size"), 1.27, 1.27]],
                    [sexpdata.Symbol("justify"), sexpdata.Symbol("left")],
                ],
            ]
        )

        symbol.append(
            [
                sexpdata.Symbol("property"),
                "Value",
                component.value,
                [sexpdata.Symbol("id"), 1],
                [sexpdata.Symbol("at"), val_pos[0], val_pos[1], val_pos[2]],
                [
                    sexpdata.Symbol("effects"),
                    [sexpdata.Symbol("font"), [sexpdata.Symbol("size"), 1.27, 1.27]],
                    [sexpdata.Symbol("justify"), sexpdata.Symbol("left")],
                ],
            ]
        )

        # Add pins with UUIDs
        for pin in component.pins:
            symbol.append(
                [
                    sexpdata.Symbol("pin"),
                    pin.number,
                    [sexpdata.Symbol("uuid"), pin.uuid or str(uuid.uuid4())],
                ]
            )

        # Add instances section - this is critical for KiCad to properly display references
        if self.project_name and hasattr(self.schematic, "uuid"):
            instances = [sexpdata.Symbol("instances")]
            instance = [
                sexpdata.Symbol("project"),
                self.project_name,
                [
                    sexpdata.Symbol("path"),
                    f"/{self.schematic.uuid}",
                    [sexpdata.Symbol("reference"), component.reference],
                    [
                        sexpdata.Symbol("unit"),
                        int(component.unit) if component.unit else 1,
                    ],
                ],
            ]
            instances.append(instance)
            symbol.append(instances)

        return symbol

    def write_net(self, net: SchematicNet) -> List[Any]:
        """Convert a net to KiCad format.

        Args:
            net: Net object to convert

        Returns:
            S-expression list representing the net
        """
        net_expr = [
            sexpdata.Symbol("net"),
            [sexpdata.Symbol("name"), net.name],
            [sexpdata.Symbol("uuid"), net.uuid],
        ]

        # Add path if hierarchical
        if net.full_path != f"/{net.name}":
            net_expr.append([sexpdata.Symbol("path"), net.full_path])

        # Add nodes
        for node in net.nodes:
            node_expr = [
                sexpdata.Symbol("node"),
                [sexpdata.Symbol("ref"), node.component_ref],
                [sexpdata.Symbol("pin"), node.pin_num],
                [sexpdata.Symbol("pintype"), node.pin_type],
                [sexpdata.Symbol("uuid"), node.uuid],
            ]
            net_expr.append(node_expr)

        return net_expr

    def write_sheet(self, sheet: SchematicSheet) -> List[Any]:
        """Convert a hierarchical sheet to KiCad format.

        Args:
            sheet: Sheet object to convert

        Returns:
            S-expression list representing the sheet
        """
        sheet_expr = [
            sexpdata.Symbol("sheet"),
            [sexpdata.Symbol("at"), 127, 88.9],  # Default position
            [sexpdata.Symbol("size"), 20, 20],  # Default size
            [sexpdata.Symbol("fields_autoplaced")],
            [
                sexpdata.Symbol("stroke"),
                [sexpdata.Symbol("width"), 0.1524],
                [sexpdata.Symbol("type"), "solid"],
                [sexpdata.Symbol("color"), 0, 0, 0, 0],
            ],
            [sexpdata.Symbol("fill"), [sexpdata.Symbol("type"), "none"]],
            [sexpdata.Symbol("uuid"), sheet.uuid],
            [
                sexpdata.Symbol("property"),
                "Sheet name",
                sheet.name,
                [sexpdata.Symbol("id"), 0],
                [sexpdata.Symbol("at"), 127, 87.1984, 0],
                [
                    sexpdata.Symbol("effects"),
                    [sexpdata.Symbol("font"), [sexpdata.Symbol("size"), 1.27, 1.27]],
                ],
            ],
            [
                sexpdata.Symbol("property"),
                "Sheet file",
                sheet.path,
                [sexpdata.Symbol("id"), 1],
                [sexpdata.Symbol("at"), 127, 90.6984, 0],
                [
                    sexpdata.Symbol("effects"),
                    [sexpdata.Symbol("font"), [sexpdata.Symbol("size"), 1.27, 1.27]],
                ],
            ],
        ]

        return sheet_expr

    def _ensure_required_sections(self, data: List[Any]) -> List[Any]:
        """Ensure all required sections are present in the schematic.

        Args:
            data: S-expression data to check

        Returns:
            Data with required sections added if missing
        """
        # Required sections with default values
        required = {
            "version": [sexpdata.Symbol("version"), "20211123"],
            "generator": [sexpdata.Symbol("generator"), "circuit-synth"],
            "uuid": [sexpdata.Symbol("uuid"), "00000000-0000-0000-0000-000000000000"],
            "paper": [sexpdata.Symbol("paper"), "A4"],
        }

        # Track what we've found
        found_sections = set()
        for item in data:
            if isinstance(item, list) and item:
                section_name = (
                    str(item[0])
                    if isinstance(item[0], sexpdata.Symbol)
                    else str(item[0])
                )
                found_sections.add(section_name)

        # Add any missing sections
        result = list(data)  # Make a copy
        for name, default_value in required.items():
            if name not in found_sections:
                result.append(default_value)

        return result

    def _format_schematic(self, data: List[Any]) -> List[Any]:
        """Format schematic data for output.

        Args:
            data: S-expression data to format

        Returns:
            Formatted data
        """
        # Ensure required sections
        data = self._ensure_required_sections(data)

        # Sort sections in standard order
        section_order = [
            "kicad_sch",
            "version",
            "generator",
            "uuid",
            "paper",
            "lib_symbols",
            "symbol",  # Individual components
            "sheet_instances",
            "symbol_instances",  # Component instance mappings
        ]

        # Group items by section
        sections = {}
        other_items = []

        for item in data:
            if isinstance(item, list) and item:
                section_name = (
                    str(item[0])
                    if isinstance(item[0], sexpdata.Symbol)
                    else str(item[0])
                )
                if section_name in section_order:
                    if section_name not in sections:
                        sections[section_name] = []
                    sections[section_name].append(item)
                else:
                    other_items.append(item)
            else:
                other_items.append(item)

        # Rebuild in correct order
        result = []
        for section in section_order:
            if section in sections:
                result.extend(sections[section])
        result.extend(other_items)

        return result
