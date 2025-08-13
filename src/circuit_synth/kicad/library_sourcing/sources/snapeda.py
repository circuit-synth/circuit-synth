"""
SnapEDA API source implementation
"""

import time
from typing import List, Optional
from urllib.parse import quote

import aiohttp

from ..models import ComponentSearchResult, LibrarySource, SearchQuery
from .base import BaseLibrarySource


class SnapEDASource(BaseLibrarySource):
    """Source for SnapEDA component library API"""

    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key
        self.base_url = "https://www.snapeda.com/api/v1"

    async def search(self, query: SearchQuery) -> List[ComponentSearchResult]:
        """Search SnapEDA for components"""

        if not self.is_available():
            return []

        results = []

        try:
            async with aiohttp.ClientSession() as session:
                # Search parts endpoint
                search_url = f"{self.base_url}/parts/search"
                params = {
                    "q": query.query,
                    "limit": query.max_results,
                    "format": "kicad",  # Request KiCad-compatible results
                }

                if query.manufacturer:
                    params["manufacturer"] = query.manufacturer
                if query.part_number:
                    params["part_number"] = query.part_number
                if query.package:
                    params["package"] = query.package

                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"

                async with session.get(
                    search_url, params=params, headers=headers
                ) as response:
                    if response.status == 200:
                        data = await response.json()
                        results = self._parse_snapeda_response(data)
                    elif response.status == 429:
                        logger.warning("SnapEDA rate limit exceeded")
                    else:
                        logger.warning(f"SnapEDA search failed: {response.status}")

        except Exception as e:
            logger.error(f"SnapEDA search error: {e}")

        return results

    def _parse_snapeda_response(self, data: dict) -> List[ComponentSearchResult]:
        """Parse SnapEDA API response"""

        results = []

        parts = data.get("parts", [])
        for part in parts:
            # Extract KiCad library information
            kicad_data = part.get("kicad", {})

            result = ComponentSearchResult(
                symbol_library=kicad_data.get("symbol_library"),
                symbol_name=kicad_data.get("symbol_name"),
                footprint_library=kicad_data.get("footprint_library"),
                footprint_name=kicad_data.get("footprint_name"),
                model_3d=kicad_data.get("model_3d"),
                description=part.get("description"),
                manufacturer=part.get("manufacturer"),
                part_number=part.get("mpn"),
                datasheet_url=part.get("datasheet_url"),
                source=LibrarySource.SNAPEDA,
                availability=part.get("available", True),
                confidence_score=float(part.get("match_score", 0.7)),
                supplier_links=part.get("supplier_links", []),
                specifications=part.get("specifications", {}),
            )

            results.append(result)

        return results

    def is_available(self) -> bool:
        """Check if SnapEDA API is available"""
        self.last_check = time.time()

        # SnapEDA has free tier, so assume available
        # Full connectivity check would be in health_check()
        return True

    async def health_check(self) -> bool:
        """Check SnapEDA API connectivity"""

        try:
            async with aiohttp.ClientSession() as session:
                # Test API connectivity
                test_url = f"{self.base_url}/health"
                headers = {}
                if self.api_key:
                    headers["Authorization"] = f"Bearer {self.api_key}"

                async with session.get(
                    test_url, headers=headers, timeout=5
                ) as response:
                    return response.status in [
                        200,
                        404,
                    ]  # 404 acceptable if no health endpoint

        except Exception as e:
            logger.debug(f"SnapEDA health check failed: {e}")
            return False
