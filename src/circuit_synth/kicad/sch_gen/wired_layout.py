# -*- coding: utf-8 -*-
"""Wired schematic layout.

Places the components of one sheet and connects them with drawn wires instead
of relying on a net label at every pin. The layout follows the conventions of a
hand-drawn schematic:

* Components that share a signal net form a group, and groups are spaced evenly
  down the sheet so unrelated circuitry does not intermingle.
* Two-pin passives in series become a horizontal chain at a constant pitch,
  wired end to end through a node between each pair.
* A passive with one end on a power rail hangs below the node it decouples,
  with its power symbol underneath and a junction where it meets the chain.
* Ground and the supply rails always render as power symbols at the pin. They
  are never wired across the sheet and never become labels.
* Anything whose geometry does not fit one of these shapes keeps a label, which
  is what the generator did for every net before. Falling back this way means
  the netlist stays correct even where the layout cannot be drawn tidily.

The engine only computes a plan. Writing symbols, wires and labels into the
schematic stays in :mod:`schematic_writer`.
"""

import logging
import math
from collections import defaultdict
from dataclasses import dataclass, field
from enum import Enum
from typing import Dict, List, Optional, Sequence, Set, Tuple

logger = logging.getLogger(__name__)

# KiCad snaps schematic geometry to a 50mil grid. Every coordinate this module
# produces is a multiple of it, which is what makes pins, wires and junctions
# land on exactly the same points.
GRID = 1.27

# Spacing in mm. The pitches are grid multiples chosen so a wire between two
# adjacent parts is long enough to read as a connection.
PASSIVE_PITCH = 25.4
ROW_PITCH = 22.86
GROUP_GAP = 20.32
SHUNT_DROP = 17.78
SHEET_MARGIN_X = 30.48
SHEET_MARGIN_Y = 25.4

# The clear space kept between two parts, and the amount a symbol's body is
# shrunk by before testing whether a wire runs across it. The second figure
# stops a wire that merely grazes a symbol's declared extent from being
# rejected, since those extents include the reference and value text.
MIN_PART_GAP = 10.16
BODY_CLEARANCE = 1.27

# A part with at least this many pins anchors its group instead of joining a
# passive chain.
ANCHOR_PIN_COUNT = 5

# How far a label or power symbol is held off its pin. Placing either directly
# on the connection point draws it over the symbol body, so a short stub is run
# outward first and the label goes on the end of it.
LABEL_STUB = 5.08
POWER_STUB = 2.54

Point2D = Tuple[float, float]
Segment = Tuple[Point2D, Point2D]


def outward_step(angle: float, distance: float) -> Point2D:
    """Convert an outward-facing label angle into a schematic-space offset.

    KiCad text angles measure anticlockwise from "reads to the right", while
    schematic y grows downwards, so 90 degrees points towards smaller y.

    Args:
        angle: The outward direction in degrees.
        distance: How far to step, in mm.

    Returns:
        The ``(dx, dy)`` offset.
    """
    normalized = round(angle) % 360
    if normalized == 0:
        return (distance, 0.0)
    if normalized == 90:
        return (0.0, -distance)
    if normalized == 180:
        return (-distance, 0.0)
    if normalized == 270:
        return (0.0, distance)
    radians = math.radians(normalized)
    return (distance * math.cos(radians), -distance * math.sin(radians))


def snap(value: float) -> float:
    """Round a coordinate onto the KiCad grid.

    Args:
        value: A coordinate in mm.

    Returns:
        The nearest grid multiple.
    """
    return round(value / GRID) * GRID


class NetRole(Enum):
    """How a net is drawn on the sheet."""

    POWER = "power"
    PORT = "port"
    SIGNAL = "signal"


@dataclass
class PinInfo:
    """One pin of a component being laid out.

    Attributes:
        component: Reference designator of the owning component.
        identifier: Pin identifier as it appears in the net connections.
        offset_x: Pin x position in symbol coordinates.
        offset_y: Pin y position in symbol coordinates.
        orientation: Pin orientation in symbol coordinates, in degrees.
        net: Name of the net attached to this pin, or None.
    """

    component: str
    identifier: str
    offset_x: float
    offset_y: float
    orientation: float
    net: Optional[str] = None


