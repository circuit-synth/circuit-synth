"""
kicad - High-performance KiCad file manipulation library

This package provides a Pythonic interface to create and manipulate
KiCad schematic and PCB files using a high-performance Rust backend.

Examples:
    Basic usage::
    
        import kicad
        
        # Create a new schematic
        sch = kicad.Schematic("MyCircuit")
        
        # Add components
        sch.add_component("R1", "Device:R", "10k", (50, 50))
        sch.add_component("C1", "Device:C", "100nF", (100, 50))
        
        # Save to file
        sch.save("my_circuit.kicad_sch")

"""

__version__ = "0.1.0"
__author__ = "Circuit-Synth Contributors"
__email__ = "shane@circuit-synth.com"

# Import Rust bindings
try:
    from kicad._rust import (
        # Low-level functions from Rust
        create_minimal_schematic,
        create_empty_schematic,
        add_component_to_schematic,
        load_schematic as _rust_load_schematic,
        # Note: These will be available once exported properly
        # add_hierarchical_label_to_schematic,
        # remove_component_from_schematic,
    )
    _RUST_AVAILABLE = True
except ImportError as e:
    _RUST_AVAILABLE = False
    _import_error = e
    
    # Provide stub functions with helpful error messages
    def _not_available(*args, **kwargs):
        raise ImportError(
            "Rust backend not available. "
            "Please install with: pip install kicad[rust] "
            f"Original error: {_import_error}"
        )
    
    create_minimal_schematic = _not_available
    create_empty_schematic = _not_available
    add_component_to_schematic = _not_available
    _rust_load_schematic = _not_available

# Import Python wrappers
from .schematic import Schematic, load_schematic
from .component import Component
from .net import Net

# High-level API
__all__ = [
    # Classes
    "Schematic",
    "Component", 
    "Net",
    # Functions
    "load_schematic",
    "create_schematic",
    # Version info
    "__version__",
]

# Convenience function
def create_schematic(name: str = "NewSchematic") -> Schematic:
    """
    Create a new KiCad schematic.
    
    Args:
        name: Name of the schematic
        
    Returns:
        A new Schematic object
        
    Examples:
        >>> sch = create_schematic("MyCircuit")
        >>> sch.add_component("R1", "Device:R", "10k")
    """
    return Schematic(name)