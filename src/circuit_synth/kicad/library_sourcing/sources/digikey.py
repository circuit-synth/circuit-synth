"""
DigiKey API source implementation
"""

import time
from typing import List, Optional

import aiohttp

from ..models import ComponentSearchResult, LibrarySource, SearchQuery
from .base import BaseLibrarySource


class DigiKeySource(BaseLibrarySource):
    """Source for DigiKey component API with KiCad library integration"""

    def __init__(self, api_key: Optional[str] = None, client_id: Optional[str] = None):
        super().__init__()
        self.api_key = api_key
        self.client_id = client_id
        self.base_url = "https://api.digikey.com"
        self.kicad_library_url = "https://kicad.digikey.com/api/v1"

    async def search(self, query: SearchQuery) -> List[ComponentSearchResult]:
        """Search DigiKey for components with KiCad library data"""

        if not self.is_available():
            return []

        results = []

        try:
            # Search DigiKey parts API
            parts = await self._search_digikey_parts(query)

            # For each part, try to get KiCad library information
            for part in parts:
                kicad_info = await self._get_kicad_library_info(
                    part.get("DigiKeyPartNumber")
                )

                result = ComponentSearchResult(
                    symbol_library=kicad_info.get("symbol_library"),
                    symbol_name=kicad_info.get("symbol_name"),
                    footprint_library=kicad_info.get("footprint_library"),
                    footprint_name=kicad_info.get("footprint_name"),
                    model_3d=kicad_info.get("model_3d"),
                    description=part.get("ProductDescription"),
                    manufacturer=part.get("Manufacturer", {}).get("Name"),
                    part_number=part.get("ManufacturerPartNumber"),
                    datasheet_url=part.get("PrimaryDatasheet"),
                    source=LibrarySource.DIGIKEY,
                    availability=part.get("Quantity", 0) > 0,
                    price=self._extract_price(part.get("StandardPricing", [])),
                    stock_level=part.get("Quantity", 0),
                    supplier_links=[
                        f"https://www.digikey.com/product-detail/en/{part.get('DigiKeyPartNumber')}"
                    ],
                    confidence_score=0.8,
                    specifications=self._extract_specifications(part),
                )

                results.append(result)

        except Exception as e:
            logger.error(f"DigiKey search error: {e}")

        return results[: query.max_results]

    async def _search_digikey_parts(self, query: SearchQuery) -> List[dict]:
        """Search DigiKey parts API"""

        if not self.api_key:
            return []

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "X-DIGIKEY-Client-Id": self.client_id or "",
            "Content-Type": "application/json",
        }

        search_payload = {
            "Keywords": query.query,
            "RecordCount": query.max_results,
            "RecordStartPosition": 0,
            "Filters": {},
        }

        # Add filters based on query
        if query.manufacturer:
            search_payload["Filters"]["Manufacturer"] = query.manufacturer
        if query.component_type:
            search_payload["Filters"]["Category"] = query.component_type

        async with aiohttp.ClientSession() as session:
            search_url = f"{self.base_url}/v1/dkproductsearch/keywordsearch"

            async with session.post(
                search_url, headers=headers, json=search_payload
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return data.get("Products", [])
                else:
                    logger.warning(f"DigiKey parts search failed: {response.status}")
                    return []

    async def _get_kicad_library_info(self, digikey_part_number: str) -> dict:
        """Get KiCad library information for DigiKey part"""

        try:
            async with aiohttp.ClientSession() as session:
                # Query DigiKey's KiCad library service
                kicad_url = (
                    f"{self.kicad_library_url}/parts/{quote(digikey_part_number)}/kicad"
                )

                async with session.get(kicad_url, timeout=10) as response:
                    if response.status == 200:
                        return await response.json()
                    else:
                        return {}

        except Exception as e:
            logger.debug(
                f"KiCad library info unavailable for {digikey_part_number}: {e}"
            )
            return {}

    def _extract_price(self, pricing_data: List[dict]) -> Optional[float]:
        """Extract unit price from DigiKey pricing data"""

        if not pricing_data:
            return None

        # Get single unit price
        for price_tier in pricing_data:
            if price_tier.get("BreakQuantity", 0) == 1:
                return float(price_tier.get("UnitPrice", 0))

        # Fallback to first price tier
        if pricing_data:
            return float(pricing_data[0].get("UnitPrice", 0))

        return None

    def _extract_specifications(self, part_data: dict) -> dict:
        """Extract specifications from DigiKey part data"""

        specs = {}

        # Extract parameters
        parameters = part_data.get("Parameters", [])
        for param in parameters:
            param_name = param.get("Parameter")
            param_value = param.get("Value")
            if param_name and param_value:
                specs[param_name] = param_value

        # Add basic info
        if part_data.get("Series"):
            specs["Series"] = part_data["Series"]
        if part_data.get("Category", {}).get("Name"):
            specs["Category"] = part_data["Category"]["Name"]

        return specs

    def is_available(self) -> bool:
        """Check if DigiKey API is configured"""
        self.last_check = time.time()

        # Available if API key is configured
        return bool(self.api_key)

    async def health_check(self) -> bool:
        """Check DigiKey API connectivity"""

        if not self.api_key:
            return False

        try:
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "X-DIGIKEY-Client-Id": self.client_id or "",
            }

            async with aiohttp.ClientSession() as session:
                # Test API connectivity
                test_url = f"{self.base_url}/v1/test"

                async with session.get(
                    test_url, headers=headers, timeout=5
                ) as response:
                    return response.status == 200

        except Exception as e:
            logger.debug(f"DigiKey health check failed: {e}")
            return False
