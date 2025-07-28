"""
Additional component operations for the KiCad Schematic API.

This module implements the missing component manipulation methods:
- move_component
- remove_component
- clone_component
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, Optional, Tuple

from ..sch_editor.schematic_reader import Schematic, SchematicSymbol
from .exceptions import ComponentNotFoundError, PlacementError

logger = logging.getLogger(__name__)


@dataclass
class ComponentOperations:
    """Extended operations for component manipulation."""

    def __init__(self, schematic: Schematic, component_manager):
        """
        Initialize with schematic and component manager reference.

        Args:
            schematic: The Schematic object
            component_manager: Reference to the ComponentManager instance
        """
        self.schematic = schematic
        self.manager = component_manager

    def move_component(
        self,
        reference: str,
        new_position: Tuple[float, float],
        check_collision: bool = True,
    ) -> bool:
        """
        Move a component to a new position.

        Args:
            reference: Component reference designator
            new_position: New (x, y) position in mm
            check_collision: Whether to check for collisions

        Returns:
            True if successful, False otherwise

        Raises:
            ComponentNotFoundError: If component not found
            PlacementError: If collision detected and check_collision is True
        """
        logger.debug(f"Moving component {reference} to {new_position}")

        # Find the component
        component = self.schematic.get_component(reference)
        if not component:
            raise ComponentNotFoundError(reference)

        # Snap to grid
        snapped_pos = self.manager.placement_engine.snap_to_grid(new_position)

        # Check for collisions if requested
        if check_collision:
            # Get component size (approximate)
            size = self._estimate_component_size(component)
            collision = self.manager.placement_engine.check_collision(snapped_pos, size)
            if collision and collision != reference:
                raise PlacementError(
                    snapped_pos, f"Collision with component {collision}"
                )

        # Update position
        old_pos = component.position
        component.position = (snapped_pos[0], snapped_pos[1], component.position[2])

        logger.info(f"Moved {reference} from {old_pos} to {component.position}")
        return True

    def remove_component(self, reference: str) -> bool:
        """
        Remove a component from the schematic.

        Args:
            reference: Component reference designator

        Returns:
            True if successful, False if component not found
        """
        logger.debug(f"Removing component {reference}")

        # Find the component
        component = self.schematic.get_component(reference)
        if not component:
            logger.warning(f"Component {reference} not found for removal")
            return False

        # Remove from components list
        self.schematic.components.remove(component)

        # Remove from component index if it exists
        if hasattr(self.manager, "_component_index"):
            self.manager._component_index.pop(reference, None)

        # Remove from reference manager
        if hasattr(self.manager, "reference_manager"):
            self.manager.reference_manager.used_references.discard(reference)

        logger.info(f"Removed component {reference}")
        return True

    def clone_component(
        self,
        reference: str,
        new_reference: Optional[str] = None,
        offset: Tuple[float, float] = (25.4, 0),
        auto_increment: bool = True,
    ) -> Optional[SchematicSymbol]:
        """
        Clone an existing component.

        Args:
            reference: Reference of component to clone
            new_reference: Reference for the new component (auto-generated if None)
            offset: Position offset from original component (x, y) in mm
            auto_increment: If True and new_reference is None, increment the reference number

        Returns:
            The newly created component or None if source not found

        Raises:
            ComponentNotFoundError: If source component not found
        """
        logger.debug(f"Cloning component {reference}")

        # Find the source component
        source = self.schematic.get_component(reference)
        if not source:
            raise ComponentNotFoundError(reference)

        # Generate new reference if not provided
        if new_reference is None:
            if auto_increment:
                new_reference = self._increment_reference(reference)
            else:
                new_reference = self.manager.reference_manager.generate_reference(
                    source.lib_id
                )

        # Calculate new position
        new_x = source.position[0] + offset[0]
        new_y = source.position[1] + offset[1]
        new_position = (new_x, new_y)

        # Create the new component using the manager's add_component method
        new_component = self.manager.add_component(
            lib_id=source.lib_id,
            reference=new_reference,
            value=source.value,
            position=new_position,
            rotation=source.position[2] if len(source.position) > 2 else 0,
            properties=dict(source.properties) if source.properties else None,
            footprint=source.footprint,
            in_bom=source.in_bom,
            on_board=source.on_board,
            unit=source.unit,
        )

        if new_component:
            logger.info(
                f"Cloned {reference} as {new_reference} at position {new_position}"
            )

        return new_component

    def _estimate_component_size(
        self, component: SchematicSymbol
    ) -> Tuple[float, float]:
        """
        Estimate the size of a component for collision detection.

        Args:
            component: The component to estimate size for

        Returns:
            Estimated (width, height) in mm
        """
        # Default sizes based on component type
        if "R" in component.lib_id or "C" in component.lib_id:
            return (7.62, 2.54)  # Standard passive component
        elif "U" in component.lib_id:
            return (20.0, 15.0)  # IC package
        else:
            return (10.0, 10.0)  # Default size

    def _increment_reference(self, reference: str) -> str:
        """
        Increment a reference designator number.

        Args:
            reference: Original reference (e.g., "R1", "U10")

        Returns:
            Incremented reference (e.g., "R2", "U11")
        """
        import re

        # Extract prefix and number
        match = re.match(r"^([A-Z]+)(\d+)$", reference)
        if match:
            prefix = match.group(1)
            number = int(match.group(2))

            # Find next available number
            while True:
                number += 1
                new_ref = f"{prefix}{number}"
                if self.manager.reference_manager.is_reference_available(new_ref):
                    return new_ref

        # Fallback to auto-generation
        return self.manager.reference_manager.generate_reference("Device:R")
