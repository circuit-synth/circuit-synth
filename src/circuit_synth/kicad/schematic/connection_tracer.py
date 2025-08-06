"""
Connection tracing functionality for KiCad schematics.

This module provides tools for tracing electrical connections through
schematics, finding paths between components, and analyzing connectivity.
"""

import logging
from collections import deque
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Dict, List, Optional, Set, Tuple, Union

from ..core.types import (
    Junction,
    Label,
    LabelType,
    Net,
    Point,
    Schematic,
    SchematicSymbol,
    Wire,
)

logger = logging.getLogger(__name__)


@dataclass
class ComponentPin:
    """Represents a component pin."""

    component_ref: str
    pin_number: str
    position: Point
    net_name: Optional[str] = None


@dataclass
class ConnectionNode:
    """Node in the connection graph."""

    position: Point
    node_type: str  # "pin", "junction", "label", "wire_point"
    connected_elements: Set[str] = field(default_factory=set)  # UUIDs
    net_name: Optional[str] = None

    def __hash__(self):
        return hash((self.position.x, self.position.y, self.node_type))


@dataclass
class ConnectionEdge:
    """Edge in the connection graph."""

    start_node: ConnectionNode
    end_node: ConnectionNode
    wire_uuid: Optional[str] = None

    def __hash__(self):
        return hash((self.start_node, self.end_node))


@dataclass
class NetTrace:
    """Complete trace of a net."""

    net_name: str
    nodes: List[ConnectionNode] = field(default_factory=list)
    edges: List[ConnectionEdge] = field(default_factory=list)
    component_pins: List[ComponentPin] = field(default_factory=list)
    total_length: float = 0.0

    def add_node(self, node: ConnectionNode):
        """Add a node to the trace."""
        if node not in self.nodes:
            self.nodes.append(node)

    def add_edge(self, edge: ConnectionEdge):
        """Add an edge to the trace."""
        if edge not in self.edges:
            self.edges.append(edge)
            # Update total length
            dx = edge.end_node.position.x - edge.start_node.position.x
            dy = edge.end_node.position.y - edge.start_node.position.y
            self.total_length += (dx**2 + dy**2) ** 0.5


@dataclass
class ConnectionPath:
    """Path between two pins."""

    start_pin: ComponentPin
    end_pin: ComponentPin
    path_nodes: List[ConnectionNode] = field(default_factory=list)
    path_wires: List[Wire] = field(default_factory=list)
    total_length: float = 0.0


class ConnectionGraph:
    """Graph representation of schematic connections."""

    def __init__(self):
        """Initialize connection graph."""
        self.nodes: Dict[Tuple[float, float], ConnectionNode] = {}
        self.edges: List[ConnectionEdge] = []
        self.adjacency: Dict[ConnectionNode, List[ConnectionNode]] = {}

    def add_node(self, node: ConnectionNode):
        """Add a node to the graph."""
        key = (node.position.x, node.position.y)
        if key not in self.nodes:
            self.nodes[key] = node
            self.adjacency[node] = []

    def add_edge(
        self,
        start: ConnectionNode,
        end: ConnectionNode,
        wire_uuid: Optional[str] = None,
    ):
        """Add an edge to the graph."""
        edge = ConnectionEdge(start, end, wire_uuid)
        self.edges.append(edge)

        # Update adjacency
        if start in self.adjacency:
            self.adjacency[start].append(end)
        if end in self.adjacency:
            self.adjacency[end].append(start)

    def get_node_at(self, position: Point) -> Optional[ConnectionNode]:
        """Get node at position."""
        key = (position.x, position.y)
        return self.nodes.get(key)

    def find_path(
        self, start: ConnectionNode, end: ConnectionNode
    ) -> Optional[List[ConnectionNode]]:
        """Find path between two nodes using BFS."""
        if start not in self.adjacency or end not in self.adjacency:
            return None

        visited = set()
        queue = deque([(start, [start])])

        while queue:
            current, path = queue.popleft()

            if current == end:
                return path

            if current in visited:
                continue

            visited.add(current)

            for neighbor in self.adjacency.get(current, []):
                if neighbor not in visited:
                    queue.append((neighbor, path + [neighbor]))

        return None


