#!/usr/bin/env python3
"""
Daily Example Update Script

Prototype system to update circuit examples with in-stock JLCPCB components.
Focus on STM32 microcontrollers as proof of concept.

Daily workflow:
1. Query JLCPCB for STM32G0/STM32G4 families
2. Filter by stock level (>100) and package type (LQFP/TQFP preferred)
3. Validate KiCad symbol+footprint exist
4. Update examples with best matches
5. Generate updated example files
"""

import json
import logging
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple

# Add circuit-synth to path
sys.path.insert(0, str(Path(__file__).parent.parent / "src"))

from circuit_synth.manufacturing.jlcpcb.jlc_web_scraper import JlcWebScraper

logger = logging.getLogger(__name__)

# Component selection priorities
PACKAGE_PRIORITY = {
    "LQFP": 10,  # Preferred - easy to solder
    "TQFP": 8,  # Good - still hand-solderable
    "QFN": 6,  # Acceptable - requires skill
    "UFQFPN": 5,  # Harder to solder
    "BGA": 0,  # Avoid - not hand-solderable
}

PIN_COUNT_PREFERENCE = {
    "ideal_min": 32,  # Minimum pins for useful peripherals
    "ideal_max": 100,  # Maximum for beginner-friendly complexity
    "absolute_max": 144,  # Hard limit
}


