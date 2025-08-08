# Python Package Structure for kicad-rust

## Directory Layout
```
kicad-rust/
├── Cargo.toml                   # Rust crate configuration
├── pyproject.toml               # Python package configuration
├── README.md                    # Shared README for both Rust and Python
├── LICENSE-MIT                  # License file
├── src/                         # Rust source code
│   ├── lib.rs                   # Rust library entry point
│   ├── python_bindings.rs       # PyO3 bindings
│   └── ...                      # Other Rust modules
├── python/                      # Python package
│   └── kicad/                   # Python module
│       ├── __init__.py          # Python API
│       ├── schematic.py         # High-level Schematic class
│       ├── component.py         # Component helpers
│       ├── net.py              # Net management
│       └── py.typed            # Type hints marker
├── examples/
│   ├── rust/                    # Rust examples
│   │   └── voltage_divider.rs
│   └── python/                  # Python examples
│       ├── basic_circuit.py
│       ├── hierarchical_design.py
│       └── component_library.py
└── tests/
    ├── rust/                    # Rust tests
    └── python/                  # Python tests
        └── test_schematic.py
```

## Python Module (`python/kicad/__init__.py`)
```python
"""
kicad - High-performance KiCad file manipulation library

This package provides a Pythonic interface to create and manipulate
KiCad schematic and PCB files using a high-performance Rust backend.
"""

__version__ = "0.1.0"

# Import Rust bindings
from kicad._rust import (
    # Low-level functions
    create_minimal_schematic,
    add_component_to_schematic,
    load_schematic,
    # Classes if exported
    PyRustSchematicWriter,
    PySimpleComponent,
)

# Import Python wrappers
from .schematic import Schematic
from .component import Component
from .net import Net

# High-level API
__all__ = [
    "Schematic",
    "Component", 
    "Net",
    "load_schematic",
    "__version__",
]

# Convenience function
def create_schematic(name: str = "NewSchematic") -> Schematic:
    """Create a new KiCad schematic."""
    return Schematic(name)
```

## High-Level Python Wrapper (`python/kicad/schematic.py`)
```python
"""High-level Schematic class wrapping Rust functionality."""

from typing import Optional, Tuple, List, Dict, Any
from kicad._rust import (
    create_minimal_schematic,
    add_component_to_schematic,
    load_schematic as rust_load_schematic,
)


class Schematic:
    """
    A KiCad schematic that can be programmatically created and modified.
    
    This class provides a Pythonic interface to the high-performance
    Rust backend for KiCad file manipulation.
    
    Examples:
        >>> sch = Schematic("MyCircuit")
        >>> sch.add_component("R1", "Device:R", "10k", (50, 50))
        >>> sch.add_component("C1", "Device:C", "100nF", (100, 50))
        >>> sch.save("my_circuit.kicad_sch")
    """
    
    def __init__(self, name: str = "NewSchematic"):
        """Initialize a new schematic."""
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
    ) -> None:
        """
        Add a component to the schematic.
        
        Args:
            reference: Component reference (e.g., "R1", "U1")
            symbol: KiCad symbol library reference (e.g., "Device:R")
            value: Component value (e.g., "10k", "100nF")
            position: (x, y) position in mm
            rotation: Rotation in degrees
            footprint: PCB footprint reference
        """
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
        }
    
    def connect(self, ref: str, pin: int, net_name: str) -> None:
        """
        Connect a component pin to a net.
        
        Args:
            ref: Component reference
            pin: Pin number
            net_name: Name of the net
        """
        if net_name not in self._nets:
            self._nets[net_name] = []
        self._nets[net_name].append((ref, pin))
        # Note: Actual connection would be handled by Rust backend
    
    def save(self, filename: str) -> None:
        """Save the schematic to a KiCad file."""
        with open(filename, "w") as f:
            f.write(self._schematic_str)
    
    def __repr__(self) -> str:
        return f"Schematic(name='{self.name}', components={len(self._components)})"


def load_schematic(filename: str) -> Schematic:
    """Load a schematic from a KiCad file."""
    with open(filename, "r") as f:
        content = f.read()
    
    sch = Schematic()
    sch._schematic_str = content
    # TODO: Parse components and nets from loaded schematic
    return sch
```

## Publishing Strategy

### 1. Rust Crate (crates.io)
```bash
# Publish Rust crate only
cargo publish --no-default-features
```

### 2. Python Package (PyPI)
```bash
# Build Python wheels for multiple platforms
maturin build --release --features python

# Or use cibuildwheel for multi-platform
pip install cibuildwheel
cibuildwheel --platform linux

# Upload to PyPI
twine upload dist/*
```

### 3. Dual Usage Examples

#### From Rust:
```rust
// Cargo.toml
[dependencies]
kicad = "0.1"
```

```rust
use kicad::{Schematic, Component};

let mut sch = Schematic::new("MyCircuit");
sch.add_component(...);
```

#### From Python:
```bash
pip install kicad
```

```python
import kicad

sch = kicad.Schematic("MyCircuit")
sch.add_component("R1", "Device:R", "10k", (50, 50))
sch.save("circuit.kicad_sch")
```

## Benefits of Dual Publishing

1. **Wider Reach**: Available to both Rust and Python communities
2. **Performance**: Python users get native Rust performance
3. **Type Safety**: Rust users get compile-time guarantees
4. **Ease of Use**: Python users get a familiar API
5. **Single Codebase**: Maintain one implementation for both

## CI/CD for Both Packages

The GitHub Actions workflow will:
1. Test Rust code with `cargo test`
2. Test Python bindings with `pytest`
3. Build wheels for multiple Python versions/platforms
4. Publish to both crates.io and PyPI on release