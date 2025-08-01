#!/usr/bin/env python3
"""
MODM Device Search Integration

Provides intelligent component search using the modm-devices database.
Enables finding microcontrollers by specifications, features, and constraints.
"""

import logging
import sys
from dataclasses import dataclass
from pathlib import Path
from typing import Dict, List, Optional, Set, Tuple

logger = logging.getLogger(__name__)


@dataclass
class MCUSpecification:
    """Microcontroller specification for search filtering."""

    family: Optional[str] = None  # e.g., "stm32", "avr", "nrf", "sam"
    series: Optional[str] = None  # e.g., "g4", "f4", "h7"
    flash_min: Optional[int] = None  # Minimum flash size in KB
    flash_max: Optional[int] = None  # Maximum flash size in KB
    ram_min: Optional[int] = None  # Minimum RAM size in KB
    ram_max: Optional[int] = None  # Maximum RAM size in KB
    package: Optional[str] = None  # e.g., "lqfp", "qfn", "bga"
    pin_count_min: Optional[int] = None
    pin_count_max: Optional[int] = None
    peripherals: Optional[List[str]] = None  # Required peripherals
    temperature_grade: Optional[str] = None  # e.g., "3" (commercial), "6" (industrial)


@dataclass
class MCUSearchResult:
    """Result from MCU search with complete device information."""

    part_number: str
    family: str
    series: str
    flash_size: int  # KB
    ram_size: int  # KB
    package: str
    pin_count: int
    temperature_grade: str
    peripherals: List[str]
    kicad_symbol: Optional[str] = None
    kicad_footprint: Optional[str] = None
    description: str = ""
    availability_score: float = 0.0


