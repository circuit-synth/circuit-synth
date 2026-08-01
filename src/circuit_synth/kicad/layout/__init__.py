# -*- coding: utf-8 -*-
"""Schematic layout tooling.

Generating a schematic and laying one out well are different problems. The
generator works out what connects to what; laying it out so an engineer can
read it is a judgement call about grouping, flow and convention that an
algorithm makes badly.

This package provides the machinery for a person, or Claude, to do the layout
instead:

* :mod:`extract` reads a generated sheet and describes it - every component,
  every pin with its position and electrical type, and the nets - in a form
  compact enough to reason over.
* :mod:`spec` applies a placement decision back onto the sheet, moving symbols
  and redrawing the wires, junctions, labels and power symbols.
* :mod:`validate` checks the result against the circuit it came from, so a
  layout can never quietly change the connectivity.
* :mod:`render` turns a sheet into a PNG so the result can be looked at.
"""

from .extract import SheetDescription, describe_sheet
from .render import render_sheets
from .spec import PlacementSpec, apply_placement
from .validate import LayoutProblem, validate_layout

__all__ = [
    "SheetDescription",
    "describe_sheet",
    "PlacementSpec",
    "apply_placement",
    "LayoutProblem",
    "validate_layout",
    "render_sheets",
]
