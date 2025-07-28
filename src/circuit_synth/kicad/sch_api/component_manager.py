"""
Component Manager for KiCad Schematic API.

This is the core class that manages all component operations in a KiCad schematic,
including adding, removing, moving, and modifying components.
"""

import logging
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

import sexpdata

from ..kicad_symbol_cache import SymbolLibCache
from ..sch_editor.schematic_reader import Schematic, SchematicPin, SchematicSymbol
from .component_operations import ComponentOperations
from .exceptions import (
    ComponentError,
    ComponentNotFoundError,
    DuplicateReferenceError,
    InvalidLibraryError,
    InvalidPropertyError,
    PlacementError,
)
from .models import (
    CloneOptions,
    ComponentConnections,
    MoveOptions,
    MoveResult,
    PlacementInfo,
    PlacementStrategy,
    RemovalOptions,
    RemovalResult,
)
from .placement_engine import PlacementEngine
from .reference_manager import ReferenceManager

logger = logging.getLogger(__name__)


class ComponentManager:
    """
    Manages component operations in a KiCad schematic.

    This class provides a comprehensive API for manipulating components,
    including adding, removing, moving, cloning, and modifying components
    while maintaining schematic integrity.
    """

    def __init__(self, schematic: Schematic):
        """
        Initialize the ComponentManager with a schematic.

        Args:
            schematic: The Schematic object to manage
        """
        self.schematic = schematic
        self.symbol_cache = SymbolLibCache()
        self.placement_engine = PlacementEngine()
        self.reference_manager = ReferenceManager()

        # Initialize reference manager with existing components
        existing_refs = [
            comp.reference
            for comp in schematic.components
            if comp.reference and not comp.reference.endswith("?")
        ]
        self.reference_manager.add_existing_references(existing_refs)

        # Build component index for fast lookup
        self._component_index = {comp.reference: comp for comp in schematic.components}

        logger.info(
            f"Initialized ComponentManager with {len(schematic.components)} components"
        )

        # Initialize component operations
        self.operations = ComponentOperations(schematic, self)

    def add_component(
        self,
        lib_id: str,
        reference: Optional[str] = None,
        value: str = "",
        position: Optional[Tuple[float, float]] = None,
        rotation: float = 0.0,
        properties: Optional[Dict[str, str]] = None,
        footprint: Optional[str] = None,
        in_bom: bool = True,
        on_board: bool = True,
        unit: int = 1,
        mirror: Optional[str] = None,
        dnp: bool = False,
    ) -> SchematicSymbol:
        """
        Add a new component to the schematic.

        Args:
            lib_id: Library ID of the symbol (e.g., "Device:R")
            reference: Optional reference designator (auto-generated if None)
            value: Component value (e.g., "10k", "100nF")
            position: Optional (x, y) position in mm (auto-placed if None)
            rotation: Rotation angle in degrees (0, 90, 180, 270)
            properties: Additional properties as key-value pairs
            footprint: Optional footprint specification
            in_bom: Whether component appears in BOM
            on_board: Whether component is placed on board
            unit: Unit number for multi-unit symbols
            mirror: Mirror orientation ('x', 'y', or None)
            dnp: Do Not Populate flag

        Returns:
            The newly created SchematicSymbol

        Raises:
            InvalidLibraryError: If the library ID is invalid or symbol not found
            DuplicateReferenceError: If the reference already exists
            PlacementError: If the component cannot be placed at the requested position
        """
        logger.debug(
            f"Adding component: lib_id={lib_id}, reference={reference}, value={value}"
        )

        # Step 1: Validate library ID and fetch symbol data
        symbol_data = self._validate_and_fetch_symbol(lib_id)

        # Step 2: Generate or validate reference
        if reference is None:
            reference = self.reference_manager.generate_reference(lib_id)
        else:
            # Validate user-provided reference
            if not self.reference_manager.is_reference_available(reference):
                raise DuplicateReferenceError(reference)
            self.reference_manager.used_references.add(reference)

        # Step 3: Calculate position
        if position is None:
            position = self.placement_engine.find_next_position(
                self.schematic, symbol_data
            )
        else:
            # Validate and snap position
            position = self.placement_engine.snap_to_grid(position)
            # Check for collisions
            size = self._get_symbol_size(symbol_data)
            collision = self.placement_engine.check_collision(position, size)
            if collision:
                raise PlacementError(position, f"Collision with component {collision}")

        # Step 4: Create component instance
        component = self._create_component_instance(
            lib_id=lib_id,
            reference=reference,
            value=value,
            position=position,
            rotation=rotation,
            symbol_data=symbol_data,
            unit=unit,
            mirror=mirror,
            dnp=dnp,
        )

        # Step 5: Set properties
        self._set_component_properties(
            component, properties, footprint, in_bom, on_board
        )

        # Step 6: Create pins from library data
        self._create_pins(component, symbol_data, unit)

        # Step 7: Add to schematic
        self.schematic.components.append(component)
        self._component_index[reference] = component

        # Step 8: Update placement engine state
        self.placement_engine._update_state(self.schematic)

        logger.info(f"Added component {reference} at position {position}")
        return component

    def _validate_and_fetch_symbol(self, lib_id: str) -> Dict[str, Any]:
        """
        Validate library ID and fetch symbol data.

        Args:
            lib_id: The library ID to validate

        Returns:
            Symbol data dictionary

        Raises:
            InvalidLibraryError: If the symbol cannot be found
        """
        try:
            # Validate format
            if ":" not in lib_id:
                raise ValueError(f"Invalid lib_id format: {lib_id}")

            lib_name, symbol_name = lib_id.split(":", 1)

            # Try to get symbol data
            try:
                symbol_data = self.symbol_cache.get_symbol_data(lib_id)
            except (KeyError, FileNotFoundError) as e:
                # Try alternative: search by symbol name only
                logger.debug(f"Failed to find {lib_id}, searching for {symbol_name}")
                try:
                    symbol_data = self.symbol_cache.get_symbol_data_by_name(symbol_name)
                    logger.info(f"Found symbol {symbol_name} in alternative library")
                except KeyError:
                    raise InvalidLibraryError(lib_id, str(e))

            # Validate symbol structure
            if not symbol_data:
                raise InvalidLibraryError(lib_id, "Symbol data is empty")

            # Ensure required fields exist
            if "pins" not in symbol_data:
                logger.warning(f"Symbol {lib_id} has no pin definitions")
                symbol_data["pins"] = []

            return symbol_data

        except Exception as e:
            raise InvalidLibraryError(lib_id, str(e))

    def _create_component_instance(
        self,
        lib_id: str,
        reference: str,
        value: str,
        position: Tuple[float, float],
        rotation: float,
        symbol_data: Dict[str, Any],
        unit: int,
        mirror: Optional[str],
        dnp: bool,
    ) -> SchematicSymbol:
        """Create a new component instance."""
        # Generate UUID
        component_uuid = str(uuid.uuid4())

        # Create position tuple with rotation
        position_tuple = (position[0], position[1], rotation)

        # Create the component
        component = SchematicSymbol(
            reference=reference,
            value=value,
            footprint=None,  # Set later in properties
            unit=unit,
            pins=[],  # Will be populated later
            uuid=component_uuid,
            lib_id=lib_id,
            position=position_tuple,
            in_bom=True,  # Will be updated in properties
            on_board=True,  # Will be updated in properties
            fields_autoplaced=True,
            properties={},
        )

        # Handle mirror if specified
        if mirror:
            component.properties["mirror"] = mirror

        # Handle DNP flag
        if dnp:
            component.properties["dnp"] = "yes"

        return component

    def _set_component_properties(
        self,
        component: SchematicSymbol,
        properties: Optional[Dict[str, str]],
        footprint: Optional[str],
        in_bom: bool,
        on_board: bool,
    ) -> None:
        """Set component properties."""
        # Set standard properties
        component.properties["Reference"] = component.reference
        component.properties["Value"] = component.value

        if footprint:
            component.footprint = footprint
            component.properties["Footprint"] = footprint

        component.in_bom = in_bom
        component.on_board = on_board

        # Set custom properties
        if properties:
            for key, value in properties.items():
                # Validate property names
                if not self._is_valid_property_name(key):
                    raise InvalidPropertyError(key, "Invalid property name format")
                component.properties[key] = value

    def _create_pins(
        self, component: SchematicSymbol, symbol_data: Dict[str, Any], unit: int
    ) -> None:
        """Create pins for the component from symbol data."""
        pins_data = symbol_data.get("pins", [])

        for pin_data in pins_data:
            # Check if pin belongs to this unit (for multi-unit symbols)
            pin_unit = pin_data.get("unit", 1)
            if pin_unit != 0 and pin_unit != unit:  # unit 0 means common to all units
                continue

            # Create pin
            pin = SchematicPin(
                number=str(pin_data.get("number", "")),
                type=pin_data.get("electrical_type", "passive"),
                net_name=None,  # Will be set when connected
                uuid=str(uuid.uuid4()),
            )

            component.pins.append(pin)

        logger.debug(
            f"Created {len(component.pins)} pins for component {component.reference}"
        )

    def _get_symbol_size(self, symbol_data: Dict[str, Any]) -> Tuple[float, float]:
        """Get the size of a symbol for collision detection."""
        # Try to get size from symbol data
        # This is a simplified version - real implementation would parse
        # the graphical elements to determine actual size

        # For now, use default sizes based on pin count
        pin_count = len(symbol_data.get("pins", []))

        if pin_count <= 2:
            return (10.16, 5.08)  # Small component (resistor, capacitor)
        elif pin_count <= 8:
            return (20.32, 15.24)  # Medium component (small IC)
        else:
            return (30.48, 25.4)  # Large component (large IC)

    def _is_valid_property_name(self, name: str) -> bool:
        """Check if a property name is valid."""
        # Property names should not contain special characters
        # that could interfere with S-expression parsing
        invalid_chars = ["(", ")", '"', "\\", "\n", "\r", "\t"]
        return not any(char in name for char in invalid_chars)

    def get_component(self, reference: str) -> Optional[SchematicSymbol]:
        """
        Get a component by its reference designator.

        Args:
            reference: The reference designator (e.g., "R1", "U2")

        Returns:
            The component or None if not found
        """
        return self._component_index.get(reference)

    def get_all_components(self) -> List[SchematicSymbol]:
        """
        Get all components in the schematic.

        Returns:
            List of all components
        """
        return list(self.schematic.components)

    def update_component_property(
        self,
        reference: str,
        property_name: str,
        new_value: str,
        create_if_missing: bool = True,
    ) -> bool:
        """
        Update a component property.

        Args:
            reference: Component reference designator
            property_name: Name of the property to update
            new_value: New value for the property
            create_if_missing: Whether to create the property if it doesn't exist

        Returns:
            True if successful, False otherwise

        Raises:
            ComponentNotFoundError: If the component is not found
            InvalidPropertyError: If the property name is invalid
        """
        component = self.get_component(reference)
        if not component:
            raise ComponentNotFoundError(reference)

        # Validate property name
        if not self._is_valid_property_name(property_name):
            raise InvalidPropertyError(property_name)

        # Check if property exists
        if property_name in component.properties:
            old_value = component.properties[property_name]
            component.properties[property_name] = new_value

            # Special handling for certain properties
            if property_name == "Reference":
                # Update reference in manager
                if self.reference_manager.update_reference(reference, new_value):
                    component.reference = new_value
                    # Update index
                    del self._component_index[reference]
                    self._component_index[new_value] = component
                else:
                    # Rollback
                    component.properties[property_name] = old_value
                    return False

            elif property_name == "Value":
                component.value = new_value

            elif property_name == "Footprint":
                component.footprint = new_value

            logger.debug(
                f"Updated property {property_name} of {reference} to {new_value}"
            )
            return True

        elif create_if_missing:
            # Add new property
            component.properties[property_name] = new_value
            logger.debug(
                f"Added property {property_name} to {reference} with value {new_value}"
            )
            return True

        return False

    def validate_schematic(self) -> List[str]:
        """
        Validate the schematic for common issues.

        Returns:
            List of validation warnings/errors
        """
        issues = []

        # Check for duplicate references
        seen_refs = set()
        for comp in self.schematic.components:
            if comp.reference in seen_refs:
                issues.append(f"Duplicate reference: {comp.reference}")
            seen_refs.add(comp.reference)

        # Check for unassigned references
        for comp in self.schematic.components:
            if comp.reference.endswith("?"):
                issues.append(
                    f"Unassigned reference: {comp.reference} at {comp.position}"
                )

        # Check for components without values
        for comp in self.schematic.components:
            if not comp.value:
                issues.append(f"Component {comp.reference} has no value")

        # Check for overlapping components
        for i, comp1 in enumerate(self.schematic.components):
            if not comp1.position:
                continue
            for comp2 in self.schematic.components[i + 1 :]:
                if not comp2.position:
                    continue
                # Simple distance check
                dx = abs(comp1.position[0] - comp2.position[0])
                dy = abs(comp1.position[1] - comp2.position[1])
                if dx < 5.0 and dy < 5.0:  # Within 5mm
                    issues.append(
                        f"Components {comp1.reference} and {comp2.reference} may overlap"
                    )

        return issues

    # Delegate methods to ComponentOperations
    def move_component(
        self,
        reference: str,
        new_position: Tuple[float, float],
        check_collision: bool = True,
    ) -> bool:
        """Move a component to a new position."""
        return self.operations.move_component(reference, new_position, check_collision)

    def remove_component(self, reference: str) -> bool:
        """Remove a component from the schematic."""
        return self.operations.remove_component(reference)

    def clone_component(
        self,
        reference: str,
        new_reference: Optional[str] = None,
        offset: Tuple[float, float] = (25.4, 0),
        auto_increment: bool = True,
    ) -> Optional[SchematicSymbol]:
        """Clone an existing component."""
        return self.operations.clone_component(
            reference, new_reference, offset, auto_increment
        )
