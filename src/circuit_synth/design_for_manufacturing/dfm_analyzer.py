#!/usr/bin/env python3
"""
Core DFM Analyzer for Circuit-Synth

Analyzes circuits for manufacturability, cost optimization, and production readiness.
"""

import json
import logging
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class ManufacturingProcess(Enum):
    """Manufacturing process types"""

    SMT = "Surface Mount Technology"
    THT = "Through-Hole Technology"
    MIXED = "Mixed Technology"
    MANUAL = "Manual Assembly"
    SELECTIVE = "Selective Soldering"
    WAVE = "Wave Soldering"
    REFLOW = "Reflow Soldering"


class IssueSeverity(Enum):
    """DFM issue severity levels"""

    CRITICAL = 5  # Will prevent manufacturing
    HIGH = 4  # Will significantly impact yield/cost
    MEDIUM = 3  # Will moderately impact yield/cost
    LOW = 2  # Minor impact on yield/cost
    INFO = 1  # Informational only


class IssueCategory(Enum):
    """DFM issue categories"""

    COMPONENT_SELECTION = "Component Selection"
    COMPONENT_PLACEMENT = "Component Placement"
    PCB_DESIGN = "PCB Design"
    ASSEMBLY_PROCESS = "Assembly Process"
    TESTABILITY = "Testability"
    COST_OPTIMIZATION = "Cost Optimization"
    SUPPLY_CHAIN = "Supply Chain"
    RELIABILITY = "Reliability"


@dataclass
class ManufacturingIssue:
    """Represents a DFM issue found during analysis"""

    category: IssueCategory
    severity: IssueSeverity
    component: Optional[str]
    description: str
    impact: str
    recommendation: str
    cost_impact: Optional[float] = None
    yield_impact: Optional[float] = None

    @property
    def priority_score(self) -> int:
        """Calculate priority score for issue resolution"""
        base_score = self.severity.value * 100

        # Add cost impact factor
        if self.cost_impact:
            if self.cost_impact > 10:
                base_score += 50
            elif self.cost_impact > 5:
                base_score += 30
            elif self.cost_impact > 1:
                base_score += 10

        # Add yield impact factor
        if self.yield_impact:
            if self.yield_impact > 0.1:  # >10% yield loss
                base_score += 50
            elif self.yield_impact > 0.05:  # >5% yield loss
                base_score += 30
            elif self.yield_impact > 0.01:  # >1% yield loss
                base_score += 10

        return base_score


@dataclass
class ComponentAnalysis:
    """Analysis results for a single component"""

    reference: str
    part_number: str
    package: str
    technology: ManufacturingProcess
    availability_score: float  # 0-100
    cost_score: float  # 0-100
    manufacturability_score: float  # 0-100
    issues: List[ManufacturingIssue] = field(default_factory=list)
    alternatives: List[Dict[str, Any]] = field(default_factory=list)

    @property
    def overall_score(self) -> float:
        """Calculate overall component DFM score"""
        return (
            self.availability_score * 0.3
            + self.cost_score * 0.3
            + self.manufacturability_score * 0.4
        )


@dataclass
class PCBAnalysis:
    """Analysis results for PCB design"""

    layer_count: int
    board_size_mm2: float
    min_trace_width_mm: float
    min_via_size_mm: float
    component_density: float  # components per cm²
    technology_mix: Dict[ManufacturingProcess, int]
    panelization_efficiency: float  # 0-100%
    testpoint_coverage: float  # 0-100%
    issues: List[ManufacturingIssue] = field(default_factory=list)

    @property
    def complexity_score(self) -> float:
        """Calculate PCB complexity score (lower is better)"""
        score = 0

        # Layer count factor
        if self.layer_count <= 2:
            score += 10
        elif self.layer_count <= 4:
            score += 30
        elif self.layer_count <= 6:
            score += 50
        else:
            score += 70

        # Component density factor
        if self.component_density < 5:
            score += 10
        elif self.component_density < 10:
            score += 20
        elif self.component_density < 20:
            score += 40
        else:
            score += 60

        # Technology mix factor
        if len(self.technology_mix) == 1:
            score += 10
        elif len(self.technology_mix) == 2:
            score += 30
        else:
            score += 50

        return min(score, 100)