class ExampleUpdater:
    """Updates circuit examples with current component availability."""

    def __init__(self):
        self.jlc_scraper = JlcWebScraper(delay_seconds=1.0)
        self.updated_examples = {}

    def find_best_stm32_match(
        self, family: str = "STM32G0", min_stock: int = 100
    ) -> Optional[Dict]:
        """
        Find the best STM32 match based on our selection criteria.

        Args:
            family: STM32 family to search (G0, G4, etc.)
            min_stock: Minimum stock level required

        Returns:
            Best component match or None
        """
        logger.info(f"Searching for {family} components with stock >= {min_stock}")

        # Search JLCPCB web for family
        search_term = family  # Web scraper takes single search term
        candidates = self.jlc_scraper.search_components(search_term, max_results=200)

        if not candidates:
            logger.warning(f"No {family} components found in JLCPCB")
            return None

        logger.info(f"Found {len(candidates)} {family} candidates")

        # Score and filter candidates
        scored_candidates = []
        for component in candidates:
            score = self._score_component(component, min_stock)
            if score > 0:
                scored_candidates.append((component, score))

        if not scored_candidates:
            logger.warning(f"No suitable {family} components after filtering")
            return None

        # Sort by score (descending) and return best
        scored_candidates.sort(key=lambda x: x[1], reverse=True)
        best_component, best_score = scored_candidates[0]

        logger.info(
            f"Best match: {best_component['part_number']} "
            f"(stock: {best_component['stock']}, score: {best_score:.1f})"
        )

        # For prototype, add basic KiCad mapping
        logger.info(f"Adding basic KiCad mapping for prototype")
        self._add_basic_kicad_mapping(best_component)
        return best_component

    def _score_component(self, component: Dict, min_stock: int) -> float:
        """
        Score a component based on our selection criteria.

        Returns:
            Score (0 = reject, higher = better)
        """
        stock = int(component.get("stock", 0))
        package = component.get("package", "").upper()
        part_number = component.get("part_number", "")

        # Must meet minimum stock
        if stock < min_stock:
            return 0.0

        # Extract pin count from part number or package
        pin_count = self._extract_pin_count(part_number, package)
        if not pin_count:
            return 0.0

        # Check pin count preferences
        if pin_count > PIN_COUNT_PREFERENCE["absolute_max"]:
            return 0.0

        # Start with base score from stock level
        if stock >= 10000:
            stock_score = 10.0
        elif stock >= 1000:
            stock_score = 8.0
        elif stock >= 500:
            stock_score = 6.0
        elif stock >= 100:
            stock_score = 4.0
        else:
            stock_score = 0.0

        # Package preference score
        package_score = 0.0
        for pkg_type, score in PACKAGE_PRIORITY.items():
            if pkg_type in package:
                package_score = score
                break

        # Pin count preference score
        ideal_min = PIN_COUNT_PREFERENCE["ideal_min"]
        ideal_max = PIN_COUNT_PREFERENCE["ideal_max"]

        if ideal_min <= pin_count <= ideal_max:
            pin_score = 5.0
        elif pin_count < ideal_min:
            pin_score = 2.0  # Too few pins
        else:
            pin_score = max(0.0, 5.0 - (pin_count - ideal_max) * 0.1)

        total_score = stock_score + package_score + pin_score

        logger.debug(
            f"{part_number}: stock={stock_score:.1f}, pkg={package_score:.1f}, "
            f"pins={pin_score:.1f}, total={total_score:.1f}"
        )

        return total_score

    def _extract_pin_count(self, part_number: str, package: str) -> Optional[int]:
        """Extract pin count from part number or package string."""

        # Try to extract from part number (e.g., STM32G071C8T6 -> look for package hint)
        # STM32 part numbers: family + subfamily + pincount + flash + temp + package

        # Look for common pin count patterns in package name
        pin_patterns = [
            r"(\d+)[-_]?PIN",
            r"[A-Z]+(\d+)",  # LQFP64, TQFP48, etc.
            r"(\d+)$",  # Number at end
        ]

        search_text = f"{part_number} {package}"
        for pattern in pin_patterns:
            match = re.search(pattern, search_text, re.IGNORECASE)
            if match:
                try:
                    pin_count = int(match.group(1))
                    if 16 <= pin_count <= 256:  # Reasonable range
                        return pin_count
                except (ValueError, IndexError):
                    continue

        return None

    def _validate_kicad_compatibility(self, component: Dict) -> bool:
        """
        Validate that component has compatible KiCad symbol and footprint.

        Args:
            component: JLCPCB component data

        Returns:
            True if KiCad compatible, False otherwise
        """
        part_number = component.get("part_number", "")
        package = component.get("package", "")

        # Try to find matching KiCad symbol
        # For STM32, symbols are typically in MCU_ST_STM32xx library
        family_match = re.search(r"STM32([A-Z]\d+)", part_number)
        if not family_match:
            logger.warning(f"Cannot extract STM32 family from {part_number}")
            return False

        family = family_match.group(1)  # e.g., "G0", "G4"

        # Build likely symbol name
        symbol_candidates = [
            f"MCU_ST_STM32{family}:{part_number}",
            f"MCU_ST_STM32{family[0]}x:{part_number}",  # STM32Gx
            f"MCU_ST_STM32:{part_number}",
        ]

        for symbol in symbol_candidates:
            try:
                # For prototype, assume symbol exists and determine footprint
                logger.info(f"Assuming KiCad symbol exists: {symbol}")
                component["kicad_symbol"] = symbol

                # Try to determine footprint
                footprint = self._determine_footprint(package, part_number)
                if footprint:
                    component["kicad_footprint"] = footprint
                    logger.info(f"Determined footprint: {footprint}")
                    return True
                else:
                    logger.warning(f"Could not determine footprint for {package}")
            except Exception as e:
                logger.debug(f"Symbol check failed for {symbol}: {e}")

        logger.warning(f"No KiCad symbol found for {part_number}")
        return False

    def _add_basic_kicad_mapping(self, component: Dict) -> None:
        """Add basic KiCad symbol and footprint mapping for prototype."""
        part_number = component.get("part_number", "")
        package = component.get("package", "")

        # Basic STM32 symbol mapping
        if "STM32G0" in part_number:
            component["kicad_symbol"] = f"MCU_ST_STM32G0:{part_number}"
        elif "STM32G4" in part_number:
            component["kicad_symbol"] = f"MCU_ST_STM32G4:{part_number}"
        else:
            component["kicad_symbol"] = f"MCU_ST_STM32:{part_number}"

        # Basic footprint mapping
        component["kicad_footprint"] = (
            self._determine_footprint(package, part_number)
            or "Package_QFP:LQFP-48_7x7mm_P0.5mm"
        )

    def _determine_footprint(self, package: str, part_number: str) -> Optional[str]:
        """
        Determine KiCad footprint from package information.

        Args:
            package: Package type (e.g., "LQFP-48")
            part_number: Full part number for additional context

        Returns:
            KiCad footprint string or None
        """
        package_upper = package.upper()

        # Common STM32 package mappings
        footprint_mappings = {
            "LQFP-48": "Package_QFP:LQFP-48_7x7mm_P0.5mm",
            "LQFP-64": "Package_QFP:LQFP-64_10x10mm_P0.5mm",
            "LQFP-100": "Package_QFP:LQFP-100_14x14mm_P0.5mm",
            "TQFP-48": "Package_QFP:TQFP-48_7x7mm_P0.5mm",
            "TQFP-64": "Package_QFP:TQFP-64_10x10mm_P0.5mm",
            "QFN-48": "Package_DFN_QFN:QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm",
            "UFQFPN-48": "Package_DFN_QFN:QFN-48-1EP_7x7mm_P0.5mm_EP5.6x5.6mm",
        }

        # Direct mapping first
        for pkg_pattern, footprint in footprint_mappings.items():
            if pkg_pattern in package_upper:
                return footprint

        # Pattern-based matching for variations
        if "LQFP" in package_upper:
            pin_match = re.search(r"(\d+)", package_upper)
            if pin_match:
                pins = int(pin_match.group(1))
                if pins == 32:
                    return "Package_QFP:LQFP-32_7x7mm_P0.8mm"
                elif pins == 48:
                    return "Package_QFP:LQFP-48_7x7mm_P0.5mm"
                elif pins == 64:
                    return "Package_QFP:LQFP-64_10x10mm_P0.5mm"
                elif pins == 100:
                    return "Package_QFP:LQFP-100_14x14mm_P0.5mm"

        return None

    def update_example_file(
        self, example_path: Path, component_updates: Dict[str, Dict]
    ) -> bool:
        """
        Update an example file with new component selections.

        Args:
            example_path: Path to example file
            component_updates: Dict of component type -> updated component data

        Returns:
            True if updated, False if no changes needed
        """
        if not example_path.exists():
            logger.error(f"Example file not found: {example_path}")
            return False

        # Read current file
        with open(example_path, "r") as f:
            content = f.read()

        original_content = content
        updated = False

        # Update STM32 components
        if "stm32" in component_updates:
            stm32_data = component_updates["stm32"]

            # Replace symbol reference
            old_symbol_pattern = r'symbol="[^"]*STM32[^"]*"'
            new_symbol = f'symbol="{stm32_data["kicad_symbol"]}"'
            content = re.sub(old_symbol_pattern, new_symbol, content)

            # Replace footprint reference
            old_footprint_pattern = r'footprint="[^"]*Package_[^"]*"'
            new_footprint = f'footprint="{stm32_data["kicad_footprint"]}"'
            content = re.sub(old_footprint_pattern, new_footprint, content)

            # Update comments with stock info
            stock_info = f" # Stock: {stm32_data['stock']} units (LCSC: {stm32_data.get('lcsc_part', 'N/A')})"
            content = re.sub(
                r'(symbol="[^"]*STM32[^"]*"[^#\n]*)', r"\1" + stock_info, content
            )

            updated = True

        # Write updated file if changes made
        if updated and content != original_content:
            # Create backup
            backup_path = example_path.with_suffix(".py.backup")
            with open(backup_path, "w") as f:
                f.write(original_content)

            # Write updated content
            with open(example_path, "w") as f:
                f.write(content)

            logger.info(f"Updated {example_path}")
            return True
        else:
            logger.info(f"No updates needed for {example_path}")
            return False

    def generate_update_report(self, updates: Dict) -> str:
        """Generate a summary report of all updates made."""

        report = [
            "# Daily Example Update Report",
            f"Generated: {__import__('datetime').datetime.now().isoformat()}",
            "",
        ]

        for component_type, data in updates.items():
            report.extend(
                [
                    f"## {component_type.upper()} Updates",
                    f"- **Part**: {data.get('part_number', 'N/A')}",
                    f"- **Stock**: {data.get('stock', 0):,} units",
                    f"- **Package**: {data.get('package', 'N/A')}",
                    f"- **LCSC**: {data.get('lcsc_part', 'N/A')}",
                    f"- **Symbol**: `{data.get('kicad_symbol', 'N/A')}`",
                    f"- **Footprint**: `{data.get('kicad_footprint', 'N/A')}`",
                    "",
                ]
            )

        return "\n".join(report)


