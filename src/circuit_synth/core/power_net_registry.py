"""
Power net auto-detection registry.

Scans KiCad power symbol library to build list of known power nets.
Supports automatic conversion of common power nets (GND, VCC, etc.)
to power symbols without explicit user declaration.
"""

import os
import re
from pathlib import Path
from typing import Dict, List, Optional, Set

from loguru import logger


def _sorted_kicad_version_dirs(kicad_root: Path) -> List[Path]:
    """Return versioned KiCad dirs under ``kicad_root``, newest first.

    Matches children named like ``8.0``, ``9.0``, ``10.0`` and sorts numerically
    descending. Avoids hardcoding version numbers so future KiCad releases are
    discovered automatically.
    """
    if not kicad_root.is_dir():
        return []
    versioned = []
    for child in kicad_root.iterdir():
        if child.is_dir() and re.fullmatch(r"\d+(?:\.\d+)*", child.name):
            key = tuple(int(p) for p in child.name.split("."))
            versioned.append((key, child))
    versioned.sort(key=lambda t: t[0], reverse=True)
    return [path for _, path in versioned]


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

    _instance: Optional["PowerNetRegistry"] = None
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

        Parses power.kicad_sym to extract the real power symbol names and builds
        the net-name -> lib_id mapping. Builtin defaults are seeded first as a
        fallback for when the library is not found, then -- when the library IS
        found -- every mapping is validated against it and any entry pointing at a
        symbol this KiCad does not actually provide (e.g. power:VIN/VOUT/VBAT) is
        pruned, so generation never emits an "Unknown library ID: power:*".
        """
        logger.debug("Discovering power symbols from KiCad library...")

        # Start with builtin defaults to ensure common nets are always available
        self._use_builtin_defaults()
        initial_count = len(self._power_symbols)

        # Get power library path
        power_lib_path = self._find_power_library()
        if not power_lib_path:
            logger.debug(
                f"Could not find power.kicad_sym, using {initial_count} built-in defaults only"
            )
            return

        # Parse power.kicad_sym and MERGE with builtin defaults
        try:
            with open(power_lib_path, "r") as f:
                content = f.read()

            # Extract symbol names. The regex also matches per-unit body symbols
            # (e.g. "GND_0_1"); those are internal and never referenced by a
            # lib_id, so keep only the top-level power symbol names. Preserve
            # file order (dedup in place) so variant-collision resolution is
            # deterministic across runs.
            all_matches = re.findall(r'\(symbol\s+"([^"]+)"', content)
            library_symbols = []
            _seen = set()
            for name in all_matches:
                if re.search(r"_\d+_\d+$", name) or name in _seen:
                    continue
                _seen.add(name)
                library_symbols.append(name)
            library_symbol_set = set(library_symbols)

            for symbol_name in library_symbols:
                # symbol_name is like "+3V3", "GND", "VCC", etc.
                lib_id = f"power:{symbol_name}"

                # Store with exact name (may override builtin default)
                self._power_symbols[symbol_name] = lib_id

                # Also store common variants
                # e.g., "3V3" -> "power:+3V3", "3.3V" -> "power:+3V3"
                self._add_common_variants(symbol_name, lib_id)

            # Prune any mapping (builtin default or variant) whose target symbol
            # this library does not provide, so no net can be classified as power
            # only to fail later with "Unknown library ID: power:<name>".
            pruned = [
                net_name
                for net_name, lib_id in self._power_symbols.items()
                if lib_id.split("power:", 1)[-1] not in library_symbol_set
            ]
            for net_name in pruned:
                del self._power_symbols[net_name]

            logger.debug(
                f"Discovered {len(library_symbols)} symbols from KiCad library, "
                f"pruned {len(pruned)} mapping(s) with no matching symbol "
                f"= {len(self._power_symbols)} total mappings"
            )

        except Exception as e:
            logger.warning(
                f"Error parsing power library: {e}, "
                f"using {initial_count} built-in defaults only"
            )

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
        """Find power.kicad_sym in KiCad library paths.

        Discovery order:
        1. KICAD*_SYMBOL_DIR environment variables (any version).
        2. Version-agnostic system locations.
        3. Per-user/per-platform install dirs, globbing every installed KiCad
           version and preferring the newest (so KiCad 10+ is found without a
           code change).
        """
        search_paths = [
            Path("tests/test_data/kicad_symbols/power.kicad_sym"),
            Path("tests/test_data/kicad9/power.kicad_sym"),
        ]

        # 1. Environment variables (KICAD_SYMBOL_DIR, KICAD10_SYMBOL_DIR, ...)
        for env_name, env_val in os.environ.items():
            if env_name.startswith("KICAD") and env_name.endswith("SYMBOL_DIR"):
                for part in env_val.split(os.pathsep):
                    if part:
                        search_paths.append(Path(part) / "power.kicad_sym")

        # 2. Version-agnostic system locations
        search_paths.extend(
            [
                Path("/usr/share/kicad/symbols/power.kicad_sym"),
                Path("/usr/local/share/kicad/symbols/power.kicad_sym"),
                Path(
                    "/Applications/KiCad/KiCad.app/Contents/SharedSupport/"
                    "symbols/power.kicad_sym"
                ),
            ]
        )

        # 3. Versioned install roots, newest first (Linux, macOS, Windows)
        home = Path.home()
        versioned_roots = [
            home / ".local/share/kicad",
            home / "Library/Application Support/kicad",
            Path(os.environ.get("PROGRAMFILES", r"C:\Program Files")) / "KiCad",
        ]
        for root in versioned_roots:
            for versioned in _sorted_kicad_version_dirs(root):
                # Linux/macOS: <root>/<ver>/symbols ; Windows install layout:
                # <PF>/KiCad/<ver>/share/kicad/symbols
                search_paths.append(versioned / "symbols" / "power.kicad_sym")
                search_paths.append(
                    versioned / "share" / "kicad" / "symbols" / "power.kicad_sym"
                )

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
            # Common ground variants (analog/digital/power)
            "AGND": "power:GND",  # Analog ground → use GND symbol
            "DGND": "power:GND",  # Digital ground → use GND symbol
            "PGND": "power:GND",  # Power ground → use GND symbol
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
            # NOTE: VBAT/VIN/VOUT are intentionally NOT here -- KiCad's power
            # library has no such symbol, so classifying them as power nets makes
            # the writer emit an "Unknown library ID: power:VIN" and place nothing.
            # They are signal/IO nets. (If a KiCad version ever ships these
            # symbols, the library scan below re-adds them automatically.)
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
