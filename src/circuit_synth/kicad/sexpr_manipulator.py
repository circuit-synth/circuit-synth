"""
S-Expression Manipulation Layer - Pure data structure operations.

This module provides clean S-expression manipulation without any file I/O or
KiCad-specific business logic. It focuses on parsing, modifying, and serializing
S-expression data structures.
"""

import logging
import uuid
from typing import Any, Dict, List, Optional, Tuple, Union

import sexpdata

logger = logging.getLogger(__name__)


class SExpressionManipulator:
    """
    Pure S-expression data manipulation.

    This class handles S-expression parsing and modification without any knowledge
    of files or KiCad-specific business logic. It provides clean data structure
    operations that can be used by higher layers.
    """

    def __init__(self, data: Optional[Union[str, List]] = None):
        """
        Initialize S-expression manipulator.

        Args:
            data: Initial S-expression data (string or parsed structure)
        """
        if isinstance(data, str):
            self._data = self.parse_string(data)
        elif isinstance(data, list):
            self._data = data
        else:
            self._data = []

    @classmethod
    def parse_string(cls, content: str) -> List:
        """
        Parse S-expression string to data structure.

        Args:
            content: S-expression string content

        Returns:
            Parsed S-expression data structure

        Raises:
            ValueError: If content cannot be parsed
        """
        try:
            return sexpdata.loads(content)
        except Exception as e:
            logger.error(f"Failed to parse S-expression: {e}")
            raise ValueError(f"Invalid S-expression content: {e}") from e

    def to_string(self, pretty: bool = True) -> str:
        """
        Convert S-expression data structure to string.

        Args:
            pretty: If True, format with proper indentation

        Returns:
            S-expression string
        """
        if pretty:
            return self._format_pretty(self._data)
        else:
            return sexpdata.dumps(self._data)

    def find_section(self, section_name: str) -> Optional[List]:
        """
        Find a top-level section by name.

        Args:
            section_name: Name of section to find (e.g., "lib_symbols")

        Returns:
            Section list if found, None otherwise
        """
        if not isinstance(self._data, list):
            return None

        for item in self._data:
            if (
                isinstance(item, list)
                and len(item) > 0
                and isinstance(item[0], sexpdata.Symbol)
                and str(item[0]) == section_name
            ):
                return item

        return None

    def add_section(self, section_name: str, content: List = None) -> List:
        """
        Add or update a top-level section.

        Args:
            section_name: Name of section to add
            content: Content for the section (default: empty list)

        Returns:
            The added/updated section
        """
        if content is None:
            content = []

        # Remove existing section if it exists
        self.remove_section(section_name)

        # Create new section
        section = [sexpdata.Symbol(section_name)] + content

        # Add to data structure
        if not isinstance(self._data, list):
            self._data = []
        self._data.append(section)

        logger.debug(f"Added section: {section_name}")
        return section

    def remove_section(self, section_name: str) -> bool:
        """
        Remove a top-level section.

        Args:
            section_name: Name of section to remove

        Returns:
            True if section was removed, False if not found
        """
        if not isinstance(self._data, list):
            return False

        for i, item in enumerate(self._data):
            if (
                isinstance(item, list)
                and len(item) > 0
                and isinstance(item[0], sexpdata.Symbol)
                and str(item[0]) == section_name
            ):
                del self._data[i]
                logger.debug(f"Removed section: {section_name}")
                return True

        return False

    def find_symbol(self, reference: str) -> Optional[List]:
        """
        Find a symbol by reference in the S-expression data.

        Args:
            reference: Component reference (e.g., "R1")

        Returns:
            Symbol list if found, None otherwise
        """
        if not isinstance(self._data, list):
            return None

        for item in self._data:
            if self._is_symbol_with_reference(item, reference):
                return item

        return None

    def add_symbol(self, symbol_data: Dict) -> List:
        """
        Add a symbol to the S-expression data.

        Args:
            symbol_data: Symbol data dictionary with keys like:
                - lib_id: Library identifier
                - reference: Component reference
                - value: Component value
                - position: (x, y) position
                - uuid: Component UUID
                - etc.

        Returns:
            The added symbol S-expression
        """
        symbol_sexp = self._create_symbol_sexp(symbol_data)

        if not isinstance(self._data, list):
            self._data = []

        # Insert symbol before sheet_instances if it exists
        insert_index = len(self._data)
        for i, item in enumerate(self._data):
            if (
                isinstance(item, list)
                and len(item) > 0
                and isinstance(item[0], sexpdata.Symbol)
                and str(item[0]) == "sheet_instances"
            ):
                insert_index = i
                break

        self._data.insert(insert_index, symbol_sexp)
        logger.debug(f"Added symbol: {symbol_data.get('reference')}")
        return symbol_sexp

    def remove_symbol(self, reference: str) -> bool:
        """
        Remove a symbol by reference.

        Args:
            reference: Component reference to remove

        Returns:
            True if symbol was removed, False if not found
        """
        if not isinstance(self._data, list):
            return False

        for i, item in enumerate(self._data):
            if self._is_symbol_with_reference(item, reference):
                del self._data[i]
                logger.debug(f"Removed symbol: {reference}")
                return True

        return False

    def create_blank_schematic(self) -> None:
        """
        Create a blank KiCad schematic structure.

        This creates the minimal structure needed for a valid KiCad schematic file.
        """
        self._data = [
            sexpdata.Symbol("kicad_sch"),
            [sexpdata.Symbol("version"), 20250114],
            [sexpdata.Symbol("generator"), "circuit_synth"],
            [sexpdata.Symbol("generator_version"), "9.0"],
            [sexpdata.Symbol("paper"), "A4"],
            [sexpdata.Symbol("lib_symbols")],
            [sexpdata.Symbol("symbol_instances")],
        ]
        logger.debug("Created blank schematic structure")

    def _is_symbol_with_reference(self, item: Any, reference: str) -> bool:
        """Check if an S-expression item is a symbol with the given reference."""
        if not (isinstance(item, list) and len(item) > 0):
            return False

        # Check if this is a symbol
        if not (isinstance(item[0], sexpdata.Symbol) and str(item[0]) == "symbol"):
            return False

        # Look for property with Reference
        for subitem in item[1:]:
            if (
                isinstance(subitem, list)
                and len(subitem) >= 3
                and isinstance(subitem[0], sexpdata.Symbol)
                and str(subitem[0]) == "property"
                and len(subitem) >= 3
                and str(subitem[1]) == "Reference"
                and str(subitem[2]) == reference
            ):
                return True

        return False

    def _create_symbol_sexp(self, symbol_data: Dict) -> List:
        """Create S-expression for a symbol from data dictionary."""
        # Generate UUID if not provided
        symbol_uuid = symbol_data.get("uuid", str(uuid.uuid4()))

        # Extract position
        position = symbol_data.get("position", (100, 100))
        rotation = symbol_data.get("rotation", 0)

        # Create basic symbol structure
        symbol_sexp = [
            sexpdata.Symbol("symbol"),
            [sexpdata.Symbol("lib_id"), symbol_data["lib_id"]],
            [sexpdata.Symbol("at"), position[0], position[1], rotation],
            [sexpdata.Symbol("unit"), symbol_data.get("unit", 1)],
            [sexpdata.Symbol("exclude_from_sim"), sexpdata.Symbol("no")],
            [sexpdata.Symbol("in_bom"), sexpdata.Symbol("yes")],
            [sexpdata.Symbol("on_board"), sexpdata.Symbol("yes")],
            [sexpdata.Symbol("dnp"), sexpdata.Symbol("no")],
            [sexpdata.Symbol("fields_autoplaced"), sexpdata.Symbol("yes")],
            [sexpdata.Symbol("uuid"), symbol_uuid],
        ]

        # Add Reference property
        if "reference" in symbol_data:
            ref_prop = [
                sexpdata.Symbol("property"),
                "Reference",
                symbol_data["reference"],
                [sexpdata.Symbol("at"), position[0], position[1] - 5, 0],
                [
                    sexpdata.Symbol("effects"),
                    [sexpdata.Symbol("font"), [sexpdata.Symbol("size"), 1.27, 1.27]],
                    [sexpdata.Symbol("justify"), sexpdata.Symbol("left")],
                ],
            ]
            symbol_sexp.append(ref_prop)

        # Add Value property
        if "value" in symbol_data:
            val_prop = [
                sexpdata.Symbol("property"),
                "Value",
                str(symbol_data["value"]),
                [sexpdata.Symbol("at"), position[0], position[1] + 5, 0],
                [
                    sexpdata.Symbol("effects"),
                    [sexpdata.Symbol("font"), [sexpdata.Symbol("size"), 1.27, 1.27]],
                    [sexpdata.Symbol("justify"), sexpdata.Symbol("left")],
                ],
            ]
            symbol_sexp.append(val_prop)

        # Add Footprint property
        if "footprint" in symbol_data:
            fp_prop = [
                sexpdata.Symbol("property"),
                "Footprint",
                symbol_data["footprint"],
                [sexpdata.Symbol("at"), position[0], position[1], 0],
                [
                    sexpdata.Symbol("effects"),
                    [sexpdata.Symbol("font"), [sexpdata.Symbol("size"), 1.27, 1.27]],
                    [sexpdata.Symbol("hide"), sexpdata.Symbol("yes")],
                ],
            ]
            symbol_sexp.append(fp_prop)

        return symbol_sexp

    def _format_pretty(self, data: Any, indent: int = 0) -> str:
        """Format S-expression with proper indentation."""
        if not isinstance(data, list):
            if isinstance(data, sexpdata.Symbol):
                return str(data)
            else:
                return str(data)

        if len(data) == 0:
            return "()"

        # Check if this should be on one line (short lists)
        if len(data) <= 3 and all(not isinstance(item, list) for item in data):
            return "(" + " ".join(self._format_pretty(item) for item in data) + ")"

        # Multi-line format
        indent_str = "\t" * indent
        result = "("

        for i, item in enumerate(data):
            if i == 0:
                # First item (typically the symbol name) stays on same line
                result += self._format_pretty(item, indent)
            else:
                # Subsequent items on new lines with indentation
                result += (
                    "\n" + indent_str + "\t" + self._format_pretty(item, indent + 1)
                )

        result += "\n" + indent_str + ")"
        return result
