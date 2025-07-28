"""
Integrated Placement - Uses new API's PlacementEngine in current workflow.

This module demonstrates how to enhance the existing collision-based placement
with the new API's advanced placement strategies.
"""

import logging
from typing import Dict, List, Optional, Tuple

from circuit_synth.kicad.sch_api import PlacementEngine, PlacementStrategy
from circuit_synth.kicad.sch_api.models import BoundingBox, Position

logger = logging.getLogger(__name__)


class IntegratedPlacementManager:
    """
    Enhances the existing CollisionManager with new API placement strategies.
    """

    def __init__(self, sheet_size: Tuple[float, float] = (210.0, 297.0)):
        self.sheet_size = sheet_size
        self.placement_engine = PlacementEngine()

        # Component type categorization for placement strategies
        self.connector_types = ["connector", "testpoint", "jumper", "header", "socket"]
        self.power_types = ["regulator", "dcdc", "battery", "power", "supply"]
        self.passive_types = ["resistor", "capacitor", "inductor", "ferrite"]
        self.ic_types = ["ic", "microcontroller", "mcu", "processor", "opamp"]

    def place_components_with_strategy(self, components: List) -> Dict[str, Position]:
        """
        Place components using intelligent strategies based on component type.

        Args:
            components: List of component objects from current system

        Returns:
            Dictionary mapping component IDs to Position objects
        """
        placements = {}
        placed_components = []

        # Group components by type
        connectors = []
        power_components = []
        passives = []
        ics = []
        others = []

        for comp in components:
            comp_type = self._get_component_type(comp).lower()

            if any(ct in comp_type for ct in self.connector_types):
                connectors.append(comp)
            elif any(pt in comp_type for pt in self.power_types):
                power_components.append(comp)
            elif any(pt in comp_type for pt in self.passive_types):
                passives.append(comp)
            elif any(it in comp_type for it in self.ic_types):
                ics.append(comp)
            else:
                others.append(comp)

        # Place connectors on the left edge
        if connectors:
            logger.info(f"Placing {len(connectors)} connectors on left edge")
            positions = self.placement_engine.edge_placement(
                count=len(connectors),
                edge="left",
                spacing=20.0,
                sheet_size=self.sheet_size,
            )
            for comp, pos in zip(connectors, positions):
                placements[self._get_component_id(comp)] = pos
                placed_components.append(self._create_placed_component(comp, pos))

        # Place power components on the top edge
        if power_components:
            logger.info(f"Placing {len(power_components)} power components on top edge")
            positions = self.placement_engine.edge_placement(
                count=len(power_components),
                edge="top",
                spacing=25.0,
                sheet_size=self.sheet_size,
            )
            for comp, pos in zip(power_components, positions):
                placements[self._get_component_id(comp)] = pos
                placed_components.append(self._create_placed_component(comp, pos))

        # Place ICs in the center using grid placement
        if ics:
            logger.info(f"Placing {len(ics)} ICs in center grid")
            # Calculate center starting position
            center_x = self.sheet_size[0] / 2 - 40  # Offset for typical IC size
            center_y = self.sheet_size[1] / 2 - 30

            positions = self.placement_engine.grid_placement(
                count=len(ics),
                start_position=Position(center_x, center_y),
                grid_spacing=30.0,  # Larger spacing for ICs
                columns=2,
            )
            for comp, pos in zip(ics, positions):
                placements[self._get_component_id(comp)] = pos
                placed_components.append(self._create_placed_component(comp, pos))

        # Place passives using contextual placement near ICs
        if passives and placed_components:
            logger.info(f"Placing {len(passives)} passive components contextually")
            for passive in passives:
                # Find the best position near existing components
                pos = self.placement_engine.find_position(
                    strategy=PlacementStrategy.CONTEXTUAL,
                    existing_components=placed_components,
                    bounding_box=BoundingBox(0, 0, 5, 5),  # Small components
                    spacing=5.0,
                )
                placements[self._get_component_id(passive)] = pos
                placed_components.append(self._create_placed_component(passive, pos))

        # Place remaining components using grid placement
        if others:
            logger.info(f"Placing {len(others)} other components in grid")
            # Start below the center area
            start_y = self.sheet_size[1] / 2 + 40

            positions = self.placement_engine.grid_placement(
                count=len(others),
                start_position=Position(20, start_y),
                grid_spacing=15.0,
                columns=4,
            )
            for comp, pos in zip(others, positions):
                placements[self._get_component_id(comp)] = pos
                placed_components.append(self._create_placed_component(comp, pos))

        return placements

    def _get_component_type(self, component) -> str:
        """Extract component type from various possible attributes."""
        if hasattr(component, "type"):
            return str(component.type)
        elif hasattr(component, "component_type"):
            return str(component.component_type)
        elif hasattr(component, "symbol_id"):
            # Extract from symbol_id (e.g., "Device:R" -> "resistor")
            symbol_id = component.symbol_id
            if ":R" in symbol_id:
                return "resistor"
            elif ":C" in symbol_id:
                return "capacitor"
            elif ":L" in symbol_id:
                return "inductor"
            elif ":Conn" in symbol_id:
                return "connector"
            elif ":U" in symbol_id:
                return "ic"
        return "unknown"

    def _get_component_id(self, component) -> str:
        """Get unique identifier for component."""
        if hasattr(component, "id"):
            return str(component.id)
        elif hasattr(component, "uuid"):
            return str(component.uuid)
        elif hasattr(component, "reference"):
            return str(component.reference)
        else:
            return str(id(component))

    def _create_placed_component(self, component, position: Position) -> dict:
        """Create a placed component dict for the placement engine."""
        # Estimate bounding box (will be refined when we have actual symbol data)
        comp_type = self._get_component_type(component).lower()

        # Default sizes based on component type
        if any(ct in comp_type for ct in self.passive_types):
            bbox = BoundingBox(position.x, position.y, 7.5, 5)
        elif any(ct in comp_type for ct in self.ic_types):
            bbox = BoundingBox(position.x, position.y, 20, 15)
        elif any(ct in comp_type for ct in self.connector_types):
            bbox = BoundingBox(position.x, position.y, 10, 20)
        else:
            bbox = BoundingBox(position.x, position.y, 10, 10)

        return {
            "reference": self._get_component_id(component),
            "position": position,
            "bounding_box": bbox,
        }


