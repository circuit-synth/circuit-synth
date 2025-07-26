"""
High-performance Rust-based reference manager for Circuit Synth.

This package provides a drop-in replacement for the Python ReferenceManager
implementation with significant performance improvements:

- Sub-millisecond reference generation and validation
- Thread-safe hierarchical reference management
- Memory-efficient data structures
- Seamless integration with existing Python code

Example:
    >>> from rust_reference_manager import RustReferenceManager
    >>> manager = RustReferenceManager()
    >>> ref1 = manager.generate_next_reference("R")
    >>> print(ref1)  # "R1"
    >>> ref2 = manager.generate_next_reference("R") 
    >>> print(ref2)  # "R2"
"""

from typing import Dict, List, Optional, Any, Union, Set
import warnings
import os
import logging

# Feature flag for enabling Rust implementation
ENABLE_RUST_REFERENCE_MANAGER = os.environ.get('ENABLE_RUST_REFERENCE_MANAGER', 'true').lower() == 'true'

try:
    from ._rust_reference_manager import (
        RustReferenceManager as _RustReferenceManager,
        benchmark_reference_generation,
        compare_performance,
        batch_validate_references,
    )
    RUST_AVAILABLE = True
except ImportError as e:
    RUST_AVAILABLE = False
    _import_error = e

# Import Python fallback implementation
try:
    from circuit_synth.core.reference_manager import ReferenceManager as _PythonReferenceManager
    PYTHON_FALLBACK_AVAILABLE = True
except ImportError:
    PYTHON_FALLBACK_AVAILABLE = False
    _PythonReferenceManager = None

__version__ = "0.1.0"
__author__ = "Circuit Synth Team"
__all__ = [
    "RustReferenceManager",
    "benchmark_reference_generation", 
    "compare_performance",
    "batch_validate_references",
    "is_rust_available",
    "is_using_rust",
    "get_implementation_info",
]

# Configure logging
logger = logging.getLogger(__name__)


def is_rust_available() -> bool:
    """Check if the Rust extension is available."""
    return RUST_AVAILABLE


def is_using_rust() -> bool:
    """Check if Rust implementation is currently being used."""
    return RUST_AVAILABLE and ENABLE_RUST_REFERENCE_MANAGER


def get_implementation_info() -> Dict[str, Any]:
    """Get information about the current implementation."""
    return {
        "rust_available": RUST_AVAILABLE,
        "python_fallback_available": PYTHON_FALLBACK_AVAILABLE,
        "using_rust": is_using_rust(),
        "feature_flag_enabled": ENABLE_RUST_REFERENCE_MANAGER,
        "version": __version__,
        "rust_import_error": str(_import_error) if not RUST_AVAILABLE else None,
    }


