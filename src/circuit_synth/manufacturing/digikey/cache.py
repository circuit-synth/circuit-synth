#!/usr/bin/env python3
"""
DigiKey Cache System for Circuit-Synth

Provides caching for DigiKey API responses to reduce API calls and improve performance.
"""

import hashlib
import json
import logging
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)


class DigiKeyCache:
    """
    Cache manager for DigiKey API responses.

    Reduces API calls and improves response times by caching:
    - Product search results
    - Product details
    - Pricing and availability data
    """

    def __init__(self, cache_dir: Optional[Path] = None, ttl_seconds: int = 3600):
        """
        Initialize the cache manager.

        Args:
            cache_dir: Directory for cache storage
            ttl_seconds: Time-to-live for cached data (default 1 hour)
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".circuit_synth" / "digikey_cache"

        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        self.ttl_seconds = ttl_seconds

        # Create subdirectories for different cache types
        self.search_cache_dir = self.cache_dir / "searches"
        self.product_cache_dir = self.cache_dir / "products"
        self.search_cache_dir.mkdir(exist_ok=True)
        self.product_cache_dir.mkdir(exist_ok=True)

        logger.debug(f"DigiKey cache initialized at: {self.cache_dir}")

    def _get_cache_key(self, data: Any) -> str:
        """Generate a cache key from input data."""
        if isinstance(data, dict):
            data_str = json.dumps(data, sort_keys=True)
        else:
            data_str = str(data)

        return hashlib.md5(data_str.encode()).hexdigest()

    def _is_cache_valid(self, cache_file: Path) -> bool:
        """Check if a cache file is still valid."""
        if not cache_file.exists():
            return False

        # Check if cache has expired
        cache_age = time.time() - cache_file.stat().st_mtime
        return cache_age < self.ttl_seconds

    def _read_cache(self, cache_file: Path) -> Optional[Dict[str, Any]]:
        """Read data from cache file."""
        try:
            with open(cache_file, "r") as f:
                return json.load(f)
        except Exception as e:
            logger.warning(f"Failed to read cache file {cache_file}: {e}")
            return None

    def _write_cache(self, cache_file: Path, data: Dict[str, Any]):
        """Write data to cache file."""
        try:
            with open(cache_file, "w") as f:
                json.dump(data, f, indent=2)
            logger.debug(f"Cached data to {cache_file}")
        except Exception as e:
            logger.warning(f"Failed to write cache file {cache_file}: {e}")

    def get_search_cache(
        self, search_params: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """
        Get cached search results.

        Args:
            search_params: Search parameters (keyword, filters, etc.)

        Returns:
            Cached search results or None if not found/expired
        """
        cache_key = self._get_cache_key(search_params)
        cache_file = self.search_cache_dir / f"{cache_key}.json"

        if self._is_cache_valid(cache_file):
            logger.debug(f"Cache hit for search: {search_params.get('keyword', '')}")
            return self._read_cache(cache_file)

        return None

    def set_search_cache(self, search_params: Dict[str, Any], results: Dict[str, Any]):
        """
        Cache search results.

        Args:
            search_params: Search parameters
            results: Search results to cache
        """
        cache_key = self._get_cache_key(search_params)
        cache_file = self.search_cache_dir / f"{cache_key}.json"

        cache_data = {
            "params": search_params,
            "results": results,
            "cached_at": time.time(),
        }

        self._write_cache(cache_file, cache_data)

    def get_product_cache(self, part_number: str) -> Optional[Dict[str, Any]]:
        """
        Get cached product details.

        Args:
            part_number: DigiKey part number

        Returns:
            Cached product data or None if not found/expired
        """
        cache_file = self.product_cache_dir / f"{part_number}.json"

        if self._is_cache_valid(cache_file):
            logger.debug(f"Cache hit for product: {part_number}")
            return self._read_cache(cache_file)

        return None

    def set_product_cache(self, part_number: str, product_data: Dict[str, Any]):
        """
        Cache product details.

        Args:
            part_number: DigiKey part number
            product_data: Product data to cache
        """
        cache_file = self.product_cache_dir / f"{part_number}.json"

        cache_data = {
            "part_number": part_number,
            "data": product_data,
            "cached_at": time.time(),
        }

        self._write_cache(cache_file, cache_data)

    def clear_cache(self, cache_type: Optional[str] = None):
        """
        Clear cache files.

        Args:
            cache_type: Type of cache to clear ("search", "product", or None for all)
        """
        if cache_type == "search" or cache_type is None:
            for cache_file in self.search_cache_dir.glob("*.json"):
                cache_file.unlink()
            logger.info("Cleared search cache")

        if cache_type == "product" or cache_type is None:
            for cache_file in self.product_cache_dir.glob("*.json"):
                cache_file.unlink()
            logger.info("Cleared product cache")

    def get_cache_stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        search_files = list(self.search_cache_dir.glob("*.json"))
        product_files = list(self.product_cache_dir.glob("*.json"))

        # Calculate cache sizes
        search_size = sum(f.stat().st_size for f in search_files)
        product_size = sum(f.stat().st_size for f in product_files)

        # Count valid vs expired
        valid_searches = sum(1 for f in search_files if self._is_cache_valid(f))
        valid_products = sum(1 for f in product_files if self._is_cache_valid(f))

        return {
            "search_cache": {
                "total_files": len(search_files),
                "valid_files": valid_searches,
                "expired_files": len(search_files) - valid_searches,
                "size_bytes": search_size,
            },
            "product_cache": {
                "total_files": len(product_files),
                "valid_files": valid_products,
                "expired_files": len(product_files) - valid_products,
                "size_bytes": product_size,
            },
            "total_size_mb": (search_size + product_size) / (1024 * 1024),
            "ttl_seconds": self.ttl_seconds,
        }


# Global cache instance
_cache_instance: Optional[DigiKeyCache] = None


def get_digikey_cache() -> DigiKeyCache:
    """Get or create the global DigiKey cache instance."""
    global _cache_instance
    if _cache_instance is None:
        _cache_instance = DigiKeyCache()
    return _cache_instance


def cached_digikey_search(
    keyword: str,
    filters: Optional[Dict[str, Any]] = None,
    max_results: int = 25,
) -> Optional[List[Dict[str, Any]]]:
    """
    Perform a cached DigiKey search.

    Args:
        keyword: Search term
        filters: Optional search filters
        max_results: Maximum results to return

    Returns:
        Cached search results or None if not cached
    """
    cache = get_digikey_cache()

    search_params = {
        "keyword": keyword,
        "filters": filters or {},
        "max_results": max_results,
    }

    cached_data = cache.get_search_cache(search_params)
    if cached_data:
        return cached_data.get("results", {}).get("Products", [])

    return None


def cached_digikey_product(part_number: str) -> Optional[Dict[str, Any]]:
    """
    Get cached product details.

    Args:
        part_number: DigiKey part number

    Returns:
        Cached product data or None if not cached
    """
    cache = get_digikey_cache()

    cached_data = cache.get_product_cache(part_number)
    if cached_data:
        return cached_data.get("data")

    return None
