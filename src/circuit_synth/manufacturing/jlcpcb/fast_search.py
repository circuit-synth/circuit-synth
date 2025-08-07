#!/usr/bin/env python3
"""
Fast JLCPCB Component Search
Optimized direct search without agent overhead for improved performance and reduced token usage.

This module provides a streamlined interface for searching JLCPCB components
with intelligent caching and fast response times.
"""

import logging
import time
from dataclasses import dataclass
from typing import Dict, List, Optional, Tuple

from .cache import JLCPCBCache, get_jlcpcb_cache
from .jlc_web_scraper import JlcWebScraper

logger = logging.getLogger(__name__)


@dataclass
class FastSearchResult:
    """Lightweight search result optimized for speed."""

    part_number: str
    manufacturer_part: str
    description: str
    stock: int
    price: float  # Price for qty 1
    package: str
    basic_part: bool  # Basic vs Extended part
    match_score: float  # How well it matches the query

    def to_dict(self) -> Dict:
        """Convert to dictionary for JSON serialization."""
        return {
            "part_number": self.part_number,
            "manufacturer_part": self.manufacturer_part,
            "description": self.description,
            "stock": self.stock,
            "price": self.price,
            "package": self.package,
            "basic_part": self.basic_part,
            "match_score": self.match_score,
        }


