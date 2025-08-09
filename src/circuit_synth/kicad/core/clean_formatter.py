#!/usr/bin/env python3
"""
Clean S-expression formatter for KiCad schematic files.

This module provides a cleaner, more maintainable implementation of the
S-expression formatter, replacing the complex 700+ line _format_sexp method.

Key improvements:
1. Rule-based formatting using a registry
2. Clear separation of concerns
3. No complex boolean context tracking
4. Easier to extend and maintain
"""

import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Set, Tuple, Union

logger = logging.getLogger(__name__)


@dataclass
class FormatRule:
    """Formatting rule for S-expression elements."""

    inline: bool = False  # Format on single line
    max_inline_elements: Optional[int] = None  # Max elements for inline
    quote_indices: Set[int] = None  # Indices to quote
    custom_handler: Optional[Callable] = None  # Custom formatting function

    def __post_init__(self):
        if self.quote_indices is None:
            self.quote_indices = set()


class FormattingRules:
    """Registry of formatting rules for different S-expression tags."""

    def __init__(self):
        self.rules = {}
        self._initialize_rules()

    def _initialize_rules(self):
        """Initialize default formatting rules."""

        # Version and metadata - inline
        self.rules["version"] = FormatRule(inline=True)
        self.rules["generator"] = FormatRule(inline=True, quote_indices={1})
        self.rules["generator_version"] = FormatRule(inline=True, quote_indices={1})
        self.rules["uuid"] = FormatRule(inline=True)
        self.rules["paper"] = FormatRule(inline=True, quote_indices={1})

        # Properties - special KiCad format: (property "Name" "Value" ...)
        self.rules["property"] = FormatRule(
            inline=False,
            quote_indices={1, 2},  # Quote property name and value
            custom_handler=self._format_property_kicad,
        )

        # Position and geometry - inline
        self.rules["at"] = FormatRule(inline=True)
        self.rules["xy"] = FormatRule(inline=True)
        self.rules["pts"] = FormatRule(inline=False)
        self.rules["start"] = FormatRule(inline=True)
        self.rules["end"] = FormatRule(inline=True)
        self.rules["mid"] = FormatRule(inline=True)
        self.rules["center"] = FormatRule(inline=True)
        self.rules["radius"] = FormatRule(inline=True)
        self.rules["length"] = FormatRule(inline=True)
        self.rules["size"] = FormatRule(inline=True)

        # Component attributes - inline
        self.rules["unit"] = FormatRule(inline=True)
        self.rules["exclude_from_sim"] = FormatRule(inline=True)
        self.rules["in_bom"] = FormatRule(inline=True)
        self.rules["on_board"] = FormatRule(inline=True)
        self.rules["dnp"] = FormatRule(inline=True)
        self.rules["fields_autoplaced"] = FormatRule(inline=True)

        # Library references
        self.rules["lib_id"] = FormatRule(inline=True, quote_indices={1})
        self.rules["lib_name"] = FormatRule(inline=True, quote_indices={1})

        # Effects and formatting
        self.rules["effects"] = FormatRule(inline=False)
        self.rules["font"] = FormatRule(inline=False)
        self.rules["justify"] = FormatRule(inline=True)
        self.rules["hide"] = FormatRule(inline=True)

        # Pins
        self.rules["pin"] = FormatRule(inline=False, custom_handler=self._format_pin)
        self.rules["name"] = FormatRule(inline=False, quote_indices={1})
        self.rules["number"] = FormatRule(inline=False, quote_indices={1})

        # Stroke and fill
        self.rules["stroke"] = FormatRule(inline=False)
        self.rules["width"] = FormatRule(inline=True)
        self.rules["type"] = FormatRule(inline=True)
        self.rules["color"] = FormatRule(inline=True)
        self.rules["fill"] = FormatRule(inline=False)

        # Hierarchical sheets
        self.rules["sheet"] = FormatRule(inline=False)
        self.rules["hierarchical_label"] = FormatRule(inline=False, quote_indices={1})

        # Text elements
        self.rules["text"] = FormatRule(inline=False, quote_indices={1})
        self.rules["text_box"] = FormatRule(inline=False, quote_indices={1})
        self.rules["title"] = FormatRule(inline=True, quote_indices={1})
        self.rules["company"] = FormatRule(inline=True, quote_indices={1})
        self.rules["date"] = FormatRule(inline=True, quote_indices={1})
        self.rules["comment"] = FormatRule(inline=False, quote_indices={2})

        # Symbol definitions
        self.rules["symbol"] = FormatRule(
            inline=False, custom_handler=self._format_symbol
        )
        self.rules["lib_symbols"] = FormatRule(inline=False)
        self.rules["pin_numbers"] = FormatRule(
            inline=True, custom_handler=self._format_pin_numbers
        )
        self.rules["pin_names"] = FormatRule(inline=False)
        self.rules["offset"] = FormatRule(inline=True)

        # Wire and junction
        self.rules["wire"] = FormatRule(inline=False)
        self.rules["junction"] = FormatRule(inline=False)
        self.rules["no_connect"] = FormatRule(inline=False)
        self.rules["bus_entry"] = FormatRule(inline=False)
        self.rules["label"] = FormatRule(inline=False, quote_indices={1})
        self.rules["global_label"] = FormatRule(inline=False, quote_indices={1})

        # Instances - CRITICAL: Proper formatting for KiCad reference display
        self.rules["instances"] = FormatRule(
            inline=False, custom_handler=self._format_instances
        )
        self.rules["project"] = FormatRule(
            inline=False, custom_handler=self._format_project
        )
        self.rules["path"] = FormatRule(inline=False, custom_handler=self._format_path)
        self.rules["reference"] = FormatRule(
            inline=True, quote_indices={1}
        )  # Should be inline

        # Sheet instances
        self.rules["sheet_instances"] = FormatRule(inline=False)
        self.rules["page"] = FormatRule(inline=True, quote_indices={1})

    def get_rule(self, tag: str) -> FormatRule:
        """Get formatting rule for a tag.

        Args:
            tag: S-expression tag

        Returns:
            Formatting rule (default if not found)
        """
        return self.rules.get(tag, FormatRule())

    def _format_property_kicad(self, sexp: List, indent: int, formatter) -> str:
        """Custom handler for KiCad property formatting.

        KiCad properties have this specific format:
        (property "Name" "Value"
            (at x y angle)
            (effects ...)
        )

        Name and Value go on the same line as 'property'.
        """
        if len(sexp) < 3:
            return formatter._format_default(sexp, indent)

        lines = []
        indent_str = formatter._get_indent(indent)

        # Start with property tag, name, and value on same line (KiCad format)
        lines.append(f'{indent_str}(property "{sexp[1]}" "{sexp[2]}"')

        # Format remaining elements (at, effects, etc.) on subsequent lines
        for elem in sexp[3:]:
            if isinstance(elem, list):
                lines.append(formatter.format(elem, indent + 1))
            else:
                lines.append(f"{formatter._get_indent(indent + 1)}{elem}")

        lines.append(f"{indent_str})")

        return "\n".join(lines)

    def _format_pin(self, sexp: List, indent: int, formatter) -> str:
        """Custom handler for pin formatting.

        CRITICAL: KiCad expects: (pin passive line
        All on ONE line!
        """
        if len(sexp) < 2:
            return formatter._format_default(sexp, indent)

        indent_str = formatter._get_indent(indent)
        lines = []

        # Collect pin type, direction, and shape for first line
        first_line_parts = ["pin"]
        i = 1
        while i < len(sexp) and not isinstance(sexp[i], list):
            first_line_parts.append(str(sexp[i]))
            i += 1

        # Format first line with all keywords
        lines.append(f"{indent_str}({' '.join(first_line_parts)}")

        # Format remaining elements (at, length, name, number)
        for elem in sexp[i:]:
            if isinstance(elem, list):
                # Special handling for name and number - should be on same line
                if elem[0] == "name" and len(elem) >= 2:
                    lines.append(
                        f'{formatter._get_indent(indent + 1)}(name "{elem[1]}"'
                    )
                    # Format effects if present
                    for sub in elem[2:]:
                        if isinstance(sub, list):
                            lines.append(formatter.format(sub, indent + 2))
                    lines.append(f"{formatter._get_indent(indent + 1)})")
                elif elem[0] == "number" and len(elem) >= 2:
                    lines.append(
                        f'{formatter._get_indent(indent + 1)}(number "{elem[1]}"'
                    )
                    # Format effects if present
                    for sub in elem[2:]:
                        if isinstance(sub, list):
                            lines.append(formatter.format(sub, indent + 2))
                    lines.append(f"{formatter._get_indent(indent + 1)})")
                else:
                    lines.append(formatter.format(elem, indent + 1))

        lines.append(f"{indent_str})")
        return "\n".join(lines)

    def _format_pin_numbers(self, sexp: List, indent: int, formatter) -> str:
        """Custom handler for pin_numbers.

        CRITICAL: Must be (pin_numbers hide) on ONE line for KiCad
        """
        indent_str = formatter._get_indent(indent)
        if len(sexp) == 2:
            # Check if it's a symbol or string "hide"
            elem = str(sexp[1])
            if elem == "hide" or elem == "yes":
                return f"{indent_str}(pin_numbers {elem})"
            else:
                # Default format
                return f'{indent_str}(pin_numbers "{elem}")'
        else:
            # Just pin_numbers with no args
            return f"{indent_str}(pin_numbers)"

    def _format_symbol(self, sexp: List, indent: int, formatter) -> str:
        """Custom handler for symbol formatting.

        Symbols in lib_symbols have their ID on the same line as 'symbol':
        (symbol "Device:R" ...)

        Regular symbols have lib_id as a separate element:
        (symbol
            (lib_id "Device:R")
            ...)
        """
        if len(sexp) < 2:
            return formatter._format_default(sexp, indent)

        indent_str = formatter._get_indent(indent)

        # Check if this is a lib_symbols symbol (second element is a string, not a list)
        if isinstance(sexp[1], str):
            # This is a lib_symbols definition: (symbol "Device:R" ...)
            # Format with ID on same line
            lines = [f'{indent_str}(symbol "{sexp[1]}"']

            # Format remaining elements
            for elem in sexp[2:]:
                if isinstance(elem, list):
                    lines.append(formatter.format(elem, indent + 1))
                else:
                    lines.append(f"{formatter._get_indent(indent + 1)}{elem}")
        else:
            # This is a regular symbol instance
            lines = [f"{indent_str}(symbol"]

            # Format all elements normally
            for elem in sexp[1:]:
                if isinstance(elem, list):
                    lines.append(formatter.format(elem, indent + 1))
                else:
                    lines.append(f"{formatter._get_indent(indent + 1)}{elem}")

        lines.append(f"{indent_str})")
        return "\n".join(lines)

    def _format_instances(self, sexp: List, indent: int, formatter) -> str:
        """Custom handler for instances block.

        Standard format for instances block in components.
        """
        if len(sexp) < 2:
            return formatter._format_default(sexp, indent)

        lines = []
        indent_str = formatter._get_indent(indent)

        # Start with instances tag
        lines.append(f"{indent_str}(instances")

        # Format project blocks
        for elem in sexp[1:]:
            if isinstance(elem, list):
                lines.append(formatter.format(elem, indent + 1))
            else:
                lines.append(f"{formatter._get_indent(indent + 1)}{elem}")

        lines.append(f"{indent_str})")
        return "\n".join(lines)

    def _format_project(self, sexp: List, indent: int, formatter) -> str:
        """Custom handler for project element in instances.

        CRITICAL: Project name MUST be on same line as 'project':
        (project "reference_generated"
            (path ...))
        """
        if len(sexp) < 2:
            return formatter._format_default(sexp, indent)

        indent_str = formatter._get_indent(indent)

        # Project name on same line as 'project'
        project_name = sexp[1] if len(sexp) > 1 else ""
        if isinstance(project_name, str) and project_name:
            lines = [f'{indent_str}(project "{project_name}"']
        else:
            lines = [f"{indent_str}(project"]

        # Format path block (should be the next element)
        for elem in sexp[2:]:
            if isinstance(elem, list):
                lines.append(formatter.format(elem, indent + 1))
            else:
                lines.append(f"{formatter._get_indent(indent + 1)}{elem}")

        lines.append(f"{indent_str})")
        return "\n".join(lines)

    def _format_path(self, sexp: List, indent: int, formatter) -> str:
        """Custom handler for path element in instances.

        CRITICAL: Path UUID MUST be on same line as 'path':
        (path "/7992fcb0-e3cc-44bb-8801-36d85754f2fc"
            (reference "R1")
            (unit 1))
        """
        if len(sexp) < 2:
            return formatter._format_default(sexp, indent)

        indent_str = formatter._get_indent(indent)

        # Path UUID on same line as 'path'
        path_uuid = sexp[1] if len(sexp) > 1 else "/"
        if isinstance(path_uuid, str):
            lines = [f'{indent_str}(path "{path_uuid}"']
        else:
            lines = [f"{indent_str}(path"]

        # Format reference and unit (should be the next elements)
        for elem in sexp[2:]:
            if isinstance(elem, list):
                lines.append(formatter.format(elem, indent + 1))
            else:
                lines.append(f"{formatter._get_indent(indent + 1)}{elem}")

        lines.append(f"{indent_str})")
        return "\n".join(lines)


