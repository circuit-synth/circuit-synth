"""
KiCad HTTP Library source implementation
"""

import json
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

import aiohttp

from ..models import ComponentSearchResult, LibrarySource, SearchQuery
from .base import BaseLibrarySource


class HTTPLibrarySource(BaseLibrarySource):
    """Source for KiCad HTTP libraries (.kicad_httplib)"""

    def __init__(self):
        super().__init__()
        self.http_configs = self._load_http_configs()

    def _load_http_configs(self) -> List[Dict[str, Any]]:
        """Load HTTP library configurations from .kicad_httplib files"""

        configs = []

        # Common locations for HTTP library configs
        config_paths = [
            # User libraries
            Path.home() / ".kicad" / "library",
            Path.home() / "Documents" / "KiCad" / "library",
            # Project-specific configs
            Path.cwd() / "library",
            Path.cwd() / ".kicad" / "library",
        ]

        for config_path in config_paths:
            if config_path.exists():
                for httplib_file in config_path.glob("*.kicad_httplib"):
                    try:
                        config = self._parse_httplib_config(httplib_file)
                        if config:
                            configs.append(config)
                    except Exception as e:
                        logger.warning(
                            f"Failed to load HTTP lib config {httplib_file}: {e}"
                        )

        return configs

    def _parse_httplib_config(self, config_file: Path) -> Optional[Dict[str, Any]]:
        """Parse .kicad_httplib configuration file"""

        try:
            with open(config_file, "r") as f:
                content = f.read()

            # Simple parser for KiCad HTTP lib format
            # Example format:
            # {
            #   "meta": {
            #     "version": 1
            #   },
            #   "name": "My Parts Library",
            #   "description": "Company parts database",
            #   "source": {
            #     "type": "REST_API",
            #     "api_version": "v1",
            #     "root_url": "https://api.company.com/parts",
            #     "token": "access_token_here"
            #   }
            # }

            config = json.loads(content)
            return config

        except Exception as e:
            logger.error(f"Error parsing HTTP lib config {config_file}: {e}")
            return None

    async def search(self, query: SearchQuery) -> List[ComponentSearchResult]:
        """Search HTTP library sources"""

        if not self.http_configs:
            return []

        all_results = []

        for config in self.http_configs:
            try:
                results = await self._search_http_source(config, query)
                all_results.extend(results)
            except Exception as e:
                logger.warning(
                    f"Error searching HTTP source {config.get('name', 'unknown')}: {e}"
                )

        return all_results

    async def _search_http_source(
        self, config: Dict[str, Any], query: SearchQuery
    ) -> List[ComponentSearchResult]:
        """Search a single HTTP library source"""

        source_config = config.get("source", {})
        root_url = source_config.get("root_url")
        token = source_config.get("token")
        api_version = source_config.get("api_version", "v1")

        if not root_url:
            return []

        headers = {}
        if token:
            headers["Authorization"] = f"Token {token}"

        async with aiohttp.ClientSession() as session:
            # Query parts endpoint
            parts_url = f"{root_url}/{api_version}/parts"
            params = {"search": query.query, "limit": query.max_results}

            if query.component_type:
                params["category"] = query.component_type
            if query.manufacturer:
                params["manufacturer"] = query.manufacturer
            if query.part_number:
                params["part_number"] = query.part_number

            async with session.get(
                parts_url, headers=headers, params=params
            ) as response:
                if response.status == 200:
                    data = await response.json()
                    return self._parse_http_response(
                        data, config.get("name", "HTTP Library")
                    )
                else:
                    logger.warning(f"HTTP library search failed: {response.status}")
                    return []

    def _parse_http_response(
        self, data: Dict[str, Any], source_name: str
    ) -> List[ComponentSearchResult]:
        """Parse HTTP library API response"""

        results = []

        parts = data.get("parts", [])
        for part in parts:
            # Extract component information
            result = ComponentSearchResult(
                symbol_library=part.get("symbol_library"),
                symbol_name=part.get("symbol_name"),
                footprint_library=part.get("footprint_library"),
                footprint_name=part.get("footprint_name"),
                model_3d=part.get("model_3d"),
                description=part.get("description"),
                manufacturer=part.get("manufacturer"),
                part_number=part.get("part_number"),
                datasheet_url=part.get("datasheet_url"),
                source=LibrarySource.HTTP_LIBRARY,
                availability=part.get("available", True),
                confidence_score=float(part.get("confidence", 0.7)),
                specifications=part.get("specifications", {}),
            )

            results.append(result)

        return results

    def is_available(self) -> bool:
        """Check if HTTP libraries are configured and available"""
        self.last_check = time.time()

        if not self.http_configs:
            return False

        # Quick availability check - just verify configs exist
        # Full network check would be done in health_check()
        return True

    async def health_check(self) -> bool:
        """Perform network health check on HTTP libraries"""

        if not self.http_configs:
            return False

        # Test connectivity to each configured HTTP library
        for config in self.http_configs:
            source_config = config.get("source", {})
            root_url = source_config.get("root_url")

            if not root_url:
                continue

            try:
                async with aiohttp.ClientSession() as session:
                    # Test basic connectivity
                    async with session.get(f"{root_url}/health", timeout=5) as response:
                        if response.status == 200:
                            return True
            except Exception:
                continue

        return False
