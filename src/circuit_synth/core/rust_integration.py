"""
Automatic Rust integration module for circuit-synth.

This module provides seamless Rust acceleration by:
1. Automatically detecting available Rust extensions
2. Providing transparent fallback to Python implementations
3. Zero configuration required from users

The goal is to eventually replace Python implementations entirely with Rust,
while maintaining 100% API compatibility.
"""

import importlib
import logging
from functools import wraps
from typing import Any, Callable, Optional

logger = logging.getLogger(__name__)


class RustAccelerator:
    """
    Automatic Rust acceleration manager.

    This class handles detection and loading of Rust extensions,
    providing transparent acceleration without user intervention.
    """

    def __init__(self):
        self.rust_modules = {}
        self._detect_rust_modules()

    def _detect_rust_modules(self):
        """Automatically detect available Rust modules."""
        # List of Rust modules we want to accelerate (in priority order)
        rust_candidates = [
            ("kicad_writer", "circuit_synth.rust.kicad_writer"),
            ("symbol_cache", "circuit_synth.rust.symbol_cache"),
            ("placement", "circuit_synth.rust.placement"),
            # Fallback to standalone modules if integrated not available
            ("kicad_writer_standalone", "rust_kicad_schematic_writer"),
            ("symbol_cache_standalone", "rust_symbol_cache"),
            ("placement_standalone", "rust_force_directed_placement"),
        ]

        for name, module_name in rust_candidates:
            try:
                module = importlib.import_module(module_name)
                self.rust_modules[name] = module
                logger.debug(f"Rust acceleration available: {name} ({module_name})")
            except ImportError:
                logger.debug(f"Rust module not available: {name} ({module_name})")

        if self.rust_modules:
            logger.debug(
                f"Rust acceleration active for {len(self.rust_modules)} modules"
            )
        else:
            logger.debug("Using Python implementations (Rust not available)")

    def get_rust_function(
        self, module_name: str, function_name: str
    ) -> Optional[Callable]:
        """Get a Rust function if available, None otherwise."""
        if module_name in self.rust_modules:
            module = self.rust_modules[module_name]
            return getattr(module, function_name, None)
        return None

    def has_rust_module(self, module_name: str) -> bool:
        """Check if a Rust module is available."""
        return module_name in self.rust_modules


# Global accelerator instance
_accelerator = RustAccelerator()


def rust_accelerated(rust_module: str, rust_function: str):
    """
    Decorator to automatically use Rust acceleration when available.

    Usage:
        @rust_accelerated('kicad_writer', 'generate_component_sexp')
        def generate_component_sexp_python(component_data):
            # Python implementation
            pass

    The decorator will:
    1. Try to use the Rust function first
    2. Fall back to Python implementation if Rust unavailable
    3. Log execution path for debugging
    """

    def decorator(python_func):
        @wraps(python_func)
        def wrapper(*args, **kwargs):
            # Try Rust first
            rust_func = _accelerator.get_rust_function(rust_module, rust_function)
            if rust_func:
                try:
                    logger.debug(f"Using Rust: {rust_module}.{rust_function}")
                    return rust_func(*args, **kwargs)
                except Exception as e:
                    logger.warning(f"Rust failed, using Python fallback: {e}")

            # Use Python implementation
            logger.debug(f"Using Python: {python_func.__name__}")
            return python_func(*args, **kwargs)

        # Store metadata for introspection
        wrapper.__rust_module__ = rust_module
        wrapper.__rust_function__ = rust_function
        wrapper.__python_impl__ = python_func

        return wrapper

    return decorator


def get_acceleration_status() -> dict:
    """Get current Rust acceleration status."""
    return {
        "rust_available": bool(_accelerator.rust_modules),
        "active_modules": list(_accelerator.rust_modules.keys()),
        "total_modules": len(_accelerator.rust_modules),
    }


# Convenience functions for common operations
def generate_component_sexp(component_data: dict) -> str:
    """Generate KiCad component S-expression with automatic Rust acceleration."""
    rust_func = _accelerator.get_rust_function(
        "kicad_writer", "generate_component_sexp"
    )
    if not rust_func:
        rust_func = _accelerator.get_rust_function(
            "kicad_writer_standalone", "generate_component_sexp"
        )

    if rust_func:
        logger.debug("Using Rust for component S-expression generation")
        return rust_func(component_data)
    else:
        logger.debug("Using Python for component S-expression generation")
        # Import Python implementation
        from circuit_synth.kicad.sch_gen.s_expression_generator import (
            generate_component_sexp_python,
        )

        return generate_component_sexp_python(component_data)


def create_symbol_cache():
    """Create symbol cache with automatic Rust acceleration."""
    rust_cache_class = _accelerator.get_rust_function(
        "symbol_cache", "RustSymbolLibCache"
    )
    if not rust_cache_class:
        rust_cache_class = _accelerator.get_rust_function(
            "symbol_cache_standalone", "RustSymbolLibCache"
        )

    if rust_cache_class:
        logger.debug("🦀 Using Rust symbol cache")
        return rust_cache_class()
    else:
        logger.debug("🐍 Using Python symbol cache")
        from circuit_synth.core.component import SymbolLibCache

        return SymbolLibCache()


def create_placement_engine():
    """Create placement engine with automatic Rust acceleration."""
    rust_placer_class = _accelerator.get_rust_function(
        "placement", "ForceDirectedPlacer"
    )
    if not rust_placer_class:
        rust_placer_class = _accelerator.get_rust_function(
            "placement_standalone", "ForceDirectedPlacer"
        )

    if rust_placer_class:
        logger.debug("🦀 Using Rust placement engine")
        return rust_placer_class()
    else:
        logger.debug("🐍 Using Python placement engine")
        from circuit_synth.kicad_api.schematic.placement import PlacementEngine

        return PlacementEngine()


# Module initialization
logger.debug("Rust integration module initialized")
status = get_acceleration_status()
if status["rust_available"]:
    logger.info(
        f"🚀 Circuit-synth acceleration: {status['total_modules']} Rust modules active"
    )
else:
    logger.debug("Circuit-synth running in Python mode (Rust not available)")
