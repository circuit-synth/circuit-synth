"""
Circuit-Synth: Open Source Circuit Synthesis Framework

A Python framework for programmatic circuit design with KiCad integration.
"""

__version__ = "0.1.0"

# Dependency injection imports
# Exception imports
# Core imports
from .core import (
    Circuit,
    CircuitSynthError,
    Component,
    ComponentError,
    DependencyContainer,
    IDependencyContainer,
    Net,
    Pin,
    ServiceLocator,
    ValidationError,
    circuit,
)

# Annotation imports
from .core.annotations import (
    Graphic,
    Table,
    TextBox,
    TextProperty,
    add_table,
    add_text,
    add_text_box,
)
from .core.enhanced_netlist_exporter import EnhancedNetlistExporter
from .core.netlist_exporter import NetlistExporter

# Reference manager and netlist exporters
from .core.reference_manager import ReferenceManager

# Interfaces imports
from .interfaces import (
    ICircuitModel,
    IKiCadIntegration,
    KiCadGenerationConfig,
)

# KiCad integration
from .kicad.unified_kicad_integration import create_unified_kicad_integration

# KiCad API imports
from .kicad_api import (
    Junction,
    Label,
    Schematic,
    SchematicSymbol,
    Wire,
)

__all__ = [
    # Core
    "Circuit",
    "Component",
    "Net",
    "Pin",
    "circuit",
    # Annotations
    "TextProperty",
    "TextBox",
    "Table",
    "Graphic",
    "add_text",
    "add_text_box",
    "add_table",
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
