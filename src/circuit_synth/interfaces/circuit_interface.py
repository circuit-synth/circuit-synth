"""
Circuit Model Abstract Interfaces

Defines abstract interfaces for core circuit models to eliminate circular dependencies
and provide clear contracts between core models and other modules.
"""

from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from typing import Any, Callable, Dict, Iterator, List, Optional, Tuple, Union


class PinType(Enum):
    """Pin type enumeration"""

    INPUT = "input"
    OUTPUT = "output"
    BIDIRECTIONAL = "bidirectional"
    POWER = "power"
    PASSIVE = "passive"


class ComponentType(Enum):
    """Component type enumeration"""

    RESISTOR = "resistor"
    CAPACITOR = "capacitor"
    INDUCTOR = "inductor"
    IC = "ic"
    CONNECTOR = "connector"
    TRANSISTOR = "transistor"
    DIODE = "diode"
    LED = "led"
    SWITCH = "switch"
    OTHER = "other"


@dataclass
class PinInfo:
    """Pin information structure"""

    number: str
    name: str
    pin_type: PinType
    electrical_type: str
    position: Tuple[float, float]
    connected_net: Optional[str] = None


@dataclass
class ComponentInfo:
    """Component information structure"""

    reference: str
    value: str
    footprint: str
    symbol: str
    library: str
    component_type: ComponentType
    properties: Dict[str, str]
    pins: List[PinInfo]
    position: Tuple[float, float]


class ICircuitModel(ABC):
    """
    Abstract interface for circuit models.

    Provides a unified API for circuit operations without exposing
    implementation details or creating circular dependencies.
    """

    @abstractmethod
    def get_name(self) -> str:
        """Get circuit name"""
        pass

    @abstractmethod
    def set_name(self, name: str) -> None:
        """Set circuit name"""
        pass

    @abstractmethod
    def add_component(self, component: "IComponentModel") -> bool:
        """Add a component to the circuit"""
        pass

    @abstractmethod
    def remove_component(self, reference: str) -> bool:
        """Remove a component by reference"""
        pass

    @abstractmethod
    def get_component(self, reference: str) -> Optional["IComponentModel"]:
        """Get a component by reference"""
        pass

    @abstractmethod
    def get_components(self) -> List["IComponentModel"]:
        """Get all components in the circuit"""
        pass

    @abstractmethod
    def add_net(self, net: "INetModel") -> bool:
        """Add a net to the circuit"""
        pass

    @abstractmethod
    def remove_net(self, net_name: str) -> bool:
        """Remove a net by name"""
        pass

    @abstractmethod
    def get_net(self, net_name: str) -> Optional["INetModel"]:
        """Get a net by name"""
        pass

    @abstractmethod
    def get_nets(self) -> List["INetModel"]:
        """Get all nets in the circuit"""
        pass

    @abstractmethod
    def connect(self, component_ref: str, pin_number: str, net_name: str) -> bool:
        """Connect a component pin to a net"""
        pass

    @abstractmethod
    def disconnect(self, component_ref: str, pin_number: str) -> bool:
        """Disconnect a component pin"""
        pass

    @abstractmethod
    def validate(self) -> Tuple[bool, List[str]]:
        """Validate the circuit and return any errors"""
        pass

    @abstractmethod
    def get_statistics(self) -> Dict[str, Any]:
        """Get circuit statistics"""
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert circuit to dictionary representation"""
        pass

    @abstractmethod
    def from_dict(self, data: Dict[str, Any]) -> bool:
        """Load circuit from dictionary representation"""
        pass


class IComponentModel(ABC):
    """
    Abstract interface for component models.

    Provides a unified API for component operations without exposing
    implementation details or creating circular dependencies.
    """

    @abstractmethod
    def get_reference(self) -> str:
        """Get component reference designator"""
        pass

    @abstractmethod
    def set_reference(self, reference: str) -> None:
        """Set component reference designator"""
        pass

    @abstractmethod
    def get_value(self) -> str:
        """Get component value"""
        pass

    @abstractmethod
    def set_value(self, value: str) -> None:
        """Set component value"""
        pass

    @abstractmethod
    def get_footprint(self) -> str:
        """Get component footprint"""
        pass

    @abstractmethod
    def set_footprint(self, footprint: str) -> None:
        """Set component footprint"""
        pass

    @abstractmethod
    def get_symbol(self) -> str:
        """Get component symbol"""
        pass

    @abstractmethod
    def set_symbol(self, symbol: str) -> None:
        """Set component symbol"""
        pass

    @abstractmethod
    def get_library(self) -> str:
        """Get component library"""
        pass

    @abstractmethod
    def set_library(self, library: str) -> None:
        """Set component library"""
        pass

    @abstractmethod
    def get_component_type(self) -> ComponentType:
        """Get component type"""
        pass

    @abstractmethod
    def get_property(self, name: str) -> Optional[str]:
        """Get a component property"""
        pass

    @abstractmethod
    def set_property(self, name: str, value: str) -> None:
        """Set a component property"""
        pass

    @abstractmethod
    def get_properties(self) -> Dict[str, str]:
        """Get all component properties"""
        pass

    @abstractmethod
    def get_pins(self) -> List["IPinModel"]:
        """Get all component pins"""
        pass

    @abstractmethod
    def get_pin(self, pin_number: str) -> Optional["IPinModel"]:
        """Get a specific pin by number"""
        pass

    @abstractmethod
    def get_position(self) -> Tuple[float, float]:
        """Get component position"""
        pass

    @abstractmethod
    def set_position(self, x: float, y: float) -> None:
        """Set component position"""
        pass

    @abstractmethod
    def get_rotation(self) -> float:
        """Get component rotation"""
        pass

    @abstractmethod
    def set_rotation(self, rotation: float) -> None:
        """Set component rotation"""
        pass

    @abstractmethod
    def validate(self) -> Tuple[bool, List[str]]:
        """Validate the component and return any errors"""
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert component to dictionary representation"""
        pass


