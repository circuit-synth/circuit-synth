#!/usr/bin/env python3
"""
Test script for the new multi-file KiCad to Python conversion structure
"""

import logging
import sys
from pathlib import Path

# Add the src directory to the path so we can import circuit_synth modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from circuit_synth.tools.kicad_parser import KiCadParser
from circuit_synth.tools.python_code_generator import PythonCodeGenerator

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_new_structure():
    """Test the new multi-file structure"""
    logger.info("🧪 Testing new multi-file KiCad to Python conversion structure")
    
    # Input KiCad project
    kicad_project = Path("/Users/shanemattner/Desktop/circuit-synth/tests/kicad_to_python/03_dual_hierarchy_connected/03_dual_hierarchy_connected/03_dual_hierarchy_connected.kicad_pro")
    
    # Output directory
    output_dir = Path("/tmp/test_new_structure")
    output_dir.mkdir(exist_ok=True)
    main_file = output_dir / "main.py"
    
    logger.info(f"📂 Input KiCad project: {kicad_project}")
    logger.info(f"📂 Output directory: {output_dir}")
    
    try:
        # Step 1: Parse KiCad project
        logger.info("Step 1: Parsing KiCad project")
        parser = KiCadParser(str(kicad_project))
        circuits = parser.parse_circuits()
        
        if not circuits:
            logger.error("❌ No circuits found in KiCad project")
            return False
            
        logger.info(f"✅ Found {len(circuits)} circuits:")
        for name, circuit in circuits.items():
            logger.info(f"  - {name}: {len(circuit.components)} components, {len(circuit.nets)} nets")
        
        # Step 2: Generate Python files using new structure
        logger.info("Step 2: Generating Python files with new structure")
        project_name = kicad_project.stem
        generator = PythonCodeGenerator(project_name=project_name)
        
        # Use the new multi-file generation method
        main_code = generator.update_python_file(main_file, circuits, preview_only=False)
        
        if main_code:
            logger.info("✅ Successfully generated new file structure!")
            logger.info(f"📁 Files created in {output_dir}:")
            
            # List the created files
            for file_path in sorted(output_dir.glob("*.py")):
                logger.info(f"  - {file_path.name}")
                
            return True
        else:
            logger.error("❌ Failed to generate Python files")
            return False
            
    except Exception as e:
        logger.error(f"❌ Test failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

if __name__ == "__main__":
    success = test_new_structure()
    sys.exit(0 if success else 1)