def main():
    """Main update workflow."""

    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    updater = ExampleUpdater()

    # Find best STM32G0 match
    logger.info("=== Starting Daily Example Update ===")

    stm32g0_match = updater.find_best_stm32_match("STM32G0", min_stock=100)
    if not stm32g0_match:
        logger.error("No suitable STM32G0 found")
        return

    # Also try STM32G4 for comparison
    stm32g4_match = updater.find_best_stm32_match("STM32G4", min_stock=100)

    # Determine which is better overall
    updates = {"stm32": stm32g0_match}  # Default to G0

    if stm32g4_match:
        g0_score = updater._score_component(stm32g0_match, 100)
        g4_score = updater._score_component(stm32g4_match, 100)

        if g4_score > g0_score:
            logger.info("STM32G4 scored higher, using G4 instead of G0")
            updates["stm32"] = stm32g4_match

    # Update example files
    examples_dir = Path(__file__).parent.parent / "examples" / "agent-training"
    example_files = [
        examples_dir / "microcontrollers" / "01_esp32_minimal.py",
        examples_dir / "microcontrollers" / "02_stm32_with_crystal.py",
        examples_dir / "03_complete_stm32_development_board.py",
        # Add more example files as needed
    ]

    updated_files = []
    for example_file in example_files:
        if example_file.exists():
            if updater.update_example_file(example_file, updates):
                updated_files.append(example_file)

    # Generate report
    report = updater.generate_update_report(updates)
    report_path = Path(__file__).parent.parent / "daily_update_report.md"
    with open(report_path, "w") as f:
        f.write(report)

    logger.info(f"=== Update Complete: {len(updated_files)} files updated ===")
    logger.info(f"Report saved to: {report_path}")

    # Print summary
    for component_type, data in updates.items():
        print(
            f"✅ {component_type.upper()}: {data['part_number']} "
            f"({data['stock']:,} units in stock)"
        )


if __name__ == "__main__":
    main()
