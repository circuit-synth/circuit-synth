#!/usr/bin/env python3
"""
JLC Parts Integration for Circuit-Synth

Provides component recommendations based on JLC PCB availability and pricing
using direct API integration for real-time manufacturability analysis.

This module enables circuit-synth users to make informed component choices
based on current stock levels and pricing from JLCPCB's assembly service.
"""

import csv
import logging
import os
import time
from typing import Any, Callable, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


class JlcPartsInterface:
    """
    Interface to JLC PCB parts database for component recommendations.

    Adapted from yaqwsx/jlcparts for circuit-synth integration.
    """

    def __init__(self, key: Optional[str] = None, secret: Optional[str] = None) -> None:
        """
        Initialize JLC Parts interface.

        Args:
            key: JLCPCB API key (optional, uses JLCPCB_KEY env var if not provided)
            secret: JLCPCB API secret (optional, uses JLCPCB_SECRET env var if not provided)
        """
        self.key = key or os.environ.get("JLCPCB_KEY")
        self.secret = secret or os.environ.get("JLCPCB_SECRET")
        self.token = None
        self.lastPage = None

        if not self.key or not self.secret:
            logger.warning(
                "JLCPCB API credentials not found. Component recommendations will be limited."
            )

    def _obtain_token(self) -> None:
        """Obtain authentication token from JLCPCB API."""
        if not self.key or not self.secret:
            raise RuntimeError("JLCPCB API credentials not configured")

        body = {"appKey": self.key, "appSecret": self.secret}
        headers = {
            "Content-Type": "application/json",
        }

        try:
            resp = requests.post(
                "https://jlcpcb.com/external/genToken",
                json=body,
                headers=headers,
                timeout=30,
            )
            if resp.status_code != 200:
                raise RuntimeError(f"Cannot obtain token {resp.json()}")
            data = resp.json()
            if data["code"] != 200:
                raise RuntimeError(f"Cannot obtain token {data}")
            self.token = data["data"]
            logger.info("Successfully obtained JLCPCB API token")
        except requests.RequestException as e:
            raise RuntimeError(f"Network error obtaining token: {e}")

    def get_component_page(self) -> Optional[List[Dict[str, Any]]]:
        """
        Fetch a page of components from JLCPCB API.

        Returns:
            List of component dictionaries or None if no more pages
        """
        if self.token is None:
            self._obtain_token()

        headers = {
            "externalApiToken": self.token,
        }
        if self.lastPage is None:
            body = {}
        else:
            body = {"lastKey": self.lastPage}

        try:
            resp = requests.post(
                "https://jlcpcb.com/external/component/getComponentInfos",
                data=body,
                headers=headers,
                timeout=30,
            )
            data = resp.json()["data"]
            self.lastPage = data["lastKey"]
            return data["componentInfos"]
        except Exception as e:
            logger.error(f"Error fetching component page: {e}")
            raise RuntimeError(
                f"Cannot fetch page: {resp.text if 'resp' in locals() else str(e)}"
            )

    def search_components(
        self, search_terms: List[str], max_results: int = 50
    ) -> List[Dict[str, Any]]:
        """
        Search for components matching given terms.

        Args:
            search_terms: List of search terms (e.g., ["STM32G0", "LQFP"])
            max_results: Maximum number of results to return

        Returns:
            List of matching components with stock and pricing info
        """
        if not self.key or not self.secret:
            logger.warning("API credentials not available, returning empty results")
            return []

        matching_components = []
        processed_count = 0

        try:
            while len(matching_components) < max_results:
                page = self.get_component_page()
                if page is None:
                    break

                for component in page:
                    processed_count += 1

                    # Check if component matches search terms
                    component_text = " ".join(
                        [
                            str(component.get("mfrPart", "")),
                            str(component.get("description", "")),
                            str(component.get("manufacturer", "")),
                            str(component.get("package", "")),
                        ]
                    ).upper()

                    if all(term.upper() in component_text for term in search_terms):
                        matching_components.append(
                            {
                                "lcsc_part": component.get("lcscPart"),
                                "manufacturer_part": component.get("mfrPart"),
                                "manufacturer": component.get("manufacturer"),
                                "description": component.get("description"),
                                "package": component.get("package"),
                                "stock": component.get("stock", 0),
                                "price": component.get("price", "N/A"),
                                "datasheet": component.get("datasheet"),
                                "library_type": component.get("libraryType"),
                            }
                        )

                        if len(matching_components) >= max_results:
                            break

                # Avoid overwhelming the API
                time.sleep(0.1)

        except Exception as e:
            logger.error(f"Error during component search: {e}")

        logger.info(
            f"Found {len(matching_components)} matching components from {processed_count} processed"
        )
        return matching_components

    def get_most_available_part(
        self, search_terms: List[str]
    ) -> Optional[Dict[str, Any]]:
        """
        Find the component with highest stock availability matching search terms.

        Args:
            search_terms: List of search terms

        Returns:
            Component with highest stock or None if no matches
        """
        components = self.search_components(search_terms, max_results=100)
        if not components:
            return None

        # Sort by stock quantity (descending)
        components.sort(key=lambda x: int(x.get("stock", 0)), reverse=True)
        return components[0] if components else None