@dataclass
class ComponentInfo:
    """A component as far as layout is concerned.

    Attributes:
        reference: Reference designator.
        lib_id: Library identifier of the symbol.
        pins: The component's pins, in symbol order.
        width: Symbol width in mm.
        height: Symbol height in mm.
    """

    reference: str
    lib_id: str
    pins: List[PinInfo]
    width: float = 10.0
    height: float = 10.0

    @property
    def is_passive(self) -> bool:
        """Whether this is a two-pin part that can join a chain."""
        return len(self.pins) == 2

    @property
    def is_anchor(self) -> bool:
        """Whether this part anchors its group rather than joining a chain."""
        return len(self.pins) >= ANCHOR_PIN_COUNT


@dataclass
class Placement:
    """Where a component ends up.

    Attributes:
        x: Symbol origin x in mm.
        y: Symbol origin y in mm.
        rotation: Symbol rotation in degrees.
    """

    x: float
    y: float
    rotation: float = 0.0


@dataclass
class LayoutPlan:
    """Everything the writer needs to draw one sheet.

    Attributes:
        placements: Position and rotation per component reference.
        wires: Wire segments as ``((x1, y1), (x2, y2))`` pairs.
        junctions: Points where three or more connections meet.
        power_symbols: ``(lib_id, net_name, x, y, rotation)`` per power symbol.
        node_labels: ``(net_name, x, y, rotation)`` for labels on wired nodes.
        wired_pins: ``(component_reference, pin_identifier)`` pairs that a wire
            already connects, so no label is needed at them.
        fully_wired_nets: Signal nets whose every pin is joined by wire.
        height: Vertical extent consumed below the starting y, in mm.
    """

    placements: Dict[str, Placement] = field(default_factory=dict)
    wires: List[Tuple[Tuple[float, float], Tuple[float, float]]] = field(
        default_factory=list
    )
    junctions: List[Tuple[float, float]] = field(default_factory=list)
    power_symbols: List[Tuple[str, str, float, float, float]] = field(
        default_factory=list
    )
    node_labels: List[Tuple[str, float, float, float]] = field(default_factory=list)
    wired_pins: Set[Tuple[str, str]] = field(default_factory=set)
    fully_wired_nets: Set[str] = field(default_factory=set)
    height: float = 0.0


def rotate_offset(
    offset_x: float, offset_y: float, rotation: float
) -> Tuple[float, float]:
    """Rotate a symbol-space pin offset into schematic space.

    Symbol coordinates have y increasing upwards while schematic coordinates
    have y increasing downwards, so the y offset is negated first. KiCad then
    turns a placed symbol the opposite way round from the sign convention that
    negation leaves behind, so the angle is negated too. Getting this backwards
    swaps a two-pin part end for end, which silently rewires the schematic.

    Args:
        offset_x: Pin x offset in symbol coordinates.
        offset_y: Pin y offset in symbol coordinates.
        rotation: Symbol rotation in degrees.

    Returns:
        The ``(dx, dy)`` offset from the symbol origin, in schematic space.
    """
    radians = math.radians(-rotation)
    local_x = offset_x
    local_y = -offset_y
    return (
        (local_x * math.cos(radians)) - (local_y * math.sin(radians)),
        (local_x * math.sin(radians)) + (local_y * math.cos(radians)),
    )


@dataclass
class _Chain:
    """A run of two-pin parts in series, with the shunts hanging off it.

    Attributes:
        series: The parts carrying the signal through, in left to right order.
        shunts: Parts with one end on a power rail, keyed by the signal net
            they attach to.
    """

    series: List[ComponentInfo] = field(default_factory=list)
    shunts: Dict[str, List[ComponentInfo]] = field(default_factory=dict)


