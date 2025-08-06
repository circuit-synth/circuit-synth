"""
Sheet management for hierarchical KiCad schematics.

This module provides functionality for creating and managing hierarchical
sheets in KiCad schematics.
"""

import logging
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

from ..core.s_expression import SExpressionParser
from ..core.types import BoundingBox, Point, Schematic, SchematicSymbol, Sheet, SheetPin

logger = logging.getLogger(__name__)


@dataclass
class SheetInfo:
    """Information about a sheet and its contents."""

    sheet: Sheet
    schematic: Optional[Schematic] = None
    instance_count: int = 1
    parent_sheet: Optional[str] = None  # UUID of parent sheet


class SheetManager:
    """
    Manages hierarchical sheets in KiCad schematics.

    This class provides functionality to:
    - Create and manage sheets
    - Add/remove sheet pins
    - Load sheet contents
    - Validate sheet hierarchy
    """

    def __init__(self, schematic: Schematic, project_path: Optional[Path] = None):
        """
        Initialize sheet manager.

        Args:
            schematic: The main schematic
            project_path: Path to the project directory
        """
        self.schematic = schematic
        self.project_path = project_path or Path.cwd()
        self.sheets: Dict[str, SheetInfo] = {}
        self._parser = SExpressionParser()

        # Index existing sheets
        self._index_sheets()

    def _index_sheets(self):
        """Index all existing sheets in the schematic."""
        for sheet in self.schematic.sheets:
            self.sheets[sheet.uuid] = SheetInfo(sheet=sheet)

    def add_sheet(
        self,
        name: str,
        filename: str,
        position: Tuple[float, float],
        size: Tuple[float, float],
    ) -> Sheet:
        """
        Add a new sheet to the schematic.

        Args:
            name: Sheet name
            filename: Filename for the sheet schematic
            position: Position (x, y) in mm
            size: Size (width, height) in mm

        Returns:
            The created sheet
        """
        # Validate filename
        if not self._validate_filename(filename):
            raise ValueError(f"Invalid sheet filename: {filename}")

        # Create sheet
        sheet = Sheet(
            name=name,
            filename=filename,
            position=Point(position[0], position[1]),
            size=size,
            uuid=str(uuid.uuid4()),
        )

        # Add to schematic
        self.schematic.sheets.append(sheet)

        # Add to index
        self.sheets[sheet.uuid] = SheetInfo(sheet=sheet)

        logger.info(f"Added sheet '{name}' at position {position}")

        return sheet

    def remove_sheet(self, sheet_uuid: str) -> bool:
        """
        Remove a sheet from the schematic.

        Args:
            sheet_uuid: UUID of the sheet to remove

        Returns:
            True if removed, False if not found
        """
        if sheet_uuid not in self.sheets:
            return False

        # Remove from schematic
        self.schematic.sheets = [
            s for s in self.schematic.sheets if s.uuid != sheet_uuid
        ]

        # Remove from index
        del self.sheets[sheet_uuid]

        logger.info(f"Removed sheet {sheet_uuid}")

        return True

    def update_sheet(self, sheet_uuid: str, **kwargs) -> bool:
        """
        Update sheet properties.

        Args:
            sheet_uuid: UUID of the sheet to update
            **kwargs: Properties to update (name, filename, position, size)

        Returns:
            True if updated, False if not found
        """
        if sheet_uuid not in self.sheets:
            return False

        sheet = self.sheets[sheet_uuid].sheet

        # Update properties
        if "name" in kwargs:
            sheet.name = kwargs["name"]
        if "filename" in kwargs:
            if not self._validate_filename(kwargs["filename"]):
                raise ValueError(f"Invalid filename: {kwargs['filename']}")
            sheet.filename = kwargs["filename"]
        if "position" in kwargs:
            pos = kwargs["position"]
            sheet.position = Point(pos[0], pos[1]) if isinstance(pos, tuple) else pos
        if "size" in kwargs:
            sheet.size = kwargs["size"]

        logger.info(f"Updated sheet {sheet_uuid}")

        return True

    def add_sheet_pin(
        self, sheet_uuid: str, name: str, pin_type: str, side: str
    ) -> Optional[SheetPin]:
        """
        Add a pin to a sheet.

        Args:
            sheet_uuid: UUID of the sheet
            name: Pin name
            pin_type: Pin type ("input", "output", "bidirectional", "tri_state", "passive")
            side: Side of sheet ("left", "right", "top", "bottom")

        Returns:
            The created sheet pin, or None if sheet not found
        """
        if sheet_uuid not in self.sheets:
            return None

        sheet = self.sheets[sheet_uuid].sheet

        # Calculate pin position
        position = self._calculate_pin_position(sheet, side, len(sheet.pins))

        # Create pin
        pin = SheetPin(
            name=name,
            position=position,
            orientation=self._get_pin_orientation(side),
            shape=pin_type,
            uuid=str(uuid.uuid4()),
        )

        # Add to sheet
        sheet.pins.append(pin)

        logger.info(f"Added pin '{name}' to sheet {sheet_uuid}")

        return pin

    def remove_sheet_pin(self, sheet_uuid: str, pin_name: str) -> bool:
        """
        Remove a pin from a sheet.

        Args:
            sheet_uuid: UUID of the sheet
            pin_name: Name of the pin to remove

        Returns:
            True if removed, False if not found
        """
        if sheet_uuid not in self.sheets:
            return False

        sheet = self.sheets[sheet_uuid].sheet

        # Find and remove pin
        original_count = len(sheet.pins)
        sheet.pins = [p for p in sheet.pins if p.name != pin_name]

        if len(sheet.pins) < original_count:
            logger.info(f"Removed pin '{pin_name}' from sheet {sheet_uuid}")
            # Recalculate pin positions
            self._recalculate_pin_positions(sheet)
            return True

        return False

    def get_sheet_contents(self, sheet_uuid: str) -> Optional[Schematic]:
        """
        Load the contents of a sheet.

        Args:
            sheet_uuid: UUID of the sheet

        Returns:
            Schematic object for the sheet, or None if not found
        """
        if sheet_uuid not in self.sheets:
            return None

        sheet_info = self.sheets[sheet_uuid]

        # Check cache
        if sheet_info.schematic:
            return sheet_info.schematic

        # Load from file
        sheet = sheet_info.sheet
        sheet_path = self._resolve_sheet_path(sheet.filename)

        if not sheet_path.exists():
            logger.warning(f"Sheet file not found: {sheet_path}")
            return None

        try:
            # Parse sheet schematic
            sheet_schematic = self._parser.parse_file(sheet_path)
            sheet_info.schematic = sheet_schematic
            return sheet_schematic

        except Exception as e:
            logger.error(f"Error loading sheet {sheet.filename}: {e}")
            return None

    def create_sheet_from_components(
        self,
        components: List[SchematicSymbol],
        name: str,
        filename: Optional[str] = None,
    ) -> Sheet:
        """
        Create a new sheet containing the specified components.

        Args:
            components: Components to move to the sheet
            name: Name for the new sheet
            filename: Optional filename (auto-generated if not provided)

        Returns:
            The created sheet
        """
        # Generate filename if not provided
        if not filename:
            filename = f"{name.lower().replace(' ', '_')}.kicad_sch"

        # Calculate sheet size based on components
        size = self._calculate_sheet_size(components)

        # Find position for new sheet
        position = self._find_sheet_position()

        # Create sheet
        sheet = self.add_sheet(name, filename, position, size)

        # Create sheet schematic
        sheet_schematic = Schematic(
            version=self.schematic.version,
            generator=self.schematic.generator,
            title=name,
        )

        # Move components to sheet schematic
        for component in components:
            # Remove from main schematic
            self.schematic.components.remove(component)
            # Add to sheet schematic
            sheet_schematic.add_component(component)

        # Save sheet schematic
        sheet_path = self._resolve_sheet_path(filename)
        self._parser.write_file(
            self._parser.from_schematic(sheet_schematic), sheet_path
        )

        # Cache the schematic
        self.sheets[sheet.uuid].schematic = sheet_schematic

        logger.info(f"Created sheet '{name}' with {len(components)} components")

        return sheet

    def get_sheet_by_name(self, name: str) -> Optional[Sheet]:
        """Find a sheet by name."""
        for sheet_info in self.sheets.values():
            if sheet_info.sheet.name == name:
                return sheet_info.sheet
        return None

    def get_sheet_hierarchy(self) -> Dict[str, List[str]]:
        """
        Get the sheet hierarchy.

        Returns:
            Dictionary mapping sheet UUIDs to list of child sheet UUIDs
        """
        hierarchy = {}

        for sheet_uuid, sheet_info in self.sheets.items():
            hierarchy[sheet_uuid] = []

            # Load sheet contents
            sheet_schematic = self.get_sheet_contents(sheet_uuid)
            if sheet_schematic:
                # Find child sheets
                for child_sheet in sheet_schematic.sheets:
                    hierarchy[sheet_uuid].append(child_sheet.uuid)

        return hierarchy

    def validate_hierarchy(self) -> List[str]:
        """
        Validate the sheet hierarchy for issues.

        Returns:
            List of validation issues
        """
        issues = []

        # Check for missing files
        for sheet_uuid, sheet_info in self.sheets.items():
            sheet = sheet_info.sheet
            sheet_path = self._resolve_sheet_path(sheet.filename)

            if not sheet_path.exists():
                issues.append(f"Missing sheet file: {sheet.filename}")

        # Check for circular references
        hierarchy = self.get_sheet_hierarchy()
        circular = self._find_circular_references(hierarchy)
        for cycle in circular:
            issues.append(f"Circular reference: {' -> '.join(cycle)}")

        # Check for duplicate sheet names
        names = {}
        for sheet_info in self.sheets.values():
            name = sheet_info.sheet.name
            if name in names:
                issues.append(f"Duplicate sheet name: {name}")
            names[name] = True

        return issues

    def _validate_filename(self, filename: str) -> bool:
        """Validate sheet filename."""
        # Must end with .kicad_sch
        if not filename.endswith(".kicad_sch"):
            return False

        # No path separators (sheets must be in project directory)
        if "/" in filename or "\\" in filename:
            return False

        # Valid filename characters
        import re

        if not re.match(r"^[a-zA-Z0-9_\-\.]+$", filename):
            return False

        return True

    def _resolve_sheet_path(self, filename: str) -> Path:
        """Resolve sheet filename to full path."""
        return self.project_path / filename

    def _calculate_pin_position(self, sheet: Sheet, side: str, index: int) -> Point:
        """Calculate position for a sheet pin."""
        # Pin spacing
        spacing = 2.54  # Standard grid
        margin = 5.0  # Margin from corners

        if side == "left":
            x = sheet.position.x
            y = sheet.position.y + margin + (index * spacing)
        elif side == "right":
            x = sheet.position.x + sheet.size[0]
            y = sheet.position.y + margin + (index * spacing)
        elif side == "top":
            x = sheet.position.x + margin + (index * spacing)
            y = sheet.position.y
        else:  # bottom
            x = sheet.position.x + margin + (index * spacing)
            y = sheet.position.y + sheet.size[1]

        return Point(x, y)

    def _get_pin_orientation(self, side: str) -> int:
        """Get pin orientation based on side."""
        orientations = {"left": 0, "right": 180, "top": 90, "bottom": 270}
        return orientations.get(side, 0)

    def _recalculate_pin_positions(self, sheet: Sheet):
        """Recalculate positions for all pins on a sheet."""
        # Group pins by side
        pins_by_side = {"left": [], "right": [], "top": [], "bottom": []}

        for pin in sheet.pins:
            # Determine side based on orientation
            if pin.orientation == 0:
                pins_by_side["left"].append(pin)
            elif pin.orientation == 180:
                pins_by_side["right"].append(pin)
            elif pin.orientation == 90:
                pins_by_side["top"].append(pin)
            else:
                pins_by_side["bottom"].append(pin)

        # Recalculate positions
        for side, side_pins in pins_by_side.items():
            for i, pin in enumerate(side_pins):
                pin.position = self._calculate_pin_position(sheet, side, i)

    def _calculate_sheet_size(
        self, components: List[SchematicSymbol]
    ) -> Tuple[float, float]:
        """Calculate appropriate sheet size for components."""
        if not components:
            return (100.0, 100.0)  # Default size

        # Find bounding box of components
        min_x = min(c.position.x for c in components)
        max_x = max(c.position.x for c in components)
        min_y = min(c.position.y for c in components)
        max_y = max(c.position.y for c in components)

        # Add margin
        margin = 25.0
        width = max_x - min_x + 2 * margin
        height = max_y - min_y + 2 * margin

        # Round to grid
        grid = 25.4  # 1 inch
        width = round(width / grid) * grid
        height = round(height / grid) * grid

        # Minimum size
        width = max(width, 100.0)
        height = max(height, 100.0)

        return (width, height)

    def _find_sheet_position(self) -> Tuple[float, float]:
        """Find a good position for a new sheet."""
        if not self.schematic.sheets:
            return (50.0, 50.0)  # Default position

        # Find rightmost sheet
        max_x = max(s.position.x + s.size[0] for s in self.schematic.sheets)

        # Place new sheet to the right
        margin = 25.0
        return (max_x + margin, 50.0)

    def _find_circular_references(
        self, hierarchy: Dict[str, List[str]]
    ) -> List[List[str]]:
        """Find circular references in hierarchy."""
        cycles = []

        def dfs(node: str, path: List[str], visited: Set[str]):
            if node in path:
                # Found cycle
                cycle_start = path.index(node)
                cycle = path[cycle_start:] + [node]
                cycles.append(cycle)
                return

            if node in visited:
                return

            visited.add(node)
            path.append(node)

            for child in hierarchy.get(node, []):
                dfs(child, path[:], visited)

        visited = set()
        for sheet_uuid in hierarchy:
            if sheet_uuid not in visited:
                dfs(sheet_uuid, [], visited)

        return cycles
