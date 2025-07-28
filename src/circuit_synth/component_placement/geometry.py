"""Component geometry handling for KiCad schematic placement.

This module provides base classes for handling component-specific geometry including:
- Bounding box calculations
- Pin location mapping
- Component dimensions
"""

import math
from dataclasses import dataclass
from typing import Dict, Optional, Tuple


@dataclass
class PinLocation:
    """Represents a pin's location relative to component center."""

    x: float  # X offset from center
    y: float  # Y offset from center
    side: str  # Which side of component (left, right, top, bottom)


@dataclass
class ComponentDimensions:
    """Represents a component's dimensions."""

    width: float
    height: float
    pin_grid: float = 2.54  # Default grid spacing


class ComponentGeometryHandler:
    """Base class for handling component geometry and pin locations."""

    def __init__(self, component_type: str):
        """Initialize with component type."""
        self.component_type = component_type
        self._dimensions = self._get_default_dimensions()
        self._pin_locations: Dict[str, PinLocation] = {}
        self._setup_pin_locations()

    def _get_default_dimensions(self) -> ComponentDimensions:
        """Get default dimensions for this component type."""
        # Default dimensions - override in subclasses
        return ComponentDimensions(width=5.08, height=15.24)

    def _setup_pin_locations(self) -> None:
        """Set up pin locations for this component type."""
        # Override in subclasses to define pin locations
        pass

    def get_pin_location(
        self, pin_number: str, rotation: float = 0
    ) -> Optional[Tuple[float, float]]:
        """Get pin location relative to component center, accounting for rotation."""
        if pin_number not in self._pin_locations:
            return None

        pin = self._pin_locations[pin_number]

        # Apply rotation transformation
        theta = math.radians(rotation)
        rotated_x = pin.x * math.cos(theta) - pin.y * math.sin(theta)
        rotated_y = pin.x * math.sin(theta) + pin.y * math.cos(theta)

        return (rotated_x, rotated_y)

    def get_bounding_box(
        self, x: float, y: float, rotation: float
    ) -> Tuple[float, float, float, float]:
        """Get component bounding box at given position and rotation."""
        width = self._dimensions.width
        height = self._dimensions.height

        # For 90/270 degree rotations, swap width and height
        if rotation in [90, 270]:
            width, height = height, width

        # Calculate corners relative to center
        left = x - width / 2
        top = y - height / 2

        return (left, top, width, height)


class ResistorGeometryHandler(ComponentGeometryHandler):
    """Geometry handler for resistor components."""

    def _get_default_dimensions(self) -> ComponentDimensions:
        """Get resistor-specific dimensions."""
        dims = ComponentDimensions(
            width=5.08,  # Standard resistor symbol width
            height=10.16,  # Reduced height for better spacing
        )
        print(f"Creating resistor with dimensions: {dims}")
        return dims

    def _setup_pin_locations(self) -> None:
        """Set up resistor pin locations."""
        # Standard resistor has pins at top and bottom center
        pin1 = PinLocation(x=0, y=5.08, side="top")  # Pin 1 at top
        pin2 = PinLocation(x=0, y=-5.08, side="bottom")  # Pin 2 at bottom
        print(f"Setting up resistor pins:")
        print(f"  Pin 1 at: ({pin1.x}, {pin1.y})")
        print(f"  Pin 2 at: ({pin2.x}, {pin2.y})")
        self._pin_locations = {"1": pin1, "2": pin2}


class PowerSymbolGeometryHandler(ComponentGeometryHandler):
    """Geometry handler for power symbols."""

    def _get_default_dimensions(self) -> ComponentDimensions:
        """Get power symbol dimensions."""
        dims = ComponentDimensions(
            width=5.08,  # Increased width for better visibility
            height=5.08,  # Increased height for better spacing
        )
        print(f"Creating power symbol with dimensions: {dims}")
        return dims

    def _setup_pin_locations(self) -> None:
        """Set up power symbol pin locations."""
        # Power symbols have pin at bottom center
        pin_loc = PinLocation(x=0, y=2.54, side="bottom")  # Offset pin from center
        print(f"Setting up power symbol pin at: ({pin_loc.x}, {pin_loc.y})")
        self._pin_locations = {"1": pin_loc}


def create_geometry_handler(
    component_type: str, library: str
) -> ComponentGeometryHandler:
    """Factory function to create appropriate geometry handler for component."""
    if library == "Device" and component_type == "R":
        return ResistorGeometryHandler(component_type)
    elif library == "power":
        return PowerSymbolGeometryHandler(component_type)
    else:
        # Default to base handler for unknown components
        return ComponentGeometryHandler(component_type)
