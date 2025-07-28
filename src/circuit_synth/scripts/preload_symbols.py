#!/usr/bin/env python3
"""
Script to preload KiCad symbol libraries into the cache for faster access.
"""
import argparse
import os
import re
from pathlib import Path

import sexpdata

# Import for tab completion
try:
    import argcomplete
except ImportError:
    argcomplete = None


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


from circuit_synth.kicad.symbol_lib_parser_manager import SharedParserManager


def extract_symbol_names(sym_file_path: Path):
    """
    Parse a .kicad_sym file (S-expression) to find all top-level symbol names.
    This function uses the 'sexpdata' library to load the file contents
    and search for (symbol "SymbolName" ...).
    """
    with sym_file_path.open("r", encoding="utf-8") as f:
        data = f.read()

    try:
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


def preload_all_symbols(library_root: Path, verbose: bool = False):
    """
    Recursively find all *.kicad_sym files in `library_root`,
    parse them for symbol names, and cache each symbol by calling parser.parse_symbol().
    """
    print(f"Preloading symbols from library root: {library_root}")
    parser = SharedParserManager.get_parser()

    total_symbols = 0
    cached_symbols = 0
    failed_symbols = 0

    # If you have multiple library paths, you could do SharedParserManager.add_symbol_paths([...])
    # or rely on KICAD_SYMBOL_DIR. For now, assume library_root is already in your KiCad paths.

    # Example: gather all .kicad_sym files under library_root:
    for sym_file in library_root.rglob("*.kicad_sym"):
        lib_name = sym_file.stem  # e.g. "Device", "Diode", or "SomeLib"
        # Convert file name to a "library name" – if you have subfolders, you might do something else

        symbol_list = extract_symbol_names(sym_file)
        if not symbol_list:
            continue

        print(f"  Found {len(symbol_list)} symbols in {sym_file.name} => {lib_name}")
        total_symbols += len(symbol_list)

        for sym_name in symbol_list:
            full_symbol_id = f"{lib_name}:{sym_name}"
            try:
                # Force parse to store in disk cache
                parser.parse_symbol(full_symbol_id)
                cached_symbols += 1
                if verbose:
                    print(f"    Cached symbol: {full_symbol_id}")
            except Exception as e:
                failed_symbols += 1
                if verbose:
                    print(f"    WARNING: Could not parse {full_symbol_id}: {e}")

    # Done – all discovered symbols are now in the disk cache
    print(
        f"Preloading complete! Cached {cached_symbols}/{total_symbols} symbols ({failed_symbols} failed)"
    )


def main():
    """Main function to preload KiCad symbols."""
    parser = argparse.ArgumentParser(
        description="Preload KiCad symbol libraries into the cache for faster access."
    )
    parser.add_argument(
        "--lib-path",
        type=Path,
        default=os.environ.get("KICAD_SYMBOL_DIR", _get_default_kicad_symbol_path()),
        help="Path to KiCad symbol libraries (default: KICAD_SYMBOL_DIR environment variable or KiCad default location)",
    )
    parser.add_argument(
        "--verbose",
        "-v",
        action="store_true",
        help="Enable verbose output showing each symbol being cached",
    )

    # Enable tab completion if argcomplete is available
    if argcomplete:
        argcomplete.autocomplete(parser)

    args = parser.parse_args()

    # Preload symbols from the specified path
    lib_root = Path(args.lib_path)
    if not lib_root.exists():
        print(f"Error: Symbol library path does not exist: {lib_root}")
        return 1

    print(f"Using symbol library path: {lib_root}")
    preload_all_symbols(lib_root, verbose=args.verbose)
    return 0


if __name__ == "__main__":
    import sys

    sys.exit(main())
