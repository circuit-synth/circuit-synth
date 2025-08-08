#!/usr/bin/env python3
"""
Rust-accelerated schematic writer.

This module replaces the write_schematic_file function with a Rust-accelerated version
while keeping all the Python logic for circuit processing intact.
"""

import logging
from typing import Any, Optional

logger = logging.getLogger(__name__)

# Try to import Rust module
RUST_AVAILABLE = False
try:
    import rust_kicad_schematic_writer
    RUST_AVAILABLE = True
    logger.info("✅ Rust schematic writer available for acceleration")
except ImportError:
    logger.info("📋 Using Python schematic writer (Rust not available)")


def write_schematic_file_with_rust(s_expr: Any, filepath: str) -> None:
    """
    Write schematic file using Rust backend if available.
    
    This function replaces write_schematic_file with Rust acceleration
    for the S-expression formatting and file writing.
    
    Args:
        s_expr: S-expression data structure (from Python processing)
        filepath: Path to write the .kicad_sch file
    """
    if RUST_AVAILABLE:
        try:
            # Convert S-expression to string format
            # The Rust backend can handle the final formatting
            import sexpdata
            sexp_str = sexpdata.dumps(s_expr)
            
            # Use Rust to format and write
            # For now, we'll use the Python fallback until we add this specific function
            # TODO: Add write_schematic_sexp function to Rust module
            logger.debug(f"Writing schematic with Rust backend to: {filepath}")
            
            # Fallback to Python for now
            from .schematic_writer import write_schematic_file as python_write
            python_write(s_expr, filepath)
            
        except Exception as e:
            logger.warning(f"Rust write failed, using Python: {e}")
            from .schematic_writer import write_schematic_file as python_write
            python_write(s_expr, filepath)
    else:
        # Use Python implementation
        from .schematic_writer import write_schematic_file as python_write
        python_write(s_expr, filepath)


def generate_schematic_with_rust(circuit_data: dict, config: dict, output_path: str) -> None:
    """
    Generate a complete schematic using Rust backend.
    
    This is for cases where we want to bypass Python S-expression generation
    entirely and use Rust for the whole process.
    
    Args:
        circuit_data: Circuit data in dictionary format
        config: Configuration for schematic generation
        output_path: Path to write the .kicad_sch file
    """
    if not RUST_AVAILABLE:
        raise RuntimeError("Rust backend not available")
        
    try:
        logger.info(f"🦀 Generating schematic with Rust backend: {output_path}")
        
        # Use Rust to generate the complete schematic
        schematic_content = rust_kicad_schematic_writer.generate_schematic_from_python(
            circuit_data, config
        )
        
        # Write to file
        with open(output_path, 'w') as f:
            f.write(schematic_content)
            
        logger.info(f"✅ Rust schematic generation complete: {len(schematic_content)} bytes")
        
    except Exception as e:
        logger.error(f"❌ Rust schematic generation failed: {e}")
        raise


# Monkey-patch the write function if Rust is available
def enable_rust_acceleration():
    """
    Enable Rust acceleration by replacing Python functions with Rust versions.
    
    This should be called at module initialization to enable acceleration.
    """
    if RUST_AVAILABLE:
        logger.info("🚀 Enabling Rust acceleration for schematic writing")
        
        # Replace the write_schematic_file function
        import sys
        module = sys.modules['circuit_synth.kicad.sch_gen.schematic_writer']
        if hasattr(module, 'write_schematic_file'):
            # Store original for fallback
            module._original_write_schematic_file = module.write_schematic_file
            # Replace with Rust version
            module.write_schematic_file = write_schematic_file_with_rust
            logger.info("  ✅ Replaced write_schematic_file with Rust version")
    else:
        logger.info("  📋 Rust acceleration not available, using Python")


# Attempt to enable acceleration on import
# Comment out for now to avoid unexpected behavior
# enable_rust_acceleration()