def recommend_jlc_component(
    component_type: str, package_preference: Optional[str] = None
) -> Optional[Dict[str, Any]]:
    """
    Recommend a JLC-compatible component for circuit-synth designs.

    Args:
        component_type: Type of component (e.g., "STM32G0", "LM358", "USB-C")
        package_preference: Preferred package type (e.g., "LQFP", "QFN", "0603")

    Returns:
        Recommended component dict with stock/pricing info or None
    """
    interface = JlcPartsInterface()

    search_terms = [component_type]
    if package_preference:
        search_terms.append(package_preference)

    try:
        component = interface.get_most_available_part(search_terms)
        if component:
            logger.info(
                f"Recommended {component['manufacturer_part']} with {component['stock']} units in stock"
            )
        return component
    except Exception as e:
        logger.error(f"Error getting component recommendation: {e}")
        return None


def get_component_alternatives(lcsc_part: str, limit: int = 5) -> List[Dict[str, Any]]:
    """
    Get alternative components similar to the given LCSC part.

    Args:
        lcsc_part: LCSC part number to find alternatives for
        limit: Maximum number of alternatives to return

    Returns:
        List of alternative components
    """
    # This would require additional API endpoints or local database
    # For now, return empty list as placeholder
    logger.info(f"Alternative lookup for {lcsc_part} not yet implemented")
    return []


# Circuit-synth integration helpers
def enhance_component_with_jlc_data(
    component_symbol: str, component_value: str = ""
) -> Dict[str, Any]:
    """
    Enhance a circuit-synth component with JLC availability data.

    Args:
        component_symbol: KiCad symbol name (e.g., "MCU_ST_STM32G0:STM32G030C8T6")
        component_value: Component value if applicable

    Returns:
        Enhanced component data with JLC recommendations
    """
    # Extract component type from symbol
    if ":" in component_symbol:
        lib_name, symbol_name = component_symbol.split(":", 1)
        search_term = symbol_name
    else:
        search_term = component_symbol

    # Add value to search if provided
    if component_value:
        search_term = f"{search_term} {component_value}"

    recommendation = recommend_jlc_component(search_term)

    return {
        "original_symbol": component_symbol,
        "original_value": component_value,
        "jlc_recommendation": recommendation,
        "manufacturability_score": _calculate_manufacturability_score(recommendation),
    }


def _calculate_manufacturability_score(
    component_data: Optional[Dict[str, Any]],
) -> float:
    """
    Calculate a manufacturability score (0-1) based on JLC availability.

    Args:
        component_data: JLC component data or None

    Returns:
        Score from 0.0 (not manufacturable) to 1.0 (highly manufacturable)
    """
    if not component_data:
        return 0.0

    stock = int(component_data.get("stock", 0))
    library_type = component_data.get("library_type", "")

    # Base score from stock availability
    if stock >= 10000:
        stock_score = 1.0
    elif stock >= 1000:
        stock_score = 0.8
    elif stock >= 100:
        stock_score = 0.6
    elif stock >= 10:
        stock_score = 0.4
    elif stock > 0:
        stock_score = 0.2
    else:
        stock_score = 0.0

    # Bonus for basic/preferred parts
    library_bonus = 0.2 if "basic" in library_type.lower() else 0.0

    return min(1.0, stock_score + library_bonus)


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Test component search
    print("Testing JLC parts integration...")
    result = recommend_jlc_component("STM32G0", "LQFP")
    if result:
        print(
            f"Found: {result['manufacturer_part']} - {result['stock']} units in stock"
        )
    else:
        print("No components found or API credentials not configured")
