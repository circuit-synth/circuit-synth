#!/usr/bin/env python3
"""
Comprehensive debugging script to trace dictionary strings in lib_symbols generation.
This script will add aggressive logging to identify exactly where dictionary objects become strings.
"""

import sys
import os
import logging
import importlib
from pathlib import Path

# Add the src directory to Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Configure detailed logging
logging.basicConfig(
    level=logging.DEBUG,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('debug_lib_symbols_comprehensive.log'),
        logging.StreamHandler()
    ]
)

logger = logging.getLogger(__name__)

def monkey_patch_str_calls():
    """Monkey patch str() calls to detect when dictionaries are converted to strings."""
    original_str = str
    
    def debug_str(obj):
        if isinstance(obj, dict) and any(key in str(obj) for key in ['Reference', 'Value', 'Footprint']):
            import traceback
            logger.error(f"🚨 DICTIONARY TO STRING CONVERSION DETECTED!")
            logger.error(f"Dictionary: {obj}")
            logger.error(f"Stack trace:")
            for line in traceback.format_stack():
                logger.error(line.strip())
            logger.error("=" * 80)
        return original_str(obj)
    
    # Replace built-in str with our debug version
    import builtins
    builtins.str = debug_str
    logger.info("🔧 Monkey patched str() to detect dictionary conversions")

def trace_symbol_cache_operations():
    """Add tracing to symbol cache operations."""
    try:
        from circuit_synth.kicad.kicad_symbol_cache import SymbolLibCache
        
        # Monkey patch get_symbol_data
        original_get_symbol_data = SymbolLibCache.get_symbol_data
        
        @classmethod
        def traced_get_symbol_data(cls, symbol_id):
            logger.info(f"🔍 SymbolLibCache.get_symbol_data called with: {symbol_id}")
            result = original_get_symbol_data(symbol_id)
            logger.info(f"🔍 SymbolLibCache.get_symbol_data result type: {type(result)}")
            
            # Check if result contains dictionary strings
            if isinstance(result, dict):
                for key, value in result.items():
                    if isinstance(value, str) and value.startswith('{') and value.endswith('}'):
                        logger.error(f"🚨 FOUND DICTIONARY STRING in symbol cache result!")
                        logger.error(f"Key: {key}, Value: {value}")
                    elif isinstance(value, list):
                        for i, item in enumerate(value):
                            if isinstance(item, str) and item.startswith('{') and item.endswith('}'):
                                logger.error(f"🚨 FOUND DICTIONARY STRING in symbol cache result list!")
                                logger.error(f"Key: {key}[{i}], Value: {item}")
            
            return result
        
        SymbolLibCache.get_symbol_data = traced_get_symbol_data
        logger.info("🔧 Added tracing to SymbolLibCache.get_symbol_data")
        
    except ImportError as e:
        logger.warning(f"Could not trace SymbolLibCache: {e}")

def trace_symbol_parser_operations():
    """Add tracing to symbol parser operations."""
    try:
        from circuit_synth.kicad import kicad_symbol_parser
        
        # Monkey patch parse_kicad_sym_file
        original_parse = kicad_symbol_parser.parse_kicad_sym_file
        
        def traced_parse(file_path):
            logger.info(f"🔍 parse_kicad_sym_file called with: {file_path}")
            result = original_parse(file_path)
            logger.info(f"🔍 parse_kicad_sym_file result type: {type(result)}")
            
            # Check if result contains dictionary strings
            if isinstance(result, dict) and 'symbols' in result:
                for sym_name, sym_data in result['symbols'].items():
                    if isinstance(sym_data, dict) and 'properties' in sym_data:
                        for prop in sym_data['properties']:
                            if isinstance(prop, str) and prop.startswith('{') and prop.endswith('}'):
                                logger.error(f"🚨 FOUND DICTIONARY STRING in symbol parser result!")
                                logger.error(f"Symbol: {sym_name}, Property: {prop}")
            
            return result
        
        kicad_symbol_parser.parse_kicad_sym_file = traced_parse
        logger.info("🔧 Added tracing to parse_kicad_sym_file")
        
    except ImportError as e:
        logger.warning(f"Could not trace symbol parser: {e}")