@dataclass
class DFMReport:
    """Complete DFM analysis report"""

    circuit_name: str
    timestamp: str
    total_components: int
    unique_components: int

    # Analysis results
    component_analyses: List[ComponentAnalysis]
    pcb_analysis: Optional[PCBAnalysis]

    # Cost analysis
    total_component_cost: float
    pcb_cost_estimate: float
    assembly_cost_estimate: float
    total_unit_cost: float

    # Volume analysis
    volume_pricing: Dict[int, float]  # quantity -> unit price

    # Issues and recommendations
    issues: List[ManufacturingIssue]
    critical_issues_count: int
    high_issues_count: int

    # Scores
    overall_manufacturability_score: float  # 0-100
    cost_optimization_score: float  # 0-100
    supply_chain_risk_score: float  # 0-100 (lower is better)

    # Optimization opportunities
    cost_reduction_opportunities: List[Dict[str, Any]]
    alternative_components: List[Dict[str, Any]]

    def get_executive_summary(self) -> str:
        """Generate executive summary of DFM analysis"""
        summary = f"""
DFM Analysis Executive Summary
==============================
Circuit: {self.circuit_name}
Date: {self.timestamp}

Key Metrics:
- Total Components: {self.total_components}
- Unique Parts: {self.unique_components}
- Manufacturability Score: {self.overall_manufacturability_score:.1f}/100
- Cost Optimization Score: {self.cost_optimization_score:.1f}/100
- Supply Chain Risk: {self.supply_chain_risk_score:.1f}/100

Cost Analysis:
- Component Cost: ${self.total_component_cost:.2f}
- PCB Cost: ${self.pcb_cost_estimate:.2f}
- Assembly Cost: ${self.assembly_cost_estimate:.2f}
- Total Unit Cost: ${self.total_unit_cost:.2f}

Issues Summary:
- Critical Issues: {self.critical_issues_count}
- High Priority Issues: {self.high_issues_count}
- Total Issues: {len(self.issues)}

Top Recommendations:
"""
        # Add top 3 critical issues
        critical_issues = [
            i for i in self.issues if i.severity == IssueSeverity.CRITICAL
        ][:3]
        for i, issue in enumerate(critical_issues, 1):
            summary += (
                f"{i}. {issue.description}\n   Recommendation: {issue.recommendation}\n"
            )

        return summary