class ModmDeviceSearch:
    """
    Intelligent microcontroller search using modm-devices database.

    Provides comprehensive MCU search with specifications filtering,
    peripheral requirements, and manufacturing constraints.
    """

    def __init__(self):
        """Initialize the device search system."""
        self._devices_cache = {}
        self._modm_path = self._find_modm_devices_path()

        if self._modm_path:
            self._load_modm_devices()
        else:
            logger.warning("modm-devices not found - MCU search will be limited")

    def _find_modm_devices_path(self) -> Optional[Path]:
        """Find the modm-devices installation path."""
        # Try relative path first (in our repository)
        repo_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "submodules"
            / "modm-devices"
        )
        if repo_path.exists():
            return repo_path

        # Try alternative path structure (legacy)
        alt_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "src"
            / "external_repos"
            / "modm-devices"
        )
        if alt_path.exists():
            return alt_path

        # Try system installation
        try:
            import modm_devices

            return Path(modm_devices.__file__).parent.parent
        except ImportError:
            pass

        return None

    def _load_modm_devices(self):
        """Load modm-devices module and initialize device database."""
        if not self._modm_path:
            return

        # Add modm-devices to Python path
        sys.path.insert(0, str(self._modm_path))

        try:
            import modm_devices
            from modm_devices import device_file, parser

            # Load device files
            device_files = list(self._modm_path.glob("devices/**/*.xml"))
            device_parser = parser.DeviceParser()

            for xml_file in device_files:
                try:
                    # Parse XML file
                    schema_path = (
                        self._modm_path
                        / "modm_devices"
                        / "resources"
                        / "schema"
                        / "device.xsd"
                    )
                    root_node = parser.Parser.validate_and_parse_xml(
                        str(xml_file), str(schema_path)
                    )

                    # Create device file object
                    dev_file = device_file.DeviceFile(str(xml_file), root_node)

                    # Get devices from file
                    devices = dev_file.get_devices()

                    for device in devices:
                        family = device.identifier["platform"]
                        if family not in self._devices_cache:
                            self._devices_cache[family] = []
                        self._devices_cache[family].append(device)

                except Exception as e:
                    logger.debug(f"Could not parse {xml_file}: {e}")

            logger.info(
                f"Loaded {sum(len(devs) for devs in self._devices_cache.values())} devices from modm-devices"
            )

        except ImportError as e:
            logger.warning(f"Could not import modm-devices: {e}")

    def search_mcus(
        self, spec: MCUSpecification, max_results: int = 10
    ) -> List[MCUSearchResult]:
        """
        Search for microcontrollers matching specifications.

        Args:
            spec: MCU specification for filtering
            max_results: Maximum number of results to return

        Returns:
            List of matching MCU search results
        """
        if not self._devices_cache:
            logger.warning("No device database loaded")
            return []

        results = []

        # Filter by family if specified
        families_to_search = (
            [spec.family] if spec.family else list(self._devices_cache.keys())
        )

        for family in families_to_search:
            if family not in self._devices_cache:
                continue

            for device in self._devices_cache[family]:
                result = self._evaluate_device(device, spec)
                if result:
                    results.append(result)

                if len(results) >= max_results:
                    break

        # Sort by availability score (descending)
        results.sort(key=lambda x: x.availability_score, reverse=True)

        return results[:max_results]

    def _evaluate_device(
        self, device, spec: MCUSpecification
    ) -> Optional[MCUSearchResult]:
        """Evaluate if a device matches the specification."""
        try:
            identifier = device.identifier
            properties = device.properties

            # Extract device information
            part_number = identifier.string
            family = identifier["platform"]

            # Series extraction (e.g., "f3" from STM32F3)
            series = identifier.get("family", "")

            # Get memory information
            flash_size = self._extract_memory_size(properties, "flash")
            ram_size = self._extract_memory_size(properties, "ram")

            # Get package information
            package = identifier.get("package", "")
            pin_count = self._extract_pin_count(properties)

            # Get temperature grade
            temp_grade = identifier.get("temperature", "")

            # Get peripherals
            peripherals = self._extract_peripherals(properties)

            # Apply filters
            if spec.family and family != spec.family:
                return None

            if spec.series and series != spec.series:
                return None

            if spec.flash_min and flash_size < spec.flash_min:
                return None

            if spec.flash_max and flash_size > spec.flash_max:
                return None

            if spec.ram_min and ram_size < spec.ram_min:
                return None

            if spec.ram_max and ram_size > spec.ram_max:
                return None

            if spec.package and spec.package.lower() not in package.lower():
                return None

            if spec.pin_count_min and pin_count < spec.pin_count_min:
                return None

            if spec.pin_count_max and pin_count > spec.pin_count_max:
                return None

            if spec.temperature_grade and temp_grade != spec.temperature_grade:
                return None

            if spec.peripherals:
                # Check if required peripherals are available (case-insensitive, partial match)
                available_peripheral_names = set(p.upper() for p in peripherals)
                for required_peripheral in spec.peripherals:
                    required_upper = required_peripheral.upper()
                    # Check if any available peripheral starts with the required name
                    found = any(
                        p.startswith(required_upper) for p in available_peripheral_names
                    )
                    if not found:
                        return None

            # Calculate availability score
            availability_score = self._calculate_availability_score(
                family, series, flash_size, ram_size, package
            )

            # Find KiCad symbol and footprint
            kicad_symbol, kicad_footprint = self._find_kicad_components(
                part_number, package
            )

            # Create description
            description = f"{family.upper()} {series.upper()} MCU, {flash_size}KB Flash, {ram_size}KB RAM, {package.upper()}"

            return MCUSearchResult(
                part_number=part_number,
                family=family,
                series=series,
                flash_size=flash_size,
                ram_size=ram_size,
                package=package,
                pin_count=pin_count,
                temperature_grade=temp_grade,
                peripherals=peripherals,
                kicad_symbol=kicad_symbol,
                kicad_footprint=kicad_footprint,
                description=description,
                availability_score=availability_score,
            )

        except Exception as e:
            logger.debug(f"Error evaluating device {device.partname}: {e}")
            return None

    def _extract_memory_size(self, properties: dict, memory_type: str) -> int:
        """Extract memory size from device properties."""
        try:
            # Look for memory information in properties
            if "driver" in properties:
                for driver in properties["driver"]:
                    if driver.get("name") == "core" or driver.get("name") == "memory":
                        # Check for memory-related properties
                        for key, value in driver.items():
                            if memory_type in key.lower() and "size" in key.lower():
                                # Extract size value (could be in various formats)
                                if isinstance(value, (int, str)):
                                    return self._parse_memory_value(str(value))

            # Fallback: try to extract from identifier
            # This is device-family specific logic
            return self._extract_memory_from_identifier(properties, memory_type)

        except Exception:
            return 0

    def _parse_memory_value(self, value: str) -> int:
        """Parse memory value string to KB."""
        value = value.lower().strip()

        if "kb" in value or "k" in value:
            return int("".join(c for c in value if c.isdigit()))
        elif "mb" in value or "m" in value:
            return int("".join(c for c in value if c.isdigit())) * 1024
        else:
            # Assume it's already in KB or bytes
            num = int("".join(c for c in value if c.isdigit()))
            # If it's a very large number, assume it's bytes
            return num // 1024 if num > 10000 else num

    def _extract_memory_from_identifier(
        self, properties: dict, memory_type: str
    ) -> int:
        """Extract memory size from device identifier (family-specific)."""
        # This would need device-family specific logic
        # For now, return a default value
        return 128 if memory_type == "flash" else 32

    def _extract_pin_count(self, properties: dict) -> int:
        """Extract pin count from device properties."""
        try:
            # Look for GPIO or pin information
            if "driver" in properties:
                for driver in properties["driver"]:
                    if driver.get("name") == "gpio":
                        # Count GPIO pins
                        gpio_count = 0
                        if "gpio" in driver:
                            for gpio in driver["gpio"]:
                                if isinstance(gpio, dict) and "port" in gpio:
                                    gpio_count += len(gpio.get("pin", []))
                        return gpio_count

            # Fallback to default based on package
            return 64

        except Exception:
            return 64

    def _extract_peripherals(self, properties: dict) -> List[str]:
        """Extract available peripherals from device properties."""
        peripherals = []

        try:
            if "driver" in properties:
                for driver in properties["driver"]:
                    name = driver.get("name", "")
                    if name and name != "core" and name != "gpio":
                        # Check for instances
                        if "instance" in driver:
                            instances = driver["instance"]
                            if isinstance(instances, list):
                                # Instances can be strings or dicts
                                for instance in instances:
                                    if isinstance(instance, str):
                                        peripherals.append(f"{name.upper()}{instance}")
                                    elif (
                                        isinstance(instance, dict)
                                        and "name" in instance
                                    ):
                                        peripherals.append(
                                            f"{name.upper()}{instance['name']}"
                                        )
                            elif isinstance(instances, dict) and "name" in instances:
                                peripherals.append(f"{name.upper()}{instances['name']}")
                            elif isinstance(instances, str):
                                peripherals.append(f"{name.upper()}{instances}")
                        else:
                            # No instances, just add the peripheral name
                            peripherals.append(name.upper())
        except Exception:
            pass

        return sorted(set(peripherals))

    def _calculate_availability_score(
        self, family: str, series: str, flash: int, ram: int, package: str
    ) -> float:
        """Calculate availability score for the device."""
        score = 0.5  # Base score

        # Popular families get higher scores
        popular_families = ["stm32", "sam", "nrf"]
        if family in popular_families:
            score += 0.2

        # Popular series get higher scores
        popular_series = ["f4", "g4", "l4", "h7"]
        if series in popular_series:
            score += 0.1

        # Common memory sizes get higher scores
        if 64 <= flash <= 512:
            score += 0.1
        if 16 <= ram <= 128:
            score += 0.1

        # Common packages get higher scores
        common_packages = ["lqfp", "qfn", "soic"]
        if any(pkg in package.lower() for pkg in common_packages):
            score += 0.1

        return min(1.0, score)

    def _find_kicad_components(
        self, part_number: str, package: str
    ) -> Tuple[Optional[str], Optional[str]]:
        """Find appropriate KiCad symbol and footprint."""
        family = part_number[:5].upper()  # e.g., STM32

        # Map to KiCad symbols
        symbol_map = {
            "STM32": "MCU_ST_STM32G4:STM32G431CBTx",  # Generic STM32
            "ATMEG": "MCU_Microchip_ATmega:ATmega328P-PU",
            "NRF52": "RF_Module:nRF52832-CIAA",
            "SAMD2": "MCU_Microchip_SAMD:SAMD21E18A-AU",
        }

        symbol = None
        for prefix, sym in symbol_map.items():
            if part_number.upper().startswith(prefix):
                symbol = sym
                break

        # Map to KiCad footprints
        footprint = None
        package_lower = package.lower()
        if "lqfp" in package_lower:
            if "48" in package_lower:
                footprint = "Package_QFP:LQFP-48_7x7mm_P0.5mm"
            elif "64" in package_lower:
                footprint = "Package_QFP:LQFP-64_10x10mm_P0.5mm"
        elif "qfn" in package_lower:
            if "32" in package_lower:
                footprint = "Package_DFN_QFN:QFN-32_5x5mm_P0.5mm"

        return symbol, footprint

    def get_available_families(self) -> List[str]:
        """Get list of available MCU families."""
        return list(self._devices_cache.keys())

    def get_family_series(self, family: str) -> List[str]:
        """Get available series for a specific family."""
        if family not in self._devices_cache:
            return []

        series_set = set()
        for device in self._devices_cache[family]:
            series = device.identifier.get("family", "")
            if series:
                series_set.add(series)

        return sorted(series_set)


