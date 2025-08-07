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
    
    Currently, Rust backend is only used for simple (non-hierarchical) circuits.
    Once hierarchical support is complete, this can be updated.
    
    Args:
        json_file: Path to the circuit JSON file
        
    Returns:
        True if Rust backend should be used, False otherwise
    """
    try:
        import json
        with open(json_file, 'r') as f:
            data = json.load(f)
            
        # Check if circuit has subcircuits (hierarchical)
        has_subcircuits = bool(data.get('subcircuits'))
        
        # Check component count (Rust is optimized for larger circuits)
        component_count = len(data.get('components', {}))
        
        # For now, only use Rust for non-hierarchical circuits
        # TODO: Enable for hierarchical once support is complete
        if has_subcircuits:
            logger.info(f"  Circuit is hierarchical - using Python backend")
            return False
            
        # Use Rust for simple circuits
        logger.info(f"  Circuit is simple ({component_count} components) - using Rust backend")
        return True
        
    except Exception as e:
        logger.warning(f"  Could not analyze circuit complexity: {e}")
        logger.info(f"  Defaulting to Python backend")
        return False


def get_schematic_generator(output_dir: str, project_name: str, json_file: Optional[str] = None):
    """
    Get the appropriate schematic generator based on circuit complexity.
    
    Args:
        output_dir: Output directory for the project
        project_name: Name of the KiCad project  
        json_file: Optional path to circuit JSON for analysis
        
    Returns:
        SchematicGenerator instance (either Rust-integrated or Python)
    """
    use_rust = False
    
    if json_file:
        use_rust = should_use_rust_backend(json_file)
    
    if use_rust:
        try:
            from .rust_integrated_generator import RustIntegratedSchematicGenerator
            logger.info("✅ Using Rust-integrated schematic generator")
            return RustIntegratedSchematicGenerator(output_dir, project_name, use_rust=True)
        except ImportError:
            logger.warning("❌ Rust backend not available, falling back to Python")
    
    # Default to Python implementation
    from .main_generator import SchematicGenerator
    logger.info("📋 Using Python schematic generator")
    return SchematicGenerator(output_dir, project_name)