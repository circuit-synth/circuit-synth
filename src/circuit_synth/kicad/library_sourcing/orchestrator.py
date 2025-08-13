"""
Library sourcing orchestrator - coordinates multiple component sources
"""

import asyncio
import time
from typing import Any, Dict, List, Optional

from loguru import logger

from .cache import LibraryCache
from .models import (
    ComponentSearchResult,
    LibrarySource,
    SearchQuery,
    SourceConfig,
    SourcePriority,
)
from .sources import (
    BaseLibrarySource,
    DigiKeyGitHubSource,
    DigiKeySource,
    HTTPLibrarySource,
    LocalKiCadSource,
    SnapEDASource,
)
from .sources.digikey_github_modern import DigiKeyGitHubModernSource


class LibraryOrchestrator:
    """
    Orchestrates component sourcing across multiple KiCad library sources

    Implements hybrid approach:
    1. Local KiCad libraries (fastest, most reliable)
    2. KiCad HTTP libraries (component metadata)
    3. Third-party APIs (validation, sourcing, alternatives)
    """

    def __init__(
        self, config_path: Optional[str] = None, cache_dir: Optional[str] = None
    ):
        self.sources: Dict[LibrarySource, BaseLibrarySource] = {}
        self.source_configs: Dict[LibrarySource, SourceConfig] = {}
        self.cache = LibraryCache(cache_dir)

        # Initialize default sources
        self._initialize_sources()

        if config_path:
            self.load_config(config_path)

    def _initialize_sources(self):
        """Initialize all available library sources"""

        # Local KiCad installation (highest priority)
        self.sources[LibrarySource.LOCAL_KICAD] = LocalKiCadSource()
        self.source_configs[LibrarySource.LOCAL_KICAD] = SourceConfig(
            source=LibrarySource.LOCAL_KICAD, priority=SourcePriority.LOCAL.value
        )

        # DigiKey GitHub library (second priority) - modern converted format
        self.sources[LibrarySource.DIGIKEY_GITHUB] = DigiKeyGitHubModernSource()
        self.source_configs[LibrarySource.DIGIKEY_GITHUB] = SourceConfig(
            source=LibrarySource.DIGIKEY_GITHUB,
            priority=SourcePriority.DIGIKEY_GITHUB.value,
        )

        # KiCad HTTP libraries
        self.sources[LibrarySource.HTTP_LIBRARY] = HTTPLibrarySource()
        self.source_configs[LibrarySource.HTTP_LIBRARY] = SourceConfig(
            source=LibrarySource.HTTP_LIBRARY, priority=SourcePriority.HTTP.value
        )

        # Third-party APIs
        self.sources[LibrarySource.SNAPEDA] = SnapEDASource()
        self.source_configs[LibrarySource.SNAPEDA] = SourceConfig(
            source=LibrarySource.SNAPEDA, priority=SourcePriority.SNAPEDA.value
        )

        self.sources[LibrarySource.DIGIKEY_API] = DigiKeySource()
        self.source_configs[LibrarySource.DIGIKEY_API] = SourceConfig(
            source=LibrarySource.DIGIKEY_API, priority=SourcePriority.DIGIKEY_API.value
        )

    async def search_component(self, query: SearchQuery) -> List[ComponentSearchResult]:
        """
        Search for components across all configured sources

        Strategy:
        1. Try sources in priority order
        2. Return early if high-confidence results found
        3. Aggregate results from multiple sources
        4. Apply deduplication and ranking
        """

        # Check cache first
        cached_results = self.cache.get(query)
        if cached_results:
            logger.debug(f"Returning cached results for: {query.query}")
            return cached_results

        all_results = []

        # Get enabled sources sorted by priority
        enabled_sources = [
            (self.source_configs[source_type].priority, source_type, source)
            for source_type, source in self.sources.items()
            if self.source_configs[source_type].enabled
            and source_type in query.preferred_sources
        ]
        enabled_sources.sort(key=lambda x: x[0])  # Sort by priority

        # Search sources in parallel for speed
        search_tasks = []
        for priority, source_type, source in enabled_sources:
            task = self._search_source_with_timeout(source, query, source_type)
            search_tasks.append(task)

        # Execute searches
        source_results = await asyncio.gather(*search_tasks, return_exceptions=True)

        # Process results
        for i, result in enumerate(source_results):
            if isinstance(result, Exception):
                source_type = enabled_sources[i][1]
                logger.warning(f"Search failed for {source_type}: {result}")
                continue

            if result:
                all_results.extend(result)

        # Post-process results
        final_results = self._post_process_results(all_results, query)

        # Cache results
        self.cache.set(query, final_results)

        return final_results

    async def _search_source_with_timeout(
        self, source: BaseLibrarySource, query: SearchQuery, source_type: LibrarySource
    ) -> List[ComponentSearchResult]:
        """Search a single source with timeout"""

        config = self.source_configs[source_type]

        try:
            return await asyncio.wait_for(source.search(query), timeout=config.timeout)
        except asyncio.TimeoutError:
            logger.warning(f"Timeout searching {source_type} after {config.timeout}s")
            return []
        except Exception as e:
            logger.error(f"Error searching {source_type}: {e}")
            return []

    def _post_process_results(
        self, results: List[ComponentSearchResult], query: SearchQuery
    ) -> List[ComponentSearchResult]:
        """Post-process search results"""

        # Filter by confidence threshold
        filtered = [r for r in results if r.confidence_score >= query.min_confidence]

        # Filter by availability if required
        if query.require_availability:
            filtered = [r for r in filtered if r.availability]

        # Filter by datasheet requirement
        if query.require_datasheet:
            filtered = [r for r in filtered if r.datasheet_url]

        # Deduplicate by symbol/footprint combination
        seen = set()
        deduplicated = []
        for result in filtered:
            key = (result.symbol_ref, result.footprint_ref)
            if key not in seen:
                seen.add(key)
                deduplicated.append(result)

        # Sort by confidence score and source priority
        deduplicated.sort(
            key=lambda r: (
                -r.confidence_score,  # Higher confidence first
                self.source_configs[r.source].priority,  # Lower priority number first
            )
        )

        # Limit results
        return deduplicated[: query.max_results]

    async def search_as_fallback(
        self, query: str, local_results: List[tuple]
    ) -> List[ComponentSearchResult]:
        """
        Search APIs as fallback when local results are insufficient
        Used by existing find-symbol/find-footprint commands
        """

        # Only search APIs if local results are empty or insufficient
        if len(local_results) >= 3:  # Sufficient local results
            return []

        search_query = SearchQuery(
            query=query,
            max_results=10 - len(local_results),  # Fill gap in results
            preferred_sources=[
                LibrarySource.DIGIKEY_GITHUB,
                LibrarySource.SNAPEDA,
                LibrarySource.DIGIKEY_API,
            ],  # GitHub first, then APIs
        )

        return await self.search_component(search_query)

    def load_config(self, config_path: str):
        """Load source configurations from file"""
        # TODO: Implement configuration loading
        pass

    def get_source_status(self) -> Dict[LibrarySource, Dict[str, Any]]:
        """Get status of all configured sources"""
        status = {}

        for source_type, source in self.sources.items():
            config = self.source_configs[source_type]
            status[source_type] = {
                "enabled": config.enabled,
                "priority": config.priority,
                "last_check": getattr(source, "last_check", None),
                "status": "available" if source.is_available() else "unavailable",
            }

        return status
