#!/usr/bin/env python3
"""
JLCPCB Search Cache System

Implements caching for JLCPCB API calls to avoid repeated searches
and improve performance for component availability checking.
"""

import hashlib
import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional


class JLCPCBCache:
    """
    Cache system for JLCPCB search results.

    Caches component search results with timestamp-based expiration
    to reduce API calls and improve search performance.
    """

    def __init__(
        self, cache_dir: Optional[Path] = None, cache_duration_hours: int = 24
    ):
        """
        Initialize JLCPCB cache.

        Args:
            cache_dir: Directory to store cache files (default: ~/.circuit-synth/cache)
            cache_duration_hours: Cache expiration time in hours
        """
        if cache_dir is None:
            cache_dir = Path.home() / ".circuit-synth" / "cache" / "jlcpcb"

        self.cache_dir = cache_dir
        self.cache_duration = cache_duration_hours * 3600  # Convert to seconds
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # In-memory cache for this session
        self._memory_cache: Dict[str, Dict[str, Any]] = {}

    def _get_cache_key(self, search_term: str) -> str:
        """Generate cache key from search term."""
        return hashlib.md5(search_term.lower().encode()).hexdigest()

    def _get_cache_file(self, cache_key: str) -> Path:
        """Get cache file path for a given key."""
        return self.cache_dir / f"{cache_key}.json"

    def _is_cache_valid(self, cache_data: Dict[str, Any]) -> bool:
        """Check if cached data is still valid."""
        if "timestamp" not in cache_data:
            return False

        cache_age = time.time() - cache_data["timestamp"]
        return cache_age < self.cache_duration

    def get(self, search_term: str) -> Optional[List[Dict[str, Any]]]:
        """
        Get cached search results for a search term.

        Args:
            search_term: Component search term

        Returns:
            Cached search results or None if not found/expired
        """
        cache_key = self._get_cache_key(search_term)

        # Check memory cache first
        if cache_key in self._memory_cache:
            if self._is_cache_valid(self._memory_cache[cache_key]):
                return self._memory_cache[cache_key]["results"]
            else:
                del self._memory_cache[cache_key]

        # Check disk cache
        cache_file = self._get_cache_file(cache_key)
        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    cache_data = json.load(f)

                if self._is_cache_valid(cache_data):
                    # Load into memory cache
                    self._memory_cache[cache_key] = cache_data
                    return cache_data["results"]
                else:
                    # Remove expired cache file
                    cache_file.unlink()
            except (json.JSONDecodeError, KeyError):
                # Remove corrupted cache file
                cache_file.unlink()

        return None

    def set(self, search_term: str, results: List[Dict[str, Any]]) -> None:
        """
        Cache search results for a search term.

        Args:
            search_term: Component search term
            results: Search results to cache
        """
        cache_key = self._get_cache_key(search_term)
        cache_data = {
            "timestamp": time.time(),
            "search_term": search_term,
            "results": results,
        }

        # Store in memory cache
        self._memory_cache[cache_key] = cache_data

        # Store in disk cache
        cache_file = self._get_cache_file(cache_key)
        try:
            with open(cache_file, "w") as f:
                json.dump(cache_data, f, indent=2)
        except Exception as e:
            print(f"Warning: Could not write cache file {cache_file}: {e}")

    def clear_expired(self) -> int:
        """
        Clear expired cache entries.

        Returns:
            Number of entries cleared
        """
        cleared_count = 0

        # Clear expired memory cache
        expired_keys = []
        for key, cache_data in self._memory_cache.items():
            if not self._is_cache_valid(cache_data):
                expired_keys.append(key)

        for key in expired_keys:
            del self._memory_cache[key]
            cleared_count += 1

        # Clear expired disk cache
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                with open(cache_file, "r") as f:
                    cache_data = json.load(f)

                if not self._is_cache_valid(cache_data):
                    cache_file.unlink()
                    cleared_count += 1
            except (json.JSONDecodeError, KeyError):
                # Remove corrupted cache file
                cache_file.unlink()
                cleared_count += 1

        return cleared_count

    def clear_all(self) -> int:
        """
        Clear all cache entries.

        Returns:
            Number of entries cleared
        """
        cleared_count = 0

        # Clear memory cache
        cleared_count += len(self._memory_cache)
        self._memory_cache.clear()

        # Clear disk cache
        for cache_file in self.cache_dir.glob("*.json"):
            cache_file.unlink()
            cleared_count += 1

        return cleared_count

    def get_cache_info(self) -> Dict[str, Any]:
        """Get cache statistics and information."""
        disk_files = list(self.cache_dir.glob("*.json"))

        return {
            "cache_dir": str(self.cache_dir),
            "cache_duration_hours": self.cache_duration / 3600,
            "memory_entries": len(self._memory_cache),
            "disk_entries": len(disk_files),
            "total_size_bytes": sum(f.stat().st_size for f in disk_files),
        }


# Global cache instance
_global_cache = None


def get_jlcpcb_cache() -> JLCPCBCache:
    """Get global JLCPCB cache instance."""
    global _global_cache
    if _global_cache is None:
        _global_cache = JLCPCBCache()
    return _global_cache


def cached_jlcpcb_search(search_term: str, search_function) -> List[Dict[str, Any]]:
    """
    Perform cached JLCPCB search.

    Args:
        search_term: Component search term
        search_function: Function to call if not cached

    Returns:
        Search results (cached or fresh)
    """
    cache = get_jlcpcb_cache()

    # Try to get from cache
    results = cache.get(search_term)
    if results is not None:
        return results

    # Not cached, perform search
    results = search_function(search_term)

    # Cache the results
    if results:
        cache.set(search_term, results)

    return results
