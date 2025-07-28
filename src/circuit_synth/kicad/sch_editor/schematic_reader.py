"""
SchematicReader module for parsing KiCad schematic files.

This module implements the SchematicReader class which uses the S-expression parser
to read and interpret KiCad schematic files. It handles:
- Component extraction with pin types
- Net connections with preserved paths
- Hierarchical sheet support
- Pin type preservation according to the Pin Type Handling Pattern
- Path preservation following the Path Preservation Pattern
"""

from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

import sexpdata

# Import the new API's S-expression parser
from circuit_synth.kicad_api.core.s_expression import SExpressionParser


@dataclass
class SchematicPin:
    """Represents a component pin with type information."""

    number: str
    type: str
    net_name: Optional[str] = None
    uuid: Optional[str] = None


@dataclass
class SchematicSymbol:
    """Represents a schematic component with pins and all properties."""

    reference: str
    value: str
    footprint: Optional[str]
    unit: int
    pins: List[SchematicPin]
    uuid: str
    lib_id: str
    position: Optional[tuple[float, float, float]] = None  # x, y, rotation
    in_bom: bool = True
    on_board: bool = True
    fields_autoplaced: bool = True
    properties: Dict[str, str] = None  # Store all properties as a dictionary

    def __post_init__(self):
        if self.properties is None:
            self.properties = {}


@dataclass
class NetNode:
    """Represents a node in a net connection."""

    component_ref: str
    pin_num: str
    pin_type: str
    uuid: str


@dataclass
class SchematicNet:
    """Represents a net with hierarchical path information."""

    name: str
    full_path: str
    nodes: List[NetNode]
    uuid: str


@dataclass
class HierarchicalLabel:
    """Represents a hierarchical label in the schematic."""

    name: str
    shape: str  # input, output, bidirectional, tri_state, passive
    position: Tuple[float, float]  # x, y coordinates
    effects: Dict[str, Any]  # font, justify, etc.
    uuid: str


@dataclass
class SchematicSheet:
    """Represents a hierarchical sheet."""

    name: str
    path: str
    parent_path: Optional[str]
    uuid: str


@dataclass
class Schematic:
    """Represents a complete KiCad schematic."""

    components: List[SchematicSymbol]
    nets: List[SchematicNet]
    sheets: List[SchematicSheet]
    hierarchical_labels: List[HierarchicalLabel]
    lib_symbols: Dict[str, Any]  # Store raw S-expression for lib_symbols
    version: str
    uuid: str
    # Store raw hierarchical data for proper export
    sheet_instances: Optional[Any] = None  # Raw sheet_instances S-expression
    symbol_instances: Optional[Any] = None  # Raw symbol_instances S-expression
    hierarchical_path: Optional[str] = None  # Path for this schematic in hierarchy

    def __iter__(self):
        """Make Schematic iterable to support iteration over components."""
        return iter(self.components)

    def get_component(self, reference: str) -> Optional[SchematicSymbol]:
        """Get a component by its reference designator.

        Args:
            reference: The reference designator to search for (e.g. 'R1', 'U2')

        Returns:
            The matching SchematicSymbol or None if not found
        """
        for component in self.components:
            if component.reference == reference:
                return component
        return None


