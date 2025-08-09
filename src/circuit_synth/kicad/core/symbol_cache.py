"""
Symbol library cache for KiCad API.

This module provides caching and lookup functionality for KiCad symbol libraries,
allowing efficient access to symbol definitions and pin information.
"""

import hashlib
import json
import logging
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Set, Tuple

from ...kicad.kicad_symbol_parser import parse_kicad_sym_file
from .types import Point, SchematicPin

logger = logging.getLogger(__name__)


@dataclass
class SymbolDefinition:
    """Definition of a symbol from KiCad library."""

    lib_id: str
    name: str
    reference_prefix: str
    description: str = ""
    keywords: str = ""
    datasheet: str = ""
    pins: List[SchematicPin] = field(default_factory=list)
    units: int = 1
    unit_names: Dict[int, str] = field(default_factory=dict)
    power_symbol: bool = False
    graphic_elements: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def bounding_box(self) -> Tuple[float, float, float, float]:
        """Calculate bounding box from graphic elements and pins."""
        if not self.graphic_elements and not self.pins:
            return (0, 0, 0, 0)

        min_x = min_y = float("inf")
        max_x = max_y = float("-inf")

        # Check pins
        for pin in self.pins:
            min_x = min(min_x, pin.position.x)
            min_y = min(min_y, pin.position.y)
            max_x = max(max_x, pin.position.x)
            max_y = max(max_y, pin.position.y)

        # Check graphic elements
        for elem in self.graphic_elements:
            if "points" in elem:
                for point in elem["points"]:
                    min_x = min(min_x, point[0])
                    min_y = min(min_y, point[1])
                    max_x = max(max_x, point[0])
                    max_y = max(max_y, point[1])

        return (min_x, min_y, max_x, max_y)


