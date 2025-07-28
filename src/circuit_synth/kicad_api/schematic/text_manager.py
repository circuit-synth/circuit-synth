"""
Text annotation management for KiCad schematics.
Provides add, remove, update, and search operations for text annotations.
"""

import logging
import uuid
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple

from ..core.types import Point, Schematic, Text
from .connection_utils import points_equal, snap_to_grid

logger = logging.getLogger(__name__)


class TextManager:
    """
    Manages text annotations in a KiCad schematic.
    Provides high-level operations for adding, removing, and manipulating text.
    """

    def __init__(self, schematic: Schematic):
        """
        Initialize text manager with a schematic.

        Args:
            schematic: The schematic to manage
        """
        self.schematic = schematic
        self._text_index = self._build_text_index()

    def _build_text_index(self) -> Dict[str, Text]:
        """Build an index of texts by UUID for fast lookup."""
        return {text.uuid: text for text in self.schematic.texts}

    def _generate_uuid(self) -> str:
        """Generate a new UUID for a text."""
        return str(uuid.uuid4())

    def add_text(
        self,
        content: str,
        position: Tuple[float, float],
        size: float = 1.27,
        orientation: int = 0,
        snap_points: bool = True,
        effects: Optional[Dict[str, Any]] = None,
    ) -> Optional[Text]:
        """
        Add a text annotation to the schematic.

        Args:
            content: Text content (supports multi-line with \\n)
            position: (x, y) position
            size: Text size in mm
            orientation: Rotation angle (0, 90, 180, 270)
            snap_points: Whether to snap position to grid
            effects: Optional text effects (font, style, etc.)

        Returns:
            Created text or None if invalid
        """
        if not content:
            logger.error("Text content cannot be empty")
            return None

        # Validate orientation
        if orientation not in [0, 90, 180, 270]:
            logger.error(
                f"Invalid orientation {orientation}, must be 0, 90, 180, or 270"
            )
            return None

        # Validate size
        if size <= 0:
            logger.error(f"Invalid text size {size}, must be positive")
            return None

        # Convert position to Point and optionally snap to grid
        x, y = position
        if snap_points:
            x, y = snap_to_grid((x, y))
        text_position = Point(x, y)

        # Create text
        text = Text(
            content=content,
            position=text_position,
            orientation=orientation,
            size=size,
            effects=effects,
            uuid=self._generate_uuid(),
        )

        # Add to schematic
        self.schematic.add_text(text)
        self._text_index[text.uuid] = text

        logger.info(f"Added text annotation at ({x}, {y})")
        return text

    def remove_text(self, text_uuid: str) -> bool:
        """
        Remove a text annotation from the schematic.

        Args:
            text_uuid: UUID of text to remove

        Returns:
            True if removed, False if not found
        """
        text = self._text_index.get(text_uuid)
        if not text:
            logger.warning(f"Text {text_uuid} not found")
            return False

        # Remove from schematic
        self.schematic.texts.remove(text)
        del self._text_index[text_uuid]

        logger.info(f"Removed text annotation")
        return True

    def update_text(self, text_uuid: str, **properties) -> bool:
        """
        Update text properties.

        Args:
            text_uuid: UUID of text to update
            **properties: Properties to update (content, position, size, etc.)

        Returns:
            True if updated, False if not found
        """
        text = self._text_index.get(text_uuid)
        if not text:
            logger.warning(f"Text {text_uuid} not found")
            return False

        # Update properties
        for key, value in properties.items():
            if hasattr(text, key):
                if key == "position" and isinstance(value, tuple):
                    # Convert tuple to Point
                    x, y = value
                    if properties.get("snap_points", True):
                        x, y = snap_to_grid((x, y))
                    value = Point(x, y)
                elif key == "orientation":
                    # Validate orientation
                    if value not in [0, 90, 180, 270]:
                        logger.error(f"Invalid orientation {value}")
                        continue
                elif key == "size":
                    # Validate size
                    if value <= 0:
                        logger.error(f"Invalid size {value}")
                        continue

                setattr(text, key, value)
                logger.debug(f"Updated text {key} to {value}")

        return True

    def find_text_at_point(
        self, point: Tuple[float, float], tolerance: float = 0.1
    ) -> List[Text]:
        """
        Find text annotations at or near a specific point.

        Args:
            point: (x, y) coordinates to search
            tolerance: Distance tolerance for matching

        Returns:
            List of texts at or near the point
        """
        test_point = Point(*point)
        matching_texts = []

        for text in self.schematic.texts:
            if points_equal(text.position, test_point, tolerance):
                matching_texts.append(text)

        return matching_texts

    def find_text_by_content(
        self, pattern: str, exact_match: bool = False
    ) -> List[Text]:
        """
        Find text annotations by content pattern.

        Args:
            pattern: Content pattern to search for
            exact_match: If True, require exact match; if False, substring match

        Returns:
            List of matching texts
        """
        matching_texts = []

        for text in self.schematic.texts:
            if exact_match:
                if text.content == pattern:
                    matching_texts.append(text)
            else:
                if pattern.lower() in text.content.lower():
                    matching_texts.append(text)

        return matching_texts

    def align_texts(
        self, text_uuids: List[str], alignment: str = "left", spacing: float = 2.54
    ) -> bool:
        """
        Align multiple text annotations.

        Args:
            text_uuids: List of text UUIDs to align
            alignment: Alignment type ("left", "right", "top", "bottom", "center")
            spacing: Spacing between texts (for vertical/horizontal distribution)

        Returns:
            True if aligned, False if any text not found
        """
        # Get all texts
        texts = []
        for uuid in text_uuids:
            text = self._text_index.get(uuid)
            if not text:
                logger.warning(f"Text {uuid} not found")
                return False
            texts.append(text)

        if len(texts) < 2:
            logger.warning("Need at least 2 texts to align")
            return True

        # Sort texts by position for consistent ordering
        texts.sort(key=lambda t: (t.position.y, t.position.x))

        if alignment == "left":
            # Align to leftmost text
            min_x = min(t.position.x for t in texts)
            for text in texts:
                text.position.x = min_x

        elif alignment == "right":
            # Align to rightmost text
            max_x = max(t.position.x for t in texts)
            for text in texts:
                text.position.x = max_x

        elif alignment == "top":
            # Align to topmost text
            min_y = min(t.position.y for t in texts)
            for text in texts:
                text.position.y = min_y

        elif alignment == "bottom":
            # Align to bottommost text
            max_y = max(t.position.y for t in texts)
            for text in texts:
                text.position.y = max_y

        elif alignment == "center":
            # Center horizontally
            avg_x = sum(t.position.x for t in texts) / len(texts)
            for text in texts:
                text.position.x = avg_x

        elif alignment == "distribute_horizontal":
            # Distribute horizontally with equal spacing
            min_x = min(t.position.x for t in texts)
            for i, text in enumerate(texts):
                text.position.x = min_x + (i * spacing)

        elif alignment == "distribute_vertical":
            # Distribute vertically with equal spacing
            min_y = min(t.position.y for t in texts)
            for i, text in enumerate(texts):
                text.position.y = min_y + (i * spacing)

        else:
            logger.error(f"Unknown alignment type: {alignment}")
            return False

        logger.info(f"Aligned {len(texts)} texts with {alignment} alignment")
        return True

    def add_multiline_text(
        self,
        lines: List[str],
        position: Tuple[float, float],
        line_spacing: float = 1.5,
        size: float = 1.27,
        orientation: int = 0,
    ) -> List[Text]:
        """
        Add multiple lines of text as separate text objects.

        Args:
            lines: List of text lines
            position: Starting position for first line
            line_spacing: Spacing between lines (in mm)
            size: Text size
            orientation: Text orientation

        Returns:
            List of created text objects
        """
        created_texts = []
        x, y = position

        for i, line in enumerate(lines):
            if not line.strip():
                continue

            # Calculate position for this line
            if orientation == 0 or orientation == 180:
                # Horizontal text - adjust Y position
                line_y = y + (i * line_spacing * (1 if orientation == 0 else -1))
                line_position = (x, line_y)
            else:
                # Vertical text - adjust X position
                line_x = x + (i * line_spacing * (1 if orientation == 90 else -1))
                line_position = (line_x, y)

            text = self.add_text(
                content=line, position=line_position, size=size, orientation=orientation
            )

            if text:
                created_texts.append(text)

        return created_texts

    def get_text_by_uuid(self, text_uuid: str) -> Optional[Text]:
        """Get a text by its UUID."""
        return self._text_index.get(text_uuid)

    def get_all_texts(self) -> List[Text]:
        """Get all text annotations in the schematic."""
        return list(self.schematic.texts)
