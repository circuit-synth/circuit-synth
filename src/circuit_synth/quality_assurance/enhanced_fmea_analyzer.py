#!/usr/bin/env python3
"""
Enhanced FMEA Analyzer with Comprehensive Knowledge Base Integration
Uses the full FMEA knowledge base for detailed failure mode analysis
"""

import json
import os
import random
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .fmea_analyzer import ComponentType, FailureMode, UniversalFMEAAnalyzer
from .fmea_report_generator import FMEAReportGenerator

# import yaml  # No longer needed, using JSON


class EnhancedFMEAAnalyzer(UniversalFMEAAnalyzer):
    """Enhanced FMEA analyzer that uses the comprehensive knowledge base"""

    def __init__(self):
        super().__init__()
        self.knowledge_base = self._load_knowledge_base()

    def _load_knowledge_base(self) -> Dict:
        """Load the comprehensive FMEA knowledge base"""
        kb = {
            "component_specific": {},
            "environmental": {},
            "manufacturing": {},
            "standards": {},
        }

        kb_path = Path("knowledge_base") / "fmea"
        if not kb_path.exists():
            print(f"Warning: Knowledge base not found at {kb_path}")
            return kb

        # Load component-specific failure modes
        component_path = kb_path / "failure_modes" / "component_specific"
        if component_path.exists():
            for json_file in component_path.glob("*.json"):
                try:
                    with open(json_file, "r") as f:
                        component_type = json_file.stem
                        kb["component_specific"][component_type] = json.load(f)
                except Exception as e:
                    print(f"Error loading {json_file}: {e}")

        # Load environmental failure modes
        env_path = kb_path / "failure_modes" / "environmental"
        if env_path.exists():
            for json_file in env_path.glob("*.json"):
                try:
                    with open(json_file, "r") as f:
                        env_type = json_file.stem
                        kb["environmental"][env_type] = json.load(f)
                except Exception as e:
                    print(f"Error loading {json_file}: {e}")

        # Load manufacturing defects
        mfg_path = kb_path / "failure_modes" / "manufacturing"
        if mfg_path.exists():
            for json_file in mfg_path.glob("*.json"):
                try:
                    with open(json_file, "r") as f:
                        mfg_type = json_file.stem
                        kb["manufacturing"][mfg_type] = json.load(f)
                except Exception as e:
                    print(f"Error loading {json_file}: {e}")

        # Load standards
        standards_path = kb_path / "standards"
        if standards_path.exists():
            for json_file in standards_path.glob("*.json"):
                try:
                    with open(json_file, "r") as f:
                        standard_type = json_file.stem
                        kb["standards"][standard_type] = json.load(f)
                except Exception as e:
                    print(f"Error loading {json_file}: {e}")

        return kb

    def analyze_component(
        self, component_info: Dict, circuit_context: Dict
    ) -> List[FailureMode]:
        """Enhanced component analysis using comprehensive knowledge base"""

        # Get base failure modes from parent class
        base_failure_modes = super().analyze_component(component_info, circuit_context)

        # Enhance with knowledge base data
        enhanced_modes = []
        component_type = self.identify_component_type(component_info)

        # Add component-specific failure modes from knowledge base
        enhanced_modes.extend(
            self._get_component_specific_modes(component_info, component_type)
        )

        # Add environmental failure modes
        enhanced_modes.extend(
            self._get_environmental_modes(component_info, circuit_context)
        )

        # Add manufacturing defect modes
        enhanced_modes.extend(self._get_manufacturing_modes(component_info))

        # Combine and deduplicate
        all_modes = base_failure_modes + enhanced_modes

        # Apply modifiers based on circuit context
        for mode in all_modes:
            self._apply_context_modifiers(mode, circuit_context)

        return all_modes

    def _get_component_specific_modes(
        self, component_info: Dict, component_type: ComponentType
    ) -> List[FailureMode]:
        """Get failure modes specific to component type from knowledge base"""
        modes = []

        # Map component type to knowledge base category
        kb_mapping = {
            ComponentType.CAPACITOR: "capacitors",
            ComponentType.RESISTOR: "resistors",
            ComponentType.INDUCTOR: "inductors",
            ComponentType.CONNECTOR: "connectors",
            ComponentType.IC: "integrated_circuits",
            ComponentType.MCU: "integrated_circuits",
            ComponentType.CRYSTAL: "crystals_oscillators",
            ComponentType.DIODE: "semiconductors",
            ComponentType.TRANSISTOR: "semiconductors",
        }

        kb_category = kb_mapping.get(component_type)
        if (
            not kb_category
            or kb_category not in self.knowledge_base["component_specific"]
        ):
            return modes

        kb_data = self.knowledge_base["component_specific"][kb_category]

        # Extract failure modes based on component specifics
        if component_type == ComponentType.CAPACITOR:
            modes.extend(self._get_capacitor_modes(component_info, kb_data))
        elif component_type == ComponentType.RESISTOR:
            modes.extend(self._get_resistor_modes(component_info, kb_data))
        elif component_type == ComponentType.CONNECTOR:
            modes.extend(self._get_connector_modes(component_info, kb_data))
        elif component_type in [ComponentType.IC, ComponentType.MCU]:
            modes.extend(self._get_ic_modes(component_info, kb_data))
        elif component_type == ComponentType.INDUCTOR:
            modes.extend(self._get_inductor_modes(component_info, kb_data))
        elif component_type == ComponentType.CRYSTAL:
            modes.extend(self._get_crystal_modes(component_info, kb_data))

        return modes

    def _get_capacitor_modes(
        self, component_info: Dict, kb_data: Dict
    ) -> List[FailureMode]:
        """Get capacitor-specific failure modes"""
        modes = []

        # Determine capacitor type from footprint/value
        value = component_info.get("value", "").lower()
        footprint = component_info.get("footprint", "").lower()

        if "uf" in value and float(value.replace("uf", "")) > 1:
            # Likely electrolytic
            cap_type = "aluminum_electrolytic"
        elif "0402" in footprint or "0603" in footprint or "0805" in footprint:
            # SMD ceramic
            cap_type = "ceramic_mlcc"
        else:
            cap_type = "ceramic_mlcc"  # default

        if cap_type in kb_data:
            for fm_data in kb_data[cap_type].get("failure_modes", []):
                mode = FailureMode(
                    component=component_info["ref"],
                    component_type=ComponentType.CAPACITOR,
                    failure_mode=fm_data.get("mechanism", "Unknown"),
                    cause=", ".join(fm_data.get("causes", [])),
                    effect=fm_data.get("effects", {}).get(
                        "system", "System malfunction"
                    ),
                    severity=fm_data.get("severity", {}).get("power_supply", 7),
                    occurrence=fm_data.get("occurrence", {}).get("base", 5),
                    detection=fm_data.get("detection", {}).get("difficulty", 5),
                    recommendation=self._generate_kb_recommendation(fm_data),
                )
                modes.append(mode)

        return modes[:3]  # Limit to top 3 modes per component

    def _get_resistor_modes(
        self, component_info: Dict, kb_data: Dict
    ) -> List[FailureMode]:
        """Get resistor-specific failure modes"""
        modes = []

        # Determine resistor type
        footprint = component_info.get("footprint", "").lower()
        if "0402" in footprint or "0603" in footprint or "0805" in footprint:
            res_type = "thick_film_chip"
        else:
            res_type = "thick_film_chip"  # default

        if res_type in kb_data:
            for fm_data in kb_data[res_type].get("failure_modes", [])[:2]:
                mode = FailureMode(
                    component=component_info["ref"],
                    component_type=ComponentType.RESISTOR,
                    failure_mode=fm_data.get("mechanism", "Unknown"),
                    cause=", ".join(fm_data.get("causes", [])),
                    effect=fm_data.get("effects", {}).get("circuit", "Parameter drift"),
                    severity=fm_data.get("severity", {}).get("precision_circuit", 6),
                    occurrence=fm_data.get("occurrence", {}).get("base", 4),
                    detection=fm_data.get("detection", {}).get("difficulty", 6),
                    recommendation=self._generate_kb_recommendation(fm_data),
                )
                modes.append(mode)

        return modes

    def _get_connector_modes(
        self, component_info: Dict, kb_data: Dict
    ) -> List[FailureMode]:
        """Get connector-specific failure modes"""
        modes = []

        symbol = component_info.get("symbol", "").lower()
        if "usb_c" in symbol:
            conn_type = "usb_c"
            section = "usb_connectors"
        elif "usb" in symbol:
            conn_type = "usb_a_b"
            section = "usb_connectors"
        else:
            conn_type = None
            section = None

        if section and section in kb_data:
            conn_data = kb_data[section].get(conn_type, {})
            for fm_data in conn_data.get("failure_modes", [])[:3]:
                mode = FailureMode(
                    component=component_info["ref"],
                    component_type=ComponentType.CONNECTOR,
                    failure_mode=fm_data.get("mechanism", "Unknown"),
                    cause=", ".join(fm_data.get("causes", [])),
                    effect=fm_data.get("effects", {}).get(
                        "system", "Connection failure"
                    ),
                    severity=fm_data.get("severity", {}).get("power_delivery", 8),
                    occurrence=fm_data.get("occurrence", {}).get("base", 5),
                    detection=fm_data.get("detection", {}).get("difficulty", 5),
                    recommendation=self._generate_kb_recommendation(fm_data),
                )
                modes.append(mode)

        return modes

    def _get_ic_modes(self, component_info: Dict, kb_data: Dict) -> List[FailureMode]:
        """Get IC-specific failure modes"""
        modes = []

        # Add silicon-level failures
        if "silicon_level_failures" in kb_data:
            for category in ["gate_oxide_breakdown", "electromigration", "latchup"]:
                if category in kb_data["silicon_level_failures"]:
                    fm_list = kb_data["silicon_level_failures"][category].get(
                        "failure_modes", []
                    )
                    if fm_list:
                        fm_data = fm_list[0]  # Take first mode from each category
                        mode = FailureMode(
                            component=component_info["ref"],
                            component_type=ComponentType.IC,
                            failure_mode=fm_data.get("mechanism", "Unknown"),
                            cause=", ".join(fm_data.get("causes", [])),
                            effect=fm_data.get("effects", {}).get(
                                "system", "Device failure"
                            ),
                            severity=fm_data.get("severity", {}).get(
                                "digital_logic", 8
                            ),
                            occurrence=fm_data.get("occurrence", {}).get("base", 4),
                            detection=fm_data.get("detection", {}).get("difficulty", 6),
                            recommendation=self._generate_kb_recommendation(fm_data),
                        )
                        modes.append(mode)

        # Add package-level failures
        if "package_level_failures" in kb_data:
            for category in ["wire_bond_failures", "mold_compound_failures"]:
                if category in kb_data["package_level_failures"]:
                    fm_list = kb_data["package_level_failures"][category].get(
                        "failure_modes", []
                    )
                    if fm_list:
                        fm_data = fm_list[0]
                        mode = FailureMode(
                            component=component_info["ref"],
                            component_type=ComponentType.IC,
                            failure_mode=fm_data.get("mechanism", "Unknown"),
                            cause=", ".join(fm_data.get("causes", [])),
                            effect=fm_data.get("effects", {}).get(
                                "system", "Device failure"
                            ),
                            severity=fm_data.get("severity", {}).get(
                                "all_applications", 9
                            ),
                            occurrence=fm_data.get("occurrence", {}).get("base", 3),
                            detection=fm_data.get("detection", {}).get("difficulty", 7),
                            recommendation=self._generate_kb_recommendation(fm_data),
                        )
                        modes.append(mode)

        return modes[:4]  # Limit to 4 modes for ICs

    def _get_inductor_modes(
        self, component_info: Dict, kb_data: Dict
    ) -> List[FailureMode]:
        """Get inductor-specific failure modes"""
        modes = []

        # Default to ferrite core
        ind_type = "ferrite_core_inductors"

        if ind_type in kb_data:
            for fm_data in kb_data[ind_type].get("failure_modes", [])[:2]:
                mode = FailureMode(
                    component=component_info["ref"],
                    component_type=ComponentType.INDUCTOR,
                    failure_mode=fm_data.get("mechanism", "Unknown"),
                    cause=", ".join(fm_data.get("causes", [])),
                    effect=fm_data.get("effects", {}).get(
                        "system", "Circuit malfunction"
                    ),
                    severity=fm_data.get("severity", {}).get("switching_regulators", 7),
                    occurrence=fm_data.get("occurrence", {}).get("base", 4),
                    detection=fm_data.get("detection", {}).get("difficulty", 5),
                    recommendation=self._generate_kb_recommendation(fm_data),
                )
                modes.append(mode)

        return modes

    def _get_crystal_modes(
        self, component_info: Dict, kb_data: Dict
    ) -> List[FailureMode]:
        """Get crystal/oscillator-specific failure modes"""
        modes = []

        if "quartz_crystals" in kb_data:
            for fm_data in kb_data["quartz_crystals"].get("failure_modes", [])[:2]:
                mode = FailureMode(
                    component=component_info["ref"],
                    component_type=ComponentType.CRYSTAL,
                    failure_mode=fm_data.get("mechanism", "Unknown"),
                    cause=", ".join(fm_data.get("causes", [])),
                    effect=fm_data.get("effects", {}).get("system", "Timing failure"),
                    severity=fm_data.get("severity", {}).get("timing_critical", 9),
                    occurrence=fm_data.get("occurrence", {}).get("base", 4),
                    detection=fm_data.get("detection", {}).get("difficulty", 4),
                    recommendation=self._generate_kb_recommendation(fm_data),
                )
                modes.append(mode)

        return modes

    def _get_environmental_modes(
        self, component_info: Dict, circuit_context: Dict
    ) -> List[FailureMode]:
        """Get environmental stress failure modes"""
        modes = []

        # Add thermal stress modes for power components
        if "thermal" in self.knowledge_base["environmental"]:
            thermal_data = self.knowledge_base["environmental"]["thermal"]

            # Check if component is power-related
            if any(
                keyword in component_info.get("symbol", "").lower()
                for keyword in ["regulator", "power", "mosfet", "driver"]
            ):

                if "temperature_cycling" in thermal_data:
                    fm_list = thermal_data["temperature_cycling"].get(
                        "failure_modes", []
                    )
                    if fm_list:
                        fm_data = fm_list[0]
                        mode = FailureMode(
                            component=component_info["ref"],
                            component_type=self.identify_component_type(component_info),
                            failure_mode=f"Thermal: {fm_data.get('mechanism', 'Unknown')}",
                            cause=", ".join(fm_data.get("causes", [])),
                            effect=fm_data.get("effects", {}).get(
                                "system", "Thermal failure"
                            ),
                            severity=fm_data.get("severity", {}).get("bga_packages", 8),
                            occurrence=fm_data.get("occurrence", {}).get("base", 5),
                            detection=fm_data.get("detection", {}).get("difficulty", 7),
                            recommendation="Implement thermal management and use appropriate derating",
                        )
                        modes.append(mode)

        # Add mechanical stress for connectors and large components
        if "mechanical" in self.knowledge_base["environmental"]:
            mech_data = self.knowledge_base["environmental"]["mechanical"]

            if component_info.get("type") == ComponentType.CONNECTOR:
                if "vibration" in mech_data:
                    fm_list = mech_data["vibration"].get("failure_modes", [])
                    if fm_list:
                        fm_data = fm_list[0]
                        mode = FailureMode(
                            component=component_info["ref"],
                            component_type=ComponentType.CONNECTOR,
                            failure_mode=f"Mechanical: {fm_data.get('mechanism', 'Unknown')}",
                            cause="Vibration and mechanical stress",
                            effect=fm_data.get("effects", {}).get(
                                "system", "Connection failure"
                            ),
                            severity=7,
                            occurrence=4,
                            detection=5,
                            recommendation="Use mechanical support and vibration damping",
                        )
                        modes.append(mode)

        # Add electrical stress modes
        if "electrical" in self.knowledge_base["environmental"]:
            elec_data = self.knowledge_base["environmental"]["electrical"]

            # ESD for all semiconductors
            if component_info.get("type") in [
                ComponentType.IC,
                ComponentType.MCU,
                ComponentType.TRANSISTOR,
                ComponentType.DIODE,
            ]:
                if "electrostatic_discharge" in elec_data:
                    fm_list = elec_data["electrostatic_discharge"].get(
                        "failure_modes", []
                    )
                    if fm_list:
                        fm_data = fm_list[0]
                        mode = FailureMode(
                            component=component_info["ref"],
                            component_type=self.identify_component_type(component_info),
                            failure_mode=f"ESD: {fm_data.get('mechanism', 'Unknown')}",
                            cause="Electrostatic discharge during handling",
                            effect=fm_data.get("effects", {}).get(
                                "system", "Device damage"
                            ),
                            severity=fm_data.get("severity", {}).get("modern_cmos", 9),
                            occurrence=fm_data.get("occurrence", {}).get("base", 5),
                            detection=fm_data.get("detection", {}).get("difficulty", 6),
                            recommendation="Implement ESD protection and handling procedures",
                        )
                        modes.append(mode)

        return modes[:2]  # Limit environmental modes

    def _get_manufacturing_modes(self, component_info: Dict) -> List[FailureMode]:
        """Get manufacturing defect failure modes"""
        modes = []

        if "solder_defects" in self.knowledge_base["manufacturing"]:
            solder_data = self.knowledge_base["manufacturing"]["solder_defects"]

            # Add solder joint defects for all components
            if "solder_joint_defects" in solder_data:
                # Select relevant defects based on footprint
                footprint = component_info.get("footprint", "").lower()

                if "bga" in footprint:
                    defect_type = "head_in_pillow"
                elif any(size in footprint for size in ["0201", "0402"]):
                    defect_type = "tombstoning"
                else:
                    defect_type = "bridging"

                if defect_type in solder_data["solder_joint_defects"]:
                    fm_list = solder_data["solder_joint_defects"][defect_type].get(
                        "failure_modes", []
                    )
                    if fm_list:
                        fm_data = fm_list[0]
                        mode = FailureMode(
                            component=component_info["ref"],
                            component_type=self.identify_component_type(component_info),
                            failure_mode=f"Manufacturing: {fm_data.get('mechanism', 'Unknown')}",
                            cause=", ".join(fm_data.get("causes", [])[:2]),
                            effect=fm_data.get("effects", {}).get(
                                "system", "Assembly defect"
                            ),
                            severity=fm_data.get("severity", {}).get(
                                "all_applications", 7
                            ),
                            occurrence=fm_data.get("occurrence", {}).get("base", 4),
                            detection=fm_data.get("detection", {}).get("difficulty", 3),
                            recommendation="Implement AOI and proper assembly process controls",
                        )
                        modes.append(mode)

        return modes[:1]  # Limit to 1 manufacturing mode per component

    def _generate_kb_recommendation(self, fm_data: Dict) -> str:
        """Generate recommendation based on failure mode data from knowledge base"""
        mitigations = fm_data.get("mitigation", [])
        if mitigations:
            return f"Recommended: {', '.join(mitigations[:2])}"

        # Generate based on occurrence modifiers
        modifiers = fm_data.get("occurrence", {}).get("modifiers", {})
        recommendations = []
        for key, value in modifiers.items():
            if value < 0:  # Negative modifier means it reduces risk
                recommendations.append(key.replace("_", " ").title())

        if recommendations:
            return f"Consider: {', '.join(recommendations[:2])}"

        return "Implement standard reliability practices and monitoring"

    def _apply_context_modifiers(
        self, mode: FailureMode, circuit_context: Dict
    ) -> None:
        """Apply circuit context modifiers to failure mode ratings"""

        # Adjust based on operating environment
        environment = circuit_context.get("environment", "indoor")
        if environment == "automotive":
            mode.occurrence = min(10, mode.occurrence + 1)
            mode.severity = min(10, mode.severity + 1)
        elif environment == "industrial":
            mode.occurrence = min(10, mode.occurrence + 1)

        # Adjust based on criticality
        if circuit_context.get("safety_critical", False):
            mode.severity = min(10, mode.severity + 2)
            mode.detection = max(1, mode.detection - 1)

        # Adjust based on production volume
        volume = circuit_context.get("production_volume", "medium")
        if volume == "high":
            mode.detection = max(1, mode.detection - 1)  # Better testing
        elif volume == "prototype":
            mode.detection = min(10, mode.detection + 1)  # Less testing


