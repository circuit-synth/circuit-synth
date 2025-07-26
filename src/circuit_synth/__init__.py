"""
Circuit-Synth: Open Source Circuit Synthesis Framework

A Python framework for programmatic circuit design with KiCad integration.
"""

__version__ = "0.1.0"

# Core imports
from .core import (
    Circuit,
    Component,
    Net,
    Pin,
    circuit,
)

# Exception imports
from .core import (
    ComponentError,
    ValidationError,
    CircuitSynthError,
)

# Dependency injection imports
from .core import (
    DependencyContainer,
    ServiceLocator,
    IDependencyContainer,
)

# Interfaces imports
from .interfaces import (
    IKiCadIntegration,
    ICircuitModel,
    KiCadGenerationConfig,
)

# KiCad API imports
from .kicad_api import (
    Schematic,
    SchematicSymbol,
    Wire,
    Junction,
    Label,
)

# Reference manager and netlist exporters
from .core.reference_manager import ReferenceManager
from .core.netlist_exporter import NetlistExporter
from .core.enhanced_netlist_exporter import EnhancedNetlistExporter

# KiCad integration
from .kicad.unified_kicad_integration import create_unified_kicad_integration

__all__ = [
    # Core
    "Circuit",
    "Component",
    "Net",
    "Pin",
    "circuit",
    # Exceptions
    "ComponentError",
    "ValidationError",
    "CircuitSynthError",
    # Dependency injection
    "DependencyContainer",
    "ServiceLocator",
    "IDependencyContainer",
    # Interfaces
    "IKiCadIntegration",
    "ICircuitModel",
    "KiCadGenerationConfig",
    # KiCad API
    "Schematic",
    "SchematicSymbol",
    "Wire",
    "Junction",
    "Label",
    # Reference manager and exporters
    "ReferenceManager",
    "NetlistExporter",
    "EnhancedNetlistExporter",
    # KiCad integration
    "create_unified_kicad_integration",
]