#!/usr/bin/env python3
"""
Hybrid test: Generate circuits with old system, then enhance with atomic operations.
Uses flag to switch between old logic and new atomic operations.
"""

import sys
import logging
from pathlib import Path
import difflib
import os

# Add src to path  
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from circuit_synth import *
from circuit_synth.kicad.atomic_operations_exact import (
    add_component_to_schematic_exact as add_component_to_schematic,
    remove_component_from_schematic_exact as remove_component_from_schematic
)

# Set up detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('hybrid_test.log', mode='w'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

# FLAG: Use new atomic operations instead of old system
USE_ATOMIC_OPERATIONS = False

@circuit(name="blank_schematic")
def blank_schematic():
    """A blank schematic circuit."""
    logger.info("🏗️ Creating blank_schematic")
    pass


@circuit(name="single_resistor")
def single_resistor():
    """A circuit with a single 10k resistor."""
    logger.info("🏗️ Creating single_resistor circuit")
    r1 = Component("Device:R", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    logger.info(f"📦 Created component R1: {r1}")
    logger.info(f"📦 Component attributes: lib_id=Device:R, value=10k, footprint=Resistor_SMD:R_0603_1608Metric")
    return r1


@circuit(name="two_resistors")
def two_resistors():
    """A circuit with two 10k resistors."""
    logger.info("🏗️ Creating two_resistors circuit")
    r1 = Component("Device:R", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r2 = Component("Device:R", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    logger.info(f"📦 Created components R1: {r1}, R2: {r2}")
    return [r1, r2]


def generate_with_old_system(circuit_func, name):
    """Generate circuit using the old (broken) system."""
    logger.info(f"🔧 OLD SYSTEM: Generating {name}...")
    
    try:
        circuit = circuit_func()
        logger.info(f"🔧 OLD SYSTEM: Circuit object created: {circuit}")
        logger.info(f"🔧 OLD SYSTEM: Circuit components: {getattr(circuit, '_component_list', 'No _component_list')}")
        logger.info(f"🔧 OLD SYSTEM: Circuit nets: {getattr(circuit, 'nets', 'No nets')}")
        
        project_name = f"{name}_old"
        logger.info(f"🔧 OLD SYSTEM: Calling generate_kicad_project({project_name})")
        
        circuit.generate_kicad_project(project_name=project_name)
        
        schematic_path = Path(project_name) / f"{project_name}.kicad_sch"
        logger.info(f"🔧 OLD SYSTEM: Generated schematic at {schematic_path}")
        
        if schematic_path.exists():
            with open(schematic_path, 'r') as f:
                content = f.read()
            logger.info(f"🔧 OLD SYSTEM: Generated file size: {len(content)} chars")
            logger.info(f"🔧 OLD SYSTEM: Symbol count: {content.count('(symbol')}")
            logger.info(f"🔧 OLD SYSTEM: First 200 chars: {content[:200]}")
        
        return schematic_path
        
    except Exception as e:
        logger.error(f"🔧 OLD SYSTEM: Failed to generate {name}: {e}")
        import traceback
        logger.error(f"🔧 OLD SYSTEM: Traceback: {traceback.format_exc()}")
        return None


def generate_with_atomic_operations(circuit_func, name):
    """Generate circuit using atomic operations."""
    logger.info(f"⚡ ATOMIC SYSTEM: Generating {name}...")
    
    try:
        # Step 1: Generate blank schematic with old system
        blank_circuit = blank_schematic()
        project_name = f"{name}_atomic"
        blank_circuit.generate_kicad_project(project_name=project_name)
        
        schematic_path = Path(project_name) / f"{project_name}.kicad_sch"
        logger.info(f"⚡ ATOMIC SYSTEM: Created blank schematic at {schematic_path}")
        
        # Step 2: Use atomic operations to add components
        if name == "single_resistor":
            logger.info("⚡ ATOMIC SYSTEM: Adding single resistor")
            success = add_component_to_schematic(
                schematic_path,
                lib_id="Device:R",
                reference="R1",
                value="10k",
                position=(121.92, 68.58),
                footprint="Resistor_SMD:R_0603_1608Metric"
            )
            logger.info(f"⚡ ATOMIC SYSTEM: Add R1 result: {success}")
            
        elif name == "two_resistors":
            logger.info("⚡ ATOMIC SYSTEM: Adding two resistors")
            success1 = add_component_to_schematic(
                schematic_path,
                lib_id="Device:R", 
                reference="R1",
                value="10k",
                position=(121.92, 67.31),
                footprint="Resistor_SMD:R_0603_1608Metric"
            )
            success2 = add_component_to_schematic(
                schematic_path,
                lib_id="Device:R",
                reference="R2", 
                value="10k",
                position=(137.16, 68.58),
                footprint="Resistor_SMD:R_0603_1608Metric"
            )
            logger.info(f"⚡ ATOMIC SYSTEM: Add R1 result: {success1}, R2 result: {success2}")
        
        # Step 3: Check result
        if schematic_path.exists():
            with open(schematic_path, 'r') as f:
                content = f.read()
            logger.info(f"⚡ ATOMIC SYSTEM: Final file size: {len(content)} chars")
            logger.info(f"⚡ ATOMIC SYSTEM: Symbol count: {content.count('(symbol')}")
            logger.info(f"⚡ ATOMIC SYSTEM: First 200 chars: {content[:200]}")
        
        return schematic_path
        
    except Exception as e:
        logger.error(f"⚡ ATOMIC SYSTEM: Failed to generate {name}: {e}")
        import traceback
        logger.error(f"⚡ ATOMIC SYSTEM: Traceback: {traceback.format_exc()}")
        return None


def compare_to_reference(generated_path, name):
    """Compare generated file to reference."""
    logger.info(f"🔍 Comparing {name} to reference...")
    
    # Map to reference paths
    ref_map = {
        "blank_schematic": "blank_schematic/blank_schematic.kicad_sch",
        "single_resistor": "single_resistor/single_resistor.kicad_sch", 
        "two_resistors": "two_resistors/two_resistors.kicad_sch"
    }
    
    if name not in ref_map:
        logger.error(f"🔍 No reference mapping for {name}")
        return False
    
    reference_path = Path(ref_map[name])
    
    if not generated_path or not generated_path.exists():
        logger.error(f"🔍 Generated file missing: {generated_path}")
        return False
    
    if not reference_path.exists():
        logger.error(f"🔍 Reference file missing: {reference_path}")
        return False
    
    # Read files
    with open(generated_path, 'r') as f:
        generated = f.read()
    with open(reference_path, 'r') as f:
        reference = f.read()
    
    # Compare
    gen_symbols = generated.count("(symbol")
    ref_symbols = reference.count("(symbol")
    
    logger.info(f"🔍 {name}: Generated={len(generated)} chars, Reference={len(reference)} chars")
    logger.info(f"🔍 {name}: Generated symbols={gen_symbols}, Reference symbols={ref_symbols}")
    
    # Success if symbol counts match (ignoring UUIDs and exact formatting)
    match = gen_symbols == ref_symbols
    
    if match:
        logger.info(f"✅ {name}: Symbol counts match!")
    else:
        logger.error(f"❌ {name}: Symbol counts differ (gen={gen_symbols}, ref={ref_symbols})")
        
        # Show sample differences
        logger.info("🔍 Sample differences:")
        gen_lines = generated.split('\n')[:10]
        ref_lines = reference.split('\n')[:10]
        for i, (g, r) in enumerate(zip(gen_lines, ref_lines)):
            if g != r:
                logger.info(f"  Line {i}: GEN='{g[:50]}' REF='{r[:50]}'")
    
    return match


def main():
    logger.info("🧪 Hybrid Circuit Generation Test")
    logger.info(f"🚀 USE_ATOMIC_OPERATIONS = {USE_ATOMIC_OPERATIONS}")
    
    circuits = [
        (blank_schematic, "blank_schematic"),
        (single_resistor, "single_resistor"),
        (two_resistors, "two_resistors")
    ]
    
    results = {}
    
    for circuit_func, name in circuits:
        logger.info(f"\n{'='*60}")
        logger.info(f"🔬 Testing {name}")
        logger.info(f"{'='*60}")
        
        if USE_ATOMIC_OPERATIONS:
            generated_path = generate_with_atomic_operations(circuit_func, name)
        else:
            generated_path = generate_with_old_system(circuit_func, name)
        
        # Compare to reference
        match = compare_to_reference(generated_path, name)
        results[name] = match
    
    # Summary
    logger.info(f"\n{'='*60}")
    logger.info("📊 FINAL RESULTS")
    logger.info(f"{'='*60}")
    logger.info(f"System used: {'ATOMIC OPERATIONS' if USE_ATOMIC_OPERATIONS else 'OLD SYSTEM'}")
    
    for name, match in results.items():
        status = "✅ MATCH" if match else "❌ DIFFER"
        logger.info(f"{status}: {name}")
    
    total_matches = sum(results.values())
    logger.info(f"📈 Score: {total_matches}/{len(results)} circuits match reference")


if __name__ == "__main__":
    main()