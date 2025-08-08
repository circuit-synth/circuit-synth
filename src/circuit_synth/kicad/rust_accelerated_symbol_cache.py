"""
Rust-accelerated KiCad symbol library cache for high-performance symbol lookups.

This module provides a drop-in replacement for the Python-based SymbolLibCache
that uses a Rust backend for improved performance on large symbol libraries.
"""

import logging
import sys
from pathlib import Path
from typing import Any, Dict, Optional

logger = logging.getLogger(__name__)

# Try to import Rust implementation
_RUST_SYMBOL_CACHE_AVAILABLE = False
_RustSymbolLibCache = None

# Optional Rust import
try:
    import rust_symbol_cache
    if hasattr(rust_symbol_cache, 'RustSymbolLibCache'):
        _RustSymbolLibCache = rust_symbol_cache.RustSymbolLibCache
        _RUST_SYMBOL_CACHE_AVAILABLE = True
        logger.debug("🦀 Rust symbol cache available and functional")
    else:
        logger.debug("⚠️ Rust module found but missing RustSymbolLibCache")
except ImportError:
    logger.debug("🐍 Using Python symbol cache (Rust not available)")
except Exception as e:
    logger.warning(f"⚠️ Error loading Rust symbol cache: {e}")

# Fallback to Python implementation
if not _RUST_SYMBOL_CACHE_AVAILABLE:
    from ..kicad.kicad_symbol_cache import SymbolLibCache as _PythonSymbolLibCache
    logger.info("🐍 Using Python SymbolLibCache (Rust not available)")


class RustAcceleratedSymbolLibCache:
    """
    Rust-accelerated symbol library cache that seamlessly falls back to Python.
    
    This class provides the same interface as SymbolLibCache but uses a Rust
    backend when available for improved performance.
    """

    def __init__(self, cache_dir: Optional[str] = None):
        """
        Initialize the symbol cache with optional cache directory.
        
        Args:
            cache_dir: Optional directory for caching parsed symbols
        """
        self._impl = None
        
        if _RUST_SYMBOL_CACHE_AVAILABLE and _RustSymbolLibCache:
            try:
                # Try to initialize Rust cache
                if cache_dir:
                    self._impl = _RustSymbolLibCache(cache_dir)
                else:
                    self._impl = _RustSymbolLibCache()
                logger.info("🦀 Using Rust-accelerated symbol cache")
            except Exception as e:
                logger.warning(f"Failed to initialize Rust cache: {e}, falling back to Python")
                self._impl = None
        
        # Fallback to Python implementation
        if self._impl is None:
            self._impl = _PythonSymbolLibCache(cache_dir)
            logger.debug("Using Python symbol cache implementation")

    def parse_library(self, lib_path: str, force_refresh: bool = False) -> None:
        """
        Parse a KiCad symbol library file.
        
        Args:
            lib_path: Path to the .kicad_sym file
            force_refresh: Force re-parsing even if cached
        """
        if self._impl:
            self._impl.parse_library(lib_path, force_refresh)

    def get_symbol(self, library_name: str, symbol_name: str) -> Optional[Dict[str, Any]]:
        """
        Get a symbol from the cache.
        
        Args:
            library_name: Name of the library (without extension)
            symbol_name: Name of the symbol
            
        Returns:
            Symbol data dictionary or None if not found
        """
        if self._impl:
            return self._impl.get_symbol(library_name, symbol_name)
        return None

    def get_all_symbols(self, library_name: str) -> Dict[str, Any]:
        """
        Get all symbols from a library.
        
        Args:
            library_name: Name of the library (without extension)
            
        Returns:
            Dictionary of all symbols in the library
        """
        if self._impl:
            return self._impl.get_all_symbols(library_name)
        return {}

    def clear_cache(self) -> None:
        """Clear the symbol cache."""
        if self._impl:
            self._impl.clear_cache()

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics.
        
        Returns:
            Dictionary with cache statistics
        """
        if self._impl and hasattr(self._impl, 'get_cache_stats'):
            return self._impl.get_cache_stats()
        
        # Provide basic stats if not available
        return {
            "implementation": "rust" if _RUST_SYMBOL_CACHE_AVAILABLE else "python",
            "libraries_cached": 0,
            "symbols_cached": 0,
        }

    @property
    def is_rust_accelerated(self) -> bool:
        """Check if using Rust acceleration."""
        return _RUST_SYMBOL_CACHE_AVAILABLE and isinstance(
            self._impl, _RustSymbolLibCache if _RustSymbolLibCache else type(None)
        )

    def __repr__(self) -> str:
        """String representation."""
        impl_type = "Rust" if self.is_rust_accelerated else "Python"
        return f"<RustAcceleratedSymbolLibCache({impl_type})>"

    def get_implementation_info(self) -> Dict[str, Any]:
        """
        Get information about the current implementation.
        
        Returns:
            Dictionary with implementation details
        """
        return {
            "backend": "rust" if self.is_rust_accelerated else "python",
            "rust_available": _RUST_SYMBOL_CACHE_AVAILABLE,
            "performance_tier": (
                "high" if self.is_rust_accelerated else "standard"
            ),
            "expected_speedup": (
                "10-50x for large libraries" if self.is_rust_accelerated 
                else "baseline"
            ),
        }


# Alias for drop-in replacement
SymbolLibCache = RustAcceleratedSymbolLibCache

# Module-level flag for checking availability
RUST_SYMBOL_CACHE_AVAILABLE = _RUST_SYMBOL_CACHE_AVAILABLE