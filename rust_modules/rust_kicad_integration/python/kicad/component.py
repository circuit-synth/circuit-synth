"""Component class for KiCad schematics."""

from typing import Optional, Tuple, Dict, Any
from dataclasses import dataclass, field


@dataclass
class Component:
    """
    Represents a component in a KiCad schematic.
    
    This is a data class that holds component information before
    adding it to a schematic.
    
    Attributes:
        reference: Component reference designator (e.g., "R1", "U1")
        symbol: KiCad symbol library reference (e.g., "Device:R")
        value: Component value (e.g., "10k", "100nF")
        position: (x, y) position in mm
        rotation: Rotation in degrees (0, 90, 180, 270)
        footprint: PCB footprint reference
        unit: Unit number for multi-unit components
        properties: Additional properties
    
    Examples:
        >>> r1 = Component("R1", "Device:R", "10k")
        >>> r1.position = (50, 50)
        >>> r1.footprint = "Resistor_SMD:R_0603_1608Metric"
        
        >>> c1 = Component(
        ...     reference="C1",
        ...     symbol="Device:C",
        ...     value="100nF",
        ...     position=(100, 50),
        ...     footprint="Capacitor_SMD:C_0603_1608Metric"
        ... )
    """
    
    reference: str
    symbol: str
    value: Optional[str] = None
    position: Tuple[float, float] = (0.0, 0.0)
    rotation: float = 0.0
    footprint: Optional[str] = None
    unit: Optional[int] = None
    properties: Dict[str, Any] = field(default_factory=dict)
    
    def __post_init__(self):
        """Validate component data after initialization."""
        if not self.reference:
            raise ValueError("Component reference cannot be empty")
        
        if not self.symbol:
            raise ValueError("Component symbol cannot be empty")
        
        # Validate rotation is a standard angle
        valid_rotations = [0, 90, 180, 270, 0.0, 90.0, 180.0, 270.0]
        if self.rotation not in valid_rotations:
            print(f"Warning: Non-standard rotation {self.rotation}° for {self.reference}")
        
        # Default value to reference if not provided
        if self.value is None:
            self.value = self.reference
    
    def to_dict(self) -> Dict[str, Any]:
        """
        Convert component to dictionary format.
        
        Returns:
            Dictionary representation of the component
        """
        return {
            "reference": self.reference,
            "symbol": self.symbol,
            "value": self.value,
            "position": self.position,
            "rotation": self.rotation,
            "footprint": self.footprint,
            "unit": self.unit,
            "properties": self.properties,
        }
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Component":
        """
        Create a Component from a dictionary.
        
        Args:
            data: Dictionary with component data
            
        Returns:
            Component instance
        """
        return cls(**data)
    
    def __str__(self) -> str:
        return f"{self.reference} ({self.symbol}): {self.value}"
    
    def __repr__(self) -> str:
        return (
            f"Component(reference='{self.reference}', "
            f"symbol='{self.symbol}', value='{self.value}')"
        )


# Convenience functions for common components

def resistor(
    reference: str,
    value: str,
    position: Tuple[float, float] = (0.0, 0.0),
    footprint: str = "Resistor_SMD:R_0603_1608Metric"
) -> Component:
    """
    Create a resistor component.
    
    Args:
        reference: Reference designator (e.g., "R1")
        value: Resistance value (e.g., "10k", "4.7k")
        position: (x, y) position
        footprint: SMD footprint (default 0603)
        
    Returns:
        Component configured as a resistor
    """
    return Component(
        reference=reference,
        symbol="Device:R",
        value=value,
        position=position,
        footprint=footprint
    )


def capacitor(
    reference: str,
    value: str,
    position: Tuple[float, float] = (0.0, 0.0),
    footprint: str = "Capacitor_SMD:C_0603_1608Metric"
) -> Component:
    """
    Create a capacitor component.
    
    Args:
        reference: Reference designator (e.g., "C1")
        value: Capacitance value (e.g., "100nF", "10uF")
        position: (x, y) position
        footprint: SMD footprint (default 0603)
        
    Returns:
        Component configured as a capacitor
    """
    return Component(
        reference=reference,
        symbol="Device:C",
        value=value,
        position=position,
        footprint=footprint
    )


def inductor(
    reference: str,
    value: str,
    position: Tuple[float, float] = (0.0, 0.0),
    footprint: Optional[str] = None
) -> Component:
    """
    Create an inductor component.
    
    Args:
        reference: Reference designator (e.g., "L1")
        value: Inductance value (e.g., "10uH", "100nH")
        position: (x, y) position
        footprint: SMD footprint
        
    Returns:
        Component configured as an inductor
    """
    return Component(
        reference=reference,
        symbol="Device:L",
        value=value,
        position=position,
        footprint=footprint
    )


def led(
    reference: str,
    color: Optional[str] = None,
    position: Tuple[float, float] = (0.0, 0.0),
    footprint: str = "LED_SMD:LED_0603_1608Metric"
) -> Component:
    """
    Create an LED component.
    
    Args:
        reference: Reference designator (e.g., "D1")
        color: LED color (e.g., "Red", "Green", "Blue")
        position: (x, y) position
        footprint: SMD footprint (default 0603)
        
    Returns:
        Component configured as an LED
    """
    return Component(
        reference=reference,
        symbol="Device:LED",
        value=color or "LED",
        position=position,
        footprint=footprint
    )