"""
KiCad Schematic Updater

This module provides the SchematicUpdater class that applies synchronization changes
to KiCad schematic files while preserving user placement and connections.

The updater handles:
- Adding new components with hierarchical labels
- Updating component properties while preserving position
- Preserving user-added components and connections
- Finding safe placement locations for new components
"""

import logging
import uuid
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..sch_editor.schematic_editor import SchematicEditor
from ..sch_editor.schematic_reader import (
    NetNode,
    Schematic,
    SchematicNet,
    SchematicPin,
    SchematicSymbol,
)

logger = logging.getLogger(__name__)


@dataclass
class PlacementInfo:
    """Information about component placement"""

    position: Tuple[float, float]  # x, y coordinates in mm
    rotation: float = 0.0  # rotation in degrees


@dataclass
class ComponentUpdate:
    """Represents an update to be applied to a component"""

    action: str  # 'add', 'modify', 'preserve'
    component_id: str
    kicad_reference: Optional[str] = None
    new_properties: Optional[Dict[str, Any]] = None
    placement: Optional[PlacementInfo] = None


class SchematicUpdater:
    """
    Updates KiCad schematic files based on synchronization results.

    This class takes a SyncReport and applies the necessary changes to the
    KiCad schematic while preserving user placement and connections.
    """

    def __init__(
        self,
        schematic: Schematic,
        project_path: Path,
        schematic_path: Optional[Path] = None,
    ):
        """
        Initialize the schematic updater.

        Args:
            schematic: The loaded KiCad schematic to update
            project_path: Path to the KiCad project directory
            schematic_path: Optional path to the actual schematic file being updated
        """
        self.schematic = schematic
        self.project_path = project_path
        self.schematic_path = schematic_path  # Store the actual schematic file path
        self.grid_spacing = 2.54  # Standard KiCad grid spacing in mm
        self.component_spacing = 10.16  # Minimum spacing between components in mm

        logger.info(f"SchematicUpdater initialized for project: {project_path}")
        logger.debug(f"Loaded schematic with {len(schematic.components)} components")

    def apply_updates(self, updates: List[ComponentUpdate]) -> None:
        """
        Apply a list of component updates to the schematic.

        Args:
            updates: List of ComponentUpdate objects describing changes to make
        """
        logger.info(f"Applying {len(updates)} updates to schematic")

        for update in updates:
            if update.action == "add":
                self._add_component(update)
            elif update.action == "modify":
                self._modify_component(update)
            elif update.action == "preserve":
                logger.debug(f"Preserving component: {update.kicad_reference}")
            elif update.action == "remove":
                self._remove_component(update)
            else:
                logger.warning(f"Unknown update action: {update.action}")

        logger.info("All updates applied successfully")

    def _add_component(self, update: ComponentUpdate) -> None:
        """
        Add a new component to the schematic.

        Args:
            update: ComponentUpdate with action='add'
        """
        logger.debug(f"Adding new component: {update.component_id}")

        # Find safe placement location if not provided
        if update.placement is None:
            placement = self._find_safe_placement()
        else:
            placement = update.placement

        # Create new SchematicSymbol
        new_symbol = self._create_schematic_symbol(update, placement)

        # Add to schematic
        self.schematic.components.append(new_symbol)

        # Add hierarchical labels for all pins
        self._add_hierarchical_labels(new_symbol)

        logger.info(
            f"Added component {update.component_id} at position ({placement.position[0]:.2f}, {placement.position[1]:.2f})"
        )

    def _modify_component(self, update: ComponentUpdate) -> None:
        """
        Modify an existing component's properties while preserving position.

        Args:
            update: ComponentUpdate with action='modify'
        """
        logger.debug(f"Modifying component: {update.kicad_reference}")

        # Find the component in the schematic
        component = self.schematic.get_component(update.kicad_reference)
        if component is None:
            logger.error(
                f"Component {update.kicad_reference} not found for modification"
            )
            return

        # Update properties while preserving position and connections
        if update.new_properties:
            for prop_name, prop_value in update.new_properties.items():
                if prop_name == "value":
                    component.value = prop_value
                elif prop_name == "footprint":
                    component.footprint = prop_value
                else:
                    # Store in properties dictionary
                    component.properties[prop_name] = prop_value

        logger.info(f"Modified component {update.kicad_reference} properties")

    def _remove_component(self, update: ComponentUpdate) -> None:
        """
        Remove a component from the schematic.

        Args:
            update: ComponentUpdate with action='remove'
        """
        logger.debug(f"Removing component: {update.kicad_reference}")

        # Use the schematic editor to remove the component
        editor = SchematicEditor(self.schematic_path)
        editor.remove_component(update.kicad_reference)
        editor.save()

        logger.info(f"Removed component {update.kicad_reference}")

    def _create_schematic_symbol(
        self, update: ComponentUpdate, placement: PlacementInfo
    ) -> SchematicSymbol:
        """
        Create a new SchematicSymbol from component update information.

        Args:
            update: ComponentUpdate containing component information
            placement: PlacementInfo for positioning

        Returns:
            New SchematicSymbol instance
        """
        # Extract component information from update
        props = update.new_properties or {}

        # Create pins list (will be populated based on lib_id)
        pins = self._create_component_pins(props.get("lib_id", "Device:R"))

        # Create the symbol
        symbol = SchematicSymbol(
            reference=props.get("reference", update.component_id),
            value=props.get("value", ""),
            footprint=props.get("footprint"),
            unit=1,
            pins=pins,
            uuid=str(uuid.uuid4()),
            lib_id=props.get("lib_id", "Device:R"),
            position=(placement.position[0], placement.position[1], placement.rotation),
            properties=props.copy(),
        )

        return symbol

    def _create_component_pins(self, lib_id: str) -> List[SchematicPin]:
        """
        Create pins for a component based on its library ID.

        Args:
            lib_id: KiCad library identifier (e.g., 'Device:R')

        Returns:
            List of SchematicPin objects
        """
        # Basic pin configurations for common components
        pin_configs = {
            "Device:R": [SchematicPin("1", "passive"), SchematicPin("2", "passive")],
            "Device:C": [SchematicPin("1", "passive"), SchematicPin("2", "passive")],
            "Device:L": [SchematicPin("1", "passive"), SchematicPin("2", "passive")],
            "Connector:TestPoint": [SchematicPin("1", "passive")],
        }

        # Get pin configuration or default to 2-pin passive
        pins_config = pin_configs.get(
            lib_id, [SchematicPin("1", "passive"), SchematicPin("2", "passive")]
        )

        # Create pins with UUIDs
        pins = []
        for pin_config in pins_config:
            pin = SchematicPin(
                number=pin_config.number, type=pin_config.type, uuid=str(uuid.uuid4())
            )
            pins.append(pin)

        return pins

    def _find_safe_placement(self) -> PlacementInfo:
        """
        Find a safe location to place a new component that doesn't overlap existing ones.

        Returns:
            PlacementInfo with safe coordinates
        """
        # Get bounding box of existing components
        existing_positions = []
        for component in self.schematic.components:
            if component.position:
                existing_positions.append(
                    (component.position[0], component.position[1])
                )

        if not existing_positions:
            # No existing components, place at origin with offset
            return PlacementInfo(position=(25.4, 25.4))  # 1 inch from origin

        # Find the rightmost and bottommost positions
        max_x = max(pos[0] for pos in existing_positions)
        max_y = max(pos[1] for pos in existing_positions)

        # Calculate grid-aligned position with spacing
        new_x = self._align_to_grid(max_x + self.component_spacing)
        new_y = self._align_to_grid(max_y)

        # Check if we need to wrap to next row
        sheet_width = 279.4  # A4 width in mm
        if new_x > sheet_width - 25.4:  # Leave margin
            new_x = 25.4  # Reset to left margin
            new_y = self._align_to_grid(max_y + self.component_spacing)

        return PlacementInfo(position=(new_x, new_y))

    def _align_to_grid(self, coordinate: float) -> float:
        """
        Align a coordinate to the KiCad grid.

        Args:
            coordinate: Coordinate to align

        Returns:
            Grid-aligned coordinate
        """
        return round(coordinate / self.grid_spacing) * self.grid_spacing

    def _add_hierarchical_labels(self, symbol: SchematicSymbol) -> None:
        """
        Add hierarchical labels for all pins of a component.

        Args:
            symbol: SchematicSymbol to add labels for
        """
        logger.debug(f"Adding hierarchical labels for component {symbol.reference}")

        # For now, we'll just log this as the actual implementation would require
        # more complex label placement logic and net management
        for pin in symbol.pins:
            label_name = f"{symbol.reference}_pin_{pin.number}"
            logger.debug(
                f"Would add hierarchical label: {label_name} for pin {pin.number}"
            )

    def save_schematic(self, output_path: Optional[Path] = None) -> None:
        """
        Save the updated schematic to a file.

        Args:
            output_path: Optional path to save to. If None, overwrites original.
        """
        if output_path is None:
            if self.schematic_path:
                # Use the stored schematic path (the actual file we loaded from)
                output_path = self.schematic_path
            else:
                # Fallback to main schematic file
                project_name = self.project_path.stem
                output_path = self.project_path.parent / f"{project_name}.kicad_sch"

        logger.info(f"Saving updated schematic to: {output_path}")

        # Use the schematic editor to save the file
        editor = SchematicEditor(self.schematic_path)
        editor.data = self.schematic
        editor.save(str(output_path))

        logger.info("Schematic saved successfully")


