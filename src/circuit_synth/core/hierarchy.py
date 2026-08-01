# FILE: src/circuit_synth/core/hierarchy.py
"""Hierarchical block ports.

A hierarchical block is a subcircuit that declares a named, directional
interface. Each declared port becomes a sheet pin on the parent's sheet symbol
and a matching hierarchical label inside the child schematic, which is how
KiCad represents nested hierarchical blocks.

Ports are declared by annotating the parameters of a ``@circuit`` function:

.. code-block:: python

    from circuit_synth import Bidirectional, Input, Net, Output, circuit

    @circuit(name="HalfBridge")
    def half_bridge(HI: Input, LI: Input, PHASE: Output, GND: Bidirectional):
        ...

The parameter name becomes the port name, so the same block can be instantiated
several times with different nets connected to it. Ports may also be declared
without annotations by passing ``ports`` to the decorator::

    @circuit(name="HalfBridge", ports={"HI": "input", "LI": "input"})
    def half_bridge(HI, LI, PHASE, GND):
        ...

A circuit that declares no ports keeps the previous behaviour, where labels are
named after the nets themselves.
"""

from dataclasses import dataclass
from enum import Enum
from typing import Any, Dict, Optional

__all__ = [
    "PortDirection",
    "Port",
    "PortAnnotation",
    "Input",
    "Output",
    "Bidirectional",
    "TriState",
    "PassivePort",
    "PowerIn",
    "PowerOut",
    "resolve_port_direction",
]


class PortDirection(Enum):
    """Direction of a hierarchical port.

    The values match the ``shape`` keyword KiCad uses for hierarchical labels
    and the pin type it uses for sheet pins, so they can be written straight
    into a ``.kicad_sch`` file.
    """

    INPUT = "input"
    OUTPUT = "output"
    BIDIRECTIONAL = "bidirectional"
    TRI_STATE = "tri_state"
    PASSIVE = "passive"

    @classmethod
    def from_value(cls, value: Any) -> "PortDirection":
        """Coerce ``value`` to a :class:`PortDirection`.

        Args:
            value: A :class:`PortDirection`, a :class:`PortAnnotation` subclass,
                or a string such as ``"input"``, ``"in"``, ``"out"`` or
                ``"bidi"``.

        Returns:
            The matching direction.

        Raises:
            ValueError: If ``value`` does not name a known direction.
        """
        if isinstance(value, PortDirection):
            return value

        if isinstance(value, type) and issubclass(value, PortAnnotation):
            return value.direction

        if isinstance(value, PortAnnotation):
            return value.direction

        if isinstance(value, str):
            key = value.strip().lower().replace("-", "_").replace(" ", "_")
            aliases = {
                "in": cls.INPUT,
                "input": cls.INPUT,
                "power_in": cls.INPUT,
                "out": cls.OUTPUT,
                "output": cls.OUTPUT,
                "power_out": cls.OUTPUT,
                "bidi": cls.BIDIRECTIONAL,
                "inout": cls.BIDIRECTIONAL,
                "bidirectional": cls.BIDIRECTIONAL,
                "tri_state": cls.TRI_STATE,
                "tristate": cls.TRI_STATE,
                "passive": cls.PASSIVE,
            }
            if key in aliases:
                return aliases[key]

        raise ValueError(f"Unknown port direction: {value!r}")


class PortAnnotation:
    """Base class for the annotation markers used to declare port direction.

    Subclasses are never instantiated. They are used purely as parameter
    annotations on ``@circuit`` functions, where they read naturally::

        def half_bridge(HI: Input, PHASE: Output):
            ...
    """

    direction: PortDirection = PortDirection.PASSIVE


class Input(PortAnnotation):
    """Annotation marking a parameter as a hierarchical input port."""

    direction = PortDirection.INPUT


class Output(PortAnnotation):
    """Annotation marking a parameter as a hierarchical output port."""

    direction = PortDirection.OUTPUT


class Bidirectional(PortAnnotation):
    """Annotation marking a parameter as a bidirectional hierarchical port."""

    direction = PortDirection.BIDIRECTIONAL


class TriState(PortAnnotation):
    """Annotation marking a parameter as a tri-state hierarchical port."""

    direction = PortDirection.TRI_STATE


class PassivePort(PortAnnotation):
    """Annotation marking a parameter as a passive hierarchical port."""

    direction = PortDirection.PASSIVE


class PowerIn(PortAnnotation):
    """Annotation for a power rail consumed by the block.

    KiCad has no dedicated power shape for hierarchical labels, so this is
    recorded as an input.
    """

    direction = PortDirection.INPUT


class PowerOut(PortAnnotation):
    """Annotation for a power rail produced by the block.

    KiCad has no dedicated power shape for hierarchical labels, so this is
    recorded as an output.
    """

    direction = PortDirection.OUTPUT


def resolve_port_direction(
    annotation: Any, override: Optional[Any] = None
) -> Optional[PortDirection]:
    """Resolve the direction declared for a single circuit parameter.

    Args:
        annotation: The parameter's type annotation, or
            :attr:`inspect.Parameter.empty` when it has none.
        override: An explicit direction from the decorator's ``ports``
            argument, which takes precedence over the annotation.

    Returns:
        The declared direction, or ``None`` if the parameter declares no port.
    """
    if override is not None:
        return PortDirection.from_value(override)

    if annotation is None:
        return None

    # inspect.Parameter.empty is a sentinel class; treat anything that is not a
    # port marker as "not a port declaration".
    try:
        return PortDirection.from_value(annotation)
    except ValueError:
        return None


@dataclass
class Port:
    """A named, directional connection point on a hierarchical block.

    Attributes:
        name: The port name, local to the block. This is the sheet pin name in
            the parent schematic and the hierarchical label text in the child.
        direction: The port direction.
        net_name: Name of the net bound to this port in the parent scope.
    """

    name: str
    direction: PortDirection
    net_name: str

    def to_dict(self) -> Dict[str, str]:
        """Serialize the port for the intermediate circuit JSON.

        Returns:
            A dictionary with ``name``, ``direction`` and ``net`` keys.
        """
        return {
            "name": self.name,
            "direction": self.direction.value,
            "net": self.net_name,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Port":
        """Rebuild a :class:`Port` from its JSON representation.

        Args:
            data: A dictionary as produced by :meth:`to_dict`.

        Returns:
            The reconstructed port.
        """
        return Port(
            name=data["name"],
            direction=PortDirection.from_value(data.get("direction", "passive")),
            net_name=data.get("net", ""),
        )
