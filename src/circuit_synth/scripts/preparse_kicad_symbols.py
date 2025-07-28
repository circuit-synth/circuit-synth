#!/usr/bin/env python3


def _get_default_kicad_symbol_path():
    """Get the default KiCad symbol path for the current platform."""
    import platform
    from pathlib import Path

    if platform.system() == "Darwin":  # macOS
        possible_paths = [
            "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/",
            "/Applications/KiCad9/KiCad.app/Contents/SharedSupport/symbols/",
        ]
    elif platform.system() == "Linux":
        possible_paths = [
            "/usr/share/kicad/symbols/",
            "/usr/local/share/kicad/symbols/",
            "/snap/kicad/current/usr/share/kicad/symbols/",
        ]
    elif platform.system() == "Windows":
        possible_paths = [
            "C:\\Program Files\\KiCad\\share\\kicad\\symbols\\",
            "C:\\Program Files (x86)\\KiCad\\share\\kicad\\symbols\\",
        ]
    else:
        possible_paths = ["/usr/share/kicad/symbols/"]

    # Find the first existing path
    for path in possible_paths:
        if Path(path).exists():
            return path

    # Fallback to Linux default
    return "/usr/share/kicad/symbols/"


#!/usr/bin/env python3
"""
Enhanced KiCad symbol pre-parsing script with cache management functionality.

This script provides comprehensive symbol library management including:
- Pre-parsing all .kicad_sym files into SymbolLibCache
- Cache status and information commands
- Cache invalidation and cleanup
- Progress feedback and error handling
- Bulk symbol library processing
"""
import argparse
import os
import sys
import time
from pathlib import Path
from typing import Dict, List, Set

import sexpdata

# Import for tab completion
try:
    import argcomplete
except ImportError:
    argcomplete = None

from circuit_synth.kicad.kicad_symbol_cache import SymbolLibCache
from circuit_synth.kicad.symbol_lib_parser_manager import SharedParserManager


def extract_symbol_names(sym_file_path: Path) -> List[str]:
    """
    Parse a .kicad_sym file (S-expression) to find all top-level symbol names.
    This function uses the 'sexpdata' library to load the file contents
    and search for (symbol "SymbolName" ...).
    """
    try:
        with sym_file_path.open("r", encoding="utf-8") as f:
            data = f.read()

        s_expr = sexpdata.loads(data)
    except Exception as e:
        print(f"WARNING: Unable to parse {sym_file_path} with sexpdata: {e}")
        return []

    # Typically, the file structure is like: (kicad_symbol (symbol "Name" (...)) (symbol "Name2" (...)) ...)
    # So s_expr[1:] often contain each (symbol ...). We'll gather their names.
    symbol_names = []
    # s_expr should be a list: [Symbol('kicad_symbol'), (symbol ...), (symbol ...), ...]
    for expr in s_expr[1:]:
        if isinstance(expr, list) and len(expr) >= 2:
            # The first element might be Symbol('symbol'), then the second is the symbol name
            try:
                if expr[0].value().lower() == "symbol":
                    # e.g. (symbol "Name")
                    name_val = expr[1]
                    if isinstance(name_val, str):
                        symbol_names.append(name_val)
            except (AttributeError, IndexError):
                pass

    return symbol_names


def find_kicad_symbol_files(library_root: Path) -> List[Path]:
    """Find all .kicad_sym files recursively in the given directory."""
    if not library_root.exists():
        raise FileNotFoundError(f"Library path does not exist: {library_root}")

    if not library_root.is_dir():
        raise NotADirectoryError(f"Library path is not a directory: {library_root}")

    symbol_files = list(library_root.rglob("*.kicad_sym"))
    return symbol_files