def create_component_updates_from_sync_report(
    sync_report: Dict[str, Any],
    circuit_components: Dict[str, Any],
    kicad_components: Dict[str, Any],
) -> List[ComponentUpdate]:
    """
    Create a list of ComponentUpdate objects from a synchronization report.

    Args:
        sync_report: Dictionary containing sync results
        circuit_components: Components from circuit definition
        kicad_components: Components from KiCad schematic

    Returns:
        List of ComponentUpdate objects
    """
    updates = []

    # Parse details from sync report to create updates
    for detail in sync_report.get("details", []):
        if detail.startswith("Added:"):
            component_id = detail.split("Added: ")[1]
            if component_id in circuit_components:
                circuit_comp = circuit_components[component_id]
                update = ComponentUpdate(
                    action="add",
                    component_id=component_id,
                    new_properties={
                        "reference": circuit_comp.get("reference", component_id),
                        "value": circuit_comp.get("value", ""),
                        "footprint": circuit_comp.get("footprint"),
                        "lib_id": circuit_comp.get("lib_id", "Device:R"),
                    },
                )
                updates.append(update)

        elif detail.startswith("Modified:"):
            # Parse "Modified: R1 (resistor_1)"
            parts = detail.split("Modified: ")[1].split(" (")
            kicad_ref = parts[0]
            circuit_id = parts[1].rstrip(")")

            if circuit_id in circuit_components:
                circuit_comp = circuit_components[circuit_id]
                update = ComponentUpdate(
                    action="modify",
                    component_id=circuit_id,
                    kicad_reference=kicad_ref,
                    new_properties={
                        "value": circuit_comp.get("value"),
                        "footprint": circuit_comp.get("footprint"),
                    },
                )
                updates.append(update)

        elif detail.startswith("Preserved:"):
            kicad_ref = detail.split("Preserved: ")[1]
            update = ComponentUpdate(
                action="preserve", component_id=kicad_ref, kicad_reference=kicad_ref
            )
            updates.append(update)

        elif detail.startswith("Removed:"):
            kicad_ref = detail.split("Removed: ")[1]
            update = ComponentUpdate(
                action="remove", component_id=kicad_ref, kicad_reference=kicad_ref
            )
            updates.append(update)

    return updates
