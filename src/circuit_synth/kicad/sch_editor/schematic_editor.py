"""
KiCad Schematic Editor
"""

import logging
from typing import Any, List

import sexpdata

# Import the new API's S-expression parser
from circuit_synth.kicad_api.core.s_expression import SExpressionParser

from .schematic_exporter import SchematicExporter

logger = logging.getLogger(__name__)


class SchematicEditor:
    """
    Edits KiCad schematic files by manipulating the S-expression data structure.
    """

    def __init__(self, schematic_path: str):
        self.schematic_path = schematic_path
        self.parser = SExpressionParser()
        # Read file content and parse
        with open(schematic_path, "r", encoding="utf-8") as f:
            content = f.read()
        self.data = self.parser.parse_string(content)

    @property
    def schematic_data(self):
        if isinstance(self.data, list):
            return self.data
        else:
            # This is a Schematic object, we need to convert it to a list of S-expressions
            exporter = SchematicExporter(self.data)
            # The exporter's `export_file` method returns a boolean, so we need to get the data from the writer
            # This is a bit of a hack, but it's the easiest way to get the data without modifying the exporter
            # The proper solution would be to have the exporter return the data directly
            # but that would require more refactoring
            # For now, we'll just write to a temporary file and read it back
            import tempfile

            with tempfile.NamedTemporaryFile(
                mode="w+", delete=False, suffix=".kicad_sch"
            ) as f:
                exporter.export_file(f.name)
                f.seek(0)
                content = f.read()
                # Clean up temp file
                import os

                os.unlink(f.name)
                return self.parser.parse_string(content)

    def remove_component(self, reference: str):
        """
        Removes a component from the schematic.
        """
        # Get the raw S-expression data
        data = self.schematic_data

        # Find the symbol with the matching reference
        for i, item in enumerate(data):
            if isinstance(item, list) and len(item) > 1 and str(item[0]) == "symbol":
                # Find the property with the name "Reference"
                for prop in item:
                    if (
                        isinstance(prop, list)
                        and len(prop) > 2
                        and str(prop[0]) == "property"
                        and str(prop[1]).strip('"') == "Reference"
                        and str(prop[2]).strip('"') == reference
                    ):
                        # Found the component, now remove it
                        del data[i]
                        # Update self.data with the modified data
                        self.data = data
                        logger.info(f"Removed component '{reference}' from schematic.")
                        return
        logger.warning(f"Component '{reference}' not found in schematic.")

    def add_component(self, component: Any):
        """
        Adds a component to the schematic.
        """
        pass

    def save(self, output_path: str = None):
        """
        Saves the modified schematic to a file.
        """
        if output_path is None:
            output_path = self.schematic_path

        # Use the new formatter from kicad_formatter.py
        from circuit_synth.kicad.sch_gen.kicad_formatter import format_kicad_schematic

        # Format the data
        formatted_content = format_kicad_schematic(self.schematic_data)

        # Write to file
        with open(output_path, "w", encoding="utf-8") as f:
            f.write(formatted_content)

        logger.info(f"Saved schematic to '{output_path}'")