def build_symbol_index(verbose: bool = False, progress: bool = True) -> Dict[str, any]:
    """
    Fast symbol index building - scans all .kicad_sym files and builds a complete
    symbol name -> library mapping without parsing full symbol data.

    Uses KICAD_SYMBOL_DIR environment variable to find symbol libraries.
    This is much faster than the old preparse_symbols approach.
    """
    start_time = time.time()

    if progress:
        print(f"🔍 Building symbol index from KICAD_SYMBOL_DIR")

    # Use the enhanced SymbolLibCache to build the index
    from circuit_synth.kicad.kicad_symbol_cache import SymbolLibCache

    # Trigger index building
    all_libraries = SymbolLibCache.get_all_libraries()
    all_symbols = SymbolLibCache.get_all_symbols()

    processing_time = time.time() - start_time

    # Build detailed statistics
    libraries = {}
    for lib_name, lib_path in all_libraries.items():
        # Count symbols in this library
        lib_symbols = [sym for sym, lib in all_symbols.items() if lib == lib_name]
        libraries[lib_name] = {
            "file_path": str(lib_path),
            "total_symbols": len(lib_symbols),
            "indexed_symbols": len(lib_symbols),
            "symbols": [
                {"name": sym, "status": "indexed"} for sym in lib_symbols[:10]
            ],  # Show first 10
        }

        if verbose and lib_symbols:
            print(f"  📚 {lib_name}: {len(lib_symbols)} symbols")
            if verbose and len(lib_symbols) <= 20:  # Show all if small library
                for sym in lib_symbols:
                    print(f"    - {sym}")
            elif verbose:
                print(
                    f"    - {', '.join(lib_symbols[:5])}... and {len(lib_symbols)-5} more"
                )

    # Summary
    if progress:
        print(f"\n✅ Symbol index built successfully!")
        print(f"  📁 Libraries indexed: {len(all_libraries)}")
        print(f"  🔍 Symbols indexed: {len(all_symbols)}")
        print(f"  ⏱️  Processing time: {processing_time:.2f} seconds")
        print(f"  💾 Cache directory: {SymbolLibCache.CACHE_DIR}")

        # Show some example symbols
        if all_symbols:
            common_symbols = ["C", "R", "L", "D", "LED", "Q"]
            found_examples = []
            for sym in common_symbols:
                if sym in all_symbols:
                    found_examples.append(f"{sym} ({all_symbols[sym]})")
            if found_examples:
                print(f"  📋 Example symbols: {', '.join(found_examples[:5])}")

    return {
        "total_files": len(all_libraries),
        "total_symbols": len(all_symbols),
        "indexed_symbols": len(all_symbols),
        "failed_symbols": 0,
        "processing_time": processing_time,
        "libraries": libraries,
        "index_built": True,
    }


def preparse_symbols(
    library_root: Path = None, verbose: bool = False, progress: bool = True
) -> Dict[str, any]:
    """
    Legacy function - now redirects to fast index building.
    For backward compatibility, but much faster implementation.
    The library_root parameter is ignored - uses KICAD_SYMBOL_DIR instead.
    """
    if progress:
        print("⚡ Using fast symbol index building (lazy loading approach)")

    return build_symbol_index(verbose, progress)


