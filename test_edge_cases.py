#!/usr/bin/env python3
"""
Comprehensive edge case testing for the new multi-file KiCad to Python conversion
"""

import logging
import sys
import tempfile
from pathlib import Path

# Add the src directory to the path so we can import circuit_synth modules
sys.path.insert(0, str(Path(__file__).parent / "src"))

from circuit_synth.tools.kicad_parser import KiCadParser
from circuit_synth.tools.python_code_generator import PythonCodeGenerator

# Set up logging
logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
logger = logging.getLogger(__name__)

def test_edge_case(test_name: str, kicad_project_path: str, expected_behavior: str):
    """Test a specific edge case"""
    logger.info(f"🧪 Testing: {test_name}")
    logger.info(f"📂 Project: {kicad_project_path}")
    logger.info(f"📝 Expected: {expected_behavior}")
    
    try:
        # Create temporary output directory
        output_dir = Path(tempfile.mkdtemp()) / f"test_{test_name.lower().replace(' ', '_')}"
        output_dir.mkdir(exist_ok=True)
        main_file = output_dir / "main.py"
        
        # Parse KiCad project
        parser = KiCadParser(kicad_project_path)
        circuits = parser.parse_circuits()
        
        if not circuits:
            logger.warning(f"❓ {test_name}: No circuits found")
            return False
            
        logger.info(f"✅ Found {len(circuits)} circuits: {list(circuits.keys())}")
        
        # Generate Python files
        project_name = Path(kicad_project_path).stem.replace('.kicad_pro', '')
        generator = PythonCodeGenerator(project_name=project_name)
        
        main_code = generator.update_python_file(main_file, circuits, preview_only=False)
        
        if main_code:
            # List generated files
            generated_files = list(output_dir.glob("*.py"))
            logger.info(f"✅ {test_name}: Generated {len(generated_files)} files:")
            for file_path in sorted(generated_files):
                logger.info(f"  - {file_path.name}")
                
            # Brief content preview
            logger.info(f"📄 Main file preview (first 5 lines):")
            for i, line in enumerate(main_code.split('\n')[:5], 1):
                logger.info(f"  {i}: {line}")
                
            return True
        else:
            logger.error(f"❌ {test_name}: Failed to generate code")
            return False
            
    except Exception as e:
        logger.error(f"❌ {test_name}: Exception - {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def test_programmatic_edge_cases():
    """Test edge cases using programmatically created circuits"""
    logger.info("🧪 Testing programmatic edge cases")
    
    from circuit_synth.tools.models import Circuit, Component, Net
    
    # Test case: Empty circuit
    empty_circuit = Circuit(name="empty", components=[], nets=[])
    
    # Test case: Circuit with components but no nets
    no_nets_circuit = Circuit(
        name="no_nets", 
        components=[Component(reference="R1", lib_id="Device:R", value="10k")],
        nets=[]
    )
    
    # Test case: Circuit with invalid net names
    invalid_names_circuit = Circuit(
        name="invalid_names",
        components=[],
        nets=[
            Net(name="+3.3V", connections=[]),  # Invalid Python name
            Net(name="123_invalid", connections=[]),  # Starts with number
            Net(name="signal/with/slashes", connections=[]),  # Contains slashes
            Net(name="signal with spaces", connections=[])  # Contains spaces
        ]
    )
    
    # Test case: Three-level hierarchy (main -> parent -> child)
    # Main circuit with shared nets
    main_circuit = Circuit(
        name="main",
        components=[Component(reference="R1", lib_id="Device:R", value="1k")],
        nets=[Net(name="VCC", connections=[]), Net(name="GND", connections=[]), Net(name="SIGNAL", connections=[])]
    )
    
    # Parent circuit (shares some nets with main, some with child)
    parent_circuit = Circuit(
        name="parent",
        components=[Component(reference="R2", lib_id="Device:R", value="2k")],
        nets=[Net(name="VCC", connections=[]), Net(name="GND", connections=[]), Net(name="LOCAL_NET", connections=[])]
    )
    
    # Child circuit (shares some nets with parent)
    child_circuit = Circuit(
        name="child",
        components=[Component(reference="R3", lib_id="Device:R", value="3k")],
        nets=[Net(name="GND", connections=[]), Net(name="LOCAL_NET", connections=[])]
    )
    
    # Test case: Partially shared nets
    circuit_a = Circuit(
        name="circuit_a",
        components=[],
        nets=[Net(name="VCC", connections=[]), Net(name="GND", connections=[]), Net(name="UNIQUE_A", connections=[])]
    )
    
    circuit_b = Circuit(
        name="circuit_b",
        components=[],
        nets=[Net(name="VCC", connections=[]), Net(name="UNIQUE_B", connections=[])]  # Only shares VCC
    )
    
    # Test the code generator with these edge cases
    generator = PythonCodeGenerator(project_name="edge_test")
    
    try:
        # Test empty circuit
        logger.info("🧪 Testing empty circuit")
        empty_code = generator._generate_flat_code(empty_circuit)
        logger.info(f"✅ Empty circuit: Generated {len(empty_code)} characters")
        
        # Test no nets circuit
        logger.info("🧪 Testing circuit with no nets")
        no_nets_code = generator._generate_flat_code(no_nets_circuit)
        logger.info(f"✅ No nets circuit: Generated {len(no_nets_code)} characters")
        
        # Test invalid net names
        logger.info("🧪 Testing invalid net names sanitization")
        for net in invalid_names_circuit.nets:
            sanitized = generator._sanitize_variable_name(net.name)
            logger.info(f"  '{net.name}' → '{sanitized}'")
        
        # Test multi-level hierarchy
        logger.info("🧪 Testing multi-level hierarchy (main -> parent -> child)")
        multi_circuits = {"main": main_circuit, "parent": parent_circuit, "child": child_circuit}
        
        # Create temporary test file
        import tempfile
        temp_dir = Path(tempfile.mkdtemp())
        temp_main = temp_dir / "main.py"
        
        multi_code = generator._generate_multiple_files(temp_main, multi_circuits, preview_only=True)
        if multi_code:
            logger.info(f"✅ Multi-level hierarchy: Generated code successfully")
        else:
            logger.warning("⚠️ Multi-level hierarchy: Code generation returned None")
        
        # Test partially shared nets
        logger.info("🧪 Testing partially shared nets")
        partial_circuits = {"main": circuit_a, "subcircuit": circuit_b}
        partial_code = generator._generate_multiple_files(temp_main, partial_circuits, preview_only=True)
        if partial_code:
            logger.info(f"✅ Partially shared nets: Generated code successfully")
        else:
            logger.warning("⚠️ Partially shared nets: Code generation returned None")
        
        logger.info("✅ Programmatic edge cases passed")
        return True
        
    except Exception as e:
        logger.error(f"❌ Programmatic edge cases failed: {e}")
        import traceback
        logger.error(traceback.format_exc())
        return False

def run_edge_case_tests():
    """Run comprehensive edge case tests"""
    logger.info("🔬 Starting comprehensive edge case testing")
    
    test_cases = [
        {
            "name": "Single Circuit (Non-hierarchical)",
            "path": "/Users/shanemattner/Desktop/circuit-synth/tests/kicad_to_python/01_simple_resistor/01_simple_resistor_reference/01_simple_resistor_reference.kicad_pro",
            "expected": "Should generate single main.py file, no separate subcircuit files"
        },
        {
            "name": "Dual Hierarchy (No Connections)", 
            "path": "/Users/shanemattner/Desktop/circuit-synth/tests/kicad_to_python/02_dual_hierarchy/02_dual_hierarchy/02_dual_hierarchy.kicad_pro",
            "expected": "Should generate main.py + child1.py, but no shared nets (empty parameters)"
        },
        {
            "name": "Dual Hierarchy (With Connections)",
            "path": "/Users/shanemattner/Desktop/circuit-synth/tests/kicad_to_python/03_dual_hierarchy_connected/03_dual_hierarchy_connected/03_dual_hierarchy_connected.kicad_pro", 
            "expected": "Should generate main.py + child1.py with shared nets passed as parameters"
        }
    ]
    
    results = []
    for test_case in test_cases:
        success = test_edge_case(
            test_case["name"],
            test_case["path"], 
            test_case["expected"]
        )
        results.append((test_case["name"], success))
        logger.info(f"{'✅' if success else '❌'} {test_case['name']}: {'PASSED' if success else 'FAILED'}")
        logger.info("-" * 80)
    
    # Run programmatic edge cases
    logger.info("-" * 80)
    programmatic_success = test_programmatic_edge_cases()
    results.append(("Programmatic Edge Cases", programmatic_success))
    
    # Summary
    passed = sum(1 for _, success in results if success)
    total = len(results)
    logger.info(f"🎯 EDGE CASE TEST SUMMARY: {passed}/{total} tests passed")
    
    for name, success in results:
        logger.info(f"  {'✅' if success else '❌'} {name}")
    
    return passed == total

if __name__ == "__main__":
    success = run_edge_case_tests()
    sys.exit(0 if success else 1)