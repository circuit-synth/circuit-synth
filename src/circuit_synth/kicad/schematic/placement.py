"""
Component placement engine for KiCad schematics.
Provides automatic placement strategies and collision detection.
"""

import logging
import time
from enum import Enum
from typing import List, Optional, Tuple

from ..core.types import Point, Schematic, SchematicSymbol, Sheet
from .symbol_geometry import SymbolGeometry

# Python-only implementation

logger = logging.getLogger(__name__)


class ElementBounds:
    """Bounding box for any schematic element (component or sheet)."""

    def __init__(
        self,
        x: float,
        y: float,
        width: float,
        height: float,
        element_type: str = "component",
    ):
        self.x = x
        self.y = y
        self.width = width
        self.height = height
        self.element_type = element_type  # "component" or "sheet"

    @property
    def right(self) -> float:
        return self.x + self.width

    @property
    def bottom(self) -> float:
        return self.y + self.height

    def overlaps(self, other: "ElementBounds") -> bool:
        """Check if this bounds overlaps with another."""
        return not (
            self.right < other.x
            or other.right < self.x
            or self.bottom < other.y
            or other.bottom < self.y
        )


# Keep ComponentBounds as alias for backward compatibility
ComponentBounds = ElementBounds


class PlacementStrategy(Enum):
    """Component placement strategies."""

    AUTO = "auto"  # Find next available position
    GRID = "grid"  # Place in grid pattern
    EDGE_RIGHT = "edge_right"  # Place at right edge
    EDGE_BOTTOM = "edge_bottom"  # Place at bottom edge
    CENTER = "center"  # Place at center


