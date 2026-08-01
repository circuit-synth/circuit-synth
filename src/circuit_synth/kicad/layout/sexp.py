# -*- coding: utf-8 -*-
"""Minimal S-expression splicing for KiCad schematic files.

The layout tools change a few coordinates and replace the wiring, and leave
everything else exactly as it was. Parsing to a tree and writing it back would
reformat the whole file and lose the generator's output verbatim, so the edits
are made on the text with matched parentheses instead.
"""

import re
from typing import Iterator, List, Optional, Tuple


def find_block(text: str, start: int) -> Tuple[int, int]:
    """Find the extent of the parenthesised block beginning at ``start``.

    Args:
        text: The file contents.
        start: Index of the opening parenthesis.

    Returns:
        A ``(start, end)`` pair where ``end`` is one past the closing
        parenthesis.

    Raises:
        ValueError: If the parentheses do not balance.
    """
    if text[start] != "(":
        raise ValueError(f"expected '(' at {start}, found {text[start]!r}")

    depth = 0
    in_string = False
    index = start
    while index < len(text):
        character = text[index]
        if in_string:
            if character == "\\":
                index += 2
                continue
            if character == '"':
                in_string = False
        elif character == '"':
            in_string = True
        elif character == "(":
            depth += 1
        elif character == ")":
            depth -= 1
            if depth == 0:
                return start, index + 1
        index += 1

    raise ValueError("unbalanced parentheses")


def iter_blocks(text: str, keyword: str, depth: int = 1) -> Iterator[Tuple[int, int]]:
    """Yield the extent of every block with the given keyword at one depth.

    Args:
        text: The file contents.
        keyword: The block keyword, such as ``"symbol"`` or ``"wire"``.
        depth: Nesting depth to search at. Top level inside ``kicad_sch`` is 1.

    Yields:
        ``(start, end)`` pairs, in file order.
    """
    pattern = re.compile(
        r"\n" + "\t" * depth + r"(\()" + re.escape(keyword) + r"[\s\)]"
    )
    for match in pattern.finditer(text):
        yield find_block(text, match.start(1))


def block_text(text: str, extent: Tuple[int, int]) -> str:
    """Return the text of a block.

    Args:
        text: The file contents.
        extent: A ``(start, end)`` pair.

    Returns:
        The block's text.
    """
    return text[extent[0] : extent[1]]


def read_string(block: str, keyword: str) -> Optional[str]:
    """Read the first quoted value of a keyword inside a block.

    Args:
        block: The block text.
        keyword: The keyword to look for, such as ``"lib_id"``.

    Returns:
        The quoted value, or None when the keyword is absent.
    """
    match = re.search(rf'\({re.escape(keyword)}\s+"([^"]*)"', block)
    return match.group(1) if match else None


def read_property(block: str, name: str) -> Optional[str]:
    """Read a symbol property's value.

    Args:
        block: The symbol block text.
        name: The property name, such as ``"Reference"``.

    Returns:
        The property value, or None when the property is absent.
    """
    match = re.search(rf'\(property\s+"{re.escape(name)}"\s+"([^"]*)"', block)
    return match.group(1) if match else None


def read_position(block: str) -> Optional[Tuple[float, float, float]]:
    """Read a block's own ``(at x y [angle])``.

    Args:
        block: The block text.

    Returns:
        An ``(x, y, angle)`` triple, or None when there is no position.
    """
    match = re.search(r"\(at\s+(-?[\d.]+)\s+(-?[\d.]+)(?:\s+(-?[\d.]+))?\s*\)", block)
    if not match:
        return None
    angle = float(match.group(3)) if match.group(3) is not None else 0.0
    return float(match.group(1)), float(match.group(2)), angle


def replace_positions(block: str, dx: float, dy: float, angle: Optional[float]) -> str:
    """Move every ``(at ...)`` in a block by an offset.

    Moving the symbol and its property text together keeps the reference and
    value where the symbol's author put them relative to the body.

    Args:
        block: The block text.
        dx: Distance to move in x, in mm.
        dy: Distance to move in y, in mm.
        angle: New angle for the block's own position, or None to keep it.

    Returns:
        The updated block text.
    """
    seen = [False]

    def shift(match: "re.Match[str]") -> str:
        x = round(float(match.group(1)) + dx, 4)
        y = round(float(match.group(2)) + dy, 4)
        rotation = match.group(3)
        if not seen[0]:
            seen[0] = True
            if angle is not None:
                rotation = f"{angle:g}"
        tail = f" {rotation}" if rotation is not None else ""
        return f"(at {x:g} {y:g}{tail})"

    return re.sub(
        r"\(at\s+(-?[\d.]+)\s+(-?[\d.]+)(?:\s+(-?[\d.]+))?\s*\)", shift, block
    )


def strip_blocks(text: str, keywords: List[str]) -> str:
    """Remove every top-level block with any of the given keywords.

    Args:
        text: The file contents.
        keywords: Block keywords to remove.

    Returns:
        The text with those blocks removed.
    """
    extents: List[Tuple[int, int]] = []
    for keyword in keywords:
        extents.extend(iter_blocks(text, keyword))

    result = text
    for start, end in sorted(extents, reverse=True):
        # Take the newline and indentation in front of the block with it.
        line_start = result.rfind("\n", 0, start)
        result = result[:line_start] + result[end:]
    return result


def insert_before_end(text: str, addition: str) -> str:
    """Insert new top-level content just before the file's closing parenthesis.

    Args:
        text: The file contents.
        addition: The text to insert.

    Returns:
        The updated file contents.
    """
    if not addition:
        return text
    closing = text.rstrip().rfind(")")
    return text[:closing] + addition + text[closing:]
