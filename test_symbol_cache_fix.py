#!/usr/bin/env python3
"""
Test script to verify that the symbol cache fix returns clean property values
instead of dictionary objects in the lib_symbols section.
"""

import sys
import os
import logging
from pathlib import Path

# Add the src directory to the Python path
sys.path.insert(0, str(Path(__file__).parent / "src"))

# Configure logging to see debug messages
logging.basicConfig(level=logging.DEBUG, format="%(asctime)s - %(levelname)s - %(name)s - %(message)s")

def test_symbol_parser_fix():
    """Test that the KiCad symbol parser returns clean property values."""
    print("=" * 80)
    print("🧪 TESTING SYMBOL PARSER FIX")
    print("=" * 80)
    
    try:
        from circuit_synth.kicad.kicad_symbol_parser import parse_kicad_sym_file
        
        # Find a test symbol file
        test_symbol_files = [
            "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/Device.kicad_sym",
            "/usr/share/kicad/symbols/Device.kicad_sym",
            "C:\\Program Files\\KiCad\\share\\kicad\\symbols\\Device.kicad_sym",
        ]
        
        symbol_file = None
        for test_file in test_symbol_files:
            if os.path.exists(test_file):
                symbol_file = test_file
                break
        
        if not symbol_file:
            print("❌ No KiCad symbol files found. Cannot test parser.")
            return False
        
        print(f"📁 Testing with symbol file: {symbol_file}")
        
        # Parse the symbol file
        result = parse_kicad_sym_file(symbol_file)
        
        if "symbols" not in result:
            print("❌ No symbols found in parsed result")
            return False
        
        symbols = result["symbols"]
        print(f"✅ Found {len(symbols)} symbols")
        
        # Test a few symbols for clean property values
        test_count = 0
        clean_count = 0
        
        for symbol_name, symbol_data in list(symbols.items())[:5]:  # Test first 5 symbols
            test_count += 1
            print(f"\n🔍 Testing symbol: {symbol_name}")
            
            if "properties" not in symbol_data:
                print(f"  ⚠️  No properties found for {symbol_name}")
                continue
            
            properties = symbol_data["properties"]
            print(f"  📋 Found {len(properties)} properties")
            
            symbol_is_clean = True
            for prop_name, prop_value in properties.items():
                print(f"    🏷️  {prop_name}: {repr(prop_value)} (type: {type(prop_value)})")
                
                if isinstance(prop_value, dict):
                    print(f"    ❌ Property {prop_name} is still a dictionary object!")
                    symbol_is_clean = False
                elif isinstance(prop_value, str) and (prop_value.startswith("{'value':") or prop_value.startswith('{"value":')):
                    print(f"    ❌ Property {prop_name} is a dictionary string!")
                    symbol_is_clean = False
                else:
                    print(f"    ✅ Property {prop_name} is clean")
            
            if symbol_is_clean:
                clean_count += 1
                print(f"  ✅ Symbol {symbol_name} has all clean properties")
            else:
                print(f"  ❌ Symbol {symbol_name} has dictionary properties")
        
        print(f"\n📊 RESULTS: {clean_count}/{test_count} symbols have clean properties")
        
        if clean_count == test_count:
            print("🎉 SUCCESS: All tested symbols have clean property values!")
            return True
        else:
            print("❌ FAILURE: Some symbols still have dictionary properties")
            return False
            
    except Exception as e:
        print(f"❌ ERROR testing symbol parser: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_schematic_generation():
    """Test that schematic generation produces clean lib_symbols."""
    print("\n" + "=" * 80)
    print("🧪 TESTING SCHEMATIC GENERATION")
    print("=" * 80)
    
    try:
        # Look for existing test projects
        test_projects = [
            "reference_troubleshooting/test_project/test_project.kicad_sch",
            "reference_troubleshooting/generated_project/generated_project.kicad_sch",
        ]
        
        for test_project in test_projects:
            if os.path.exists(test_project):
                print(f"📁 Examining existing schematic: {test_project}")
                
                with open(test_project, 'r') as f:
                    content = f.read()
                
                # Look for lib_symbols section
                if "(lib_symbols" in content:
                    print("✅ Found lib_symbols section")
                    
                    # Extract lib_symbols section
                    start_idx = content.find("(lib_symbols")
                    if start_idx != -1:
                        # Find the matching closing parenthesis
                        paren_count = 0
                        end_idx = start_idx
                        for i, char in enumerate(content[start_idx:], start_idx):
                            if char == '(':
                                paren_count += 1
                            elif char == ')':
                                paren_count -= 1
                                if paren_count == 0:
                                    end_idx = i + 1
                                    break
                        
                        lib_symbols_content = content[start_idx:end_idx]
                        
                        # Check for dictionary strings in properties
                        if "{'value':" in lib_symbols_content or '{"value":' in lib_symbols_content:
                            print("❌ Found dictionary strings in lib_symbols section!")
                            print("Sample problematic content:")
                            lines = lib_symbols_content.split('\n')
                            for i, line in enumerate(lines):
                                if "{'value':" in line or '{"value":' in line:
                                    print(f"  Line {i+1}: {line.strip()}")
                                    if i < 3:  # Show first few occurrences
                                        break
                            return False
                        else:
                            print("✅ No dictionary strings found in lib_symbols section!")
                            
                            # Show sample property lines
                            print("Sample property lines:")
                            lines = lib_symbols_content.split('\n')
                            prop_count = 0
                            for line in lines:
                                if '(property ' in line and prop_count < 3:
                                    print(f"  {line.strip()}")
                                    prop_count += 1
                            
                            return True
                else:
                    print("⚠️  No lib_symbols section found")
        
        print("⚠️  No test schematics found to examine")
        return None
        
    except Exception as e:
        print(f"❌ ERROR testing schematic generation: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🚀 Starting Symbol Cache Fix Test")
    
    # Test 1: Symbol parser fix
    parser_success = test_symbol_parser_fix()
    
    # Test 2: Schematic generation
    schematic_success = test_schematic_generation()
    
    print("\n" + "=" * 80)
    print("📋 FINAL RESULTS")
    print("=" * 80)
    print(f"Symbol Parser Fix: {'✅ PASS' if parser_success else '❌ FAIL'}")
    print(f"Schematic Generation: {'✅ PASS' if schematic_success else '❌ FAIL' if schematic_success is not None else '⚠️  SKIP'}")
    
    if parser_success and (schematic_success is None or schematic_success):
        print("\n🎉 OVERALL: Symbol cache fix appears to be working!")
        sys.exit(0)
    else:
        print("\n❌ OVERALL: Symbol cache fix needs more work")
        sys.exit(1)