class PlacementEngine:
    """
    Handles automatic component placement with collision detection.
    """

    def __init__(
        self,
        schematic: Schematic,
        grid_size: float = 2.54,
        sheet_size: Tuple[float, float] = None,
    ):
        """
        Initialize placement engine.

        Args:
            schematic: The schematic to place components in
            grid_size: Grid size in mm (default 2.54mm = 0.1 inch)
            sheet_size: (width, height) of the sheet in mm (default A4: 210x297mm)
        """
        self.schematic = schematic
        self.grid_size = grid_size
        self.margin = 25.4  # 1 inch margin from edges
        self._symbol_geometry = SymbolGeometry()
        # Default to A4 if no sheet size provided
        self.sheet_size = sheet_size if sheet_size else (210.0, 297.0)

    def find_position(
        self,
        strategy: PlacementStrategy = PlacementStrategy.AUTO,
        component_size: Tuple[float, float] = (10.0, 10.0),
        component: Optional[SchematicSymbol] = None,
    ) -> Tuple[float, float]:
        """
        Find a suitable position for a new component using dynamic sizing.

        Args:
            strategy: Placement strategy to use
            component_size: (width, height) of component in mm (ignored if component provided)
            component: Component for dynamic sizing

        Returns:
            (x, y) position in mm
        """
        if strategy == PlacementStrategy.AUTO:
            if component:
                return self._find_next_available_position(component)
            else:
                # Fallback for when no component is provided
                logger.warning(
                    "No component provided for dynamic placement, using default size"
                )
                return self._find_next_available_position_with_size(component_size)
        elif strategy == PlacementStrategy.GRID:
            return self._find_grid_position(component)
        elif strategy == PlacementStrategy.EDGE_RIGHT:
            return self._find_edge_position("right", component)
        elif strategy == PlacementStrategy.EDGE_BOTTOM:
            return self._find_edge_position("bottom", component)
        elif strategy == PlacementStrategy.CENTER:
            return self._find_center_position(component)
        else:
            # Default to auto
            if component:
                return self._find_next_available_position(component)
            else:
                return self._find_next_available_position_with_size(component_size)

    def _estimate_component_size(
        self, component: SchematicSymbol
    ) -> Tuple[float, float]:
        """
        Estimate component size including labels using actual symbol geometry.
        """
        logger.debug(
            f"Estimating size for component {component.reference} ({component.lib_id})"
        )

        # Get actual symbol dimensions from library
        try:
            symbol_width, symbol_height = self._symbol_geometry.get_symbol_bounds(
                component.lib_id
            )
            logger.debug(
                f"Got symbol bounds: {symbol_width:.2f} x {symbol_height:.2f} mm"
            )
        except Exception as e:
            logger.warning(f"Failed to get symbol bounds for {component.lib_id}: {e}")
            # Fallback to old estimation
            pin_count = len(component.pins) if component.pins else 2
            if "Regulator" in component.lib_id or "U" in component.reference:
                symbol_width = 15.24  # 600 mil
                symbol_height = 15.24
            elif pin_count > 4:
                symbol_width = 12.7 + (pin_count * 1.27)
                symbol_height = 12.7
            else:
                symbol_width = 7.62  # 300 mil
                symbol_height = 5.08  # 200 mil

        # Calculate text dimensions
        ref_text = component.reference or "U?"
        ref_width = SymbolGeometry.calculate_text_width(ref_text, 1.27)
        ref_height = 1.27  # Font height

        value_text = component.value or ""
        value_width = (
            SymbolGeometry.calculate_text_width(value_text, 1.27) if value_text else 0
        )
        value_height = 1.27 if value_text else 0

        # Add space for pin labels
        # Estimate based on longest pin name
        max_pin_label_width = 0
        if component.pins:
            for pin in component.pins:
                if pin.name and pin.name != "~":
                    label_width = SymbolGeometry.calculate_text_width(
                        pin.name, 1.0
                    )  # Smaller font for pins
                    max_pin_label_width = max(max_pin_label_width, label_width)

        # Add padding for pin labels on both sides
        # Increased padding to ensure labels don't overlap
        pin_label_padding = (
            max_pin_label_width + 2.54 if max_pin_label_width > 0 else 2.54
        )

        # Total size calculation
        # Width: symbol width + pin label space on both sides
        width = symbol_width + (2 * pin_label_padding)

        # Height: symbol height + reference above + value below
        height = symbol_height + ref_height + 1.27 + value_height + 1.27  # Small gaps

        # Ensure text doesn't make component narrower than needed
        width = max(width, ref_width + 2.54, value_width + 2.54)

        # Log the estimation for debugging
        logger.info(
            f"Component {component.reference} ({component.lib_id}): "
            f"symbol=({symbol_width:.1f}x{symbol_height:.1f}), "
            f"max_pin_label_width={max_pin_label_width:.1f}, "
            f"pin_label_padding={pin_label_padding:.1f}, "
            f"total size=({width:.1f}x{height:.1f})"
        )

        return (width, height)

    def _estimate_sheet_size(self, sheet: Sheet) -> Tuple[float, float]:
        """
        Estimate sheet size based on pin count and name.
        Matches logic from sheet_placement.py
        """
        pin_count = len(sheet.pins)

        # Calculate height based on pin count
        PIN_SPACING = 2.54  # 100 mil between pins
        MIN_SHEET_HEIGHT = 20.32  # 0.8 inch minimum height
        SHEET_PADDING = 5.08  # 200 mil padding top/bottom

        pin_area_height = pin_count * PIN_SPACING
        height = max(MIN_SHEET_HEIGHT, pin_area_height + (2 * SHEET_PADDING))

        # Calculate width based on sheet name length
        MIN_SHEET_WIDTH = 25.4  # 1 inch minimum width
        char_width = 1.5  # mm per character
        name_width = len(sheet.name) * char_width + (2 * 2.54)  # Add margin
        width = max(MIN_SHEET_WIDTH, name_width)

        # Round to grid
        grid = 1.27  # 50 mil grid
        width = round(width / grid) * grid
        height = round(height / grid) * grid

        logger.debug(f"Sheet '{sheet.name}' with {pin_count} pins: {width}x{height}mm")

        return (width, height)

    def place_element(
        self,
        element,
        element_type: str = "component",
        strategy: PlacementStrategy = PlacementStrategy.AUTO,
    ) -> Point:
        """
        Place any schematic element (component or sheet).

        Args:
            element: SchematicSymbol or Sheet object
            element_type: "component" or "sheet"
            strategy: Placement strategy to use

        Returns:
            Point object with placement position
        """
        if element_type == "component":
            size = self._estimate_component_size(element)
        elif element_type == "sheet":
            size = self._estimate_sheet_size(element)
        else:
            raise ValueError(f"Unknown element type: {element_type}")

        # Find position using existing logic
        x, y = self.find_position(
            strategy, size, element if element_type == "component" else None
        )

        # Update element position
        element.position = Point(x, y)

        logger.info(
            f"Placed {element_type} '{getattr(element, 'reference', getattr(element, 'name', 'unknown'))}' "
            f"at ({x:.1f}, {y:.1f}) with size ({size[0]:.1f}, {size[1]:.1f})"
        )

        return element.position

    def _find_next_available_position(
        self, component: SchematicSymbol
    ) -> Tuple[float, float]:
        """
        Find the next available position with dynamic spacing based on component size.
        """
        component_size = self._estimate_component_size(component)

        # Start position
        x = self.margin
        y = self.margin
        row_start_x = self.margin

        # Get existing component bounds
        occupied_bounds = self._get_occupied_bounds()

        # Increased spacing - 200 mil (5.08mm) between bounding boxes
        spacing_x = 5.08  # 200 mil
        spacing_y = 5.08  # 200 mil

        logger.info(
            f"Dynamic placement for {component.reference}: "
            f"size=({component_size[0]:.1f}, {component_size[1]:.1f}) mm, "
            f"spacing=({spacing_x:.1f}, {spacing_y:.1f}) mm"
        )

        # Log existing components
        logger.debug(f"Existing components: {len(occupied_bounds)}")
        for i, bounds in enumerate(occupied_bounds):
            logger.debug(
                f"  Occupied[{i}]: x={bounds.x:.1f}-{bounds.right:.1f}, y={bounds.y:.1f}-{bounds.bottom:.1f}"
            )

        # Grid search for available position
        max_attempts = 1000
        attempts = 0

        while attempts < max_attempts:
            # Create bounds for current position
            test_bounds = ComponentBounds(
                x - component_size[0] / 2,
                y - component_size[1] / 2,
                component_size[0],
                component_size[1],
            )

            # Check if position is available
            collision = False
            for occupied in occupied_bounds:
                if test_bounds.overlaps(occupied):
                    collision = True
                    # If collision detected, jump past the occupied component
                    x = max(x, occupied.right + spacing_x + component_size[0] / 2)
                    logger.debug(f"Collision detected, jumping to x={x:.1f}")
                    break

            if not collision:
                # Check if component fits within sheet boundaries
                if self._check_within_bounds(
                    x, y, component_size[0], component_size[1]
                ):
                    return self._snap_to_grid((x, y))

            # Move to next position with dynamic spacing
            next_x = x + component_size[0] + spacing_x
            logger.debug(
                f"Moving from x={x:.1f} to x={next_x:.1f} (size={component_size[0]:.1f} + spacing={spacing_x:.1f})"
            )
            x = next_x

            # Wrap to next row if we exceed sheet width
            if x + component_size[0] / 2 > self.sheet_size[0] - self.margin:
                # Find the starting x position for the next row
                # This should be past any components that extend into this row
                row_start_x = self.margin
                for occupied in occupied_bounds:
                    if (
                        occupied.y <= y + component_size[1] + spacing_y
                        and occupied.bottom > y
                    ):
                        row_start_x = max(
                            row_start_x,
                            occupied.right + spacing_x + component_size[0] / 2,
                        )

                x = row_start_x
                y += component_size[1] + spacing_y
                logger.debug(f"Wrapping to next row at x={x:.1f}, y={y:.1f}")

            # Check if we've exceeded sheet height
            if y + component_size[1] / 2 > self.sheet_size[1] - self.margin:
                logger.warning(
                    f"Component {component.reference} exceeds sheet boundaries"
                )
                break

            attempts += 1

        # Fallback
        logger.warning(
            "Could not find available position with dynamic spacing, using origin"
        )
        return (self.margin, self.margin)

    def _find_next_available_position_with_size(
        self, component_size: Tuple[float, float]
    ) -> Tuple[float, float]:
        """
        Find the next available position when only size is known (no component object).
        This is a fallback method.

        Args:
            component_size: (width, height) of component

        Returns:
            (x, y) position
        """
        # Start position
        x = self.margin
        y = self.margin
        row_start_x = self.margin

        # Get existing component bounds
        occupied_bounds = self._get_occupied_bounds()

        # Increased spacing - 200 mil (5.08mm) between bounding boxes
        spacing_x = 5.08  # 200 mil
        spacing_y = 5.08  # 200 mil

        # Grid search for available position
        max_attempts = 1000
        attempts = 0

        while attempts < max_attempts:
            # Create bounds for current position
            test_bounds = ComponentBounds(
                x - component_size[0] / 2,
                y - component_size[1] / 2,
                component_size[0],
                component_size[1],
            )

            # Check if position is available
            collision = False
            for occupied in occupied_bounds:
                if test_bounds.overlaps(occupied):
                    collision = True
                    # If collision detected, jump past the occupied component
                    x = max(x, occupied.right + spacing_x + component_size[0] / 2)
                    break

            if not collision:
                # Check if component fits within sheet boundaries
                if self._check_within_bounds(
                    x, y, component_size[0], component_size[1]
                ):
                    final_pos = self._snap_to_grid((x, y))
                    comp_ref = (
                        getattr(component, "reference", "unknown")
                        if component
                        else "unknown"
                    )
                    logger.info(
                        f"Placing {comp_ref} at ({final_pos[0]:.1f}, {final_pos[1]:.1f})"
                    )
                    return final_pos
                else:
                    logger.debug(
                        f"Position ({x:.1f}, {y:.1f}) exceeds sheet boundaries"
                    )

            # Move to next position
            x += component_size[0] + spacing_x

            # Wrap to next row if we exceed sheet width
            if x + component_size[0] / 2 > self.sheet_size[0] - self.margin:
                # Find the starting x position for the next row
                row_start_x = self.margin
                for occupied in occupied_bounds:
                    if (
                        occupied.y <= y + component_size[1] + spacing_y
                        and occupied.bottom > y
                    ):
                        row_start_x = max(
                            row_start_x,
                            occupied.right + spacing_x + component_size[0] / 2,
                        )

                x = row_start_x
                y += component_size[1] + spacing_y

            # Check if we've exceeded sheet height
            if y + component_size[1] / 2 > self.sheet_size[1] - self.margin:
                logger.warning("Component exceeds sheet boundaries")
                break

            attempts += 1

        # Fallback - place at origin if no position found
        logger.warning("Could not find available position, using origin")
        return (self.margin, self.margin)

    def _find_grid_position(
        self, component: Optional[SchematicSymbol]
    ) -> Tuple[float, float]:
        """
        Find position in a regular grid pattern with dynamic spacing.

        Args:
            component: Component to place (for size estimation)

        Returns:
            (x, y) position
        """
        # Count existing components
        component_count = len(self.schematic.components)

        # Get average component size for grid spacing
        if component:
            size = self._estimate_component_size(component)
            spacing_x = size[0] + max(self.grid_size * 6, size[0] * 0.3)
            spacing_y = size[1] + max(self.grid_size * 6, size[1] * 0.3)
        else:
            # Default spacing if no component provided
            spacing_x = 40.0  # ~1.6 inch
            spacing_y = 30.0  # ~1.2 inch

        # Calculate grid position
        columns = 10  # Components per row
        row = component_count // columns
        col = component_count % columns

        x = self.margin + (col * spacing_x)
        y = self.margin + (row * spacing_y)

        return self._snap_to_grid((x, y))

    def _find_edge_position(
        self, edge: str, component: Optional[SchematicSymbol]
    ) -> Tuple[float, float]:
        """
        Find position at the specified edge with dynamic spacing.

        Args:
            edge: "right" or "bottom"
            component: Component to place (for size estimation)

        Returns:
            (x, y) position
        """
        if not self.schematic.components:
            # First component - place at margin
            return (self.margin, self.margin)

        # Get component size for spacing
        if component:
            size = self._estimate_component_size(component)
            spacing = 5.08  # 200 mil spacing
        else:
            spacing = 5.08  # 200 mil default

        if edge == "right":
            # Find rightmost component
            max_x = max(comp.position.x for comp in self.schematic.components)
            # Place to the right with dynamic spacing
            x = max_x + spacing
            # Average Y position
            avg_y = sum(comp.position.y for comp in self.schematic.components) / len(
                self.schematic.components
            )
            y = avg_y
        else:  # bottom
            # Find bottommost component
            max_y = max(comp.position.y for comp in self.schematic.components)
            # Place below with dynamic spacing
            y = max_y + spacing
            # Average X position
            avg_x = sum(comp.position.x for comp in self.schematic.components) / len(
                self.schematic.components
            )
            x = avg_x

        return self._snap_to_grid((x, y))

    def _find_center_position(
        self, component: Optional[SchematicSymbol]
    ) -> Tuple[float, float]:
        """
        Find position at the center of existing components.

        Args:
            component: Component to place (for size estimation)

        Returns:
            (x, y) position
        """
        if not self.schematic.components:
            # First component - place at reasonable center
            return (127.0, 127.0)  # ~5 inches from origin

        # Calculate center of existing components
        avg_x = sum(comp.position.x for comp in self.schematic.components) / len(
            self.schematic.components
        )
        avg_y = sum(comp.position.y for comp in self.schematic.components) / len(
            self.schematic.components
        )

        # Get component size
        if component:
            component_size = self._estimate_component_size(component)
        else:
            component_size = (20.0, 20.0)  # Default size

        # Find nearest available position to center
        center = (avg_x, avg_y)
        occupied_bounds = self._get_occupied_bounds()

        # Spiral search from center with better spacing
        spacing = 5.08  # 200 mil
        for radius in range(0, 200, int(self.grid_size * 4)):  # Step by ~10mm
            for angle in range(0, 360, 45):
                import math

                rad = math.radians(angle)
                x = center[0] + radius * math.cos(rad)
                y = center[1] + radius * math.sin(rad)

                # Create test bounds
                test_bounds = ComponentBounds(
                    x - component_size[0] / 2,
                    y - component_size[1] / 2,
                    component_size[0],
                    component_size[1],
                )

                # Check for collisions
                collision = False
                for occupied in occupied_bounds:
                    if test_bounds.overlaps(occupied):
                        collision = True
                        break

                if not collision:
                    # Check if component fits within sheet boundaries
                    if self._check_within_bounds(
                        x, y, component_size[0], component_size[1]
                    ):
                        return self._snap_to_grid((x, y))

        # Fallback
        return (
            self._find_next_available_position(component)
            if component
            else self._find_next_available_position_with_size(component_size)
        )

    def _get_occupied_bounds(self) -> List[ElementBounds]:
        """Get bounds of all placed elements (components and sheets)."""
        bounds = []

        # Add component bounds
        for comp in self.schematic.components:
            # Estimate size for existing component
            size = self._estimate_component_size(comp)

            # Create bounds centered on component position
            bounds.append(
                ElementBounds(
                    comp.position.x - size[0] / 2,
                    comp.position.y - size[1] / 2,
                    size[0],
                    size[1],
                    "component",
                )
            )

        # Add sheet bounds if sheets exist
        if hasattr(self.schematic, "sheets"):
            for sheet in self.schematic.sheets:
                # Sheets store their position as top-left corner
                bounds.append(
                    ElementBounds(
                        sheet.position.x,
                        sheet.position.y,
                        sheet.size[0],
                        sheet.size[1],
                        "sheet",
                    )
                )

        return bounds

    def _snap_to_grid(self, position: Tuple[float, float]) -> Tuple[float, float]:
        """
        Snap position to grid.

        Args:
            position: (x, y) position

        Returns:
            Grid-aligned position
        """
        x = round(position[0] / self.grid_size) * self.grid_size
        y = round(position[1] / self.grid_size) * self.grid_size
        return (x, y)

    def _check_within_bounds(
        self, x: float, y: float, width: float, height: float
    ) -> bool:
        """
        Check if an element with given dimensions fits within sheet boundaries.

        Args:
            x: X position (center)
            y: Y position (center)
            width: Element width
            height: Element height

        Returns:
            True if element fits within bounds, False otherwise
        """
        left = x - width / 2
        right = x + width / 2
        top = y - height / 2
        bottom = y + height / 2

        return (
            left >= self.margin
            and right <= self.sheet_size[0] - self.margin
            and top >= self.margin
            and bottom <= self.sheet_size[1] - self.margin
        )

    def arrange_components(
        self,
        components: List[SchematicSymbol],
        arrangement: str = "grid",
    ) -> None:
        """
        Arrange multiple components in a pattern with dynamic spacing.

        Args:
            components: Components to arrange
            arrangement: "grid", "vertical", "horizontal", "circular" or "force_directed"
        """
        if not components:
            return

        start_time = time.perf_counter()
        logger.info(
            f"ARRANGE_COMPONENTS: Starting arrangement of {len(components)} components using '{arrangement}' strategy"
        )

        if arrangement == "grid":
            self._arrange_grid(components)
        elif arrangement == "vertical":
            self._arrange_vertical(components)
        elif arrangement == "horizontal":
            self._arrange_horizontal(components)
        elif arrangement == "circular":
            self._arrange_circular(components)
        elif arrangement == "force_directed":
            # Python force-directed implementation
            logger.info("ARRANGE_COMPONENTS: Using Python force-directed placement")
            self._arrange_force_directed_python(components)
        else:
            # Default to grid
            self._arrange_grid(components)

        total_time = time.perf_counter() - start_time
        logger.info(
            f"ARRANGE_COMPONENTS: Component arrangement completed in {total_time*1000:.2f}ms"
        )

    def _arrange_force_directed_python(self, components: List[SchematicSymbol]) -> None:
        """
        Python force-directed placement algorithm.

        This is a simplified force-directed algorithm for automatic component placement.
        """
        start_time = time.perf_counter()
        logger.info(f"PYTHON_FORCE_DIRECTED: Starting Python force-directed placement")
        logger.info(f"PYTHON_FORCE_DIRECTED: Processing {len(components)} components")

        # Simple iterative placement with force calculations
        iterations = 50
        attraction_strength = 1.5
        repulsion_strength = 50.0
        damping = 0.8

        for iteration in range(iterations):
            forces = {}

            # Initialize forces
            for comp in components:
                forces[comp.reference] = [0.0, 0.0]

            # Calculate repulsion forces between all components
            for i, comp1 in enumerate(components):
                for j, comp2 in enumerate(components):
                    if i >= j:
                        continue

                    # Calculate distance
                    dx = comp2.position.x - comp1.position.x
                    dy = comp2.position.y - comp1.position.y
                    distance = max(1.0, (dx * dx + dy * dy) ** 0.5)

                    # Calculate repulsion force
                    force_magnitude = repulsion_strength / (distance * distance)
                    force_x = -force_magnitude * dx / distance
                    force_y = -force_magnitude * dy / distance

                    # Apply forces (Newton's third law)
                    forces[comp1.reference][0] += force_x
                    forces[comp1.reference][1] += force_y
                    forces[comp2.reference][0] -= force_x
                    forces[comp2.reference][1] -= force_y

            # Apply forces to update positions
            for comp in components:
                force = forces[comp.reference]

                # Apply damping
                delta_x = force[0] * damping
                delta_y = force[1] * damping

                # Update position
                new_x = comp.position.x + delta_x
                new_y = comp.position.y + delta_y

                # Keep within bounds
                new_x = max(self.margin, min(self.sheet_size[0] - self.margin, new_x))
                new_y = max(self.margin, min(self.sheet_size[1] - self.margin, new_y))

                comp.position = Point(*self._snap_to_grid((new_x, new_y)))

        python_time = time.perf_counter() - start_time
        logger.info(
            f"✅ PYTHON_FORCE_DIRECTED: Python placement completed in {python_time*1000:.2f}ms"
        )
        logger.info(f"🔄 PYTHON_FORCE_DIRECTED: Used {iterations} iterations")

    def _arrange_grid(self, components: List[SchematicSymbol]) -> None:
        """Arrange components in a grid pattern with dynamic spacing."""
        columns = int(len(components) ** 0.5) + 1

        # Calculate maximum component size for uniform grid
        max_width = 0
        max_height = 0
        for comp in components:
            size = self._estimate_component_size(comp)
            max_width = max(max_width, size[0])
            max_height = max(max_height, size[1])

        # Add increased spacing - 200 mil between components
        spacing_x = max_width + 5.08  # 200 mil
        spacing_y = max_height + 5.08  # 200 mil

        for i, comp in enumerate(components):
            row = i // columns
            col = i % columns

            x = self.margin + (col * spacing_x)
            y = self.margin + (row * spacing_y)

            comp.position = Point(*self._snap_to_grid((x, y)))

    def _arrange_vertical(self, components: List[SchematicSymbol]) -> None:
        """Arrange components vertically with dynamic spacing."""
        x = self.margin
        current_y = self.margin

        for comp in components:
            comp.position = Point(*self._snap_to_grid((x, current_y)))

            # Move to next position based on component size
            size = self._estimate_component_size(comp)
            spacing_y = size[1] + 5.08  # 200 mil spacing
            current_y += spacing_y

    def _arrange_horizontal(self, components: List[SchematicSymbol]) -> None:
        """Arrange components horizontally with dynamic spacing."""
        y = self.margin
        current_x = self.margin

        for comp in components:
            comp.position = Point(*self._snap_to_grid((current_x, y)))

            # Move to next position based on component size
            size = self._estimate_component_size(comp)
            spacing_x = size[0] + 5.08  # 200 mil spacing
            current_x += spacing_x

    def _arrange_circular(self, components: List[SchematicSymbol]) -> None:
        """Arrange components in a circle with dynamic spacing."""
        import math

        if not components:
            return

        # Calculate center and radius based on component sizes
        center_x = 127.0  # ~5 inches
        center_y = 127.0

        # Calculate total circumference needed
        total_width = 0
        for comp in components:
            size = self._estimate_component_size(comp)
            total_width += size[0] + 5.08  # 200 mil spacing

        # Calculate radius from circumference
        radius = max(50.0, total_width / (2 * math.pi))

        angle_step = 360.0 / len(components)

        for i, comp in enumerate(components):
            angle = math.radians(i * angle_step)
            x = center_x + radius * math.cos(angle)
            y = center_y + radius * math.sin(angle)

            comp.position = Point(*self._snap_to_grid((x, y)))
