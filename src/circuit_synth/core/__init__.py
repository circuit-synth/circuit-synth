"""
Core circuit primitives and utilities
"""

from .circuit import Circuit
from .component import Component
from .component_replacement import (
    ReplacementResult,
    find_replaceable_components,
    replace_components,
    replace_multiple,
)
from .decorators import circuit
from .dependency_injection import (
    DependencyContainer,
    IDependencyContainer,
    ServiceLocator,
)
from .exception import CircuitSynthError, ComponentError, ValidationError
from .net import Net
from .pin import Pin

__all__ = [
    "Circuit",
    "Component",
    "Net",
    "Pin",
    "circuit",
    "ComponentError",
    "ValidationError",
    "CircuitSynthError",
    "DependencyContainer",
    "ServiceLocator",
    "IDependencyContainer",
    # Component replacement
    "replace_components",
    "replace_multiple",
    "find_replaceable_components",
    "ReplacementResult",
]
