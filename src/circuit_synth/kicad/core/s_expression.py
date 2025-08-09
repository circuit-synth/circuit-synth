"""
S-expression parser for KiCad files using sexpdata library.

This module provides parsing and writing capabilities for KiCad's S-expression format,
built on top of the sexpdata library.
"""

import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import sexpdata

from ..core.types import (
    Junction,
    Label,
    LabelType,
    Net,
    Point,
    Rectangle,
    Schematic,
    SchematicPin,
    SchematicSymbol,
    Sheet,
    SheetPin,
    SymbolInstance,
    Wire,
)
from .clean_formatter import CleanSExprFormatter
from .symbol_cache import get_symbol_cache

logger = logging.getLogger(__name__)


class SExpressionParser:
    """
    S-expression parser for KiCad schematic files using sexpdata.

    This parser handles reading and writing KiCad's S-expression format,
    providing conversion between S-expressions and our internal data structures.
    """

    def __init__(self):
        """Initialize the parser."""
        self._clean_formatter = CleanSExprFormatter()
        logger.info("S-expression parser initialized with clean formatter")

    def parse_file(self, filepath: Union[str, Path]) -> Schematic:
        """
        Parse a KiCad schematic file.

        Args:
            filepath: Path to the .kicad_sch file

        Returns:
            Schematic object

        Raises:
            FileNotFoundError: If file doesn't exist
            Exception: If parsing fails
        """
        filepath = Path(filepath)
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            sexp_data = self.parse_string(content)
            return self.to_schematic(sexp_data)
        except Exception as e:
            logger.error(f"Error parsing {filepath}: {e}")
            raise

    def parse_string(self, content: str) -> Any:
        """
        Parse S-expression content from a string.

        Args:
            content: S-expression string content

        Returns:
            Parsed S-expression data structure
        """
        return sexpdata.loads(content)

    def write_file(self, data: Any, filepath: Union[str, Path]):
        """
        Write S-expression data to a file.

        Args:
            data: S-expression data structure
            filepath: Path to write to
        """
        filepath = Path(filepath)
        content = self.dumps(data)

        # Ensure directory exists
        filepath.parent.mkdir(parents=True, exist_ok=True)

        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

    def dumps(self, data: Any) -> str:
        """
        Convert data structure to S-expression string.

        Args:
            data: Data structure to convert

        Returns:
            S-expression string
        """
        # Convert to plain lists for clean formatter
        converted = self._convert_to_plain_lists(data)
        return self._clean_formatter.format(converted)

    def _convert_to_plain_lists(self, data: Any) -> Any:
        """Convert sexpdata format to plain Python lists.

        Args:
            data: Data in sexpdata format

        Returns:
            Data as plain Python lists/values
        """
        if isinstance(data, sexpdata.Symbol):
            return str(data)
        elif isinstance(data, (list, tuple)):
            return [self._convert_to_plain_lists(item) for item in data]
        else:
            return data

    def to_schematic(self, sexp_data: List) -> Schematic:
        """
        Convert S-expression data to Schematic object.

        Args:
            sexp_data: Parsed S-expression data

        Returns:
            Schematic object
        """
        # This is a placeholder - actual implementation would parse the S-expression
        # and build up the Schematic object with all its components
        schematic = Schematic()

        # Parse top-level elements
        for item in sexp_data:
            if not isinstance(item, list):
                continue

            tag = (
                str(item[0]) if item and isinstance(item[0], sexpdata.Symbol) else None
            )

            if tag == "version":
                schematic.version = str(item[1]) if len(item) > 1 else ""
            elif tag == "generator":
                schematic.generator = str(item[1]) if len(item) > 1 else ""
            elif tag == "symbol":
                # Parse symbol instances
                symbol = self._parse_symbol(item)
                if symbol:
                    schematic.components.append(symbol)
            elif tag == "wire":
                # Parse wires
                wire = self._parse_wire(item)
                if wire:
                    schematic.wires.append(wire)
            elif tag == "junction":
                # Parse junctions
                junction = self._parse_junction(item)
                if junction:
                    schematic.junctions.append(junction)
            elif tag == "label":
                # Parse labels
                label = self._parse_label(item)
                if label:
                    schematic.labels.append(label)
            elif tag == "sheet":
                # Parse hierarchical sheets
                sheet = self._parse_sheet(item)
                if sheet:
                    schematic.sheets.append(sheet)

        return schematic

    def _parse_symbol(self, sexp: List) -> Optional[SchematicSymbol]:
        """Parse a symbol S-expression."""
        logger.debug("=" * 60)
        logger.debug("PARSING SYMBOL - Starting")
        logger.debug(f"  Input type: {type(sexp)}")
        logger.debug(
            f"  Input length: {len(sexp) if isinstance(sexp, list) else 'N/A'}"
        )

        try:
            # Skip if this is not a symbol instance (could be lib_symbol definition)
            if not isinstance(sexp, list) or len(sexp) < 2:
                logger.debug("  SKIP: Not a list or too short")
                return None

            # Check if first element is 'symbol' (without checking for Symbol type)
            first_elem = str(sexp[0]) if sexp else None
            logger.debug(f"  First element: '{first_elem}' (type: {type(sexp[0])})")

            if first_elem != "symbol":
                logger.debug(f"  SKIP: First element is not 'symbol'")
                return None

            # Look for lib_id to distinguish from lib_symbols definitions
            lib_id = None
            reference = None
            value = None
            footprint = None
            position = Point(0, 0)
            rotation = 0.0
            unit = 1
            in_bom = True
            on_board = True
            uuid_str = None

            logger.debug("  Scanning sub-elements...")
            for item in sexp[1:]:
                if not isinstance(item, list) or len(item) < 2:
                    logger.debug(f"    Skipping non-list or short item: {item}")
                    continue

                tag = str(item[0]) if item else None
                logger.debug(f"    Found tag: '{tag}'")

                if tag == "lib_id":
                    lib_id = str(item[1]) if len(item) > 1 else None
                    logger.debug(f"      lib_id = '{lib_id}'")

                elif tag == "at":
                    # Parse position: (at x y rotation)
                    if len(item) >= 3:
                        try:
                            x = float(item[1])
                            y = float(item[2])
                            position = Point(x, y)
                            if len(item) > 3:
                                rotation = float(item[3])
                            logger.debug(
                                f"      position = ({x}, {y}), rotation = {rotation}"
                            )
                        except (ValueError, TypeError) as e:
                            logger.debug(f"      ERROR parsing position: {e}")

                elif tag == "unit":
                    if len(item) > 1:
                        try:
                            unit = int(item[1])
                            logger.debug(f"      unit = {unit}")
                        except (ValueError, TypeError):
                            logger.debug(f"      ERROR parsing unit: {item[1]}")

                elif tag == "uuid":
                    uuid_str = str(item[1]) if len(item) > 1 else None
                    logger.debug(f"      uuid = '{uuid_str}'")

                elif tag == "in_bom":
                    val = str(item[1]) if len(item) > 1 else "yes"
                    in_bom = val == "yes"
                    logger.debug(f"      in_bom = {in_bom}")

                elif tag == "on_board":
                    val = str(item[1]) if len(item) > 1 else "yes"
                    on_board = val == "yes"
                    logger.debug(f"      on_board = {on_board}")

                elif tag == "property":
                    # Parse properties: (property "Name" "Value" ...)
                    if len(item) >= 3:
                        prop_name = str(item[1])
                        prop_value = str(item[2])
                        logger.debug(f"      property '{prop_name}' = '{prop_value}'")

                        if prop_name == "Reference":
                            reference = prop_value
                        elif prop_name == "Value":
                            value = prop_value
                        elif prop_name == "Footprint":
                            footprint = prop_value

            # Only create symbol if we have a lib_id (indicates it's a component instance)
            if lib_id:
                logger.debug("  Creating SchematicSymbol:")
                logger.debug(f"    lib_id: '{lib_id}'")
                logger.debug(f"    reference: '{reference}'")
                logger.debug(f"    value: '{value}'")
                logger.debug(f"    footprint: '{footprint}'")
                logger.debug(f"    position: {position}")
                logger.debug(f"    unit: {unit}")

                symbol = SchematicSymbol(
                    reference=reference or "",
                    value=value or "",
                    lib_id=lib_id,
                    position=position,
                    rotation=rotation,
                    footprint=footprint,
                    unit=unit,
                    in_bom=in_bom,
                    on_board=on_board,
                    uuid=uuid_str or str(uuid.uuid4()),
                )
                logger.debug(f"  SUCCESS: Created symbol {reference}")
                return symbol
            else:
                logger.debug(
                    "  SKIP: No lib_id found, probably a lib_symbol definition"
                )
                return None

        except Exception as e:
            logger.error(f"  ERROR parsing symbol: {e}")
            import traceback

            logger.error(traceback.format_exc())
            return None

    def _parse_wire(self, sexp: List) -> Optional[Wire]:
        """Parse a wire S-expression."""
        # Placeholder implementation
        return None

    def _parse_junction(self, sexp: List) -> Optional[Junction]:
        """Parse a junction S-expression."""
        # Placeholder implementation
        return None

    def _parse_label(self, sexp: List) -> Optional[Label]:
        """Parse a label S-expression."""
        # Placeholder implementation
        return None

    def _parse_sheet(self, sexp: List) -> Optional[Sheet]:
        """Parse a sheet S-expression."""
        # Placeholder implementation
        return None

    def from_schematic(self, schematic: Schematic) -> List:
        """
        Convert Schematic object to S-expression data.

        Args:
            schematic: Schematic object

        Returns:
            S-expression data structure
        """
        # Placeholder implementation
        result = [sexpdata.Symbol("kicad_sch")]

        # Add version
        if schematic.version:
            result.append([sexpdata.Symbol("version"), schematic.version])

        # Add generator
        if schematic.generator:
            result.append([sexpdata.Symbol("generator"), schematic.generator])

        # Add generator_version (required for KiCad 9)
        result.append([sexpdata.Symbol("generator_version"), "9.0"])

        # Add UUID (required for proper reference assignment)
        if hasattr(schematic, "uuid") and schematic.uuid:
            result.append([sexpdata.Symbol("uuid"), schematic.uuid])

        # Add paper size (required for lib_symbols insertion point)
        result.append([sexpdata.Symbol("paper"), "A4"])

        # Add lib_symbols placeholder (will be populated later)
        result.append([sexpdata.Symbol("lib_symbols")])

        # Add components (symbols) - only if they have content
        for component in schematic.components:
            sexp = self._symbol_to_sexp(component)
            # Only add non-empty symbols
            if sexp and len(sexp) > 1:
                result.append(sexp)

        # Add wires - only if they have content
        for wire in schematic.wires:
            sexp = self._wire_to_sexp(wire)
            if sexp and len(sexp) > 1:
                result.append(sexp)

        # Add junctions - only if they have content
        for junction in schematic.junctions:
            sexp = self._junction_to_sexp(junction)
            if sexp and len(sexp) > 1:
                result.append(sexp)

        # Add labels - only if they have content
        for label in schematic.labels:
            sexp = self._label_to_sexp(label)
            if sexp and len(sexp) > 1:
                result.append(sexp)

        # Add sheets - only if they have content
        for sheet in schematic.sheets:
            sexp = self._sheet_to_sexp(sheet)
            if sexp and len(sexp) > 1:
                result.append(sexp)

        # Add sheet_instances placeholder (will be populated later)
        result.append([sexpdata.Symbol("sheet_instances")])

        return result

    def _symbol_to_sexp(self, symbol: SchematicSymbol) -> List:
        """Convert a SchematicSymbol to S-expression."""
        logger.debug(
            f"_symbol_to_sexp: Converting symbol {symbol.reference} at ({symbol.position.x}, {symbol.position.y})"
        )

        result = [sexpdata.Symbol("symbol")]

        # Add lib_id
        result.append([sexpdata.Symbol("lib_id"), symbol.lib_id])

        # Add position (at x y angle) - always include angle for KiCad compatibility
        at_expr = [
            sexpdata.Symbol("at"),
            symbol.position.x,
            symbol.position.y,
            symbol.rotation,
        ]
        result.append(at_expr)

        # Add unit
        result.append([sexpdata.Symbol("unit"), symbol.unit])

        # Add exclude_from_sim
        result.append([sexpdata.Symbol("exclude_from_sim"), sexpdata.Symbol("no")])

        # Add in_bom/on_board/dnp flags
        result.append(
            [
                sexpdata.Symbol("in_bom"),
                sexpdata.Symbol("yes") if symbol.in_bom else sexpdata.Symbol("no"),
            ]
        )
        result.append(
            [
                sexpdata.Symbol("on_board"),
                sexpdata.Symbol("yes") if symbol.on_board else sexpdata.Symbol("no"),
            ]
        )
        result.append(
            [
                sexpdata.Symbol("dnp"),
                sexpdata.Symbol("yes") if symbol.dnp else sexpdata.Symbol("no"),
            ]
        )

        # Add fields_autoplaced
        result.append([sexpdata.Symbol("fields_autoplaced"), sexpdata.Symbol("yes")])

        # Add UUID
        result.append([sexpdata.Symbol("uuid"), symbol.uuid])

        # Add properties
        if symbol.reference:
            prop = [sexpdata.Symbol("property"), "Reference", symbol.reference]
            prop.append(
                [sexpdata.Symbol("at"), symbol.position.x, symbol.position.y - 5, 0]
            )
            prop.append(
                [
                    sexpdata.Symbol("effects"),
                    [sexpdata.Symbol("font"), [sexpdata.Symbol("size"), 1.27, 1.27]],
                    [sexpdata.Symbol("justify"), sexpdata.Symbol("left")],
                ]
            )
            result.append(prop)

        if symbol.value:
            prop = [sexpdata.Symbol("property"), "Value", str(symbol.value)]
            prop.append(
                [sexpdata.Symbol("at"), symbol.position.x, symbol.position.y + 5, 0]
            )
            prop.append(
                [
                    sexpdata.Symbol("effects"),
                    [sexpdata.Symbol("font"), [sexpdata.Symbol("size"), 1.27, 1.27]],
                    [sexpdata.Symbol("justify"), sexpdata.Symbol("left")],
                ]
            )
            result.append(prop)

        if symbol.footprint:
            prop = [sexpdata.Symbol("property"), "Footprint", symbol.footprint]
            prop.append(
                [sexpdata.Symbol("at"), symbol.position.x, symbol.position.y + 10, 0]
            )
            prop.append(
                [
                    sexpdata.Symbol("effects"),
                    [sexpdata.Symbol("font"), [sexpdata.Symbol("size"), 1.27, 1.27]],
                    [sexpdata.Symbol("hide"), sexpdata.Symbol("yes")],
                ]
            )
            result.append(prop)

        # Add instances
        if hasattr(symbol, "instances") and symbol.instances:
            logger.debug(
                f"  Creating instances S-expression for {len(symbol.instances)} instance(s)"
            )
            instances_sexp = [sexpdata.Symbol("instances")]

            # Group instances by project
            project_instances = {}
            for instance in symbol.instances:
                if instance.project not in project_instances:
                    project_instances[instance.project] = []
                project_instances[instance.project].append(instance)

            # Create project blocks
            for project_name, project_inst_list in project_instances.items():
                for inst in project_inst_list:
                    project_block = [
                        sexpdata.Symbol("project"),
                        project_name,
                        [
                            sexpdata.Symbol("path"),
                            inst.path,
                            [sexpdata.Symbol("reference"), inst.reference],
                            [sexpdata.Symbol("unit"), inst.unit],
                        ],
                    ]
                    instances_sexp.append(project_block)

            result.append(instances_sexp)
        else:
            # Create default instances for new symbols
            logger.debug(f"  Creating default instances for symbol {symbol.reference}")
            instances_sexp = [sexpdata.Symbol("instances")]

            # Get project name from schematic or use default
            project_name = getattr(symbol, "_project_name", "")
            if not project_name:
                # Try to get from parent schematic
                project_name = getattr(self, "_current_project_name", "")

            # Get the hierarchical path
            hier_path = getattr(symbol, "hierarchical_path", "/")
            if not hier_path:
                hier_path = "/"

            # Create default instance
            project_block = [
                sexpdata.Symbol("project"),
                project_name,  # Empty string for default project
                [
                    sexpdata.Symbol("path"),
                    hier_path,
                    [sexpdata.Symbol("reference"), symbol.reference],
                    [sexpdata.Symbol("unit"), symbol.unit],
                ],
            ]
            instances_sexp.append(project_block)
            result.append(instances_sexp)
            logger.debug(f"  Default instances created for symbol {symbol.reference}")

        return result

    def _wire_to_sexp(self, wire: Wire) -> List:
        """Convert a wire to S-expression."""
        sexp = [sexpdata.Symbol("wire")]

        # Add points
        pts = [sexpdata.Symbol("pts")]
        for point in wire.points:
            pts.append([sexpdata.Symbol("xy"), point.x, point.y])
        sexp.append(pts)

        # Add stroke
        stroke = [sexpdata.Symbol("stroke")]
        stroke.append([sexpdata.Symbol("width"), wire.stroke_width])
        # Stroke type must be a symbol, not a string
        stroke_type = (
            sexpdata.Symbol(wire.stroke_type)
            if wire.stroke_type
            else sexpdata.Symbol("default")
        )
        stroke.append([sexpdata.Symbol("type"), stroke_type])
        sexp.append(stroke)

        # Add UUID
        sexp.append([sexpdata.Symbol("uuid"), wire.uuid])

        return sexp

    def _sheet_to_sexp(self, sheet: Sheet) -> List:
        """Convert a sheet to S-expression."""
        sexp = [sexpdata.Symbol("sheet")]

        # Add position
        sexp.append([sexpdata.Symbol("at"), sheet.position.x, sheet.position.y])

        # Add size
        sexp.append([sexpdata.Symbol("size"), sheet.size[0], sheet.size[1]])

        # Add stroke
        stroke = [sexpdata.Symbol("stroke")]
        stroke.append([sexpdata.Symbol("width"), 0.12])
        stroke.append([sexpdata.Symbol("type"), sexpdata.Symbol("solid")])
        sexp.append(stroke)

        # Add fill
        sexp.append([sexpdata.Symbol("fill"), [sexpdata.Symbol("color"), 0, 0, 0, 0.0]])

        # Add UUID
        sexp.append([sexpdata.Symbol("uuid"), sheet.uuid])

        # Add sheet name property
        if sheet.name:
            prop = [sexpdata.Symbol("property"), "Sheetname", sheet.name]
            prop.append(
                [sexpdata.Symbol("at"), sheet.position.x, sheet.position.y - 1.27, 0]
            )
            prop.append(
                [
                    sexpdata.Symbol("effects"),
                    [sexpdata.Symbol("font"), [sexpdata.Symbol("size"), 1.27, 1.27]],
                    [
                        sexpdata.Symbol("justify"),
                        sexpdata.Symbol("left"),
                        sexpdata.Symbol("bottom"),
                    ],
                ]
            )
            sexp.append(prop)

        # Add sheet file property
        if sheet.filename:
            prop = [sexpdata.Symbol("property"), "Sheetfile", sheet.filename]
            prop.append(
                [
                    sexpdata.Symbol("at"),
                    sheet.position.x,
                    sheet.position.y + sheet.size[1] + 1.27,
                    0,
                ]
            )
            prop.append(
                [
                    sexpdata.Symbol("effects"),
                    [sexpdata.Symbol("font"), [sexpdata.Symbol("size"), 1.27, 1.27]],
                    [
                        sexpdata.Symbol("justify"),
                        sexpdata.Symbol("left"),
                        sexpdata.Symbol("top"),
                    ],
                    [sexpdata.Symbol("hide"), sexpdata.Symbol("yes")],
                ]
            )
            sexp.append(prop)

        # Add sheet pins
        for pin in sheet.pins:
            # Pin shape (electrical type) must be an unquoted symbol
            pin_sexp = [sexpdata.Symbol("pin"), pin.name, sexpdata.Symbol(pin.shape)]
            at_expr = [
                sexpdata.Symbol("at"),
                pin.position.x,
                pin.position.y,
                pin.orientation,
            ]
            logger.debug(f"Creating 'at' expression for pin '{pin.name}': {at_expr}")
            pin_sexp.append(at_expr)
            pin_sexp.append(
                [
                    sexpdata.Symbol("effects"),
                    [sexpdata.Symbol("font"), [sexpdata.Symbol("size"), 1.27, 1.27]],
                    [sexpdata.Symbol("justify"), sexpdata.Symbol("right")],
                ]
            )
            pin_sexp.append([sexpdata.Symbol("uuid"), str(uuid.uuid4())])
            logger.debug(f"Complete pin_sexp for '{pin.name}': {pin_sexp}")
            sexp.append(pin_sexp)

        # Add instances section for new KiCad format
        # Sheets need the actual project name in their instances
        instances = [sexpdata.Symbol("instances")]
        # Get the project name from the schematic if available
        project_name = getattr(
            sheet, "_project_name", "circuit_synth"
        )  # fallback to circuit_synth if not set
        project_instance = [
            sexpdata.Symbol("project"),
            project_name,
            [sexpdata.Symbol("path"), "/", [sexpdata.Symbol("page"), "1"]],
        ]
        instances.append(project_instance)
        sexp.append(instances)

        return sexp

    def _generate_lib_symbols(self, schematic: Schematic) -> Optional[List]:
        """Generate lib_symbols section with symbol definitions."""
        if not schematic.components:
            return None

        lib_symbols = [sexpdata.Symbol("lib_symbols")]

        # Track which symbols we've already added
        added_symbols = set()
        symbol_cache = get_symbol_cache()

        for component in schematic.components:
            lib_id = component.lib_id
            if lib_id in added_symbols:
                continue
            added_symbols.add(lib_id)

            # Get symbol from cache
            symbol_def_obj = symbol_cache.get_symbol(lib_id)
            if symbol_def_obj:
                symbol_def = self._symbol_definition_to_sexp(symbol_def_obj)
                lib_symbols.append(symbol_def)
            else:
                logger.warning(f"Symbol {lib_id} not found in symbol cache")
                continue

        return lib_symbols if len(lib_symbols) > 1 else None

    def _symbol_definition_to_sexp(self, symbol_def) -> List:
        """Convert a SymbolDefinition object to S-expression format."""
        sexp = [sexpdata.Symbol("symbol"), symbol_def.lib_id]

        # Add basic properties
        # For KiCad compatibility, pin_numbers uses special format: (pin_numbers (hide yes))
        sexp.append(
            [
                sexpdata.Symbol("pin_numbers"),
                [sexpdata.Symbol("hide"), sexpdata.Symbol("yes")],
            ]
        )
        sexp.append([sexpdata.Symbol("pin_names"), [sexpdata.Symbol("offset"), 0]])
        sexp.append([sexpdata.Symbol("exclude_from_sim"), sexpdata.Symbol("no")])
        sexp.append([sexpdata.Symbol("in_bom"), sexpdata.Symbol("yes")])
        sexp.append([sexpdata.Symbol("on_board"), sexpdata.Symbol("yes")])

        # Add properties
        properties = [
            ("Reference", symbol_def.reference_prefix, [0, 0, 0]),
            ("Value", symbol_def.name, [0, -2.54, 0]),
            ("Footprint", "", [0, -5.08, 0]),
            ("Datasheet", symbol_def.datasheet or "~", [0, -7.62, 0]),
            ("Description", symbol_def.description, [0, -10.16, 0]),
        ]

        if symbol_def.keywords:
            properties.append(("ki_keywords", symbol_def.keywords, [0, -12.7, 0]))

        for prop_name, prop_value, position in properties:
            prop = [sexpdata.Symbol("property"), prop_name, prop_value]
            prop.append([sexpdata.Symbol("at"), position[0], position[1], position[2]])
            effects = [
                sexpdata.Symbol("effects"),
                [sexpdata.Symbol("font"), [sexpdata.Symbol("size"), 1.27, 1.27]],
            ]
            if prop_name not in ["Reference", "Value"]:
                effects.append([sexpdata.Symbol("hide"), sexpdata.Symbol("yes")])
            prop.append(effects)
            sexp.append(prop)

        # Add graphic elements sub-symbol
        if symbol_def.graphic_elements:
            # Extract symbol name from lib_id (e.g., "Device:R" -> "R")
            symbol_name = (
                symbol_def.lib_id.split(":")[-1]
                if ":" in symbol_def.lib_id
                else symbol_def.lib_id
            )
            graphics_symbol = [sexpdata.Symbol("symbol"), f"{symbol_name}_0_1"]
            for i, element in enumerate(symbol_def.graphic_elements):
                graphic_sexp = self._graphic_element_to_sexp(element)
                graphics_symbol.append(graphic_sexp)
            sexp.append(graphics_symbol)

        # Add pins sub-symbol
        if symbol_def.pins:
            # Extract symbol name from lib_id (e.g., "Device:R" -> "R")
            symbol_name = (
                symbol_def.lib_id.split(":")[-1]
                if ":" in symbol_def.lib_id
                else symbol_def.lib_id
            )
            pins_symbol = [sexpdata.Symbol("symbol"), f"{symbol_name}_1_1"]

            # Track which position/name combinations we've seen to hide duplicates
            seen_positions = {}

            for pin in symbol_def.pins:
                # Create a key based on position and name
                pos_key = f"{pin.position.x},{pin.position.y},{pin.name}"

                # Check if this is a duplicate position/name combination
                is_duplicate = pos_key in seen_positions
                if not is_duplicate:
                    seen_positions[pos_key] = pin.number

                pin_sexp = [
                    sexpdata.Symbol("pin"),
                    sexpdata.Symbol(
                        pin.type
                    ),  # electrical type (passive, input, output, etc.)
                    sexpdata.Symbol("line"),  # graphic style
                ]

                # Add (hide yes) for duplicate pins
                if is_duplicate:
                    pin_sexp.append([sexpdata.Symbol("hide"), sexpdata.Symbol("yes")])
                pin_sexp.extend(
                    [
                        [
                            sexpdata.Symbol("at"),
                            pin.position.x,
                            pin.position.y,
                            pin.orientation,
                        ],
                        [sexpdata.Symbol("length"), pin.length],
                        [
                            sexpdata.Symbol("name"),
                            str(pin.name),
                            [
                                sexpdata.Symbol("effects"),
                                [
                                    sexpdata.Symbol("font"),
                                    [sexpdata.Symbol("size"), 1.27, 1.27],
                                ],
                            ],
                        ],
                        # Pin number MUST be a quoted string
                        [
                            sexpdata.Symbol("number"),
                            str(pin.number),
                            [
                                sexpdata.Symbol("effects"),
                                [
                                    sexpdata.Symbol("font"),
                                    [sexpdata.Symbol("size"), 1.27, 1.27],
                                ],
                            ],
                        ],
                    ]
                )

                pins_symbol.append(pin_sexp)
            sexp.append(pins_symbol)

        sexp.append([sexpdata.Symbol("embedded_fonts"), sexpdata.Symbol("no")])
        return sexp

    def _graphic_element_to_sexp(self, element: Dict[str, Any]) -> List:
        """Convert a graphic element to S-expression format."""
        elem_type = element.get("type", "")

        if elem_type == "rectangle":
            return [
                sexpdata.Symbol("rectangle"),
                [
                    sexpdata.Symbol("start"),
                    element["start"]["x"],
                    element["start"]["y"],
                ],
                [sexpdata.Symbol("end"), element["end"]["x"], element["end"]["y"]],
                [
                    sexpdata.Symbol("stroke"),
                    [sexpdata.Symbol("width"), element.get("stroke_width", 0.254)],
                    [
                        sexpdata.Symbol("type"),
                        sexpdata.Symbol(element.get("stroke_type", "default")),
                    ],
                ],
                [
                    sexpdata.Symbol("fill"),
                    [
                        sexpdata.Symbol("type"),
                        sexpdata.Symbol(element.get("fill_type", "none")),
                    ],
                ],
            ]
        elif elem_type == "polyline":
            pts = [sexpdata.Symbol("pts")]
            for point in element.get("points", []):
                pts.append([sexpdata.Symbol("xy"), point["x"], point["y"]])
            return [
                sexpdata.Symbol("polyline"),
                pts,
                [
                    sexpdata.Symbol("stroke"),
                    [sexpdata.Symbol("width"), element.get("stroke_width", 0.254)],
                    [
                        sexpdata.Symbol("type"),
                        sexpdata.Symbol(element.get("stroke_type", "default")),
                    ],
                ],
                [
                    sexpdata.Symbol("fill"),
                    [
                        sexpdata.Symbol("type"),
                        sexpdata.Symbol(element.get("fill_type", "none")),
                    ],
                ],
            ]
        elif elem_type == "circle":
            circle_sexp = [sexpdata.Symbol("circle")]

            # Center is required for circles
            if "center" in element and element["center"]:
                circle_sexp.append(
                    [
                        sexpdata.Symbol("center"),
                        element["center"]["x"],
                        element["center"]["y"],
                    ]
                )
            else:
                # Default center at origin if missing
                circle_sexp.append([sexpdata.Symbol("center"), 0, 0])

            # Radius is required
            circle_sexp.append([sexpdata.Symbol("radius"), element.get("radius", 1.0)])

            # Add stroke and fill
            circle_sexp.extend(
                [
                    [
                        sexpdata.Symbol("stroke"),
                        [sexpdata.Symbol("width"), element.get("stroke_width", 0.254)],
                        [
                            sexpdata.Symbol("type"),
                            sexpdata.Symbol(element.get("stroke_type", "default")),
                        ],
                    ],
                    [
                        sexpdata.Symbol("fill"),
                        [
                            sexpdata.Symbol("type"),
                            sexpdata.Symbol(element.get("fill_type", "none")),
                        ],
                    ],
                ]
            )
            return circle_sexp
        elif elem_type == "arc":
            arc_sexp = [
                sexpdata.Symbol("arc"),
                [
                    sexpdata.Symbol("start"),
                    element["start"]["x"],
                    element["start"]["y"],
                ],
            ]

            # Mid point is optional for arcs
            if "mid" in element and element["mid"]:
                arc_sexp.append(
                    [sexpdata.Symbol("mid"), element["mid"]["x"], element["mid"]["y"]]
                )

            arc_sexp.extend(
                [
                    [sexpdata.Symbol("end"), element["end"]["x"], element["end"]["y"]],
                    [
                        sexpdata.Symbol("stroke"),
                        [sexpdata.Symbol("width"), element.get("stroke_width", 0.254)],
                        [
                            sexpdata.Symbol("type"),
                            sexpdata.Symbol(element.get("stroke_type", "default")),
                        ],
                    ],
                    [
                        sexpdata.Symbol("fill"),
                        [
                            sexpdata.Symbol("type"),
                            sexpdata.Symbol(element.get("fill_type", "none")),
                        ],
                    ],
                ]
            )
            return arc_sexp
        else:
            logger.warning(f"Unknown graphic element type: {elem_type}")
            return []

    def _label_to_sexp(self, label: Label) -> List:
        """Convert a label to S-expression."""
        # Determine the symbol name based on label type
        if label.label_type == LabelType.GLOBAL:
            symbol_name = "global_label"
        elif label.label_type == LabelType.HIERARCHICAL:
            symbol_name = "hierarchical_label"
        else:
            symbol_name = "label"

        sexp = [sexpdata.Symbol(symbol_name), label.text]

        # Add shape for hierarchical labels
        if label.label_type == LabelType.HIERARCHICAL:
            sexp.append([sexpdata.Symbol("shape"), sexpdata.Symbol("input")])

        # Add position - always include orientation for KiCad compatibility
        at_expr = [
            sexpdata.Symbol("at"),
            label.position.x,
            label.position.y,
            int(label.orientation),
        ]
        sexp.append(at_expr)

        # Add effects
        effects = [sexpdata.Symbol("effects")]
        effects.append([sexpdata.Symbol("font"), [sexpdata.Symbol("size"), 1.27, 1.27]])

        # Add justification based on orientation
        # KiCad Y-axis increases downward, so 270° points up
        if label.orientation == 0:  # Right
            effects.append([sexpdata.Symbol("justify"), sexpdata.Symbol("left")])
        elif label.orientation == 90:  # Down
            effects.append([sexpdata.Symbol("justify"), sexpdata.Symbol("left")])
        elif label.orientation == 180:  # Left
            effects.append([sexpdata.Symbol("justify"), sexpdata.Symbol("right")])
        elif label.orientation == 270:  # Up
            effects.append([sexpdata.Symbol("justify"), sexpdata.Symbol("right")])

        sexp.append(effects)

        # Add UUID
        sexp.append([sexpdata.Symbol("uuid"), label.uuid])

        return sexp

    def _junction_to_sexp(self, junction: Junction) -> List:
        """Convert a junction to S-expression."""
        sexp = [sexpdata.Symbol("junction")]

        # Add position
        sexp.append([sexpdata.Symbol("at"), junction.position.x, junction.position.y])

        # Add diameter if not default
        if junction.diameter != 0.9144:
            sexp.append([sexpdata.Symbol("diameter"), junction.diameter])

        # Add UUID
        sexp.append([sexpdata.Symbol("uuid"), junction.uuid])

        return sexp

    def _rectangle_to_sexp(self, rect: Rectangle) -> List:
        """Convert Rectangle to S-expression matching KiCad format."""
        sexp = [
            sexpdata.Symbol("rectangle"),
            [sexpdata.Symbol("start"), rect.start.x, rect.start.y],
            [sexpdata.Symbol("end"), rect.end.x, rect.end.y],
            [
                sexpdata.Symbol("stroke"),
                [sexpdata.Symbol("width"), rect.stroke_width],
                [sexpdata.Symbol("type"), sexpdata.Symbol(rect.stroke_type)],
            ],
            [
                sexpdata.Symbol("fill"),
                [sexpdata.Symbol("type"), sexpdata.Symbol(rect.fill_type)],
            ],
            [sexpdata.Symbol("uuid"), rect.uuid],
        ]

        # Add stroke color if specified
        if rect.stroke_color:
            stroke_section = sexp[3]  # stroke section
            stroke_section.append([sexpdata.Symbol("color"), rect.stroke_color])

        return sexp

    def _text_to_sexp(self, text) -> List:
        """Convert Text element to S-expression (either text or text_box)."""
        # Check if this is a TextBox (has special attributes)
        if hasattr(text, "_is_textbox") and text._is_textbox:
            return self._textbox_to_sexp(text)
        else:
            return self._simple_text_to_sexp(text)

    def _textbox_to_sexp(self, text) -> List:
        """Convert TextBox to KiCad text_box S-expression format."""
        # Based on your example format
        sexp = [
            sexpdata.Symbol("text_box"),
            text.content,  # The text content
            [sexpdata.Symbol("exclude_from_sim"), sexpdata.Symbol("yes")],
            [sexpdata.Symbol("at"), text.position.x, text.position.y, text.orientation],
            [sexpdata.Symbol("size"), text._textbox_size[0], text._textbox_size[1]],
            [sexpdata.Symbol("margins")] + list(text._textbox_margins),
        ]

        # Add stroke (border) section
        stroke_section = [sexpdata.Symbol("stroke")]
        if text._textbox_border:
            stroke_section.extend(
                [
                    [sexpdata.Symbol("width"), 0.1],  # Default border width
                    [sexpdata.Symbol("type"), sexpdata.Symbol("solid")],
                ]
            )
        else:
            stroke_section.extend(
                [
                    [sexpdata.Symbol("width"), 0],
                    [sexpdata.Symbol("type"), sexpdata.Symbol("solid")],
                ]
            )
        sexp.append(stroke_section)

        # Add fill (background) section
        fill_section = [sexpdata.Symbol("fill")]
        if text._textbox_background:
            # Convert background color name to RGB
            bg_color = self._color_name_to_rgb(text._textbox_background_color)
            fill_section.extend(
                [
                    [sexpdata.Symbol("type"), sexpdata.Symbol("color")],
                    [sexpdata.Symbol("color")] + bg_color + [1],  # RGB + alpha
                ]
            )
        else:
            fill_section.append([sexpdata.Symbol("type"), sexpdata.Symbol("none")])
        sexp.append(fill_section)

        # Add text effects
        effects_section = [sexpdata.Symbol("effects")]
        font_section = [sexpdata.Symbol("font")]
        font_section.extend(
            [
                [sexpdata.Symbol("size"), text.size, text.size],
                [sexpdata.Symbol("thickness"), 0.254],
            ]
        )

        # Add bold/italic if specified
        if hasattr(text, "_text_bold") and text._text_bold:
            font_section.append([sexpdata.Symbol("bold"), sexpdata.Symbol("yes")])
        if hasattr(text, "_text_color") and text._text_color:
            color_rgb = self._color_name_to_rgb(text._text_color)
            font_section.append([sexpdata.Symbol("color")] + color_rgb + [1])

        effects_section.append(font_section)
        effects_section.append(
            [
                sexpdata.Symbol("justify"),
                sexpdata.Symbol("left"),
                sexpdata.Symbol("top"),
            ]
        )
        sexp.append(effects_section)

        # Add UUID
        sexp.append([sexpdata.Symbol("uuid"), text._textbox_uuid])

        return sexp

    def _simple_text_to_sexp(self, text) -> List:
        """Convert simple Text to KiCad text S-expression format."""
        sexp = [
            sexpdata.Symbol("text"),
            text.content,
            [sexpdata.Symbol("exclude_from_sim"), sexpdata.Symbol("yes")],
            [sexpdata.Symbol("at"), text.position.x, text.position.y, text.orientation],
        ]

        # Add text effects
        effects_section = [sexpdata.Symbol("effects")]
        font_section = [
            sexpdata.Symbol("font"),
            [sexpdata.Symbol("size"), text.size, text.size],
        ]

        # Add bold/italic if specified
        if hasattr(text, "_text_bold") and text._text_bold:
            font_section.append([sexpdata.Symbol("bold"), sexpdata.Symbol("yes")])
        if hasattr(text, "_text_italic") and text._text_italic:
            font_section.append([sexpdata.Symbol("italic"), sexpdata.Symbol("yes")])
        if hasattr(text, "_text_color") and text._text_color:
            color_rgb = self._color_name_to_rgb(text._text_color)
            font_section.append([sexpdata.Symbol("color")] + color_rgb + [1])

        effects_section.append(font_section)
        sexp.append(effects_section)

        # Add UUID
        if hasattr(text, "_text_uuid"):
            sexp.append([sexpdata.Symbol("uuid"), text._text_uuid])
        elif hasattr(text, "uuid"):
            sexp.append([sexpdata.Symbol("uuid"), text.uuid])
        else:
            import uuid as uuid_module

            sexp.append([sexpdata.Symbol("uuid"), str(uuid_module.uuid4())])

        return sexp

    def _color_name_to_rgb(self, color_name: str) -> List[int]:
        """Convert color name to RGB values (0-255)."""
        color_map = {
            "black": [0, 0, 0],
            "white": [255, 255, 255],
            "red": [255, 0, 0],
            "green": [0, 255, 0],
            "blue": [0, 0, 255],
            "yellow": [255, 255, 0],
            "cyan": [0, 255, 255],
            "magenta": [255, 0, 255],
            "lightyellow": [255, 255, 224],
            "lightgray": [211, 211, 211],
            "gray": [128, 128, 128],
            "darkgray": [64, 64, 64],
        }

        if color_name.lower() in color_map:
            return color_map[color_name.lower()]

        # Try to parse hex color
        if color_name.startswith("#"):
            try:
                hex_color = color_name[1:]
                if len(hex_color) == 6:
                    r = int(hex_color[0:2], 16)
                    g = int(hex_color[2:4], 16)
                    b = int(hex_color[4:6], 16)
                    return [r, g, b]
            except ValueError:
                pass

        # Default to black
        return [0, 0, 0]
