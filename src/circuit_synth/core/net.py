# FILE: src/circuit_synth/core/net.py

from typing import Optional, Set

from ._logger import context_logger
from .decorators import get_current_circuit
from .exception import CircuitSynthError


class Net:
    """
    A Net represents an electrical node (set of pins). The name may be auto-generated.
    """

    def __init__(self, name: Optional[str] = None):
        self.name = name
        self._pins: Set["Pin"] = set()

        # Immediately register with the current circuit
        circuit = get_current_circuit()
        if circuit is None:
            raise CircuitSynthError(
                f"Cannot create Net('{name or ''}'): No active circuit found."
            )
        circuit.add_net(self)

    @property
    def pins(self):
        return frozenset(self._pins)

    def __iadd__(self, other):
        """
        net += pin => pin connects to this net
        net += net => unify (if different) by bringing other net's pins over
        """
        from .pin import Pin

        if isinstance(other, Pin):
            other.connect_to_net(self)

        elif isinstance(other, Net):
            if other is not self:
                # unify: move all pins from 'other' into this net
                for p in list(other._pins):
                    p.connect_to_net(self)

        else:
            raise TypeError(f"Cannot do net += with {type(other)}")

        return self

    def __repr__(self):
        nm = self.name if self.name else "unnamed"
        return f"<Net {nm}>"
