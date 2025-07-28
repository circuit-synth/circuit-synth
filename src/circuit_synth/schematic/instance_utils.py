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
