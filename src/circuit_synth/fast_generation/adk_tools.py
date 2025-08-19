"""
Google ADK Tool Wrappers for Circuit Design
Provides KiCad symbol, footprint, and pin finding tools for Google ADK agents
"""

import subprocess
import os
from typing import Dict, List, Optional
from pathlib import Path

try:
    from google.adk.tools import FunctionTool
    ADK_AVAILABLE = True
except ImportError:
    ADK_AVAILABLE = False
    FunctionTool = None

from .pin_finder import pin_finder


def find_symbol_tool_function(search_term: str) -> str:
    """
    Find KiCad symbols matching the search term
    
    Args:
        search_term: Component name to search for (e.g., "STM32F4", "ESP32")
        
    Returns:
        Formatted string with matching symbols and libraries
    """
    try:
        # Define KiCad symbol paths for different platforms
        symbol_paths = [
            "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols",  # macOS
            "/usr/share/kicad/symbols",  # Linux
            "/usr/local/share/kicad/symbols"  # Linux alternative
        ]
        
        # Find the correct path
        kicad_symbols_path = None
        for path in symbol_paths:
            if os.path.exists(path):
                kicad_symbols_path = path
                break
        
        if not kicad_symbols_path:
            return f"❌ KiCad symbol libraries not found. Checked: {', '.join(symbol_paths)}"
        
        # Step 1: Find library files containing the search term
        cmd = f'find "{kicad_symbols_path}" -name "*.kicad_sym" | xargs grep -l "{search_term}"'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0 or not result.stdout.strip():
            return f"❌ No symbols found containing '{search_term}'"
        
        matching_libraries = result.stdout.strip().split('\n')
        
        # Step 2: Extract specific symbol names from libraries
        output = [f"📍 Found {len(matching_libraries)} libraries containing '{search_term}':"]
        output.append("=" * 60)
        
        for lib_path in matching_libraries:
            lib_name = Path(lib_path).stem  # Remove .kicad_sym extension
            
            # Get symbol names from this library
            symbol_cmd = f'grep -o \'symbol "[^"]*{search_term}[^"]*"\' "{lib_path}" | head -5'
            symbol_result = subprocess.run(symbol_cmd, shell=True, capture_output=True, text=True)
            
            if symbol_result.stdout:
                output.append(f"\nLibrary: {lib_name}")
                symbols = []
                for line in symbol_result.stdout.strip().split('\n'):
                    if 'symbol "' in line:
                        symbol_name = line.split('"')[1]
                        if not symbol_name.endswith(('_0_0', '_0_1', '_1_1')):  # Filter unit variants
                            symbols.append(symbol_name)
                
                for symbol in symbols[:5]:  # Show up to 5 symbols per library
                    output.append(f"  - {lib_name}:{symbol}")
        
        output.append(f"\n🔧 Circuit-synth usage:")
        output.append(f'component = Component(symbol="LibraryName:SymbolName", ref="U1")')
        
        return "\n".join(output)
        
    except Exception as e:
        return f"❌ Error searching for symbols: {e}"


def find_footprint_tool_function(search_term: str) -> str:
    """
    Find KiCad footprints matching the search term
    
    Args:
        search_term: Footprint name to search for (e.g., "LQFP", "0603", "USB_C")
        
    Returns:
        Formatted string with matching footprints and libraries
    """
    try:
        # Define KiCad footprint paths for different platforms
        footprint_paths = [
            "/Applications/KiCad/KiCad.app/Contents/SharedSupport/footprints",  # macOS
            "/usr/share/kicad/footprints",  # Linux
            "/usr/local/share/kicad/footprints"  # Linux alternative
        ]
        
        # Find the correct path
        kicad_footprints_path = None
        for path in footprint_paths:
            if os.path.exists(path):
                kicad_footprints_path = path
                break
        
        if not kicad_footprints_path:
            return f"❌ KiCad footprint libraries not found. Checked: {', '.join(footprint_paths)}"
        
        # Find footprint files containing the search term
        cmd = f'find "{kicad_footprints_path}" -name "*.pretty" -exec find {{}} -name "*{search_term}*" \\;'
        result = subprocess.run(cmd, shell=True, capture_output=True, text=True)
        
        if result.returncode != 0 or not result.stdout.strip():
            return f"❌ No footprints found containing '{search_term}'"
        
        matching_footprints = result.stdout.strip().split('\n')
        
        output = [f"📍 Found {len(matching_footprints)} footprints containing '{search_term}':"]
        output.append("=" * 60)
        
        # Group by library and show footprints
        libraries = {}
        for fp_path in matching_footprints[:20]:  # Limit to 20 results
            path_parts = Path(fp_path).parts
            for i, part in enumerate(path_parts):
                if part.endswith('.pretty'):
                    lib_name = part[:-7]  # Remove .pretty extension
                    fp_name = Path(fp_path).stem  # Remove .kicad_mod extension
                    if lib_name not in libraries:
                        libraries[lib_name] = []
                    libraries[lib_name].append(fp_name)
                    break
        
        for lib_name, footprints in list(libraries.items())[:10]:  # Show up to 10 libraries
            output.append(f"\nLibrary: {lib_name}")
            for fp in footprints[:5]:  # Show up to 5 footprints per library
                output.append(f"  - {lib_name}:{fp}")
        
        output.append(f"\n🔧 Circuit-synth usage:")
        output.append(f'footprint="LibraryName:FootprintName"')
        
        return "\n".join(output)
        
    except Exception as e:
        return f"❌ Error searching for footprints: {e}"


def find_pins_tool_function(symbol_name: str) -> str:
    """
    Find exact pin names for a KiCad component symbol
    
    Args:
        symbol_name: Full symbol name (e.g., "RF_Module:ESP32-S3-WROOM-1")
        
    Returns:
        Formatted string with pin names and usage examples
    """
    try:
        result = pin_finder.get_pin_info_for_ai(symbol_name)
        return result
    except Exception as e:
        return f"❌ Error finding pins for {symbol_name}: {e}"


# Create Google ADK tools if available
def create_adk_tools() -> List:
    """Create Google ADK tools for circuit design"""
    tools = []
    
    if not ADK_AVAILABLE:
        return tools
    
    try:
        # Create find-symbol tool
        find_symbol_tool = FunctionTool(find_symbol_tool_function)
        tools.append(find_symbol_tool)
        
        # Create find-footprint tool
        find_footprint_tool = FunctionTool(find_footprint_tool_function)
        tools.append(find_footprint_tool)
        
        # Create find-pins tool
        find_pins_tool = FunctionTool(find_pins_tool_function)
        tools.append(find_pins_tool)
        
        return tools
        
    except Exception as e:
        print(f"Warning: Could not create ADK tools: {e}")
        return []


# For testing without ADK
if __name__ == "__main__":
    print("Testing ADK tool functions:")
    
    print("\n1. Testing find_symbol_tool_function:")
    result = find_symbol_tool_function("ESP32")
    print(result[:300] + "..." if len(result) > 300 else result)
    
    print("\n2. Testing find_footprint_tool_function:")
    result = find_footprint_tool_function("LQFP")
    print(result[:300] + "..." if len(result) > 300 else result)
    
    print("\n3. Testing find_pins_tool_function:")
    result = find_pins_tool_function("RF_Module:ESP32-S3-WROOM-1")
    print(result[:300] + "..." if len(result) > 300 else result)