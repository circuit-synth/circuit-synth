"""
Lazy-loading footprint library cache for KiCad footprints.

This module provides efficient access to KiCad footprint libraries by only
parsing footprint files when they are actually needed, rather than parsing
all 14,000+ footprints at startup.
"""

import json
import logging
import os
import platform
from dataclasses import asdict, dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

import sexpdata

from .types import Arc, Layer, Line, Pad, Property, Text

logger = logging.getLogger(__name__)


@dataclass
class FootprintInfo:
    """Metadata about a footprint (without full parsing)."""

    library: str
    name: str
    file_path: Path

    # Basic metadata (loaded from index)
    description: str = ""
    tags: str = ""
    keywords: str = ""
    pad_count: int = 0
    pad_types: Set[str] = field(default_factory=set)

    # Size information (loaded from index)
    body_size: Tuple[float, float] = (0.0, 0.0)
    courtyard_area: float = 0.0

    # 3D models
    models_3d: List[str] = field(default_factory=list)

    # File info
    last_modified: Optional[datetime] = None

    # Full data (loaded on demand)
    _full_data: Optional[Dict[str, Any]] = field(default=None, init=False)
    _pads: Optional[List[Pad]] = field(default=None, init=False)

    @property
    def footprint_type(self) -> str:
        """Get footprint type: SMD, THT, or Mixed."""
        if self.is_smd:
            return "SMD"
        elif self.is_tht:
            return "THT"
        elif self.is_mixed:
            return "Mixed"
        return "Unknown"

    @property
    def is_smd(self) -> bool:
        """Check if footprint is SMD (surface mount)."""
        return "smd" in self.pad_types and "thru_hole" not in self.pad_types

    @property
    def is_tht(self) -> bool:
        """Check if footprint is THT (through-hole)."""
        return "thru_hole" in self.pad_types and "smd" not in self.pad_types

    @property
    def is_mixed(self) -> bool:
        """Check if footprint has both SMD and THT pads."""
        return "smd" in self.pad_types and "thru_hole" in self.pad_types


