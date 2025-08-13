"""
Local KiCad installation library source
"""

import os
import re
import subprocess
import time
from pathlib import Path
from typing import List, Optional

from ..models import ComponentSearchResult, LibrarySource, SearchQuery
from .base import BaseLibrarySource


class LocalKiCadSource(BaseLibrarySource):
    """Source for local KiCad installation libraries"""

    def __init__(self):
        super().__init__()
        self.symbol_paths = self._find_symbol_paths()
        self.footprint_paths = self._find_footprint_paths()

    def _find_symbol_paths(self) -> List[Path]:
        """Find KiCad symbol library paths"""
        common_paths = [
            # macOS
            "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols",
            # Linux
            "/usr/share/kicad/symbols",
            "/usr/local/share/kicad/symbols",
            # Windows
            "C:/Program Files/KiCad/share/kicad/symbols",
        ]

        paths = []
        for path_str in common_paths:
            path = Path(path_str)
            if path.exists() and path.is_dir():
                paths.append(path)

        return paths

    def _find_footprint_paths(self) -> List[Path]:
        """Find KiCad footprint library paths"""
        common_paths = [
            # macOS
            "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints",
            # Linux
            "/usr/share/kicad/footprints",
            "/usr/local/share/kicad/footprints",
            # Windows
            "C:/Program Files/KiCad/share/kicad/footprints",
        ]

        paths = []
        for path_str in common_paths:
            path = Path(path_str)
            if path.exists() and path.is_dir():
                paths.append(path)

        return paths

    async def search(self, query: SearchQuery) -> List[ComponentSearchResult]:
        """Search local KiCad libraries"""

        results = []

        # Search symbols
        symbol_matches = await self._search_symbols(query.query)

        # Search footprints
        footprint_matches = await self._search_footprints(query.query)

        # Combine results
        for symbol_lib, symbol_name in symbol_matches:
            # Try to find matching footprint
            best_footprint = self._find_best_footprint_match(
                symbol_name, footprint_matches
            )

            result = ComponentSearchResult(
                symbol_library=symbol_lib,
                symbol_name=symbol_name,
                footprint_library=best_footprint[0] if best_footprint else None,
                footprint_name=best_footprint[1] if best_footprint else None,
                source=LibrarySource.LOCAL_KICAD,
                confidence_score=0.9,  # High confidence for local libraries
                availability=True,
            )
            results.append(result)

        # Add standalone footprints
        for footprint_lib, footprint_name in footprint_matches:
            # Check if already added via symbol match
            if not any(r.footprint_name == footprint_name for r in results):
                result = ComponentSearchResult(
                    footprint_library=footprint_lib,
                    footprint_name=footprint_name,
                    source=LibrarySource.LOCAL_KICAD,
                    confidence_score=0.8,
                    availability=True,
                )
                results.append(result)

        return results[: query.max_results]

    async def _search_symbols(self, query: str) -> List[tuple]:
        """Search symbol libraries for matching symbols"""

        matches = []

        for symbol_path in self.symbol_paths:
            try:
                # Use grep to find symbol files containing the query
                cmd = [
                    "find",
                    str(symbol_path),
                    "-name",
                    "*.kicad_sym",
                    "-exec",
                    "grep",
                    "-l",
                    query,
                    "{}",
                    ";",
                ]

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

                if result.returncode == 0:
                    for lib_file in result.stdout.strip().split("\n"):
                        if lib_file:
                            lib_name = Path(lib_file).stem
                            symbol_names = self._extract_symbol_names(lib_file, query)
                            for symbol_name in symbol_names:
                                matches.append((lib_name, symbol_name))

            except Exception as e:
                logger.warning(f"Error searching symbols in {symbol_path}: {e}")

        return matches

    async def _search_footprints(self, query: str) -> List[tuple]:
        """Search footprint libraries for matching footprints"""

        matches = []

        for footprint_path in self.footprint_paths:
            try:
                # Find footprint files matching query
                cmd = ["find", str(footprint_path), "-name", f"*{query}*.kicad_mod"]

                result = subprocess.run(cmd, capture_output=True, text=True, timeout=10)

                if result.returncode == 0:
                    for fp_file in result.stdout.strip().split("\n"):
                        if fp_file:
                            fp_path = Path(fp_file)
                            lib_name = fp_path.parent.name.replace(".pretty", "")
                            fp_name = fp_path.stem
                            matches.append((lib_name, fp_name))

            except Exception as e:
                logger.warning(f"Error searching footprints in {footprint_path}: {e}")

        return matches

    def _extract_symbol_names(self, lib_file: str, query: str) -> List[str]:
        """Extract symbol names from library file"""

        symbol_names = []

        try:
            with open(lib_file, "r") as f:
                content = f.read()

            # Find symbol definitions matching query
            pattern = rf'symbol\s+"[^"]*{re.escape(query)}[^"]*"'
            matches = re.findall(pattern, content, re.IGNORECASE)

            for match in matches:
                # Extract symbol name from match
                name_match = re.search(r'"([^"]+)"', match)
                if name_match:
                    symbol_names.append(name_match.group(1))

        except Exception as e:
            logger.warning(f"Error extracting symbols from {lib_file}: {e}")

        return symbol_names

    def _find_best_footprint_match(
        self, symbol_name: str, footprint_matches: List[tuple]
    ) -> Optional[tuple]:
        """Find best footprint match for a symbol"""

        # Simple heuristic: look for package type in symbol name
        symbol_lower = symbol_name.lower()

        # Common package mappings
        package_hints = {
            "qfp": ["qfp", "lqfp"],
            "qfn": ["qfn", "dfn"],
            "bga": ["bga"],
            "soic": ["soic", "so"],
            "ssop": ["ssop", "tssop"],
            "sot": ["sot"],
            "to": ["to-"],
        }

        # Find package type in symbol name
        for package_type, variants in package_hints.items():
            if any(variant in symbol_lower for variant in variants):
                # Look for matching footprints
                for lib, fp_name in footprint_matches:
                    if any(variant in fp_name.lower() for variant in variants):
                        return (lib, fp_name)

        # Fallback: return first footprint if available
        return footprint_matches[0] if footprint_matches else None

    def is_available(self) -> bool:
        """Check if local KiCad installation is available"""
        self.last_check = time.time()
        return len(self.symbol_paths) > 0 or len(self.footprint_paths) > 0