class ConnectionTracer:
    """
    Traces electrical connections through a schematic.

    This class builds a connection graph from the schematic elements
    and provides methods to trace nets, find paths, and analyze connectivity.
    """

    def __init__(self, schematic: Schematic):
        """
        Initialize the connection tracer.

        Args:
            schematic: The schematic to trace
        """
        self.schematic = schematic
        self.graph = ConnectionGraph()
        self._tolerance = 0.01  # Position matching tolerance
        self._build_connection_graph()

    def _build_connection_graph(self):
        """Build the connection graph from schematic elements."""
        # Add wire endpoints and intermediate points as nodes
        for wire in self.schematic.wires:
            prev_node = None
            for i, point in enumerate(wire.points):
                node = self._get_or_create_node(point, "wire_point")
                node.connected_elements.add(wire.uuid)

                if prev_node:
                    self.graph.add_edge(prev_node, node, wire.uuid)
                prev_node = node

        # Add junctions as nodes
        for junction in self.schematic.junctions:
            node = self._get_or_create_node(junction.position, "junction")
            node.connected_elements.add(junction.uuid)

        # Add labels as nodes
        for label in self.schematic.labels:
            node = self._get_or_create_node(label.position, "label")
            node.connected_elements.add(label.uuid)
            node.net_name = label.text

        # Add component pins as nodes (simplified - needs symbol library)
        for component in self.schematic.components:
            # For now, just add the component position as a pin
            # Real implementation would get actual pin positions
            node = self._get_or_create_node(component.position, "pin")
            node.connected_elements.add(component.uuid)

    def _get_or_create_node(self, position: Point, node_type: str) -> ConnectionNode:
        """Get existing node at position or create new one."""
        # Check for existing node within tolerance
        for (x, y), node in self.graph.nodes.items():
            if (
                abs(x - position.x) < self._tolerance
                and abs(y - position.y) < self._tolerance
            ):
                return node

        # Create new node
        node = ConnectionNode(position=position, node_type=node_type)
        self.graph.add_node(node)
        return node

    def trace_net(self, start_point: Union[ComponentPin, Point, str]) -> NetTrace:
        """
        Trace a complete net from a starting point.

        Args:
            start_point: Starting point (pin, position, or net name)

        Returns:
            Complete trace of the net
        """
        # Determine starting node
        if isinstance(start_point, str):
            # Net name - find a label with this name
            for label in self.schematic.labels:
                if label.text == start_point:
                    start_node = self.graph.get_node_at(label.position)
                    if start_node:
                        break
            else:
                return NetTrace(net_name=start_point)
        elif isinstance(start_point, ComponentPin):
            start_node = self.graph.get_node_at(start_point.position)
        else:  # Point
            start_node = self.graph.get_node_at(start_point)

        if not start_node:
            return NetTrace(net_name="")

        # Determine net name
        net_name = start_node.net_name or ""
        trace = NetTrace(net_name=net_name)

        # BFS to find all connected nodes
        visited = set()
        queue = deque([start_node])

        while queue:
            node = queue.popleft()

            if node in visited:
                continue

            visited.add(node)
            trace.add_node(node)

            # Add connected nodes
            for neighbor in self.graph.adjacency.get(node, []):
                if neighbor not in visited:
                    queue.append(neighbor)

                    # Find edge
                    for edge in self.graph.edges:
                        if (edge.start_node == node and edge.end_node == neighbor) or (
                            edge.start_node == neighbor and edge.end_node == node
                        ):
                            trace.add_edge(edge)
                            break

            # Update net name if found
            if node.net_name and not net_name:
                net_name = node.net_name
                trace.net_name = net_name

        # Find component pins in the trace
        for node in trace.nodes:
            if node.node_type == "pin":
                # Find component at this position
                for component in self.schematic.components:
                    if self._points_equal(component.position, node.position):
                        pin = ComponentPin(
                            component_ref=component.reference,
                            pin_number="1",  # Placeholder
                            position=node.position,
                            net_name=net_name,
                        )
                        trace.component_pins.append(pin)
                        break

        return trace

    def find_all_connections(
        self, component_ref: str, pin: str = None
    ) -> List[NetTrace]:
        """
        Find all connections to a component or specific pin.

        Args:
            component_ref: Component reference
            pin: Optional pin number

        Returns:
            List of net traces connected to the component
        """
        traces = []

        # Find component
        component = None
        for comp in self.schematic.components:
            if comp.reference == component_ref:
                component = comp
                break

        if not component:
            return traces

        # Find node at component position
        node = self.graph.get_node_at(component.position)
        if node:
            trace = self.trace_net(component.position)
            if trace.nodes:
                traces.append(trace)

        return traces

    def get_net_endpoints(self, net_name: str) -> List[ComponentPin]:
        """
        Get all component pins connected to a net.

        Args:
            net_name: Name of the net

        Returns:
            List of component pins
        """
        trace = self.trace_net(net_name)
        return trace.component_pins

    def find_path_between_pins(
        self, start_pin: ComponentPin, end_pin: ComponentPin
    ) -> Optional[ConnectionPath]:
        """
        Find the connection path between two pins.

        Args:
            start_pin: Starting pin
            end_pin: Ending pin

        Returns:
            Connection path if found
        """
        # Get nodes for pins
        start_node = self.graph.get_node_at(start_pin.position)
        end_node = self.graph.get_node_at(end_pin.position)

        if not start_node or not end_node:
            return None

        # Find path
        path_nodes = self.graph.find_path(start_node, end_node)
        if not path_nodes:
            return None

        # Build connection path
        path = ConnectionPath(
            start_pin=start_pin, end_pin=end_pin, path_nodes=path_nodes
        )

        # Find wires in path
        for i in range(len(path_nodes) - 1):
            node1, node2 = path_nodes[i], path_nodes[i + 1]

            # Find wire connecting these nodes
            for wire in self.schematic.wires:
                if (
                    wire.uuid in node1.connected_elements
                    and wire.uuid in node2.connected_elements
                ):
                    path.path_wires.append(wire)
                    break

            # Calculate length
            dx = node2.position.x - node1.position.x
            dy = node2.position.y - node1.position.y
            path.total_length += (dx**2 + dy**2) ** 0.5

        return path

    def find_floating_nets(self) -> List[NetTrace]:
        """Find nets that are not connected to any components."""
        floating_nets = []

        # Check each label
        for label in self.schematic.labels:
            trace = self.trace_net(label.text)

            # Check if any component pins in trace
            if not trace.component_pins:
                floating_nets.append(trace)

        return floating_nets

    def find_short_circuits(self) -> List[Tuple[str, str]]:
        """
        Find potential short circuits (different nets connected).

        Returns:
            List of (net1, net2) pairs that are shorted
        """
        shorts = []
        net_nodes = {}  # net_name -> set of nodes

        # Build net to nodes mapping
        for label in self.schematic.labels:
            trace = self.trace_net(label.text)
            net_nodes[label.text] = set(trace.nodes)

        # Check for overlapping nodes between different nets
        net_names = list(net_nodes.keys())
        for i in range(len(net_names)):
            for j in range(i + 1, len(net_names)):
                net1, net2 = net_names[i], net_names[j]

                # Check for common nodes
                common_nodes = net_nodes[net1] & net_nodes[net2]
                if common_nodes:
                    shorts.append((net1, net2))

        return shorts

    def _points_equal(self, p1: Point, p2: Point) -> bool:
        """Check if two points are equal within tolerance."""
        return abs(p1.x - p2.x) < self._tolerance and abs(p1.y - p2.y) < self._tolerance

    def analyze_connectivity(self) -> Dict[str, Any]:
        """
        Analyze overall connectivity of the schematic.

        Returns:
            Dictionary with connectivity statistics
        """
        stats = {
            "total_nets": 0,
            "floating_nets": 0,
            "component_count": len(self.schematic.components),
            "connected_components": 0,
            "unconnected_components": 0,
            "short_circuits": 0,
            "average_net_length": 0.0,
            "longest_net": None,
            "most_connected_net": None,
        }

        # Find all unique nets
        net_names = set()
        for label in self.schematic.labels:
            net_names.add(label.text)

        stats["total_nets"] = len(net_names)

        # Analyze each net
        net_lengths = []
        max_length = 0.0
        longest_net = None
        max_connections = 0
        most_connected = None

        for net_name in net_names:
            trace = self.trace_net(net_name)

            # Check if floating
            if not trace.component_pins:
                stats["floating_nets"] += 1

            # Track length
            if trace.total_length > 0:
                net_lengths.append(trace.total_length)
                if trace.total_length > max_length:
                    max_length = trace.total_length
                    longest_net = net_name

            # Track connections
            if len(trace.component_pins) > max_connections:
                max_connections = len(trace.component_pins)
                most_connected = net_name

        # Calculate averages
        if net_lengths:
            stats["average_net_length"] = sum(net_lengths) / len(net_lengths)

        stats["longest_net"] = longest_net
        stats["most_connected_net"] = most_connected

        # Check for shorts
        shorts = self.find_short_circuits()
        stats["short_circuits"] = len(shorts)

        # Count connected components
        for component in self.schematic.components:
            connections = self.find_all_connections(component.reference)
            if connections:
                stats["connected_components"] += 1
            else:
                stats["unconnected_components"] += 1

        return stats
