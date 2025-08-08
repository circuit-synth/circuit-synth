#!/usr/bin/env python3
"""
DFM Analyzer with Real DigiKey Pricing
Uses actual supplier data - no estimates or placeholders
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..manufacturing.digikey import search_digikey_components

logger = logging.getLogger(__name__)


@dataclass
class DigiKeyPricing:
    """Real pricing data from DigiKey"""

    digikey_part_number: str
    manufacturer_part_number: str
    manufacturer: str
    description: str
    unit_price: float
    price_breaks: List[Dict[str, float]]  # [{"quantity": 10, "price": 1.23}, ...]
    stock_quantity: int
    lead_time_weeks: Optional[int]
    minimum_order_quantity: int
    packaging: str
    datasheet_url: Optional[str]
    product_url: str
    last_updated: datetime


@dataclass
class ComponentPricingAnalysis:
    """Component analysis with real supplier data"""

    reference: str
    part_number: str
    digikey_pricing: Optional[DigiKeyPricing]
    alternatives: List[DigiKeyPricing] = field(default_factory=list)

    @property
    def has_pricing(self) -> bool:
        """Check if real pricing is available"""
        return self.digikey_pricing is not None

    @property
    def unit_price(self) -> Optional[float]:
        """Get unit price at quantity 1"""
        if self.digikey_pricing:
            return self.digikey_pricing.unit_price
        return None

    def get_price_at_quantity(self, quantity: int) -> Optional[float]:
        """Get best price for given quantity from price breaks"""
        if not self.digikey_pricing or not self.digikey_pricing.price_breaks:
            return self.unit_price

        best_price = self.digikey_pricing.unit_price
        for price_break in self.digikey_pricing.price_breaks:
            if quantity >= price_break["quantity"]:
                best_price = price_break["price"]

        return best_price

    def get_extended_price(self, quantity: int) -> Optional[float]:
        """Get total price for quantity"""
        price = self.get_price_at_quantity(quantity)
        if price:
            return price * quantity
        return None


@dataclass
class BOMPricing:
    """Bill of Materials pricing with real data"""

    total_components: int
    priced_components: int
    missing_components: List[str]

    # Pricing at different quantities
    pricing_tiers: Dict[int, float]  # {10: 123.45, 100: 98.76, ...}

    # Component details
    component_analyses: List[ComponentPricingAnalysis]

    # Metadata
    pricing_date: datetime
    data_source: str = "DigiKey"
    currency: str = "USD"

    @property
    def coverage_percentage(self) -> float:
        """Percentage of components with pricing data"""
        if self.total_components == 0:
            return 0
        return (self.priced_components / self.total_components) * 100

    def get_bom_cost(self, quantity: int) -> Optional[float]:
        """Get total BOM cost at specified quantity"""
        if quantity in self.pricing_tiers:
            return self.pricing_tiers[quantity]

        # Calculate if not in tiers
        total = 0
        components_with_pricing = 0

        for comp in self.component_analyses:
            price = comp.get_price_at_quantity(quantity)
            if price:
                total += price
                components_with_pricing += 1

        if components_with_pricing > 0:
            return total
        return None

    def get_detailed_breakdown(self, quantity: int) -> List[Dict]:
        """Get detailed cost breakdown for each component"""
        breakdown = []

        for comp in self.component_analyses:
            price = comp.get_price_at_quantity(quantity)
            if price:
                breakdown.append(
                    {
                        "reference": comp.reference,
                        "part_number": comp.part_number,
                        "digikey_part": (
                            comp.digikey_pricing.digikey_part_number
                            if comp.digikey_pricing
                            else "N/A"
                        ),
                        "unit_price": price,
                        "extended_price": price,
                        "stock": (
                            comp.digikey_pricing.stock_quantity
                            if comp.digikey_pricing
                            else 0
                        ),
                        "source": "DigiKey" if comp.digikey_pricing else "Not Found",
                    }
                )
            else:
                breakdown.append(
                    {
                        "reference": comp.reference,
                        "part_number": comp.part_number,
                        "digikey_part": "Not Found",
                        "unit_price": None,
                        "extended_price": None,
                        "stock": 0,
                        "source": "Not Found",
                    }
                )

        return breakdown


class RealDataDFMAnalyzer:
    """DFM Analyzer using only real supplier data"""

    def __init__(self):
        """Initialize analyzer with DigiKey integration"""
        self.pricing_cache = {}
        logger.info("Initialized DFM Analyzer with real supplier data requirements")

    def analyze_bom_pricing(
        self, components: Dict[str, Dict], quantity_tiers: List[int] = None
    ) -> BOMPricing:
        """
        Analyze BOM with real DigiKey pricing

        Args:
            components: Dictionary of components with part numbers
            quantity_tiers: List of quantities to price at (default: [1, 10, 100, 1000])

        Returns:
            BOMPricing object with real data only
        """
        if quantity_tiers is None:
            quantity_tiers = [1, 10, 25, 100, 250, 500, 1000]

        logger.info(f"Analyzing BOM pricing for {len(components)} components")

        # Analyze each component
        component_analyses = []
        missing_components = []
        priced_components = 0

        for ref, comp_data in components.items():
            part_number = comp_data.get("part_number", comp_data.get("value", ""))
            manufacturer = comp_data.get("manufacturer", "")

            # Get real pricing from DigiKey
            pricing = self._get_digikey_pricing(part_number, manufacturer)

            analysis = ComponentPricingAnalysis(
                reference=ref, part_number=part_number, digikey_pricing=pricing
            )

            if pricing:
                priced_components += 1
                logger.info(f"✓ Found DigiKey pricing for {ref}: {part_number}")
            else:
                missing_components.append(f"{ref}: {part_number}")
                logger.warning(f"✗ No DigiKey pricing for {ref}: {part_number}")

            component_analyses.append(analysis)

        # Calculate pricing at each tier
        pricing_tiers_dict = {}
        for qty in quantity_tiers:
            total = 0
            count = 0
            for comp in component_analyses:
                price = comp.get_price_at_quantity(qty)
                if price:
                    total += price
                    count += 1

            if count > 0:
                pricing_tiers_dict[qty] = total

        return BOMPricing(
            total_components=len(components),
            priced_components=priced_components,
            missing_components=missing_components,
            pricing_tiers=pricing_tiers_dict,
            component_analyses=component_analyses,
            pricing_date=datetime.now(),
        )

    def _get_digikey_pricing(
        self, part_number: str, manufacturer: str = ""
    ) -> Optional[DigiKeyPricing]:
        """
        Get real pricing from DigiKey API

        Args:
            part_number: Component part number
            manufacturer: Manufacturer name (optional)

        Returns:
            DigiKeyPricing object or None if not found
        """
        # Check cache first
        cache_key = f"{manufacturer}:{part_number}"
        if cache_key in self.pricing_cache:
            return self.pricing_cache[cache_key]

        try:
            # Search DigiKey - combine manufacturer and part number for better results
            search_term = (
                f"{manufacturer} {part_number}" if manufacturer else part_number
            )

            results = search_digikey_components(
                keyword=search_term,
                max_results=3,  # Get a few results to find best match
                in_stock_only=False,  # Include out of stock items too
            )

            if results and len(results) > 0:
                result = results[0]

                # Extract price breaks
                price_breaks = []
                if "price_breaks" in result:
                    for pb in result["price_breaks"]:
                        price_breaks.append(
                            {"quantity": pb["quantity"], "price": pb["unit_price"]}
                        )

                pricing = DigiKeyPricing(
                    digikey_part_number=result.get("digikey_part_number", ""),
                    manufacturer_part_number=result.get(
                        "manufacturer_part_number", part_number
                    ),
                    manufacturer=result.get("manufacturer", manufacturer),
                    description=result.get("description", ""),
                    unit_price=result.get("unit_price", 0),
                    price_breaks=price_breaks,
                    stock_quantity=result.get("quantity_available", 0),
                    lead_time_weeks=result.get("lead_time_weeks"),
                    minimum_order_quantity=result.get("minimum_order_quantity", 1),
                    packaging=result.get("packaging", ""),
                    datasheet_url=result.get("datasheet_url"),
                    product_url=result.get("product_url", ""),
                    last_updated=datetime.now(),
                )

                # Cache the result
                self.pricing_cache[cache_key] = pricing
                return pricing

        except Exception as e:
            logger.error(f"Error fetching DigiKey pricing for {part_number}: {e}")

        return None

    def generate_bom_report(self, bom_pricing: BOMPricing) -> str:
        """Generate a factual BOM report with real pricing"""

        report = []
        report.append("=" * 60)
        report.append("BILL OF MATERIALS - REAL PRICING ANALYSIS")
        report.append("=" * 60)
        report.append(f"Data Source: DigiKey")
        report.append(
            f"Analysis Date: {bom_pricing.pricing_date.strftime('%Y-%m-%d %H:%M:%S')}"
        )
        report.append(f"Currency: {bom_pricing.currency}")
        report.append("")

        # Coverage summary
        report.append("PRICING COVERAGE:")
        report.append(f"  Total Components: {bom_pricing.total_components}")
        report.append(f"  Components with Pricing: {bom_pricing.priced_components}")
        report.append(f"  Coverage: {bom_pricing.coverage_percentage:.1f}%")

        if bom_pricing.missing_components:
            report.append(
                f"\n  Missing Pricing Data ({len(bom_pricing.missing_components)} components):"
            )
            for missing in bom_pricing.missing_components[:10]:  # Show first 10
                report.append(f"    - {missing}")
            if len(bom_pricing.missing_components) > 10:
                report.append(
                    f"    ... and {len(bom_pricing.missing_components) - 10} more"
                )

        report.append("")
        report.append("=" * 60)
        report.append("BOM COST AT DIFFERENT QUANTITIES (DigiKey Pricing)")
        report.append("=" * 60)

        # Pricing table
        report.append(
            f"{'Quantity':<12} {'BOM Cost':<15} {'Unit Cost':<15} {'Data Coverage'}"
        )
        report.append("-" * 60)

        for qty in sorted(bom_pricing.pricing_tiers.keys()):
            bom_cost = bom_pricing.pricing_tiers[qty]
            unit_cost = bom_cost  # For single unit
            coverage = f"{bom_pricing.coverage_percentage:.0f}% of components"

            report.append(
                f"{qty:<12} ${bom_cost:<14.2f} ${unit_cost:<14.2f} {coverage}"
            )

        report.append("")
        report.append("NOTE: Prices shown are for components only (from DigiKey)")
        report.append("      PCB and assembly costs are NOT included")
        report.append(
            "      Only components with available DigiKey pricing are included"
        )

        # Component details
        report.append("")
        report.append("=" * 60)
        report.append("COMPONENT PRICING DETAILS (Qty 1)")
        report.append("=" * 60)

        report.append(
            f"{'Ref':<8} {'Part Number':<20} {'DigiKey P/N':<20} {'Price':<10} {'Stock'}"
        )
        report.append("-" * 80)

        for comp in bom_pricing.component_analyses[:20]:  # Show first 20
            ref = comp.reference[:7]
            part = comp.part_number[:19] if comp.part_number else "N/A"

            if comp.digikey_pricing:
                dk_part = comp.digikey_pricing.digikey_part_number[:19]
                price = f"${comp.digikey_pricing.unit_price:.3f}"
                stock = f"{comp.digikey_pricing.stock_quantity:,}"
            else:
                dk_part = "Not Found"
                price = "N/A"
                stock = "N/A"

            report.append(f"{ref:<8} {part:<20} {dk_part:<20} {price:<10} {stock}")

        if len(bom_pricing.component_analyses) > 20:
            report.append(
                f"... and {len(bom_pricing.component_analyses) - 20} more components"
            )

        report.append("")
        report.append("=" * 60)
        report.append("END OF REPORT - All prices from DigiKey API")
        report.append("=" * 60)

        return "\n".join(report)


def analyze_circuit_with_real_pricing(
    components: Dict[str, Dict], quantities: List[int] = None
) -> Tuple[BOMPricing, str]:
    """
    Convenience function to analyze circuit with real DigiKey pricing

    Args:
        components: Component dictionary
        quantities: List of quantities to analyze

    Returns:
        Tuple of (BOMPricing object, text report)
    """
    analyzer = RealDataDFMAnalyzer()
    bom_pricing = analyzer.analyze_bom_pricing(components, quantities)
    report = analyzer.generate_bom_report(bom_pricing)

    return bom_pricing, report