class WiredLayoutEngine:
    """Plan a sheet's component placement and wiring.

    Args:
        components: The components on the sheet.
        net_roles: How each net should be drawn.
        power_symbols: Power symbol library id per power net.
        origin_y: The y coordinate layout starts at, below any sheet symbols.
    """

    def __init__(
        self,
        components: Sequence[ComponentInfo],
        net_roles: Dict[str, NetRole],
        power_symbols: Dict[str, str],
        origin_y: float = SHEET_MARGIN_Y,
    ) -> None:
        self.components = {component.reference: component for component in components}
        self.net_roles = net_roles
        self.power_symbols = power_symbols
        self.origin_y = origin_y

        self.plan = LayoutPlan()
        self._net_pins: Dict[str, List[PinInfo]] = defaultdict(list)
        for component in components:
            for pin in component.pins:
                if pin.net:
                    self._net_pins[pin.net].append(pin)

        self._shunt_refs: Set[str] = {
            component.reference for component in components if self._is_shunt(component)
        }

        # Chain node per net, the pin point index used when validating routes,
        # and the segments each routed net has claimed.
        self._nodes: Dict[str, Point2D] = {}
        self._pin_owner: Dict[Point2D, Set[str]] = {}
        self._claimed: Dict[str, List[Segment]] = {}

    # ------------------------------------------------------------------
    # Public entry point
    # ------------------------------------------------------------------

    def build(self) -> LayoutPlan:
        """Place every component and route what can be routed.

        Returns:
            The completed layout plan.
        """
        groups = self._build_groups()
        logger.debug(
            "Wired layout: %d component(s) in %d group(s)",
            len(self.components),
            len(groups),
        )

        cursor_y = self.origin_y
        for index, group in enumerate(groups):
            consumed = self._layout_group(group, cursor_y)
            cursor_y = snap(cursor_y + consumed + GROUP_GAP)
            logger.debug(
                "Group %d (%d parts) laid out, next row at y=%.2f",
                index,
                len(group),
                cursor_y,
            )

        self.plan.height = max(0.0, cursor_y - self.origin_y)
        self._add_power_symbols()
        self._route_signal_nets()
        return self.plan

    # ------------------------------------------------------------------
    # Classification and grouping
    # ------------------------------------------------------------------

    def _role(self, net: Optional[str]) -> Optional[NetRole]:
        """Look up how a net is drawn.

        Args:
            net: The net name, or None.

        Returns:
            The net's role, or None when there is no net.
        """
        return self.net_roles.get(net) if net else None

    def _is_shunt(self, component: ComponentInfo) -> bool:
        """Report whether a part shunts a signal to a power rail.

        Args:
            component: The component to classify.

        Returns:
            True for a two-pin part with one end on a power rail and the other
            on a signal net.
        """
        if not component.is_passive:
            return False
        roles = [self._role(pin.net) for pin in component.pins]
        return NetRole.POWER in roles and NetRole.SIGNAL in roles

    def _build_groups(self) -> List[List[ComponentInfo]]:
        """Partition components into groups that share signal nets.

        Components joined by a signal net belong together and end up adjacent
        on the sheet. A part with no signal net at all, such as a decoupling
        capacitor sitting across two rails, forms its own group.

        Returns:
            Groups of components, largest first, each in a stable order.
        """
        adjacency: Dict[str, Set[str]] = {ref: set() for ref in self.components}
        for net, pins in self._net_pins.items():
            if self._role(net) is not NetRole.SIGNAL:
                continue
            references = {pin.component for pin in pins if pin.component in adjacency}
            for reference in references:
                adjacency[reference] |= references - {reference}

        groups: List[List[ComponentInfo]] = []
        seen: Set[str] = set()
        for reference in sorted(self.components):
            if reference in seen:
                continue
            stack = [reference]
            members: List[str] = []
            while stack:
                current = stack.pop()
                if current in seen:
                    continue
                seen.add(current)
                members.append(current)
                stack.extend(sorted(adjacency[current] - seen))
            groups.append([self.components[member] for member in sorted(members)])

        # Bigger groups first keeps the busiest circuitry at the top, and
        # sorting by reference within a group keeps the output reproducible.
        groups.sort(key=lambda group: (-len(group), group[0].reference))
        return groups

    # ------------------------------------------------------------------
    # Per-group layout
    # ------------------------------------------------------------------

    def _layout_group(self, group: List[ComponentInfo], top_y: float) -> float:
        """Place one group and wire what it can.

        Args:
            group: The components in the group.
            top_y: The y coordinate the group starts at.

        Returns:
            The height the group consumed, in mm.
        """
        anchors = [component for component in group if component.is_anchor]
        rest = [component for component in group if not component.is_anchor]

        row_y = snap(top_y)
        consumed = 0.0

        if anchors:
            cursor_x = SHEET_MARGIN_X
            tallest = 0.0
            for anchor in anchors:
                self.plan.placements[anchor.reference] = Placement(
                    snap(cursor_x + anchor.width / 2),
                    snap(row_y + anchor.height / 2),
                )
                cursor_x = snap(cursor_x + anchor.width + GROUP_GAP)
                tallest = max(tallest, anchor.height)
            row_y = snap(row_y + tallest + ROW_PITCH)
            consumed += tallest + ROW_PITCH

        for chain in self._build_chains(rest):
            chain_height = self._layout_chain(chain, row_y)
            row_y = snap(row_y + chain_height + ROW_PITCH)
            consumed += chain_height + ROW_PITCH

        return consumed

    def _build_chains(self, components: List[ComponentInfo]) -> List[_Chain]:
        """Split a group's non-anchor parts into series chains with shunts.

        Two parts are in series when a signal net joins exactly one pin of each
        and touches no other series part. Following those links from an end
        produces the left to right order a schematic is read in. Shunts are
        then attached to whichever chain node carries their signal net.

        Args:
            components: The non-anchor components of a group.

        Returns:
            The chains that make up the group.
        """
        series_parts = [
            component
            for component in components
            if component.is_passive and component.reference not in self._shunt_refs
        ]
        shunt_parts = [
            component
            for component in components
            if component.reference in self._shunt_refs
        ]
        leftovers = [
            component
            for component in components
            if not component.is_passive and component.reference not in self._shunt_refs
        ]

        series_refs = {component.reference for component in series_parts}
        neighbours: Dict[str, Set[str]] = defaultdict(set)
        for net, pins in self._net_pins.items():
            if self._role(net) is not NetRole.SIGNAL:
                continue
            touching = {pin.component for pin in pins if pin.component in series_refs}
            if len(touching) == 2:
                first, second = sorted(touching)
                neighbours[first].add(second)
                neighbours[second].add(first)

        by_reference = {component.reference: component for component in series_parts}
        chains: List[_Chain] = []
        placed: Set[str] = set()

        # Start from chain ends so each walk traces a path rather than cutting
        # a loop in an arbitrary place.
        ends = [ref for ref in sorted(by_reference) if len(neighbours[ref]) <= 1]
        for start in ends + sorted(by_reference):
            if start in placed:
                continue
            chain = _Chain()
            current: Optional[str] = start
            while current is not None and current not in placed:
                placed.add(current)
                chain.series.append(by_reference[current])
                remaining = sorted(neighbours[current] - placed)
                current = remaining[0] if remaining else None
            chains.append(chain)

        if not chains:
            chains.append(_Chain())

        # Attach every shunt to the chain that carries its signal net.
        for shunt in shunt_parts:
            net = self._signal_net_of(shunt)
            target = self._chain_for_net(chains, net) if net else None
            if target is None:
                target = chains[0]
            target.shunts.setdefault(net or shunt.reference, []).append(shunt)

        # Parts that are neither anchors nor two-pin passives get their own row.
        for component in leftovers:
            chains.append(_Chain(series=[component]))

        return [chain for chain in chains if chain.series or chain.shunts]

    def _signal_net_of(self, component: ComponentInfo) -> Optional[str]:
        """Return the single signal net a shunt attaches to.

        Args:
            component: The shunt component.

        Returns:
            The signal net name, or None.
        """
        for pin in component.pins:
            if self._role(pin.net) is NetRole.SIGNAL:
                return pin.net
        return None

    def _chain_for_net(self, chains: List[_Chain], net: str) -> Optional[_Chain]:
        """Find the chain whose series parts touch a net.

        Args:
            chains: The chains built so far.
            net: The net to look for.

        Returns:
            The matching chain, or None.
        """
        for chain in chains:
            for component in chain.series:
                if any(pin.net == net for pin in component.pins):
                    return chain
        return None

    def _layout_chain(self, chain: _Chain, row_y: float) -> float:
        """Place one chain horizontally and hang its shunts below it.

        The pitch grows to fit the widest part in the chain, so parts are
        evenly spaced without ever touching. Shunts drop below the node they
        decouple, leaving room for their power symbol underneath.

        Args:
            chain: The chain to lay out.
            row_y: The y coordinate the chain starts at.

        Returns:
            The height the chain consumed, including shunts.
        """
        parts = chain.series + [s for group in chain.shunts.values() for s in group]
        if not parts:
            return 0.0

        widest = max(part.width for part in parts)
        tallest = max(part.height for part in parts)
        pitch = snap(max(PASSIVE_PITCH, widest + MIN_PART_GAP))

        axis_y = snap(row_y + tallest / 2)
        height = tallest

        for index, component in enumerate(chain.series):
            x = snap(SHEET_MARGIN_X + index * pitch + pitch / 2)
            # Two-pin parts stand vertically by default; a quarter turn lays
            # them along the chain with pin 1 on the left, so the signal reads
            # left to right the way a schematic normally does.
            rotation = 90.0 if component.is_passive else 0.0
            self.plan.placements[component.reference] = Placement(x, axis_y, rotation)

        nodes = self._chain_nodes(chain, axis_y, pitch)
        self._nodes.update(nodes)

        shunt_x = snap(SHEET_MARGIN_X + pitch / 2)
        drop = snap(max(SHUNT_DROP, tallest / 2 + MIN_PART_GAP))
        for net, shunts in sorted(chain.shunts.items()):
            node = nodes.get(net)
            for shunt in shunts:
                x = node[0] if node else shunt_x
                self.plan.placements[shunt.reference] = Placement(
                    x, snap(axis_y + drop), 0.0
                )
                height = max(height, drop + shunt.height)
                if node is None:
                    shunt_x = snap(shunt_x + pitch)

        return height

    def _chain_nodes(
        self, chain: _Chain, axis_y: float, pitch: float
    ) -> Dict[str, Tuple[float, float]]:
        """Work out the wiring node for each net along a chain.

        A node sits midway between two series parts, or half a pitch beyond the
        ends of the chain, and is where the series wires, any shunt drop and any
        label all meet. Only chains made purely of two-pin passives get nodes,
        because that is the only shape whose geometry is known to be free of
        other pins.

        Args:
            chain: The chain being laid out.
            axis_y: The y coordinate of the chain axis.
            pitch: The horizontal spacing between parts in this chain.

        Returns:
            The ``(x, y)`` node point for each net along the chain.
        """
        nodes: Dict[str, Tuple[float, float]] = {}
        if not all(component.is_passive for component in chain.series):
            return nodes

        for component in chain.series:
            placement = self.plan.placements[component.reference]
            for pin in component.pins:
                if self._role(pin.net) is not NetRole.SIGNAL or pin.net in nodes:
                    continue
                position = self.pin_position(pin)
                if position is None:
                    continue
                # Push the node out from the pin, along the chain, far enough
                # that two adjacent parts share one node between them.
                direction = 1.0 if position[0] >= placement.x else -1.0
                reach = pitch / 2 - abs(position[0] - placement.x)
                nodes[pin.net] = (snap(position[0] + direction * reach), axis_y)
        return nodes

    # ------------------------------------------------------------------
    # Wiring
    # ------------------------------------------------------------------

    def pin_position(self, pin: PinInfo) -> Optional[Tuple[float, float]]:
        """Resolve a pin's connection point on the sheet.

        Args:
            pin: The pin to locate.

        Returns:
            The ``(x, y)`` connection point, or None if its component is
            unplaced.
        """
        placement = self.plan.placements.get(pin.component)
        if placement is None:
            return None
        dx, dy = rotate_offset(pin.offset_x, pin.offset_y, placement.rotation)
        return (snap(placement.x + dx), snap(placement.y + dy))

    def _route_signal_nets(self) -> None:
        """Wire every signal net whose route can be proven safe.

        A net is routed only if the wires it needs touch nothing belonging to
        another net. Anything that fails the check keeps its labels, so a net
        is never silently shorted to its neighbour by a wire that happens to
        pass through the wrong point.
        """
        self._index_pin_points()

        for net in sorted(self._net_pins):
            if self._role(net) is not NetRole.SIGNAL:
                continue

            pins = [
                pin
                for pin in self._net_pins[net]
                if pin.component in self.plan.placements
            ]
            if len(pins) < 2 or len(pins) != len(self._net_pins[net]):
                # Part of the net lives somewhere this sheet cannot draw, so
                # the whole net stays on labels.
                continue

            route = self._plan_route(net, pins)
            if route is None:
                continue

            segments, junctions = route
            if not self._route_is_safe(net, segments):
                logger.debug("Route for net '%s' rejected, keeping labels", net)
                continue

            self.plan.wires.extend(segments)
            self.plan.junctions.extend(junctions)
            self.plan.fully_wired_nets.add(net)
            for pin in pins:
                self.plan.wired_pins.add((pin.component, pin.identifier))
            self._claim_segments(net, segments)

            # Name the wire once so the netlist keeps the name from the Python
            # source instead of one KiCad invents from the parts it joins.
            anchor = self._nodes.get(net) or self._segment_midpoint(segments[0])
            self.plan.node_labels.append((net, anchor[0], anchor[1], 0.0))
            logger.debug(
                "Net '%s' wired with %d segment(s), %d junction(s)",
                net,
                len(segments),
                len(junctions),
            )

    @staticmethod
    def _segment_midpoint(segment: Segment) -> Point2D:
        """Return the grid-aligned midpoint of a wire segment.

        Args:
            segment: The segment to measure.

        Returns:
            The ``(x, y)`` midpoint.
        """
        (x1, y1), (x2, y2) = segment
        return (snap((x1 + x2) / 2), snap((y1 + y2) / 2))

    def _index_pin_points(self) -> None:
        """Record which net owns each pin point on the sheet."""
        self._pin_owner = {}
        for net, pins in self._net_pins.items():
            for pin in pins:
                position = self.pin_position(pin)
                if position is not None:
                    self._pin_owner.setdefault(position, set()).add(net)

    def _plan_route(
        self, net: str, pins: List[PinInfo]
    ) -> Optional[Tuple[List[Segment], List[Point2D]]]:
        """Build the wire segments that would connect one net.

        Args:
            net: The net being routed.
            pins: The net's pins, all of them placed.

        Returns:
            A ``(segments, junctions)`` pair, or None when this net has no
            shape the router knows how to draw.
        """
        points = []
        for pin in pins:
            position = self.pin_position(pin)
            if position is None:
                return None
            points.append(position)

        if len(set(points)) != len(points):
            # Two pins of the same net landing on one point needs no wire, but
            # it also means the placement collapsed. Leave it to the labels.
            return None

        node = self._nodes.get(net)
        if node is not None:
            segments: List[Segment] = []
            for point in points:
                leg = self._orthogonal(point, node)
                if leg is None:
                    return None
                segments.extend(leg)
            junctions = [node] if len(points) >= 3 else []
            return segments, junctions

        if len(points) == 2:
            leg = self._orthogonal(points[0], points[1])
            return (leg, []) if leg else None

        return None

    @staticmethod
    def _orthogonal(start: Point2D, end: Point2D) -> Optional[List[Segment]]:
        """Build an orthogonal path between two points.

        A straight run becomes one segment and anything else takes a single
        bend. Diagonal wires are never emitted, since schematics read far more
        easily without them.

        Args:
            start: The first connection point.
            end: The second connection point.

        Returns:
            The segments, or None when the two points coincide.
        """
        if start == end:
            return None
        if math.isclose(start[1], end[1], abs_tol=GRID / 4):
            return [(start, (end[0], start[1]))]
        if math.isclose(start[0], end[0], abs_tol=GRID / 4):
            return [(start, (start[0], end[1]))]
        corner = (end[0], start[1])
        return [(start, corner), (corner, end)]

    def _route_is_safe(self, net: str, segments: List[Segment]) -> bool:
        """Check that a candidate route cannot join this net to another.

        Two wires that merely cross are separate nets in KiCad, so a crossing
        is allowed. What is not allowed is a wire passing through a pin of a
        different net, ending on another net's wire, or running along it.

        Args:
            net: The net being routed.
            segments: The candidate wire segments.

        Returns:
            True when the route is safe to draw.
        """
        for start, end in segments:
            for point, owners in self._pin_owner.items():
                if owners == {net}:
                    continue
                if self._point_on_segment(point, start, end):
                    return False

            for other_net, claimed in self._claimed.items():
                if other_net == net:
                    continue
                for other in claimed:
                    if self._segments_conflict((start, end), other):
                        return False

            for reference, placement in self.plan.placements.items():
                if self._crosses_body(reference, placement, (start, end), net):
                    return False
        return True

    def _claim_segments(self, net: str, segments: List[Segment]) -> None:
        """Record the segments a net now occupies.

        Args:
            net: The net that was routed.
            segments: Its wire segments.
        """
        self._claimed.setdefault(net, []).extend(segments)

    @staticmethod
    def _point_on_segment(point: Point2D, start: Point2D, end: Point2D) -> bool:
        """Report whether a point lies on an orthogonal segment.

        Args:
            point: The point to test.
            start: One end of the segment.
            end: The other end.

        Returns:
            True if the point lies on the segment, endpoints included.
        """
        tolerance = GRID / 4
        if abs(start[1] - end[1]) < tolerance:
            return abs(point[1] - start[1]) < tolerance and (
                min(start[0], end[0]) - tolerance
                <= point[0]
                <= max(start[0], end[0]) + tolerance
            )
        if abs(start[0] - end[0]) < tolerance:
            return abs(point[0] - start[0]) < tolerance and (
                min(start[1], end[1]) - tolerance
                <= point[1]
                <= max(start[1], end[1]) + tolerance
            )
        return False

    @classmethod
    def _segments_conflict(cls, first: Segment, second: Segment) -> bool:
        """Report whether two segments would connect in KiCad.

        Args:
            first: The candidate segment.
            second: A segment already claimed by another net.

        Returns:
            True when the two would form a connection rather than a crossing.
        """
        # An endpoint of either segment lying on the other creates a T joint,
        # which KiCad treats as a connection.
        for point in first:
            if cls._point_on_segment(point, second[0], second[1]):
                return True
        for point in second:
            if cls._point_on_segment(point, first[0], first[1]):
                return True

        # Two parallel segments sharing a line would overlap rather than cross.
        first_horizontal = abs(first[0][1] - first[1][1]) < GRID / 4
        second_horizontal = abs(second[0][1] - second[1][1]) < GRID / 4
        if first_horizontal != second_horizontal:
            return False
        if first_horizontal:
            return abs(first[0][1] - second[0][1]) < GRID / 4 and not (
                max(first[0][0], first[1][0]) < min(second[0][0], second[1][0])
                or min(first[0][0], first[1][0]) > max(second[0][0], second[1][0])
            )
        return abs(first[0][0] - second[0][0]) < GRID / 4 and not (
            max(first[0][1], first[1][1]) < min(second[0][1], second[1][1])
            or min(first[0][1], first[1][1]) > max(second[0][1], second[1][1])
        )

    def _crosses_body(
        self,
        reference: str,
        placement: Placement,
        segment: Segment,
        net: str,
    ) -> bool:
        """Report whether a segment cuts through a component's body.

        Args:
            reference: The component's reference designator.
            placement: Where the component sits.
            segment: The candidate wire segment.
            net: The net being routed.

        Returns:
            True if the wire would run across the symbol.
        """
        component = self.components.get(reference)
        if component is None:
            return False
        if any(pin.net == net for pin in component.pins):
            # The wire is meant to reach this part, so touching it is expected.
            return False

        half_width = component.width / 2 - BODY_CLEARANCE
        half_height = component.height / 2 - BODY_CLEARANCE
        if half_width <= 0 or half_height <= 0:
            return False

        left, right = placement.x - half_width, placement.x + half_width
        top, bottom = placement.y - half_height, placement.y + half_height
        (x1, y1), (x2, y2) = segment

        if abs(y1 - y2) < GRID / 4:
            return top <= y1 <= bottom and not (
                max(x1, x2) <= left or min(x1, x2) >= right
            )
        return left <= x1 <= right and not (max(y1, y2) <= top or min(y1, y2) >= bottom)

    def _add_power_symbols(self) -> None:
        """Place a power symbol at every pin sitting on a power rail.

        Ground and the supply rails are drawn this way rather than wired across
        the sheet, which is what keeps a schematic readable as it grows.
        """
        for net, role in self.net_roles.items():
            if role is not NetRole.POWER:
                continue
            lib_id = self.power_symbols.get(net)
            if not lib_id:
                continue

            for pin in self._net_pins[net]:
                position = self.pin_position(pin)
                if position is None:
                    continue
                placement = self.plan.placements[pin.component]
                self.plan.power_symbols.append(
                    (
                        lib_id,
                        net,
                        position[0],
                        position[1],
                        self._power_symbol_rotation(pin, placement.rotation, lib_id),
                    )
                )
                self.plan.wired_pins.add((pin.component, pin.identifier))

    @staticmethod
    def _power_symbol_rotation(
        pin: PinInfo, component_rotation: float, lib_id: str
    ) -> float:
        """Choose the rotation that points a power symbol away from its pin.

        Args:
            pin: The pin the symbol attaches to.
            component_rotation: Rotation of the owning component.
            lib_id: The power symbol's library id.

        Returns:
            The symbol rotation in degrees.
        """
        label_angle = (pin.orientation + 180.0) % 360.0
        base = ((label_angle + component_rotation) % 360.0 - 90.0) % 360.0
        if "GND" in lib_id or "VSS" in lib_id:
            # Ground symbols point down by default, the opposite of the supply
            # symbols, so they need flipping.
            return (base + 180.0) % 360.0
        return base
