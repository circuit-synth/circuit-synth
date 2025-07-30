"""
Rust-accelerated component creation helpers.

This module provides drop-in replacements for Python component creation
using high-performance Rust implementations where available.
"""

from ._logger import context_logger

# Try to import Rust-accelerated component creation
try:
    import os
    import sys

    rust_core_path = os.path.join(
        os.path.dirname(__file__), "../../rust_modules/rust_core_circuit_engine/python"
    )
    if rust_core_path not in sys.path:
        sys.path.insert(0, rust_core_path)

    from rust_core_circuit_engine import create_capacitor, create_resistor

    _RUST_COMPONENTS_AVAILABLE = True
    context_logger.info(
        "🦀 RUST_COMPONENTS: ✅ Ultra-high-performance Rust component creation loaded",
        component="RUST_COMPONENTS",
    )
    context_logger.info(
        "🚀 RUST_COMPONENTS: Expected 3-5x component creation speedup",
        component="RUST_COMPONENTS",
    )

except ImportError as e:
    _RUST_COMPONENTS_AVAILABLE = False
    context_logger.info(
        f"🐍 RUST_COMPONENTS: Not available ({e}), using Python fallback",
        component="RUST_COMPONENTS",
    )


def create_rust_resistor(ref=None, value=None, **kwargs):
    """
    Create a resistor using Rust acceleration if available.

    Args:
        ref: Component reference (e.g., "R1")
        value: Resistance value (e.g., "10k")
        **kwargs: Additional component properties

    Returns:
        Component instance with Device:R symbol
    """
    if _RUST_COMPONENTS_AVAILABLE:
        try:
            # Use Rust-accelerated component creation
            context_logger.debug(
                f"🦀 Creating Rust resistor {ref}={value}", component="RUST_COMPONENTS"
            )

            if ref and value:
                return create_resistor(reference=ref, value=value, **kwargs)
            elif ref:
                return create_resistor(reference=ref, **kwargs)
            else:
                return create_resistor(**kwargs)

        except Exception as e:
            context_logger.warning(
                f"🔄 Rust resistor creation failed, using Python fallback: {e}",
                component="RUST_COMPONENTS",
            )

    # Python fallback
    from .component import Component

    context_logger.debug(
        f"🐍 Creating Python resistor {ref}={value}", component="RUST_COMPONENTS"
    )
    return Component("Device:R", ref=ref, value=value, **kwargs)


def create_rust_capacitor(ref=None, value=None, **kwargs):
    """
    Create a capacitor using Rust acceleration if available.

    Args:
        ref: Component reference (e.g., "C1")
        value: Capacitance value (e.g., "100nF")
        **kwargs: Additional component properties

    Returns:
        Component instance with Device:C symbol
    """
    if _RUST_COMPONENTS_AVAILABLE:
        try:
            # Use Rust-accelerated component creation
            context_logger.debug(
                f"🦀 Creating Rust capacitor {ref}={value}", component="RUST_COMPONENTS"
            )

            if ref and value:
                return create_capacitor(reference=ref, value=value, **kwargs)
            elif ref:
                return create_capacitor(reference=ref, **kwargs)
            else:
                return create_capacitor(**kwargs)

        except Exception as e:
            context_logger.warning(
                f"🔄 Rust capacitor creation failed, using Python fallback: {e}",
                component="RUST_COMPONENTS",
            )

    # Python fallback
    from .component import Component

    context_logger.debug(
        f"🐍 Creating Python capacitor {ref}={value}", component="RUST_COMPONENTS"
    )
    return Component("Device:C", ref=ref, value=value, **kwargs)


def get_rust_component_status():
    """Get status of Rust component acceleration."""
    return {
        "rust_available": _RUST_COMPONENTS_AVAILABLE,
        "acceleration_type": (
            "Rust PyO3" if _RUST_COMPONENTS_AVAILABLE else "Python fallback"
        ),
        "estimated_speedup": "3-5x" if _RUST_COMPONENTS_AVAILABLE else "1x (baseline)",
    }


# Export convenience functions
__all__ = ["create_rust_resistor", "create_rust_capacitor", "get_rust_component_status"]