class IPinModel(ABC):
    """
    Abstract interface for pin models.

    Provides a unified API for pin operations without exposing
    implementation details or creating circular dependencies.
    """

    @abstractmethod
    def get_number(self) -> str:
        """Get pin number"""
        pass

    @abstractmethod
    def get_name(self) -> str:
        """Get pin name"""
        pass

    @abstractmethod
    def set_name(self, name: str) -> None:
        """Set pin name"""
        pass

    @abstractmethod
    def get_pin_type(self) -> PinType:
        """Get pin type"""
        pass

    @abstractmethod
    def set_pin_type(self, pin_type: PinType) -> None:
        """Set pin type"""
        pass

    @abstractmethod
    def get_electrical_type(self) -> str:
        """Get electrical type"""
        pass

    @abstractmethod
    def set_electrical_type(self, electrical_type: str) -> None:
        """Set electrical type"""
        pass

    @abstractmethod
    def get_position(self) -> Tuple[float, float]:
        """Get pin position relative to component"""
        pass

    @abstractmethod
    def set_position(self, x: float, y: float) -> None:
        """Set pin position relative to component"""
        pass

    @abstractmethod
    def get_connected_net(self) -> Optional["INetModel"]:
        """Get the net this pin is connected to"""
        pass

    @abstractmethod
    def connect_to_net(self, net: "INetModel") -> bool:
        """Connect this pin to a net"""
        pass

    @abstractmethod
    def disconnect(self) -> bool:
        """Disconnect this pin from any net"""
        pass

    @abstractmethod
    def is_connected(self) -> bool:
        """Check if pin is connected to a net"""
        pass

    @abstractmethod
    def validate(self) -> Tuple[bool, List[str]]:
        """Validate the pin and return any errors"""
        pass


class INetModel(ABC):
    """
    Abstract interface for net models.

    Provides a unified API for net operations without exposing
    implementation details or creating circular dependencies.
    """

    @abstractmethod
    def get_name(self) -> str:
        """Get net name"""
        pass

    @abstractmethod
    def set_name(self, name: str) -> None:
        """Set net name"""
        pass

    @abstractmethod
    def add_pin(self, pin: "IPinModel") -> bool:
        """Add a pin to this net"""
        pass

    @abstractmethod
    def remove_pin(self, pin: "IPinModel") -> bool:
        """Remove a pin from this net"""
        pass

    @abstractmethod
    def get_pins(self) -> List["IPinModel"]:
        """Get all pins connected to this net"""
        pass

    @abstractmethod
    def get_pin_count(self) -> int:
        """Get number of pins connected to this net"""
        pass

    @abstractmethod
    def is_connected_to(self, component_ref: str, pin_number: str) -> bool:
        """Check if a specific component pin is connected to this net"""
        pass

    @abstractmethod
    def get_connected_components(self) -> List[str]:
        """Get list of component references connected to this net"""
        pass

    @abstractmethod
    def validate(self) -> Tuple[bool, List[str]]:
        """Validate the net and return any errors"""
        pass

    @abstractmethod
    def to_dict(self) -> Dict[str, Any]:
        """Convert net to dictionary representation"""
        pass


# Factory function types for dependency injection
CircuitModelFactory = Callable[[], ICircuitModel]
ComponentModelFactory = Callable[[], IComponentModel]
NetModelFactory = Callable[[], INetModel]
PinModelFactory = Callable[[], IPinModel]
