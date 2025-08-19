"""
KiCad Symbol Pin Reader

Reads actual pin information directly from KiCad .kicad_sym files.
No hardcoded data - queries the real symbol libraries.
"""

import os
import re
import json
from pathlib import Path
from typing import Dict, List, Optional, Tuple
import logging

logger = logging.getLogger(__name__)


class KiCadSymbolReader:
    """Read pin information directly from KiCad symbol files"""
    
    def __init__(self):
        self.symbol_paths = self._find_kicad_symbol_paths()
        self.cache = {}
        
    def _find_kicad_symbol_paths(self) -> List[Path]:
        """Find KiCad symbol library paths"""
        paths = []
        
        # Common KiCad installation paths
        common_paths = [
            # macOS
            "/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols",
            # Linux
            "/usr/share/kicad/symbols",
            "/usr/local/share/kicad/symbols",
            # Windows
            "C:\\Program Files\\KiCad\\share\\kicad\\symbols",
            "C:\\Program Files (x86)\\KiCad\\share\\kicad\\symbols"
        ]
        
        for path_str in common_paths:
            path = Path(path_str)
            if path.exists() and path.is_dir():
                paths.append(path)
                logger.info(f"Found KiCad symbols at: {path}")
        
        return paths
    
    def find_symbol_file(self, symbol_name: str) -> Optional[Path]:
        """Find the .kicad_sym file containing a specific symbol"""
        if ":" not in symbol_name:
            return None
            
        library_name, component_name = symbol_name.split(":", 1)
        
        # Look for library_name.kicad_sym
        for symbol_path in self.symbol_paths:
            symbol_file = symbol_path / f"{library_name}.kicad_sym"
            if symbol_file.exists():
                # Verify the symbol exists in this file
                if self._symbol_exists_in_file(symbol_file, component_name):
                    return symbol_file
        
        return None
    
    def _symbol_exists_in_file(self, symbol_file: Path, component_name: str) -> bool:
        """Check if a symbol exists in a .kicad_sym file"""
        try:
            content = symbol_file.read_text(encoding='utf-8')
            # Look for symbol definition
            pattern = rf'\(symbol\s+"{re.escape(component_name)}"'
            return bool(re.search(pattern, content))
        except Exception as e:
            logger.warning(f"Error reading {symbol_file}: {e}")
            return False
    
    def read_symbol_pins(self, symbol_name: str) -> Dict[str, any]:
        """Read pin information directly from KiCad symbol file"""
        if symbol_name in self.cache:
            return self.cache[symbol_name]
        
        result = {
            "symbol": symbol_name,
            "pins": {},
            "pin_names": [],
            "success": False,
            "error": None,
            "source": "kicad_file"
        }
        
        symbol_file = self.find_symbol_file(symbol_name)
        if not symbol_file:
            result["error"] = f"Symbol file not found for {symbol_name}"
            self.cache[symbol_name] = result
            return result
        
        try:
            pins = self._parse_pins_from_file(symbol_file, symbol_name.split(":", 1)[1])
            
            if pins:
                result["pins"] = pins
                result["pin_names"] = list(pins.keys())
                result["success"] = True
                logger.info(f"Found {len(pins)} pins for {symbol_name}")
            else:
                result["error"] = f"No pins found in symbol {symbol_name}"
                
        except Exception as e:
            result["error"] = f"Error parsing {symbol_name}: {e}"
            logger.error(f"Error parsing {symbol_name}: {e}")
        
        self.cache[symbol_name] = result
        return result
    
    def _parse_pins_from_file(self, symbol_file: Path, component_name: str) -> Dict[str, str]:
        """Parse pin information from a .kicad_sym file"""
        try:
            content = symbol_file.read_text(encoding='utf-8')
            
            # Find the symbol definition
            symbol_pattern = rf'\(symbol\s+"{re.escape(component_name)}".*?\n(.*?)\n\s*\)\s*$'
            symbol_match = re.search(symbol_pattern, content, re.DOTALL | re.MULTILINE)
            
            if not symbol_match:
                logger.warning(f"Symbol {component_name} not found in {symbol_file}")
                return {}
            
            symbol_content = symbol_match.group(1)
            
            # Find all pin definitions
            pin_pattern = r'\(pin\s+(\w+)\s+(\w+)\s+\(at\s+[^)]+\)\s+\(length\s+[^)]+\)\s*(?:\(name\s+"([^"]+)"\s+[^)]*\))?\s*(?:\(number\s+"([^"]+)"\s+[^)]*\))?'
            
            pins = {}
            for match in re.finditer(pin_pattern, symbol_content):
                pin_type = match.group(1)  # input, output, bidirectional, etc.
                pin_style = match.group(2)  # line, inverted, etc.
                pin_name = match.group(3) if match.group(3) else ""
                pin_number = match.group(4) if match.group(4) else ""
                
                # Use pin_name as key if available, otherwise pin_number
                key = pin_name if pin_name else pin_number
                if key:
                    pins[key] = {
                        "name": pin_name,
                        "number": pin_number,
                        "type": pin_type,
                        "style": pin_style
                    }
            
            return pins
            
        except Exception as e:
            logger.error(f"Error parsing pins from {symbol_file}: {e}")
            return {}
    
    def get_pin_info_for_ai(self, symbol_name: str) -> str:
        """Get formatted pin information for AI consumption"""
        pin_data = self.read_symbol_pins(symbol_name)
        
        if not pin_data["success"]:
            return f"❌ Could not read pins for {symbol_name}: {pin_data['error']}"
        
        pins = pin_data["pins"]
        if not pins:
            return f"❌ No pins found for {symbol_name}"
        
        output = [f"📍 Real KiCad pins for {symbol_name}:"]
        output.append("=" * 60)
        
        # Sort pins by number/name
        sorted_pins = sorted(pins.items())
        
        pin_names = []
        for pin_key, pin_info in sorted_pins:
            pin_name = pin_info["name"] or pin_key
            pin_number = pin_info["number"]
            pin_type = pin_info["type"]
            
            if pin_number:
                output.append(f"  Pin {pin_number:>3}: {pin_name:<15} ({pin_type})")
            else:
                output.append(f"  {pin_name:<18} ({pin_type})")
            
            pin_names.append(pin_name if pin_name else pin_key)
        
        output.append(f"\n🔧 Circuit-synth usage:")
        output.append(f'component = Component(symbol="{symbol_name}", ref="U1")')
        
        # Show examples with actual pin names
        for pin_name in pin_names[:5]:
            if pin_name and pin_name not in ['', 'NC']:
                output.append(f'component["{pin_name}"] += some_net')
        
        output.append(f"\n✅ Available pins: {', '.join(pin_names[:15])}")
        if len(pin_names) > 15:
            output.append(f"    ... and {len(pin_names) - 15} more")
        
        return '\n'.join(output)


