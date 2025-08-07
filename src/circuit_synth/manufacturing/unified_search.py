#!/usr/bin/env python3
"""
Unified Component Search across Multiple Suppliers

Provides a single interface for searching components across all supported suppliers.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Union

logger = logging.getLogger(__name__)


@dataclass
class UnifiedComponent:
    """Unified component representation across all suppliers."""

    supplier: str
    supplier_part_number: str
    manufacturer_part_number: str
    manufacturer: str
    description: str
    stock: int
    unit_price: float
    min_qty: int
    datasheet_url: Optional[str] = None

    # Price breaks
    price_breaks: Optional[List[Dict[str, Any]]] = None

    # Additional metadata
    is_basic_part: bool = False  # JLCPCB specific
    packaging: Optional[str] = None
    lifecycle_status: Optional[str] = None

    @property
    def availability_score(self) -> float:
        """Score based on stock availability."""
        if self.stock > 10000:
            return 100
        elif self.stock > 5000:
            return 80
        elif self.stock > 1000:
            return 60
        elif self.stock > 100:
            return 40
        elif self.stock > 0:
            return 20
        return 0

    @property
    def value_score(self) -> float:
        """Combined score of price and availability."""
        price_score = 100
        if self.unit_price > 0:
            # Inverse price scoring (lower is better)
            if self.unit_price < 0.10:
                price_score = 100
            elif self.unit_price < 0.50:
                price_score = 80
            elif self.unit_price < 1.00:
                price_score = 60
            elif self.unit_price < 5.00:
                price_score = 40
            else:
                price_score = 20

        # Weight: 60% availability, 40% price
        return (self.availability_score * 0.6) + (price_score * 0.4)


class UnifiedComponentSearch:
    """
    Unified search interface for all component suppliers.
    """

    SUPPORTED_SUPPLIERS = ["jlcpcb", "digikey"]

    def __init__(self):
        """Initialize the unified search system."""
        self.results_cache = {}

    def search(
        self,
        query: str,
        sources: Union[str, List[str]] = "all",
        min_stock: Optional[int] = None,
        max_price: Optional[float] = None,
        in_stock_only: bool = True,
        compare: bool = False,
    ) -> Dict[str, List[UnifiedComponent]]:
        """
        Search for components across specified suppliers.

        Args:
            query: Component search query
            sources: "all", single supplier name, or list of suppliers
            min_stock: Minimum stock quantity filter
            max_price: Maximum unit price filter
            in_stock_only: Only return in-stock items
            compare: Return comparison-friendly format

        Returns:
            Dictionary with supplier names as keys and component lists as values
        """
        # Normalize sources
        if sources == "all":
            search_sources = self.SUPPORTED_SUPPLIERS
        elif isinstance(sources, str):
            search_sources = [sources]
        else:
            search_sources = sources

        # Validate sources
        for source in search_sources:
            if source not in self.SUPPORTED_SUPPLIERS:
                logger.warning(f"Unsupported supplier: {source}")

        # Search each supplier
        results = {}
        for supplier in search_sources:
            if supplier in self.SUPPORTED_SUPPLIERS:
                supplier_results = self._search_supplier(supplier, query, in_stock_only)

                # Apply filters
                if min_stock or max_price:
                    supplier_results = self._apply_filters(
                        supplier_results, min_stock, max_price
                    )

                results[supplier] = supplier_results

        # Sort results by value score
        for supplier in results:
            results[supplier].sort(key=lambda x: x.value_score, reverse=True)

        return results

    def _search_supplier(
        self, supplier: str, query: str, in_stock_only: bool
    ) -> List[UnifiedComponent]:
        """Search a specific supplier."""
        components = []

        if supplier == "jlcpcb":
            components = self._search_jlcpcb(query, in_stock_only)
        elif supplier == "digikey":
            components = self._search_digikey(query, in_stock_only)

        return components

    def _search_jlcpcb(self, query: str, in_stock_only: bool) -> List[UnifiedComponent]:
        """Search JLCPCB for components."""
        try:
            from circuit_synth.manufacturing.jlcpcb import search_jlc_components_web

            logger.info(f"Searching JLCPCB for: {query}")
            raw_results = search_jlc_components_web(query, max_results=20)

            components = []
            for item in raw_results:
                if in_stock_only and item.get("stock", 0) <= 0:
                    continue

                comp = UnifiedComponent(
                    supplier="JLCPCB",
                    supplier_part_number=item.get("lcsc_part", ""),
                    manufacturer_part_number=item.get("mfr_part", ""),
                    manufacturer=item.get("manufacturer", "Unknown"),
                    description=item.get("description", ""),
                    stock=item.get("stock", 0),
                    unit_price=float(item.get("price", 0)),
                    min_qty=item.get("min_qty", 1),
                    datasheet_url=item.get("datasheet", None),
                    is_basic_part=item.get("basic_part", False),
                    packaging=item.get("package", None),
                )
                components.append(comp)

            return components

        except Exception as e:
            logger.error(f"JLCPCB search failed: {e}")
            return []

    def _search_digikey(
        self, query: str, in_stock_only: bool
    ) -> List[UnifiedComponent]:
        """Search DigiKey for components."""
        try:
            from circuit_synth.manufacturing.digikey import search_digikey_components

            logger.info(f"Searching DigiKey for: {query}")
            raw_results = search_digikey_components(
                keyword=query, max_results=20, in_stock_only=in_stock_only
            )

            components = []
            for item in raw_results:
                comp = UnifiedComponent(
                    supplier="DigiKey",
                    supplier_part_number=item.get("digikey_part", ""),
                    manufacturer_part_number=item.get("manufacturer_part", ""),
                    manufacturer=item.get("manufacturer", "Unknown"),
                    description=item.get("description", ""),
                    stock=item.get("stock", 0),
                    unit_price=float(item.get("price", 0)),
                    min_qty=item.get("min_qty", 1),
                    datasheet_url=item.get("datasheet", None),
                    packaging=item.get("packaging", None),
                )

                # Add price breaks if available
                if "price_breaks" in item:
                    comp.price_breaks = item["price_breaks"]

                components.append(comp)

            return components

        except Exception as e:
            logger.error(f"DigiKey search failed: {e}")
            return []

    def _apply_filters(
        self,
        components: List[UnifiedComponent],
        min_stock: Optional[int],
        max_price: Optional[float],
    ) -> List[UnifiedComponent]:
        """Apply stock and price filters to components."""
        filtered = components

        if min_stock:
            filtered = [c for c in filtered if c.stock >= min_stock]

        if max_price:
            filtered = [c for c in filtered if c.unit_price <= max_price]

        return filtered

    def compare_components(
        self, results: Dict[str, List[UnifiedComponent]], max_per_supplier: int = 3
    ) -> str:
        """
        Generate a comparison table of components across suppliers.

        Args:
            results: Search results from multiple suppliers
            max_per_supplier: Maximum components to show per supplier

        Returns:
            Formatted comparison table string
        """
        output = []
        output.append("\n📊 Component Comparison\n")
        output.append("=" * 80)

        # Create comparison table
        output.append(
            "\n| Supplier | Part Number | Stock | 1pc | 100pc | Score | Notes |"
        )
        output.append(
            "|----------|-------------|-------|-----|-------|-------|-------|"
        )

        for supplier, components in results.items():
            for comp in components[:max_per_supplier]:
                # Get 100pc price if available
                price_100 = comp.unit_price
                if comp.price_breaks:
                    for pb in comp.price_breaks:
                        if pb.get("quantity", 0) <= 100:
                            price_100 = pb.get("unit_price", comp.unit_price)

                notes = []
                if comp.is_basic_part:
                    notes.append("Basic")
                if comp.packaging:
                    notes.append(comp.packaging[:10])

                output.append(
                    f"| {supplier:8} | {comp.supplier_part_number[:11]:11} | "
                    f"{comp.stock:5} | ${comp.unit_price:4.2f} | ${price_100:5.3f} | "
                    f"{comp.value_score:5.1f} | {', '.join(notes)[:7]:7} |"
                )

        # Add recommendations
        output.append("\n" + "=" * 80)
        output.append("\n💡 Recommendations:")

        # Find best for prototyping
        best_proto = None
        for supplier, components in results.items():
            for comp in components:
                if comp.min_qty == 1 and comp.stock > 0:
                    if not best_proto or comp.unit_price < best_proto.unit_price:
                        best_proto = comp

        if best_proto:
            output.append(
                f"  Prototyping: {best_proto.supplier} {best_proto.supplier_part_number} "
                f"(${best_proto.unit_price:.3f} @ 1pc)"
            )

        # Find best for production
        best_prod = None
        for supplier, components in results.items():
            for comp in components:
                if comp.stock > 1000:
                    if not best_prod or comp.value_score > best_prod.value_score:
                        best_prod = comp

        if best_prod:
            output.append(
                f"  Production: {best_prod.supplier} {best_prod.supplier_part_number} "
                f"({best_prod.stock:,} stock, score: {best_prod.value_score:.1f})"
            )

        return "\n".join(output)


def find_parts(
    query: str,
    sources: Union[str, List[str]] = "all",
    min_stock: Optional[int] = None,
    max_price: Optional[float] = None,
    compare: bool = False,
) -> Union[Dict[str, List[Dict]], str]:
    """
    Quick function to search for parts across suppliers.

    Args:
        query: Component search query
        sources: Supplier(s) to search
        min_stock: Minimum stock filter
        max_price: Maximum price filter
        compare: Return comparison format

    Returns:
        Search results or comparison table
    """
    searcher = UnifiedComponentSearch()
    results = searcher.search(
        query=query,
        sources=sources,
        min_stock=min_stock,
        max_price=max_price,
        in_stock_only=True,
        compare=compare,
    )

    if compare:
        return searcher.compare_components(results)

    # Convert to simple dict format
    simple_results = {}
    for supplier, components in results.items():
        simple_results[supplier] = []
        for comp in components:
            simple_results[supplier].append(
                {
                    "part_number": comp.supplier_part_number,
                    "manufacturer_part": comp.manufacturer_part_number,
                    "manufacturer": comp.manufacturer,
                    "description": comp.description,
                    "stock": comp.stock,
                    "price": comp.unit_price,
                    "min_qty": comp.min_qty,
                    "score": comp.value_score,
                }
            )

    return simple_results


if __name__ == "__main__":
    # Test the unified search
    import json

    logging.basicConfig(level=logging.INFO)

    print("Testing Unified Component Search\n")
    print("=" * 80)

    # Test 1: JLCPCB only
    print("\n1. Testing JLCPCB source only:")
    results = find_parts("0.1uF 0603", sources="jlcpcb")
    print(f"Found {len(results.get('jlcpcb', []))} components from JLCPCB")

    # Test 2: DigiKey only
    print("\n2. Testing DigiKey source only:")
    results = find_parts("0.1uF 0603", sources="digikey")
    print(f"Found {len(results.get('digikey', []))} components from DigiKey")

    # Test 3: All sources
    print("\n3. Testing all sources:")
    results = find_parts("0.1uF 0603", sources="all")
    for supplier, components in results.items():
        print(f"  {supplier}: {len(components)} components")

    # Test 4: Comparison mode
    print("\n4. Testing comparison mode:")
    comparison = find_parts("0.1uF 0603", sources="all", compare=True)
    print(comparison)
