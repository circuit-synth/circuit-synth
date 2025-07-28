"""
Component grouping utilities for hierarchical placement.
"""

from typing import Dict, List

from .base import ComponentWrapper
from .bbox import BoundingBox


class ComponentGroup(list):
    """Group of components at the same hierarchical level."""

    def __init__(self, components: List[ComponentWrapper] = None):
        super().__init__(components or [])
        self._hierarchical_level = None

    @property
    def bbox(self) -> BoundingBox:
        """Get the bounding box that encompasses all components in the group."""
        if not self:
            # Return a minimal bbox for empty groups
            return BoundingBox(0, 0, 0, 0)

        # Start with the first component's bbox
        bbox = self[0].bbox

        # Merge with all other component bboxes
        for component in self[1:]:
            bbox = bbox.merge(component.bbox)

        return bbox

    @property
    def hierarchical_level(self) -> str:
        """Get the hierarchical level of this group."""
        if self._hierarchical_level is None and self:
            # Extract from the first component
            self._hierarchical_level = self[0].hierarchical_path
        return self._hierarchical_level or ""

    @hierarchical_level.setter
    def hierarchical_level(self, value: str):
        """Set the hierarchical level of this group."""
        self._hierarchical_level = value

    def move(self, dx: float, dy: float):
        """Move all components in the group by the given offset."""
        for component in self:
            if isinstance(component, ComponentGroup):
                # Recursively move nested groups
                component.move(dx, dy)
            elif hasattr(component, "is_locked") and not component.is_locked:
                # Move individual components
                current_x = component.footprint.position.x
                current_y = component.footprint.position.y
                component.move_to(current_x + dx, current_y + dy)

    def set_bottom_left(self, x: float, y: float):
        """Set the position of the group based on its bottom-left corner."""
        if not self:
            return

        # Get current bottom-left
        current_bl = self.bbox.bottom_left()

        # Calculate offset
        dx = x - current_bl[0]
        dy = y - current_bl[1]

        # Move all components
        self.move(dx, dy)

    @property
    def area(self) -> float:
        """Get the total area of the group's bounding box."""
        return self.bbox.area()

    @property
    def is_locked(self) -> bool:
        """Check if all components in the group are locked."""
        return all(c.is_locked for c in self)

    def touches(self, other: "ComponentGroup") -> bool:
        """Check if this group's bounding box touches another group's."""
        # Slightly shrink the bounding boxes to avoid false positives
        bbox1 = self.bbox.inflate(-0.01)
        bbox2 = other.bbox.inflate(-0.01)
        return bbox1.intersects(bbox2)


def group_by_hierarchy(components: List[ComponentWrapper]) -> Dict[str, ComponentGroup]:
    """
    Group components by their hierarchical level.

    Args:
        components: List of component wrappers to group

    Returns:
        Dictionary mapping hierarchical paths to component groups
    """
    groups = {}

    for component in components:
        if component.is_locked:
            continue

        level = component.hierarchical_path

        if level not in groups:
            groups[level] = ComponentGroup()
            groups[level].hierarchical_level = level

        groups[level].append(component)

    return groups


def group_groups(groups: Dict[str, ComponentGroup]) -> Dict[str, ComponentGroup]:
    """
    Group component groups by the next level up in the hierarchy.

    This is used to recursively pack groups of groups.

    Args:
        groups: Dictionary of component groups

    Returns:
        Dictionary of super-groups
    """
    super_groups = {}

    for path, group in groups.items():
        # Get parent path by removing last segment
        if "/" in path:
            parent_path = "/".join(path.split("/")[:-1])
        else:
            # Top level - use empty string
            parent_path = ""

        if parent_path not in super_groups:
            super_groups[parent_path] = ComponentGroup()
            super_groups[parent_path].hierarchical_level = parent_path

        # Treat the group as a single entity
        super_groups[parent_path].append(group)

    return super_groups
