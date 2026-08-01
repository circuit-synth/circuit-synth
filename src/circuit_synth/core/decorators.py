# FILE: src/circuit_synth/core/decorators.py

import inspect
from functools import wraps
from typing import Any, Dict, List, Optional

from .hierarchy import Port, resolve_port_direction

_CURRENT_CIRCUIT = None
# Track how many times each function has been called to auto-increment instance names
_CIRCUIT_CALL_COUNTERS = {}


def get_current_circuit():
    return _CURRENT_CIRCUIT


def set_current_circuit(circuit):
    global _CURRENT_CIRCUIT
    _CURRENT_CIRCUIT = circuit


def reset_circuit_call_counters():
    """Reset the call counters for auto-incrementing circuit instance names."""
    global _CIRCUIT_CALL_COUNTERS
    _CIRCUIT_CALL_COUNTERS = {}


def _collect_ports(
    func, args, kwargs, ports_override: Optional[Dict[str, Any]]
) -> List[Port]:
    """Build the hierarchical port list for one call of a circuit function.

    A parameter becomes a port when it is annotated with a port marker (such as
    ``Input`` or ``Output``) or named in the decorator's ``ports`` argument, and
    the value bound to it is a Net. If the circuit declares at least one port
    this way, every remaining Net parameter is also exported, as a passive port,
    so that a partially annotated signature still describes a complete block
    interface.

    Args:
        func: The undecorated circuit function.
        args: Positional arguments the circuit was called with.
        kwargs: Keyword arguments the circuit was called with.
        ports_override: Explicit ``{parameter_name: direction}`` mapping from
            the decorator, or None.

    Returns:
        The declared ports, in signature order. Empty if the circuit declares
        no hierarchical interface.
    """
    from .net import Net  # local import to avoid a circular import

    try:
        signature = inspect.signature(func)
        bound = signature.bind_partial(*args, **kwargs)
    except (TypeError, ValueError):
        # Not introspectable, or called in a way we cannot map to parameters.
        return []

    bound.apply_defaults()
    overrides = ports_override or {}

    declared: List[Port] = []
    undeclared: List[Port] = []

    for param_name, param in signature.parameters.items():
        if param.kind in (param.VAR_POSITIONAL, param.VAR_KEYWORD):
            continue

        value = bound.arguments.get(param_name)
        if not isinstance(value, Net):
            continue

        if getattr(value, "is_power", False) and getattr(value, "power_symbol", None):
            # Ground and the supply rails are drawn as power symbols, which
            # connect by name across the whole design. Turning them into sheet
            # pins as well would clutter every block with rails that need no
            # routing, so they are left out of the interface.
            continue

        annotation = (
            None if param.annotation is inspect.Parameter.empty else param.annotation
        )
        direction = resolve_port_direction(annotation, overrides.get(param_name))

        if direction is None:
            undeclared.append(Port(param_name, None, value.name))
        else:
            declared.append(Port(param_name, direction, value.name))

    if not declared:
        return []

    # At least one port was declared, so treat the whole Net interface as ports.
    from .hierarchy import PortDirection

    for port in undeclared:
        port.direction = PortDirection.PASSIVE

    by_name = {port.name: port for port in declared + undeclared}
    return [
        by_name[param_name]
        for param_name in signature.parameters
        if param_name in by_name
    ]


def circuit(_func=None, *, name=None, comments=True, ports=None):
    """
    Decorator that can be used in three ways:
      1) @circuit
         def my_circuit(...):
             ...
      2) @circuit(name="someCircuitName")
         def my_circuit(...):
             ...
      3) @circuit(name="someCircuitName", comments=False)
         def my_circuit(...):
             ...

    Creates a new Circuit object, optionally using `name` as the circuit name.
    If comments=True (default), the function's docstring will be added as a
    text annotation on the generated schematic.
    If there's an existing current circuit (the "parent"), the new circuit is
    attached to the parent as a subcircuit. Then references are finalized
    before returning the child circuit.

    Args:
        _func: The decorated function when used as a bare ``@circuit``.
        name: Explicit circuit name. Defaults to the function name.
        comments: Whether the docstring becomes a schematic annotation.
        ports: Optional ``{parameter_name: direction}`` mapping declaring the
            hierarchical interface of this block, for signatures that are not
            annotated with the ``Input``/``Output``/... markers. Directions are
            strings such as ``"input"``, ``"output"``, ``"bidirectional"``,
            ``"tri_state"`` or ``"passive"``. Declaring ports makes the block
            generate KiCad sheet pins and matching hierarchical labels.
    """

    def _decorator(func):
        @wraps(func)
        def _wrapper(*args, **kwargs):
            from .circuit import Circuit  # local import to avoid circular import

            global _CURRENT_CIRCUIT
            global _CIRCUIT_CALL_COUNTERS

            parent_circuit = _CURRENT_CIRCUIT

            # Reset call counters when starting a new top-level circuit
            if parent_circuit is None:
                _CIRCUIT_CALL_COUNTERS = {}
            # Capture docstring to use as circuit description
            docstring = func.__doc__ or ""  # or you could .strip() if you prefer

            # Check if enable_comments decorator was used
            use_comments = comments or getattr(func, "_enable_comments", False)

            # Auto-increment instance name if no explicit name provided and inside parent circuit
            circuit_name = name
            if circuit_name is None:
                base_name = func.__name__
                if parent_circuit is not None:
                    # Inside a parent circuit - auto-increment the instance name
                    # Track calls per function name
                    if base_name not in _CIRCUIT_CALL_COUNTERS:
                        _CIRCUIT_CALL_COUNTERS[base_name] = 0
                    _CIRCUIT_CALL_COUNTERS[base_name] += 1
                    circuit_name = f"{base_name}_{_CIRCUIT_CALL_COUNTERS[base_name]}"
                else:
                    # Top-level circuit - use function name as-is
                    circuit_name = base_name

            c = Circuit(
                name=circuit_name,
                description=docstring,
                auto_comments=use_comments,
            )

            # Store reference to the circuit function for source rewriting
            c._circuit_func = func

            # Record the hierarchical interface declared by this call, so the
            # KiCad generator can emit sheet pins and hierarchical labels.
            for port in _collect_ports(func, args, kwargs, ports):
                c.add_port(port)

            # Link it as a subcircuit if there's a parent
            if parent_circuit is not None:
                parent_circuit.add_subcircuit(c)

            old_circuit = _CURRENT_CIRCUIT
            _CURRENT_CIRCUIT = c

            try:
                func(*args, **kwargs)
                c.finalize_references()
            finally:
                _CURRENT_CIRCUIT = old_circuit

            return c

        return _wrapper

    if _func is None:
        # @circuit(name=...)
        return _decorator
    else:
        # @circuit
        return _decorator(_func)


def enable_comments(func):
    """
    Decorator that enables automatic docstring extraction for circuit functions.
    This is equivalent to using @circuit(comments=True) but provides a more explicit API.

    Usage:
        @enable_comments
        @circuit(name="my_circuit")
        def my_circuit():
            '''This docstring becomes a schematic annotation.'''
            pass
    """
    # This decorator just marks the function for comment extraction
    # The actual logic is handled by the @circuit decorator
    func._enable_comments = True
    return func