def preparse_specific_libraries(
    library_names: List[str], verbose: bool = False, progress: bool = True
) -> Dict[str, any]:
    """
    Pre-parse specific libraries completely (full symbol data parsing).
    This is useful for libraries you know you'll use heavily.
    """
    start_time = time.time()

    if progress:
        print(f"🔧 Pre-parsing {len(library_names)} specific libraries...")

    from circuit_synth.kicad.kicad_symbol_cache import SymbolLibCache

    parser = SharedParserManager.get_parser()

    total_symbols = 0
    cached_symbols = 0
    failed_symbols = 0
    libraries = {}

    for lib_name in library_names:
        if progress:
            print(f"  📚 Processing library: {lib_name}")

        try:
            # Get all symbols in this library
            all_symbols = SymbolLibCache.get_all_symbols()
            lib_symbols = [sym for sym, lib in all_symbols.items() if lib == lib_name]

            if not lib_symbols:
                if progress:
                    print(f"    ⚠️  No symbols found in library: {lib_name}")
                continue

            lib_stats = {
                "file_path": str(SymbolLibCache._library_index.get(lib_name, "")),
                "total_symbols": len(lib_symbols),
                "cached_symbols": 0,
                "failed_symbols": 0,
                "symbols": [],
            }

            total_symbols += len(lib_symbols)

            if progress:
                print(f"    🔍 Found {len(lib_symbols)} symbols, parsing...")

            for sym_name in lib_symbols:
                symbol_id = f"{lib_name}:{sym_name}"
                try:
                    # Parse the symbol to cache it
                    parser.parse_symbol(symbol_id)
                    cached_symbols += 1
                    lib_stats["cached_symbols"] += 1
                    lib_stats["symbols"].append({"name": sym_name, "status": "cached"})

                    if verbose:
                        print(f"      ✓ {sym_name}")

                except Exception as e:
                    failed_symbols += 1
                    lib_stats["failed_symbols"] += 1
                    lib_stats["symbols"].append(
                        {"name": sym_name, "status": "failed", "error": str(e)}
                    )

                    if verbose:
                        print(f"      ✗ {sym_name}: {e}")

            libraries[lib_name] = lib_stats

            if progress:
                success_rate = (
                    lib_stats["cached_symbols"] / lib_stats["total_symbols"]
                ) * 100
                print(
                    f"    ✅ {lib_stats['cached_symbols']}/{lib_stats['total_symbols']} symbols cached ({success_rate:.1f}%)"
                )

        except Exception as e:
            if progress:
                print(f"    ❌ Failed to process library {lib_name}: {e}")
            failed_symbols += 1

    processing_time = time.time() - start_time

    if progress:
        print(f"\n🎉 Library pre-parsing complete!")
        print(f"  📚 Libraries processed: {len(library_names)}")
        print(f"  🔍 Total symbols: {total_symbols}")
        print(f"  ✅ Successfully cached: {cached_symbols}")
        print(f"  ❌ Failed: {failed_symbols}")
        print(f"  ⏱️  Processing time: {processing_time:.2f} seconds")
        if total_symbols > 0:
            success_rate = (cached_symbols / total_symbols) * 100
            print(f"  📊 Success rate: {success_rate:.1f}%")

    return {
        "total_files": len(library_names),
        "total_symbols": total_symbols,
        "cached_symbols": cached_symbols,
        "failed_symbols": failed_symbols,
        "processing_time": processing_time,
        "libraries": libraries,
        "preparse_mode": "specific_libraries",
    }


def show_cache_status():
    """Display information about the current symbol cache."""
    try:
        cache = SymbolLibCache()
        print("Symbol Cache Status:")
        print(
            f"  Cache directory: {cache.cache_dir if hasattr(cache, 'cache_dir') else 'Unknown'}"
        )

        # Try to get cache statistics if available
        if hasattr(cache, "get_cache_stats"):
            stats = cache.get_cache_stats()
            print(f"  Cached symbols: {stats.get('total_symbols', 'Unknown')}")
            print(f"  Cache size: {stats.get('cache_size_mb', 'Unknown')} MB")
        else:
            print("  Cache statistics not available")

    except Exception as e:
        print(f"Error accessing cache: {e}")


def clear_cache():
    """Clear the symbol cache."""
    try:
        cache = SymbolLibCache()
        if hasattr(cache, "clear_cache"):
            cache.clear_cache()
            print("Symbol cache cleared successfully")
        else:
            print("Cache clearing not supported by current implementation")
    except Exception as e:
        print(f"Error clearing cache: {e}")


