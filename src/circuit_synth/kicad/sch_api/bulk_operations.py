"""
Bulk Operations for KiCad Schematic API.

Provides operations that can be performed on multiple components at once,
such as moving groups, aligning components, and batch property updates.
"""

import logging
from dataclasses import dataclass
from typing import Any, Callable, Dict, List, Optional, Tuple, Union

from ..sch_editor.schematic_reader import SchematicSymbol
from .models import AlignmentOptions, MoveOptions, WireStyle
from .placement_engine import PlacementEngine

logger = logging.getLogger(__name__)


@dataclass
class GroupBounds:
    """Bounding box for a group of components."""

    min_x: float
    min_y: float
    max_x: float
    max_y: float
    center_x: float
    center_y: float
    width: float
    height: float


class BulkOperations:
    """
    Handle operations on multiple components.

    This class provides methods for performing operations on groups of components,
    such as moving, aligning, and updating properties in bulk.
    """

    # Default spacing for alignment operations (in mm)
    DEFAULT_SPACING = 25.4  # 1000 mil
    GRID_SIZE = 2.54  # 100 mil

    def __init__(self, component_manager):
        """
        Initialize bulk operations with a component manager.

        Args:
            component_manager: The ComponentManager instance
        """
        self.component_manager = component_manager
        self.placement_engine = PlacementEngine()

    def move_components(
        self,
        components: List[SchematicSymbol],
        delta: Tuple[float, float],
        maintain_relative_positions: bool = True,
        options: Optional[MoveOptions] = None,
    ) -> Dict[str, Any]:
        """
        Move multiple components together.

        Args:
            components: List of components to move
            delta: (dx, dy) offset to move by
            maintain_relative_positions: Whether to keep components' relative positions
            options: Move options for wire handling, etc.

        Returns:
            Dictionary with move results and statistics
        """
        if not components:
            return {"success": True, "moved_count": 0}

        if options is None:
            options = MoveOptions()

        results = {"success": True, "moved_count": 0, "errors": [], "warnings": []}

        if maintain_relative_positions:
            # Move as a group - simple translation
            for component in components:
                if not component.position:
                    results["warnings"].append(
                        f"Component {component.reference} has no position"
                    )
                    continue

                try:
                    # Calculate new position
                    new_x = component.position[0] + delta[0]
                    new_y = component.position[1] + delta[1]
                    new_position = (new_x, new_y)

                    # Use component manager to move (handles wire updates, etc.)
                    move_result = self.component_manager.move_component(
                        component.reference, new_position, options
                    )

                    if move_result.success:
                        results["moved_count"] += 1
                    else:
                        results["errors"].append(
                            f"Failed to move {component.reference}: {move_result.error}"
                        )

                except Exception as e:
                    results["errors"].append(
                        f"Error moving {component.reference}: {str(e)}"
                    )
                    results["success"] = False
        else:
            # Rearrange with auto-placement
            self._rearrange_components(components, delta, results)

        return results

    def align_components(
        self,
        components: List[SchematicSymbol],
        alignment: str = "horizontal",
        spacing: Optional[float] = None,
        reference_component: Optional[SchematicSymbol] = None,
    ) -> Dict[str, Any]:
        """
        Align components in a row or column.

        Args:
            components: Components to align
            alignment: 'horizontal', 'vertical', or 'grid'
            spacing: Distance between components (uses default if None)
            reference_component: Component to use as alignment reference

        Returns:
            Dictionary with alignment results
        """
        if not components:
            return {"success": True, "aligned_count": 0}

        if spacing is None:
            spacing = self.DEFAULT_SPACING

        results = {
            "success": True,
            "aligned_count": 0,
            "errors": [],
            "original_positions": {},
        }

        # Store original positions
        for comp in components:
            if comp.position:
                results["original_positions"][comp.reference] = comp.position

        # Filter components with positions
        positioned_components = [c for c in components if c.position]
        if not positioned_components:
            results["errors"].append("No components with positions to align")
            return results

        if alignment == "horizontal":
            self._align_horizontal(
                positioned_components, spacing, reference_component, results
            )
        elif alignment == "vertical":
            self._align_vertical(
                positioned_components, spacing, reference_component, results
            )
        elif alignment == "grid":
            self._align_grid(positioned_components, spacing, results)
        else:
            results["errors"].append(f"Unknown alignment type: {alignment}")
            results["success"] = False

        return results

    def update_property_bulk(
        self,
        components: List[SchematicSymbol],
        property_name: str,
        property_value: Union[str, Callable[[SchematicSymbol], str]],
        create_if_missing: bool = True,
    ) -> Dict[str, Any]:
        """
        Update a property on multiple components.

        Args:
            components: Components to update
            property_name: Name of the property to update
            property_value: New value (string or function that returns value based on component)
            create_if_missing: Whether to create the property if it doesn't exist

        Returns:
            Dictionary with update results
        """
        results = {"success": True, "updated_count": 0, "errors": [], "changes": {}}

        for component in components:
            try:
                # Determine value
                if callable(property_value):
                    value = property_value(component)
                else:
                    value = property_value

                # Store old value
                old_value = component.properties.get(property_name)

                # Update property
                success = self.component_manager.update_component_property(
                    component.reference, property_name, value, create_if_missing
                )

                if success:
                    results["updated_count"] += 1
                    results["changes"][component.reference] = {
                        "old": old_value,
                        "new": value,
                    }
                else:
                    results["errors"].append(
                        f"Failed to update {property_name} on {component.reference}"
                    )

            except Exception as e:
                results["errors"].append(
                    f"Error updating {component.reference}: {str(e)}"
                )
                results["success"] = False

        return results

    def distribute_evenly(
        self,
        components: List[SchematicSymbol],
        direction: str = "horizontal",
        bounds: Optional[Tuple[float, float, float, float]] = None,
    ) -> Dict[str, Any]:
        """
        Distribute components evenly within bounds.

        Args:
            components: Components to distribute
            direction: 'horizontal' or 'vertical'
            bounds: Optional (x1, y1, x2, y2) bounds, uses component bounds if None

        Returns:
            Dictionary with distribution results
        """
        if len(components) < 2:
            return {
                "success": True,
                "message": "Need at least 2 components to distribute",
            }

        results = {"success": True, "distributed_count": 0, "errors": []}

        # Get components with positions
        positioned = [c for c in components if c.position]
        if len(positioned) < 2:
            results["errors"].append("Need at least 2 positioned components")
            results["success"] = False
            return results

        # Calculate bounds if not provided
        if bounds is None:
            group_bounds = self._calculate_group_bounds(positioned)
            bounds = (
                group_bounds.min_x,
                group_bounds.min_y,
                group_bounds.max_x,
                group_bounds.max_y,
            )

        # Sort components by current position
        if direction == "horizontal":
            positioned.sort(key=lambda c: c.position[0])
            total_space = bounds[2] - bounds[0]
            spacing = total_space / (len(positioned) - 1)

            for i, comp in enumerate(positioned):
                new_x = bounds[0] + (i * spacing)
                new_y = comp.position[1]  # Keep Y unchanged
                new_pos = self.placement_engine.snap_to_grid((new_x, new_y))

                try:
                    move_result = self.component_manager.move_component(
                        comp.reference, new_pos
                    )
                    if move_result.success:
                        results["distributed_count"] += 1
                except Exception as e:
                    results["errors"].append(f"Error moving {comp.reference}: {str(e)}")

        else:  # vertical
            positioned.sort(key=lambda c: c.position[1])
            total_space = bounds[3] - bounds[1]
            spacing = total_space / (len(positioned) - 1)

            for i, comp in enumerate(positioned):
                new_x = comp.position[0]  # Keep X unchanged
                new_y = bounds[1] + (i * spacing)
                new_pos = self.placement_engine.snap_to_grid((new_x, new_y))

                try:
                    move_result = self.component_manager.move_component(
                        comp.reference, new_pos
                    )
                    if move_result.success:
                        results["distributed_count"] += 1
                except Exception as e:
                    results["errors"].append(f"Error moving {comp.reference}: {str(e)}")

        return results

    def rotate_group(
        self,
        components: List[SchematicSymbol],
        angle: float,
        center: Optional[Tuple[float, float]] = None,
    ) -> Dict[str, Any]:
        """
        Rotate a group of components around a center point.

        Args:
            components: Components to rotate
            angle: Rotation angle in degrees (90, 180, 270)
            center: Center of rotation (uses group center if None)

        Returns:
            Dictionary with rotation results
        """
        if angle not in [90, 180, 270]:
            return {"success": False, "error": "Angle must be 90, 180, or 270 degrees"}

        results = {"success": True, "rotated_count": 0, "errors": []}

        # Get positioned components
        positioned = [c for c in components if c.position]
        if not positioned:
            return {"success": True, "rotated_count": 0}

        # Calculate center if not provided
        if center is None:
            bounds = self._calculate_group_bounds(positioned)
            center = (bounds.center_x, bounds.center_y)

        # Rotate each component
        import math

        angle_rad = math.radians(angle)
        cos_a = math.cos(angle_rad)
        sin_a = math.sin(angle_rad)

        for comp in positioned:
            try:
                # Translate to origin
                rel_x = comp.position[0] - center[0]
                rel_y = comp.position[1] - center[1]

                # Rotate
                new_rel_x = rel_x * cos_a - rel_y * sin_a
                new_rel_y = rel_x * sin_a + rel_y * cos_a

                # Translate back
                new_x = new_rel_x + center[0]
                new_y = new_rel_y + center[1]

                # Update position
                new_pos = self.placement_engine.snap_to_grid((new_x, new_y))

                # Also update component rotation
                current_rotation = comp.position[2] if len(comp.position) > 2 else 0
                new_rotation = (current_rotation + angle) % 360

                # Move and rotate
                move_result = self.component_manager.move_component(
                    comp.reference, new_pos
                )

                if move_result.success:
                    # Update rotation
                    comp.position = (new_pos[0], new_pos[1], new_rotation)
                    results["rotated_count"] += 1
                else:
                    results["errors"].append(
                        f"Failed to rotate {comp.reference}: {move_result.error}"
                    )

            except Exception as e:
                results["errors"].append(f"Error rotating {comp.reference}: {str(e)}")
                results["success"] = False

        return results

    def mirror_group(
        self,
        components: List[SchematicSymbol],
        axis: str = "vertical",
        axis_position: Optional[float] = None,
    ) -> Dict[str, Any]:
        """
        Mirror a group of components across an axis.

        Args:
            components: Components to mirror
            axis: 'vertical' or 'horizontal'
            axis_position: Position of mirror axis (uses group center if None)

        Returns:
            Dictionary with mirror results
        """
        results = {"success": True, "mirrored_count": 0, "errors": []}

        # Get positioned components
        positioned = [c for c in components if c.position]
        if not positioned:
            return {"success": True, "mirrored_count": 0}

        # Calculate axis position if not provided
        if axis_position is None:
            bounds = self._calculate_group_bounds(positioned)
            axis_position = bounds.center_x if axis == "vertical" else bounds.center_y

        for comp in positioned:
            try:
                if axis == "vertical":
                    # Mirror across vertical axis (flip horizontally)
                    new_x = 2 * axis_position - comp.position[0]
                    new_y = comp.position[1]
                else:
                    # Mirror across horizontal axis (flip vertically)
                    new_x = comp.position[0]
                    new_y = 2 * axis_position - comp.position[1]

                new_pos = self.placement_engine.snap_to_grid((new_x, new_y))

                # Move component
                move_result = self.component_manager.move_component(
                    comp.reference, new_pos
                )

                if move_result.success:
                    # Update mirror property
                    comp.properties["mirror"] = axis[0]  # 'v' or 'h'
                    results["mirrored_count"] += 1
                else:
                    results["errors"].append(
                        f"Failed to mirror {comp.reference}: {move_result.error}"
                    )

            except Exception as e:
                results["errors"].append(f"Error mirroring {comp.reference}: {str(e)}")
                results["success"] = False

        return results

    def _calculate_group_bounds(self, components: List[SchematicSymbol]) -> GroupBounds:
        """Calculate the bounding box of a group of components."""
        if not components:
            return GroupBounds(0, 0, 0, 0, 0, 0, 0, 0)

        # Initialize with first component
        first_pos = components[0].position
        min_x = max_x = first_pos[0]
        min_y = max_y = first_pos[1]

        # Find bounds
        for comp in components[1:]:
            if comp.position:
                min_x = min(min_x, comp.position[0])
                max_x = max(max_x, comp.position[0])
                min_y = min(min_y, comp.position[1])
                max_y = max(max_y, comp.position[1])

        width = max_x - min_x
        height = max_y - min_y
        center_x = (min_x + max_x) / 2
        center_y = (min_y + max_y) / 2

        return GroupBounds(
            min_x, min_y, max_x, max_y, center_x, center_y, width, height
        )

    def _align_horizontal(
        self,
        components: List[SchematicSymbol],
        spacing: float,
        reference: Optional[SchematicSymbol],
        results: Dict,
    ) -> None:
        """Align components horizontally."""
        # Sort by current X position
        components.sort(key=lambda c: c.position[0])

        # Determine base position
        if reference and reference in components:
            base_y = reference.position[1]
            start_x = reference.position[0]
            start_index = components.index(reference)
        else:
            # Use average Y position
            base_y = sum(c.position[1] for c in components) / len(components)
            start_x = components[0].position[0]
            start_index = 0

        # Align components
        for i, comp in enumerate(components):
            offset = i - start_index
            new_x = start_x + (offset * spacing)
            new_pos = self.placement_engine.snap_to_grid((new_x, base_y))

            try:
                move_result = self.component_manager.move_component(
                    comp.reference, new_pos
                )
                if move_result.success:
                    results["aligned_count"] += 1
            except Exception as e:
                results["errors"].append(f"Error aligning {comp.reference}: {str(e)}")

    def _align_vertical(
        self,
        components: List[SchematicSymbol],
        spacing: float,
        reference: Optional[SchematicSymbol],
        results: Dict,
    ) -> None:
        """Align components vertically."""
        # Sort by current Y position
        components.sort(key=lambda c: c.position[1])

        # Determine base position
        if reference and reference in components:
            base_x = reference.position[0]
            start_y = reference.position[1]
            start_index = components.index(reference)
        else:
            # Use average X position
            base_x = sum(c.position[0] for c in components) / len(components)
            start_y = components[0].position[1]
            start_index = 0

        # Align components
        for i, comp in enumerate(components):
            offset = i - start_index
            new_y = start_y + (offset * spacing)
            new_pos = self.placement_engine.snap_to_grid((base_x, new_y))

            try:
                move_result = self.component_manager.move_component(
                    comp.reference, new_pos
                )
                if move_result.success:
                    results["aligned_count"] += 1
            except Exception as e:
                results["errors"].append(f"Error aligning {comp.reference}: {str(e)}")

    def _align_grid(
        self, components: List[SchematicSymbol], spacing: float, results: Dict
    ) -> None:
        """Align components in a grid pattern."""
        if not components:
            return

        # Calculate grid dimensions
        count = len(components)
        cols = int(count**0.5)
        rows = (count + cols - 1) // cols

        # Find starting position
        bounds = self._calculate_group_bounds(components)
        start_x = bounds.min_x
        start_y = bounds.min_y

        # Place components in grid
        for i, comp in enumerate(components):
            row = i // cols
            col = i % cols

            new_x = start_x + (col * spacing)
            new_y = start_y + (row * spacing)
            new_pos = self.placement_engine.snap_to_grid((new_x, new_y))

            try:
                move_result = self.component_manager.move_component(
                    comp.reference, new_pos
                )
                if move_result.success:
                    results["aligned_count"] += 1
            except Exception as e:
                results["errors"].append(f"Error aligning {comp.reference}: {str(e)}")

    def _rearrange_components(
        self,
        components: List[SchematicSymbol],
        delta: Tuple[float, float],
        results: Dict,
    ) -> None:
        """Rearrange components with auto-placement."""
        # This would use the placement engine to find new positions
        # for all components, maintaining some logical grouping
        # For now, just move them with the delta
        for comp in components:
            if comp.position:
                new_pos = (comp.position[0] + delta[0], comp.position[1] + delta[1])
                new_pos = self.placement_engine.snap_to_grid(new_pos)

                try:
                    move_result = self.component_manager.move_component(
                        comp.reference, new_pos
                    )
                    if move_result.success:
                        results["moved_count"] += 1
                except Exception as e:
                    results["errors"].append(f"Error moving {comp.reference}: {str(e)}")
