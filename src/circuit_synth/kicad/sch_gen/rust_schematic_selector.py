#!/usr/bin/env python3
"""
Intelligent selector for Rust vs Python schematic generation.

This module automatically chooses the best backend based on circuit complexity.
"""

import logging
from typing import Optional

logger = logging.getLogger(__name__)


def should_use_rust_backend(json_file: str) -> bool:
    """
    Determine if Rust backend should be used for a given circuit.
    
    CURRENT STATUS: Rust backend is ALWAYS used for ALL circuits.
    The Rust implementation handles both simple and hierarchical circuits.
    
    Args:
        json_file: Path to the circuit JSON file
        
    Returns:
        True (always uses Rust backend)
    """
    try:
        import json
        with open(json_file, 'r') as f:
            data = json.load(f)
            
        # Log circuit information for debugging
        has_subcircuits = bool(data.get('subcircuits'))
        component_count = len(data.get('components', {}))
        
        if has_subcircuits:
            logger.info(f"  Circuit is hierarchical ({len(data.get('subcircuits', []))} subcircuits) - using Rust backend")
        else:
            logger.info(f"  Circuit is simple ({component_count} components) - using Rust backend")
            
        # ALWAYS use Rust backend - it's fully functional
        return True
        
    except Exception as e:
        logger.warning(f"  Could not analyze circuit complexity: {e}")
        logger.info(f"  Using Rust backend anyway")
        # Even on error, we still use Rust backend
        return True


def get_schematic_generator(output_dir: str, project_name: str, json_file: Optional[str] = None):
    """
    Get the schematic generator - ALWAYS returns Rust-integrated generator.
    
    Args:
        output_dir: Output directory for the project
        project_name: Name of the KiCad project  
        json_file: Optional path to circuit JSON for analysis
        
    Returns:
        RustIntegratedSchematicGenerator instance (Rust backend always enabled)
    """
    # Log circuit analysis if json_file provided
    if json_file:
        should_use_rust_backend(json_file)  # Just for logging
    
    # ALWAYS use Rust backend - it's the only maintained implementation
    try:
        from .rust_integrated_generator import RustIntegratedSchematicGenerator
        logger.info("✅ Using Rust-integrated schematic generator")
        return RustIntegratedSchematicGenerator(output_dir, project_name, use_rust=True)
    except ImportError as e:
        # This should never happen in production since Rust is required
        logger.error(f"❌ CRITICAL: Rust backend not available: {e}")
        logger.error("❌ The Rust backend is REQUIRED for circuit-synth to function")
        raise ImportError(
            "Rust backend is required but not available. "
            "Please ensure rust_kicad_integration module is built and installed."
        )