class FastJLCSearch:
    """
    Optimized JLCPCB search implementation.

    Features:
    - Direct search without agent overhead
    - Intelligent caching to avoid repeated searches
    - Fast filtering and sorting
    - Minimal token usage (no LLM required)
    """

    def __init__(self, cache_hours: int = 24):
        """
        Initialize fast search with caching.

        Args:
            cache_hours: How long to cache results (default 24 hours)
        """
        # Create cache directly with duration parameter
        self.cache = JLCPCBCache(cache_duration_hours=cache_hours)
        self.scraper = JlcWebScraper(delay_seconds=0.5)  # Respectful rate limiting
        self._last_search_time = 0
        self._min_delay = 0.5  # Minimum delay between searches

    def search(
        self,
        query: str,
        category: Optional[str] = None,
        min_stock: int = 0,
        prefer_basic: bool = True,
        max_results: int = 10,
        sort_by: str = "relevance",  # relevance, price, stock
    ) -> List[FastSearchResult]:
        """
        Fast search for JLCPCB components.

        Args:
            query: Search query (e.g., "STM32G4", "0.1uF 0603", "LM358")
            category: Optional category filter
            min_stock: Minimum stock required (0 = any)
            prefer_basic: Prefer basic parts over extended
            max_results: Maximum results to return
            sort_by: Sort results by relevance, price, or stock

        Returns:
            List of FastSearchResult objects
        """
        start_time = time.time()

        # Check cache first
        cache_key = f"{query}_{category}_{min_stock}_{prefer_basic}"
        cached_results = self.cache.get(cache_key)

        if cached_results:
            logger.debug(f"Cache hit for query: {query}")
            results = self._parse_cached_results(cached_results)
        else:
            logger.debug(f"Cache miss for query: {query}")
            results = self._perform_search(query, category)

            # Cache the raw results
            if results:
                self.cache.set(cache_key, [r.to_dict() for r in results])

        # Apply filters
        results = self._apply_filters(results, min_stock, prefer_basic)

        # Sort results
        results = self._sort_results(results, sort_by)

        # Limit results
        results = results[:max_results]

        elapsed = time.time() - start_time
        logger.info(
            f"Search completed in {elapsed:.2f}s: {len(results)} results for '{query}'"
        )

        return results

    def search_by_specs(
        self, component_type: str, specs: Dict[str, any], max_results: int = 5
    ) -> List[FastSearchResult]:
        """
        Search by specific component specifications.

        Args:
            component_type: Type of component (resistor, capacitor, etc.)
            specs: Specification dictionary (value, tolerance, package, etc.)
            max_results: Maximum results to return

        Returns:
            List of matching components
        """
        # Build intelligent query from specs
        query = self._build_query_from_specs(component_type, specs)

        # Determine category
        category = self._get_category_for_type(component_type)

        # Perform search
        return self.search(
            query=query,
            category=category,
            min_stock=specs.get("min_stock", 100),
            max_results=max_results,
        )

    def find_cheapest(
        self, query: str, min_stock: int = 100
    ) -> Optional[FastSearchResult]:
        """Find the cheapest component matching the query with sufficient stock."""
        results = self.search(
            query=query, min_stock=min_stock, sort_by="price", max_results=1
        )
        return results[0] if results else None

    def find_most_available(self, query: str) -> Optional[FastSearchResult]:
        """Find the component with the highest stock."""
        results = self.search(query=query, sort_by="stock", max_results=1)
        return results[0] if results else None

    def find_alternatives(
        self, part_number: str, max_alternatives: int = 5
    ) -> List[FastSearchResult]:
        """
        Find alternative components for a given part.

        Args:
            part_number: JLCPCB part number or manufacturer part
            max_alternatives: Maximum alternatives to return

        Returns:
            List of alternative components
        """
        # First search for the exact part to understand what we're replacing
        exact_results = self.search(part_number, max_results=1)

        if not exact_results:
            return []

        original = exact_results[0]

        # Extract key specs from description
        specs = self._extract_specs_from_description(original.description)

        # Search for alternatives
        alternatives = self.search(
            query=specs.get("base_query", original.description.split()[0]),
            min_stock=100,
            max_results=max_alternatives + 1,  # +1 to exclude original
        )

        # Filter out the original part
        alternatives = [a for a in alternatives if a.part_number != part_number]

        return alternatives[:max_alternatives]

    def _perform_search(
        self, query: str, category: Optional[str]
    ) -> List[FastSearchResult]:
        """Perform actual search using web scraper."""
        # Rate limiting
        elapsed = time.time() - self._last_search_time
        if elapsed < self._min_delay:
            time.sleep(self._min_delay - elapsed)

        try:
            # Use existing web scraper
            raw_results = self.scraper.search_components(query, max_results=50)
            self._last_search_time = time.time()

            # Convert to FastSearchResult objects
            results = []
            for item in raw_results:
                result = self._convert_to_fast_result(item, query)
                if result:
                    results.append(result)

            return results

        except Exception as e:
            logger.error(f"Search error: {e}")
            return []

    def _convert_to_fast_result(
        self, raw_data: Dict, query: str
    ) -> Optional[FastSearchResult]:
        """Convert raw search data to FastSearchResult."""
        try:
            # Calculate match score based on query relevance
            match_score = self._calculate_match_score(
                raw_data.get("description", ""),
                raw_data.get("manufacturer_part", ""),
                query,
            )

            return FastSearchResult(
                part_number=raw_data.get("lcsc_part", ""),
                manufacturer_part=raw_data.get("manufacturer_part", ""),
                description=raw_data.get("description", ""),
                stock=int(raw_data.get("stock", 0)),
                price=float(raw_data.get("price", 0)),
                package=raw_data.get("package", ""),
                basic_part=raw_data.get("library_type", "") == "Basic",
                match_score=match_score,
            )
        except (KeyError, ValueError) as e:
            logger.debug(f"Error converting result: {e}")
            return None

    def _calculate_match_score(
        self, description: str, part_number: str, query: str
    ) -> float:
        """Calculate how well a result matches the query."""
        score = 0.0
        query_lower = query.lower()
        desc_lower = description.lower()
        part_lower = part_number.lower()

        # Exact part number match
        if query_lower == part_lower:
            score = 1.0
        # Part number contains query
        elif query_lower in part_lower:
            score = 0.8
        # Description contains all query terms
        elif all(term in desc_lower for term in query_lower.split()):
            score = 0.6
        # Description contains some query terms
        else:
            matches = sum(1 for term in query_lower.split() if term in desc_lower)
            score = 0.3 * (matches / len(query_lower.split()))

        return score

    def _apply_filters(
        self, results: List[FastSearchResult], min_stock: int, prefer_basic: bool
    ) -> List[FastSearchResult]:
        """Apply filters to search results."""
        filtered = results

        # Stock filter
        if min_stock > 0:
            filtered = [r for r in filtered if r.stock >= min_stock]

        # Basic part preference (boost score, don't exclude)
        if prefer_basic:
            for result in filtered:
                if result.basic_part:
                    result.match_score *= 1.2  # 20% boost for basic parts

        return filtered

    def _sort_results(
        self, results: List[FastSearchResult], sort_by: str
    ) -> List[FastSearchResult]:
        """Sort results by specified criteria."""
        if sort_by == "price":
            return sorted(results, key=lambda x: (x.price, -x.match_score))
        elif sort_by == "stock":
            return sorted(results, key=lambda x: (-x.stock, -x.match_score))
        else:  # relevance
            return sorted(results, key=lambda x: -x.match_score)

    def _parse_cached_results(self, cached_data: List[Dict]) -> List[FastSearchResult]:
        """Parse cached results back into FastSearchResult objects."""
        results = []
        for item in cached_data:
            try:
                results.append(FastSearchResult(**item))
            except Exception as e:
                logger.debug(f"Error parsing cached result: {e}")
        return results

    def _build_query_from_specs(self, component_type: str, specs: Dict) -> str:
        """Build search query from component specifications."""
        query_parts = []

        # Add value if present
        if "value" in specs:
            query_parts.append(str(specs["value"]))

        # Add package if present
        if "package" in specs:
            query_parts.append(specs["package"])

        # Add tolerance for passives
        if component_type in ["resistor", "capacitor"] and "tolerance" in specs:
            query_parts.append(specs["tolerance"])

        # Add voltage rating for capacitors
        if component_type == "capacitor" and "voltage" in specs:
            query_parts.append(f"{specs['voltage']}V")

        return " ".join(query_parts)

    def _get_category_for_type(self, component_type: str) -> Optional[str]:
        """Map component type to JLCPCB category."""
        category_map = {
            "resistor": "Resistors",
            "capacitor": "Capacitors",
            "inductor": "Inductors",
            "diode": "Diodes",
            "transistor": "Transistors",
            "ic": "Integrated Circuits",
            "connector": "Connectors",
            "crystal": "Crystals/Oscillators",
            "led": "Optoelectronics",
        }
        return category_map.get(component_type.lower())

    def _extract_specs_from_description(self, description: str) -> Dict:
        """Extract specifications from component description."""
        # This is a simplified extraction - could be enhanced with regex
        specs = {}
        desc_lower = description.lower()

        # Extract common values
        if "ohm" in desc_lower or "ω" in description:
            specs["type"] = "resistor"
        elif "uf" in desc_lower or "nf" in desc_lower or "pf" in desc_lower:
            specs["type"] = "capacitor"

        # Extract package
        for pkg in ["0603", "0805", "1206", "SOT-23", "SOIC", "LQFP", "QFN"]:
            if pkg.lower() in desc_lower:
                specs["package"] = pkg
                break

        # Base query is first significant word
        words = description.split()
        if words:
            specs["base_query"] = words[0]

        return specs


# Convenience functions for direct import
_default_searcher = None


def get_fast_searcher() -> FastJLCSearch:
    """Get or create the default fast searcher instance."""
    global _default_searcher
    if _default_searcher is None:
        _default_searcher = FastJLCSearch()
    return _default_searcher


def fast_jlc_search(
    query: str, min_stock: int = 0, max_results: int = 10, **kwargs
) -> List[FastSearchResult]:
    """
    Convenience function for fast JLCPCB searches.

    Args:
        query: Search query
        min_stock: Minimum stock required
        max_results: Maximum results to return
        **kwargs: Additional arguments for search()

    Returns:
        List of search results
    """
    searcher = get_fast_searcher()
    return searcher.search(
        query, min_stock=min_stock, max_results=max_results, **kwargs
    )


def find_cheapest_jlc(query: str, min_stock: int = 100) -> Optional[FastSearchResult]:
    """Find the cheapest JLCPCB component matching the query."""
    searcher = get_fast_searcher()
    return searcher.find_cheapest(query, min_stock)


def find_most_available_jlc(query: str) -> Optional[FastSearchResult]:
    """Find the JLCPCB component with highest stock."""
    searcher = get_fast_searcher()
    return searcher.find_most_available(query)
