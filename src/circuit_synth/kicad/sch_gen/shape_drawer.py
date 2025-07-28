# -*- coding: utf-8 -*-
#
# shape_drawer.py
#
# Provides helper functions to build s-expression fragments for shapes:
# rectangle, polyline, circle, arc, etc.

import logging

from sexpdata import Symbol

logger = logging.getLogger(__name__)


def rectangle_s_expr(
    start_x, start_y, end_x, end_y, stroke_width=0.254, fill_type="none"
):
    """
    Returns an S-expression for a rectangle:
      (rectangle (start x_start y_start) (end x_end y_end)
        (stroke (width stroke_width) (type default)) (fill (type fill_type)))
    """
    logger.debug(
        "Creating rectangle S-exp: start=(%.2f, %.2f), end=(%.2f, %.2f), stroke_width=%.3f, fill='%s'",
        start_x,
        start_y,
        end_x,
        end_y,
        stroke_width,
        fill_type,
    )
    return [
        Symbol("rectangle"),
        [Symbol("start"), float(start_x), float(start_y)],
        [Symbol("end"), float(end_x), float(end_y)],
        [
            Symbol("stroke"),
            [Symbol("width"), float(stroke_width)],
            [Symbol("type"), Symbol("default")],
        ],
        [Symbol("fill"), [Symbol("type"), Symbol(fill_type)]],
    ]


def polyline_s_expr(
    points, stroke_width=0.254, stroke_type="default", fill_type="none"
):
    """
    Build a (polyline ...) S-expression with:
      (polyline (pts (xy x1 y1) (xy x2 y2) ... ) (stroke ...) (fill ...))
    """
    pts_expr = []
    for x, y in points:
        pts_expr.append([Symbol("xy"), float(x), float(y)])

    return [
        Symbol("polyline"),
        [Symbol("pts")] + pts_expr,
        [
            Symbol("stroke"),
            [Symbol("width"), float(stroke_width)],
            [Symbol("type"), Symbol(stroke_type)],
        ],
        [Symbol("fill"), [Symbol("type"), Symbol(fill_type)]],
    ]


def circle_s_expr(center_x, center_y, radius, stroke_width=0.254, fill_type="none"):
    """
    (circle (center cx cy) (radius r)
      (stroke (width ...) (type default)) (fill (type ...)))
    """
    logger.debug(
        "Creating circle S-exp: center=(%.2f, %.2f), radius=%.2f, stroke_width=%.3f, fill='%s'",
        center_x,
        center_y,
        radius,
        stroke_width,
        fill_type,
    )
    return [
        Symbol("circle"),
        [Symbol("center"), float(center_x), float(center_y)],
        [Symbol("radius"), float(radius)],
        [
            Symbol("stroke"),
            [Symbol("width"), float(stroke_width)],
            [Symbol("type"), Symbol("default")],
        ],
        [Symbol("fill"), [Symbol("type"), Symbol(fill_type)]],
    ]


def arc_s_expr(start_xy, mid_xy, end_xy, stroke_width=0.254):
    """
    Build a (arc ...) S-expression with:
      (arc (start x1 y1) (mid xm ym) (end x2 y2) (stroke ...))
    """
    logger.debug(
        "Creating arc S-exp: start=(%.2f,%.2f), mid=(%.2f,%.2f), end=(%.2f,%.2f), stroke_width=%.3f",
        start_xy[0],
        start_xy[1],
        mid_xy[0],
        mid_xy[1],
        end_xy[0],
        end_xy[1],
        stroke_width,
    )
    return [
        Symbol("arc"),
        [Symbol("start"), float(start_xy[0]), float(start_xy[1])],
        [Symbol("mid"), float(mid_xy[0]), float(mid_xy[1])],  # Include midpoint
        [Symbol("end"), float(end_xy[0]), float(end_xy[1])],
        [
            Symbol("stroke"),
            [Symbol("width"), float(stroke_width)],
            [Symbol("type"), Symbol("default")],
        ],
    ]
