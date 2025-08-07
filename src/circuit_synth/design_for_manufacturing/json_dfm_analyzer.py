#!/usr/bin/env python3
"""
JSON-based DFM Analyzer for Circuit-Synth
Processes hierarchical circuit JSON with real supplier data only
"""

import json
import logging
from dataclasses import dataclass, field
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class DFMAnalysisResult:
    """Results from DFM analysis of circuit JSON"""

    # Circuit info
    circuit_name: str
    total_components: int
    unique_components: int
    subcircuit_count: int

    # Technology assessment
    technology_mix: Dict[str, int]  # SMT, THT counts
    assembly_complexity: str  # Low, Medium, High

    # Component pricing (REAL DATA ONLY)
    components_with_pricing: int
    components_without_pricing: List[str]
    pricing_coverage_percent: float
    bom_cost_qty_1: Optional[float]
    bom_cost_qty_100: Optional[float]
    bom_cost_qty_1000: Optional[float]

    # Manufacturing assessment
    manufacturing_issues: List[Dict[str, Any]]
    critical_issues: int
    optimization_opportunities: List[str]

    # Metadata
    analysis_date: str
    data_sources: List[str]

    def to_report(self) -> str:
        """Generate human-readable DFM report"""
        lines = []
        lines.append("=" * 80)
        lines.append("DFM ANALYSIS REPORT - JSON-BASED WORKFLOW")
        lines.append("=" * 80)
        lines.append(f"Circuit: {self.circuit_name}")
        lines.append(f"Analysis Date: {self.analysis_date}")
        lines.append(f"Data Sources: {', '.join(self.data_sources)}")
        lines.append("")

        lines.append("CIRCUIT SUMMARY:")
        lines.append(f"  Total Components: {self.total_components}")
        lines.append(f"  Unique Parts: {self.unique_components}")
        lines.append(f"  Subcircuits: {self.subcircuit_count}")
        lines.append(f"  Assembly Complexity: {self.assembly_complexity}")
        lines.append("")

        lines.append("TECHNOLOGY MIX:")
        for tech, count in self.technology_mix.items():
            percentage = (
                (count / self.total_components * 100)
                if self.total_components > 0
                else 0
            )
            lines.append(f"  {tech}: {count} ({percentage:.1f}%)")
        lines.append("")

        lines.append("COMPONENT PRICING:")
        lines.append(
            f"  Coverage: {self.pricing_coverage_percent:.1f}% ({self.components_with_pricing}/{self.total_components})"
        )

        if self.bom_cost_qty_1:
            lines.append(f"  BOM Cost @ Qty 1: ${self.bom_cost_qty_1:.2f}")
        if self.bom_cost_qty_100:
            lines.append(f"  BOM Cost @ Qty 100: ${self.bom_cost_qty_100:.2f}")
        if self.bom_cost_qty_1000:
            lines.append(f"  BOM Cost @ Qty 1000: ${self.bom_cost_qty_1000:.2f}")

        if not self.bom_cost_qty_1:
            lines.append("  ⚠️  No pricing data available (DigiKey API required)")

        if self.components_without_pricing:
            lines.append(
                f"\n  Missing Pricing ({len(self.components_without_pricing)} components):"
            )
            for comp in self.components_without_pricing[:5]:
                lines.append(f"    - {comp}")
            if len(self.components_without_pricing) > 5:
                lines.append(
                    f"    ... and {len(self.components_without_pricing) - 5} more"
                )
        lines.append("")

        if self.manufacturing_issues:
            lines.append(f"MANUFACTURING ISSUES: {len(self.manufacturing_issues)}")
            if self.critical_issues > 0:
                lines.append(f"  ⚠️  Critical Issues: {self.critical_issues}")
            for issue in self.manufacturing_issues[:3]:
                lines.append(f"  • {issue.get('description', 'Issue')}")
        lines.append("")

        if self.optimization_opportunities:
            lines.append("OPTIMIZATION OPPORTUNITIES:")
            for opp in self.optimization_opportunities[:5]:
                lines.append(f"  • {opp}")

        lines.append("")
        lines.append("NOTE: This analysis uses only verified supplier data.")
        lines.append("      PCB and assembly costs are not included.")

        return "\n".join(lines)


