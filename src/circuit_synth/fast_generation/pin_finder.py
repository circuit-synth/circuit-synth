"""
Pin Finder Tool for Fast Circuit Generation

Programmatic interface to find exact pin names from KiCad component symbols.
Integrates with both OpenRouter and Google ADK workflows.
"""

import os
import sys
import json
from typing import Dict, List, Optional, Tuple, Union
from pathlib import Path

try:
    from circuit_synth.kicad.kicad_symbol_cache import SymbolLibCache
    HAS_SYMBOL_CACHE = True
except ImportError:
    SymbolLibCache = None
    HAS_SYMBOL_CACHE = False


class PinFinder:
    """Find exact pin names for KiCad component symbols"""
    
    def __init__(self):
        self.cache = {}
        
    def find_pins(self, symbol_name: str) -> Dict[str, any]:
        """
        Find pin information for a KiCad symbol
        
        Args:
            symbol_name: KiCad symbol name (e.g., "MCU_Espressif:ESP32-S3")
            
        Returns:
            Dict with pin information and formatted results
        """
        if symbol_name in self.cache:
            return self.cache[symbol_name]
            
        result = {
            "symbol": symbol_name,
            "pins": {},
            "pin_names": [],
            "success": False,
            "error": None,
            "formatted_output": ""
        }
        
        try:
            # First try the KiCad symbol cache
            if HAS_SYMBOL_CACHE:
                try:
                    symbol_data = SymbolLibCache.get_symbol_data(symbol_name)
                    
                    if symbol_data and 'pins' in symbol_data:
                        pins = symbol_data['pins']
                        result["pins"] = pins
                        result["success"] = True
                        result["error"] = "From KiCad symbol cache"
                        
                        # Extract pin names - pins is a list, not dict
                        pin_names = []
                        for pin_info in pins:
                            pin_name = pin_info.get('name', '')
                            pin_number = pin_info.get('number', '')
                            # Use pin number if name is empty or ~
                            if pin_name and pin_name != '~':
                                pin_names.append(pin_name)
                            elif pin_number:
                                pin_names.append(pin_number)
                        
                        result["pin_names"] = sorted(set(pin_names))
                        
                        # Format output for AI consumption
                        result["formatted_output"] = self._format_kicad_pins(symbol_name, pins)
                        
                        return result
                        
                except Exception as cache_error:
                    # Fall through to fallback
                    pass
            
            # Fallback to common pin patterns
            result = self._fallback_pin_detection(symbol_name)
                
        except Exception as e:
            result["error"] = str(e)
            result["formatted_output"] = f"❌ Error finding pins for {symbol_name}: {e}"
        
        # Cache the result
        self.cache[symbol_name] = result
        return result
    
    def _format_pin_info(self, symbol_name: str, pins: Dict) -> str:
        """Format pin information for AI consumption"""
        output = [f"📍 Pin information for {symbol_name}:"]
        output.append("=" * 50)
        
        # Sort pins by number for easier reading
        sorted_pins = sorted(pins.items(), 
                           key=lambda x: int(x[0]) if str(x[0]).isdigit() else float('inf'))
        
        pin_list = []
        for pin_num, pin_info in sorted_pins:
            pin_name = pin_info.get('name', 'Unknown')
            pin_type = pin_info.get('type', 'Unknown')
            output.append(f"Pin {pin_num:>3}: {pin_name:<20} ({pin_type})")
            if pin_name != 'Unknown':
                pin_list.append(pin_name)
        
        # Add circuit-synth usage example
        output.append(f"\n🔧 Circuit-synth usage:")
        output.append(f'component = Component(symbol="{symbol_name}", ref="U1")')
        
        # Show first few pins as examples
        for pin_num, pin_info in list(sorted_pins)[:5]:
            pin_name = pin_info.get('name', 'Unknown')
            if pin_name not in ['Unknown', '']:
                output.append(f'component["{pin_name}"] += some_net  # Pin {pin_num}')
        
        output.append(f"\nAvailable pin names: {', '.join(pin_list[:20])}")
        if len(pin_list) > 20:
            output.append(f"... and {len(pin_list) - 20} more")
            
        return '\n'.join(output)
    
    def _format_kicad_pins(self, symbol_name: str, pins: List) -> str:
        """Format pin information from KiCad symbol cache"""
        output = [f"📍 Real KiCad pins for {symbol_name}:"]
        output.append("=" * 60)
        
        pin_list = []
        for pin_info in pins:
            pin_name = pin_info.get('name', '')
            pin_number = pin_info.get('number', '')
            pin_type = pin_info.get('function', 'unknown')
            
            # Choose display name and add to list
            display_name = pin_name if pin_name and pin_name != '~' else pin_number
            usable_name = display_name
            
            output.append(f"Pin {pin_number:>3}: {display_name:<15} ({pin_type})")
            if usable_name:
                pin_list.append(usable_name)
        
        # Add circuit-synth usage example
        output.append(f"\n🔧 Circuit-synth usage:")
        output.append(f'component = Component(symbol="{symbol_name}", ref="U1")')
        
        # Show first few pins as examples
        for pin_name in pin_list[:5]:
            if pin_name not in ['Unknown', '', 'NC', '~']:
                output.append(f'component["{pin_name}"] += some_net')
        
        output.append(f"\n✅ Available pin names: {', '.join(pin_list[:15])}")
        if len(pin_list) > 15:
            output.append(f"... and {len(pin_list) - 15} more")
            
        return '\n'.join(output)
    
    def _fallback_pin_detection(self, symbol_name: str) -> Dict:
        """Fallback pin detection for common components"""
        result = {
            "symbol": symbol_name,
            "pins": {},
            "pin_names": [],
            "success": False,
            "error": "Using fallback pin detection",
            "formatted_output": ""
        }
        
        # Common pin patterns for known components
        common_pins = {
            "Device:R": ["1", "2"],
            "Device:C": ["1", "2"],  
            "Device:LED": ["A", "K"],  # Anode, Cathode
            "Device:Crystal": ["1", "2", "3", "4"],
            
            # ESP32 patterns (based on common variants)
            "MCU_Espressif:ESP32-S3": [
                "VDD3P3", "VDD3P3_CPU", "VDD3P3_RTC", "GND", "CHIP_PU", "EN",
                "GPIO0", "GPIO1", "GPIO2", "GPIO3", "GPIO4", "GPIO5", "GPIO6", "GPIO7",
                "GPIO8", "GPIO9", "GPIO10", "GPIO11", "GPIO12", "GPIO13", "GPIO14", 
                "GPIO17", "GPIO18", "GPIO19/USB_D-", "GPIO20/USB_D+", "GPIO21",
                "U0TXD", "U0RXD", "XTAL_P", "XTAL_N"
            ],
            
            "RF_Module:ESP32-C6-MINI-1": [
                "3V3", "GND", "EN", "IO0", "IO1", "IO2", "IO3", "IO4", "IO5", 
                "IO6", "IO7", "IO8", "IO9", "IO10", "IO18", "IO19", "IO20", "IO21",
                "TXD0", "RXD0"
            ],
            
            "Sensor_Motion:MPU-6050": [
                "VDD", "GND", "SCL", "SDA", "AD0", "INT", "CLKIN", "CPOUT", 
                "FSYNC", "REGOUT", "VLOGIC", "AUX_CL", "AUX_DA", "NC", "RESV"
            ],
            
            "Connector:USB_C_Receptacle_USB2.0_16P": [
                "A1", "A2", "A3", "A4", "A5", "A6", "A7", "A8", "A9", "A10", "A11", "A12",
                "B1", "B2", "B3", "B4", "B5", "B6", "B7", "B8", "B9", "B10", "B11", "B12",
                "VBUS", "GND", "D+", "D-", "CC1", "CC2", "SBU1", "SBU2", "VCONN", "SHIELD"
            ],
            
            # STM32 patterns
            "MCU_ST_STM32F4:STM32F411CEUx": [
                "VDD", "VSS", "VDDA", "VSSA", "NRST", "BOOT0",
                "PA0", "PA1", "PA2", "PA3", "PA4", "PA5", "PA6", "PA7",
                "PA8", "PA9", "PA10", "PA11", "PA12", "PA13", "PA14", "PA15",
                "PB0", "PB1", "PB2", "PB3", "PB4", "PB5", "PB6", "PB7",
                "PB8", "PB9", "PB10", "PB12", "PB13", "PB14", "PB15",
                "PC13", "PC14", "PC15"
            ]
        }
        
        if symbol_name in common_pins:
            pin_names = common_pins[symbol_name]
            result["pin_names"] = pin_names
            result["success"] = True
            result["error"] = "Using fallback common pin patterns"
            
            # Create formatted output
            output = [f"📍 Common pins for {symbol_name} (fallback):"]
            output.append("=" * 50)
            output.extend(pin_names)
            output.append(f"\n🔧 Circuit-synth usage:")
            output.append(f'component = Component(symbol="{symbol_name}", ref="U1")')
            
            for pin_name in pin_names[:3]:
                output.append(f'component["{pin_name}"] += some_net')
                
            result["formatted_output"] = '\n'.join(output)
        else:
            result["formatted_output"] = f"❌ No fallback pins available for {symbol_name}"
            
        return result
    
    def get_pin_info_for_ai(self, symbol_name: str) -> str:
        """Get pin information formatted for AI context"""
        pin_info = self.find_pins(symbol_name)
        return pin_info["formatted_output"]
    
    def verify_pins_exist(self, symbol_name: str, pin_names: List[str]) -> Tuple[List[str], List[str]]:
        """
        Verify which pins exist for a component
        
        Returns:
            Tuple of (valid_pins, invalid_pins)
        """
        pin_info = self.find_pins(symbol_name)
        
        if not pin_info["success"]:
            return [], pin_names  # All invalid if we can't find the component
            
        available_pins = set(pin_info["pin_names"])
        valid_pins = [pin for pin in pin_names if pin in available_pins]
        invalid_pins = [pin for pin in pin_names if pin not in available_pins]
        
        return valid_pins, invalid_pins


# Global pin finder instance
pin_finder = PinFinder()


def find_component_pins(symbol_name: str) -> Dict:
    """Convenient function to find pins for a component"""
    return pin_finder.find_pins(symbol_name)


def get_ai_pin_context(components: List[str]) -> str:
    """Get pin information for multiple components formatted for AI"""
    context_parts = []
    
    for symbol in components:
        pin_info = pin_finder.get_pin_info_for_ai(symbol)
        context_parts.append(pin_info)
        context_parts.append("")  # Empty line separator
    
    return '\n'.join(context_parts)


# Tool interface compatible with Google ADK
class PinFinderTool:
    """Tool interface for Google ADK integration"""
    
    name = "find_pins"
    description = "Find exact pin names for KiCad component symbols"
    
    def __call__(self, symbol_name: str) -> str:
        """Execute pin finding tool"""
        return pin_finder.get_pin_info_for_ai(symbol_name)
        
    def to_adk_tool(self):
        """Convert to Google ADK tool format"""
        # This would need to be implemented based on actual ADK API
        return {
            "name": self.name,
            "description": self.description,
            "function": self.__call__
        }


# Export the tool for ADK usage
adk_pin_finder_tool = PinFinderTool()