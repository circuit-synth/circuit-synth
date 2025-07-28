"""
Custom S-expression formatter for KiCad PCB files.

This formatter ensures that symbols are written as unquoted identifiers,
which is required by KiCad's PCB parser.
"""

from typing import Any, List, Union

import sexpdata


class PCBFormatter:
    """Custom formatter for PCB S-expressions that handles symbols correctly."""

    def __init__(self):
        self.indent_level = 0
        self.indent_str = "  "

    def format(self, sexp: Any) -> str:
        """Format an S-expression to a string."""
        if isinstance(sexp, list):
            return self._format_list(sexp)
        elif isinstance(sexp, sexpdata.Symbol):
            # Symbols should be unquoted
            return str(sexp)
        elif isinstance(sexp, str):
            # Check if this string should be treated as a symbol (unquoted)
            # These are KiCad keywords that should never be quoted
            keywords = {
                "setup",
                "general",
                "layers",
                "pcbplotparams",
                "paper",
                "net",
                "footprint",
                "via",
                "segment",
                "zone",
                "group",
                "dimension",
                "gr_line",
                "gr_rect",
                "gr_circle",
                "gr_arc",
                "gr_text",
                "pad_to_mask_clearance",
                "allow_soldermask_bridges_in_footprints",
                "tenting",
                "layerselection",
                "plot_on_all_layers_selection",
                "disableapertmacros",
                "usegerberextensions",
                "usegerberattributes",
                "usegerberadvancedattributes",
                "creategerberjobfile",
                "dashed_line_dash_ratio",
                "dashed_line_gap_ratio",
                "svgprecision",
                "plotframeref",
                "mode",
                "useauxorigin",
                "hpglpennumber",
                "hpglpenspeed",
                "hpglpendiameter",
                "pdf_front_fp_property_popups",
                "pdf_back_fp_property_popups",
                "pdf_metadata",
                "pdf_single_document",
                "dxfpolygonmode",
                "dxfimperialunits",
                "dxfusepcbnewfont",
                "psnegative",
                "psa4output",
                "plot_black_and_white",
                "plotinvisibletext",
                "sketchpadsonfab",
                "plotpadnumbers",
                "hidednponfab",
                "sketchdnponfab",
                "crossoutdnponfab",
                "subtractmaskfromsilk",
                "outputformat",
                "mirror",
                "drillshape",
                "scaleselection",
                "outputdirectory",
                "thickness",
                "legacy_teardrops",
                "front",
                "back",
                "yes",
                "no",
                "signal",
                "user",
            }

            if sexp in keywords:
                return sexp  # Unquoted
            else:
                return f'"{sexp}"'  # Quoted
        elif isinstance(sexp, (int, float)):
            return str(sexp)
        elif isinstance(sexp, bool):
            return "yes" if sexp else "no"
        else:
            return str(sexp)

    def _format_list(self, lst: List) -> str:
        """Format a list S-expression."""
        if not lst:
            return "()"

        # Check if this is a simple key-value pair
        if len(lst) == 2 and not isinstance(lst[1], list):
            return f"({self.format(lst[0])} {self.format(lst[1])})"

        # Check if first element is a symbol or string
        if lst and (isinstance(lst[0], sexpdata.Symbol) or isinstance(lst[0], str)):
            symbol_name = str(lst[0])

            # Special handling for certain elements that should be on one line
            if symbol_name in [
                "at",
                "size",
                "thickness",
                "width",
                "layer",
                "effects",
                "font",
                "justify",
                "uuid",
                "stroke",
                "fill",
                "net",
                "drill",
                "layers",
                "roundrect_rratio",
                "thermal_bridge_angle",
                "thermal_gap",
                "thermal_bridge_width",
            ]:
                # Format inline
                parts = [self.format(item) for item in lst]
                return f"({' '.join(parts)})"

            # Multi-line formatting for complex structures
            result = f"({self.format(lst[0])}"

            # Handle the rest of the elements
            for item in lst[1:]:
                if isinstance(item, list):
                    # Sub-lists go on new lines with increased indent
                    self.indent_level += 1
                    formatted = self.format(item)
                    self.indent_level -= 1
                    result += (
                        f"\n{self.indent_str * (self.indent_level + 1)}{formatted}"
                    )
                else:
                    # Simple values stay on the same line
                    result += f" {self.format(item)}"

            result += ")"
            return result
        else:
            # Not a symbol-led list, format all elements
            parts = [self.format(item) for item in lst]
            return f"({' '.join(parts)})"

    def format_pcb(self, sexp: List) -> str:
        """
        Format a complete PCB S-expression with special handling for the header.

        Args:
            sexp: The PCB S-expression list

        Returns:
            Formatted string
        """
        if (
            not sexp
            or not isinstance(sexp[0], sexpdata.Symbol)
            or str(sexp[0]) != "kicad_pcb"
        ):
            return self.format(sexp)

        # Special handling for kicad_pcb root element
        result = "(kicad_pcb"

        # Format header elements inline
        i = 1
        while i < len(sexp):
            item = sexp[i]
            if isinstance(item, list) and len(item) >= 2:
                key = str(item[0]) if isinstance(item[0], sexpdata.Symbol) else None
                if key in ["version", "generator", "generator_version"]:
                    result += f" {self.format(item)}"
                    i += 1
                else:
                    break
            else:
                break

        # Add newline after header
        result += "\n"

        # Format the rest of the elements
        for j in range(i, len(sexp)):
            self.indent_level = 0
            formatted = self.format(sexp[j])
            result += f"  {formatted}\n"

        result += ")"
        return result
