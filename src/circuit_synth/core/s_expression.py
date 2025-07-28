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
        pass

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
        # Format with proper indentation
        return self._format_sexp(data)

    def _format_sexp(
        self,
        sexp: Any,
        indent: int = 0,
        parent_tag: str = None,
        in_number: bool = False,
        in_project: bool = False,
        in_instances: bool = False,
        in_page: bool = False,
        in_property_value: bool = False,
        in_property_name: bool = False,
        in_generator: bool = False,
        in_symbol: bool = False,
        in_lib_symbols: bool = False,
        in_name: bool = False,
    ) -> str:
        """Format S-expression with proper indentation.

        Args:
            sexp: The S-expression to format
            indent: Current indentation level
            parent_tag: The parent tag name (used for context-sensitive formatting)
            in_number: True if we're inside a number expression
            in_project: True if we're inside a project expression
            in_instances: True if we're inside an instances expression
            in_page: True if we're inside a page expression
            in_property_value: True if we're formatting a property value (index 2 of property expression)
            in_property_name: True if we're formatting a property name (index 1 of property expression)
            in_generator: True if we're formatting a generator value
            in_symbol: True if we're formatting a symbol library ID
            in_lib_symbols: True if we're inside a lib_symbols section
        """
        if not isinstance(sexp, list):
            # Handle symbols and values
            if isinstance(sexp, sexpdata.Symbol):
                return str(sexp)
            elif isinstance(sexp, str):
                # Empty strings must be quoted
                if sexp == "":
                    return '""'
                # Property names must always be quoted
                if in_property_name:
                    return '"' + sexp + '"'
                # Pin numbers must always be quoted (when directly after "number" tag)
                if in_number and sexp.isdigit():
                    return '"' + sexp + '"'
                # Pin names must be quoted if they are numeric (when directly after "name" tag)
                if in_name and sexp.isdigit():
                    return '"' + sexp + '"'
                # Project names must always be quoted
                if in_project:
                    return '"' + sexp + '"'
                # Page values must always be quoted
                if in_page:
                    return '"' + sexp + '"'
                # Property values must always be quoted
                if in_property_value:
                    return '"' + sexp + '"'
                # Generator values must always be quoted
                if in_generator:
                    return '"' + sexp + '"'
                # Symbol library IDs must always be quoted
                if in_symbol:
                    return '"' + sexp + '"'
                # Quote strings if they contain spaces or special characters
                if " " in sexp or "\n" in sexp or '"' in sexp or "/" in sexp:
                    return '"' + sexp.replace('"', '\\"') + '"'
                # Library IDs with colons (like "Device:R") should be quoted when in symbol context
                if ":" in sexp and not " " in sexp:
                    return sexp
                # Don't quote simple identifiers (property names, etc.)
                return sexp
            elif isinstance(sexp, (int, float)):
                # Pin numbers must always be quoted (when directly after "number" tag)
                if in_number:
                    return '"' + str(sexp) + '"'
                # Pin names must be quoted if they are numeric (when directly after "name" tag)
                if in_name:
                    return '"' + str(sexp) + '"'
                # Page values must always be quoted
                if in_page:
                    return '"' + str(sexp) + '"'
                # Property values must always be quoted
                if in_property_value:
                    return '"' + str(sexp) + '"'
                # Property names must always be quoted
                if in_property_name:
                    return '"' + str(sexp) + '"'
                return str(sexp)
            else:
                return str(sexp)

        if not sexp:
            return "()"

        # Get the tag name for context
        tag_name = None
        if sexp and isinstance(sexp[0], sexpdata.Symbol):
            tag_name = str(sexp[0])

        # Check if this is a simple list that should be on one line
        # Special case: symbol expressions in lib_symbols should format their ID on same line
        is_symbol_expr = tag_name == "symbol"
        is_symbol_in_lib_symbols = is_symbol_expr and in_lib_symbols and len(sexp) >= 2
        is_simple = (
            len(sexp) <= 4
            and all(not isinstance(item, list) for item in sexp)
            and sum(len(str(item)) for item in sexp) < 60
        ) or (
            is_symbol_in_lib_symbols and len(sexp) == 2
        )  # Just symbol tag and ID

        # Check if this is a number expression
        is_number_expr = tag_name == "number"
        # Check if this is a name expression
        is_name_expr = tag_name == "name"
        # Check if this is a project expression
        is_project_expr = tag_name == "project"
        # Check if this is an instances expression
        is_instances_expr = tag_name == "instances"
        # Check if this is a page expression
        is_page_expr = tag_name == "page"
        # Check if this is a property expression
        is_property_expr = tag_name == "property"
        # Check if this is a generator expression
        is_generator_expr = tag_name == "generator"
        # Check if this is a lib_symbols expression
        is_lib_symbols_expr = tag_name == "lib_symbols"

        if is_simple:
            # Format on one line
            parts = []
            for i, item in enumerate(sexp):
                # For number expressions, pass in_number=True for the value at index 1
                if is_number_expr and i == 1:
                    parts.append(
                        self._format_sexp(item, indent, tag_name, in_number=True)
                    )
                # For name expressions, pass in_name=True for the value at index 1
                elif is_name_expr and i == 1:
                    parts.append(
                        self._format_sexp(item, indent, tag_name, in_name=True)
                    )
                # For project expressions, pass in_project=True for the value at index 1
                elif is_project_expr and i == 1:
                    parts.append(
                        self._format_sexp(
                            item,
                            indent,
                            tag_name,
                            in_project=True,
                            in_instances=in_instances,
                        )
                    )
                elif is_instances_expr:
                    # Inside instances, pass the flag down
                    parts.append(
                        self._format_sexp(item, indent, tag_name, in_instances=True)
                    )
                elif is_lib_symbols_expr:
                    # Inside lib_symbols, pass the flag down
                    parts.append(
                        self._format_sexp(
                            item,
                            indent,
                            tag_name,
                            in_lib_symbols=True,
                            in_instances=in_instances,
                        )
                    )
                elif is_page_expr and i == 1:
                    # For page expressions, pass in_page=True for the value at index 1
                    parts.append(
                        self._format_sexp(
                            item,
                            indent,
                            tag_name,
                            in_page=True,
                            in_instances=in_instances,
                        )
                    )
                elif is_property_expr and i == 1:
                    # For property expressions, pass in_property_name=True for the name at index 1
                    parts.append(
                        self._format_sexp(
                            item,
                            indent,
                            tag_name,
                            in_property_name=True,
                            in_instances=in_instances,
                        )
                    )
                elif is_property_expr and i == 2:
                    # For property expressions, pass in_property_value=True for the value at index 2
                    parts.append(
                        self._format_sexp(
                            item,
                            indent,
                            tag_name,
                            in_property_value=True,
                            in_instances=in_instances,
                        )
                    )
                elif is_symbol_expr and i == 1:
                    # For symbol expressions, the library ID at index 1 should be quoted
                    parts.append(
                        self._format_sexp(
                            item,
                            indent,
                            tag_name,
                            in_symbol=True,
                            in_instances=in_instances,
                        )
                    )
                elif is_generator_expr and i == 1:
                    # For generator expressions, the value at index 1 should be quoted
                    parts.append(
                        self._format_sexp(
                            item,
                            indent,
                            tag_name,
                            in_generator=True,
                            in_instances=in_instances,
                        )
                    )
                else:
                    parts.append(
                        self._format_sexp(
                            item, indent, tag_name, in_instances=in_instances
                        )
                    )
            return "(" + " ".join(parts) + ")"
        else:
            # Special handling for symbol expressions in lib_symbols
            if is_symbol_expr and in_lib_symbols and len(sexp) >= 2:
                # Format symbol tag and library ID on same line
                result = "(" + str(sexp[0])  # symbol tag
                # Library ID should be quoted
                result += ' "' + str(sexp[1]) + '"'
                # Rest of content on new lines
                for i in range(2, len(sexp)):
                    result += (
                        "\n"
                        + "\t" * (indent + 1)
                        + self._format_sexp(
                            sexp[i],
                            indent + 1,
                            tag_name,
                            in_lib_symbols=in_lib_symbols,
                            in_instances=in_instances,
                        )
                    )
                result += "\n" + "\t" * indent + ")"
                return result

            # Format with indentation
            result = "("
            for i, item in enumerate(sexp):
                if i == 0:
                    # First item (usually the tag) stays on the same line
                    result += self._format_sexp(
                        item,
                        indent,
                        tag_name,
                        in_number=False,
                        in_instances=in_instances,
                        in_lib_symbols=in_lib_symbols,
                    )
                else:
                    # Other items on new lines with indentation
                    # For number expressions, pass in_number=True for the value at index 1
                    if is_number_expr and i == 1:
                        result += (
                            "\n"
                            + "\t" * (indent + 1)
                            + self._format_sexp(
                                item,
                                indent + 1,
                                tag_name,
                                in_number=True,
                                in_instances=in_instances,
                            )
                        )
                    # For name expressions, pass in_name=True for the value at index 1
                    elif is_name_expr and i == 1:
                        result += (
                            "\n"
                            + "\t" * (indent + 1)
                            + self._format_sexp(
                                item,
                                indent + 1,
                                tag_name,
                                in_name=True,
                                in_instances=in_instances,
                            )
                        )
                    elif is_project_expr and i == 1:
                        # For project expressions, pass in_project=True for the value at index 1
                        result += (
                            "\n"
                            + "\t" * (indent + 1)
                            + self._format_sexp(
                                item,
                                indent + 1,
                                tag_name,
                                in_project=True,
                                in_instances=in_instances,
                            )
                        )
                    elif is_instances_expr:
                        # Inside instances, pass the flag down
                        result += (
                            "\n"
                            + "\t" * (indent + 1)
                            + self._format_sexp(
                                item, indent + 1, tag_name, in_instances=True
                            )
                        )
                    elif is_lib_symbols_expr:
                        # Inside lib_symbols, pass the flag down
                        result += (
                            "\n"
                            + "\t" * (indent + 1)
                            + self._format_sexp(
                                item,
                                indent + 1,
                                tag_name,
                                in_lib_symbols=True,
                                in_instances=in_instances,
                            )
                        )
                    elif is_page_expr and i == 1:
                        # For page expressions, pass in_page=True for the value at index 1
                        result += (
                            "\n"
                            + "\t" * (indent + 1)
                            + self._format_sexp(
                                item,
                                indent + 1,
                                tag_name,
                                in_page=True,
                                in_instances=in_instances,
                            )
                        )
                    elif is_property_expr and i == 1:
                        # For property expressions, pass in_property_name=True for the name at index 1
                        result += (
                            "\n"
                            + "\t" * (indent + 1)
                            + self._format_sexp(
                                item,
                                indent + 1,
                                tag_name,
                                in_property_name=True,
                                in_instances=in_instances,
                            )
                        )
                    elif is_property_expr and i == 2:
                        # For property expressions, pass in_property_value=True for the value at index 2
                        result += (
                            "\n"
                            + "\t" * (indent + 1)
                            + self._format_sexp(
                                item,
                                indent + 1,
                                tag_name,
                                in_property_value=True,
                                in_instances=in_instances,
                            )
                        )
                    elif is_symbol_expr and i == 1:
                        # For symbol expressions, the library ID at index 1 should be quoted
                        result += (
                            "\n"
                            + "\t" * (indent + 1)
                            + self._format_sexp(
                                item,
                                indent + 1,
                                tag_name,
                                in_symbol=True,
                                in_instances=in_instances,
                            )
                        )
                    elif is_generator_expr and i == 1:
                        # For generator expressions, the value at index 1 should be quoted
                        result += (
                            "\n"
                            + "\t" * (indent + 1)
                            + self._format_sexp(
                                item,
                                indent + 1,
                                tag_name,
                                in_generator=True,
                                in_instances=in_instances,
                            )
                        )
                    else:
                        result += (
                            "\n"
                            + "\t" * (indent + 1)
                            + self._format_sexp(
                                item,
                                indent + 1,
                                tag_name,
                                in_number=False,
                                in_instances=in_instances,
                            )
                        )
            result += "\n" + "\t" * indent + ")"
            return result

    def to_schematic(self, sexp_data: Any) -> Schematic:
        """
        Convert parsed S-expression data to Schematic object.

        Args:
            sexp_data: Parsed S-expression data

        Returns:
            Schematic object
        """
        schematic = Schematic()

        # Parse the top-level kicad_sch expression
        if (
            not self._is_sexp_list(sexp_data)
            or not self._get_symbol_name(sexp_data[0]) == "kicad_sch"
        ):
            raise ValueError("Invalid KiCad schematic format")

        # Process each element in the schematic
        for element in sexp_data[1:]:
            if not self._is_sexp_list(element):
                continue

            element_type = self._get_symbol_name(element[0])

            if element_type == "version":
                schematic.version = element[1]
            elif element_type == "generator":
                schematic.generator = element[1]
            elif element_type == "uuid":
                schematic.uuid = element[1]
            elif element_type == "title_block":
                self._parse_title_block(element, schematic)
            elif element_type == "symbol":
                symbol = self._parse_symbol(element)
                if symbol:
                    schematic.add_component(symbol)
            elif element_type == "wire":
                wire = self._parse_wire(element)
                if wire:
                    schematic.add_wire(wire)
            elif element_type == "label":
                label = self._parse_label(element, LabelType.LOCAL)
                if label:
                    schematic.add_label(label)
            elif element_type == "global_label":
                label = self._parse_label(element, LabelType.GLOBAL)
                if label:
                    schematic.add_label(label)
            elif element_type == "hierarchical_label":
                label = self._parse_label(element, LabelType.HIERARCHICAL)
                if label:
                    schematic.add_label(label)
            elif element_type == "junction":
                junction = self._parse_junction(element)
                if junction:
                    schematic.add_junction(junction)
            elif element_type == "sheet":
                sheet = self._parse_sheet(element)
                if sheet:
                    schematic.sheets.append(sheet)

        return schematic

    def from_schematic(self, schematic: Schematic) -> List:
        """
        Convert Schematic object to S-expression data.
        """
        sexp = [sexpdata.Symbol("kicad_sch")]

        # Add metadata
        try:
            version_num = int(schematic.version)
        except ValueError:
            version_num = 20250114
        sexp.append([sexpdata.Symbol("version"), version_num])
        sexp.append([sexpdata.Symbol("generator"), schematic.generator])
        sexp.append([sexpdata.Symbol("generator_version"), "9.0"])
        sexp.append([sexpdata.Symbol("uuid"), schematic.uuid])

        # Add paper size only once
        sexp.append([sexpdata.Symbol("paper"), "A4"])

        # Add lib_symbols section
        lib_symbols = self._generate_lib_symbols(schematic)
        if lib_symbols:
            sexp.append(lib_symbols)

        # Add title block
        if schematic.title or schematic.date or schematic.revision:
            title_block = [sexpdata.Symbol("title_block")]
            if schematic.title:
                title_block.append([sexpdata.Symbol("title"), schematic.title])
            if schematic.date:
                title_block.append([sexpdata.Symbol("date"), schematic.date])
            if schematic.revision:
                title_block.append([sexpdata.Symbol("rev"), schematic.revision])
            if schematic.company:
                title_block.append([sexpdata.Symbol("company"), schematic.company])
            if schematic.comment:
                title_block.append([sexpdata.Symbol("comment"), 1, schematic.comment])
            sexp.append(title_block)

        # Add components
        for component in schematic.components:
            sexp.append(self._symbol_to_sexp(component))

        # Add wires, labels, junctions, sheets...
        for wire in schematic.wires:
            sexp.append(self._wire_to_sexp(wire))
        for label in schematic.labels:
            sexp.append(self._label_to_sexp(label))
        for junction in schematic.junctions:
            sexp.append(self._junction_to_sexp(junction))
        for sheet in schematic.sheets:
            sexp.append(self._sheet_to_sexp(sheet))

        # Add rectangles
        for rectangle in schematic.rectangles:
            sexp.append(self._rectangle_to_sexp(rectangle))

        # Add sheet_instances only once

        # Determine the path to write
        if hasattr(schematic, "hierarchical_path") and schematic.hierarchical_path:
            path_str = "/" + "/".join(schematic.hierarchical_path)
        else:
            path_str = "/"

        sheet_instances = [
            sexpdata.Symbol("sheet_instances"),
            [sexpdata.Symbol("path"), path_str, [sexpdata.Symbol("page"), "1"]],
        ]
        sexp.append(sheet_instances)

        # For new KiCad format (20250114+), do NOT add symbol_instances table
        # Each symbol has its own instances block instead

        # Add embedded_fonts flag
        sexp.append([sexpdata.Symbol("embedded_fonts"), sexpdata.Symbol("no")])

        return sexp

    def _is_sexp_list(self, obj: Any) -> bool:
        """Check if object is a list (S-expression)."""
        return isinstance(obj, list)

    def _get_symbol_name(self, obj: Any) -> Optional[str]:
        """Get the name of a symbol if it is one."""
        if isinstance(obj, sexpdata.Symbol):
            return str(obj)
        return None

    def _find_element(self, sexp: List, name: str) -> Optional[Any]:
        """Find an element by name in an S-expression."""
        for item in sexp:
            if self._is_sexp_list(item) and self._get_symbol_name(item[0]) == name:
                return item
        return None

    def _find_all_elements(self, sexp: List, name: str) -> List[Any]:
        """Find all elements by name in an S-expression."""
        results = []
        for item in sexp:
            if self._is_sexp_list(item) and self._get_symbol_name(item[0]) == name:
                results.append(item)
        return results

    def _get_value(self, sexp: List, name: str, default: Any = None) -> Any:
        """Get the value of a named element."""
        element = self._find_element(sexp, name)
        if element and len(element) > 1:
            return element[1]
        return default

    def _parse_title_block(self, sexp: List, schematic: Schematic):
        """Parse title block information."""
        schematic.title = self._get_value(sexp, "title", "")
        schematic.date = self._get_value(sexp, "date", "")
        schematic.revision = self._get_value(sexp, "rev", "")
        schematic.company = self._get_value(sexp, "company", "")

        # Parse comments
        comment_elem = self._find_element(sexp, "comment")
        if comment_elem and len(comment_elem) > 2:
            schematic.comment = comment_elem[2]

    def _parse_symbol(self, sexp: List) -> Optional[SchematicSymbol]:
        """Parse a symbol (component) from S-expression."""
        try:
            # Get lib_id
            lib_id = self._get_value(sexp, "lib_id")
            if not lib_id:
                return None

            # Get position
            at_elem = self._find_element(sexp, "at")
            if not at_elem or len(at_elem) < 3:
                return None

            position = Point(float(at_elem[1]), float(at_elem[2]))
            rotation = float(at_elem[3]) if len(at_elem) > 3 else 0.0

            # Get UUID
            uuid = self._get_value(sexp, "uuid", "")

            # Create symbol
            symbol = SchematicSymbol(
                reference="",  # Will be filled from properties
                value="",  # Will be filled from properties
                lib_id=lib_id,
                position=position,
                rotation=rotation,
                uuid=uuid,
            )

            # Parse properties
            for prop_elem in self._find_all_elements(sexp, "property"):
                if len(prop_elem) >= 3:
                    prop_name = prop_elem[1]
                    prop_value = prop_elem[2]

                    if prop_name == "Reference":
                        symbol.reference = prop_value
                    elif prop_name == "Value":
                        symbol.value = prop_value
                    elif prop_name == "Footprint":
                        symbol.footprint = prop_value
                    else:
                        symbol.properties[prop_name] = prop_value

            # Parse other attributes
            symbol.unit = self._get_value(sexp, "unit", 1)
            symbol.in_bom = self._get_value(sexp, "in_bom", "yes") == "yes"
            symbol.on_board = self._get_value(sexp, "on_board", "yes") == "yes"
            symbol.dnp = self._get_value(sexp, "dnp", "no") == "yes"

            mirror_elem = self._find_element(sexp, "mirror")
            if mirror_elem and len(mirror_elem) > 1:
                symbol.mirror = mirror_elem[1]

            return symbol

        except Exception as e:
            logger.error(f"Error parsing symbol: {e}")
            return None

    def _parse_wire(self, sexp: List) -> Optional[Wire]:
        """Parse a wire from S-expression."""
        try:
            pts_elem = self._find_element(sexp, "pts")
            if not pts_elem:
                return None

            points = []
            for pt in pts_elem[1:]:
                if self._get_symbol_name(pt[0]) == "xy" and len(pt) >= 3:
                    points.append(Point(float(pt[1]), float(pt[2])))

            if len(points) < 2:
                return None

            wire = Wire(points=points)
            wire.uuid = self._get_value(sexp, "uuid", "")

            # Parse stroke
            stroke_elem = self._find_element(sexp, "stroke")
            if stroke_elem:
                wire.stroke_width = self._get_value(stroke_elem, "width", 0.0)
                wire.stroke_type = self._get_value(stroke_elem, "type", "default")

            return wire

        except Exception as e:
            logger.error(f"Error parsing wire: {e}")
            return None

    def _parse_label(self, sexp: List, label_type: LabelType) -> Optional[Label]:
        """Parse a label from S-expression."""
        try:
            text = sexp[1] if len(sexp) > 1 else ""

            at_elem = self._find_element(sexp, "at")
            if not at_elem or len(at_elem) < 3:
                return None

            position = Point(float(at_elem[1]), float(at_elem[2]))
            orientation = int(at_elem[3]) if len(at_elem) > 3 else 0

            label = Label(
                text=text,
                position=position,
                label_type=label_type,
                orientation=orientation,
            )

            label.uuid = self._get_value(sexp, "uuid", "")

            # Parse effects
            effects_elem = self._find_element(sexp, "effects")
            if effects_elem:
                label.effects = {}  # Would need more parsing for full effects

            return label

        except Exception as e:
            logger.error(f"Error parsing label: {e}")
            return None

    def _parse_junction(self, sexp: List) -> Optional[Junction]:
        """Parse a junction from S-expression."""
        try:
            at_elem = self._find_element(sexp, "at")
            if not at_elem or len(at_elem) < 3:
                return None

            position = Point(float(at_elem[1]), float(at_elem[2]))

            junction = Junction(position=position)
            junction.uuid = self._get_value(sexp, "uuid", "")
            junction.diameter = self._get_value(sexp, "diameter", 0.9144)

            return junction

        except Exception as e:
            logger.error(f"Error parsing junction: {e}")
            return None

    def _parse_sheet(self, sexp: List) -> Optional[Sheet]:
        """Parse a sheet from S-expression."""
        try:
            # Initialize with default values
            name = ""
            filename = ""
            position = Point(0, 0)
            size = (100, 80)  # Default size
            pins = []
            uuid_val = ""

            # Parse position and size
            at_elem = self._find_element(sexp, "at")
            if at_elem and len(at_elem) >= 3:
                position = Point(float(at_elem[1]), float(at_elem[2]))

            size_elem = self._find_element(sexp, "size")
            if size_elem and len(size_elem) >= 3:
                size = (float(size_elem[1]), float(size_elem[2]))

            # Parse UUID
            uuid_val = self._get_value(sexp, "uuid", "")

            # Parse properties
            for elem in sexp:
                if (
                    self._is_sexp_list(elem)
                    and self._get_symbol_name(elem[0]) == "property"
                ):
                    prop_name = elem[1] if len(elem) > 1 else ""
                    prop_value = elem[2] if len(elem) > 2 else ""

                    if prop_name == "Sheetname":
                        name = prop_value
                    elif prop_name == "Sheetfile":
                        filename = prop_value

            # Parse sheet pins
            for elem in sexp:
                if self._is_sexp_list(elem) and self._get_symbol_name(elem[0]) == "pin":
                    pin = self._parse_sheet_pin(elem)
                    if pin:
                        pins.append(pin)

            # Create sheet with all required arguments
            sheet = Sheet(
                name=name, filename=filename, position=position, size=size, pins=pins
            )
            if uuid_val:
                sheet.uuid = uuid_val

            return sheet

        except Exception as e:
            logger.error(f"Error parsing sheet: {e}")
            return None

    def _parse_sheet_pin(self, sexp: List) -> Optional[SheetPin]:
        """Parse a sheet pin from S-expression."""
        try:
            # Initialize with default values
            name = ""
            position = Point(0, 0)
            orientation = 0
            shape = "input"
            uuid_val = ""

            # Parse name (first element after 'pin')
            if len(sexp) > 1:
                name = sexp[1]

            # Parse shape/type
            shape = self._get_value(sexp, "type", "input")

            # Parse position and orientation
            at_elem = self._find_element(sexp, "at")
            if at_elem and len(at_elem) >= 3:
                position = Point(float(at_elem[1]), float(at_elem[2]))
                # Parse rotation if present
                if len(at_elem) >= 4:
                    orientation = int(float(at_elem[3]))

            # Parse UUID
            uuid_val = self._get_value(sexp, "uuid", "")

            # Create sheet pin with all required arguments
            pin = SheetPin(
                name=name, position=position, orientation=orientation, shape=shape
            )
            if uuid_val:
                pin.uuid = uuid_val

            return pin

        except Exception as e:
            logger.error(f"Error parsing sheet pin: {e}")
            return None

    # Helper methods for writing

    def _symbol_to_sexp(self, symbol: SchematicSymbol) -> List:
        """Convert a symbol to S-expression."""
        sexp = [sexpdata.Symbol("symbol")]

        # Add lib_id
        sexp.append([sexpdata.Symbol("lib_id"), symbol.lib_id])

        # Add position - always include rotation for KiCad compatibility
        at_expr = [
            sexpdata.Symbol("at"),
            symbol.position.x,
            symbol.position.y,
            int(symbol.rotation),
        ]
        sexp.append(at_expr)

        # Add unit
        if symbol.unit != 1:
            sexp.append([sexpdata.Symbol("unit"), symbol.unit])

        # Add flags - use symbols not strings for KiCad compatibility
        sexp.append(
            [
                sexpdata.Symbol("in_bom"),
                sexpdata.Symbol("yes") if symbol.in_bom else sexpdata.Symbol("no"),
            ]
        )
        sexp.append(
            [
                sexpdata.Symbol("on_board"),
                sexpdata.Symbol("yes") if symbol.on_board else sexpdata.Symbol("no"),
            ]
        )
        sexp.append(
            [
                sexpdata.Symbol("dnp"),
                sexpdata.Symbol("yes") if symbol.dnp else sexpdata.Symbol("no"),
            ]
        )

        # Add UUID
        sexp.append([sexpdata.Symbol("uuid"), symbol.uuid])

        # Add properties with proper formatting
        if symbol.reference:
            prop = [sexpdata.Symbol("property"), "Reference", symbol.reference]
            # Position relative to symbol
            prop.append(
                [sexpdata.Symbol("at"), symbol.position.x, symbol.position.y - 5, 0]
            )
            prop.append(
                [
                    sexpdata.Symbol("effects"),
                    [sexpdata.Symbol("font"), [sexpdata.Symbol("size"), 1.27, 1.27]],
                ]
            )
            sexp.append(prop)

        if symbol.value:
            prop = [sexpdata.Symbol("property"), "Value", str(symbol.value)]
            # Position relative to symbol
            prop.append(
                [sexpdata.Symbol("at"), symbol.position.x, symbol.position.y + 5, 0]
            )
            prop.append(
                [
                    sexpdata.Symbol("effects"),
                    [sexpdata.Symbol("font"), [sexpdata.Symbol("size"), 1.27, 1.27]],
                ]
            )
            sexp.append(prop)

        if symbol.footprint:
            # IMPORTANT: Use "Footprint" with capital F, not "footprint"
            prop = [sexpdata.Symbol("property"), "Footprint", symbol.footprint]
            # Position relative to symbol
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
            sexp.append(prop)

        # Add custom properties, but skip internal ones and standard KiCad properties
        internal_properties = {
            "hierarchy_path",
            "ki_keywords",
            "ki_description",
            "Reference",
            "Value",
            "Footprint",
            "Datasheet",
            "Description",
            "project_name",
            "hierarchical_path",
        }
        for name, value in symbol.properties.items():
            if name not in internal_properties:
                prop = [sexpdata.Symbol("property"), name, str(value)]
                # Position relative to symbol
                prop.append(
                    [
                        sexpdata.Symbol("at"),
                        symbol.position.x,
                        symbol.position.y + 15,
                        0,
                    ]
                )
                prop.append(
                    [
                        sexpdata.Symbol("effects"),
                        [
                            sexpdata.Symbol("font"),
                            [sexpdata.Symbol("size"), 1.27, 1.27],
                        ],
                        [sexpdata.Symbol("hide"), sexpdata.Symbol("yes")],
                    ]
                )
                sexp.append(prop)

        # Add mirror if present
        if symbol.mirror:
            sexp.append([sexpdata.Symbol("mirror"), symbol.mirror])

        # Add instances section for new KiCad format (version 20250114+)
        # This replaces the old symbol_instances table
        logger.debug(f"=== PROCESSING INSTANCES FOR SYMBOL {symbol.reference} ===")
        logger.debug(f"  Symbol UUID: {symbol.uuid}")
        logger.debug(f"  Has instances attribute: {hasattr(symbol, 'instances')}")
        if hasattr(symbol, "instances"):
            logger.debug(
                f"  Number of instances: {len(symbol.instances) if symbol.instances else 0}"
            )
            logger.debug(f"  Instances: {symbol.instances}")

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

            logger.debug(f"  Grouped into {len(project_instances)} project(s)")

            # Create project blocks
            for project_name, project_inst_list in project_instances.items():
                logger.debug(f"  Processing project: {project_name}")
                for inst in project_inst_list:
                    logger.debug(f"    Creating instance block:")
                    logger.debug(f"      Path: '{inst.path}'")
                    logger.debug(f"      Reference: '{inst.reference}'")
                    logger.debug(f"      Unit: {inst.unit}")

                    project_block = [
                        sexpdata.Symbol("project"),
                        project_name,
                        [
                            sexpdata.Symbol("path"),
                            inst.path,  # Path will be quoted by formatter
                            [sexpdata.Symbol("reference"), inst.reference],
                            [sexpdata.Symbol("unit"), inst.unit],
                        ],
                    ]
                    instances_sexp.append(project_block)
                    logger.debug(f"    Instance block created")

            sexp.append(instances_sexp)
            logger.debug(f"  Instances S-expression added to symbol")
        else:
            logger.error(f"Symbol {symbol.reference} has NO instances information!")
            logger.error(
                f"  Symbol must have 'instances' field populated (internal library requirement)"
            )
            logger.error(
                f"  This is handled automatically by the Circuit Synth library"
            )
            raise ValueError(
                f"Symbol {symbol.reference} missing required instances data"
            )

        return sexp

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
        instances = [sexpdata.Symbol("instances")]
        project_instance = [
            sexpdata.Symbol("project"),
            "circuit_synth",
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
        sexp.append(
            [
                sexpdata.Symbol("pin_numbers"),
                [sexpdata.Symbol("hide"), sexpdata.Symbol("no")],
            ]
        )
        sexp.append([sexpdata.Symbol("pin_names"), [sexpdata.Symbol("offset"), 0.254]])
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
            for element in symbol_def.graphic_elements:
                graphics_symbol.append(self._graphic_element_to_sexp(element))
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
