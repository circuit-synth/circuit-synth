"""
Integration with existing find-symbol and find-footprint commands
"""

import asyncio
from pathlib import Path
from typing import Any, Dict, List

from .models import ComponentSearchResult, SearchQuery
from .orchestrator import LibraryOrchestrator


class EnhancedSymbolFinder:
    """Enhanced symbol finder with fallback to API sources"""

    def __init__(self):
        self.orchestrator = LibraryOrchestrator()

    async def find_symbols_with_fallback(self, search_term: str) -> Dict[str, Any]:
        """
        Find symbols with fallback to API sources

        Returns format compatible with existing find-symbol command:
        {
            "local_results": [(library, symbol_name), ...],
            "api_results": [ComponentSearchResult, ...],
            "total_found": int
        }
        """

        # First, try local KiCad search (existing logic)
        local_results = await self._search_local_symbols(search_term)

        # If insufficient local results, search APIs as fallback
        api_results = []
        if len(local_results) < 3:
            api_results = await self.orchestrator.search_as_fallback(
                search_term, local_results
            )

        return {
            "local_results": local_results,
            "api_results": api_results,
            "total_found": len(local_results) + len(api_results),
        }

    async def _search_local_symbols(self, search_term: str) -> List[tuple]:
        """Search local KiCad symbols (existing logic)"""

        # Use LocalKiCadSource for consistency
        local_source = self.orchestrator.sources.get("LOCAL_KICAD")
        if not local_source:
            return []

        query = SearchQuery(query=search_term, max_results=10)
        results = await local_source.search(query)

        # Convert to tuple format for compatibility
        local_results = []
        for result in results:
            if result.symbol_library and result.symbol_name:
                local_results.append((result.symbol_library, result.symbol_name))

        return local_results

    def format_results_for_display(self, results: Dict[str, Any]) -> str:
        """Format results for command line display"""

        output_lines = []

        # Local results
        if results["local_results"]:
            output_lines.append("## Local KiCad Libraries")

            # Group by library
            library_groups = {}
            for lib, symbol in results["local_results"]:
                if lib not in library_groups:
                    library_groups[lib] = []
                library_groups[lib].append(symbol)

            for library, symbols in library_groups.items():
                output_lines.append(f"\n**Library**: {library}.kicad_sym")
                output_lines.append("**Symbols**:")
                for symbol in symbols[:5]:  # Limit display
                    output_lines.append(f"- {symbol}")
                if len(symbols) > 5:
                    output_lines.append(f"- ... and {len(symbols) - 5} more")

        # API results
        if results["api_results"]:
            output_lines.append("\n## External Sources")

            for result in results["api_results"][:5]:  # Limit display
                source_tag = f"[{result.source.value.upper()}]"
                if result.symbol_ref:
                    output_lines.append(f"- {result.symbol_ref} {source_tag}")
                    if result.description:
                        output_lines.append(f"  *{result.description}*")
                    if result.manufacturer and result.part_number:
                        output_lines.append(
                            f"  {result.manufacturer} - {result.part_number}"
                        )

        # Summary
        total = results["total_found"]
        if total == 0:
            output_lines.append(
                "No symbols found. Try different search terms or check API configuration."
            )
        else:
            local_count = len(results["local_results"])
            api_count = len(results["api_results"])
            output_lines.append(
                f"\n**Found {total} symbols** ({local_count} local, {api_count} external)"
            )

        return "\n".join(output_lines)


class EnhancedFootprintFinder:
    """Enhanced footprint finder with fallback to API sources"""

    def __init__(self):
        self.orchestrator = LibraryOrchestrator()

    async def find_footprints_with_fallback(self, search_term: str) -> Dict[str, Any]:
        """Find footprints with fallback to API sources"""

        # Search local footprints first
        local_results = await self._search_local_footprints(search_term)

        # API fallback if needed
        api_results = []
        if len(local_results) < 3:
            # Create query focused on footprints
            query = SearchQuery(
                query=search_term,
                max_results=10 - len(local_results),
                preferred_sources=["SNAPEDA", "DIGIKEY"],
            )
            api_results = await self.orchestrator.search_component(query)
            # Filter to only results with footprints
            api_results = [r for r in api_results if r.footprint_ref]

        return {
            "local_results": local_results,
            "api_results": api_results,
            "total_found": len(local_results) + len(api_results),
        }

    async def _search_local_footprints(self, search_term: str) -> List[tuple]:
        """Search local KiCad footprints"""

        local_source = self.orchestrator.sources.get("LOCAL_KICAD")
        if not local_source:
            return []

        query = SearchQuery(query=search_term, max_results=10)
        results = await local_source.search(query)

        # Convert to tuple format
        local_results = []
        for result in results:
            if result.footprint_library and result.footprint_name:
                local_results.append((result.footprint_library, result.footprint_name))

        return local_results
