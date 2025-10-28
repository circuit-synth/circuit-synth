"""
Power net auto-detection registry.

Scans KiCad power symbol library to build list of known power nets.
Supports automatic conversion of common power nets (GND, VCC, etc.)
to power symbols without explicit user declaration.
"""

import re
from pathlib import Path
from typing import Dict, Set, Optional
from loguru import logger


class PowerNetRegistry:
    """
    Registry of known power net symbols from KiCad library.

    Singleton that scans power.kicad_sym to build mapping of
    net names to power symbol lib_ids.

    Example:
        >>> from circuit_synth.core.power_net_registry import is_power_net, get_power_symbol
        >>> is_power_net("GND")
        True
        >>> get_power_symbol("GND")
        'power:GND'
        >>> is_power_net("DATA_OUT")
        False
    """

    _instance: Optional['PowerNetRegistry'] = None
    _initialized: bool = False

    # Known power nets and their symbols
    _power_symbols: Dict[str, str] = {}

    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance

    def __init__(self):
        if not self._initialized:
            self._discover_power_symbols()
            PowerNetRegistry._initialized = True

    def _discover_power_symbols(self) -> None:
        """
        Scan KiCad power symbol library to build registry.

        Parses power.kicad_sym to extract all power symbol names
        and build mapping of net name -> lib_id.
        """
        logger.debug("Discovering power symbols from KiCad library...")

        # Get power library path
        power_lib_path = self._find_power_library()
        if not power_lib_path:
            logger.debug("Could not find power.kicad_sym, using built-in defaults")
            self._use_builtin_defaults()
            return

        # Parse power.kicad_sym
        try:
            with open(power_lib_path, 'r') as f:
                content = f.read()

            # Extract symbol names using regex
            # Pattern: (symbol "SYMBOL_NAME"
            pattern = r'\(symbol\s+"([^"]+)"'
            matches = re.findall(pattern, content)

            for symbol_name in matches:
                # symbol_name is like "+3V3", "GND", "VCC", etc.
                lib_id = f"power:{symbol_name}"

                # Store with exact name
                self._power_symbols[symbol_name] = lib_id

                # Also store common variants
                # e.g., "3V3" -> "power:+3V3", "3.3V" -> "power:+3V3"
                self._add_common_variants(symbol_name, lib_id)

            logger.debug(f"Discovered {len(self._power_symbols)} power symbol mappings")

        except Exception as e:
            logger.warning(f"Error parsing power library: {e}, using built-in defaults")
            self._use_builtin_defaults()

    def _add_common_variants(self, symbol_name: str, lib_id: str) -> None:
        """Add common variants for a power symbol."""
        # For voltage symbols like "+3V3", also accept "3V3", "+3.3V", "3.3V"
        if symbol_name.startswith("+") and "V" in symbol_name:
            # "+3V3" -> "3V3"
            without_plus = symbol_name[1:]
            self._power_symbols[without_plus] = lib_id

            # "+3V3" -> "+3.3V"
            with_decimal = symbol_name.replace("V", ".") + "V"
            self._power_symbols[with_decimal] = lib_id

            # "+3V3" -> "3.3V"
            without_plus_decimal = without_plus.replace("V", ".") + "V"
            self._power_symbols[without_plus_decimal] = lib_id

    def _find_power_library(self) -> Optional[Path]:
        """Find power.kicad_sym in KiCad library paths."""
        # Check common locations
        search_paths = [
            Path("tests/test_data/kicad_symbols/power.kicad_sym"),
            Path("tests/test_data/kicad9/power.kicad_sym"),
            Path("/usr/share/kicad/symbols/power.kicad_sym"),
            Path.home() / ".local/share/kicad/8.0/symbols/power.kicad_sym",
            Path.home() / ".local/share/kicad/9.0/symbols/power.kicad_sym",
            # macOS paths
            Path("/Applications/KiCad/KiCad.app/Contents/SharedSupport/symbols/power.kicad_sym"),
            Path.home() / "Library/Application Support/kicad/8.0/symbols/power.kicad_sym",
            Path.home() / "Library/Application Support/kicad/9.0/symbols/power.kicad_sym",
        ]

        for path in search_paths:
            if path.exists():
                logger.debug(f"Found power library at: {path}")
                return path

        return None

    def _use_builtin_defaults(self) -> None:
        """Fallback to common power symbols if library not found."""
        self._power_symbols = {
            # Ground variants
            "GND": "power:GND",
            "GNDA": "power:GNDA",
            "GNDD": "power:GNDD",
            "GNDPWR": "power:GNDPWR",
            "GNDREF": "power:GNDREF",

            # Positive supplies
            "VCC": "power:VCC",
            "VDD": "power:VDD",
            "VEE": "power:VEE",
            "VSS": "power:VSS",

            # Fixed voltages (exact names)
            "+3V3": "power:+3V3",
            "+5V": "power:+5V",
            "+12V": "power:+12V",
            "+15V": "power:+15V",
            "+24V": "power:+24V",
            "+48V": "power:+48V",

            # Common variants
            "3V3": "power:+3V3",
            "+3.3V": "power:+3V3",
            "3.3V": "power:+3V3",
            "5V": "power:+5V",
            "12V": "power:+12V",
            "15V": "power:+15V",
            "24V": "power:+24V",
            "48V": "power:+48V",

            # Negative voltages
            "-5V": "power:-5V",
            "-12V": "power:-12V",
            "-15V": "power:-15V",

            # Special purpose
            "VBUS": "power:VBUS",
            "VBAT": "power:VBAT",
            "VIN": "power:VIN",
            "VOUT": "power:VOUT",
            "+1V0": "power:+1V0",
            "1V0": "power:+1V0",
            "+1V2": "power:+1V2",
            "1V2": "power:+1V2",
            "+1V8": "power:+1V8",
            "1V8": "power:+1V8",
            "+2V5": "power:+2V5",
            "2V5": "power:+2V5",
        }

        logger.debug(f"Using {len(self._power_symbols)} built-in power symbol mappings")

    def is_power_net(self, net_name: str) -> bool:
        """
        Check if net name matches a known power symbol.

        Args:
            net_name: Net name to check (e.g., "GND", "VCC", "+3V3")

        Returns:
            True if net_name is a known power net, False otherwise

        Example:
            >>> registry.is_power_net("GND")
            True
            >>> registry.is_power_net("DATA_OUT")
            False
        """
        return net_name in self._power_symbols

    def get_power_symbol(self, net_name: str) -> Optional[str]:
        """
        Get power symbol lib_id for net name.

        Args:
            net_name: Net name (e.g., "GND", "+3V3")

        Returns:
            Power symbol lib_id (e.g., "power:GND") or None if not a power net

        Example:
            >>> registry.get_power_symbol("GND")
            'power:GND'
            >>> registry.get_power_symbol("+3V3")
            'power:+3V3'
            >>> registry.get_power_symbol("DATA_OUT")
            None
        """
        return self._power_symbols.get(net_name)

    def get_all_power_nets(self) -> Set[str]:
        """
        Get set of all known power net names.

        Returns:
            Set of power net names

        Example:
            >>> nets = registry.get_all_power_nets()
            >>> "GND" in nets
            True
            >>> "VCC" in nets
            True
        """
        return set(self._power_symbols.keys())


# Singleton instance
_registry = PowerNetRegistry()


def is_power_net(net_name: str) -> bool:
    """
    Check if net name is a known power net.

    Args:
        net_name: Net name to check

    Returns:
        True if net_name matches a known power symbol

    Example:
        >>> is_power_net("GND")
        True
        >>> is_power_net("+3V3")
        True
        >>> is_power_net("DATA")
        False
    """
    return _registry.is_power_net(net_name)


def get_power_symbol(net_name: str) -> Optional[str]:
    """
    Get power symbol for net name.

    Args:
        net_name: Net name

    Returns:
        Power symbol lib_id or None

    Example:
        >>> get_power_symbol("GND")
        'power:GND'
        >>> get_power_symbol("VCC")
        'power:VCC'
    """
    return _registry.get_power_symbol(net_name)


def get_all_power_nets() -> Set[str]:
    """
    Get all known power net names.

    Returns:
        Set of power net names
    """
    return _registry.get_all_power_nets()
