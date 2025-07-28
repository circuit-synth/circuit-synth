# -*- coding: utf-8 -*-
#
# data_structures.py
#
# Defines the core classes used by Circuit-Synth to represent a hierarchical circuit
# before generating KiCad files.

import logging
from typing import Dict, List

logger = logging.getLogger(__name__)


class Pin:
    """
    Represents a single pin on a component (including location, orientation, etc.).
    """

    def __init__(
        self,
        number: str,
        name: str,
        function: str,
        orientation: float,
        x: float,
        y: float,
        length: float,
    ):
        self.number = number  # e.g. "1"
        self.name = name  # e.g. "GND"
        self.function = function  # e.g. "power_in"
        self.orientation = orientation
        self.x = x
        self.y = y
        self.length = length

    def __repr__(self):
        return (
            f"Pin(number='{self.number}', name='{self.name}', function='{self.function}', "
            f"orientation={self.orientation}, x={self.x}, y={self.y}, length={self.length})"
        )


class Component:
    """
    Represents a circuit component with reference, symbol library ID, value, footprint, pins, etc.
    """

    def __init__(self, ref: str, symbol_id: str, value: str, footprint: str):
        self.ref = ref  # e.g. "C1"
        self.symbol_id = symbol_id  # e.g. "Device:C"
        self.value = value  # e.g. "10uF"
        self.footprint = footprint  # e.g. "Capacitor_SMD:C_0603"
        self.pins: List[Pin] = []
        self.hierarchy_path = "/"  # default top-level

        # During placement, we store x,y (in mm)
        self.x = 0.0
        self.y = 0.0
        # Rotation if needed
        self.rotation = 0.0

    def __repr__(self):
        return (
            f"Component(ref='{self.ref}', symbol_id='{self.symbol_id}', value='{self.value}', "
            f"footprint='{self.footprint}', pins=[{', '.join(str(p) for p in self.pins)}], "
            f"x={self.x}, y={self.y}, rotation={self.rotation})"
        )


class Net:
    """
    Represents an electrical net (by name) and the pin connections (component ref, pin_number).
    """

    def __init__(self, name: str):
        self.name = name
        # Each connection is a tuple (comp_ref, pin_number).
        self.connections: List[tuple] = []

    def __repr__(self):
        return f"Net(name='{self.name}', connections={self.connections})"


class Circuit:
    """
    Holds all components, nets, and child subcircuits (instances).
    """

    def __init__(self, name: str):
        self.name = name
        self.components: List[Component] = []
        self.nets: List[Net] = []
        # child_instances: each item is { "sub_name": <str>, "instance_label": <str>, "x": float, "y": float, "width": float, "height": float }
        # We'll store subcircuit usage references here for building hierarchical sheets.
        # x, y, width, height are added during collision placement
        self.child_instances = []

    def add_component(self, comp: Component):
        logger.debug(
            f"Adding component {comp.ref} ({comp.symbol_id}) to circuit '{self.name}'"
        )
        self.components.append(comp)

    def add_net(self, net: Net):
        logger.debug(
            f"Adding net {net.name} with {len(net.connections)} connections to circuit '{self.name}'"
        )
        self.nets.append(net)

    def __repr__(self):
        return (
            f"Circuit(name='{self.name}', "
            f"components=[{', '.join(str(c) for c in self.components)}], "
            f"nets=[{', '.join(str(n) for n in self.nets)}], "
            f"child_instances={self.child_instances})"
        )