class FootprintLibraryCache:
    """
    Lazy-loading cache for KiCad footprint libraries.

    This implementation only parses footprint files when they are actually
    requested, making startup much faster.
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        """Initialize the lazy-loading footprint cache."""
        self._library_paths: List[Path] = []
        self._footprint_index: Dict[str, FootprintInfo] = {}  # Basic metadata only
        self._library_index: Dict[str, List[str]] = {}  # Library -> footprint names
        self._cache_dir = (
            cache_dir or Path.home() / ".cache" / "circuit_synth" / "footprints"
        )
        self._cache_dir.mkdir(parents=True, exist_ok=True)
        self._index_file = self._cache_dir / "footprint_index.json"

        # Discover libraries and load/build index
        self._discover_system_libraries()
        self._load_or_build_index()

    def _discover_system_libraries(self):
        """Automatically discover KiCad system footprint libraries."""
        system = platform.system()

        # Common KiCad footprint library paths
        search_paths = []

        if system == "Darwin":  # macOS
            search_paths.extend(
                [
                    Path(
                        "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints"
                    ),
                    Path("/Applications/KiCad.app/Contents/SharedSupport/footprints"),
                    Path.home() / "Library/Application Support/kicad/footprints",
                ]
            )
        elif system == "Windows":
            search_paths.extend(
                [
                    Path("C:/Program Files/KiCad/share/kicad/footprints"),
                    Path("C:/Program Files/KiCad/9.0/share/kicad/footprints"),
                    Path("C:/Program Files/KiCad/8.0/share/kicad/footprints"),
                    Path("C:/Program Files/KiCad/7.0/share/kicad/footprints"),
                    (
                        Path(os.environ.get("APPDATA", "")) / "kicad/footprints"
                        if os.environ.get("APPDATA")
                        else None
                    ),
                ]
            )
        else:  # Linux
            search_paths.extend(
                [
                    Path("/usr/share/kicad/footprints"),
                    Path("/usr/local/share/kicad/footprints"),
                    Path.home() / ".local/share/kicad/footprints",
                    Path.home() / ".config/kicad/footprints",
                ]
            )

        # Add paths from environment variable
        if "KICAD_FOOTPRINT_DIR" in os.environ:
            for path in os.environ["KICAD_FOOTPRINT_DIR"].split(os.pathsep):
                if path:
                    search_paths.append(Path(path))

        # Add discovered paths
        for path in search_paths:
            if path and path.exists() and path.is_dir():
                self._library_paths.append(path)
                logger.info(f"Discovered footprint library path: {path}")

    def _load_or_build_index(self):
        """Load the footprint index from cache or build it."""
        if self._index_file.exists():
            try:
                # Check if index is up to date
                index_mtime = self._index_file.stat().st_mtime
                needs_rebuild = False

                # Check if any library directory is newer than index
                for lib_path in self._library_paths:
                    if lib_path.stat().st_mtime > index_mtime:
                        needs_rebuild = True
                        break

                if not needs_rebuild:
                    # Load existing index
                    with open(self._index_file, "r") as f:
                        data = json.load(f)

                    # Reconstruct footprint index
                    for fp_id, fp_data in data.get("footprints", {}).items():
                        info = FootprintInfo(
                            library=fp_data["library"],
                            name=fp_data["name"],
                            file_path=Path(fp_data["file_path"]),
                            description=fp_data.get("description", ""),
                            tags=fp_data.get("tags", ""),
                            keywords=fp_data.get("keywords", ""),
                            pad_count=fp_data.get("pad_count", 0),
                            pad_types=set(fp_data.get("pad_types", [])),
                            body_size=tuple(fp_data.get("body_size", [0.0, 0.0])),
                            courtyard_area=fp_data.get("courtyard_area", 0.0),
                        )
                        self._footprint_index[fp_id] = info

                    # Reconstruct library index
                    self._library_index = data.get("libraries", {})

                    logger.info(
                        f"Loaded footprint index with {len(self._footprint_index)} footprints"
                    )
                    return
            except Exception as e:
                logger.warning(f"Failed to load footprint index: {e}")

        # Build new index
        logger.info("Building footprint index...")
        self._build_index()
        self._save_index()

    def _build_index(self):
        """Build the footprint index by scanning library directories."""
        total_footprints = 0

        for lib_path in self._library_paths:
            for pretty_dir in lib_path.glob("*.pretty"):
                if pretty_dir.is_dir():
                    library_name = pretty_dir.stem
                    footprint_names = []

                    for kicad_mod in pretty_dir.glob("*.kicad_mod"):
                        try:
                            # Extract just basic metadata
                            info = self._extract_basic_info(kicad_mod, library_name)
                            if info:
                                fp_id = f"{library_name}:{info.name}"
                                self._footprint_index[fp_id] = info
                                footprint_names.append(info.name)
                                total_footprints += 1
                        except Exception as e:
                            logger.debug(f"Failed to index {kicad_mod}: {e}")

                    if footprint_names:
                        self._library_index[library_name] = footprint_names

        logger.info(
            f"Indexed {total_footprints} footprints in {len(self._library_index)} libraries"
        )

    def _extract_basic_info(
        self, file_path: Path, library_name: str
    ) -> Optional[FootprintInfo]:
        """Extract just basic metadata from a footprint file (fast)."""
        try:
            # Read only the first few KB to get metadata
            with open(file_path, "r", encoding="utf-8") as f:
                # Read in chunks to find key metadata
                content = f.read(4096)  # Usually metadata is at the start

                # Quick extraction using string operations (faster than full parsing)
                info = FootprintInfo(
                    library=library_name, name=file_path.stem, file_path=file_path
                )

                # Extract description
                descr_start = content.find('(descr "')
                if descr_start != -1:
                    descr_end = content.find('")', descr_start + 8)
                    if descr_end != -1:
                        info.description = content[descr_start + 8 : descr_end]

                # Extract tags
                tags_start = content.find('(tags "')
                if tags_start != -1:
                    tags_end = content.find('")', tags_start + 7)
                    if tags_end != -1:
                        info.tags = content[tags_start + 7 : tags_end]

                # Count pads and detect types (simple regex would be faster)
                info.pad_count = content.count("(pad ")
                if " smd " in content or "(pad smd" in content:
                    info.pad_types.add("smd")
                if " thru_hole " in content or "(pad thru_hole" in content:
                    info.pad_types.add("thru_hole")

                # Generate keywords
                keywords = set()
                if info.tags:
                    keywords.update(info.tags.lower().split())
                if info.description:
                    # Add first few words of description
                    desc_words = info.description.lower().split()[:10]
                    keywords.update(desc_words)
                info.keywords = " ".join(sorted(keywords))

                return info

        except Exception as e:
            logger.debug(f"Failed to extract info from {file_path}: {e}")
            return None

    def _save_index(self):
        """Save the footprint index to disk."""
        try:
            data = {
                "footprints": {},
                "libraries": self._library_index,
                "version": 1,
                "created": datetime.now().isoformat(),
            }

            # Convert footprint info to JSON-serializable format
            for fp_id, info in self._footprint_index.items():
                data["footprints"][fp_id] = {
                    "library": info.library,
                    "name": info.name,
                    "file_path": str(info.file_path),
                    "description": info.description,
                    "tags": info.tags,
                    "keywords": info.keywords,
                    "pad_count": info.pad_count,
                    "pad_types": list(info.pad_types),
                    "body_size": list(info.body_size),
                    "courtyard_area": info.courtyard_area,
                }

            with open(self._index_file, "w") as f:
                json.dump(data, f, indent=2)

            logger.info(f"Saved footprint index to {self._index_file}")
        except Exception as e:
            logger.error(f"Failed to save footprint index: {e}")

    def search_footprints(
        self, query: str = "", filters: Optional[Dict[str, Any]] = None
    ) -> List[FootprintInfo]:
        """
        Search for footprints matching the query and filters.

        This only uses the pre-built index and doesn't parse full footprint files.
        """
        results = []
        query_lower = query.lower()

        for fp_id, info in self._footprint_index.items():
            # Check query match
            if query and not any(
                query_lower in field.lower()
                for field in [
                    info.name,
                    info.description,
                    info.tags,
                    info.keywords,
                    info.library,
                ]
            ):
                continue

            # Apply filters
            if filters:
                # Filter by footprint type
                if "footprint_type" in filters:
                    if filters["footprint_type"] != info.footprint_type:
                        continue

                # Filter by pad count
                if "pad_count" in filters:
                    pad_filter = filters["pad_count"]
                    if isinstance(pad_filter, dict):
                        if "min" in pad_filter and info.pad_count < pad_filter["min"]:
                            continue
                        if "max" in pad_filter and info.pad_count > pad_filter["max"]:
                            continue
                    elif info.pad_count != pad_filter:
                        continue

                # Filter by size
                if "max_size" in filters:
                    max_w, max_h = filters["max_size"]
                    if info.body_size[0] > max_w or info.body_size[1] > max_h:
                        continue

                # Filter by library
                if "library" in filters and info.library != filters["library"]:
                    continue

            results.append(info)

        # Sort by relevance (simple scoring based on query match location)
        if query:

            def score(info):
                if query_lower in info.name.lower():
                    return 0  # Highest priority
                elif query_lower in info.library.lower():
                    return 1
                elif query_lower in info.tags.lower():
                    return 2
                else:
                    return 3

            results.sort(key=lambda x: (score(x), x.name))

        return results

    def get_footprint(self, footprint_id: str) -> Optional[FootprintInfo]:
        """Get basic footprint info by ID (library:name format)."""
        return self._footprint_index.get(footprint_id)

    def get_footprint_data(self, footprint_id: str) -> Optional[Dict[str, Any]]:
        """
        Get full footprint data by parsing the file.

        This is called only when full pad/graphic data is needed.
        """
        info = self._footprint_index.get(footprint_id)
        if not info:
            return None

        # Check if we already have cached full data
        if info._full_data is not None:
            return info._full_data

        # Parse the full file
        try:
            with open(info.file_path, "r", encoding="utf-8") as f:
                content = f.read()

            parsed = sexpdata.loads(content)

            # Convert to dictionary format for easier use
            info._full_data = self._sexp_to_dict(parsed)
            return info._full_data

        except Exception as e:
            logger.error(f"Failed to parse footprint {footprint_id}: {e}")
            return None

    def _sexp_to_dict(self, sexp) -> Dict[str, Any]:
        """Convert S-expression to dictionary format."""
        if not isinstance(sexp, list):
            return sexp

        result = {"_tag": str(sexp[0])}

        # Process elements
        values = []
        for i, item in enumerate(sexp[1:]):
            if isinstance(item, list) and len(item) > 0:
                # Nested s-expression
                key = str(item[0])
                if key not in result:
                    result[key] = []
                result[key].append(item[1:] if len(item) > 1 else item)
            else:
                # Direct value
                values.append(item)

        # Store direct values with index keys
        for i, val in enumerate(values):
            result[f"value_{i}"] = val

        return result

    def list_libraries(self) -> List[str]:
        """Get list of all available libraries."""
        return sorted(self._library_index.keys())

    def refresh_cache(self):
        """Rebuild the footprint index."""
        logger.info("Refreshing footprint cache...")
        self._footprint_index.clear()
        self._library_index.clear()
        self._build_index()
        self._save_index()


# Global cache instance
_footprint_cache: Optional[FootprintLibraryCache] = None


def get_footprint_cache() -> FootprintLibraryCache:
    """Get the global footprint cache instance."""
    global _footprint_cache
    if _footprint_cache is None:
        _footprint_cache = FootprintLibraryCache()
    return _footprint_cache
