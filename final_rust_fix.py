#!/usr/bin/env python3
"""
Final fix for Rust module import issues.
Properly cleans up all the problematic files.
"""

from pathlib import Path

def fix_rust_accelerated_symbol_cache():
    """Fix the symbol cache file properly."""
    file_path = Path("src/circuit_synth/kicad/rust_accelerated_symbol_cache.py")
    
    # Read the file
    lines = file_path.read_text().splitlines()
    
    # Find the problematic section (lines 20-60 approximately)
    # Replace the duplicated except block with clean code
    new_lines = []
    skip_until = None
    
    for i, line in enumerate(lines):
        if skip_until and i < skip_until:
            continue
        skip_until = None
        
        if i == 19:  # Just before the problematic section
            new_lines.append(line)
            # Add clean import block
            new_lines.extend([
                "# Optional Rust import",
                "_RUST_SYMBOL_CACHE_AVAILABLE = False",
                "_RustSymbolLibCache = None",
                "",
                "try:",
                "    import rust_symbol_cache",
                "    if hasattr(rust_symbol_cache, 'RustSymbolLibCache'):",
                "        _RustSymbolLibCache = rust_symbol_cache.RustSymbolLibCache",
                "        _RUST_SYMBOL_CACHE_AVAILABLE = True",
                "        logger.debug(\"🦀 Rust symbol cache available and functional\")",
                "    else:",
                "        logger.debug(\"⚠️ Rust module found but missing RustSymbolLibCache\")",
                "except ImportError:",
                "    logger.debug(\"🐍 Using Python symbol cache (Rust not available)\")",
                "except Exception as e:",
                "    logger.warning(f\"⚠️ Error loading Rust symbol cache: {e}\")",
                "",
            ])
            # Skip to line 65 or so
            skip_until = 65
        elif not (20 <= i < 65):  # Outside the problematic range
            new_lines.append(line)
    
    # Write back
    file_path.write_text("\n".join(new_lines))
    print(f"✅ Fixed {file_path}")

def fix_placement():
    """Fix placement.py properly."""
    file_path = Path("src/circuit_synth/kicad/schematic/placement.py")
    
    content = file_path.read_text()
    
    # Remove all the duplicated import blocks
    lines = content.splitlines()
    new_lines = []
    seen_rust_import = False
    
    for line in lines:
        if "# Optional Rust placement module" in line:
            if not seen_rust_import:
                seen_rust_import = True
                new_lines.append(line)
            # Skip this duplicate
        elif "RUST_PLACEMENT_AVAILABLE = " in line:
            # Skip duplicates
            pass
        else:
            new_lines.append(line)
    
    file_path.write_text("\n".join(new_lines))
    print(f"✅ Fixed {file_path}")

if __name__ == "__main__":
    print("🔧 Final cleanup of Rust import issues...")
    fix_rust_accelerated_symbol_cache()
    fix_placement()
    print("✅ All fixed!")