class DFMAnalyzer:
    """Main DFM analysis engine"""

    def __init__(self):
        """Initialize DFM analyzer"""
        self.manufacturing_constraints = self._load_manufacturing_constraints()
        self.cost_models = self._load_cost_models()
        self.component_database = {}

    def _load_manufacturing_constraints(self) -> Dict:
        """Load manufacturing constraints and capabilities"""
        # Default constraints for common PCB manufacturers
        return {
            "min_trace_width_mm": 0.127,  # 5 mil
            "min_via_size_mm": 0.2,  # 8 mil
            "min_hole_size_mm": 0.15,  # 6 mil
            "min_annular_ring_mm": 0.05,  # 2 mil
            "min_solder_mask_clearance_mm": 0.05,
            "min_silk_screen_width_mm": 0.15,
            "max_layer_count": 8,
            "max_board_size_mm": (500, 500),
            "supported_processes": [
                ManufacturingProcess.SMT,
                ManufacturingProcess.THT,
                ManufacturingProcess.MIXED,
            ],
        }

    def _load_cost_models(self) -> Dict:
        """Load cost models for components and processes"""
        return {
            "component_markup": 1.3,  # 30% markup on components
            "pcb_base_cost_per_cm2": 0.05,
            "layer_cost_multiplier": {1: 1.0, 2: 1.0, 4: 1.5, 6: 2.2, 8: 3.0},
            "assembly_cost_per_component": {
                ManufacturingProcess.SMT: 0.02,
                ManufacturingProcess.THT: 0.10,
                ManufacturingProcess.MANUAL: 0.50,
            },
            "setup_cost": 200,  # One-time setup cost
            "stencil_cost": 50,  # SMT stencil cost
        }

    def analyze_circuit(
        self,
        circuit_data: Dict,
        volume: int = 100,
        target_cost: Optional[float] = None,
        manufacturing_site: str = "generic",
    ) -> DFMReport:
        """
        Perform comprehensive DFM analysis on a circuit

        Args:
            circuit_data: Circuit definition (components, nets, etc.)
            volume: Production volume for cost calculations
            target_cost: Target unit cost for optimization
            manufacturing_site: Manufacturing location/partner

        Returns:
            Comprehensive DFM report
        """
        logger.info(f"Starting DFM analysis for volume={volume}")

        # Extract components and connections
        components = circuit_data.get("components", {})
        nets = circuit_data.get("nets", {})

        # Analyze each component
        component_analyses = []
        issues = []

        for ref, comp_data in components.items():
            comp_analysis = self._analyze_component(ref, comp_data)
            component_analyses.append(comp_analysis)
            issues.extend(comp_analysis.issues)

        # Analyze PCB design
        pcb_analysis = self._analyze_pcb(components, nets)
        if pcb_analysis:
            issues.extend(pcb_analysis.issues)

        # Calculate costs
        component_cost = self._calculate_component_cost(component_analyses)
        pcb_cost = self._calculate_pcb_cost(pcb_analysis, volume)
        assembly_cost = self._calculate_assembly_cost(component_analyses, volume)
        total_cost = component_cost + pcb_cost + assembly_cost

        # Volume pricing
        volume_pricing = self._calculate_volume_pricing(
            component_cost, pcb_cost, assembly_cost, [10, 100, 1000, 10000]
        )

        # Calculate scores
        manufacturability_score = self._calculate_manufacturability_score(
            component_analyses, pcb_analysis
        )
        cost_score = self._calculate_cost_optimization_score(total_cost, target_cost)
        supply_risk = self._calculate_supply_chain_risk(component_analyses)

        # Find optimization opportunities
        cost_opportunities = self._find_cost_reduction_opportunities(
            component_analyses, pcb_analysis
        )
        alternatives = self._find_alternative_components(component_analyses)

        # Count critical issues
        critical_count = sum(1 for i in issues if i.severity == IssueSeverity.CRITICAL)
        high_count = sum(1 for i in issues if i.severity == IssueSeverity.HIGH)

        # Sort issues by priority
        issues.sort(key=lambda x: x.priority_score, reverse=True)

        import datetime

        return DFMReport(
            circuit_name=circuit_data.get("name", "Unnamed Circuit"),
            timestamp=datetime.datetime.now().isoformat(),
            total_components=len(components),
            unique_components=len(
                set(c.get("part_number", "") for c in components.values())
            ),
            component_analyses=component_analyses,
            pcb_analysis=pcb_analysis,
            total_component_cost=component_cost,
            pcb_cost_estimate=pcb_cost,
            assembly_cost_estimate=assembly_cost,
            total_unit_cost=total_cost,
            volume_pricing=volume_pricing,
            issues=issues,
            critical_issues_count=critical_count,
            high_issues_count=high_count,
            overall_manufacturability_score=manufacturability_score,
            cost_optimization_score=cost_score,
            supply_chain_risk_score=supply_risk,
            cost_reduction_opportunities=cost_opportunities,
            alternative_components=alternatives,
        )

    def _analyze_component(self, reference: str, comp_data: Dict) -> ComponentAnalysis:
        """Analyze a single component for DFM issues"""
        issues = []

        # Determine technology type
        package = (
            comp_data.get("footprint", "").split(":")[-1]
            if comp_data.get("footprint")
            else ""
        )
        technology = self._determine_technology(package)

        # Check component availability
        availability_score = self._check_availability(comp_data)
        if availability_score < 50:
            issues.append(
                ManufacturingIssue(
                    category=IssueCategory.SUPPLY_CHAIN,
                    severity=IssueSeverity.HIGH,
                    component=reference,
                    description=f"Low availability for {reference}",
                    impact="May cause production delays",
                    recommendation="Consider alternative with better availability",
                    yield_impact=0.0,
                )
            )

        # Check package manufacturability
        manufacturability_score = self._check_package_manufacturability(package)
        if manufacturability_score < 70:
            issues.append(
                ManufacturingIssue(
                    category=IssueCategory.COMPONENT_SELECTION,
                    severity=IssueSeverity.MEDIUM,
                    component=reference,
                    description=f"Challenging package type: {package}",
                    impact="May reduce assembly yield",
                    recommendation="Consider standard package if possible",
                    yield_impact=0.02,
                )
            )

        # Cost analysis
        cost_score = self._analyze_component_cost(comp_data)

        return ComponentAnalysis(
            reference=reference,
            part_number=comp_data.get("part_number", "Unknown"),
            package=package,
            technology=technology,
            availability_score=availability_score,
            cost_score=cost_score,
            manufacturability_score=manufacturability_score,
            issues=issues,
            alternatives=[],
        )

    def _analyze_pcb(self, components: Dict, nets: Dict) -> Optional[PCBAnalysis]:
        """Analyze PCB design for DFM issues"""
        if not components:
            return None

        issues = []

        # Estimate board size based on component count
        component_count = len(components)
        estimated_area_cm2 = component_count * 2  # Rough estimate: 2cm² per component

        # Determine technology mix
        tech_mix = {}
        for comp in components.values():
            package = comp.get("footprint", "")
            tech = self._determine_technology(package)
            tech_mix[tech] = tech_mix.get(tech, 0) + 1

        # Check for mixed technology issues
        if len(tech_mix) > 2:
            issues.append(
                ManufacturingIssue(
                    category=IssueCategory.ASSEMBLY_PROCESS,
                    severity=IssueSeverity.MEDIUM,
                    component=None,
                    description="Multiple assembly technologies required",
                    impact="Increases assembly cost and complexity",
                    recommendation="Minimize technology mixing where possible",
                    cost_impact=0.50,
                )
            )

        # Estimate layer count based on complexity
        estimated_layers = (
            2 if component_count < 50 else 4 if component_count < 200 else 6
        )

        return PCBAnalysis(
            layer_count=estimated_layers,
            board_size_mm2=estimated_area_cm2 * 100,  # Convert to mm²
            min_trace_width_mm=0.2,  # Default assumption
            min_via_size_mm=0.3,  # Default assumption
            component_density=component_count / estimated_area_cm2,
            technology_mix=tech_mix,
            panelization_efficiency=75.0,  # Default assumption
            testpoint_coverage=60.0,  # Default assumption
            issues=issues,
        )

    def _determine_technology(self, package: str) -> ManufacturingProcess:
        """Determine manufacturing technology from package type"""
        package_lower = package.lower()

        if any(
            kw in package_lower
            for kw in [
                "smd",
                "smt",
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
            return ManufacturingProcess.SMT
        elif any(
            kw in package_lower
            for kw in ["tht", "through", "dip", "sip", "radial", "axial"]
        ):
            return ManufacturingProcess.THT
        else:
            return ManufacturingProcess.SMT  # Default to SMT

    def _check_availability(self, comp_data: Dict) -> float:
        """Check component availability score"""
        # This would integrate with supplier APIs
        # For now, return a default score
        return 75.0

    def _check_package_manufacturability(self, package: str) -> float:
        """Check package manufacturability score"""
        package_lower = package.lower()

        # Easy packages
        if any(kw in package_lower for kw in ["0603", "0805", "1206", "soic", "sot23"]):
            return 95.0
        # Medium difficulty
        elif any(kw in package_lower for kw in ["0402", "qfp", "ssop", "tssop"]):
            return 80.0
        # Difficult packages
        elif any(kw in package_lower for kw in ["0201", "bga", "qfn", "dfn"]):
            return 60.0
        # Through-hole (easy but manual)
        elif any(kw in package_lower for kw in ["dip", "sip", "radial"]):
            return 85.0
        else:
            return 70.0  # Unknown package

    def _analyze_component_cost(self, comp_data: Dict) -> float:
        """Analyze component cost score"""
        # This would integrate with pricing databases
        # For now, return a default score
        return 70.0

    def _calculate_component_cost(self, analyses: List[ComponentAnalysis]) -> float:
        """Calculate total component cost"""
        # Simplified cost calculation
        base_cost = len(analyses) * 0.50  # Average $0.50 per component
        return base_cost * self.cost_models["component_markup"]

    def _calculate_pcb_cost(
        self, pcb_analysis: Optional[PCBAnalysis], volume: int
    ) -> float:
        """Calculate PCB fabrication cost"""
        if not pcb_analysis:
            return 10.0  # Default cost

        area_cm2 = pcb_analysis.board_size_mm2 / 100
        base_cost = area_cm2 * self.cost_models["pcb_base_cost_per_cm2"]

        # Apply layer multiplier
        layer_mult = self.cost_models["layer_cost_multiplier"].get(
            pcb_analysis.layer_count, 1.5
        )
        base_cost *= layer_mult

        # Volume discount
        if volume >= 1000:
            base_cost *= 0.6
        elif volume >= 100:
            base_cost *= 0.8

        return base_cost

    def _calculate_assembly_cost(
        self, analyses: List[ComponentAnalysis], volume: int
    ) -> float:
        """Calculate assembly cost"""
        total_cost = self.cost_models["setup_cost"] / volume

        for analysis in analyses:
            cost_per = self.cost_models["assembly_cost_per_component"].get(
                analysis.technology, 0.05
            )
            total_cost += cost_per

        # Add stencil cost for SMT
        has_smt = any(a.technology == ManufacturingProcess.SMT for a in analyses)
        if has_smt:
            total_cost += self.cost_models["stencil_cost"] / volume

        return total_cost

    def _calculate_volume_pricing(
        self,
        component_cost: float,
        pcb_cost: float,
        assembly_cost: float,
        volumes: List[int],
    ) -> Dict[int, float]:
        """Calculate pricing at different volumes"""
        pricing = {}

        for vol in volumes:
            # Recalculate with volume discounts
            comp_cost = component_cost * (
                0.9 if vol >= 1000 else 0.95 if vol >= 100 else 1.0
            )
            pcb = pcb_cost * (0.6 if vol >= 1000 else 0.8 if vol >= 100 else 1.0)
            assembly = self.cost_models["setup_cost"] / vol + assembly_cost

            pricing[vol] = comp_cost + pcb + assembly

        return pricing

    def _calculate_manufacturability_score(
        self,
        component_analyses: List[ComponentAnalysis],
        pcb_analysis: Optional[PCBAnalysis],
    ) -> float:
        """Calculate overall manufacturability score"""
        if not component_analyses:
            return 0.0

        # Average component scores
        comp_score = sum(a.overall_score for a in component_analyses) / len(
            component_analyses
        )

        # PCB complexity score (inverted - lower complexity is better)
        pcb_score = 100 - (pcb_analysis.complexity_score if pcb_analysis else 50)

        # Weighted average
        return comp_score * 0.7 + pcb_score * 0.3

    def _calculate_cost_optimization_score(
        self, actual_cost: float, target_cost: Optional[float]
    ) -> float:
        """Calculate cost optimization score"""
        if not target_cost:
            return 75.0  # Default score if no target

        if actual_cost <= target_cost:
            return 100.0
        else:
            # Score decreases as cost exceeds target
            excess_ratio = (actual_cost - target_cost) / target_cost
            return max(0, 100 - (excess_ratio * 100))

    def _calculate_supply_chain_risk(self, analyses: List[ComponentAnalysis]) -> float:
        """Calculate supply chain risk score"""
        if not analyses:
            return 0.0

        # Average availability scores (inverted - low availability = high risk)
        avg_availability = sum(a.availability_score for a in analyses) / len(analyses)
        risk_score = 100 - avg_availability

        # Add penalty for single-source components
        # (Would need real supplier data for this)

        return risk_score

    def _find_cost_reduction_opportunities(
        self,
        component_analyses: List[ComponentAnalysis],
        pcb_analysis: Optional[PCBAnalysis],
    ) -> List[Dict[str, Any]]:
        """Identify cost reduction opportunities"""
        opportunities = []

        # Component consolidation
        part_numbers = {}
        for analysis in component_analyses:
            pn = analysis.part_number
            if pn in part_numbers:
                part_numbers[pn].append(analysis.reference)
            else:
                part_numbers[pn] = [analysis.reference]

        # Check for similar components that could be consolidated
        if len(part_numbers) > len(component_analyses) * 0.7:
            opportunities.append(
                {
                    "type": "Component Consolidation",
                    "description": "Multiple similar components could be standardized",
                    "potential_savings": len(part_numbers) * 0.10,
                    "effort": "Low",
                    "impact": "Reduce unique part count and simplify procurement",
                }
            )

        # Technology standardization
        if pcb_analysis and len(pcb_analysis.technology_mix) > 1:
            opportunities.append(
                {
                    "type": "Technology Standardization",
                    "description": "Convert THT components to SMT where possible",
                    "potential_savings": 0.50
                    * sum(
                        count
                        for tech, count in pcb_analysis.technology_mix.items()
                        if tech == ManufacturingProcess.THT
                    ),
                    "effort": "Medium",
                    "impact": "Simplify assembly process and reduce cost",
                }
            )

        return opportunities

    def _find_alternative_components(
        self, analyses: List[ComponentAnalysis]
    ) -> List[Dict[str, Any]]:
        """Find alternative components for optimization"""
        alternatives = []

        for analysis in analyses:
            if analysis.cost_score < 70 or analysis.availability_score < 70:
                # This would integrate with component databases
                # For now, return placeholder
                alternatives.append(
                    {
                        "original": analysis.reference,
                        "original_part": analysis.part_number,
                        "reason": "Cost/Availability",
                        "alternatives": [
                            {
                                "part_number": f"ALT_{analysis.part_number}",
                                "cost_reduction": 0.20,
                                "availability_improvement": 20,
                                "note": "Generic equivalent with better sourcing",
                            }
                        ],
                    }
                )

        return alternatives