# Integration example for CollisionManager
def integrate_into_collision_manager():
    """
    Shows how to modify CollisionManager to use integrated placement.
    """
    example_code = '''
    # In collision_manager.py, modify the place_component method:
    
    def __init__(self, sheet_size: Tuple[float, float] = (210.0, 297.0), grid=2.54):
        # ... existing init code ...
        
        # Add integrated placement manager
        self.integrated_placement = IntegratedPlacementManager(sheet_size)
        self.use_smart_placement = True  # Feature flag
    
    def place_all_components(self, components: List) -> Dict:
        """Place all components using smart strategies."""
        if self.use_smart_placement:
            # Use new placement engine
            placements = self.integrated_placement.place_components_with_strategy(components)
            
            # Convert Position objects to tuples for compatibility
            result = {}
            for comp_id, position in placements.items():
                result[comp_id] = (position.x, position.y)
            return result
        else:
            # Fall back to original placement logic
            return self._original_place_components(components)
    '''
    return example_code


# Test the integrated placement
def test_integrated_placement():
    """Test the integrated placement manager."""

    class MockComponent:
        def __init__(self, comp_id, comp_type, symbol_id):
            self.id = comp_id
            self.type = comp_type
            self.symbol_id = symbol_id

    # Create test components
    components = [
        # Connectors
        MockComponent("J1", "connector", "Connector:Conn_01x04"),
        MockComponent("J2", "connector", "Connector:USB_B"),
        # Power
        MockComponent("U1", "regulator", "Regulator_Linear:LM7805"),
        # ICs
        MockComponent("U2", "microcontroller", "MCU_Microchip:ATmega328P"),
        MockComponent("U3", "opamp", "Amplifier_Operational:LM358"),
        # Passives
        MockComponent("R1", "resistor", "Device:R"),
        MockComponent("R2", "resistor", "Device:R"),
        MockComponent("C1", "capacitor", "Device:C"),
        MockComponent("C2", "capacitor", "Device:C"),
        # Others
        MockComponent("D1", "diode", "Device:D"),
        MockComponent("Q1", "transistor", "Device:Q_NPN_BCE"),
    ]

    # Test placement
    manager = IntegratedPlacementManager()
    placements = manager.place_components_with_strategy(components)

    print("Integrated Placement Results:")
    print("-" * 50)
    for comp in components:
        pos = placements.get(comp.id)
        if pos:
            print(f"{comp.id} ({comp.type}): x={pos.x:.1f}, y={pos.y:.1f}")

    # Visualize placement groups
    print("\nPlacement Strategy Summary:")
    print("- Connectors: Left edge")
    print("- Power components: Top edge")
    print("- ICs: Center grid")
    print("- Passives: Near ICs (contextual)")
    print("- Others: Bottom grid")


if __name__ == "__main__":
    test_integrated_placement()
