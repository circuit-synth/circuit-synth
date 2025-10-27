# FILE: src/circuit_synth/core/net.py

from typing import Optional, Set, Any, Dict

from loguru import logger

from ._logger import context_logger
from .decorators import get_current_circuit
from .exception import CircuitSynthError
from .power_net_registry import is_power_net, get_power_symbol


class Net:
    """
    A Net represents an electrical node (set of pins).

    Supports:
    - Automatic power net detection (GND, VCC, etc.)
    - Explicit power net declaration
    - Physical constraints (trace current, impedance)
    - Custom properties
    - Differential pairs (via KiCad naming conventions)

    Examples:
        # Auto-detected power net (recommended)
        >>> gnd = Net(name="GND")  # Automatically becomes power net

        # Explicit power net
        >>> vcc = Net(name="VCC", is_power=True, power_symbol="power:VCC")

        # Prevent auto-detection
        >>> not_power = Net(name="GND_SENSE", is_power=False)

        # Differential pair (KiCad detects automatically by name)
        >>> usb_dp = Net(name="USB_DP", impedance=90)  # KiCad pairs USB_DP/USB_DN
        >>> usb_dn = Net(name="USB_DN", impedance=90)

        # High current trace
        >>> power_5v = Net(name="+5V", trace_current=2000)  # 2A, auto-detected as power

        # Custom properties
        >>> rf = Net(name="RF_OUT", impedance=50, substrate_height=1.6)

    Note:
        Differential pairs use KiCad naming conventions (_P/_N, +/-, etc.).
        KiCad automatically detects and routes them as differential pairs.
    """

    def __init__(
        self,
        name: Optional[str] = None,
        # Power net parameters
        is_power: Optional[bool] = None,  # None = auto-detect
        power_symbol: Optional[str] = None,
        # Physical constraints
        trace_current: Optional[float] = None,  # mA
        impedance: Optional[float] = None,      # ohms
        # Custom properties
        **properties: Any
    ):
        """
        Create an electrical net.

        Args:
            name: Net name (e.g., "GND", "USB_DP"). Auto-generated if None.
                 For differential pairs, use KiCad naming conventions:
                 - NAME_P / NAME_N  (e.g., USB_DP / USB_DN)
                 - NAME+ / NAME-    (e.g., ETH_TX+ / ETH_TX-)
            is_power: Power net flag. None (default) = auto-detect from name,
                     True = explicitly mark as power net,
                     False = explicitly NOT a power net.
            power_symbol: KiCad power symbol (e.g., "power:GND").
                         Auto-filled if is_power is auto-detected.
            trace_current: Maximum current in milliamps (mA).
            impedance: Target impedance in ohms for controlled impedance routing.
                      For differential pairs, this is the differential impedance.
            **properties: Custom properties for specialized applications.

        Note:
            Differential pairs are detected automatically by KiCad based on net naming.
            Use matching prefixes with _P/_N, +/-, or similar suffixes.
        """
        self.name = name
        self._pins: Set["Pin"] = set()

        # Auto-detect power nets if not explicitly specified
        if is_power is None and name:
            if is_power_net(name):
                is_power = True
                power_symbol = power_symbol or get_power_symbol(name)
                logger.debug(
                    f"Auto-detected power net '{name}' -> {power_symbol}"
                )

        self.is_power = is_power if is_power is not None else False
        self.power_symbol = power_symbol
        self.trace_current = trace_current
        self.impedance = impedance
        self.properties: Dict[str, Any] = properties

        # Validate at construction time
        self._validate_construction()

        # Immediately register with the current circuit
        circuit = get_current_circuit()
        if circuit is None:
            raise CircuitSynthError(
                f"Cannot create Net('{name or ''}'): No active circuit found."
            )
        circuit.add_net(self)

    def _validate_construction(self) -> None:
        """Validate parameters at construction time."""
        # Power net validation
        if self.is_power and not self.power_symbol:
            raise CircuitSynthError(
                f"Power net '{self.name}' requires power_symbol parameter. "
                f"Example: Net(name='{self.name}', is_power=True, "
                f"power_symbol='power:GND')"
            )

        # Physical constraint validation
        if self.trace_current is not None and self.trace_current <= 0:
            raise CircuitSynthError(
                f"trace_current must be positive, got {self.trace_current}"
            )

        if self.impedance is not None and self.impedance <= 0:
            raise CircuitSynthError(
                f"impedance must be positive, got {self.impedance}"
            )

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

    def to_dict(self) -> Dict[str, Any]:
        """Serialize Net to dictionary for JSON encoding."""
        return {
            "name": self.name,
            "is_power": self.is_power,
            "power_symbol": self.power_symbol,
            "trace_current": self.trace_current,
            "impedance": self.impedance,
            "properties": self.properties,
        }

    @staticmethod
    def from_dict(data: Dict[str, Any]) -> "Net":
        """
        Deserialize Net from dictionary.

        Note: This creates a Net outside of circuit context, so it won't
        auto-register. Caller must manually add to circuit._nets.
        """
        # Create Net with minimal circuit context handling
        # We'll manually construct it to avoid circuit registration
        net = object.__new__(Net)
        net.name = data.get("name")
        net._pins = set()
        net.is_power = data.get("is_power", False)
        net.power_symbol = data.get("power_symbol")
        net.trace_current = data.get("trace_current")
        net.impedance = data.get("impedance")
        net.properties = data.get("properties", {})
        return net

    def __repr__(self):
        nm = self.name if self.name else "unnamed"
        flags = []
        if self.is_power:
            flags.append("power")
        if self.impedance is not None:
            flags.append(f"{self.impedance}Ω")

        flag_str = f" [{', '.join(flags)}]" if flags else ""
        return f"<Net {nm}{flag_str}>"
