#!/usr/bin/env python3
"""
Emergency fix for Rust module packaging issues.
This makes all Rust modules optional with Python fallbacks.
"""

import os
from pathlib import Path

def fix_kicad_formatter():
    """Fix kicad_formatter.py to make Rust completely optional."""
    file_path = Path("src/circuit_synth/kicad/sch_gen/kicad_formatter.py")
    
    # Read the file
    lines = file_path.read_text().splitlines()
    
    # Find the try block start
    try_start = None
    for i, line in enumerate(lines):
        if "import_start = time.perf_counter()" in line:
            try_start = i - 1  # Go back to the try: line
            break
    
    if try_start is None:
        print(f"❌ Could not find import block in {file_path}")
        return False
    
    # Find the end of the exception block
    except_end = None
    for i in range(try_start, len(lines)):
        if lines[i].strip() == "raise" and i > try_start + 10:
            except_end = i
            break
    
    if except_end is None:
        print(f"❌ Could not find end of import block in {file_path}")
        return False
    
    # Replace the entire block
    new_block = [
        "# Make Rust module optional - use Python fallback if not available",
        "_rust_sexp_module = None",
        "try:",
        "    import rust_kicad_integration",
        "    if hasattr(rust_kicad_integration, 'is_rust_available') and rust_kicad_integration.is_rust_available():",
        "        _rust_sexp_module = rust_kicad_integration",
        "        logging.getLogger(__name__).info(\"🦀 RUST: KiCad S-expression generation accelerated\")",
        "    else:",
        "        logging.getLogger(__name__).warning(\"⚠️ Rust module found but not functional\")",
        "except ImportError:",
        "    logging.getLogger(__name__).info(\"🐍 Using Python implementation for KiCad formatting\")",
        "except Exception as e:",
        "    logging.getLogger(__name__).warning(f\"⚠️ Error loading Rust module: {e}, using Python fallback\")",
    ]
    
    # Rebuild the file
    new_lines = lines[:try_start] + new_block + lines[except_end+1:]
    
    # Write back
    file_path.write_text("\n".join(new_lines))
    print(f"✅ Fixed {file_path}")
    return True

def fix_rust_accelerated_symbol_cache():
    """Fix rust_accelerated_symbol_cache.py."""
    file_path = Path("src/circuit_synth/kicad/rust_accelerated_symbol_cache.py")
    
    content = file_path.read_text()
    
    # Replace the complex import logic with simple optional import
    lines = content.splitlines()
    
    # Find import block
    import_start = None
    for i, line in enumerate(lines):
        if "try:" in line and i < 50:  # Near the top of file
            import_start = i
            break
    
    if import_start:
        # Find end of import block
        import_end = None
        for i in range(import_start, min(import_start + 100, len(lines))):
            if "logger" in lines[i] and "RUST_IMPORT" in lines[i]:
                import_end = i + 1
                break
        
        if import_end:
            new_block = [
                "# Optional Rust import",
                "RUST_AVAILABLE = False",
                "try:",
                "    import rust_symbol_cache",
                "    RUST_AVAILABLE = True",
                "    logger.debug(\"🦀 Rust symbol cache available\")",
                "except ImportError:",
                "    logger.debug(\"🐍 Using Python symbol cache\")",
            ]
            
            new_lines = lines[:import_start] + new_block + lines[import_end:]
            file_path.write_text("\n".join(new_lines))
            print(f"✅ Fixed {file_path}")
            return True
    
    print(f"⚠️ Could not fix {file_path} - manual intervention needed")
    return False

def fix_placement():
    """Fix placement.py."""
    file_path = Path("src/circuit_synth/kicad/schematic/placement.py")
    
    content = file_path.read_text()
    
    # Replace complex Rust import with simple optional
    lines = content.splitlines()
    
    new_lines = []
    skip_until = None
    
    for i, line in enumerate(lines):
        if skip_until and i < skip_until:
            continue
        skip_until = None
        
        if "import rust_force_directed_placement" in line or "from rust_force_directed_placement" in line:
            # Start of Rust import block
            # Find the end of the try/except block
            for j in range(i, min(i + 50, len(lines))):
                if "except" in lines[j] and j > i:
                    for k in range(j, min(j + 20, len(lines))):
                        if lines[k] and not lines[k].startswith(" ") and not lines[k].startswith("\t"):
                            skip_until = k
                            break
                    break
            
            # Add simple import
            new_lines.extend([
                "# Optional Rust placement module",
                "try:",
                "    import rust_force_directed_placement",
                "    RUST_PLACEMENT_AVAILABLE = True",
                "except ImportError:",
                "    RUST_PLACEMENT_AVAILABLE = False",
            ])
        else:
            new_lines.append(line)
    
    file_path.write_text("\n".join(new_lines))
    print(f"✅ Fixed {file_path}")
    return True

def fix_rust_components():
    """Fix rust_components.py."""
    file_path = Path("src/circuit_synth/core/rust_components.py")
    
    content = file_path.read_text()
    
    # Make Rust import optional
    lines = content.splitlines()
    new_lines = []
    skip_until = None
    
    for i, line in enumerate(lines):
        if skip_until and i < skip_until:
            continue
        skip_until = None
        
        if "sys.path.insert" in line or "sys.path.append" in line:
            # Skip path manipulation
            continue
        elif "spec.loader.exec_module" in line:
            # Skip file-based loading
            for j in range(i-10, i+10):
                if j >= 0 and j < len(lines) and "except" in lines[j]:
                    skip_until = j + 5
                    break
            new_lines.extend([
                "# Use simple import instead",
                "try:",
                "    import rust_core_circuit_engine",
                "    RUST_AVAILABLE = True",
                "except ImportError:",
                "    RUST_AVAILABLE = False",
            ])
        else:
            new_lines.append(line)
    
    file_path.write_text("\n".join(new_lines))
    print(f"✅ Fixed {file_path}")
    return True

if __name__ == "__main__":
    print("🚨 EMERGENCY: Fixing Rust module packaging issues...")
    print("=" * 60)
    
    # Fix all problematic files
    fix_kicad_formatter()
    fix_rust_accelerated_symbol_cache()
    fix_placement()
    fix_rust_components()
    
    print("\n✅ Emergency fixes applied!")
    print("\nNow the package should work even without Rust modules compiled.")