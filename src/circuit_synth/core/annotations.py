# FILE: src/circuit_synth/core/annotations.py

"""
Annotation components for adding text, graphics, and other non-electrical
elements to circuit schematics.
"""

import uuid
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple


@dataclass
class TextProperty:
    """Simple text annotation for schematics."""

    text: str
    position: Tuple[float, float]  # (x, y) in mm
    size: float = 1.27  # Text size in mm (KiCad default)
    bold: bool = False
    italic: bool = False
    color: str = "black"  # Color name or hex
    rotation: int = 0  # 0, 90, 180, 270 degrees
    justify: str = "left top"  # KiCad justification
    uuid: str = None

    def __post_init__(self):
        if self.uuid is None:
            self.uuid = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        """Convert annotation to dictionary format for JSON export."""
        return {
            "type": "TextProperty",
            "text": self.text,
            "position": self.position,
            "size": self.size,
            "bold": self.bold,
            "italic": self.italic,
            "color": self.color,
            "rotation": self.rotation,
            "justify": self.justify,
            "uuid": self.uuid,
        }


@dataclass
class TextBox:
    """Text with optional background box and border."""

    text: str
    position: Tuple[float, float]  # (x, y) in mm
    size: Tuple[float, float] = (40.0, 20.0)  # (width, height) in mm
    margins: Tuple[float, float, float, float] = (
        1.0,
        1.0,
        1.0,
        1.0,
    )  # top, right, bottom, left
    text_size: float = 1.27
    bold: bool = False
    italic: bool = False
    text_color: str = "black"
    background: bool = True
    background_color: str = "white"
    border: bool = True
    border_width: float = 0.1
    border_color: str = "black"
    justify: str = "left top"
    rotation: int = 0
    uuid: str = None

    def __post_init__(self):
        if self.uuid is None:
            self.uuid = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        """Convert annotation to dictionary format for JSON export."""
        return {
            "type": "TextBox",
            "text": self.text,
            "position": self.position,
            "size": self.size,
            "margins": self.margins,
            "text_size": self.text_size,
            "bold": self.bold,
            "italic": self.italic,
            "text_color": self.text_color,
            "background": self.background,
            "background_color": self.background_color,
            "border": self.border,
            "border_width": self.border_width,
            "border_color": self.border_color,
            "justify": self.justify,
            "rotation": self.rotation,
            "uuid": self.uuid,
        }


@dataclass
class Table:
    """Tabular data display on schematic."""

    data: List[List[str]]  # List of rows, each row is list of cells
    position: Tuple[float, float]  # (x, y) in mm
    cell_width: float = 20.0  # mm
    cell_height: float = 5.0  # mm
    text_size: float = 1.0
    border: bool = True
    border_width: float = 0.1
    header_bold: bool = True
    uuid: str = None

    def __post_init__(self):
        if self.uuid is None:
            self.uuid = str(uuid.uuid4())

    def to_dict(self) -> Dict[str, Any]:
        """Convert annotation to dictionary format for JSON export."""
        return {
            "type": "Table",
            "data": self.data,
            "position": self.position,
            "cell_width": self.cell_width,
            "cell_height": self.cell_height,
            "text_size": self.text_size,
            "border": self.border,
            "border_width": self.border_width,
            "header_bold": self.header_bold,
            "uuid": self.uuid,
        }


class Graphic:
    """Factory class for creating graphic elements."""

    @staticmethod
    def rectangle(
        position: Tuple[float, float],
        width: float,
        height: float,
        style: str = "solid",
        color: str = "black",
        fill: bool = False,
        fill_color: str = "white",
    ) -> Dict[str, Any]:
        """Create a rectangle graphic element."""
        return {
            "type": "rectangle",
            "position": position,
            "width": width,
            "height": height,
            "style": style,
            "color": color,
            "fill": fill,
            "fill_color": fill_color,
            "uuid": str(uuid.uuid4()),
        }

    @staticmethod
    def circle(
        center: Tuple[float, float],
        radius: float,
        style: str = "solid",
        color: str = "black",
        fill: bool = False,
        fill_color: str = "white",
    ) -> Dict[str, Any]:
        """Create a circle graphic element."""
        return {
            "type": "circle",
            "center": center,
            "radius": radius,
            "style": style,
            "color": color,
            "fill": fill,
            "fill_color": fill_color,
            "uuid": str(uuid.uuid4()),
        }

    @staticmethod
    def line(
        start: Tuple[float, float],
        end: Tuple[float, float],
        style: str = "solid",
        color: str = "black",
        width: float = 0.1,
    ) -> Dict[str, Any]:
        """Create a line graphic element."""
        return {
            "type": "line",
            "start": start,
            "end": end,
            "style": style,
            "color": color,
            "width": width,
            "uuid": str(uuid.uuid4()),
        }


def add_text(text: str, position: Tuple[float, float], **kwargs) -> TextProperty:
    """Convenience function to create a TextProperty."""
    return TextProperty(text=text, position=position, **kwargs)


def add_text_box(text: str, position: Tuple[float, float], **kwargs) -> TextBox:
    """Convenience function to create a TextBox."""
    return TextBox(text=text, position=position, **kwargs)


def add_table(data: List[List[str]], position: Tuple[float, float], **kwargs) -> Table:
    """Convenience function to create a Table."""
    return Table(data=data, position=position, **kwargs)