def trace_s_expression_operations():
    """Add tracing to S-expression formatting operations."""
    try:
        from circuit_synth.kicad_api.core.s_expression import SExpressionParser
        
        # Check if there are methods that might convert dictionaries to strings
        for attr_name in dir(SExpressionParser):
            if not attr_name.startswith('_'):
                attr = getattr(SExpressionParser, attr_name)
                if callable(attr):
                    logger.info(f"🔍 Found SExpressionParser method: {attr_name}")
        
    except ImportError as e:
        logger.warning(f"Could not trace S-expression operations: {e}")

def trace_schematic_writer_operations():
    """Add tracing to schematic writer operations."""
    try:
        from circuit_synth.kicad.sch_gen.schematic_writer import SchematicWriter
        
        # Look for methods that generate lib_symbols
        for attr_name in dir(SchematicWriter):
            if 'lib' in attr_name.lower() or 'symbol' in attr_name.lower():
                logger.info(f"🔍 Found SchematicWriter method: {attr_name}")
        
    except ImportError as e:
        logger.warning(f"Could not trace schematic writer: {e}")

def run_test_generation():
    """Run a test generation to trigger the issue."""
    logger.info("🚀 Starting test generation to trigger lib_symbols issue...")
    
    try:
        # Import and run the circuit generation
        from circuit_synth.kicad.sch_gen.main_generator import SchematicGenerator
        
        # Create a simple test circuit
        test_circuit_data = {
            "json_file": "reference_troubleshooting/circuit-synth_project.py",
            "components": [
                {
                    "ref": "R1",
                    "symbol": "Device:R",
                    "value": "10k",
                    "footprint": "Resistor_SMD:R_0603_1608Metric"
                }
            ],
            "nets": []
        }
        
        # Generate schematic
        generator = SchematicGenerator("debug_output", "test_lib_symbols")
        result = generator.generate_from_circuit_data(test_circuit_data)
        
        logger.info(f"✅ Test generation completed: {result}")
        
        # Check the generated .kicad_sch file for dictionary strings
        sch_file = Path("debug_output/test_lib_symbols/test_lib_symbols.kicad_sch")
        if sch_file.exists():
            with open(sch_file, 'r') as f:
                content = f.read()
                
            # Look for dictionary strings in lib_symbols section
            if '(lib_symbols' in content:
                lib_symbols_start = content.find('(lib_symbols')
                lib_symbols_end = content.find(')', lib_symbols_start)
                lib_symbols_section = content[lib_symbols_start:lib_symbols_end + 1]
                
                logger.info("🔍 Found lib_symbols section:")
                logger.info(lib_symbols_section[:500] + "..." if len(lib_symbols_section) > 500 else lib_symbols_section)
                
                # Check for dictionary strings
                if '{' in lib_symbols_section and '}' in lib_symbols_section:
                    logger.error("🚨 FOUND DICTIONARY STRINGS IN LIB_SYMBOLS SECTION!")
                    
                    # Extract the problematic parts
                    lines = lib_symbols_section.split('\n')
                    for i, line in enumerate(lines):
                        if '{' in line and '}' in line:
                            logger.error(f"Line {i}: {line.strip()}")
                else:
                    logger.info("✅ No dictionary strings found in lib_symbols section")
        
    except Exception as e:
        logger.error(f"❌ Test generation failed: {e}")
        import traceback
        logger.error(traceback.format_exc())

def main():
    """Main debugging function."""
    logger.info("🔧 Starting comprehensive lib_symbols debugging...")
    
    # Clear any cached modules to ensure fresh imports
    modules_to_clear = [
        'circuit_synth.kicad.kicad_symbol_cache',
        'circuit_synth.kicad.kicad_symbol_parser',
        'circuit_synth.kicad.sch_gen.schematic_writer',
        'circuit_synth.kicad_api.core.s_expression'
    ]
    
    for module_name in modules_to_clear:
        if module_name in sys.modules:
            del sys.modules[module_name]
            logger.info(f"🔄 Cleared cached module: {module_name}")
    
    # Apply monkey patches and tracing
    monkey_patch_str_calls()
    trace_symbol_cache_operations()
    trace_symbol_parser_operations()
    trace_s_expression_operations()
    trace_schematic_writer_operations()
    
    # Run test generation
    run_test_generation()
    
    logger.info("🏁 Comprehensive debugging completed. Check the log file for details.")

if __name__ == "__main__":
    main()