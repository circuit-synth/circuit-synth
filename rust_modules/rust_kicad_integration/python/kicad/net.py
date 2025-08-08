"""Net class for KiCad schematics."""

from typing import List, Tuple, Union, Optional
from dataclasses import dataclass, field


@dataclass
class Net:
    """
    Represents a net (electrical connection) in a KiCad schematic.
    
    A net connects multiple component pins together, representing
    an electrical connection in the circuit.
    
    Attributes:
        name: Name of the net (e.g., "VCC", "GND", "SIGNAL1")
        connections: List of (reference, pin) tuples
        label_position: Optional position for net label
    
    Examples:
        >>> vcc = Net("VCC")
        >>> vcc.add_connection("R1", 1)
        >>> vcc.add_connection("C1", 1)
        >>> vcc.add_connection("U1", 14)
        
        >>> gnd = Net("GND")
        >>> gnd.connect_pins([("R1", 2), ("C1", 2), ("U1", 7)])
    """
    
    name: str
    connections: List[Tuple[str, Union[int, str]]] = field(default_factory=list)
    label_position: Optional[Tuple[float, float]] = None
    
    def __post_init__(self):
        """Validate net data after initialization."""
        if not self.name:
            raise ValueError("Net name cannot be empty")
        
        # Common net name validation
        if self.name.startswith(" ") or self.name.endswith(" "):
            print(f"Warning: Net name '{self.name}' has leading/trailing spaces")
    
    def add_connection(self, reference: str, pin: Union[int, str]) -> "Net":
        """
        Add a single connection to the net.
        
        Args:
            reference: Component reference (e.g., "R1")
            pin: Pin number or name
            
        Returns:
            Self for method chaining
            
        Examples:
            >>> net = Net("SIGNAL")
            >>> net.add_connection("U1", "PA0").add_connection("R1", 1)
        """
        self.connections.append((reference, pin))
        return self
    
    def connect_pins(self, pins: List[Tuple[str, Union[int, str]]]) -> "Net":
        """
        Connect multiple pins to the net at once.
        
        Args:
            pins: List of (reference, pin) tuples
            
        Returns:
            Self for method chaining
            
        Examples:
            >>> vcc = Net("VCC")
            >>> vcc.connect_pins([
            ...     ("U1", 14),
            ...     ("U2", 16),
            ...     ("C1", 1),
            ...     ("C2", 1)
            ... ])
        """
        self.connections.extend(pins)
        return self
    
    def remove_connection(self, reference: str, pin: Optional[Union[int, str]] = None) -> "Net":
        """
        Remove connections from the net.
        
        Args:
            reference: Component reference
            pin: Optional specific pin (removes all pins of component if None)
            
        Returns:
            Self for method chaining
        """
        if pin is None:
            # Remove all connections for this reference
            self.connections = [
                (ref, p) for ref, p in self.connections 
                if ref != reference
            ]
        else:
            # Remove specific pin connection
            self.connections = [
                (ref, p) for ref, p in self.connections 
                if not (ref == reference and p == pin)
            ]
        return self
    
    def get_connected_components(self) -> List[str]:
        """
        Get list of all components connected to this net.
        
        Returns:
            List of unique component references
            
        Examples:
            >>> net = Net("VCC")
            >>> net.connect_pins([("R1", 1), ("R2", 1), ("C1", 1)])
            >>> net.get_connected_components()
            ['R1', 'R2', 'C1']
        """
        return list(set(ref for ref, _ in self.connections))
    
    def get_component_pins(self, reference: str) -> List[Union[int, str]]:
        """
        Get all pins of a component connected to this net.
        
        Args:
            reference: Component reference
            
        Returns:
            List of pin numbers/names
        """
        return [pin for ref, pin in self.connections if ref == reference]
    
    def is_connected(self, reference: str, pin: Optional[Union[int, str]] = None) -> bool:
        """
        Check if a component/pin is connected to this net.
        
        Args:
            reference: Component reference
            pin: Optional specific pin to check
            
        Returns:
            True if connected
        """
        if pin is None:
            return any(ref == reference for ref, _ in self.connections)
        return (reference, pin) in self.connections
    
    def __len__(self) -> int:
        """Return number of connections in the net."""
        return len(self.connections)
    
    def __str__(self) -> str:
        return f"Net '{self.name}' with {len(self.connections)} connections"
    
    def __repr__(self) -> str:
        return f"Net(name='{self.name}', connections={len(self.connections)})"


# Predefined common nets

def power_net(voltage: str = "VCC") -> Net:
    """
    Create a power supply net.
    
    Args:
        voltage: Voltage rail name (e.g., "VCC", "3V3", "5V", "12V")
        
    Returns:
        Net configured as power rail
    """
    return Net(voltage)


def ground_net() -> Net:
    """
    Create a ground net.
    
    Returns:
        Net configured as ground
    """
    return Net("GND")


class NetManager:
    """
    Manages multiple nets in a schematic.
    
    This class helps organize and manage all nets in a circuit,
    providing methods to create, find, and connect nets.
    
    Examples:
        >>> nets = NetManager()
        >>> nets.create("VCC").connect("U1", 14)
        >>> nets.create("GND").connect("U1", 7)
        >>> nets.connect("R1", 1, "VCC")
        >>> nets.connect("R1", 2, "GND")
    """
    
    def __init__(self):
        """Initialize the net manager."""
        self._nets: Dict[str, Net] = {}
    
    def create(self, name: str) -> Net:
        """
        Create a new net.
        
        Args:
            name: Net name
            
        Returns:
            The created Net object
            
        Raises:
            ValueError: If net already exists
        """
        if name in self._nets:
            raise ValueError(f"Net '{name}' already exists")
        
        net = Net(name)
        self._nets[name] = net
        return net
    
    def get(self, name: str) -> Optional[Net]:
        """
        Get a net by name.
        
        Args:
            name: Net name
            
        Returns:
            Net object or None if not found
        """
        return self._nets.get(name)
    
    def get_or_create(self, name: str) -> Net:
        """
        Get existing net or create if it doesn't exist.
        
        Args:
            name: Net name
            
        Returns:
            Net object
        """
        if name not in self._nets:
            self._nets[name] = Net(name)
        return self._nets[name]
    
    def connect(
        self, 
        reference: str, 
        pin: Union[int, str], 
        net_name: str
    ) -> None:
        """
        Connect a component pin to a net.
        
        Args:
            reference: Component reference
            pin: Pin number or name
            net_name: Name of the net
        """
        net = self.get_or_create(net_name)
        net.add_connection(reference, pin)
    
    def find_net_for_pin(
        self, 
        reference: str, 
        pin: Union[int, str]
    ) -> Optional[str]:
        """
        Find which net a pin is connected to.
        
        Args:
            reference: Component reference
            pin: Pin number or name
            
        Returns:
            Net name or None if not connected
        """
        for net_name, net in self._nets.items():
            if net.is_connected(reference, pin):
                return net_name
        return None
    
    @property
    def nets(self) -> Dict[str, Net]:
        """Get all nets."""
        return self._nets.copy()
    
    def __len__(self) -> int:
        """Return number of nets."""
        return len(self._nets)
    
    def __repr__(self) -> str:
        return f"NetManager(nets={len(self._nets)})"