def main():
    """Main function for KiCad symbol pre-parsing and cache management."""
    parser = argparse.ArgumentParser(
        description="Enhanced KiCad symbol pre-parsing and cache management tool with lazy loading",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Build fast symbol index (recommended - very fast)
  preparse_kicad_symbols
  
  # Build index from custom location
  preparse_kicad_symbols --lib-path /path/to/symbols
  
  # Pre-parse specific libraries completely (slower but caches full data)
  preparse_kicad_symbols --preparse-libraries Device,MCU_ST_STM32
  
  # Show cache status
  preparse_kicad_symbols --status
  
  # Clear cache
  preparse_kicad_symbols --clear-cache
        """,
    )

    # Main operation arguments
    parser.add_argument(
        "--lib-path",
        type=Path,
        default=os.environ.get("KICAD_SYMBOL_DIR", _get_default_kicad_symbol_path()),
        help="Path to KiCad symbol libraries (default: KICAD_SYMBOL_DIR environment variable or KiCad default location)",
    )

    # Operation modes
    parser.add_argument(
        "--build-index",
        action="store_true",
        default=True,
        help="Build fast symbol index only (default, very fast)",
    )

    parser.add_argument(
        "--preparse-libraries",
        type=str,
        help="Comma-separated list of specific libraries to fully pre-parse (e.g., 'Device,MCU_ST_STM32')",
    )

    parser.add_argument(
        "--legacy-preparse",
        action="store_true",
        help="Use legacy full pre-parsing (very slow, not recommended)",
    )

    # Output control
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output showing detailed processing information",
    )

    parser.add_argument(
        "--quiet",
        "-q",
        action="store_true",
        help="Suppress progress output (only show errors and final summary)",
    )

    # Cache management commands
    parser.add_argument(
        "--status", action="store_true", help="Show cache status and exit"
    )

    parser.add_argument(
        "--clear-cache", action="store_true", help="Clear the symbol cache and exit"
    )

    # Enable tab completion if argcomplete is available
    if argcomplete:
        argcomplete.autocomplete(parser)

    args = parser.parse_args()

    # Handle cache management commands
    if args.status:
        show_cache_status()
        return 0

    if args.clear_cache:
        clear_cache()
        return 0

    # Validate library paths (can be multiple directories separated by colons)
    def validate_symbol_paths(path_str: str) -> list[Path]:
        """Validate and parse symbol library paths."""
        import os

        separator = ";" if os.name == "nt" else ":"
        paths = [p.strip() for p in path_str.split(separator) if p.strip()]
        valid_paths = []

        for path_str in paths:
            path_obj = Path(path_str)
            if path_obj.exists() and path_obj.is_dir():
                valid_paths.append(path_obj)
            else:
                print(f"⚠️  Warning: Symbol library path does not exist: {path_obj}")

        return valid_paths

    valid_paths = validate_symbol_paths(str(args.lib_path))
    if not valid_paths:
        print(f"❌ Error: No valid symbol library paths found in: {args.lib_path}")
        return 1

    try:
        progress = not args.quiet
        if progress:
            print(f"📁 Using symbol library paths:")
            for path in valid_paths:
                print(f"   - {path}")

        # Determine operation mode
        if args.preparse_libraries:
            # Pre-parse specific libraries
            library_names = [lib.strip() for lib in args.preparse_libraries.split(",")]
            if progress:
                print(f"🎯 Pre-parsing specific libraries: {', '.join(library_names)}")
            stats = preparse_specific_libraries(
                library_names, verbose=args.verbose, progress=progress
            )

        elif args.legacy_preparse:
            # Legacy full pre-parsing (not recommended)
            if progress:
                print("⚠️  Using legacy full pre-parsing (this will be very slow)")
                print(
                    "💡 Consider using --preparse-libraries for specific libraries instead"
                )
            # Use the old implementation for backward compatibility
            stats = preparse_symbols_legacy(
                lib_root, verbose=args.verbose, progress=progress
            )

        else:
            # Default: Fast index building
            if progress:
                print("⚡ Building fast symbol index (lazy loading approach)")
            stats = build_symbol_index(verbose=args.verbose, progress=progress)

        # Return appropriate exit code
        failed_symbols = stats.get("failed_symbols", 0)
        total_symbols = stats.get("total_symbols", 0)

        if failed_symbols > 0 and total_symbols > 0:
            if (
                stats.get("cached_symbols", 0) == 0
                and stats.get("indexed_symbols", 0) == 0
            ):
                return 1  # Complete failure
            else:
                return 2  # Partial failure
        else:
            return 0  # Success

    except KeyboardInterrupt:
        print("\n⏹️  Operation cancelled by user")
        return 130
    except Exception as e:
        print(f"❌ Error: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


def preparse_symbols_legacy(
    library_root: Path, verbose: bool = False, progress: bool = True
) -> Dict[str, any]:
    """
    Legacy implementation that parses every symbol individually.
    Kept for backward compatibility but not recommended due to poor performance.
    """
    start_time = time.time()

    if progress:
        print(f"⚠️  WARNING: Legacy mode will parse {44000}+ symbols individually")
        print(
            f"   This may take several hours. Consider using fast index building instead."
        )
        print(f"🔍 Scanning for .kicad_sym files in: {library_root}")

    # Find all symbol files
    symbol_files = find_kicad_symbol_files(library_root)

    if not symbol_files:
        print(f"No .kicad_sym files found in {library_root}")
        return {
            "total_files": 0,
            "total_symbols": 0,
            "cached_symbols": 0,
            "failed_symbols": 0,
            "processing_time": 0.0,
            "libraries": {},
        }

    if progress:
        print(f"Found {len(symbol_files)} symbol library files")

    parser = SharedParserManager.get_parser()

    total_symbols = 0
    cached_symbols = 0
    failed_symbols = 0
    libraries = {}

    for i, sym_file in enumerate(symbol_files, 1):
        lib_name = sym_file.stem

        if progress:
            print(f"[{i}/{len(symbol_files)}] Processing {sym_file.name}...")

        symbol_list = extract_symbol_names(sym_file)
        if not symbol_list:
            if verbose:
                print(f"  No symbols found in {sym_file.name}")
            continue

        lib_stats = {
            "file_path": str(sym_file),
            "total_symbols": len(symbol_list),
            "cached_symbols": 0,
            "failed_symbols": 0,
            "symbols": [],
        }

        if verbose or progress:
            print(f"  Found {len(symbol_list)} symbols in {sym_file.name}")

        total_symbols += len(symbol_list)

        for sym_name in symbol_list:
            full_symbol_id = f"{lib_name}:{sym_name}"
            try:
                parser.parse_symbol(full_symbol_id)
                cached_symbols += 1
                lib_stats["cached_symbols"] += 1
                lib_stats["symbols"].append({"name": sym_name, "status": "cached"})

                if verbose:
                    print(f"    ✓ Cached: {full_symbol_id}")
            except Exception as e:
                failed_symbols += 1
                lib_stats["failed_symbols"] += 1
                lib_stats["symbols"].append(
                    {"name": sym_name, "status": "failed", "error": str(e)}
                )

                if verbose:
                    print(f"    ✗ Failed: {full_symbol_id} - {e}")

        libraries[lib_name] = lib_stats

    processing_time = time.time() - start_time

    if progress:
        print(f"\nLegacy pre-parsing complete!")
        print(f"  Files processed: {len(symbol_files)}")
        print(f"  Total symbols: {total_symbols}")
        print(f"  Successfully cached: {cached_symbols}")
        print(f"  Failed: {failed_symbols}")
        print(f"  Processing time: {processing_time:.2f} seconds")
        if total_symbols > 0:
            success_rate = (cached_symbols / total_symbols) * 100
            print(f"  Success rate: {success_rate:.1f}%")

    return {
        "total_files": len(symbol_files),
        "total_symbols": total_symbols,
        "cached_symbols": cached_symbols,
        "failed_symbols": failed_symbols,
        "processing_time": processing_time,
        "libraries": libraries,
    }


if __name__ == "__main__":
    sys.exit(main())
