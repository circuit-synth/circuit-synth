"""
Component management for KiCad schematics.
Provides add, remove, update, and search operations for schematic components.
"""

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from ..core.symbol_cache import get_symbol_cache
from ..core.types import Point, Schematic, SchematicSymbol
from .instance_utils import add_symbol_instance
from .placement import PlacementEngine, PlacementStrategy

logger = logging.getLogger(__name__)

# Performance debugging
import time

try:
    from ..sch_gen.debug_performance import log_symbol_lookup, timed_operation

    PERF_DEBUG = True
except ImportError:
    PERF_DEBUG = False
    from contextlib import contextmanager

    @contextmanager
    def timed_operation(*args, **kwargs):
        yield


class ComponentManager:
    """
    Manages components in a KiCad schematic.
    Provides high-level operations for adding, removing, updating, and searching components.
    """

    def __init__(self, schematic: Schematic, sheet_size: Tuple[float, float] = None):
        """
        Initialize component manager with a schematic.

        Args:
            schematic: The schematic to manage
            sheet_size: (width, height) of the sheet in mm (default A4: 210x297mm)
        """
        self.schematic = schematic
        self.placement_engine = PlacementEngine(schematic, sheet_size=sheet_size)
        self._component_index = self._build_component_index()

    def _build_component_index(self) -> Dict[str, SchematicSymbol]:
        """Build an index of components by reference for fast lookup."""
        return {comp.reference: comp for comp in self.schematic.components}

    def _generate_uuid(self) -> str:
        """Generate a new UUID for a component."""
        return str(uuid.uuid4())

    def add_component(
        self,
        library_id: str,
        reference: Optional[str] = None,
        value: Optional[str] = None,
        position: Optional[Tuple[float, float]] = None,
        placement_strategy: PlacementStrategy = PlacementStrategy.AUTO,
        footprint: Optional[str] = None,
        **properties,
    ) -> Optional[SchematicSymbol]:
        """
        Add a new component to the schematic.

        Args:
            library_id: Library identifier (e.g., "Device:R")
            reference: Component reference (e.g., "R1"). Auto-generated if None.
            value: Component value (e.g., "10k")
            position: (x, y) position in mm. Auto-placed if None.
            placement_strategy: Strategy for automatic placement
            **properties: Additional component properties

        Returns:
            The created component, or None if creation failed
        """
        # Validate library ID
        symbol_cache = get_symbol_cache()
        # Time symbol cache lookup
        sym_start = time.perf_counter()
        symbol_def = symbol_cache.get_symbol(library_id)
        sym_time = (time.perf_counter() - sym_start) * 1000
        if PERF_DEBUG and sym_time > 10:
            logger.warning(f"🐌 SLOW: get_symbol({library_id}) took {sym_time:.2f}ms")
            if sym_time > 50:
                logger.error(f"🔴 VERY SLOW: {library_id} - investigating...")
        if not symbol_def:
            logger.error(f"Unknown library ID: {library_id}")
            return None

        # Generate reference if not provided
        if not reference:
            reference = self._generate_reference(symbol_def.reference_prefix)

        # Check for duplicate reference
        if reference in self._component_index:
            logger.error(f"Component with reference {reference} already exists")
            return None

        # Create component first (needed for dynamic sizing)
        component = SchematicSymbol(
            uuid=self._generate_uuid(),
            lib_id=library_id,
            position=Point(0, 0),  # Temporary position
            reference=reference,
            value=value or "",
            footprint=footprint,
            properties=properties,
            pins=symbol_def.pins.copy() if symbol_def.pins else [],
            in_bom=True,  # Ensure component is included in BOM
            on_board=True,  # Ensure component is included on board
        )

        # Determine position (now with component for dynamic sizing)
        if position is None:
            position = self.placement_engine.find_position(
                placement_strategy,
                component_size=(20.0, 20.0),  # Default size fallback
                component=component,  # Pass component for dynamic sizing
            )
        else:
            # Ensure grid alignment
            position = self._snap_to_grid(position)

        # Update component position
        component.position = Point(position[0], position[1])

        # Add instance using centralized utility with proper hierarchy
        from .instance_utils import add_symbol_instance, get_project_hierarchy_path

        schematic_path = getattr(self.schematic, "file_path", "")
        if schematic_path:
            project_name, hierarchical_path = get_project_hierarchy_path(schematic_path)
        else:
            project_name = getattr(self.schematic, "project_name", "circuit")
            hierarchical_path = "/"
        add_symbol_instance(component, project_name, hierarchical_path)

        # Add to schematic
        self.schematic.components.append(component)
        self._component_index[reference] = component

        logger.debug(f"Added component {reference} ({library_id}) at {position}")
        return component

    def remove_component(self, reference: str) -> bool:
        """
        Remove a component from the schematic.

        Args:
            reference: Component reference to remove

        Returns:
            True if component was removed, False if not found
        """
        if reference not in self._component_index:
            logger.warning(f"Component {reference} not found")
            return False

        component = self._component_index[reference]
        self.schematic.components.remove(component)
        del self._component_index[reference]

        logger.debug(f"Removed component {reference}")
        return True

    def update_component(
        self,
        reference: str,
        value: Optional[str] = None,
        position: Optional[Tuple[float, float]] = None,
        rotation: Optional[float] = None,
        footprint: Optional[str] = None,
        **properties,
    ) -> bool:
        """
        Update properties of an existing component.

        Args:
            reference: Component reference to update
            value: New value (if provided)
            position: New position (if provided)
            rotation: New rotation in degrees (if provided)
            footprint: New footprint (if provided)
            **properties: Additional properties to update

        Returns:
            True if component was updated, False if not found
        """
        if reference not in self._component_index:
            logger.warning(f"Component {reference} not found")
            return False

        component = self._component_index[reference]

        # Update value
        if value is not None:
            component.value = value

        # Update footprint
        if footprint is not None:
            component.footprint = footprint

        # Update position
        if position is not None:
            position = self._snap_to_grid(position)
            component.position = Point(position[0], position[1])

        # Update rotation
        if rotation is not None:
            component.rotation = rotation

        # Ensure component is properly included in BOM and board
        # This fixes the "?" symbol issue caused by in_bom=no or on_board=no
        component.in_bom = True
        component.on_board = True

        # Ensure component has proper instance information for reference display
        if not component.instances or len(component.instances) == 0:
            from .instance_utils import add_symbol_instance, get_project_hierarchy_path

            schematic_path = getattr(self.schematic, "file_path", "")
            if schematic_path:
                project_name, hierarchical_path = get_project_hierarchy_path(
                    schematic_path
                )
            else:
                project_name = getattr(self.schematic, "project_name", "circuit")
                hierarchical_path = "/"
            add_symbol_instance(component, project_name, hierarchical_path)
            logger.debug(
                f"Added instance information to component {component.reference}"
            )

        # Update additional properties
        component.properties.update(properties)

        logger.debug(
            f"Updated component {reference} - ensuring in_bom=True, on_board=True"
        )
        return True

    def find_component(self, reference: str) -> Optional[SchematicSymbol]:
        """
        Find a component by reference.

        Args:
            reference: Component reference

        Returns:
            The component if found, None otherwise
        """
        return self._component_index.get(reference)

    def list_components(self) -> List[SchematicSymbol]:
        """
        Get all components in the schematic.

        Returns:
            List of all components
        """
        return list(self.schematic.components)

    def find_components_by_value(self, value_pattern: str) -> List[SchematicSymbol]:
        """
        Find components by value pattern.

        Args:
            value_pattern: Value to search for (exact match)

        Returns:
            List of matching components
        """
        return [
            comp for comp in self.schematic.components if comp.value == value_pattern
        ]

    def find_components_by_library(self, library_pattern: str) -> List[SchematicSymbol]:
        """
        Find components by library ID pattern.

        Args:
            library_pattern: Library ID to search for (exact match)

        Returns:
            List of matching components
        """
        return [
            comp for comp in self.schematic.components if comp.lib_id == library_pattern
        ]

    def move_component(
        self,
        reference: str,
        new_position: Tuple[float, float],
        check_collision: bool = True,
    ) -> bool:
        """
        Move a component to a new position.

        Args:
            reference: Component reference
            new_position: New (x, y) position in mm
            check_collision: Whether to check for collisions

        Returns:
            True if moved successfully, False otherwise
        """
        if reference not in self._component_index:
            logger.warning(f"Component {reference} not found")
            return False

        new_position = self._snap_to_grid(new_position)

        if check_collision:
            # Check if position is occupied
            for comp in self.schematic.components:
                if comp.reference != reference:
                    if (
                        abs(comp.position.x - new_position[0]) < 5.0
                        and abs(comp.position.y - new_position[1]) < 5.0
                    ):
                        logger.warning(
                            f"Position {new_position} would collide with {comp.reference}"
                        )
                        return False

        return self.update_component(reference, position=new_position)

    def clone_component(
        self,
        reference: str,
        new_reference: Optional[str] = None,
        offset: Tuple[float, float] = (10.0, 0.0),
    ) -> Optional[SchematicSymbol]:
        """
        Clone an existing component.

        Args:
            reference: Reference of component to clone
            new_reference: Reference for the clone (auto-generated if None)
            offset: Position offset from original component

        Returns:
            The cloned component, or None if cloning failed
        """
        if reference not in self._component_index:
            logger.warning(f"Component {reference} not found")
            return None

        original = self._component_index[reference]

        # Generate new reference if not provided
        if not new_reference:
            # Extract prefix from original reference
            prefix = "".join(c for c in original.reference if not c.isdigit())
            new_reference = self._generate_reference(prefix)

        # Calculate new position
        new_position = (
            original.position.x + offset[0],
            original.position.y + offset[1],
        )

        # Create clone
        clone = self.add_component(
            library_id=original.lib_id,
            reference=new_reference,
            value=original.value,
            position=new_position,
            **original.properties,
        )

        if clone:
            clone.rotation = original.rotation
            logger.debug(f"Cloned {reference} to {new_reference}")

        return clone

    def validate_schematic(self) -> Tuple[bool, List[str]]:
        """
        Validate the schematic for common issues.

        Returns:
            Tuple of (is_valid, list_of_messages)
        """
        messages = []
        is_valid = True

        # Check for duplicate references
        references = {}
        for comp in self.schematic.components:
            if comp.reference in references:
                messages.append(f"Duplicate reference: {comp.reference}")
                is_valid = False
            references[comp.reference] = comp

        # Check for components without values
        for comp in self.schematic.components:
            if not comp.value:
                messages.append(f"Component {comp.reference} has no value")

        # Check for overlapping components
        for i, comp1 in enumerate(self.schematic.components):
            for comp2 in self.schematic.components[i + 1 :]:
                if (
                    abs(comp1.position.x - comp2.position.x) < 5.0
                    and abs(comp1.position.y - comp2.position.y) < 5.0
                ):
                    messages.append(
                        f"Components {comp1.reference} and {comp2.reference} may overlap"
                    )

        return is_valid, messages

    def _generate_reference(self, prefix: str) -> str:
        """
        Generate a unique reference with the given prefix.

        Args:
            prefix: Reference prefix (e.g., "R", "C", "U")

        Returns:
            Unique reference (e.g., "R1", "R2", etc.)
        """
        # Find all existing references with this prefix
        existing_numbers = []
        for ref in self._component_index:
            if ref.startswith(prefix):
                try:
                    num = int(ref[len(prefix) :])
                    existing_numbers.append(num)
                except ValueError:
                    pass

        # Find the next available number
        next_num = 1
        if existing_numbers:
            next_num = max(existing_numbers) + 1

        return f"{prefix}{next_num}"

    def get_component(self, reference: str) -> Optional[SchematicSymbol]:
        """
        Get a component by reference.

        Args:
            reference: Component reference (e.g., "R1")

        Returns:
            Component if found, None otherwise
        """
        return self._component_index.get(reference)

    def _snap_to_grid(
        self, position: Tuple[float, float], grid_size: float = 2.54
    ) -> Tuple[float, float]:
        """
        Snap position to grid.

        Args:
            position: (x, y) position in mm
            grid_size: Grid size in mm (default 2.54mm = 0.1 inch)

        Returns:
            Grid-aligned position
        """
        x = round(position[0] / grid_size) * grid_size
        y = round(position[1] / grid_size) * grid_size
        return (x, y)

    def get_bounding_box(self) -> Optional[Tuple[Point, Point]]:
        """
        Get the bounding box of all components.

        Returns:
            (min_point, max_point) or None if no components
        """
        if not self.schematic.components:
            return None

        min_x = min(comp.position.x for comp in self.schematic.components)
        min_y = min(comp.position.y for comp in self.schematic.components)
        max_x = max(comp.position.x for comp in self.schematic.components)
        max_y = max(comp.position.y for comp in self.schematic.components)

        # Add some margin for component size
        margin = 10.0
        return (
            Point(min_x - margin, min_y - margin),
            Point(max_x + margin, max_y + margin),
        )
