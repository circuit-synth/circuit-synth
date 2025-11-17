"""
Component management for KiCad schematics.
Provides add, remove, update, and search operations for schematic components.
"""

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

import kicad_sch_api as ksa
from kicad_sch_api.core.components import Component, ComponentCollection
from kicad_sch_api.core.types import Point, Schematic, SchematicSymbol

from ..core.symbol_cache import get_symbol_cache
from .instance_utils import add_symbol_instance

# Debug logging for kicad-sch-api version
logger_init = logging.getLogger(__name__)
logger_init.info(f"🔍 IMPORT CHECK - kicad-sch-api version: {ksa.__version__}")
logger_init.info(f"🔍 IMPORT CHECK - ComponentCollection has _add_to_indexes: {hasattr(ComponentCollection, '_add_to_indexes')}")
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

    def __init__(self, schematic: Schematic, sheet_size: Tuple[float, float] = None, project_name: Optional[str] = None):
        """
        Initialize component manager with a schematic.

        Args:
            schematic: The schematic to manage
            sheet_size: (width, height) of the sheet in mm (default A4: 210x297mm)
            project_name: Name of the KiCad project (used for instance data if schematic not yet saved)
        """
        self.schematic = schematic
        self.project_name = project_name
        self.placement_engine = PlacementEngine(schematic, sheet_size=sheet_size)
        self._component_index = self._build_component_index()

    def _build_component_index(self) -> Dict[str, SchematicSymbol]:
        """Build an index of components by reference and unit for fast lookup."""
        index = {}
        for comp in self.schematic.components:
            unit = getattr(comp, "unit", 1)  # Default to unit 1 if not set
            component_key = f"{comp.reference}_unit{unit}"
            index[component_key] = comp
        return index

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
        snap_to_grid: bool = True,
        unit: int = 1,
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
            footprint: Component footprint
            snap_to_grid: If True, snap position to grid. If False, use exact position.
            unit: Unit number for multi-unit components (1-based, default 1)
            **properties: Additional component properties

        Returns:
            The created component, or None if creation failed
        """
        # Validate library ID
        symbol_cache = get_symbol_cache()
        symbol_def = symbol_cache.get_symbol(library_id)
        if not symbol_def:
            logger.error(f"Unknown library ID: {library_id}")
            return None

        # Generate reference if not provided
        if not reference:
            reference = self._generate_reference(symbol_def.reference_prefix)

        # Check for duplicate reference - allow same reference with different units
        # Build a unique key combining reference and unit for multi-unit components
        component_key = f"{reference}_unit{unit}"
        if component_key in self._component_index:
            logger.error(
                f"Component with reference {reference} unit {unit} already exists"
            )
            return None

        # Log properties being added
        logger.debug(f"Adding component with {len(properties)} properties")
        if properties:
            logger.debug(f"Property keys: {list(properties.keys())}")

        # Check for DNP in properties to set in_bom/on_board flags
        dnp_value = False
        if "DNP" in properties:
            dnp_str = properties["DNP"]
            dnp_value = (
                dnp_str.lower() in ("true", "yes", "1")
                if isinstance(dnp_str, str)
                else bool(dnp_str)
            )
            logger.debug(f"DNP flag detected: {dnp_value}")

        # Create component first (needed for dynamic sizing)
        component = SchematicSymbol(
            uuid=self._generate_uuid(),
            lib_id=library_id,
            position=Point(0, 0),  # Temporary position
            reference=reference,
            value=value or "",
            footprint=footprint,
            unit=unit,  # Set the unit number
            properties=properties,
            pins=symbol_def.pins.copy() if symbol_def.pins else [],
            in_bom=not dnp_value,  # If DNP, exclude from BOM
            on_board=not dnp_value,  # If DNP, exclude from board
        )

        logger.debug(
            f"Created SchematicSymbol with {len(component.properties)} properties"
        )

        # Determine position (now with component for dynamic sizing)
        if position is None:
            position = self.placement_engine.find_position(
                placement_strategy,
                component_size=(20.0, 20.0),  # Default size fallback
                component=component,  # Pass component for dynamic sizing
            )
        else:
            # Ensure grid alignment (unless snap_to_grid is False, e.g., for power symbols)
            if snap_to_grid:
                position = self._snap_to_grid(position)

        # Update component position
        component.position = Point(position[0], position[1])

        # Add instance using centralized utility with proper hierarchy
        from .instance_utils import add_symbol_instance, get_project_hierarchy_path

        schematic_path = getattr(self.schematic, "file_path", "")

        if schematic_path:
            project_name, hierarchical_path = get_project_hierarchy_path(schematic_path)
        else:
            # Use project_name from constructor, fallback to schematic attr, final fallback to "circuit"
            project_name = self.project_name or getattr(self.schematic, "project_name", "circuit")
            hierarchical_path = "/"

        add_symbol_instance(component, project_name, hierarchical_path)

        # Add to schematic - need to handle both old and new (kicad-sch-api) schematic types
        if hasattr(self.schematic, "_data"):
            # kicad-sch-api Schematic - add component to both _data and ComponentCollection
            logger.debug(f"Adding component {reference} to kicad-sch-api schematic")

            # Add to underlying S-expression data
            if 'symbol' not in self.schematic._data:
                self.schematic._data['symbol'] = []
            self.schematic._data['symbol'].append(component)

            # Also add to ComponentCollection's internal tracking using _add_item_to_collection
            if hasattr(self.schematic, "_components") and hasattr(self.schematic._components, "_add_item_to_collection"):
                comp_wrapper = Component(component, self.schematic._components)
                self.schematic._components._add_item_to_collection(comp_wrapper)
                logger.debug(f"Component added to ComponentCollection (total: {len(self.schematic._components)} items)")
            else:
                logger.debug(f"Component added to _data only (ComponentCollection not available)")
        else:
            # Fallback for older schematic types
            self.schematic.components.append(component)

        # Store in index with unique key for multi-unit support
        self._component_index[component_key] = component

        logger.debug(
            f"Added component {reference} unit {unit} ({library_id}) at {position}"
        )
        return component

    def remove_component(self, reference: str, uuid: Optional[str] = None) -> bool:
        """
        Remove a component from the schematic by reference or UUID.

        Args:
            reference: Component reference to remove
            uuid: Component UUID (optional, used if reference is ambiguous)

        Returns:
            True if component was removed, False if not found

        Note:
            Prefer UUID over reference when removing, as references are not guaranteed
            to be unique in all scenarios. The reference parameter is retained for
            backwards compatibility.
        """
        # Try UUID first if provided (more reliable)
        if uuid:
            if hasattr(self.schematic.components, "remove_by_uuid"):
                # Use new API if available (kicad-sch-api 0.4.1+)
                result = self.schematic.components.remove_by_uuid(uuid)
                if result:
                    # Also remove from our index - need to find the correct key
                    component_key = self._get_component_key(reference)
                    if component_key:
                        del self._component_index[component_key]
                    logger.info(f"Removed component {reference} by UUID {uuid}")
                    return True
            else:
                logger.warning(
                    f"remove_by_uuid not available, falling back to reference"
                )

        # Fall back to reference-based removal
        # Find the component using correct key format (with unit suffix)
        component_key = self._get_component_key(reference)
        if component_key is None:
            logger.warning(f"Component {reference} not found")
            return False

        component = self._component_index[component_key]

        # Use proper kicad-sch-api remove() method by reference
        # (Fixed in kicad-sch-api 0.4.1+: https://github.com/circuit-synth/kicad-sch-api/pull/55)
        result = self.schematic.components.remove(reference)

        if not result:
            logger.warning(
                f"Failed to remove component {reference} from ComponentCollection"
            )
            return False

        del self._component_index[component_key]

        logger.info(f"Removed component {reference}")
        return True

    def rename_component(self, old_ref: str, new_ref: str) -> bool:
        """
        Rename a component's reference designator.

        This method updates the component's reference and maintains the internal
        index consistency. It's used during bidirectional sync when a component
        reference has changed in the Python code.

        Args:
            old_ref: Current reference (e.g., "R1")
            new_ref: New reference (e.g., "R2")

        Returns:
            True if renamed successfully, False otherwise
        """
        # Check if old component exists
        old_key = self._get_component_key(old_ref)
        if old_key is None:
            logger.error(f"Cannot rename: component {old_ref} not found")
            return False

        # Check if new reference already exists
        new_key = self._get_component_key(new_ref)
        if new_key is not None:
            logger.error(f"Cannot rename to {new_ref}: reference already exists")
            return False

        # Get the component
        component = self._component_index[old_key]

        # Update the reference in the component object
        component.reference = new_ref

        # Update the internal index - construct new key with same unit
        unit = getattr(component, "unit", 1)
        new_index_key = f"{new_ref}_unit{unit}"
        self._component_index[new_index_key] = component
        del self._component_index[old_key]

        logger.info(f"Renamed component {old_ref} → {new_ref}")
        return True

    def update_component(
        self,
        reference: str,
        value: Optional[str] = None,
        position: Optional[Tuple[float, float]] = None,
        rotation: Optional[float] = None,
        footprint: Optional[str] = None,
        lib_id: Optional[str] = None,
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
            lib_id: New library symbol (if provided) - e.g., "Device:R" or "Device:C"
            **properties: Additional properties to update

        Returns:
            True if component was updated, False if not found
        """
        component_key = self._get_component_key(reference)
        if component_key is None:
            logger.warning(f"Component {reference} not found")
            return False

        component = self._component_index[component_key]

        # Update value
        if value is not None:
            component.value = value

        # Update footprint
        if footprint is not None:
            component.footprint = footprint

        # Update lib_id (symbol type) - WORKAROUND: use _data because lib_id property is read-only
        if lib_id is not None:
            old_lib_id = str(component.lib_id)
            if old_lib_id != lib_id:
                logger.info(f"Updating {reference} symbol: {old_lib_id} → {lib_id}")
                # component.lib_id is read-only, but we can modify _data.lib_id
                component._data.lib_id = lib_id

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
        if (
            not hasattr(component, "instances")
            or not component.instances
            or len(component.instances) == 0
        ):
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
        # For multi-unit components, components are indexed as "{reference}_unit{n}"
        # Try unit 1 first (most common case)
        component_key = f"{reference}_unit1"
        comp = self._component_index.get(component_key)
        if comp:
            return comp

        # If not found with unit1, search for any unit with this reference
        for key, component in self._component_index.items():
            if key.startswith(f"{reference}_unit"):
                return component

        # Not found
        return None

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
        component_key = self._get_component_key(reference)
        if component_key is None:
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
        component_key = self._get_component_key(reference)
        if component_key is None:
            logger.warning(f"Component {reference} not found")
            return None

        original = self._component_index[component_key]

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

    def _get_component_key(self, reference: str) -> Optional[str]:
        """
        Get the internal index key for a component reference.

        The index stores components with keys like "R1_unit1", "R1_unit2", etc.
        This method handles the lookup correctly by trying unit 1 first, then
        searching for any unit with this reference.

        Args:
            reference: Component reference (e.g., "R1")

        Returns:
            The internal key (e.g., "R1_unit1") if found, None otherwise
        """
        # Try unit 1 first (most common case)
        component_key = f"{reference}_unit1"
        if component_key in self._component_index:
            return component_key

        # If not found with unit1, search for any unit with this reference
        for key in self._component_index:
            if key.startswith(f"{reference}_unit"):
                return key

        # Not found
        return None

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
            # Index keys are like "R1_unit1", extract the number part
            if ref.startswith(prefix):
                try:
                    # Extract number before "_unit" suffix
                    num_str = ref[len(prefix) :].split('_')[0]
                    num = int(num_str)
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
        component_key = self._get_component_key(reference)
        if component_key is None:
            return None
        return self._component_index.get(component_key)

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
