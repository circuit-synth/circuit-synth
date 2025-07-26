"""
High-performance Rust-based symbol search engine for KiCad symbols.

This package provides a drop-in replacement for the Python symbol search
implementation with significant performance improvements:

- Sub-50ms index building for 21,000+ symbols
- Sub-5ms fuzzy searches with high accuracy  
- Memory-efficient data structures
- Seamless integration with existing Python code

Example:
    >>> from rust_symbol_search import RustSymbolSearcher
    >>> searcher = RustSymbolSearcher()
    >>> symbols = {"R": "Device", "C": "Device", "LM7805": "Regulator_Linear"}
    >>> searcher.build_index(symbols)
    >>> results = searcher.search("resistor", max_results=5)
    >>> print(results[0]["name"])  # "R"
"""

from typing import Dict, List, Optional, Any, Union
import warnings

try:
    from ._rust_symbol_search import (
        RustSymbolSearcher as _RustSymbolSearcher,
        benchmark_rust_search,
        compare_performance,
    )
    RUST_AVAILABLE = True
except ImportError as e:
    RUST_AVAILABLE = False
    _import_error = e

__version__ = "0.1.0"
__author__ = "Circuit Synth Team"
__all__ = [
    "RustSymbolSearcher",
    "benchmark_rust_search", 
    "compare_performance",
    "is_available",
]


def is_available() -> bool:
    """Check if the Rust extension is available."""
    return RUST_AVAILABLE


class RustSymbolSearcher:
    """
    High-performance symbol searcher using Rust backend.
    
    This class provides a Python interface to the Rust-based symbol search
    engine, offering significant performance improvements over pure Python
    implementations.
    
    Attributes:
        _searcher: The underlying Rust searcher instance
        _ready: Whether the searcher is ready for use
    """
    
    def __init__(self):
        """Initialize the symbol searcher."""
        if not RUST_AVAILABLE:
            raise ImportError(
                f"Rust symbol search extension not available: {_import_error}. "
                "Please install with: pip install rust-symbol-search"
            )
        
        self._searcher = _RustSymbolSearcher()
        self._ready = False
    
    def build_index(self, symbols: Dict[str, str]) -> None:
        """
        Build the search index from symbol data.
        
        Args:
            symbols: Dictionary mapping symbol_name -> library_name
            
        Raises:
            RuntimeError: If index building fails
            TypeError: If symbols is not a dictionary
        """
        if not isinstance(symbols, dict):
            raise TypeError("symbols must be a dictionary")
        
        if not symbols:
            warnings.warn("Building index with empty symbol set", UserWarning)
        
        self._searcher.build_index(symbols)
        self._ready = True
    
    def search(
        self, 
        query: str, 
        max_results: int = 10, 
        min_score: float = 0.3
    ) -> List[Dict[str, Any]]:
        """
        Search for symbols matching the query.
        
        Args:
            query: Search query string
            max_results: Maximum number of results to return
            min_score: Minimum match score threshold (0.0 to 1.0)
            
        Returns:
            List of search result dictionaries with keys:
            - lib_id: Full symbol identifier (e.g., "Device:R")
            - name: Symbol name (e.g., "R")
            - library: Library name (e.g., "Device")
            - score: Match score (0.0 to 1.0)
            - match_type: Type of match ("exact", "fuzzy", etc.)
            - match_details: Detailed scoring information
            
        Raises:
            RuntimeError: If searcher is not ready or search fails
            ValueError: If parameters are invalid
        """
        if not self._ready:
            raise RuntimeError("Searcher not ready. Call build_index() first.")
        
        if not isinstance(query, str):
            raise TypeError("query must be a string")
        
        if not query.strip():
            return []
        
        if max_results <= 0:
            raise ValueError("max_results must be positive")
        
        if not 0.0 <= min_score <= 1.0:
            raise ValueError("min_score must be between 0.0 and 1.0")
        
        return self._searcher.search(query, max_results, min_score)
    
    def get_stats(self) -> Dict[str, Any]:
        """
        Get search engine statistics.
        
        Returns:
            Dictionary with performance statistics including:
            - symbol_count: Number of indexed symbols
            - index_build_time_ns: Time to build index (nanoseconds)
            - total_searches: Number of searches performed
            - avg_search_time_ns: Average search time (nanoseconds)
            - index_size_bytes: Estimated memory usage
        """
        return self._searcher.get_stats()
    
    def is_ready(self) -> bool:
        """Check if the searcher is ready for use."""
        return self._ready
    
    def __repr__(self) -> str:
        """Get string representation."""
        status = "ready" if self._ready else "not ready"
        return f"RustSymbolSearcher({status})"
    
    def __str__(self) -> str:
        """Get string representation."""
        return "Rust-based high-performance symbol searcher"


def benchmark_search_performance(
    symbols: Dict[str, str],
    queries: List[str],
    iterations: int = 100
) -> Dict[str, Any]:
    """
    Benchmark search performance.
    
    Args:
        symbols: Symbol dictionary for indexing
        queries: List of search queries to test
        iterations: Number of iterations to run
        
    Returns:
        Dictionary with benchmark results
    """
    if not RUST_AVAILABLE:
        raise ImportError("Rust extension not available for benchmarking")
    
    return benchmark_rust_search(symbols, queries, iterations)


def compare_with_python(
    symbols: Dict[str, str],
    queries: List[str]
) -> Dict[str, Any]:
    """
    Compare Rust vs Python performance.
    
    Args:
        symbols: Symbol dictionary for testing
        queries: List of search queries
        
    Returns:
        Dictionary with comparison results
    """
    if not RUST_AVAILABLE:
        raise ImportError("Rust extension not available for comparison")
    
    return compare_performance(symbols, queries)


# Compatibility aliases
RustSymbolSearch = RustSymbolSearcher  # Alternative name