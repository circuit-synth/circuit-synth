"""
DigiKey GitHub open source library source implementation
"""

import os
import re
import time
from pathlib import Path
from typing import Dict, List, Optional

from ..models import ComponentSearchResult, LibrarySource, SearchQuery
from .base import BaseLibrarySource


class DigiKeyGitHubSource(BaseLibrarySource):
    """Source for DigiKey's open source KiCad library on GitHub"""

    def __init__(self, library_path: Optional[Path] = None):
        super().__init__()

        # Default to submodule location
        self.library_path = library_path or Path.cwd() / "libraries" / "digikey-kicad"
        self.symbols_path = self.library_path / "digikey-symbols"
        self.footprints_path = self.library_path / "digikey-footprints.pretty"

    async def search(self, query: SearchQuery) -> List[ComponentSearchResult]:
        """Search DigiKey GitHub library"""

        if not self.is_available():
            return []

        results = []

        # Search symbols
        symbol_matches = await self._search_digikey_symbols(query.query)

        # Search footprints
        footprint_matches = await self._search_digikey_footprints(query.query)

        # Combine results - DigiKey library has 1:1 symbol to footprint mapping
        for symbol_info in symbol_matches:
            # Try to find corresponding footprint
            footprint_info = self._find_matching_footprint(
                symbol_info, footprint_matches
            )

            result = ComponentSearchResult(
                symbol_library="digikey-symbols",
                symbol_name=symbol_info["name"],
                footprint_library="digikey-footprints" if footprint_info else None,
                footprint_name=footprint_info["name"] if footprint_info else None,
                description=symbol_info.get("description"),
                manufacturer=symbol_info.get("manufacturer"),
                part_number=symbol_info.get("part_number"),
                datasheet_url=symbol_info.get("datasheet"),
                source=LibrarySource.DIGIKEY_GITHUB,
                availability=True,  # Assume available since it's in DigiKey library
                confidence_score=0.85,  # High confidence for curated library
                specifications=symbol_info.get("specifications", {}),
            )

            results.append(result)

        # Add standalone footprints
        for footprint_info in footprint_matches:
            # Check if already added via symbol match
            if not any(r.footprint_name == footprint_info["name"] for r in results):
                result = ComponentSearchResult(
                    footprint_library="digikey-footprints",
                    footprint_name=footprint_info["name"],
                    description=footprint_info.get("description"),
                    source=LibrarySource.DIGIKEY_GITHUB,
                    availability=True,
                    confidence_score=0.8,
                )
                results.append(result)

        return results[: query.max_results]

    async def _search_digikey_symbols(self, query: str) -> List[Dict]:
        """Search DigiKey symbol library files"""

        symbol_matches = []

        if not self.symbols_path.exists():
            return symbol_matches

        try:
            # Search .lib files for symbols containing query
            for lib_file in self.symbols_path.glob("*.lib"):
                matches = self._parse_lib_file(lib_file, query)
                symbol_matches.extend(matches)

        except Exception as e:
            logger.warning(f"Error searching DigiKey symbols: {e}")

        return symbol_matches

    async def _search_digikey_footprints(self, query: str) -> List[Dict]:
        """Search DigiKey footprint library"""

        footprint_matches = []

        if not self.footprints_path.exists():
            return footprint_matches

        try:
            # Search .kicad_mod files
            for fp_file in self.footprints_path.glob(f"*{query}*.kicad_mod"):
                footprint_info = {
                    "name": fp_file.stem,
                    "file": str(fp_file),
                    "description": self._extract_footprint_description(fp_file),
                }
                footprint_matches.append(footprint_info)

        except Exception as e:
            logger.warning(f"Error searching DigiKey footprints: {e}")

        return footprint_matches

    def _parse_lib_file(self, lib_file: Path, query: str) -> List[Dict]:
        """Parse DigiKey .lib file for symbols matching query"""

        symbols = []

        try:
            with open(lib_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Parse KiCad legacy library format
            # Look for DEF entries that match query
            def_pattern = r"DEF\s+(\S+)\s+(\S+)\s+.*?ENDDEF"
            def_matches = re.findall(def_pattern, content, re.DOTALL | re.IGNORECASE)

            for symbol_name, reference in def_matches:
                if query.lower() in symbol_name.lower():
                    # Extract additional metadata
                    symbol_info = {
                        "name": symbol_name,
                        "reference": reference,
                        "file": str(lib_file),
                        "library": lib_file.stem,
                    }

                    # Try to extract description and other metadata
                    symbol_section = self._extract_symbol_section(content, symbol_name)
                    if symbol_section:
                        symbol_info.update(self._parse_symbol_metadata(symbol_section))

                    symbols.append(symbol_info)

        except Exception as e:
            logger.warning(f"Error parsing {lib_file}: {e}")

        return symbols

    def _extract_symbol_section(self, content: str, symbol_name: str) -> Optional[str]:
        """Extract the DEF...ENDDEF section for a specific symbol"""

        pattern = rf"DEF\s+{re.escape(symbol_name)}\s+.*?ENDDEF"
        match = re.search(pattern, content, re.DOTALL | re.IGNORECASE)

        return match.group(0) if match else None

    def _parse_symbol_metadata(self, symbol_section: str) -> Dict:
        """Parse metadata from symbol section"""

        metadata = {}

        # Look for fields with metadata
        field_pattern = r'F(\d+)\s+"([^"]*)".*?(?:V|H)'
        field_matches = re.findall(field_pattern, symbol_section)

        for field_num, field_value in field_matches:
            field_num = int(field_num)

            # Standard KiCad fields
            if field_num == 0:
                metadata["reference"] = field_value
            elif field_num == 1:
                metadata["value"] = field_value
            elif field_num == 2:
                metadata["footprint"] = field_value
            elif field_num == 3:
                metadata["datasheet"] = field_value
            elif field_num >= 4:
                # Custom fields - common DigiKey fields
                if "digikey" in field_value.lower():
                    metadata["part_number"] = field_value
                elif "manufacturer" in field_value.lower():
                    metadata["manufacturer"] = field_value
                elif "description" in field_value.lower():
                    metadata["description"] = field_value

        return metadata

    def _extract_footprint_description(self, fp_file: Path) -> Optional[str]:
        """Extract description from footprint file"""

        try:
            with open(fp_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Look for description in footprint
            desc_match = re.search(r'descr\s+"([^"]*)"', content)
            return desc_match.group(1) if desc_match else None

        except Exception:
            return None

    def _find_matching_footprint(
        self, symbol_info: Dict, footprint_matches: List[Dict]
    ) -> Optional[Dict]:
        """Find matching footprint for symbol (DigiKey has 1:1 mapping)"""

        symbol_name = symbol_info["name"]

        # DigiKey symbols often have footprint assignment in metadata
        if "footprint" in symbol_info:
            footprint_ref = symbol_info["footprint"]
            # Extract footprint name from reference
            if ":" in footprint_ref:
                footprint_name = footprint_ref.split(":")[-1]
                for fp in footprint_matches:
                    if fp["name"] == footprint_name:
                        return fp

        # Fallback: look for similar names
        for fp in footprint_matches:
            if any(
                part in fp["name"].lower() for part in symbol_name.lower().split("-")
            ):
                return fp

        return None

    def is_available(self) -> bool:
        """Check if DigiKey GitHub library is available"""
        self.last_check = time.time()

        return (
            self.library_path.exists()
            and self.symbols_path.exists()
            and self.footprints_path.exists()
        )

    def update_library(self) -> bool:
        """Update DigiKey library from GitHub (git pull)"""

        if not self.library_path.exists():
            return False

        try:
            import subprocess

            result = subprocess.run(
                ["git", "pull"],
                cwd=self.library_path,
                capture_output=True,
                text=True,
                timeout=30,
            )
            return result.returncode == 0

        except Exception as e:
            logger.error(f"Failed to update DigiKey library: {e}")
            return False
