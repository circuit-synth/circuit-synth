# FILE: src/circuit_synth/core/decorators.py

from functools import wraps

_CURRENT_CIRCUIT = None


def get_current_circuit():
    return _CURRENT_CIRCUIT


def set_current_circuit(circuit):
    global _CURRENT_CIRCUIT
    _CURRENT_CIRCUIT = circuit


def circuit(_func=None, *, name=None, comments=True):
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
    """

    def _decorator(func):
        @wraps(func)
        def _wrapper(*args, **kwargs):
            from .circuit import Circuit  # local import to avoid circular import

            global _CURRENT_CIRCUIT

            parent_circuit = _CURRENT_CIRCUIT
            # Capture docstring to use as circuit description
            docstring = func.__doc__ or ""  # or you could .strip() if you prefer

            # Check if enable_comments decorator was used
            use_comments = comments or getattr(func, "_enable_comments", False)

            c = Circuit(
                name=name or func.__name__,
                description=docstring,
                auto_comments=use_comments,
            )

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