class SymbolLibraryCache:
    """
    Cache for KiCad symbol libraries.

    This class manages loading and caching of symbol definitions from KiCad
    symbol libraries, providing fast lookup and access to symbol data.
    """

    def __init__(self, cache_dir: Optional[Path] = None):
        """
        Initialize the symbol cache.

        Args:
            cache_dir: Directory to store cached symbol data
        """
        self._symbols: Dict[str, SymbolDefinition] = {}
        self._library_paths: List[Path] = []
        self._cache_dir = (
            cache_dir or Path.home() / ".cache" / "circuit_synth" / "symbols"
        )
        self._cache_dir.mkdir(parents=True, exist_ok=True)

        # Complete symbol index: { "symbol_name": {"lib_name": str, "lib_path": Path} }
        self._symbol_index: Dict[str, Dict[str, Any]] = {}

        # Library index: { "lib_name": Path }
        self._library_index: Dict[str, Path] = {}

        # Library data cache: { lib_path : { "file_hash": <hash>, "symbols": {...} } }
        self._library_data: Dict[str, Dict[str, Any]] = {}

        # Flag to track if we've built the complete index
        self._index_built: bool = False

        # Persistent index file path
        self._index_file = self._cache_dir / "symbol_index.json"
        self._index_metadata_file = self._cache_dir / "symbol_index_metadata.json"

        # Try to load persistent index
        self._load_persistent_index()

        # Track loaded library files for lazy loading
        self._loaded_libraries: Set[Path] = set()

        # Load default libraries
        self._load_default_libraries()

    def _load_persistent_index(self) -> bool:
        """
        Load the persistent symbol index from disk if available and valid.

        Returns:
            True if index was loaded successfully, False otherwise
        """
        if not self._index_file.exists() or not self._index_metadata_file.exists():
            logger.debug("No persistent symbol index found")
            return False

        try:
            import time

            load_start = time.perf_counter()

            # Load metadata to check validity
            with open(self._index_metadata_file, "r") as f:
                metadata = json.load(f)

            # Check if index is still valid
            current_dirs = self._parse_kicad_symbol_dirs()
            saved_dirs = [Path(d) for d in metadata.get("symbol_dirs", [])]

            # Invalidate if directories changed
            if set(str(d) for d in current_dirs) != set(str(d) for d in saved_dirs):
                logger.info("Symbol directories changed, invalidating index")
                return False

            # Check if any directory was modified after index creation
            index_timestamp = metadata.get("timestamp", 0)
            for dir_path in current_dirs:
                if dir_path.exists():
                    dir_mtime = dir_path.stat().st_mtime
                    if dir_mtime > index_timestamp:
                        logger.info(
                            f"Symbol directory {dir_path} modified, invalidating index"
                        )
                        return False

            # Load the actual index
            with open(self._index_file, "r") as f:
                index_data = json.load(f)

            # Restore symbol index
            self._symbol_index = {}
            for sym_name, info in index_data.get("symbol_index", {}).items():
                self._symbol_index[sym_name] = {
                    "lib_name": info["lib_name"],
                    "lib_path": Path(info["lib_path"]),
                }

            # Restore library index
            self._library_index = {}
            for lib_name, lib_path in index_data.get("library_index", {}).items():
                self._library_index[lib_name] = Path(lib_path)

            self._index_built = True

            load_time = (time.perf_counter() - load_start) * 1000
            logger.info(
                f"Loaded persistent symbol index: {len(self._symbol_index)} symbols, "
                f"{len(self._library_index)} libraries in {load_time:.2f}ms"
            )

            return True

        except Exception as e:
            logger.warning(f"Failed to load persistent index: {e}")
            return False

    def add_library_path(self, path: Path):
        """Add a path to search for symbol libraries."""
        if path not in self._library_paths:
            self._library_paths.append(path)
            logger.info(f"Added library path: {path}")

    def get_symbol(self, lib_id: str) -> Optional[SymbolDefinition]:
        """
        Get a symbol definition by library ID using lazy search.

        Args:
            lib_id: Library ID in format "Library:Symbol"

        Returns:
            SymbolDefinition if found, None otherwise
        """
        import time

        get_start = time.perf_counter()
        logger.debug(f"🔍 get_symbol called for: {lib_id}")

        # First check if already loaded
        if lib_id in self._symbols:
            get_time = (time.perf_counter() - get_start) * 1000
            logger.debug(f"✅ Cache HIT for {lib_id} in {get_time:.2f}ms")
            return self._symbols[lib_id]

        logger.debug(f"❌ Cache MISS for {lib_id}, trying lazy search...")
        # Try lazy symbol search first (much faster)
        symbol = self._lazy_symbol_search(lib_id)
        if symbol:
            return symbol

        # Only build complete index as last resort
        logger.debug(f"Lazy search failed for {lib_id}, falling back to complete index")
        self._build_complete_index()

        # Try to parse the lib_id
        try:
            lib_name, sym_name = lib_id.split(":")
        except ValueError:
            logger.error(
                f"Invalid symbol_id format; expected 'LibName:SymbolName', got '{lib_id}'"
            )
            return None

        # Try to load the symbol from the specified library
        if self._load_symbol(lib_id):
            return self._symbols.get(lib_id)

        # If that fails, try to find the symbol in any library
        if sym_name in self._symbol_index:
            actual_lib_name = self._symbol_index[sym_name]["lib_name"]
            actual_lib_id = f"{actual_lib_name}:{sym_name}"
            logger.info(
                f"Found symbol '{sym_name}' in library '{actual_lib_name}' instead of '{lib_name}'"
            )

            if self._load_symbol(actual_lib_id):
                # Also store under the original lib_id for future lookups
                self._symbols[lib_id] = self._symbols[actual_lib_id]
                return self._symbols[lib_id]

        return None

    def get_symbol_by_name(self, symbol_name: str) -> Optional[SymbolDefinition]:
        """
        Get symbol data by just the symbol name (without library prefix).
        Automatically finds the library containing the symbol.

        Args:
            symbol_name: Symbol name without library prefix

        Returns:
            SymbolDefinition if found, None otherwise
        """
        # Build index if needed
        self._build_complete_index()

        # Check if symbol exists in index
        if symbol_name not in self._symbol_index:
            return None

        # Get the library containing this symbol
        lib_name = self._symbol_index[symbol_name]["lib_name"]
        lib_id = f"{lib_name}:{symbol_name}"

        # Use the regular get_symbol method
        return self.get_symbol(lib_id)

    def get_reference_prefix(self, lib_id: str) -> str:
        """
        Get the reference prefix for a symbol.

        Args:
            lib_id: Library ID

        Returns:
            Reference prefix (e.g., "R" for resistors, "C" for capacitors)
        """
        symbol = self.get_symbol(lib_id)
        if symbol:
            return symbol.reference_prefix

        # Fallback to common patterns
        if "Device:R" in lib_id:
            return "R"
        elif "Device:C" in lib_id:
            return "C"
        elif "Device:L" in lib_id:
            return "L"
        elif "Device:D" in lib_id:
            return "D"
        elif "Device:Q" in lib_id:
            return "Q"
        elif "Connector" in lib_id:
            return "J"
        elif "Switch" in lib_id:
            return "SW"
        else:
            return "U"

    def _load_default_libraries(self):
        """Load commonly used symbol libraries."""
        # Check for cached symbol data
        cache_file = self._cache_dir / "default_symbols.json"
        if cache_file.exists():
            try:
                with open(cache_file, "r") as f:
                    data = json.load(f)
                    for lib_id, symbol_data in data.items():
                        self._symbols[lib_id] = self._deserialize_symbol(symbol_data)
                logger.info(f"Loaded {len(self._symbols)} symbols from cache")
                return
            except Exception as e:
                logger.warning(f"Failed to load symbol cache: {e}")

        # Don't create hardcoded symbols - load from actual KiCad libraries instead
        # self._create_default_symbols()
        logger.debug(
            "Skipping hardcoded symbols - will load from KiCad libraries on demand"
        )

    def _load_symbol(self, lib_id: str) -> bool:
        """
        Try to load a symbol from library files.

        Args:
            lib_id: Library ID to load

        Returns:
            True if symbol was loaded successfully
        """
        try:
            lib_name, sym_name = lib_id.split(":")
        except ValueError:
            return False

        # Find the library file
        lib_path = self._find_library_file(lib_name)
        if not lib_path:
            return False

        # Load the library
        library_data = self._load_library(lib_path)
        if not library_data or "symbols" not in library_data:
            return False

        # Find the symbol in the library
        if sym_name not in library_data["symbols"]:
            return False

        # Convert the parsed symbol data to SymbolDefinition
        symbol_data = library_data["symbols"][sym_name]
        symbol_def = self._convert_to_symbol_definition(lib_id, symbol_data)

        if symbol_def:
            self._symbols[lib_id] = symbol_def
            return True

        return False

    def _save_cache(self):
        """Save current symbols to cache file."""
        cache_file = self._cache_dir / "default_symbols.json"
        try:
            data = {}
            for lib_id, symbol in self._symbols.items():
                data[lib_id] = self._serialize_symbol(symbol)

            with open(cache_file, "w") as f:
                json.dump(data, f, indent=2)

            logger.info(f"Saved {len(data)} symbols to cache")
        except Exception as e:
            logger.error(f"Failed to save symbol cache: {e}")

    def _serialize_symbol(self, symbol: SymbolDefinition) -> Dict[str, Any]:
        """Serialize a symbol definition to JSON-compatible format."""
        return {
            "lib_id": symbol.lib_id,
            "name": symbol.name,
            "reference_prefix": symbol.reference_prefix,
            "description": symbol.description,
            "keywords": symbol.keywords,
            "datasheet": symbol.datasheet,
            "pins": [
                {
                    "number": pin.number,
                    "name": pin.name,
                    "type": pin.type,
                    "position": {"x": pin.position.x, "y": pin.position.y},
                    "orientation": pin.orientation,
                }
                for pin in symbol.pins
            ],
            "units": symbol.units,
            "unit_names": symbol.unit_names,
            "power_symbol": symbol.power_symbol,
            "graphic_elements": symbol.graphic_elements,
        }

    def _deserialize_symbol(self, data: Dict[str, Any]) -> SymbolDefinition:
        """Deserialize a symbol definition from JSON data."""
        pins = []
        for pin_data in data.get("pins", []):
            pins.append(
                SchematicPin(
                    number=pin_data["number"],
                    name=pin_data["name"],
                    type=pin_data["type"],
                    position=Point(
                        pin_data["position"]["x"], pin_data["position"]["y"]
                    ),
                    orientation=pin_data.get("orientation", 0),
                )
            )

        return SymbolDefinition(
            lib_id=data["lib_id"],
            name=data["name"],
            reference_prefix=data["reference_prefix"],
            description=data.get("description", ""),
            keywords=data.get("keywords", ""),
            datasheet=data.get("datasheet", ""),
            pins=pins,
            units=data.get("units", 1),
            unit_names=data.get("unit_names", {}),
            power_symbol=data.get("power_symbol", False),
            graphic_elements=data.get("graphic_elements", []),
        )

    def _build_complete_index(self) -> None:
        """
        Build a complete index of ALL symbols from ALL .kicad_sym files in KICAD_SYMBOL_DIR.
        This enables automatic discovery of any symbol without knowing the library name.
        """
        if self._index_built:
            return

        logger.debug("Building complete symbol library index...")

        # Parse KICAD_SYMBOL_DIR - can contain multiple paths separated by colons
        kicad_dirs = self._parse_kicad_symbol_dirs()

        if not kicad_dirs:
            logger.error("No valid KiCad symbol directories found")
            self._index_built = True  # Mark as built to avoid repeated attempts
            return

        logger.debug(f"Scanning symbol libraries in {len(kicad_dirs)} directories:")
        for dir_path in kicad_dirs:
            logger.debug(f"  - {dir_path}")

        # Build library index
        self._library_index.clear()
        self._symbol_index.clear()

        total_files = 0
        for symbol_dir in kicad_dirs:
            # Find all .kicad_sym files recursively in this directory
            try:
                symbol_files = list(symbol_dir.rglob("*.kicad_sym"))
                total_files += len(symbol_files)
                logger.debug(f"Found {len(symbol_files)} symbol files in {symbol_dir}")

                for sym_file in symbol_files:
                    lib_name = sym_file.stem

                    # Handle duplicate library names from different directories
                    original_lib_name = lib_name
                    counter = 1
                    while lib_name in self._library_index:
                        lib_name = f"{original_lib_name}_{counter}"
                        counter += 1

                    self._library_index[lib_name] = sym_file

                    # Parse the file to get symbol names (lightweight parsing)
                    try:
                        symbol_names = self._extract_symbol_names_fast(sym_file)
                        for symbol_name in symbol_names:
                            # Store in symbol index for fast lookup
                            # If symbol exists in multiple libraries, keep the first one found
                            if symbol_name not in self._symbol_index:
                                self._symbol_index[symbol_name] = {
                                    "lib_name": lib_name,
                                    "lib_path": sym_file,
                                }
                        logger.debug(
                            f"Indexed {len(symbol_names)} symbols from {lib_name}"
                        )
                    except Exception as e:
                        logger.warning(f"Failed to index symbols from {sym_file}: {e}")

            except Exception as e:
                logger.warning(f"Failed to scan directory {symbol_dir}: {e}")

        self._index_built = True
        logger.debug(
            f"Symbol index built: {len(self._library_index)} libraries, {len(self._symbol_index)} symbols"
        )

        # Save the index to disk for future use
        self._save_persistent_index()

    def _save_persistent_index(self) -> bool:
        """
        Save the symbol index to disk for faster startup next time.

        Returns:
            True if saved successfully, False otherwise
        """
        try:
            import time

            save_start = time.perf_counter()

            # Prepare index data with string paths for JSON serialization
            symbol_index_data = {}
            for sym_name, info in self._symbol_index.items():
                symbol_index_data[sym_name] = {
                    "lib_name": info["lib_name"],
                    "lib_path": str(info["lib_path"]),
                }

            library_index_data = {}
            for lib_name, lib_path in self._library_index.items():
                library_index_data[lib_name] = str(lib_path)

            # Save the main index
            index_data = {
                "version": "1.0",
                "symbol_index": symbol_index_data,
                "library_index": library_index_data,
                "symbol_count": len(self._symbol_index),
                "library_count": len(self._library_index),
            }

            with open(self._index_file, "w") as f:
                json.dump(index_data, f, indent=2)

            # Save metadata for validation
            metadata = {
                "timestamp": time.time(),
                "symbol_dirs": [str(d) for d in self._parse_kicad_symbol_dirs()],
                "kicad_version": os.environ.get("KICAD_VERSION", "unknown"),
                "index_version": "1.0",
            }

            with open(self._index_metadata_file, "w") as f:
                json.dump(metadata, f, indent=2)

            save_time = (time.perf_counter() - save_start) * 1000
            logger.info(
                f"Saved persistent symbol index: {len(self._symbol_index)} symbols in {save_time:.2f}ms"
            )
            logger.debug(f"Index saved to: {self._index_file}")

            return True

        except Exception as e:
            logger.error(f"Failed to save persistent index: {e}")
            return False

    def _parse_kicad_symbol_dirs(self) -> List[Path]:
        """
        Parse KICAD_SYMBOL_DIR environment variable which can contain multiple paths
        separated by colons (like PATH variable). Returns list of valid directory paths.
        """
        kicad_dir_env = os.environ.get("KICAD_SYMBOL_DIR", "")
        valid_dirs = []

        if kicad_dir_env:
            # Split by colon (Unix-style) or semicolon (Windows-style)
            separator = ";" if os.name == "nt" else ":"
            dir_paths = kicad_dir_env.split(separator)

            for dir_path in dir_paths:
                dir_path = dir_path.strip()
                if not dir_path:
                    continue

                path_obj = Path(dir_path)
                if path_obj.exists() and path_obj.is_dir():
                    valid_dirs.append(path_obj)
                    logger.debug(f"Added valid symbol directory: {path_obj}")
                else:
                    logger.warning(f"Skipping invalid symbol directory: {path_obj}")

        # If no valid directories from environment, try defaults
        if not valid_dirs:
            logger.warning("KICAD_SYMBOL_DIR not set or invalid, trying default paths")
            default_dirs = [
                "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/",  # macOS
                "/usr/share/kicad/symbols/",  # Linux
                "C:\\Program Files\\KiCad\\share\\kicad\\symbols\\",  # Windows
                # Also check the path from the log output
                "/Users/shanemattner/Desktop/skip/electronics/PCB/pcb_libraries/kicad",
            ]

            for dir_path in default_dirs:
                path_obj = Path(dir_path)
                if path_obj.exists() and path_obj.is_dir():
                    valid_dirs.append(path_obj)
                    logger.info(f"Using default symbol directory: {path_obj}")

        return valid_dirs

    def _lazy_symbol_search(self, lib_id: str) -> Optional[SymbolDefinition]:
        """
        Fast lazy search for symbols without building complete index.
        Uses multiple strategies in order of speed.
        """
        try:
            lib_name, sym_name = lib_id.split(":")
        except ValueError:
            logger.error(f"Invalid symbol_id format: {lib_id}")
            return None

        # Strategy 1: File-based discovery (fastest - < 0.01s)
        symbol_file = self._find_symbol_file_by_name(lib_name)
        if symbol_file and symbol_file.exists():
            logger.debug(f"Found symbol file by name: {symbol_file}")
            return self._load_symbol_from_file(symbol_file, lib_id)

        # Strategy 2: Ripgrep search (fast - < 0.1s)
        symbol_file = self._ripgrep_symbol_search(lib_name, sym_name)
        if symbol_file:
            logger.debug(f"Found symbol via ripgrep: {symbol_file}")
            return self._load_symbol_from_file(symbol_file, lib_id)

        # Strategy 3: Python grep fallback (medium - < 1s)
        symbol_file = self._python_grep_search(lib_name, sym_name)
        if symbol_file:
            logger.debug(f"Found symbol via Python grep: {symbol_file}")
            return self._load_symbol_from_file(symbol_file, lib_id)

        logger.debug(f"Lazy search failed for {lib_id}")
        return None

    def _find_symbol_file_by_name(self, lib_name: str) -> Optional[Path]:
        """Find symbol file using intelligent file name guessing."""
        kicad_dirs = self._parse_kicad_symbol_dirs()

        for kicad_dir in kicad_dirs:
            # Try exact library name first
            candidates = [
                kicad_dir / f"{lib_name}.kicad_sym",
                kicad_dir / f"{lib_name.lower()}.kicad_sym",
                kicad_dir / f"{lib_name.upper()}.kicad_sym",
                kicad_dir / f"{lib_name.replace('_', '-')}.kicad_sym",
                kicad_dir / f"{lib_name.replace('-', '_')}.kicad_sym",
            ]

            for candidate in candidates:
                if candidate.exists():
                    return candidate

        return None

    def _ripgrep_symbol_search(self, lib_name: str, sym_name: str) -> Optional[Path]:
        """Use ripgrep to quickly find symbol in .kicad_sym files."""
        import subprocess

        kicad_dirs = self._parse_kicad_symbol_dirs()

        for kicad_dir in kicad_dirs:
            try:
                # Search for the specific symbol pattern
                result = subprocess.run(
                    [
                        "rg",
                        "-l",  # list files only
                        f'\\(symbol\\s+"{sym_name}"',  # regex pattern for symbol definition
                        str(kicad_dir),
                        "--type-add",
                        "kicad:*.kicad_sym",
                        "--type",
                        "kicad",
                    ],
                    capture_output=True,
                    text=True,
                    timeout=5,
                )

                if result.returncode == 0 and result.stdout.strip():
                    # Return first match
                    first_file = result.stdout.strip().split("\n")[0]
                    return Path(first_file)

            except (FileNotFoundError, subprocess.TimeoutExpired):
                # ripgrep not available or too slow, skip
                continue

        return None

    def _python_grep_search(self, lib_name: str, sym_name: str) -> Optional[Path]:
        """Fallback Python-based grep search for symbols."""
        import re

        kicad_dirs = self._parse_kicad_symbol_dirs()
        pattern = re.compile(rf'\(symbol\s+"{re.escape(sym_name)}"')

        for kicad_dir in kicad_dirs:
            # Search .kicad_sym files
            for sym_file in kicad_dir.rglob("*.kicad_sym"):
                try:
                    # Read file in chunks to avoid memory issues
                    with open(sym_file, "r", encoding="utf-8") as f:
                        chunk = f.read(8192)  # Read first 8KB
                        if pattern.search(chunk):
                            return sym_file
                except (IOError, UnicodeDecodeError):
                    continue

        return None

    def _load_symbol_from_file(
        self, symbol_file: Path, lib_id: str
    ) -> Optional[SymbolDefinition]:
        """Load specific symbol from a known file."""
        try:
            # Load the library if not already loaded
            resolved_path = symbol_file.resolve()
            if resolved_path not in self._loaded_libraries:
                library_data = self._load_library(symbol_file)

                # Process symbols from the loaded library
                for symbol_name, symbol_data in library_data.get("symbols", {}).items():
                    full_lib_id = f"{symbol_file.stem}:{symbol_name}"
                    if full_lib_id not in self._symbols:
                        symbol_def = self._convert_to_symbol_definition(
                            full_lib_id, symbol_data
                        )
                        if symbol_def:
                            self._symbols[full_lib_id] = symbol_def

            # Check if symbol is now available
            if lib_id in self._symbols:
                logger.debug(f"Successfully loaded {lib_id} from {symbol_file}")
                return self._symbols[lib_id]

        except Exception as e:
            logger.warning(f"Failed to load symbol {lib_id} from {symbol_file}: {e}")

        return None

    def _extract_symbol_names_fast(self, sym_file_path: Path) -> List[str]:
        """
        Quickly extract symbol names from a .kicad_sym file without full parsing.
        """
        symbol_names = []
        try:
            with open(sym_file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Quick regex to find symbol names
            import re

            # Look for (symbol "SymbolName" patterns
            pattern = r'\(symbol\s+"([^"]+)"'
            matches = re.findall(pattern, content)

            # Filter out sub-symbols (those with underscores and numbers at the end)
            for match in matches:
                if not re.match(r".*_\d+_\d+$", match):
                    symbol_names.append(match)

        except Exception as e:
            logger.warning(f"Failed to extract symbol names from {sym_file_path}: {e}")

        return symbol_names

    def _find_library_file(self, lib_name: str) -> Optional[Path]:
        """
        Find the actual file path for a given library name.
        """
        # First, try the complete index
        self._build_complete_index()
        if lib_name in self._library_index:
            return self._library_index[lib_name]

        # Fallback to checking library paths
        for lib_path in self._library_paths:
            candidate = lib_path / f"{lib_name}.kicad_sym"
            if candidate.exists():
                return candidate

        # Check current directory
        candidate = Path.cwd() / f"{lib_name}.kicad_sym"
        if candidate.exists():
            return candidate

        return None

    def _load_library(self, lib_path: Path) -> Dict[str, Any]:
        """
        Load and cache a library file.
        """
        str_path = str(lib_path.resolve())

        # Check in-memory cache first
        if str_path in self._library_data:
            # Verify file hasn't changed
            existing_hash = self._library_data[str_path]["file_hash"]
            current_hash = self._compute_file_hash(str_path)
            if existing_hash == current_hash:
                return self._library_data[str_path]
            else:
                # File changed, re-parse
                logger.debug(f"File changed, re-parsing {str_path}")
                del self._library_data[str_path]

        # Check disk cache
        cache_file = self._cache_dir / self._cache_filename(lib_path)
        current_hash = self._compute_file_hash(str_path)

        if cache_file.exists():
            try:
                with open(cache_file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if data.get("file_hash") == current_hash:
                    logger.debug(f"Loaded library from disk cache: {cache_file}")
                    self._library_data[str_path] = data
                    return data
            except Exception as e:
                logger.warning(f"Failed to load library cache file {cache_file}: {e}")

        # Parse the actual .kicad_sym file
        logger.debug(f"Parsing .kicad_sym file: {lib_path}")
        try:
            parsed_data = parse_kicad_sym_file(str_path)
            library_data = {
                "file_hash": current_hash,
                "symbols": parsed_data.get("symbols", {}),
            }

            # Store in memory
            self._library_data[str_path] = library_data

            # Track as loaded
            self._loaded_libraries.add(lib_path.resolve())

            # Store to disk
            try:
                with open(cache_file, "w", encoding="utf-8") as f:
                    json.dump(library_data, f, indent=2)
                logger.debug(f"Wrote library cache to {cache_file}")
            except Exception as e:
                logger.warning(f"Failed writing cache file {cache_file}: {e}")

            return library_data

        except Exception as e:
            logger.error(f"Failed to parse library file {lib_path}: {e}")
            return {}

    def _compute_file_hash(self, file_path: str) -> str:
        """Compute the SHA-256 of the file."""
        hasher = hashlib.sha256()
        with open(file_path, "rb") as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        return hasher.hexdigest()

    def _cache_filename(self, lib_path: Path) -> str:
        """Return a safe cache file name."""
        path_hash = hashlib.sha1(str(lib_path.resolve()).encode("utf-8")).hexdigest()[
            :8
        ]
        stem = lib_path.stem.replace(".", "_")
        return f"{stem}_{path_hash}.json"

    def _convert_to_symbol_definition(
        self, lib_id: str, symbol_data: Dict[str, Any]
    ) -> Optional[SymbolDefinition]:
        """
        Convert parsed symbol data from kicad_symbol_parser to SymbolDefinition.
        """
        try:
            # Extract basic properties - they can be strings or dicts with enhanced info
            properties = symbol_data.get("properties", {})
            reference_prop = properties.get("Reference", "U")

            # Handle both old format (strings) and new format (dicts with "value" key)
            if isinstance(reference_prop, dict):
                reference = reference_prop.get("value", "U")
            else:
                reference = str(reference_prop)

            # Convert pins
            pins = []
            for pin_data in symbol_data.get("pins", []):
                # Handle position - it might be stored differently
                x = pin_data.get("x", 0)
                y = pin_data.get("y", 0)

                # If position is stored as a dict
                if "position" in pin_data:
                    pos = pin_data["position"]
                    if isinstance(pos, dict):
                        x = pos.get("x", 0)
                        y = pos.get("y", 0)

                # Extract orientation (angle) if present
                orientation = pin_data.get("angle", pin_data.get("orientation", 0))

                # Extract pin length
                length = pin_data.get("length", 2.54)

                pin = SchematicPin(
                    number=str(pin_data.get("number", "")),
                    name=str(pin_data.get("name", "~")),
                    type=pin_data.get(
                        "electrical_type", pin_data.get("type", "passive")
                    ),
                    position=Point(x, y),
                    orientation=orientation,
                    length=length,
                )

                pins.append(pin)

            # Get description, keywords, datasheet from direct fields or properties
            # Handle both old format (strings) and new format (dicts with "value" key)
            def extract_property_value(prop_name, fallback=""):
                # Try direct field first
                direct_value = symbol_data.get(prop_name.lower())
                if direct_value:
                    return direct_value

                # Try properties
                prop_data = properties.get(prop_name, fallback)
                if isinstance(prop_data, dict):
                    return prop_data.get("value", fallback)
                return str(prop_data) if prop_data else fallback

            description = extract_property_value(
                "Description"
            ) or extract_property_value("Value")
            keywords = extract_property_value("Keywords") or extract_property_value(
                "ki_keywords"
            )
            datasheet = extract_property_value("Datasheet")

            # Extract graphic elements from parsed data
            # The parser stores them in the "graphics" field
            raw_graphics = symbol_data.get("graphics", [])

            # Convert graphic elements to the format expected by s_expression.py
            graphic_elements = []
            for elem in raw_graphics:
                if not isinstance(elem, dict):
                    continue

                converted = {
                    "type": elem.get("shape_type", ""),  # Convert shape_type to type
                    "stroke_width": elem.get("stroke_width", 0.254),
                    "stroke_type": elem.get("stroke_type", "default"),
                    "fill_type": elem.get("fill_type", "none"),
                }

                # Convert coordinate arrays to dictionaries
                if (
                    elem.get("start")
                    and isinstance(elem["start"], list)
                    and len(elem["start"]) >= 2
                ):
                    converted["start"] = {"x": elem["start"][0], "y": elem["start"][1]}

                if (
                    elem.get("end")
                    and isinstance(elem["end"], list)
                    and len(elem["end"]) >= 2
                ):
                    converted["end"] = {"x": elem["end"][0], "y": elem["end"][1]}

                if (
                    elem.get("center")
                    and isinstance(elem["center"], list)
                    and len(elem["center"]) >= 2
                ):
                    converted["center"] = {
                        "x": elem["center"][0],
                        "y": elem["center"][1],
                    }

                if elem.get("radius"):
                    converted["radius"] = elem["radius"]

                # Convert mid point for arcs
                if (
                    elem.get("mid")
                    and isinstance(elem["mid"], list)
                    and len(elem["mid"]) >= 2
                ):
                    converted["mid"] = {"x": elem["mid"][0], "y": elem["mid"][1]}

                # Convert points for polylines
                if elem.get("points") and isinstance(elem["points"], list):
                    converted["points"] = []
                    for pt in elem["points"]:
                        if isinstance(pt, list) and len(pt) >= 2:
                            converted["points"].append({"x": pt[0], "y": pt[1]})

                graphic_elements.append(converted)

            # Create symbol definition
            symbol_def = SymbolDefinition(
                lib_id=lib_id,
                name=symbol_data.get("name", lib_id.split(":")[-1]),
                reference_prefix=reference.rstrip("?"),
                description=description,
                keywords=keywords,
                datasheet=datasheet,
                pins=pins,
                units=symbol_data.get("unit_count", 1),
                power_symbol=symbol_data.get("is_power", False),
                graphic_elements=graphic_elements,
            )

            return symbol_def

        except Exception as e:
            logger.error(f"Failed to convert symbol data for {lib_id}: {e}")
            logger.debug(f"Symbol data structure: {symbol_data}")
            return None

    def get_all_symbols(self) -> Dict[str, str]:
        """
        Get a dictionary of all available symbols: {symbol_name: lib_name}

        This method is required by the symbol search agent to enumerate all
        available symbols for fuzzy matching searches.

        Returns:
            Dictionary mapping symbol names to library names
        """
        # Build index if needed
        self._build_complete_index()

        # Return mapping of symbol names to library names
        return {
            sym_name: info["lib_name"] for sym_name, info in self._symbol_index.items()
        }

    def list_libraries(self) -> List[str]:
        """
        List all available symbol libraries.

        Returns:
            List of library names
        """
        self._build_complete_index()
        return list(self._library_index.keys())


# Global instance
_symbol_cache = None


def get_symbol_cache() -> SymbolLibraryCache:
    """Get the global symbol cache instance."""
    global _symbol_cache
    if _symbol_cache is None:
        _symbol_cache = SymbolLibraryCache()
    return _symbol_cache
