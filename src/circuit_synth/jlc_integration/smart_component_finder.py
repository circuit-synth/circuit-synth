#!/usr/bin/env python3
"""
Smart Component Finder for Circuit-Synth

Provides intelligent component recommendations by combining JLCPCB availability
with KiCad symbol verification. Makes it effortless for users to find and use
manufacturable components in their designs.
"""

import logging
from dataclasses import dataclass
from typing import Any, Dict, List, Optional, Tuple

from .jlc_web_scraper import get_component_availability_web, search_jlc_components_web

logger = logging.getLogger(__name__)


@dataclass
class ComponentRecommendation:
    """A complete component recommendation with all necessary information."""

    # JLCPCB Information
    jlc_part_number: str
    manufacturer_part: str
    manufacturer: str
    description: str
    stock_quantity: int
    price: str
    library_type: str

    # KiCad Integration
    kicad_symbol: str
    kicad_footprint: str
    symbol_verified: bool
    footprint_verified: bool

    # Circuit-Synth Ready
    circuit_synth_code: str
    manufacturability_score: float
    recommendation_notes: str


class SmartComponentFinder:
    """
    Intelligent component finder that combines JLCPCB data with KiCad compatibility.

    Makes it incredibly easy for users to find manufacturable components.
    """

    def __init__(self):
        """Initialize the smart component finder."""
        self._symbol_mappings = self._load_symbol_mappings()
        self._footprint_mappings = self._load_footprint_mappings()

    def find_components(
        self,
        search_term: str,
        package_preference: Optional[str] = None,
        min_stock: int = 1000,
        max_results: int = 5,
    ) -> List[ComponentRecommendation]:
        """
        Find the best components matching criteria with full KiCad integration.

        Args:
            search_term: Component type (e.g., "STM32G4", "LM358", "USB-C")
            package_preference: Preferred package (e.g., "LQFP", "SOIC", "0603")
            min_stock: Minimum stock quantity to consider
            max_results: Maximum recommendations to return

        Returns:
            List of complete component recommendations
        """
        logger.info(f"🔍 Finding components for: {search_term}")

        # Search JLCPCB for available components
        search_terms = [search_term]
        if package_preference:
            search_terms.append(package_preference)

        jlc_components = search_jlc_components_web(
            search_term, max_results=max_results * 3
        )

        recommendations = []
        for component in jlc_components:
            if component.get("stock", 0) < min_stock:
                continue

            # Create recommendation with KiCad integration
            recommendation = self._create_recommendation(component)
            if recommendation:
                recommendations.append(recommendation)

            if len(recommendations) >= max_results:
                break

        # Sort by manufacturability score
        recommendations.sort(key=lambda x: x.manufacturability_score, reverse=True)

        logger.info(f"✅ Found {len(recommendations)} suitable components")
        return recommendations

    def get_best_component(
        self, search_term: str, package_preference: Optional[str] = None
    ) -> Optional[ComponentRecommendation]:
        """
        Get the single best component recommendation.

        Args:
            search_term: Component type to search for
            package_preference: Preferred package type

        Returns:
            Best component recommendation or None
        """
        recommendations = self.find_components(
            search_term, package_preference, max_results=1
        )
        return recommendations[0] if recommendations else None

    def find_alternatives(
        self, primary_part: str, max_alternatives: int = 3
    ) -> List[ComponentRecommendation]:
        """
        Find alternative components similar to the primary part.

        Args:
            primary_part: Primary component part number
            max_alternatives: Maximum alternatives to find

        Returns:
            List of alternative component recommendations
        """
        # Extract component family from part number for alternative search
        family = self._extract_component_family(primary_part)
        if not family:
            return []

        return self.find_components(family, max_results=max_alternatives)

    def _create_recommendation(
        self, jlc_component: Dict[str, Any]
    ) -> Optional[ComponentRecommendation]:
        """Create a complete recommendation from JLC component data."""
        try:
            part_number = jlc_component.get("part_number", "Unknown")

            # Find matching KiCad symbol and footprint
            symbol_info = self._find_kicad_symbol(jlc_component)
            footprint_info = self._find_kicad_footprint(jlc_component)

            if not symbol_info or not footprint_info:
                logger.debug(f"Skipping {part_number} - missing KiCad components")
                return None

            # Calculate manufacturability score
            score = self._calculate_score(jlc_component)

            # Generate circuit-synth code
            circuit_code = self._generate_circuit_synth_code(
                jlc_component, symbol_info, footprint_info
            )

            # Create recommendation notes
            notes = self._generate_recommendation_notes(jlc_component, score)

            return ComponentRecommendation(
                jlc_part_number=jlc_component.get("lcsc_part", "Unknown"),
                manufacturer_part=part_number,
                manufacturer=jlc_component.get("manufacturer", "Unknown"),
                description=jlc_component.get("description", ""),
                stock_quantity=jlc_component.get("stock", 0),
                price=jlc_component.get("price", "N/A"),
                library_type=jlc_component.get("library_type", "Extended"),
                kicad_symbol=symbol_info["symbol"],
                kicad_footprint=footprint_info["footprint"],
                symbol_verified=symbol_info["verified"],
                footprint_verified=footprint_info["verified"],
                circuit_synth_code=circuit_code,
                manufacturability_score=score,
                recommendation_notes=notes,
            )

        except Exception as e:
            logger.error(f"Error creating recommendation: {e}")
            return None

    def _find_kicad_symbol(self, component: Dict[str, Any]) -> Optional[Dict[str, Any]]:
        """Find appropriate KiCad symbol for component."""
        part_number = component.get("part_number", "")
        description = component.get("description", "")

        # Try to match using part family and description
        for pattern, symbol_info in self._symbol_mappings.items():
            if (
                pattern.lower() in part_number.lower()
                or pattern.lower() in description.lower()
            ):
                return {
                    "symbol": symbol_info["symbol"],
                    "verified": symbol_info.get("verified", True),
                }

        # Default fallback based on common patterns
        return self._guess_symbol_from_description(description)

    def _find_kicad_footprint(
        self, component: Dict[str, Any]
    ) -> Optional[Dict[str, Any]]:
        """Find appropriate KiCad footprint for component."""
        package = component.get("package", "")

        # Try exact package match first
        for pattern, footprint_info in self._footprint_mappings.items():
            if pattern.lower() in package.lower():
                return {
                    "footprint": footprint_info["footprint"],
                    "verified": footprint_info.get("verified", True),
                }

        # Fallback to package type guessing
        return self._guess_footprint_from_package(package)

    def _generate_circuit_synth_code(
        self,
        component: Dict[str, Any],
        symbol_info: Dict[str, Any],
        footprint_info: Dict[str, Any],
    ) -> str:
        """Generate ready-to-use circuit-synth code."""
        part_number = component.get("part_number", "Unknown")
        symbol = symbol_info["symbol"]
        footprint = footprint_info["footprint"]

        # Determine appropriate reference designator
        ref_designator = self._get_reference_designator(symbol)

        # Generate component value if applicable
        value_line = ""
        if self._is_passive_component(symbol):
            value = self._extract_component_value(component)
            if value:
                value_line = f'\n    value="{value}",'

        code = f"""# {part_number} - {component.get('stock', 0)} units in stock
# LCSC: {component.get('lcsc_part', 'N/A')} | Price: {component.get('price', 'N/A')}
component = Component(
    symbol="{symbol}",
    ref="{ref_designator}",{value_line}
    footprint="{footprint}"
)"""

        return code

    def _calculate_score(self, component: Dict[str, Any]) -> float:
        """Calculate manufacturability score for component."""
        stock = component.get("stock", 0)
        library_type = component.get("library_type", "").lower()

        # Base score from stock
        if stock >= 10000:
            stock_score = 1.0
        elif stock >= 5000:
            stock_score = 0.9
        elif stock >= 1000:
            stock_score = 0.8
        elif stock >= 100:
            stock_score = 0.6
        elif stock > 0:
            stock_score = 0.4
        else:
            stock_score = 0.0

        # Library type bonus
        library_bonus = 0.0
        if "basic" in library_type:
            library_bonus = 0.2
        elif "preferred" in library_type:
            library_bonus = 0.1

        return min(1.0, stock_score + library_bonus)

    def _generate_recommendation_notes(
        self, component: Dict[str, Any], score: float
    ) -> str:
        """Generate helpful notes for the recommendation."""
        notes = []

        stock = component.get("stock", 0)
        if stock >= 10000:
            notes.append("✅ High stock availability")
        elif stock >= 1000:
            notes.append("⚠️ Medium stock - consider ordering soon")
        else:
            notes.append("🔶 Low stock - verify availability before production")

        library_type = component.get("library_type", "").lower()
        if "basic" in library_type:
            notes.append("🎯 Basic part - optimal for assembly")
        elif "preferred" in library_type:
            notes.append("👍 Preferred part - good for assembly")

        price = component.get("price", "")
        if price and "$" in price:
            notes.append(f"💰 Price: {price}")

        return " | ".join(notes)

    def _load_symbol_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Load mappings from component types to KiCad symbols."""
        return {
            # Microcontrollers
            "STM32F0": {"symbol": "MCU_ST_STM32F0:STM32F030C8Tx", "verified": True},
            "STM32F1": {"symbol": "MCU_ST_STM32F1:STM32F103C8Tx", "verified": True},
            "STM32F4": {"symbol": "MCU_ST_STM32F4:STM32F407VETx", "verified": True},
            "STM32G0": {"symbol": "MCU_ST_STM32G0:STM32G030C8Tx", "verified": True},
            "STM32G4": {"symbol": "MCU_ST_STM32G4:STM32G431CBTx", "verified": True},
            "ESP32": {"symbol": "RF_Module:ESP32-S3-MINI-1", "verified": True},
            "ATmega": {
                "symbol": "MCU_Microchip_ATmega:ATmega328P-PU",
                "verified": True,
            },
            # Analog ICs
            "LM358": {"symbol": "Amplifier_Operational:LM358", "verified": True},
            "LM324": {"symbol": "Amplifier_Operational:LM324", "verified": True},
            "TL074": {"symbol": "Amplifier_Operational:TL074", "verified": True},
            # Power Management
            "AMS1117": {"symbol": "Regulator_Linear:AMS1117-3.3", "verified": True},
            "LM1117": {"symbol": "Regulator_Linear:LM1117-3.3", "verified": True},
            "AP1117": {"symbol": "Regulator_Linear:AP1117-15", "verified": True},
            "LM2596": {"symbol": "Regulator_Switching:LM2596S-ADJ", "verified": True},
            # Passive Components
            "resistor": {"symbol": "Device:R", "verified": True},
            "capacitor": {"symbol": "Device:C", "verified": True},
            "inductor": {"symbol": "Device:L", "verified": True},
            "diode": {"symbol": "Device:D", "verified": True},
            "LED": {"symbol": "Device:LED", "verified": True},
            # Connectors
            "USB-C": {"symbol": "Connector:USB_C_Receptacle_USB2.0", "verified": True},
            "USB": {"symbol": "Connector:USB_B_Micro", "verified": True},
            "header": {"symbol": "Connector_Generic:Conn_01x02_Male", "verified": True},
        }

    def _load_footprint_mappings(self) -> Dict[str, Dict[str, Any]]:
        """Load mappings from package types to KiCad footprints."""
        return {
            # IC Packages
            "LQFP-48": {
                "footprint": "Package_QFP:LQFP-48_7x7mm_P0.5mm",
                "verified": True,
            },
            "LQFP-64": {
                "footprint": "Package_QFP:LQFP-64_10x10mm_P0.5mm",
                "verified": True,
            },
            "LQFP-100": {
                "footprint": "Package_QFP:LQFP-100_14x14mm_P0.5mm",
                "verified": True,
            },
            "QFN-28": {
                "footprint": "Package_DFN_QFN:QFN-28_4x4mm_P0.4mm",
                "verified": True,
            },
            "QFN-32": {
                "footprint": "Package_DFN_QFN:QFN-32_5x5mm_P0.5mm",
                "verified": True,
            },
            "SOIC-8": {
                "footprint": "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
                "verified": True,
            },
            "SOIC-14": {
                "footprint": "Package_SO:SOIC-14_3.9x8.7mm_P1.27mm",
                "verified": True,
            },
            "SOT-23": {"footprint": "Package_TO_SOT_SMD:SOT-23", "verified": True},
            "SOT-223": {
                "footprint": "Package_TO_SOT_SMD:SOT-223-3_TabPin2",
                "verified": True,
            },
            # Passive Component Packages
            "0603": {"footprint": "Resistor_SMD:R_0603_1608Metric", "verified": True},
            "0805": {"footprint": "Resistor_SMD:R_0805_2012Metric", "verified": True},
            "1206": {"footprint": "Resistor_SMD:R_1206_3216Metric", "verified": True},
            # Connectors
            "USB-C": {
                "footprint": "Connector_USB:USB_C_Receptacle_Palconn_UTC16-G",
                "verified": True,
            },
            "Micro-USB": {
                "footprint": "Connector_USB:USB_Micro-B_Molex_47346-0001",
                "verified": True,
            },
        }

    def _guess_symbol_from_description(
        self, description: str
    ) -> Optional[Dict[str, Any]]:
        """Attempt to guess appropriate symbol from component description."""
        desc_lower = description.lower()

        if "microcontroller" in desc_lower or "mcu" in desc_lower:
            return {"symbol": "MCU_Generic:Generic_Microcontroller", "verified": False}
        elif "operational amplifier" in desc_lower or "opamp" in desc_lower:
            return {"symbol": "Amplifier_Operational:Generic_Op_Amp", "verified": False}
        elif "regulator" in desc_lower:
            return {"symbol": "Regulator_Linear:Generic_Regulator", "verified": False}
        elif "resistor" in desc_lower:
            return {"symbol": "Device:R", "verified": True}
        elif "capacitor" in desc_lower:
            return {"symbol": "Device:C", "verified": True}

        return None

    def _guess_footprint_from_package(self, package: str) -> Optional[Dict[str, Any]]:
        """Attempt to guess appropriate footprint from package string."""
        package_lower = package.lower()

        if "lqfp" in package_lower and "48" in package_lower:
            return {"footprint": "Package_QFP:LQFP-48_7x7mm_P0.5mm", "verified": False}
        elif "soic" in package_lower and "8" in package_lower:
            return {
                "footprint": "Package_SO:SOIC-8_3.9x4.9mm_P1.27mm",
                "verified": False,
            }
        elif "0603" in package_lower:
            return {"footprint": "Resistor_SMD:R_0603_1608Metric", "verified": False}
        elif "0805" in package_lower:
            return {"footprint": "Resistor_SMD:R_0805_2012Metric", "verified": False}

        return None

    def _get_reference_designator(self, symbol: str) -> str:
        """Get appropriate reference designator for component type."""
        symbol_lower = symbol.lower()

        if "mcu" in symbol_lower or "microcontroller" in symbol_lower:
            return "U"
        elif "amplifier" in symbol_lower or "regulator" in symbol_lower:
            return "U"
        elif ":r" in symbol_lower or "resistor" in symbol_lower:
            return "R"
        elif ":c" in symbol_lower or "capacitor" in symbol_lower:
            return "C"
        elif ":l" in symbol_lower or "inductor" in symbol_lower:
            return "L"
        elif "diode" in symbol_lower or "led" in symbol_lower:
            return "D"
        elif "connector" in symbol_lower:
            return "J"
        else:
            return "U"  # Default to U for ICs

    def _is_passive_component(self, symbol: str) -> bool:
        """Check if component is passive and needs a value."""
        passive_types = ["Device:R", "Device:C", "Device:L"]
        return any(ptype in symbol for ptype in passive_types)

    def _extract_component_value(self, component: Dict[str, Any]) -> Optional[str]:
        """Extract component value from description."""
        description = component.get("description", "")

        # Look for common value patterns
        import re

        # Resistor values (10K, 1.2K, 470R, etc.)
        resistor_match = re.search(r"(\d+\.?\d*[kKmM]?[Ωohm]*)", description)
        if resistor_match and (
            "resistor" in description.lower() or "ohm" in description.lower()
        ):
            return resistor_match.group(1)

        # Capacitor values (10uF, 100pF, etc.)
        cap_match = re.search(r"(\d+\.?\d*[upnm]?F)", description)
        if cap_match and "capacitor" in description.lower():
            return cap_match.group(1)

        return None

    def _extract_component_family(self, part_number: str) -> Optional[str]:
        """Extract component family from part number for alternative search."""
        # Remove package and variant suffixes to get base family
        import re

        # STM32G431CBT6 -> STM32G4
        stm32_match = re.match(r"(STM32[A-Z]\d+)", part_number)
        if stm32_match:
            return stm32_match.group(1)[:7]  # STM32G4

        # LM358N -> LM358
        analog_match = re.match(r"([A-Z]{2,3}\d{3,4})", part_number)
        if analog_match:
            return analog_match.group(1)

        return None


# Convenience functions for easy use
def find_component(
    search_term: str, package_preference: Optional[str] = None
) -> Optional[ComponentRecommendation]:
    """
    Find the best component matching criteria.

    Args:
        search_term: Component type (e.g., "STM32G4", "LM358")
        package_preference: Preferred package (e.g., "LQFP", "SOIC")

    Returns:
        Best component recommendation with full integration details
    """
    finder = SmartComponentFinder()
    return finder.get_best_component(search_term, package_preference)


def find_components(
    search_term: str, package_preference: Optional[str] = None, max_results: int = 5
) -> List[ComponentRecommendation]:
    """
    Find multiple components matching criteria.

    Args:
        search_term: Component type
        package_preference: Preferred package
        max_results: Maximum recommendations

    Returns:
        List of component recommendations
    """
    finder = SmartComponentFinder()
    return finder.find_components(
        search_term, package_preference, max_results=max_results
    )


def print_component_recommendation(recommendation: ComponentRecommendation) -> None:
    """Print a nicely formatted component recommendation."""
    print(f"\n🔧 Component Recommendation: {recommendation.manufacturer_part}")
    print(
        f"   📊 Stock: {recommendation.stock_quantity:,} units | Score: {recommendation.manufacturability_score:.2f}/1.0"
    )
    print(f"   💰 Price: {recommendation.price} | Type: {recommendation.library_type}")
    print(f"   📝 {recommendation.description}")
    print(
        f"   ✅ KiCad: {recommendation.kicad_symbol} → {recommendation.kicad_footprint}"
    )
    print(f"   💡 {recommendation.recommendation_notes}")
    print(f"\n📋 Circuit-Synth Code:")
    print(recommendation.circuit_synth_code)


if __name__ == "__main__":
    # Example usage
    print("🔍 Testing Smart Component Finder...")

    # Find an STM32 microcontroller
    stm32_rec = find_component("STM32G4", "LQFP")
    if stm32_rec:
        print_component_recommendation(stm32_rec)

    # Find multiple op-amps
    opamp_recs = find_components("LM358", max_results=3)
    for rec in opamp_recs:
        print_component_recommendation(rec)