def analyze_circuit_with_enhanced_kb(circuit_path: str, output_pdf: str = None) -> str:
    """Analyze a circuit using the enhanced knowledge base"""

    print("Initializing Enhanced FMEA Analyzer with comprehensive knowledge base...")
    analyzer = EnhancedFMEAAnalyzer()

    print(f"Analyzing circuit: {circuit_path}")
    circuit_context, components = analyzer.analyze_circuit_file(circuit_path)

    # Set additional context
    circuit_context.update(
        {
            "environment": "consumer",  # or 'automotive', 'industrial', etc.
            "production_volume": "medium",
            "safety_critical": False,
            "operating_temperature": "0-70C",
            "expected_lifetime": "5 years",
        }
    )

    print(f"Analyzing {len(components)} components with enhanced knowledge base...")
    all_failure_modes = []

    for component in components:
        failure_modes = analyzer.analyze_component(component, circuit_context)
        all_failure_modes.extend(failure_modes)

    print(
        f"Identified {len(all_failure_modes)} failure modes using comprehensive analysis"
    )

    # Prepare results
    analysis_results = {
        "components": components,
        "failure_modes": [
            {
                "component": fm.component,
                "component_type": fm.component_type.value,
                "failure_mode": fm.failure_mode,
                "cause": fm.cause,
                "effect": fm.effect,
                "severity": fm.severity,
                "occurrence": fm.occurrence,
                "detection": fm.detection,
                "rpn": fm.severity * fm.occurrence * fm.detection,
                "recommendation": fm.recommendation,
            }
            for fm in all_failure_modes
        ],
        "circuit_context": circuit_context,
    }

    # Generate report
    if not output_pdf:
        output_pdf = "Enhanced_FMEA_Report.pdf"

    project_name = Path(circuit_path).stem
    generator = FMEAReportGenerator(project_name)
    pdf_path = generator.generate_pdf_report(analysis_results, output_pdf)

    # Print summary
    critical = sum(
        1
        for fm in all_failure_modes
        if fm.severity * fm.occurrence * fm.detection >= 300
    )
    high_risk = sum(
        1
        for fm in all_failure_modes
        if 125 <= fm.severity * fm.occurrence * fm.detection < 300
    )

    print(f"\n✅ Enhanced FMEA Report generated: {pdf_path}")
    print(f"📊 Analysis Summary:")
    print(f"  - Total failure modes: {len(all_failure_modes)}")
    print(f"  - Critical risk (RPN ≥ 300): {critical}")
    print(f"  - High risk (125 ≤ RPN < 300): {high_risk}")
    print(f"  - Knowledge base categories used: {len(analyzer.knowledge_base)}")

    return pdf_path
