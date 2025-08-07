#!/usr/bin/env python3
"""
DigiKey Component Search for Circuit-Synth

High-level component search and recommendation functionality that integrates
with KiCad symbols and provides manufacturable component suggestions.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .api_client import DigiKeyAPIClient
from .cache import get_digikey_cache

logger = logging.getLogger(__name__)


@dataclass
class DigiKeyComponent:
    """Represents a DigiKey component with all relevant information."""

    # DigiKey Information
    digikey_part_number: str
    manufacturer_part_number: str
    manufacturer: str
    description: str

    # Availability & Pricing
    quantity_available: int
    quantity_on_hand: int
    unit_price: float
    min_order_qty: int
    packaging: str

    # Technical Information
    category: str
    family: str
    datasheet_url: Optional[str]
    parameters: Dict[str, str]

    # Pricing Breaks
    price_breaks: List[Dict[str, Any]]

    # Circuit-Synth Integration
    kicad_symbol: Optional[str] = None
    kicad_footprint: Optional[str] = None
    circuit_synth_code: Optional[str] = None

    @property
    def is_in_stock(self) -> bool:
        """Check if component is in stock."""
        return self.quantity_available > 0

    @property
    def manufacturability_score(self) -> float:
        """
        Calculate manufacturability score based on availability and pricing.

        Returns:
            Score from 0 to 100
        """
        score = 0.0

        # Stock availability (40 points)
        if self.quantity_available > 10000:
            score += 40
        elif self.quantity_available > 1000:
            score += 30
        elif self.quantity_available > 100:
            score += 20
        elif self.quantity_available > 0:
            score += 10

        # Price consideration (30 points)
        if self.unit_price < 0.10:
            score += 30
        elif self.unit_price < 1.00:
            score += 25
        elif self.unit_price < 5.00:
            score += 20
        elif self.unit_price < 20.00:
            score += 10

        # Minimum order quantity (15 points)
        if self.min_order_qty == 1:
            score += 15
        elif self.min_order_qty <= 10:
            score += 10
        elif self.min_order_qty <= 100:
            score += 5

        # Packaging type (15 points)
        preferred_packaging = ["Cut Tape", "Tape & Reel", "Tray"]
        if any(pkg in self.packaging for pkg in preferred_packaging):
            score += 15

        return min(score, 100)


class DigiKeyComponentSearch:
    """
    High-level component search interface for DigiKey.

    Provides intelligent component recommendations with caching,
    KiCad integration, and manufacturability scoring.
    """

    def __init__(self, use_cache: bool = True):
        """
        Initialize the component search.

        Args:
            use_cache: Whether to use caching for API responses
        """
        self.client = DigiKeyAPIClient()
        self.cache = get_digikey_cache() if use_cache else None
        self.use_cache = use_cache

    def search_components(
        self,
        keyword: str,
        filters: Optional[Dict[str, Any]] = None,
        max_results: int = 25,
        in_stock_only: bool = True,
    ) -> List[DigiKeyComponent]:
        """
        Search for components on DigiKey.

        Args:
            keyword: Search term (e.g., "STM32F407", "100nF capacitor")
            filters: Optional filters (manufacturer, category, etc.)
            max_results: Maximum number of results
            in_stock_only: Only return in-stock components

        Returns:
            List of DigiKey components sorted by manufacturability score
        """
        logger.info(f"Searching DigiKey for: {keyword}")

        # Check cache first
        if self.use_cache and self.cache:
            search_params = {
                "keyword": keyword,
                "filters": filters or {},
                "max_results": max_results,
            }

            cached_data = self.cache.get_search_cache(search_params)
            if cached_data:
                logger.info("Using cached search results")
                return self._parse_search_results(
                    cached_data.get("results", {}), in_stock_only
                )

        # Perform API search
        try:
            results = self.client.search_products(
                keyword=keyword,
                record_count=max_results,
                filters=filters,
            )

            # Cache the results
            if self.use_cache and self.cache:
                search_params = {
                    "keyword": keyword,
                    "filters": filters or {},
                    "max_results": max_results,
                }
                self.cache.set_search_cache(search_params, results)

            return self._parse_search_results(results, in_stock_only)

        except Exception as e:
            logger.error(f"DigiKey search failed: {e}")
            return []

    def _parse_search_results(
        self, results: Dict[str, Any], in_stock_only: bool
    ) -> List[DigiKeyComponent]:
        """Parse API search results into component objects."""
        components = []

        for product in results.get("Products", []):
            try:
                component = self._parse_product(product)

                # Filter by stock if requested
                if in_stock_only and not component.is_in_stock:
                    continue

                components.append(component)

            except Exception as e:
                logger.warning(f"Failed to parse product: {e}")
                continue

        # Sort by manufacturability score
        components.sort(key=lambda x: x.manufacturability_score, reverse=True)

        return components

    def _parse_product(self, product_data: Dict[str, Any]) -> DigiKeyComponent:
        """Parse product data into a DigiKeyComponent object."""
        # Extract basic information
        # Note: API v4 uses different field names than v3
        digikey_pn = product_data.get(
            "DigiKeyPartNumber", product_data.get("DigiKeyProductNumber", "")
        )
        manufacturer_pn = product_data.get(
            "ManufacturerPartNumber", product_data.get("ManufacturerProductNumber", "")
        )

        # Handle manufacturer field - can be dict or string
        manufacturer_field = product_data.get("Manufacturer", {})
        if isinstance(manufacturer_field, dict):
            manufacturer = manufacturer_field.get(
                "Value", manufacturer_field.get("Name", "Unknown")
            )
        else:
            manufacturer = str(manufacturer_field) if manufacturer_field else "Unknown"

        # Handle description field - can be dict or string
        description_field = product_data.get("Description", {})
        if isinstance(description_field, dict):
            description = description_field.get(
                "Value", description_field.get("ProductDescription", "")
            )
        else:
            description = str(description_field) if description_field else ""

        # Extract availability
        qty_available = product_data.get("QuantityAvailable", 0)
        qty_on_hand = product_data.get(
            "QuantityOnHand", qty_available
        )  # Use qty_available as fallback
        min_qty = product_data.get(
            "MinimumOrderQuantity", product_data.get("MinimumQuantity", 1)
        )

        # Handle packaging field
        packaging_field = product_data.get("Packaging", {})
        if isinstance(packaging_field, dict):
            packaging = packaging_field.get("Value", "Unknown")
        else:
            packaging = str(packaging_field) if packaging_field else "Unknown"

        # Extract pricing
        unit_price = product_data.get("UnitPrice", 0.0)
        price_breaks = []
        for pb in product_data.get(
            "PriceBreaks", product_data.get("StandardPricing", [])
        ):
            price_breaks.append(
                {
                    "quantity": pb.get("BreakQuantity", pb.get("Quantity", 0)),
                    "unit_price": pb.get("UnitPrice", pb.get("Price", 0)),
                    "total_price": pb.get("TotalPrice", 0),
                }
            )

        # Extract category information
        category_field = product_data.get(
            "Category", product_data.get("ProductCategory", {})
        )
        if isinstance(category_field, dict):
            category = category_field.get(
                "Value", category_field.get("Name", "Unknown")
            )
        else:
            category = str(category_field) if category_field else "Unknown"

        family_field = product_data.get("Family", product_data.get("ProductFamily", {}))
        if isinstance(family_field, dict):
            family = family_field.get("Value", family_field.get("Name", "Unknown"))
        else:
            family = str(family_field) if family_field else "Unknown"

        # Extract parameters (v3 and v4 compatible)
        parameters = {}
        for param in product_data.get(
            "Parameters", product_data.get("ProductParameters", [])
        ):
            param_name = param.get("Parameter", param.get("ParameterName", ""))
            param_value = param.get("Value", param.get("ParameterValue", ""))
            if param_name and param_value:
                parameters[param_name] = param_value

        # Get datasheet URL
        datasheet_url = product_data.get("DatasheetUrl")

        return DigiKeyComponent(
            digikey_part_number=digikey_pn,
            manufacturer_part_number=manufacturer_pn,
            manufacturer=manufacturer,
            description=description,
            quantity_available=qty_available,
            quantity_on_hand=qty_on_hand,
            unit_price=unit_price,
            min_order_qty=min_qty,
            packaging=packaging,
            category=category,
            family=family,
            datasheet_url=datasheet_url,
            parameters=parameters,
            price_breaks=price_breaks,
        )

    def get_component_details(
        self, digikey_part_number: str
    ) -> Optional[DigiKeyComponent]:
        """
        Get detailed information for a specific component.

        Args:
            digikey_part_number: DigiKey part number

        Returns:
            DigiKeyComponent object or None if not found
        """
        logger.info(f"Getting details for: {digikey_part_number}")

        # Check cache first
        if self.use_cache and self.cache:
            cached_data = self.cache.get_product_cache(digikey_part_number)
            if cached_data:
                logger.info("Using cached product details")
                return self._parse_product(cached_data.get("data", {}))

        # Get from API
        try:
            product_data = self.client.get_product_details(digikey_part_number)

            # Cache the result
            if self.use_cache and self.cache:
                self.cache.set_product_cache(digikey_part_number, product_data)

            return self._parse_product(product_data)

        except Exception as e:
            logger.error(f"Failed to get product details: {e}")
            return None

    def find_alternatives(
        self, reference_component: DigiKeyComponent, max_results: int = 10
    ) -> List[DigiKeyComponent]:
        """
        Find alternative components based on a reference.

        Args:
            reference_component: Component to find alternatives for
            max_results: Maximum number of alternatives

        Returns:
            List of alternative components
        """
        # Search using key parameters from the reference component
        search_terms = []

        # Add key parameters to search
        if "Package / Case" in reference_component.parameters:
            search_terms.append(reference_component.parameters["Package / Case"])

        if "Value" in reference_component.parameters:
            search_terms.append(reference_component.parameters["Value"])

        # Use category and family for search
        keyword = f"{reference_component.family} {' '.join(search_terms)}"

        # Search with category filter
        filters = {
            "Category": reference_component.category,
            "Family": reference_component.family,
        }

        alternatives = self.search_components(
            keyword=keyword,
            filters=filters,
            max_results=max_results * 2,  # Get more to filter
            in_stock_only=True,
        )

        # Filter out the reference component itself
        alternatives = [
            alt
            for alt in alternatives
            if alt.digikey_part_number != reference_component.digikey_part_number
        ]

        return alternatives[:max_results]


def search_digikey_components(
    keyword: str, max_results: int = 10, in_stock_only: bool = True
) -> List[Dict[str, Any]]:
    """
    Quick helper function to search DigiKey components.

    Args:
        keyword: Search term
        max_results: Maximum results to return
        in_stock_only: Only return in-stock components

    Returns:
        Simplified list of component data
    """
    searcher = DigiKeyComponentSearch()
    components = searcher.search_components(
        keyword=keyword,
        max_results=max_results,
        in_stock_only=in_stock_only,
    )

    # Convert to simplified format
    results = []
    for comp in components:
        results.append(
            {
                "digikey_part": comp.digikey_part_number,
                "manufacturer_part": comp.manufacturer_part_number,
                "manufacturer": comp.manufacturer,
                "description": comp.description,
                "stock": comp.quantity_available,
                "price": comp.unit_price,
                "min_qty": comp.min_order_qty,
                "datasheet": comp.datasheet_url,
                "score": comp.manufacturability_score,
            }
        )

    return results


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Search for STM32 microcontrollers
    results = search_digikey_components("STM32F407", max_results=5)

    print("\nTop STM32F407 Components on DigiKey:")
    print("-" * 80)

    for comp in results:
        print(f"\n{comp['manufacturer_part']} by {comp['manufacturer']}")
        print(f"  Description: {comp['description'][:60]}...")
        print(f"  Stock: {comp['stock']:,} units | Price: ${comp['price']:.2f}")
        print(f"  Min Order: {comp['min_qty']} | Score: {comp['score']:.1f}/100")
        print(f"  DigiKey PN: {comp['digikey_part']}")
