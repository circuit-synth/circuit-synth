"""High-level Schematic class wrapping Rust functionality."""

from typing import Optional, Tuple, List, Dict, Any, Union
from pathlib import Path


class Schematic:
    """
    A KiCad schematic that can be programmatically created and modified.
    
    This class provides a Pythonic interface to the high-performance
    Rust backend for KiCad file manipulation.
    
    Attributes:
        name: The name of the schematic
        components: Dictionary of components by reference
        nets: Dictionary of nets and their connections
    
    Examples:
        Creating a simple voltage divider::
        
            sch = Schematic("VoltageDivider")
            
            # Add resistors
            sch.add_component("R1", "Device:R", "10k", (50, 50))
            sch.add_component("R2", "Device:R", "10k", (50, 100))
            
            # Connect components
            sch.connect("R1", 1, "VIN")
            sch.connect("R1", 2, "VOUT")
            sch.connect("R2", 1, "VOUT")
            sch.connect("R2", 2, "GND")
            
            # Save to file
            sch.save("voltage_divider.kicad_sch")
    """
    
    def __init__(self, name: str = "NewSchematic"):
        """
        Initialize a new schematic.
        
        Args:
            name: Name of the schematic
        """
        from kicad._rust import create_minimal_schematic
        
        self.name = name
        self._schematic_str = create_minimal_schematic()
        self._components: Dict[str, Dict[str, Any]] = {}
        self._nets: Dict[str, List[Tuple[str, int]]] = {}
    
    def add_component(
        self,
        reference: str,
        symbol: str,
        value: Optional[str] = None,
        position: Tuple[float, float] = (0.0, 0.0),
        rotation: float = 0.0,
        footprint: Optional[str] = None,
        unit: Optional[int] = None,
    ) -> "Schematic":
        """
        Add a component to the schematic.
        
        Args:
            reference: Component reference (e.g., "R1", "U1")
            symbol: KiCad symbol library reference (e.g., "Device:R")
            value: Component value (e.g., "10k", "100nF")
            position: (x, y) position in mm
            rotation: Rotation in degrees (0, 90, 180, 270)
            footprint: PCB footprint reference
            unit: Unit number for multi-unit components
            
        Returns:
            Self for method chaining
            
        Examples:
            >>> sch.add_component("R1", "Device:R", "10k", (50, 50))
            >>> sch.add_component("U1", "MCU_ST:STM32F103C8Tx", 
            ...                   position=(100, 100),
            ...                   footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm")
        """
        from kicad._rust import add_component_to_schematic
        
        self._schematic_str = add_component_to_schematic(
            self._schematic_str,
            reference,
            symbol,
            value or reference,
            position[0],
            position[1],
            rotation,
            footprint,
        )
        
        self._components[reference] = {
            "symbol": symbol,
            "value": value,
            "position": position,
            "rotation": rotation,
            "footprint": footprint,
            "unit": unit,
        }
        
        return self
    
    def remove_component(self, reference: str) -> "Schematic":
        """
        Remove a component from the schematic.
        
        Args:
            reference: Component reference to remove
            
        Returns:
            Self for method chaining
            
        Note:
            This feature requires the latest Rust backend with
            component removal support.
        """
        # This will be available once the Rust function is exported
        # from kicad._rust import remove_component_from_schematic
        # self._schematic_str = remove_component_from_schematic(
        #     self._schematic_str, reference
        # )
        
        if reference in self._components:
            del self._components[reference]
            
        # Remove from nets
        for net_connections in self._nets.values():
            net_connections[:] = [
                (ref, pin) for ref, pin in net_connections 
                if ref != reference
            ]
        
        return self
    
    def connect(self, ref: str, pin: Union[int, str], net_name: str) -> "Schematic":
        """
        Connect a component pin to a net.
        
        Args:
            ref: Component reference
            pin: Pin number or name
            net_name: Name of the net
            
        Returns:
            Self for method chaining
            
        Examples:
            >>> sch.connect("R1", 1, "VCC")
            >>> sch.connect("U1", "PA0", "LED_CTRL")
        """
        if net_name not in self._nets:
            self._nets[net_name] = []
        
        # Convert pin to int if it's a string number
        if isinstance(pin, str) and pin.isdigit():
            pin = int(pin)
            
        self._nets[net_name].append((ref, pin))
        
        # Note: Actual wire connections would be handled by Rust backend
        # when that functionality is added
        
        return self
    
    def add_hierarchical_label(
        self,
        name: str,
        shape: str = "input",
        position: Tuple[float, float] = (25.0, 25.0),
        rotation: float = 0.0,
    ) -> "Schematic":
        """
        Add a hierarchical label to the schematic.
        
        Args:
            name: Label name
            shape: Label shape ("input", "output", "bidirectional", "passive")
            position: (x, y) position in mm
            rotation: Rotation in degrees
            
        Returns:
            Self for method chaining
            
        Examples:
            >>> sch.add_hierarchical_label("VCC", "input", (25, 50))
            >>> sch.add_hierarchical_label("DATA_OUT", "output", (200, 100))
        """
        # This will be available once the Rust function is exported
        # from kicad._rust import add_hierarchical_label_to_schematic
        # self._schematic_str = add_hierarchical_label_to_schematic(
        #     self._schematic_str, name, shape, 
        #     position[0], position[1], rotation
        # )
        
        return self
    
    def save(self, filename: Union[str, Path]) -> None:
        """
        Save the schematic to a KiCad file.
        
        Args:
            filename: Output filename (should end with .kicad_sch)
            
        Examples:
            >>> sch.save("my_circuit.kicad_sch")
            >>> sch.save(Path("output") / "circuit.kicad_sch")
        """
        filename = Path(filename)
        
        # Ensure .kicad_sch extension
        if not filename.suffix:
            filename = filename.with_suffix(".kicad_sch")
        elif filename.suffix != ".kicad_sch":
            print(f"Warning: Expected .kicad_sch extension, got {filename.suffix}")
        
        # Create parent directories if needed
        filename.parent.mkdir(parents=True, exist_ok=True)
        
        with open(filename, "w", encoding="utf-8") as f:
            f.write(self._schematic_str)
    
    def to_string(self) -> str:
        """
        Get the schematic as a KiCad format string.
        
        Returns:
            The schematic in KiCad S-expression format
        """
        return self._schematic_str
    
    @property
    def components(self) -> Dict[str, Dict[str, Any]]:
        """Get dictionary of all components."""
        return self._components.copy()
    
    @property
    def nets(self) -> Dict[str, List[Tuple[str, Union[int, str]]]]:
        """Get dictionary of all nets and their connections."""
        return self._nets.copy()
    
    def __repr__(self) -> str:
        return (
            f"Schematic(name='{self.name}', "
            f"components={len(self._components)}, "
            f"nets={len(self._nets)})"
        )
    
    def __str__(self) -> str:
        return f"KiCad Schematic '{self.name}' with {len(self._components)} components"


def load_schematic(filename: Union[str, Path]) -> Schematic:
    """
    Load a schematic from a KiCad file.
    
    Args:
        filename: Path to the .kicad_sch file
        
    Returns:
        A Schematic object
        
    Examples:
        >>> sch = load_schematic("existing_circuit.kicad_sch")
        >>> print(sch.components)
    """
    filename = Path(filename)
    
    with open(filename, "r", encoding="utf-8") as f:
        content = f.read()
    
    sch = Schematic(name=filename.stem)
    sch._schematic_str = content
    
    # TODO: Parse components and nets from loaded schematic
    # This would require implementing parsing in the Rust backend
    
    return sch