class JSONDFMAnalyzer:
    """Analyzes circuit JSON for DFM with real data requirements"""

    def __init__(self, require_real_data: bool = True):
        """
        Initialize analyzer

        Args:
            require_real_data: If True, only use real supplier data (no estimates)
        """
        self.require_real_data = require_real_data
        self.digikey_client = None

        # Try to import DigiKey client if available
        try:
            from circuit_synth.manufacturing.digikey import search_digikey_components

            self.digikey_search = search_digikey_components
            self.has_digikey = True
        except ImportError:
            self.has_digikey = False
            logger.warning("DigiKey integration not available")

    def analyze_circuit_json(
        self, circuit_json: Dict[str, Any], quantities: List[int] = None
    ) -> DFMAnalysisResult:
        """
        Analyze hierarchical circuit JSON for DFM

        Args:
            circuit_json: Hierarchical circuit data
            quantities: List of quantities for pricing (default: [1, 100, 1000])

        Returns:
            DFMAnalysisResult with all findings
        """
        if quantities is None:
            quantities = [1, 100, 1000]

        logger.info(f"Analyzing circuit: {circuit_json.get('name', 'Unknown')}")

        # Extract basic info
        circuit_name = circuit_json.get("name", "Unknown Circuit")
        components = circuit_json.get("components", {})
        subcircuits = circuit_json.get("subcircuits", {})
        nets = circuit_json.get("nets", {})

        # Calculate statistics
        total_components = len(components)
        unique_values = len(set(c.get("value", "") for c in components.values()))
        subcircuit_count = len(subcircuits)

        # Analyze technology mix
        technology_mix = self._analyze_technology_mix(components)

        # Assess complexity
        complexity = self._assess_assembly_complexity(
            total_components, technology_mix, subcircuit_count
        )

        # Get component pricing (REAL DATA ONLY)
        pricing_results = self._get_real_component_pricing(components, quantities)

        # Identify manufacturing issues
        issues = self._identify_manufacturing_issues(
            components, technology_mix, pricing_results
        )

        # Find optimization opportunities
        opportunities = self._find_optimization_opportunities(
            components, pricing_results, issues
        )

        # Count critical issues
        critical_count = sum(1 for i in issues if i.get("severity") == "CRITICAL")

        # Determine data sources
        data_sources = []
        if self.has_digikey and pricing_results["has_pricing"]:
            data_sources.append("DigiKey API")
        if not data_sources:
            data_sources.append("No supplier data available")

        return DFMAnalysisResult(
            circuit_name=circuit_name,
            total_components=total_components,
            unique_components=unique_values,
            subcircuit_count=subcircuit_count,
            technology_mix=technology_mix,
            assembly_complexity=complexity,
            components_with_pricing=pricing_results["priced_count"],
            components_without_pricing=pricing_results["missing_pricing"],
            pricing_coverage_percent=pricing_results["coverage_percent"],
            bom_cost_qty_1=pricing_results.get("costs", {}).get(1),
            bom_cost_qty_100=pricing_results.get("costs", {}).get(100),
            bom_cost_qty_1000=pricing_results.get("costs", {}).get(1000),
            manufacturing_issues=issues,
            critical_issues=critical_count,
            optimization_opportunities=opportunities,
            analysis_date=datetime.now().isoformat(),
            data_sources=data_sources,
        )

    def _analyze_technology_mix(self, components: Dict[str, Any]) -> Dict[str, int]:
        """Analyze SMT vs THT technology mix"""
        smt_count = 0
        tht_count = 0
        mixed_count = 0

        for comp in components.values():
            footprint = comp.get("footprint", "").lower()

            # SMT indicators
            if any(
                x in footprint
                for x in [
                    "smd",
                    "0402",
                    "0603",
                    "0805",
                    "1206",
                    "soic",
                    "qfp",
                    "qfn",
                    "bga",
                ]
            ):
                smt_count += 1
            # THT indicators
            elif any(
                x in footprint for x in ["tht", "through", "dip", "radial", "axial"]
            ):
                tht_count += 1
            # Default to SMT for unknown
            else:
                smt_count += 1

        return {"SMT": smt_count, "THT": tht_count}

    def _assess_assembly_complexity(
        self,
        total_components: int,
        technology_mix: Dict[str, int],
        subcircuit_count: int,
    ) -> str:
        """Assess assembly complexity based on circuit characteristics"""

        complexity_score = 0

        # Component count factor
        if total_components < 50:
            complexity_score += 1
        elif total_components < 200:
            complexity_score += 2
        else:
            complexity_score += 3

        # Technology mix factor
        if technology_mix.get("THT", 0) > 0 and technology_mix.get("SMT", 0) > 0:
            complexity_score += 1  # Mixed technology adds complexity

        # Subcircuit factor
        if subcircuit_count > 5:
            complexity_score += 1

        # Determine complexity level
        if complexity_score <= 2:
            return "Low"
        elif complexity_score <= 4:
            return "Medium"
        else:
            return "High"

    def _get_real_component_pricing(
        self, components: Dict[str, Any], quantities: List[int]
    ) -> Dict[str, Any]:
        """
        Get REAL component pricing from DigiKey
        NO ESTIMATES - only real data or mark as unavailable
        """
        result = {
            "has_pricing": False,
            "priced_count": 0,
            "missing_pricing": [],
            "coverage_percent": 0.0,
            "costs": {},
            "component_prices": {},
        }

        if not self.has_digikey:
            # No DigiKey API available
            result["missing_pricing"] = [
                f"{ref}: {comp.get('value', 'Unknown')}"
                for ref, comp in components.items()
            ]
            return result

        # Try to get real pricing for each component
        priced_components = []

        for ref, comp in components.items():
            value = comp.get("value", "")
            part_number = comp.get("part_number", value)

            if self.require_real_data:
                # Only use real DigiKey data
                try:
                    # Search DigiKey for the part
                    results = self.digikey_search(part_number, max_results=1)
                    if results:
                        # Found real pricing
                        priced_components.append(
                            {
                                "reference": ref,
                                "price": results[0].get("unit_price", 0),
                                "stock": results[0].get("quantity_available", 0),
                            }
                        )
                        result["priced_count"] += 1
                    else:
                        result["missing_pricing"].append(f"{ref}: {value}")
                except Exception as e:
                    logger.debug(f"Could not price {ref}: {e}")
                    result["missing_pricing"].append(f"{ref}: {value}")
            else:
                # Would estimate here, but we don't allow that
                result["missing_pricing"].append(
                    f"{ref}: {value} (estimates not allowed)"
                )

        # Calculate coverage
        if components:
            result["coverage_percent"] = (
                result["priced_count"] / len(components)
            ) * 100
            result["has_pricing"] = result["priced_count"] > 0

        # Calculate total costs at different quantities
        if priced_components:
            for qty in quantities:
                total = sum(comp["price"] for comp in priced_components)
                # Apply quantity discounts if we had real price break data
                # For now, just use base price
                result["costs"][qty] = total

        return result

    def _identify_manufacturing_issues(
        self,
        components: Dict[str, Any],
        technology_mix: Dict[str, int],
        pricing_results: Dict[str, Any],
    ) -> List[Dict[str, Any]]:
        """Identify manufacturing issues based on analysis"""
        issues = []

        # Check for mixed technology
        if technology_mix.get("SMT", 0) > 0 and technology_mix.get("THT", 0) > 0:
            issues.append(
                {
                    "severity": "MEDIUM",
                    "category": "Assembly",
                    "description": "Mixed SMT/THT assembly increases cost",
                    "recommendation": "Consider converting THT to SMT where possible",
                }
            )

        # Check for low pricing coverage
        if pricing_results["coverage_percent"] < 50:
            issues.append(
                {
                    "severity": "HIGH",
                    "category": "Sourcing",
                    "description": f"Only {pricing_results['coverage_percent']:.0f}% of components have verified pricing",
                    "recommendation": "Verify part numbers and availability before production",
                }
            )

        # Check for fine-pitch components
        for comp in components.values():
            footprint = comp.get("footprint", "").lower()
            if "0402" in footprint or "0201" in footprint:
                issues.append(
                    {
                        "severity": "LOW",
                        "category": "Assembly",
                        "description": f"Fine-pitch component ({comp.get('reference')}): {footprint}",
                        "recommendation": "May require higher-end assembly equipment",
                    }
                )
                break  # Only report once

        # Check for missing critical components
        critical_refs = ["U1", "U2", "J1"]  # MCU, regulator, connector
        for ref in critical_refs:
            if ref in components and ref + ":" in " ".join(
                pricing_results.get("missing_pricing", [])
            ):
                issues.append(
                    {
                        "severity": "CRITICAL",
                        "category": "Sourcing",
                        "description": f"Critical component {ref} has no pricing data",
                        "recommendation": "Verify availability before committing to design",
                    }
                )

        return issues

    def _find_optimization_opportunities(
        self,
        components: Dict[str, Any],
        pricing_results: Dict[str, Any],
        issues: List[Dict[str, Any]],
    ) -> List[str]:
        """Find opportunities to optimize the design for manufacturing"""
        opportunities = []

        # Component consolidation
        values = {}
        for comp in components.values():
            val = comp.get("value", "")
            if val:
                values[val] = values.get(val, 0) + 1

        # Find duplicate values that could be consolidated
        for value, count in values.items():
            if count > 3:
                opportunities.append(
                    f"Consolidate {count} instances of {value} for volume pricing"
                )

        # Technology standardization
        tech_mix = self._analyze_technology_mix(components)
        if tech_mix.get("THT", 0) > 0 and tech_mix.get("THT", 0) < 5:
            opportunities.append(
                f"Convert {tech_mix['THT']} THT components to SMT to eliminate mixed assembly"
            )

        # Package standardization
        packages = {}
        for comp in components.values():
            if comp.get("type") == "Resistor" or comp.get("type") == "Capacitor":
                pkg = (
                    comp.get("footprint", "").split(":")[-1]
                    if ":" in comp.get("footprint", "")
                    else ""
                )
                if pkg:
                    packages[pkg] = packages.get(pkg, 0) + 1

        if len(packages) > 2:
            opportunities.append(
                "Standardize passive component packages to reduce feeder setups"
            )

        # Add more opportunities based on issues
        if any(i["severity"] == "CRITICAL" for i in issues):
            opportunities.append(
                "Resolve critical sourcing issues before moving to production"
            )

        return opportunities

    def generate_agent_prompt(self, circuit_json: Dict[str, Any]) -> str:
        """
        Generate a prompt for the DFM agent with the circuit JSON

        Args:
            circuit_json: The hierarchical circuit data

        Returns:
            Formatted prompt for the DFM agent
        """
        prompt = f"""
Analyze this circuit design for Design for Manufacturing (DFM).

CIRCUIT JSON:
```json
{json.dumps(circuit_json, indent=2)}
```

REQUIREMENTS:
1. Use ONLY real component data - no estimates
2. Check each component for DigiKey availability
3. Calculate BOM costs at quantities: 1, 100, 1000
4. Identify all manufacturing issues
5. Suggest optimization opportunities
6. Clearly state which components lack pricing data

IMPORTANT:
- If pricing data is not available from DigiKey, mark as "Data Not Available"
- Do NOT estimate or guess any costs
- Clearly indicate this is component pricing only (no PCB or assembly costs)

Provide a comprehensive DFM analysis following best practices for production readiness.
"""
        return prompt


def analyze_kicad_project_for_dfm(
    project_path: str, output_file: Optional[str] = None
) -> Tuple[DFMAnalysisResult, Dict[str, Any]]:
    """
    Complete workflow: KiCad → JSON → DFM Analysis

    Args:
        project_path: Path to KiCad project
        output_file: Optional path to save JSON output

    Returns:
        Tuple of (DFM analysis result, circuit JSON)
    """
    from .kicad_dfm_analyzer import KiCadToDFMAnalyzer

    # Step 1: Convert KiCad to JSON
    kicad_analyzer = KiCadToDFMAnalyzer()
    conversion_results = kicad_analyzer.analyze_kicad_project(
        project_path, output_format="json"
    )

    circuit_json = conversion_results.get("circuit", {})

    # Save JSON if requested
    if output_file:
        with open(output_file, "w") as f:
            json.dump(circuit_json, f, indent=2)
        logger.info(f"Saved circuit JSON to {output_file}")

    # Step 2: Analyze JSON for DFM
    dfm_analyzer = JSONDFMAnalyzer(require_real_data=True)
    dfm_result = dfm_analyzer.analyze_circuit_json(circuit_json)

    return dfm_result, circuit_json