class SchematicReader:
    """Reader for KiCad schematic files implementing pin type and path preservation."""

    def __init__(self):
        self.parser = SExpressionParser()
        self._lib_symbols: Dict[str, dict] = {}
        self._current_sheet_path = "/"

    def read_file(self, filepath: str) -> Schematic:
        """Read and parse a KiCad schematic file.

        Args:
            filepath: Path to .kicad_sch file

        Returns:
            Parsed Schematic object

        Raises:
            FileNotFoundError: If file doesn't exist
            ValueError: If file format is invalid
        """
        try:
            # The new parser returns the parsed data directly
            with open(filepath, "r", encoding="utf-8") as f:
                content = f.read()
            data = self.parser.parse_string(content)
        except FileNotFoundError:
            raise FileNotFoundError(f"Schematic file not found: {filepath}")
        except Exception as e:
            raise ValueError(f"Failed to parse schematic file: {str(e)}")

        if not isinstance(data, list) or not data:
            raise ValueError("Invalid KiCad schematic format: Empty or invalid file")

        # The first element should be 'kicad_sch' (as a Symbol)
        if not (len(data) > 0 and str(data[0]) == "kicad_sch"):
            raise ValueError(
                "Invalid KiCad schematic format: File must start with (kicad_sch ...)"
            )

        kicad_sch = data  # The entire data is the kicad_sch element

        # Extract version and uuid from kicad_sch section
        version = None
        uuid = None
        for item in kicad_sch[1:]:  # Skip 'kicad_sch' token
            if isinstance(item, list):
                if str(item[0]) == "version":
                    version = str(item[1])
                elif str(item[0]) == "uuid":
                    uuid = str(item[1])

        if not version:
            raise ValueError("Invalid KiCad schematic format: Missing version")
        if not uuid:
            raise ValueError("Invalid KiCad schematic format: Missing uuid")

        # Parse library symbols first
        self._parse_lib_symbols(data)

        # Parse sheets to establish hierarchy
        sheets = self._parse_sheets(data)

        # Parse components with pin types
        components = self._parse_components(data)

        # Parse nets with preserved paths
        nets = self._parse_nets(data, components)

        # Parse hierarchical labels
        hierarchical_labels = self._parse_hierarchical_labels(data)

        # Extract raw sheet_instances and symbol_instances for hierarchical preservation
        sheet_instances_raw = None
        symbol_instances_raw = None

        sheet_instances_sections = self._find_sections(data, "sheet_instances")
        if sheet_instances_sections:
            sheet_instances_raw = sheet_instances_sections[
                0
            ]  # Store the raw S-expression

        symbol_instances_sections = self._find_sections(data, "symbol_instances")
        if symbol_instances_sections:
            symbol_instances_raw = symbol_instances_sections[
                0
            ]  # Store the raw S-expression

        return Schematic(
            components=components,
            nets=nets,
            sheets=sheets,
            hierarchical_labels=hierarchical_labels,
            version=version,
            uuid=uuid,
            lib_symbols=self._lib_symbols,
            sheet_instances=sheet_instances_raw,
            symbol_instances=symbol_instances_raw,
        )

    def _parse_lib_symbols(self, data: List) -> None:
        """Parse library symbol definitions for pin type information."""
        lib_symbols = self._find_sections(data, "lib_symbols")
        for lib_section in lib_symbols:
            for symbol in lib_section[1:]:  # Skip 'lib_symbols' token
                if isinstance(symbol, list) and len(symbol) > 1:
                    lib_id = str(symbol[1])  # Symbol name/id
                    pin_types = {}

                    # Extract pin definitions
                    for pin_def in self._find_sections(symbol, "pin"):
                        num = self._get_value(pin_def, "number")
                        pin_type = self._get_value(pin_def, "type") or "passive"
                        if num:
                            pin_types[num] = pin_type

                    self._lib_symbols[lib_id] = (
                        symbol  # Store the full S-expression for the symbol
                    )

    def _parse_sheets(self, data: List) -> List[SchematicSheet]:
        """Parse hierarchical sheets with path preservation."""
        sheets = []
        sheet_instances = self._find_sections(data, "sheet_instances")

        # Always add root sheet
        sheets.append(SchematicSheet(name="", path="/", parent_path=None, uuid=""))

        for instance in sheet_instances:
            for path_def in self._find_sections(instance, "path"):
                path = self._get_value(path_def, "path")
                if path:
                    # Handle both absolute and relative paths
                    if not path.startswith("/"):
                        path = f"/{path}"

                    # Get parent path
                    path_parts = path.rstrip("/").split("/")
                    parent_path = "/".join(path_parts[:-1]) or None
                    if parent_path == "":
                        parent_path = "/"

                    sheets.append(
                        SchematicSheet(
                            name=path_parts[-1] if path_parts else "",
                            path=path,
                            parent_path=parent_path,
                            uuid=self._get_value(path_def, "uuid") or "",
                        )
                    )

        return sheets

    def _parse_components(self, data: List) -> List[SchematicSymbol]:
        """Parse components with pin type preservation."""
        components = []

        # First parse lib_symbols to have them available
        self._parse_lib_symbols(data)

        # Look for symbol sections (newer format)
        symbol_sections = self._find_sections(data, "symbol")
        for section in symbol_sections:
            try:
                component = self._parse_symbol_section(section)
                if component:
                    components.append(component)
            except Exception as e:
                print(f"Warning: Failed to parse symbol: {str(e)}")

        # Look for comp sections (older format) if no symbols found
        if not components:
            comp_sections = self._find_sections(data, "comp")
            for section in comp_sections:
                try:
                    component = self._parse_comp_section(section)
                    if component:
                        components.append(component)
                except Exception as e:
                    print(f"Warning: Failed to parse component: {str(e)}")

        return components

    def _parse_symbol_section(self, section: List) -> Optional[SchematicSymbol]:
        """Parse a symbol section into a SchematicSymbol."""
        try:
            # Check if this is a library symbol (has pin definitions) or a component instance
            # Library symbols have 'pin' sections and should be skipped
            if self._find_sections(section, "pin"):
                return None  # This is a library symbol definition, not a component instance

            # Get basic component info
            lib_id = self._get_value(section, "lib_id")
            if not lib_id:
                return None

            # Get position
            position = None
            at_section = self._find_sections(section, "at")
            if at_section and len(at_section[0]) >= 3:
                x = float(at_section[0][1])
                y = float(at_section[0][2])
                rotation = float(at_section[0][3]) if len(at_section[0]) > 3 else 0.0
                position = (x, y, rotation)

            # Get properties
            properties = {}
            for prop in self._find_sections(section, "property"):
                if len(prop) >= 2:
                    prop_name = str(prop[1]).strip('"')
                    prop_value = str(prop[2]).strip('"') if len(prop) > 2 else ""
                    properties[prop_name] = prop_value

            ref = properties.get("Reference")
            value = properties.get("Value", "")  # Default to empty string if no value
            footprint = properties.get("Footprint")

            if not ref:  # Only require reference, not value
                return None

            # Get unit and uuid
            unit = int(self._get_value(section, "unit") or 1)
            uuid = self._get_value(section, "uuid") or ""

            # Get flags
            in_bom = self._get_value(section, "in_bom") != "no"
            on_board = self._get_value(section, "on_board") != "no"
            fields_autoplaced = "fields_autoplaced" in [
                str(x) for x in section if isinstance(x, sexpdata.Symbol)
            ]

            # Parse pins
            pins = []
            for pin_def in self._find_sections(section, "pin"):
                pin_num = self._get_value(pin_def, "number")
                if not pin_num:
                    continue

                pin_type = self._get_value(pin_def, "type")
                if not pin_type:
                    pin_type = self._get_libpart_pin_type(lib_id, pin_num)
                if not pin_type:
                    pin_type = "passive"

                pin_type = pin_type.lower()
                if pin_type not in [
                    "input",
                    "output",
                    "bidirectional",
                    "tristate",
                    "passive",
                    "power_in",
                    "power_out",
                    "open_collector",
                    "open_emitter",
                    "unspecified",
                ]:
                    pin_type = "passive"

                pin_uuid = self._get_value(pin_def, "uuid") or ""
                pins.append(SchematicPin(number=pin_num, type=pin_type, uuid=pin_uuid))

            return SchematicSymbol(
                reference=ref,
                value=value,
                footprint=footprint,
                unit=unit,
                pins=pins,
                uuid=uuid,
                lib_id=lib_id,
                position=position,
                in_bom=in_bom,
                on_board=on_board,
                fields_autoplaced=fields_autoplaced,
                properties=properties,
            )
        except Exception as e:
            raise ValueError(f"Failed to parse symbol section: {str(e)}")

    def _parse_comp_section(self, section: List) -> Optional[SchematicSymbol]:
        """Parse a comp section into a SchematicSymbol."""
        try:
            # Get component info
            properties = {}
            # Extract common properties directly
            ref = self._get_value(section, "ref")
            if ref:
                properties["Reference"] = ref
            value = self._get_value(section, "value")
            if value:
                properties["Value"] = value
            footprint = self._get_value(section, "footprint")
            if footprint:
                properties["Footprint"] = footprint

            # Get lib_id from libsource
            lib_id = None
            libsource = self._find_sections(section, "libsource")
            if libsource and len(libsource[0]) >= 3:
                lib = self._get_value(libsource[0], "lib")
                part = self._get_value(libsource[0], "part")
                if lib and part:
                    lib_id = f"{lib}:{part}"

            if not (ref and value and lib_id):
                return None

            # Get unit and uuid
            unit = int(self._get_value(section, "unit") or 1)
            uuid = self._get_value(section, "uuid") or ""

            # Extract additional fields from 'fields' section if present
            fields_section = self._find_sections(section, "fields")
            if fields_section:
                for field in self._find_sections(fields_section[0], "field"):
                    if len(field) >= 3:
                        field_name = str(field[1]).strip('"')
                        field_value = str(field[2]).strip('"')
                        properties[field_name] = field_value

            # Parse pins
            pins = []
            for pin_def in self._find_sections(section, "pin"):
                pin_num = self._get_value(pin_def, "num")
                if not pin_num:
                    continue

                pin_type = self._get_value(pin_def, "type")
                if not pin_type:
                    pin_type = self._get_libpart_pin_type(lib_id, pin_num)
                if not pin_type:
                    pin_type = "passive"

                pin_type = pin_type.lower()
                if pin_type not in [
                    "input",
                    "output",
                    "bidirectional",
                    "tristate",
                    "passive",
                    "power_in",
                    "power_out",
                    "open_collector",
                    "open_emitter",
                    "unspecified",
                ]:
                    pin_type = "passive"

                pin_uuid = self._get_value(pin_def, "uuid") or ""
                pins.append(SchematicPin(number=pin_num, type=pin_type, uuid=pin_uuid))

            return SchematicSymbol(
                reference=ref,
                value=value,
                footprint=footprint,
                unit=unit,
                pins=pins,
                uuid=uuid,
                lib_id=lib_id,
                position=None,  # Comp sections don't have position info
                in_bom=True,  # Default values for comp sections
                on_board=True,
                fields_autoplaced=False,
                properties=properties,
            )
        except Exception as e:
            raise ValueError(f"Failed to parse comp section: {str(e)}")

    def _parse_nets(
        self, data: List, components: List[SchematicSymbol]
    ) -> List[SchematicNet]:
        """Parse nets with path preservation."""
        nets = []
        net_sections = self._find_sections(data, "net")

        for net_section in net_sections:
            try:
                name = self._get_value(net_section, "name")
                if not name:
                    continue

                # Preserve hierarchical path
                path_parts = name.split("/")
                local_name = path_parts[-1]

                # Handle absolute and relative paths
                if name.startswith("/"):
                    full_path = name
                else:
                    # Use current sheet path for relative paths
                    full_path = f"{self._current_sheet_path.rstrip('/')}/{name}"

                nodes = []
                for node_def in self._find_sections(net_section, "node"):
                    ref = self._get_value(node_def, "ref")
                    pin_num = self._get_value(node_def, "pin")

                    if not (ref and pin_num):
                        continue

                    # Get pin type from component if possible
                    pin_type = "passive"  # Default type
                    for comp in components:  # Use the passed components list
                        if comp.reference == ref:
                            for pin in comp.pins:
                                if pin.number == pin_num:
                                    pin_type = pin.type
                                    break
                            break

                    nodes.append(
                        NetNode(
                            component_ref=ref,
                            pin_num=pin_num,
                            pin_type=pin_type,
                            uuid=self._get_value(node_def, "uuid") or "",
                        )
                    )

                if nodes:  # Only add nets that have nodes
                    nets.append(
                        SchematicNet(
                            name=local_name,
                            full_path=full_path,
                            nodes=nodes,
                            uuid=self._get_value(net_section, "uuid") or "",
                        )
                    )
            except Exception as e:
                print(f"Warning: Failed to parse net: {str(e)}")
                continue

        return nets

    def _parse_hierarchical_labels(self, data: List) -> List[HierarchicalLabel]:
        """Parse hierarchical labels from the schematic."""
        labels = []
        label_sections = self._find_sections(data, "hierarchical_label")

        for label_section in label_sections:
            try:
                # Extract label name (it's the second element after 'hierarchical_label')
                if len(label_section) < 2:
                    continue

                name = str(label_section[1]).strip('"')

                # Get shape
                shape_sections = self._find_sections(label_section, "shape")
                shape = "input"  # default
                if shape_sections and len(shape_sections[0]) > 1:
                    shape = str(shape_sections[0][1])

                # Get position
                at_sections = self._find_sections(label_section, "at")
                position = (0.0, 0.0)  # default
                if at_sections and len(at_sections[0]) >= 3:
                    x = float(at_sections[0][1])
                    y = float(at_sections[0][2])
                    position = (x, y)

                # Get effects (font, justify, etc.)
                effects = {}
                effects_sections = self._find_sections(label_section, "effects")
                if effects_sections:
                    for effect_section in effects_sections:
                        # Parse font
                        font_sections = self._find_sections(effect_section, "font")
                        if font_sections:
                            effects["font"] = font_sections[0]

                        # Parse justify
                        justify_sections = self._find_sections(
                            effect_section, "justify"
                        )
                        if justify_sections and len(justify_sections[0]) > 1:
                            effects["justify"] = str(justify_sections[0][1])

                # Get UUID
                uuid = self._get_value(label_section, "uuid") or ""

                labels.append(
                    HierarchicalLabel(
                        name=name,
                        shape=shape,
                        position=position,
                        effects=effects,
                        uuid=uuid,
                    )
                )

            except Exception as e:
                print(f"Warning: Failed to parse hierarchical label: {str(e)}")
                continue

        return labels

    def _get_libpart_pin_type(self, lib_id: str, pin_num: str) -> Optional[str]:
        """Get pin type from library part definition."""
        if lib_id in self._lib_symbols:
            # The _lib_symbols now stores the full S-expression, not a dict with pin_types
            symbol_data = self._lib_symbols[lib_id]
            # Find pin definitions in the symbol data
            for pin_def in self._find_sections(symbol_data, "pin"):
                num = self._get_value(pin_def, "number")
                if num == pin_num:
                    return self._get_value(pin_def, "type") or "passive"
        return None

    # Helper methods to replace the old parser's methods
    def _find_sections(self, expr: List[Any], name: str) -> List[List[Any]]:
        """Find all sections with the given name in an S-expression.

        Args:
            expr: S-expression to search (as nested lists)
            name: Name of sections to find (e.g., "component", "pin")

        Returns:
            List of matching sections
        """
        result = []
        if isinstance(expr, list):
            for item in expr:
                if isinstance(item, list) and len(item) > 0:
                    # Check if first element is a symbol with the given name
                    first_elem = item[0]
                    if (
                        isinstance(first_elem, sexpdata.Symbol)
                        and str(first_elem) == name
                    ):
                        result.append(item)
                    # Recursively search in nested lists
                    result.extend(self._find_sections(item, name))
        return result

    def _get_value(self, expr: List[Any], key: str) -> Optional[Any]:
        """Get value associated with a key in an S-expression.

        Args:
            expr: S-expression to search (as nested lists)
            key: Key to find value for

        Returns:
            Associated value if found, None otherwise
        """
        if isinstance(expr, list):
            for item in expr:
                if isinstance(item, list) and len(item) >= 2:
                    if isinstance(item[0], sexpdata.Symbol) and str(item[0]) == key:
                        return item[1]
        return None