class RustReferenceManager:
    """
    High-performance reference manager with automatic fallback support.
    
    This class provides a unified interface that automatically uses the Rust
    implementation when available and falls back to the Python implementation
    when necessary.
    
    Attributes:
        _manager: The underlying manager instance (Rust or Python)
        _using_rust: Whether the Rust implementation is being used
        _manager_id: Unique identifier for this manager instance
    """
    
    def __init__(self, initial_counters: Optional[Dict[str, int]] = None):
        """
        Initialize the reference manager.
        
        Args:
            initial_counters: Optional dictionary mapping prefix -> start_number
        """
        self._using_rust = False
        self._manager = None
        self._manager_id = None
        
        # Try to use Rust implementation first
        if is_using_rust():
            try:
                # Convert initial_counters to the format expected by Rust
                rust_counters = None
                if initial_counters:
                    rust_counters = {k: int(v) for k, v in initial_counters.items()}
                
                self._manager = _RustReferenceManager(rust_counters)
                self._using_rust = True
                self._manager_id = self._manager.get_id()
                
                logger.debug(
                    "Initialized Rust reference manager",
                    extra={
                        "component": "REFERENCE_MANAGER",
                        "implementation": "rust",
                        "manager_id": self._manager_id,
                        "initial_counters": initial_counters
                    }
                )
                return
                
            except Exception as e:
                logger.warning(
                    f"Failed to initialize Rust reference manager, falling back to Python: {e}",
                    extra={
                        "component": "REFERENCE_MANAGER",
                        "implementation": "rust",
                        "error": str(e),
                        "fallback": "python"
                    }
                )
        
        # Fall back to Python implementation
        if PYTHON_FALLBACK_AVAILABLE:
            try:
                self._manager = _PythonReferenceManager(initial_counters)
                self._using_rust = False
                self._manager_id = id(self._manager)  # Use Python object id
                
                logger.debug(
                    "Initialized Python reference manager",
                    extra={
                        "component": "REFERENCE_MANAGER",
                        "implementation": "python",
                        "manager_id": self._manager_id,
                        "initial_counters": initial_counters
                    }
                )
                return
                
            except Exception as e:
                logger.error(
                    f"Failed to initialize Python reference manager: {e}",
                    extra={
                        "component": "REFERENCE_MANAGER",
                        "implementation": "python",
                        "error": str(e)
                    }
                )
                raise RuntimeError(f"Failed to initialize reference manager: {e}")
        
        # No implementation available
        raise ImportError(
            "No reference manager implementation available. "
            f"Rust available: {RUST_AVAILABLE}, "
            f"Python fallback available: {PYTHON_FALLBACK_AVAILABLE}"
        )
    
    def set_parent(self, parent: Optional['RustReferenceManager']) -> None:
        """
        Set the parent reference manager.
        
        Args:
            parent: Parent reference manager instance or None
        """
        if self._using_rust:
            parent_id = parent._manager_id if parent else None
            self._manager.set_parent(parent_id)
        else:
            # Python implementation expects the actual manager object
            parent_manager = parent._manager if parent else None
            self._manager.set_parent(parent_manager)
    
    def register_reference(self, reference: str) -> None:
        """
        Register a new reference if it's unique in the hierarchy.
        
        Args:
            reference: Reference string to register
            
        Raises:
            ValueError: If reference format is invalid
            RuntimeError: If reference is already in use
        """
        try:
            self._manager.register_reference(reference)
            
            logger.debug(
                "Registered reference",
                extra={
                    "component": "REFERENCE_MANAGER",
                    "implementation": "rust" if self._using_rust else "python",
                    "manager_id": self._manager_id,
                    "reference": reference
                }
            )
            
        except Exception as e:
            logger.error(
                f"Failed to register reference {reference}: {e}",
                extra={
                    "component": "REFERENCE_MANAGER",
                    "implementation": "rust" if self._using_rust else "python",
                    "manager_id": self._manager_id,
                    "reference": reference,
                    "error": str(e)
                }
            )
            raise
    
    def validate_reference(self, reference: str) -> bool:
        """
        Check if reference is available across entire hierarchy.
        
        Args:
            reference: Reference string to validate
            
        Returns:
            True if reference is available, False otherwise
        """
        return self._manager.validate_reference(reference)
    
    def generate_next_reference(self, prefix: str) -> str:
        """
        Generate next available reference for a prefix.
        
        Args:
            prefix: Prefix string (e.g., "R", "C", "U")
            
        Returns:
            Next available reference string
            
        Raises:
            ValueError: If prefix format is invalid
            RuntimeError: If generation fails
        """
        try:
            reference = self._manager.generate_next_reference(prefix)
            
            logger.debug(
                "Generated reference",
                extra={
                    "component": "REFERENCE_MANAGER",
                    "implementation": "rust" if self._using_rust else "python",
                    "manager_id": self._manager_id,
                    "prefix": prefix,
                    "reference": reference
                }
            )
            
            return reference
            
        except Exception as e:
            logger.error(
                f"Failed to generate reference for prefix {prefix}: {e}",
                extra={
                    "component": "REFERENCE_MANAGER",
                    "implementation": "rust" if self._using_rust else "python",
                    "manager_id": self._manager_id,
                    "prefix": prefix,
                    "error": str(e)
                }
            )
            raise
    
    def generate_next_unnamed_net_name(self) -> str:
        """
        Generate the next globally unique name for unnamed nets.
        
        Returns:
            Next unnamed net name (e.g., "N$1", "N$2")
        """
        net_name = self._manager.generate_next_unnamed_net_name()
        
        logger.debug(
            "Generated unnamed net",
            extra={
                "component": "REFERENCE_MANAGER",
                "implementation": "rust" if self._using_rust else "python",
                "manager_id": self._manager_id,
                "net_name": net_name
            }
        )
        
        return net_name
    
    def set_initial_counters(self, counters: Dict[str, int]) -> None:
        """
        Set initial counters for reference generation.
        
        Args:
            counters: Dictionary mapping prefix -> start_number
        """
        if self._using_rust:
            # Convert to format expected by Rust
            rust_counters = {k: int(v) for k, v in counters.items()}
            self._manager.set_initial_counters(rust_counters)
        else:
            self._manager.set_initial_counters(counters)
        
        logger.debug(
            "Set initial counters",
            extra={
                "component": "REFERENCE_MANAGER",
                "implementation": "rust" if self._using_rust else "python",
                "manager_id": self._manager_id,
                "counters": counters
            }
        )
    
    def get_all_used_references(self) -> Set[str]:
        """
        Get all references used in this subtree.
        
        Returns:
            Set of all used reference strings
        """
        if self._using_rust:
            # Rust returns a list, convert to set for compatibility
            return set(self._manager.get_all_used_references())
        else:
            return self._manager.get_all_used_references()
    
    def clear(self) -> None:
        """
        Clear all registered references and counters.
        """
        self._manager.clear()
        
        logger.debug(
            "Cleared reference manager",
            extra={
                "component": "REFERENCE_MANAGER",
                "implementation": "rust" if self._using_rust else "python",
                "manager_id": self._manager_id
            }
        )
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get performance statistics.
        
        Returns:
            Dictionary with performance statistics
        """
        if self._using_rust:
            return self._manager.get_stats()
        else:
            # Python implementation doesn't have stats, return basic info
            return {
                "implementation": "python",
                "manager_id": self._manager_id,
                "references_count": len(self.get_all_used_references()),
                "performance": {
                    "note": "Performance statistics not available in Python implementation"
                }
            }
    
    def is_using_rust_implementation(self) -> bool:
        """Check if this instance is using the Rust implementation."""
        return self._using_rust
    
    def get_implementation_details(self) -> Dict[str, Any]:
        """Get detailed information about the current implementation."""
        base_info = {
            "using_rust": self._using_rust,
            "manager_id": self._manager_id,
            "version": __version__,
        }
        
        if self._using_rust:
            base_info.update({
                "implementation": "rust",
                "performance_stats_available": True,
                "thread_safe": True,
            })
        else:
            base_info.update({
                "implementation": "python",
                "performance_stats_available": False,
                "thread_safe": False,
            })
        
        return base_info
    
    def __repr__(self) -> str:
        """Get string representation."""
        impl = "Rust" if self._using_rust else "Python"
        return f"RustReferenceManager({impl}, id={self._manager_id})"
    
    def __str__(self) -> str:
        """Get string representation."""
        impl = "Rust" if self._using_rust else "Python"
        return f"{impl}-based reference manager"


# Compatibility functions for benchmarking
def benchmark_performance(
    prefixes: List[str],
    iterations: int = 1000
) -> Dict[str, Any]:
    """
    Benchmark reference generation performance.
    
    Args:
        prefixes: List of prefixes to test
        iterations: Number of iterations to run
        
    Returns:
        Dictionary with benchmark results
    """
    if not is_rust_available():
        raise ImportError("Rust extension not available for benchmarking")
    
    return benchmark_reference_generation(prefixes, iterations)


def compare_implementations(
    prefixes: List[str],
    iterations: int = 100
) -> Dict[str, Any]:
    """
    Compare Rust vs Python performance.
    
    Args:
        prefixes: List of prefixes to test
        iterations: Number of iterations
        
    Returns:
        Dictionary with comparison results
    """
    results = {
        "prefixes": prefixes,
        "iterations": iterations,
        "rust_available": RUST_AVAILABLE,
        "python_available": PYTHON_FALLBACK_AVAILABLE,
    }
    
    # Benchmark Rust implementation
    if RUST_AVAILABLE:
        try:
            rust_results = benchmark_reference_generation(prefixes, iterations)
            results["rust"] = rust_results
        except Exception as e:
            results["rust_error"] = str(e)
    
    # Benchmark Python implementation
    if PYTHON_FALLBACK_AVAILABLE:
        try:
            import time
            
            manager = _PythonReferenceManager()
            start_time = time.perf_counter()
            
            total_generated = 0
            for _ in range(iterations):
                for prefix in prefixes:
                    try:
                        manager.generate_next_reference(prefix)
                        total_generated += 1
                    except Exception:
                        break
            
            end_time = time.perf_counter()
            generation_time_ms = (end_time - start_time) * 1000
            
            results["python"] = {
                "total_generation_time_ms": generation_time_ms,
                "total_generated": total_generated,
                "avg_generation_time_ns": (generation_time_ms * 1_000_000) / total_generated if total_generated > 0 else 0,
                "generations_per_second": total_generated / (generation_time_ms / 1000) if generation_time_ms > 0 else 0,
            }
            
        except Exception as e:
            results["python_error"] = str(e)
    
    # Calculate performance improvement
    if "rust" in results and "python" in results:
        rust_time = results["rust"].get("avg_generation_time_ns", 0)
        python_time = results["python"].get("avg_generation_time_ns", 0)
        
        if rust_time > 0 and python_time > 0:
            improvement = python_time / rust_time
            results["performance_improvement"] = {
                "speedup_factor": improvement,
                "improvement_percentage": (improvement - 1) * 100,
            }
    
    return results


# Auto-log implementation info when module is imported
logger.info(
    "Reference manager module loaded",
    extra={
        "component": "REFERENCE_MANAGER",
        **get_implementation_info()
    }
)

# Warn if Rust is not available
if not RUST_AVAILABLE and ENABLE_RUST_REFERENCE_MANAGER:
    warnings.warn(
        f"Rust reference manager not available, falling back to Python implementation. "
        f"Error: {_import_error}",
        UserWarning,
        stacklevel=2
    )