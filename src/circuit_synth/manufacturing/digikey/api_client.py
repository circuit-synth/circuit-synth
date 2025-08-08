#!/usr/bin/env python3
"""
DigiKey API Client for Circuit-Synth

Provides direct integration with DigiKey's Product Information API v4
for component search, pricing, and availability data.
"""

import json
import logging
import os
import time
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

import requests

logger = logging.getLogger(__name__)


@dataclass
class DigiKeyConfig:
    """Configuration for DigiKey API access."""

    client_id: str
    client_secret: str
    sandbox_mode: bool = False
    cache_dir: Optional[Path] = None
    token_refresh_buffer: int = 300  # Refresh token 5 minutes before expiry

    @classmethod
    def from_environment(cls) -> "DigiKeyConfig":
        """Create configuration from environment variables."""
        from .config_manager import DigiKeyConfigManager

        config_dict = DigiKeyConfigManager.get_config()

        cache_dir = config_dict.get("cache_dir") or os.environ.get(
            "DIGIKEY_STORAGE_PATH"
        )
        return cls(
            client_id=config_dict["client_id"],
            client_secret=config_dict["client_secret"],
            sandbox_mode=config_dict.get("sandbox_mode", False),
            cache_dir=(
                Path(cache_dir)
                if cache_dir
                else Path.home() / ".circuit_synth" / "digikey_cache"
            ),
        )


