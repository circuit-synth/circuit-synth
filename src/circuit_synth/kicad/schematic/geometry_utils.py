"""
Geometry utilities for dynamic positioning in KiCad schematics with debug logging.
"""

import logging
import math
from typing import Dict, List, Optional, Tuple

from ..core.types import Label, LabelType, Point, SchematicPin, SchematicSymbol

# Create logger for this module
logger = logging.getLogger(__name__)


class GeometryUtils:
    """Utilities for calculating positions and transformations in schematics."""

    @staticmethod
    def get_actual_pin_position(
        symbol: SchematicSymbol, pin_number: str
    ) -> Optional[Point]:
        """
        Get the world position of a pin on a component.

        Args:
            symbol: The schematic symbol
            pin_number: Pin number to find

        Returns:
            Absolute position of the pin in world coordinates, or None if not found
        """
        logger.info(
            f"Getting actual position for pin {pin_number} on symbol {symbol.reference}"
        )

        # Find pin in symbol definition
        for pin in symbol.pins:
            if pin.number == pin_number:
                world_pos = GeometryUtils.transform_pin_to_world(
                    pin, symbol.position, symbol.rotation
                )
                logger.info(
                    f"  Pin {pin_number} world position: ({world_pos.x}, {world_pos.y})"
                )
                return world_pos

        logger.warning(f"  Pin {pin_number} not found on symbol {symbol.reference}")
        return None

    @staticmethod
    def transform_pin_to_world(
        pin: SchematicPin, symbol_pos: Point, symbol_rotation: float
    ) -> Point:
        """
        Transform pin position from symbol space to world space.

        Args:
            pin: The pin object
            symbol_pos: Symbol position in world coordinates
            symbol_rotation: Symbol rotation in degrees

        Returns:
            Pin position in world coordinates
        """
        logger.info(f"Transforming pin {pin.number} to world space:")
        logger.info(f"  Pin local position: ({pin.position.x}, {pin.position.y})")
        logger.info(f"  Pin orientation: {pin.orientation}°")
        logger.info(f"  Symbol position: ({symbol_pos.x}, {symbol_pos.y})")
        logger.info(f"  Symbol rotation: {symbol_rotation}°")

        # Apply rotation
        angle_rad = math.radians(symbol_rotation)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        # Rotate pin position
        # Note: We negate Y here because in symbol definitions, positive Y means "up"
        # but in KiCad's world coordinates, positive Y means "down"
        rotated_x = pin.position.x * cos_a - (-pin.position.y) * sin_a
        rotated_y = pin.position.x * sin_a + (-pin.position.y) * cos_a

        logger.info(f"  Rotated position: ({rotated_x}, {rotated_y})")

        # Translate to symbol position
        world_x = symbol_pos.x + rotated_x
        world_y = symbol_pos.y + rotated_y

        logger.info(f"  World position: ({world_x}, {world_y})")

        return Point(world_x, world_y)

    @staticmethod
    def get_pin_end_position(
        pin: SchematicPin, pin_world_pos: Point, symbol_rotation: float
    ) -> Point:
        """
        Get the end position of a pin (where it connects to wires).

        Args:
            pin: The pin object
            pin_world_pos: Pin position in world coordinates
            symbol_rotation: Symbol rotation in degrees

        Returns:
            End position of the pin
        """
        # Calculate pin orientation in world space
        world_orientation = (pin.orientation + symbol_rotation) % 360

        logger.info(f"Calculating pin end position for pin {pin.number}:")
        logger.info(f"  Pin world position: ({pin_world_pos.x}, {pin_world_pos.y})")
        logger.info(f"  Pin orientation: {pin.orientation}°")
        logger.info(f"  Symbol rotation: {symbol_rotation}°")
        logger.info(f"  World orientation: {world_orientation}°")
        logger.info(f"  Pin length: {pin.length}")

        # In KiCad, pin orientations indicate the direction the pin points FROM the component:
        # 0° = pin points right (connects on the left side of component)
        # 90° = pin points up (connects on the bottom of component)
        # 180° = pin points left (connects on the right side of component)
        # 270° = pin points down (connects on the top of component)

        # Calculate offset based on pin length and orientation
        # The pin end is in the OPPOSITE direction of where it connects
        if world_orientation == 0:  # Pin points right, so end is to the right
            offset_x = pin.length
            offset_y = 0
            logger.info(f"  Pin points RIGHT: offset = ({offset_x}, {offset_y})")
        elif (
            world_orientation == 90
        ):  # Pin points up, so end is up (negative Y in KiCad)
            offset_x = 0
            offset_y = -pin.length
            logger.info(f"  Pin points UP: offset = ({offset_x}, {offset_y})")
        elif world_orientation == 180:  # Pin points left, so end is to the left
            offset_x = -pin.length
            offset_y = 0
            logger.info(f"  Pin points LEFT: offset = ({offset_x}, {offset_y})")
        elif (
            world_orientation == 270
        ):  # Pin points down, so end is down (positive Y in KiCad)
            offset_x = 0
            offset_y = pin.length
            logger.info(f"  Pin points DOWN: offset = ({offset_x}, {offset_y})")
        else:
            # For non-cardinal angles, use trigonometry
            # Note: In KiCad, Y+ is down, so we need to negate the sine component
            angle_rad = math.radians(world_orientation)
            offset_x = pin.length * math.cos(angle_rad)
            offset_y = pin.length * math.sin(angle_rad)
            logger.info(
                f"  Pin at {world_orientation}°: offset = ({offset_x}, {offset_y})"
            )

        end_x = pin_world_pos.x + offset_x
        end_y = pin_world_pos.y + offset_y

        logger.info(f"  Pin end position: ({end_x}, {end_y})")

        return Point(end_x, end_y)

    @staticmethod
    def calculate_label_position(
        pin: SchematicPin,
        pin_world_pos: Point,
        symbol_rotation: float,
        offset_distance: float = 0,
    ) -> Point:
        """
        Calculate optimal label position for a pin.

        Args:
            pin: The pin object
            pin_world_pos: Pin position in world coordinates
            symbol_rotation: Symbol rotation in degrees
            offset_distance: Distance to offset label from pin (not used - kept for compatibility)

        Returns:
            Optimal position for the label
        """
        logger.info(f"Calculating label position for pin {pin.number}")

        # Place labels at the pin position (where pin connects to component)
        # KiCad will handle the label anchor correctly based on its orientation
        logger.info(f"  Label position: ({pin_world_pos.x}, {pin_world_pos.y})")

        return pin_world_pos

    @staticmethod
    def calculate_label_orientation(pin: SchematicPin, symbol_rotation: float) -> float:
        """
        Calculate readable label orientation based on pin orientation.

        Args:
            pin: The pin object
            symbol_rotation: Symbol rotation in degrees

        Returns:
            Label orientation in degrees (0, 90, 180, or 270)
        """
        # Calculate pin orientation in world space
        world_orientation = (pin.orientation + symbol_rotation) % 360

        logger.info(f"Calculating label orientation for pin {pin.number}:")
        logger.info(f"  Pin orientation: {pin.orientation}°")
        logger.info(f"  Symbol rotation: {symbol_rotation}°")
        logger.info(f"  World orientation: {world_orientation}°")

        # Label orientation should be OPPOSITE of pin direction
        # Pin pointing right (0°) -> label pointing left (180°)
        # Pin pointing up (90°) -> label pointing down (270°)
        # Pin pointing left (180°) -> label pointing right (0°)
        # Pin pointing down (270°) -> label pointing up (90°)

        # Calculate opposite orientation
        opposite_orientation = (world_orientation + 180) % 360
        logger.info(f"  Opposite orientation: {opposite_orientation}°")

        # Round to nearest 90 degrees for clean orientations
        if opposite_orientation < 45 or opposite_orientation >= 315:
            label_orientation = 0  # Right
        elif 45 <= opposite_orientation < 135:
            label_orientation = 90  # Up
        elif 135 <= opposite_orientation < 225:
            label_orientation = 180  # Left
        else:  # 225 <= opposite_orientation < 315
            label_orientation = 270  # Down

        logger.info(f"  Label orientation: {label_orientation}°")

        return label_orientation

    @staticmethod
    def create_dynamic_hierarchical_label(
        net_name: str,
        pin: SchematicPin,
        pin_world_pos: Point,
        symbol_rotation: float,
        offset_distance: float = 0,
    ) -> Label:
        """
        Create a hierarchical label with dynamic positioning.

        Args:
            net_name: Name of the net
            pin: The pin object
            pin_world_pos: Pin position in world coordinates
            symbol_rotation: Symbol rotation in degrees
            offset_distance: Distance to offset label from pin end

        Returns:
            Label object with proper positioning
        """
        logger.info(f"Creating hierarchical label '{net_name}' for pin {pin.number}")

        # Calculate label position
        label_pos = GeometryUtils.calculate_label_position(
            pin, pin_world_pos, symbol_rotation, offset_distance
        )

        # Calculate label orientation
        label_orientation = GeometryUtils.calculate_label_orientation(
            pin, symbol_rotation
        )

        logger.info(
            f"  Final label '{net_name}': position=({label_pos.x}, {label_pos.y}), orientation={label_orientation}°"
        )

        return Label(
            text=net_name,
            position=label_pos,
            orientation=label_orientation,
            label_type=LabelType.HIERARCHICAL,
        )

    @staticmethod
    def get_pins_at_position(
        symbol: SchematicSymbol, tolerance: float = 0.01
    ) -> Dict[Tuple[float, float], List[SchematicPin]]:
        """
        Group pins by their world position.

        Args:
            symbol: The schematic symbol
            tolerance: Position tolerance for grouping

        Returns:
            Dictionary mapping positions to lists of pins at that position
        """
        pins_by_position = {}

        for pin in symbol.pins:
            world_pos = GeometryUtils.transform_pin_to_world(
                pin, symbol.position, symbol.rotation
            )

            # Find existing position within tolerance
            found = False
            for pos_key in pins_by_position:
                if (
                    abs(pos_key[0] - world_pos.x) < tolerance
                    and abs(pos_key[1] - world_pos.y) < tolerance
                ):
                    pins_by_position[pos_key].append(pin)
                    found = True
                    break

            if not found:
                pins_by_position[(world_pos.x, world_pos.y)] = [pin]

        return pins_by_position
