"""Exceptions for Circuit Synth."""


class CircuitSynthError(Exception):
    """Base exception for all Circuit Synth errors."""

    pass


class LibraryNotFound(CircuitSynthError):
    """Raised when a library file cannot be found."""

    pass


class SymbolNotFoundError(CircuitSynthError):
    """Raised when a symbol is not found in a library."""

    pass


class ParseError(CircuitSynthError):
    """Raised when there is an error parsing a file."""

    pass


class ValidationError(CircuitSynthError):
    """Raised when a property validation fails."""

    pass


class ComponentError(CircuitSynthError):
    """Raised when there is an error with a component or its pins."""

    pass


class ConnectionError(CircuitSynthError):
    """Raised when there is an error with connections."""

    pass