class DigiKeyAPIClient:
    """
    Direct API client for DigiKey Product Information API v4.

    Implements OAuth2 authentication and provides methods for:
    - Product search by keyword
    - Product details lookup
    - Batch product queries
    - Pricing and availability data
    """

    def __init__(self, config: Optional[DigiKeyConfig] = None):
        """Initialize the DigiKey API client."""
        self.config = config or DigiKeyConfig.from_environment()
        self._validate_config()

        # Set up URLs based on sandbox mode
        if self.config.sandbox_mode:
            self.base_url = "https://sandbox-api.digikey.com"
            self.token_url = "https://sandbox-api.digikey.com/v1/oauth2/token"
        else:
            self.base_url = "https://api.digikey.com"
            self.token_url = "https://api.digikey.com/v1/oauth2/token"

        # Token management
        self.access_token = None
        self.token_expires_at = 0

        # Ensure cache directory exists
        if self.config.cache_dir:
            self.config.cache_dir.mkdir(parents=True, exist_ok=True)
            self.token_cache_file = self.config.cache_dir / "token_cache.json"
        else:
            self.token_cache_file = None

        # Load cached token if available
        self._load_cached_token()

    def _validate_config(self):
        """Validate the configuration has required fields."""
        if not self.config.client_id or not self.config.client_secret:
            raise ValueError(
                "DigiKey API credentials not configured. Please set "
                "DIGIKEY_CLIENT_ID and DIGIKEY_CLIENT_SECRET environment variables."
            )

    def _load_cached_token(self):
        """Load cached access token if valid."""
        if not self.token_cache_file or not self.token_cache_file.exists():
            return

        try:
            with open(self.token_cache_file, "r") as f:
                cache = json.load(f)
                self.access_token = cache.get("access_token")
                self.token_expires_at = cache.get("expires_at", 0)

                if self.token_expires_at > time.time():
                    logger.debug("Loaded valid cached token")
                else:
                    self.access_token = None
                    self.token_expires_at = 0
        except Exception as e:
            logger.warning(f"Failed to load cached token: {e}")

    def _save_cached_token(self):
        """Save access token to cache."""
        if not self.token_cache_file:
            return

        try:
            cache = {
                "access_token": self.access_token,
                "expires_at": self.token_expires_at,
            }
            with open(self.token_cache_file, "w") as f:
                json.dump(cache, f)
            logger.debug("Saved token to cache")
        except Exception as e:
            logger.warning(f"Failed to save token cache: {e}")

    def _get_access_token(self) -> str:
        """Get or refresh OAuth2 access token."""
        # Check if we have a valid token
        if self.access_token and self.token_expires_at > (
            time.time() + self.config.token_refresh_buffer
        ):
            return self.access_token

        logger.info("Obtaining new DigiKey access token...")

        # Request new token using client credentials flow
        data = {
            "client_id": self.config.client_id,
            "client_secret": self.config.client_secret,
            "grant_type": "client_credentials",
        }

        try:
            response = requests.post(self.token_url, data=data)
            response.raise_for_status()

            token_data = response.json()
            self.access_token = token_data["access_token"]
            # Token expires in 30 minutes (1800 seconds)
            self.token_expires_at = time.time() + token_data.get("expires_in", 1800)

            self._save_cached_token()
            logger.info("Successfully obtained access token")

            return self.access_token

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to obtain access token: {e}")
            raise

    def _make_api_request(
        self,
        method: str,
        endpoint: str,
        params: Optional[Dict[str, Any]] = None,
        json_data: Optional[Dict[str, Any]] = None,
    ) -> Dict[str, Any]:
        """Make an authenticated API request."""
        token = self._get_access_token()

        headers = {
            "Authorization": f"Bearer {token}",
            "X-DIGIKEY-Client-Id": self.config.client_id,
            "Content-Type": "application/json",
        }

        url = f"{self.base_url}/{endpoint}"

        try:
            response = requests.request(
                method=method,
                url=url,
                headers=headers,
                params=params,
                json=json_data,
            )
            response.raise_for_status()
            return response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"API request failed: {e}")
            if hasattr(e, "response") and e.response is not None:
                logger.error(f"Response: {e.response.text}")
            raise

    def search_products(
        self,
        keyword: str,
        record_count: int = 25,
        record_start_position: int = 0,
        filters: Optional[Dict[str, Any]] = None,
        sort: Optional[Dict[str, str]] = None,
    ) -> Dict[str, Any]:
        """
        Search for products by keyword.

        Args:
            keyword: Search term
            record_count: Number of results to return (max 50)
            record_start_position: Starting position for pagination
            filters: Optional filters (manufacturer, category, etc.)
            sort: Optional sort parameters

        Returns:
            Search results with product information
        """
        logger.info(f"Searching DigiKey for: {keyword}")

        # Build search request
        search_request = {
            "Keywords": keyword,
            "RecordCount": min(record_count, 50),
            "RecordStartPosition": record_start_position,
        }

        if filters:
            search_request["Filters"] = filters

        if sort:
            search_request["Sort"] = sort

        # Use Product Search API v4
        endpoint = "products/v4/search/keyword"

        return self._make_api_request("POST", endpoint, json_data=search_request)

    def get_product_details(self, digikey_part_number: str) -> Dict[str, Any]:
        """
        Get detailed information for a specific product.

        Args:
            digikey_part_number: DigiKey part number

        Returns:
            Detailed product information
        """
        logger.info(f"Getting details for DigiKey part: {digikey_part_number}")

        endpoint = f"products/v4/search/partdetails/{digikey_part_number}"

        return self._make_api_request("GET", endpoint)

    def batch_product_details(self, part_numbers: List[str]) -> List[Dict[str, Any]]:
        """
        Get details for multiple products in a single request.

        Args:
            part_numbers: List of DigiKey or manufacturer part numbers

        Returns:
            List of product details
        """
        logger.info(f"Getting batch details for {len(part_numbers)} parts")

        # Batch endpoint requires special permission
        # For now, we'll make individual requests
        results = []
        for part_number in part_numbers:
            try:
                result = self.get_product_details(part_number)
                results.append(result)
            except Exception as e:
                logger.warning(f"Failed to get details for {part_number}: {e}")
                results.append(None)

        return results

    def get_product_pricing(self, product_data: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Extract pricing information from product data.

        Args:
            product_data: Product data from API

        Returns:
            List of price breaks with quantities and unit prices
        """
        pricing = []

        if "PriceBreaks" in product_data:
            for price_break in product_data["PriceBreaks"]:
                pricing.append(
                    {
                        "quantity": price_break.get("BreakQuantity", 0),
                        "unit_price": price_break.get("UnitPrice", 0),
                        "total_price": price_break.get("TotalPrice", 0),
                    }
                )

        return pricing

    def get_product_availability(self, product_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Extract availability information from product data.

        Args:
            product_data: Product data from API

        Returns:
            Availability information
        """
        return {
            "in_stock": product_data.get("QuantityOnHand", 0),
            "available": product_data.get("QuantityAvailable", 0),
            "factory_stock": product_data.get("FactoryStock", 0),
            "lead_time": product_data.get("LeadTime", "Unknown"),
            "min_order_qty": product_data.get("MinimumOrderQuantity", 1),
            "packaging": product_data.get("Packaging", {}).get("Value", "Unknown"),
        }


def quick_search(keyword: str, max_results: int = 10) -> List[Dict[str, Any]]:
    """
    Quick search helper function for finding components.

    Args:
        keyword: Search term
        max_results: Maximum number of results

    Returns:
        Simplified list of component data
    """
    client = DigiKeyAPIClient()
    results = client.search_products(keyword, record_count=max_results)

    components = []
    for product in results.get("Products", []):
        components.append(
            {
                "digikey_part": product.get("DigiKeyPartNumber"),
                "manufacturer_part": product.get("ManufacturerPartNumber"),
                "manufacturer": product.get("Manufacturer", {}).get("Value"),
                "description": product.get("Description", {}).get("Value"),
                "in_stock": product.get("QuantityOnHand", 0),
                "unit_price": product.get("UnitPrice", 0),
                "datasheet": product.get("DatasheetUrl"),
            }
        )

    return components


if __name__ == "__main__":
    # Example usage
    logging.basicConfig(level=logging.INFO)

    # Quick search example
    results = quick_search("STM32F407", max_results=5)
    for component in results:
        print(f"\n{component['manufacturer_part']} - {component['description']}")
        print(f"  Stock: {component['in_stock']} | Price: ${component['unit_price']}")
        print(f"  DigiKey PN: {component['digikey_part']}")
