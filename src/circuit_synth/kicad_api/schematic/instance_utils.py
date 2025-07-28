"""
Utility functions for managing symbol instances in KiCad schematics.

This module provides centralized logic for creating and managing symbol instances,
ensuring consistent behavior across all component creation paths.
"""

from typing import Optional

from ..core.types import SchematicSymbol, SymbolInstance


def add_symbol_instance(
    symbol: SchematicSymbol, project_name: str = "circuit", hierarchical_path: str = "/"
) -> None:
    """
    Add proper instance information to a schematic symbol.

    This function ensures that all symbols have the required instance data
    for proper reference designator display in KiCad.

    Args:
        symbol: The SchematicSymbol to add instance to
        project_name: Name of the KiCad project (default: "circuit")
        hierarchical_path: Hierarchical path in the schematic (default: "/" for root)
    """
    # Create the instance
    instance = SymbolInstance(
        project=project_name,
        path=hierarchical_path,
        reference=symbol.reference,
        unit=symbol.unit if symbol.unit else 1,
    )

    # Set the instances list (replacing any existing)
    symbol.instances = [instance]


def get_project_hierarchy_path(schematic_path: str) -> tuple[str, str]:
    """
    Extract the proper project name and hierarchical path from schematic context.

    This function reads the main project schematic to determine the correct
    project name and hierarchical path structure for component instances.

    Args:
        schematic_path: Path to the current schematic file

    Returns:
        Tuple of (project_name, hierarchical_path)
    """
    from pathlib import Path

    from ..core.s_expression import SExpressionParser

    try:
        path = Path(schematic_path)

        # If this is a hierarchical sheet, find the main project file
        if path.name != f"{path.parent.name}.kicad_sch":
            # Look for main project schematic
            project_files = list(path.parent.glob("*.kicad_sch"))
            main_project = None

            for proj_file in project_files:
                if proj_file.stem == path.parent.name:
                    main_project = proj_file
                    break

            if main_project and main_project.exists():
                # Parse the main project to get hierarchy info
                parser = SExpressionParser()
                main_schematic = parser.parse_file(str(main_project))

                # Find the sheet that corresponds to our file
                for sheet in main_schematic.sheets:
                    if sheet.filename == path.name:
                        project_name = main_schematic.uuid or path.parent.name
                        # Construct hierarchical path from main project UUID and sheet UUID
                        hierarchical_path = f"/{main_schematic.uuid}/{sheet.uuid}"
                        return project_name, hierarchical_path

        # Fallback: use simple project structure
        project_name = path.parent.name
        return project_name, "/"

    except Exception:
        # Safe fallback to original behavior
        return "circuit", "/"
