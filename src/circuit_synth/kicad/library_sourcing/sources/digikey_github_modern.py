"""
DigiKey GitHub library source using converted modern .kicad_sym files
"""

import re
import time
from pathlib import Path
from typing import Dict, List, Optional

from ..converter import DigiKeyLibraryConverter
from ..models import ComponentSearchResult, LibrarySource, SearchQuery
from .base import BaseLibrarySource


class DigiKeyGitHubModernSource(BaseLibrarySource):
    """Source for DigiKey's GitHub library using converted .kicad_sym files"""

    def __init__(self, library_path: Optional[Path] = None):
        super().__init__()

        self.converter = DigiKeyLibraryConverter(library_path)
        self.symbols_path = None
        self.footprints_path = None

        # Auto-convert if needed and get paths
        self._ensure_converted()

    def _ensure_converted(self):
        """Ensure DigiKey library is converted to modern format"""

        if self.converter.is_conversion_needed():
            logger.info("Converting DigiKey legacy library to modern format...")
            success = self.converter.convert_all_libraries()
            if not success:
                logger.warning("DigiKey library conversion failed")
                return

        # Set paths to converted libraries
        self.symbols_path = self.converter.get_converted_symbols_path()
        self.footprints_path = self.converter.digikey_path / "digikey-footprints.pretty"

    async def search(self, query: SearchQuery) -> List[ComponentSearchResult]:
        """Search converted DigiKey library"""

        if not self.is_available():
            return []

        results = []

        # Search converted symbol files
        symbol_matches = await self._search_modern_symbols(query.query)

        # Search footprints
        footprint_matches = await self._search_footprints(query.query)

        # Combine results with DigiKey's 1:1 mapping
        for symbol_info in symbol_matches:
            # Find matching footprint
            footprint_info = self._find_matching_footprint(
                symbol_info, footprint_matches
            )

            result = ComponentSearchResult(
                symbol_library=symbol_info["library"],
                symbol_name=symbol_info["name"],
                footprint_library="digikey-footprints" if footprint_info else None,
                footprint_name=footprint_info["name"] if footprint_info else None,
                description=symbol_info.get("description"),
                manufacturer=symbol_info.get("manufacturer"),
                part_number=symbol_info.get("part_number"),
                datasheet_url=symbol_info.get("datasheet"),
                source=LibrarySource.DIGIKEY_GITHUB,
                availability=True,
                confidence_score=0.9,  # High confidence for curated library
                supplier_links=(
                    [
                        f"https://www.digikey.com/product-detail/en/{symbol_info.get('part_number', '')}"
                    ]
                    if symbol_info.get("part_number")
                    else []
                ),
                specifications=symbol_info.get("specifications", {}),
            )

            results.append(result)

        return results[: query.max_results]

    async def _search_modern_symbols(self, query: str) -> List[Dict]:
        """Search modern .kicad_sym files"""

        symbol_matches = []

        if not self.symbols_path or not self.symbols_path.exists():
            return symbol_matches

        try:
            # Search all .kicad_sym files
            for sym_file in self.symbols_path.glob("*.kicad_sym"):
                matches = self._parse_kicad_sym_file(sym_file, query)
                symbol_matches.extend(matches)

        except Exception as e:
            logger.warning(f"Error searching DigiKey modern symbols: {e}")

        return symbol_matches

    def _parse_kicad_sym_file(self, sym_file: Path, query: str) -> List[Dict]:
        """Parse modern .kicad_sym file for symbols matching query"""

        symbols = []

        try:
            with open(sym_file, "r", encoding="utf-8", errors="ignore") as f:
                content = f.read()

            # Parse modern KiCad symbol format
            # Look for symbol definitions: (symbol "NAME"
            symbol_pattern = r'\(symbol\s+"([^"]+)"'
            symbol_matches = re.findall(symbol_pattern, content)

            for symbol_name in symbol_matches:
                if query.lower() in symbol_name.lower():
                    # Extract symbol section
                    symbol_section = self._extract_symbol_section(content, symbol_name)

                    symbol_info = {
                        "name": symbol_name,
                        "library": sym_file.stem,
                        "file": str(sym_file),
                    }

                    # Parse properties from symbol section
                    if symbol_section:
                        properties = self._parse_symbol_properties(symbol_section)
                        symbol_info.update(properties)

                    symbols.append(symbol_info)

        except Exception as e:
            logger.warning(f"Error parsing {sym_file}: {e}")

        return symbols

    def _extract_symbol_section(self, content: str, symbol_name: str) -> Optional[str]:
        """Extract symbol section from .kicad_sym file"""

        # Find the symbol section
        start_pattern = rf'\(symbol\s+"{re.escape(symbol_name)}"'
        start_match = re.search(start_pattern, content)

        if not start_match:
            return None

        # Find matching closing parenthesis
        start_pos = start_match.start()
        paren_count = 0
        pos = start_pos

        while pos < len(content):
            if content[pos] == "(":
                paren_count += 1
            elif content[pos] == ")":
                paren_count -= 1
                if paren_count == 0:
                    return content[start_pos : pos + 1]
            pos += 1

        return None

    def _parse_symbol_properties(self, symbol_section: str) -> Dict:
        """Parse properties from modern symbol section"""

        properties = {}

        # Parse property entries: (property "NAME" "VALUE"
        prop_pattern = r'\(property\s+"([^"]+)"\s+"([^"]*)"'
        prop_matches = re.findall(prop_pattern, symbol_section)

        for prop_name, prop_value in prop_matches:
            if prop_name == "Footprint":
                properties["footprint"] = prop_value
            elif prop_name == "Datasheet":
                properties["datasheet"] = prop_value
            elif prop_name == "Description":
                properties["description"] = prop_value
            elif prop_name == "Manufacturer":
                properties["manufacturer"] = prop_value
            elif "Part" in prop_name or "PN" in prop_name:
                properties["part_number"] = prop_value

        return properties

    async def _search_footprints(self, query: str) -> List[Dict]:
        """Search DigiKey footprint library"""

        footprint_matches = []

        if not self.footprints_path or not self.footprints_path.exists():
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
        """Find matching footprint for symbol"""

        # Check if symbol has footprint assignment
        if "footprint" in symbol_info:
            footprint_ref = symbol_info["footprint"]
            if ":" in footprint_ref:
                footprint_name = footprint_ref.split(":")[-1]
                for fp in footprint_matches:
                    if fp["name"] == footprint_name:
                        return fp

        # Fallback: look for similar names
        symbol_name = symbol_info["name"].lower()
        for fp in footprint_matches:
            if any(part in fp["name"].lower() for part in symbol_name.split("-")):
                return fp

        return None

    def is_available(self) -> bool:
        """Check if converted DigiKey library is available"""
        self.last_check = time.time()

        return (
            self.symbols_path
            and self.symbols_path.exists()
            and self.footprints_path
            and self.footprints_path.exists()
        )

    def update_library(self) -> bool:
        """Update DigiKey library and reconvert if needed"""

        # Update submodule
        try:
            import subprocess

            result = subprocess.run(
                ["git", "submodule", "update", "--remote", "libraries/digikey-kicad"],
                capture_output=True,
                text=True,
                timeout=60,
            )

            if result.returncode == 0:
                # Reconvert after update
                self.converter.cleanup_converted_libraries()
                return self.converter.convert_all_libraries()

        except Exception as e:
            logger.error(f"Failed to update DigiKey library: {e}")

        return False