class CleanSExprFormatter:
    """Clean S-expression formatter using rule-based approach."""

    def __init__(self, use_tabs: bool = True):
        """Initialize formatter.

        Args:
            use_tabs: If True, use tabs for indentation (KiCad default), else use spaces
        """
        self.use_tabs = use_tabs
        self.indent_char = "\t" if use_tabs else "  "
        self.rules = FormattingRules()

    def format(self, sexp: Union[List, str, int, float], indent: int = 0) -> str:
        """Format S-expression with proper indentation and structure.

        Args:
            sexp: S-expression to format (list, string, or primitive)
            indent: Current indentation level

        Returns:
            Formatted S-expression string
        """
        # Handle primitives
        if not isinstance(sexp, list):
            return self._format_primitive(sexp)

        # Empty list
        if not sexp:
            return "()"

        # Get tag and formatting rule
        tag = self._get_tag(sexp)
        rule = self.rules.get_rule(tag)

        # Use custom handler if available
        if rule.custom_handler:
            return rule.custom_handler(sexp, indent, self)

        # Apply standard formatting based on rule
        if rule.inline and self._can_inline(sexp, rule):
            return self._format_inline(sexp, indent, rule)
        else:
            return self._format_multiline(sexp, indent, rule)

    def _get_tag(self, sexp: List) -> str:
        """Get the tag (first element) of an S-expression.

        Args:
            sexp: S-expression list

        Returns:
            Tag string or empty string
        """
        if sexp and isinstance(sexp[0], str):
            return sexp[0]
        return ""

    def _can_inline(self, sexp: List, rule: FormatRule) -> bool:
        """Check if S-expression can be formatted inline.

        Args:
            sexp: S-expression list
            rule: Formatting rule

        Returns:
            True if can be inlined
        """
        # Check max elements constraint
        if rule.max_inline_elements and len(sexp) > rule.max_inline_elements:
            return False

        # Check if any element is a complex list
        for elem in sexp[1:]:
            if isinstance(elem, list) and len(elem) > 3:
                return False

        return True

    def _format_inline(self, sexp: List, indent: int, rule: FormatRule) -> str:
        """Format S-expression on a single line.

        Args:
            sexp: S-expression list
            indent: Indentation level
            rule: Formatting rule

        Returns:
            Inline formatted string
        """
        indent_str = self._get_indent(indent)

        # Format elements with proper quoting
        elements = []
        for i, elem in enumerate(sexp):
            if i in rule.quote_indices:
                elements.append(self._quote_if_needed(elem, force_quote=True))
            elif isinstance(elem, list):
                # Recursively format nested lists
                elements.append(self.format(elem, 0))
            else:
                elements.append(self._format_primitive(elem))

        return f"{indent_str}({' '.join(elements)})"

    def _format_multiline(self, sexp: List, indent: int, rule: FormatRule) -> str:
        """Format S-expression across multiple lines.

        Args:
            sexp: S-expression list
            indent: Indentation level
            rule: Formatting rule

        Returns:
            Multiline formatted string
        """
        lines = []
        indent_str = self._get_indent(indent)

        # Start with opening parenthesis and tag
        if sexp:
            tag = self._format_primitive(sexp[0])
            lines.append(f"{indent_str}({tag}")

            # Format remaining elements
            for i, elem in enumerate(sexp[1:], 1):
                if i in rule.quote_indices:
                    lines.append(
                        f"{self._get_indent(indent + 1)}{self._quote_if_needed(elem, force_quote=True)}"
                    )
                elif isinstance(elem, list):
                    lines.append(self.format(elem, indent + 1))
                else:
                    lines.append(
                        f"{self._get_indent(indent + 1)}{self._format_primitive(elem)}"
                    )

        # Close parenthesis
        lines.append(f"{indent_str})")

        return "\n".join(lines)

    def _format_default(self, sexp: List, indent: int) -> str:
        """Default formatting when no specific rule applies.

        Args:
            sexp: S-expression list
            indent: Indentation level

        Returns:
            Formatted string
        """
        return self._format_multiline(sexp, indent, FormatRule())

    def _format_primitive(self, value: Any) -> str:
        """Format a primitive value.

        Args:
            value: Primitive value (string, number, etc.)

        Returns:
            String representation
        """
        if isinstance(value, bool):
            return "yes" if value else "no"
        elif isinstance(value, float):
            # Format floats without unnecessary decimals
            # 0.0 -> 0, 45.72 -> 45.72
            if value == int(value):
                return str(int(value))
            else:
                # Remove trailing zeros
                formatted = f"{value:.10f}".rstrip("0").rstrip(".")
                return formatted
        elif isinstance(value, int):
            return str(value)
        else:
            return str(value)

    def _quote_if_needed(self, value: Any, force_quote: bool = False) -> str:
        """Quote a value if it needs quoting.

        Args:
            value: Value to potentially quote
            force_quote: Always quote regardless of content

        Returns:
            Quoted or unquoted string
        """
        s = str(value)

        # Check if quoting is needed
        needs_quote = (
            force_quote
            or " " in s
            or "(" in s
            or ")" in s
            or '"' in s
            or "\n" in s
            or "\t" in s
            or s == ""
            or s.startswith("#")
            or ":" in s  # Library IDs like "Device:R" need quotes
            or "/" in s  # Path separators need quotes
        )

        if needs_quote:
            # Escape special characters for KiCad format
            s = s.replace("\\", "\\\\").replace('"', '\\"').replace("\n", "\\n")
            return f'"{s}"'

        return s

    def _get_indent(self, level: int) -> str:
        """Get indentation string for given level.

        Args:
            level: Indentation level

        Returns:
            Indentation string
        """
        return self.indent_char * level

    def format_schematic(self, circuit_data: Dict) -> str:
        """Format a complete schematic from circuit data.

        Args:
            circuit_data: Circuit data dictionary

        Returns:
            Formatted KiCad schematic S-expression
        """
        # Build schematic S-expression structure
        schematic = [
            "kicad_sch",
            ["version", 20250114],
            ["generator", "circuit_synth"],
            ["generator_version", "9.0"],
            ["uuid", circuit_data.get("uuid", "generated-uuid")],
            ["paper", circuit_data.get("paper", "A4")],
        ]

        # Add lib_symbols if present
        if "lib_symbols" in circuit_data:
            schematic.append(["lib_symbols"] + circuit_data["lib_symbols"])

        # Add components
        for comp in circuit_data.get("components", []):
            schematic.append(self._build_component_sexp(comp))

        # Add wires
        for wire in circuit_data.get("wires", []):
            schematic.append(self._build_wire_sexp(wire))

        # Add labels
        for label in circuit_data.get("labels", []):
            schematic.append(self._build_label_sexp(label))

        # Add sheets
        for sheet in circuit_data.get("sheets", []):
            schematic.append(self._build_sheet_sexp(sheet))

        # Add instances
        if "instances" in circuit_data:
            schematic.append(["instances"] + circuit_data["instances"])

        # Add sheet_instances
        if "sheet_instances" in circuit_data:
            schematic.append(["sheet_instances"] + circuit_data["sheet_instances"])

        # Format and return
        return self.format(schematic)

    def _build_component_sexp(self, comp: Dict) -> List:
        """Build component S-expression from data.

        Args:
            comp: Component data dictionary

        Returns:
            S-expression list
        """
        sexp = [
            "symbol",
            ["lib_id", comp.get("lib_id", "Device:R")],
            ["at", comp.get("x", 0), comp.get("y", 0), comp.get("angle", 0)],
            ["unit", comp.get("unit", 1)],
            ["exclude_from_sim", "no"],
            ["in_bom", "yes"],
            ["on_board", "yes"],
            ["dnp", "no"],
        ]

        # Add UUID
        if "uuid" in comp:
            sexp.append(["uuid", comp["uuid"]])

        # Add properties
        sexp.append(
            [
                "property",
                "Reference",
                comp.get("reference", "REF"),
                ["at", 0, 0, 0],
                ["effects", ["font", ["size", 1.27, 1.27]]],
            ]
        )

        sexp.append(
            [
                "property",
                "Value",
                comp.get("value", ""),
                ["at", 0, 5, 0],
                ["effects", ["font", ["size", 1.27, 1.27]]],
            ]
        )

        return sexp

    def _build_wire_sexp(self, wire: Dict) -> List:
        """Build wire S-expression from data."""
        return [
            "wire",
            [
                "pts",
                ["xy", wire["start_x"], wire["start_y"]],
                ["xy", wire["end_x"], wire["end_y"]],
            ],
            ["stroke", ["width", 0], ["type", "default"]],
            ["uuid", wire.get("uuid", "wire-uuid")],
        ]

    def _build_label_sexp(self, label: Dict) -> List:
        """Build label S-expression from data."""
        return [
            "label",
            label["text"],
            ["at", label["x"], label["y"], label.get("angle", 0)],
            ["effects", ["font", ["size", 1.27, 1.27]]],
            ["uuid", label.get("uuid", "label-uuid")],
        ]

    def _build_sheet_sexp(self, sheet: Dict) -> List:
        """Build sheet S-expression from data."""
        return [
            "sheet",
            ["at", sheet["x"], sheet["y"]],
            ["size", sheet["width"], sheet["height"]],
            ["stroke", ["width", 0.12], ["type", "solid"]],
            ["fill", ["color", 0, 0, 0, 0.0]],
            ["uuid", sheet.get("uuid", "sheet-uuid")],
            [
                "property",
                "Sheetname",
                sheet["name"],
                ["at", sheet["x"], sheet["y"] - 1.27, 0],
                [
                    "effects",
                    ["font", ["size", 1.27, 1.27]],
                    ["justify", "left", "bottom"],
                ],
            ],
            [
                "property",
                "Sheetfile",
                sheet["file"],
                ["at", sheet["x"], sheet["y"] + sheet["height"] + 1.27, 0],
                [
                    "effects",
                    ["font", ["size", 1.27, 1.27]],
                    ["justify", "left", "top"],
                    ["hide", "yes"],
                ],
            ],
        ]
