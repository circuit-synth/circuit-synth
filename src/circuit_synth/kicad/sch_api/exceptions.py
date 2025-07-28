"""
Custom exceptions for the KiCad Schematic API.

These exceptions provide specific error handling for component operations,
making it easier to diagnose and handle errors in client code.
"""


class ComponentError(Exception):
    """Base exception for all component-related operations."""

    pass


class ComponentNotFoundError(ComponentError):
    """Raised when a component with the given reference is not found."""

    def __init__(self, reference: str, message: str = None):
        self.reference = reference
        if message is None:
            message = f"Component with reference '{reference}' not found"
        super().__init__(message)


class InvalidLibraryError(ComponentError):
    """Raised when a library ID is invalid or the symbol is not found."""

    def __init__(self, lib_id: str, message: str = None):
        self.lib_id = lib_id
        if message is None:
            message = f"Invalid library ID or symbol not found: '{lib_id}'"
        super().__init__(message)


class PlacementError(ComponentError):
    """Raised when a component cannot be placed at the requested position."""

    def __init__(self, position: tuple, reason: str = None):
        self.position = position
        message = f"Cannot place component at position {position}"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class ConnectionError(ComponentError):
    """Raised when there's an error updating component connections."""

    def __init__(self, component_ref: str, operation: str, reason: str = None):
        self.component_ref = component_ref
        self.operation = operation
        message = f"Error {operation} connections for component '{component_ref}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)


class DuplicateReferenceError(ComponentError):
    """Raised when trying to add a component with a reference that already exists."""

    def __init__(self, reference: str):
        self.reference = reference
        message = f"Component with reference '{reference}' already exists"
        super().__init__(message)


class InvalidPropertyError(ComponentError):
    """Raised when trying to set an invalid property on a component."""

    def __init__(self, property_name: str, reason: str = None):
        self.property_name = property_name
        message = f"Invalid property '{property_name}'"
        if reason:
            message += f": {reason}"
        super().__init__(message)
