"""
kicad_symbol_cache.py

Provides a caching mechanism for KiCad symbol libraries.
"""

import hashlib
import json
import logging
import os
import re
import time
from pathlib import Path
from typing import Any, Dict, List, Optional

# Import the parser
from .kicad_symbol_parser import parse_kicad_sym_file

# Python implementation for symbol cache


# Add performance timing
try:
    from ..core.performance_profiler import quick_time
except ImportError:
    # Fallback if profiler not available
    def quick_time(name):
        def decorator(func):
            return func

        return decorator


logger = logging.getLogger(__name__)


class SymbolLibCache:
    """
    Python fallback implementation of SymbolLibCache.
    Restored from the original working implementation.
    """

    _instance = None
    _initialized = False

    # Class-level data structures for singleton pattern
    _library_data: Dict[str, Dict[str, Any]] = {}
    _symbol_index: Dict[str, Dict[str, Any]] = {}
    _library_index: Dict[str, Path] = {}
    _index_built: bool = False
    _library_categories: Dict[str, str] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            logger.debug("Initializing Python fallback SymbolLibCache")
            self._cache_dir = self._get_cache_dir()
            self._cache_dir.mkdir(parents=True, exist_ok=True)
            self.__class__._initialized = True

    @classmethod
    def _get_cache_dir(cls) -> Path:
        """Get the cache directory for symbol data."""
        cache_dir = os.environ.get("CIRCUIT_SYNTH_CACHE_DIR")
        if cache_dir:
            cache_path = Path(cache_dir)
        else:
            cache_path = Path.home() / ".cache" / "circuit_synth" / "symbols"

        # Ensure the directory exists
        cache_path.mkdir(parents=True, exist_ok=True)
        return cache_path

    @classmethod
    @quick_time("Get Symbol Data")
    def get_symbol_data(cls, symbol_id: str) -> Dict[str, Any]:
        """Get symbol data by symbol ID (LibraryName:SymbolName)."""
        instance = cls()

        # Validate format
        if ":" not in symbol_id:
            raise ValueError(
                f"Invalid symbol_id format; expected 'LibName:SymbolName', got '{symbol_id}'"
            )

        try:
            lib_name, sym_name = symbol_id.split(":", 1)
        except ValueError:
            raise ValueError(
                f"Invalid symbol_id format; expected 'LibName:SymbolName', got '{symbol_id}'"
            )

        # Try lazy symbol search first (much faster)
        try:
            return instance._lazy_symbol_search(symbol_id)
        except Exception as e:
            logger.debug(f"Lazy search failed for {symbol_id}: {e}")

        # Build index if needed (fallback)
        instance._build_complete_index()

        # Find the library file
        lib_path = instance._find_library_file(lib_name)
        if not lib_path:
            raise FileNotFoundError(f"Library '{lib_name}' not found")

        # Load the library
        library_data = instance._load_library(lib_path)
        if not library_data or "symbols" not in library_data:
            raise FileNotFoundError(f"Failed to load library '{lib_name}'")

        # Find the symbol in the library
        if sym_name not in library_data["symbols"]:
            raise FileNotFoundError(
                f"Symbol '{sym_name}' not found in library '{lib_name}'"
            )

        return library_data["symbols"][sym_name]

    @classmethod
    def get_symbol_data_by_name(cls, symbol_name: str) -> Dict[str, Any]:
        """Get symbol data by name only (searches all libraries)."""
        instance = cls()

        # Build index if needed
        instance._build_complete_index()

        # Check if symbol exists in index
        if symbol_name not in cls._symbol_index:
            raise FileNotFoundError(f"Symbol '{symbol_name}' not found in any library")

        # Get the library containing this symbol
        lib_name = cls._symbol_index[symbol_name]["lib_name"]
        symbol_id = f"{lib_name}:{symbol_name}"

        # Use the regular get_symbol_data method
        return cls.get_symbol_data(symbol_id)

    @classmethod
    def find_symbol_library(cls, symbol_name: str) -> Optional[str]:
        """Find which library contains the given symbol name."""
        instance = cls()
        instance._build_complete_index()

        if symbol_name in cls._symbol_index:
            return cls._symbol_index[symbol_name]["lib_name"]
        return None

    @classmethod
    def get_all_libraries(cls) -> Dict[str, str]:
        """Get a dictionary of all available libraries."""
        instance = cls()
        instance._build_complete_index()
        return {
            lib_name: str(lib_path) for lib_name, lib_path in cls._library_index.items()
        }

    @classmethod
    def get_all_symbols(cls) -> Dict[str, str]:
        """Get a dictionary of all available symbols."""
        instance = cls()
        instance._build_complete_index()
        return {
            sym_name: info["lib_name"] for sym_name, info in cls._symbol_index.items()
        }

    def _build_complete_index(self) -> None:
        """
        Build a complete index of ALL symbols from ALL .kicad_sym files in KICAD_SYMBOL_DIR.
        This enables automatic discovery of any symbol without knowing the library name.
        """
        if self.__class__._index_built:
            return

        logger.debug("Building complete symbol library index...")

        # Parse KICAD_SYMBOL_DIR - can contain multiple paths separated by colons
        kicad_dirs = self.__class__._parse_kicad_symbol_dirs()

        if not kicad_dirs:
            logger.error("No valid KiCad symbol directories found")
            self.__class__._index_built = (
                True  # Mark as built to avoid repeated attempts
            )
            return

        logger.debug(f"Scanning symbol libraries in {len(kicad_dirs)} directories:")
        for dir_path in kicad_dirs:
            logger.debug(f"  - {dir_path}")

        # Build library index
        self.__class__._library_index.clear()
        self.__class__._symbol_index.clear()

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

                    self.__class__._library_index[lib_name] = sym_file

                    # Parse the file to get symbol names (lightweight parsing)
                    try:
                        symbol_names = self._extract_symbol_names_fast(sym_file)
                        for symbol_name in symbol_names:
                            # Store in symbol index for fast lookup
                            # If symbol exists in multiple libraries, keep the first one found
                            if symbol_name not in self.__class__._symbol_index:
                                self.__class__._symbol_index[symbol_name] = {
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

        self.__class__._index_built = True
        logger.debug(
            f"Symbol index built: {len(self.__class__._library_index)} libraries, {len(self.__class__._symbol_index)} symbols"
        )

    @classmethod
    def _find_kicad_symbol_dirs(cls) -> List[Path]:
        """
        Find KiCad symbol directories. Alias for _parse_kicad_symbol_dirs.
        """
        return cls._parse_kicad_symbol_dirs()

    @classmethod
    def _parse_kicad_symbol_dirs(cls) -> List[Path]:
        """
        Parse KICAD_SYMBOL_DIR environment variable which can contain multiple paths
        separated by colons (like PATH variable). Returns list of valid directory paths.
        If no environment variable is set, try common KiCad installation paths.
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

                path_obj = Path(
                    dir_path
                ).resolve()  # Resolve relative paths to absolute
                if path_obj.exists() and path_obj.is_dir():
                    valid_dirs.append(path_obj)
                    logger.debug(f"Added valid symbol directory: {path_obj}")
                else:
                    logger.warning(f"Skipping invalid symbol directory: {path_obj}")
        else:
            # Try common KiCad installation paths as fallback
            common_paths = [
                "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols",  # macOS
                "/usr/share/kicad/symbols",  # Linux (KiCad 6+)
                "/usr/share/kicad/library",  # Linux (KiCad 5)
                "/usr/local/share/kicad/symbols",  # Linux alternative
                "/usr/local/share/kicad/library",  # Linux alternative (KiCad 5)
                "C:\\Program Files\\KiCad\\share\\kicad\\symbols",  # Windows
                "C:\\Program Files (x86)\\KiCad\\share\\kicad\\symbols",  # Windows 32-bit
            ]

            for path_str in common_paths:
                path_obj = Path(path_str)
                if path_obj.exists() and path_obj.is_dir():
                    valid_dirs.append(path_obj)
                    logger.info(f"Auto-detected KiCad symbol directory: {path_obj}")
                    break  # Use the first valid path found

        # If no valid directories from environment, try defaults
        if not valid_dirs:
            logger.warning("KICAD_SYMBOL_DIR not set or invalid, trying default paths")
            default_dirs = [
                "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/",  # macOS
                "/usr/share/kicad/symbols/",  # Linux (KiCad 6+)
                "/usr/share/kicad/library/",  # Linux (KiCad 5)
                "/usr/local/share/kicad/symbols/",  # Linux alternative
                "/usr/local/share/kicad/library/",  # Linux alternative (KiCad 5)
                "C:\\Program Files\\KiCad\\share\\kicad\\symbols\\",  # Windows
            ]

            for dir_path in default_dirs:
                path_obj = Path(dir_path).resolve()
                if path_obj.exists() and path_obj.is_dir():
                    valid_dirs.append(path_obj)
                    logger.info(f"Using default symbol directory: {path_obj}")

        return valid_dirs

    def _extract_symbol_names_fast(self, sym_file_path: Path) -> List[str]:
        """
        Quickly extract symbol names from a .kicad_sym file without full parsing.
        """
        symbol_names = []
        try:
            with open(sym_file_path, "r", encoding="utf-8") as f:
                content = f.read()

            # Quick regex to find symbol names
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
        if lib_name in self.__class__._library_index:
            return self.__class__._library_index[lib_name]

        # If not found in library index, check if we have it in symbol index
        # This handles cases where tests manually set up the symbol index
        for symbol_info in self.__class__._symbol_index.values():
            if symbol_info["lib_name"] == lib_name:
                lib_path = symbol_info["lib_path"]
                # Add to library index for future lookups
                self.__class__._library_index[lib_name] = lib_path
                return lib_path

        # Check current directory
        candidate = Path.cwd() / f"{lib_name}.kicad_sym"
        if candidate.exists():
            return candidate

        return None

    @quick_time("Load Symbol Library")
    def _load_library(self, lib_path: Path) -> Dict[str, Any]:
        """
        Load and cache a library file.
        """
        str_path = str(lib_path.resolve())

        # Check in-memory cache first
        if str_path in self.__class__._library_data:
            # Verify file hasn't changed
            existing_hash = self.__class__._library_data[str_path]["file_hash"]
            current_hash = self._compute_file_hash(str_path)
            if existing_hash == current_hash:
                return self.__class__._library_data[str_path]
            else:
                # File changed, re-parse
                logger.debug(f"File changed, re-parsing {str_path}")
                del self.__class__._library_data[str_path]

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

    @classmethod
    def _is_cache_expired(cls, cache_time: float, ttl_hours: int) -> bool:
        """Check if cache is expired based on TTL."""
        current_time = time.time()
        return (current_time - cache_time) > (ttl_hours * 3600)

    def _lazy_symbol_search(self, symbol_id: str) -> Dict[str, Any]:
        """
        Fast lazy search for symbols without building complete index.
        Uses multiple strategies in order of speed.
        """
        try:
            lib_name, sym_name = symbol_id.split(":", 1)
        except ValueError:
            raise ValueError(f"Invalid symbol_id format: {symbol_id}")

        # Strategy 1: File-based discovery (fastest - < 0.01s)
        symbol_file = self._find_symbol_file_by_name(lib_name)
        if symbol_file and symbol_file.exists():
            logger.debug(f"Found symbol file by name: {symbol_file}")
            return self._load_symbol_from_file_direct(symbol_file, symbol_id)

        # Strategy 2: Ripgrep search (fast - < 0.1s)
        symbol_file = self._ripgrep_symbol_search(lib_name, sym_name)
        if symbol_file:
            logger.debug(f"Found symbol via ripgrep: {symbol_file}")
            return self._load_symbol_from_file_direct(symbol_file, symbol_id)

        # Strategy 3: Python grep fallback (medium - < 1s)
        symbol_file = self._python_grep_search(lib_name, sym_name)
        if symbol_file:
            logger.debug(f"Found symbol via Python grep: {symbol_file}")
            return self._load_symbol_from_file_direct(symbol_file, symbol_id)

        raise FileNotFoundError(f"Symbol {symbol_id} not found via lazy search")

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

    def _load_symbol_from_file_direct(
        self, symbol_file: Path, symbol_id: str
    ) -> Dict[str, Any]:
        """Load specific symbol from a known file and return data directly."""
        try:
            lib_name, sym_name = symbol_id.split(":", 1)

            # Load the library
            library_data = self._load_library(symbol_file)
            if not library_data or "symbols" not in library_data:
                raise ValueError(f"No symbols found in {symbol_file}")

            # Find the specific symbol
            symbol_data = library_data["symbols"].get(sym_name)
            if not symbol_data:
                raise KeyError(f"Symbol '{sym_name}' not found in library '{lib_name}'")

            logger.debug(f"Successfully loaded {symbol_id} from {symbol_file}")
            return symbol_data

        except Exception as e:
            logger.warning(f"Failed to load symbol {symbol_id} from {symbol_file}: {e}")
            raise


# Module-level flag for checking availability (already defined above)