# Convenience functions for easy use
def search_stm32(
    series: Optional[str] = None,
    flash_min: Optional[int] = None,
    package: Optional[str] = None,
    max_results: int = 5,
) -> List[MCUSearchResult]:
    """
    Search for STM32 microcontrollers.

    Args:
        series: STM32 series (e.g., "g4", "f4", "h7")
        flash_min: Minimum flash size in KB
        package: Package type preference
        max_results: Maximum results to return

    Returns:
        List of matching STM32 devices
    """
    searcher = ModmDeviceSearch()
    spec = MCUSpecification(
        family="stm32", series=series, flash_min=flash_min, package=package
    )
    return searcher.search_mcus(spec, max_results)


def search_by_peripherals(
    peripherals: List[str], family: Optional[str] = None, max_results: int = 5
) -> List[MCUSearchResult]:
    """
    Search for MCUs by required peripherals.

    Args:
        peripherals: List of required peripherals (e.g., ["USART", "SPI", "I2C"])
        family: MCU family to search in
        max_results: Maximum results to return

    Returns:
        List of matching devices
    """
    searcher = ModmDeviceSearch()
    spec = MCUSpecification(family=family, peripherals=peripherals)
    return searcher.search_mcus(spec, max_results)


def print_mcu_result(result: MCUSearchResult) -> None:
    """Print a nicely formatted MCU search result."""
    print(f"\\n🔧 MCU Recommendation: {result.part_number}")
    print(
        f"   📊 Specs: {result.flash_size}KB Flash, {result.ram_size}KB RAM, {result.pin_count} pins"
    )
    print(
        f"   📦 Package: {result.package} | Score: {result.availability_score:.2f}/1.0"
    )
    print(f"   📝 {result.description}")

    if result.peripherals:
        print(f"   ⚡ Peripherals: {', '.join(result.peripherals[:10])}")
        if len(result.peripherals) > 10:
            print(f"      ... and {len(result.peripherals) - 10} more")

    if result.kicad_symbol:
        print(f"   ✅ KiCad: {result.kicad_symbol} → {result.kicad_footprint}")

    print(f"\\n📋 Circuit-Synth Code:")
    ref = "U"
    symbol = (
        result.kicad_symbol
        or f"MCU_{result.family.upper()}:Generic_{result.family.upper()}"
    )
    footprint = result.kicad_footprint or f"Package_QFP:LQFP-64_10x10mm_P0.5mm"

    print(
        f"""# {result.part_number} - {result.description}
{result.part_number.lower()} = Component(
    symbol="{symbol}",
    ref="{ref}",
    footprint="{footprint}"
)"""
    )


if __name__ == "__main__":
    # Example usage
    print("🔍 Testing MODM Device Search...")

    # Search for STM32G4 series with minimum 128KB flash
    stm32_results = search_stm32(series="g4", flash_min=128, max_results=3)
    for result in stm32_results:
        print_mcu_result(result)

    # Search by peripherals
    peripheral_results = search_by_peripherals(
        ["USART", "SPI"], family="stm32", max_results=2
    )
    for result in peripheral_results:
        print_mcu_result(result)