# Create global instance
kicad_reader = KiCadSymbolReader()


def read_kicad_pins(symbol_name: str) -> Dict[str, any]:
    """Read pin information from KiCad symbol files"""
    return kicad_reader.read_symbol_pins(symbol_name)


def get_kicad_pin_info(symbol_name: str) -> str:
    """Get formatted pin info for AI from real KiCad files"""
    return kicad_reader.get_pin_info_for_ai(symbol_name)


def find_symbol_in_kicad(library_name: str, component_name: str = None) -> List[str]:
    """Find all symbols in a KiCad library or search for specific component"""
    symbols = []
    
    for symbol_path in kicad_reader.symbol_paths:
        symbol_file = symbol_path / f"{library_name}.kicad_sym"
        if symbol_file.exists():
            try:
                content = symbol_file.read_text(encoding='utf-8')
                
                if component_name:
                    # Search for specific component
                    pattern = rf'\(symbol\s+"{re.escape(component_name)}"'
                    if re.search(pattern, content):
                        symbols.append(f"{library_name}:{component_name}")
                else:
                    # Find all symbols in library
                    pattern = r'\(symbol\s+"([^"]+)"'
                    matches = re.findall(pattern, content)
                    for match in matches:
                        symbols.append(f"{library_name}:{match}")
                        
            except Exception as e:
                logger.warning(f"Error reading {symbol_file}: {e}")
    
    return symbols


if __name__ == "__main__":
    # Test the reader
    test_symbols = [
        "RF_Module:ESP32-C6-MINI-1",
        "Sensor_Motion:MPU-6050",
        "Device:R",
        "MCU_ST_STM32F4:STM32F411CEUx"
    ]
    
    for symbol in test_symbols:
        print(f"\n{'='*60}")
        print(f"Testing: {symbol}")
        print('='*60)
        result = get_kicad_pin_info(symbol)
        print(result)