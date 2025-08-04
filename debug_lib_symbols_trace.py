#!/usr/bin/env python3
"""
Debug script to trace where dictionary strings are generated in lib_symbols.
This will help identify the actual active code path.
"""

import sys
import os
from pathlib import Path

# Add circuit-synth to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

def trace_lib_symbols_generation():
    """Trace the lib_symbols generation process with detailed logging."""
    print("=" * 80)
    print("🔍 TRACING LIB_SYMBOLS GENERATION")
    print("=" * 80)
    
    # Import the main generator
    from circuit_synth.kicad.sch_gen.main_generator import SchematicGeneratorImpl
    from circuit_synth.kicad.sch_gen.circuit_loader import Circuit, Net
    from circuit_synth.kicad_api.core.types import SchematicSymbol, Point
    
    # Create a simple test circuit
    print("📋 Creating test circuit...")
    circuit_data = {
        "name": "test_circuit",
        "components": [
            {
                "ref": "R1",
                "symbol_id": "Device:R",
                "value": "1k",
                "footprint": "Resistor_SMD:R_0603_1608Metric",
                "x": 100,
                "y": 100,
                "rotation": 0,
                "pins": [
                    {"num": "1", "name": "~", "net": "VCC"},
                    {"num": "2", "name": "~", "net": "GND"}
                ]
            }
        ],
        "nets": [
            {"name": "VCC", "connections": [("R1", "1")]},
            {"name": "GND", "connections": [("R1", "2")]}
        ]
    }
    
    # Create circuit manually
    circuit = Circuit("test_circuit")
    
    # Create component
    component = SchematicSymbol(
        reference="R1",
        value="1k",
        lib_id="Device:R",
        position=Point(100, 100),
        rotation=0,
        footprint="Resistor_SMD:R_0603_1608Metric"
    )
    circuit.add_component(component)
    
    # Create nets
    vcc_net = Net("VCC")
    gnd_net = Net("GND")
    circuit.add_net(vcc_net)
    circuit.add_net(gnd_net)
    
    # Create SchematicWriter directly
    output_dir = Path("debug_output")
    output_dir.mkdir(exist_ok=True)
    
    # Create a simple circuit dict for the writer
    circuit_dict = {"test_circuit": circuit}
    
    # Monkey patch the symbol cache to add tracing
    print("🔧 Adding symbol cache tracing...")
    
    # Import symbol cache classes
    from circuit_synth.kicad.kicad_symbol_cache import SymbolLibCache as PythonCache
    from circuit_synth.kicad.sch_gen.schematic_writer import SymbolLibCache
    
    # Store original methods
    original_get_symbol_data = SymbolLibCache.get_symbol_data
    
    def traced_get_symbol_data(symbol_id):
        print(f"🔍 TRACE: SymbolLibCache.get_symbol_data called for {symbol_id}")
        result = original_get_symbol_data(symbol_id)
        print(f"🔍 TRACE: Result type: {type(result)}")
        if isinstance(result, dict) and "properties" in result:
            print(f"🔍 TRACE: Properties found: {list(result['properties'].keys())}")
            for prop_name, prop_value in result['properties'].items():
                print(f"🔍 TRACE: Property {prop_name}: {repr(prop_value)} (type: {type(prop_value)})")
                if isinstance(prop_value, dict):
                    print(f"🚨 TRACE: FOUND DICTIONARY PROPERTY: {prop_name} = {prop_value}")
                elif isinstance(prop_value, str) and prop_value.startswith("{'value':"):
                    print(f"🚨 TRACE: FOUND DICTIONARY STRING: {prop_name} = {prop_value[:100]}...")
        return result
    
    # Apply monkey patch
    SymbolLibCache.get_symbol_data = staticmethod(traced_get_symbol_data)
    
    # Monkey patch the schematic writer's symbol definition creation
    from circuit_synth.kicad.sch_gen.schematic_writer import SchematicWriter
    
    original_create_symbol_definition = SchematicWriter._create_symbol_definition
    
    def traced_create_symbol_definition(self, lib_id, lib_data):
        print(f"🔍 TRACE: _create_symbol_definition called for {lib_id}")
        print(f"🔍 TRACE: lib_data type: {type(lib_data)}")
        if isinstance(lib_data, dict) and "properties" in lib_data:
            print(f"🔍 TRACE: Properties in lib_data:")
            for prop_name, prop_value in lib_data['properties'].items():
                print(f"🔍 TRACE: Property {prop_name}: {repr(prop_value)} (type: {type(prop_value)})")
                if isinstance(prop_value, dict):
                    print(f"🚨 TRACE: DICTIONARY PROPERTY DETECTED: {prop_name} = {prop_value}")
                elif isinstance(prop_value, str) and prop_value.startswith("{'value':"):
                    print(f"🚨 TRACE: DICTIONARY STRING DETECTED: {prop_name} = {prop_value[:100]}...")
        
        result = original_create_symbol_definition(self, lib_id, lib_data)
        print(f"🔍 TRACE: _create_symbol_definition result type: {type(result)}")
        return result
    
    SchematicWriter._create_symbol_definition = traced_create_symbol_definition
    
    # Monkey patch the S-expression cleaning
    from circuit_synth.kicad_api.core.s_expression import SExpressionParser
    
    original_clean_dict_strings = SExpressionParser._clean_dictionary_strings_recursive
    
    def traced_clean_dict_strings(self, data):
        print(f"🔍 TRACE: _clean_dictionary_strings_recursive called with type: {type(data)}")
        if isinstance(data, str) and (data.startswith("{'value':") or data.startswith('{"value":')):
            print(f"🚨 TRACE: CLEANING DICTIONARY STRING: {data[:100]}...")
        result = original_clean_dict_strings(self, data)
        return result
    
    SExpressionParser._clean_dictionary_strings_recursive = traced_clean_dict_strings
    
    try:
        print("🚀 Starting schematic generation...")
        
        # Create SchematicWriter directly
        writer = SchematicWriter(
            circuit=circuit,
            circuit_dict=circuit_dict,
            instance_naming_map={},
            paper_size="A4",
            project_name="debug_test"
        )
        
        # Generate S-expression
        print("📝 Generating S-expression...")
        schematic_expr = writer.generate_s_expr()
        
        # Write to file
        output_file = output_dir / "debug_test.kicad_sch"
        print(f"💾 Writing to file: {output_file}")
        
        from circuit_synth.kicad.sch_gen.schematic_writer import write_schematic_file
        write_schematic_file(schematic_expr, str(output_file))
        
        print(f"✅ Generation successful: {output_file}")
        
        # Check the generated file for dictionary strings
        if output_file.exists():
            print(f"📄 Checking generated file: {output_file}")
            with open(output_file, 'r') as f:
                content = f.read()
            
            # Look for dictionary strings in lib_symbols
            if "lib_symbols" in content:
                print("🔍 Found lib_symbols section")
                if "{'value':" in content or '{"value":' in content:
                    print("🚨 DICTIONARY STRINGS FOUND IN OUTPUT!")
                    # Find the specific lines
                    lines = content.split('\n')
                    for i, line in enumerate(lines):
                        if "{'value':" in line or '{"value":' in line:
                            print(f"🚨 Line {i+1}: {line.strip()}")
                else:
                    print("✅ No dictionary strings found in output")
            else:
                print("⚠️ No lib_symbols section found")
            
    except Exception as e:
        print(f"💥 Exception during generation: {e}")
        import traceback
        traceback.print_exc()
    
    print("=" * 80)
    print("🏁 TRACE COMPLETE")
    print("=" * 80)

if __name__ == "__main__":
    trace_lib_symbols_generation()