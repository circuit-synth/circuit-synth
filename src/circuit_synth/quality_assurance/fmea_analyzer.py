#!/usr/bin/env python3
"""
Universal FMEA Analyzer for Circuit-Synth
Analyzes any circuit design and generates comprehensive FMEA reports
"""

import ast
import json
import os
from dataclasses import dataclass, field
from enum import Enum
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from .circuit_parser import extract_components_from_python
from .fmea_report_generator import FMEAReportGenerator


class ComponentType(Enum):
    """Standard component types for FMEA analysis"""

    CONNECTOR = "connector"
    REGULATOR = "regulator"
    MCU = "mcu"
    CAPACITOR = "capacitor"
    RESISTOR = "resistor"
    INDUCTOR = "inductor"
    DIODE = "diode"
    LED = "led"
    TRANSISTOR = "transistor"
    IC = "ic"
    CRYSTAL = "crystal"
    TRANSFORMER = "transformer"
    FUSE = "fuse"
    SWITCH = "switch"
    UNKNOWN = "unknown"


@dataclass
class FailureMode:
    """Represents a single failure mode in FMEA analysis"""

    component: str
    component_type: ComponentType
    failure_mode: str
    cause: str
    effect: str
    severity: int
    occurrence: int
    detection: int
    recommendation: str

    @property
    def rpn(self) -> int:
        """Calculate Risk Priority Number"""
        return self.severity * self.occurrence * self.detection

    def to_dict(self) -> Dict:
        """Convert to dictionary for report generation"""
        return {
            "component": self.component,
            "component_type": self.component_type.value,
            "failure_mode": self.failure_mode,
            "cause": self.cause,
            "effect": self.effect,
            "severity": self.severity,
            "occurrence": self.occurrence,
            "detection": self.detection,
            "rpn": self.rpn,
            "recommendation": self.recommendation,
        }


class UniversalFMEAAnalyzer:
    """Universal FMEA analyzer for any circuit design"""

    # Standard failure modes by component type
    FAILURE_MODES_DB = {
        ComponentType.CONNECTOR: [
            ("Solder joint failure", "Thermal cycling, mechanical stress", 9, 6, 7),
            ("Contact oxidation", "Environmental exposure, age", 5, 5, 6),
            ("Mechanical damage", "Insertion cycles, force", 7, 4, 4),
            ("Pin misalignment", "Manufacturing defect", 6, 3, 5),
        ],
        ComponentType.REGULATOR: [
            ("Thermal shutdown", "Overcurrent, poor heatsinking", 8, 7, 6),
            ("Output voltage drift", "Component aging, temperature", 7, 5, 7),
            ("Input overvoltage failure", "Transient spikes", 9, 4, 7),
            ("Dropout voltage increase", "Internal resistance rise", 6, 5, 8),
        ],
        ComponentType.MCU: [
            ("ESD damage", "Handling, environmental discharge", 9, 4, 8),
            ("Clock failure", "Crystal defect, oscillator issue", 8, 3, 6),
            ("Flash corruption", "Power brownout, EMI", 7, 4, 7),
            ("I/O pin failure", "Overvoltage, overcurrent", 6, 5, 5),
            ("Thermal damage", "Overheating, inadequate cooling", 8, 4, 6),
        ],
        ComponentType.CAPACITOR: [
            ("Capacitance degradation", "Aging, temperature stress", 5, 7, 7),
            ("ESR increase", "Electrolyte drying", 6, 6, 7),
            ("Short circuit", "Dielectric breakdown", 8, 3, 5),
            ("Open circuit", "Lead fracture, corrosion", 7, 3, 5),
        ],
        ComponentType.RESISTOR: [
            ("Resistance drift", "Temperature coefficient, aging", 4, 6, 8),
            ("Open circuit", "Overstress, manufacturing defect", 6, 3, 5),
            ("Thermal damage", "Exceeded power rating", 7, 4, 6),
        ],
        ComponentType.DIODE: [
            ("Junction failure", "Overvoltage, thermal stress", 8, 4, 6),
            ("Reverse leakage", "Temperature, degradation", 5, 5, 7),
            ("Short circuit", "Overcurrent, surge", 8, 3, 5),
        ],
        ComponentType.LED: [
            ("Luminosity degradation", "Aging, overcurrent", 3, 7, 4),
            ("Color shift", "Temperature, aging", 2, 6, 5),
            ("Burn out", "Overcurrent, ESD", 4, 4, 3),
        ],
        ComponentType.CRYSTAL: [
            ("Frequency drift", "Aging, temperature", 7, 5, 8),
            ("Fracture", "Mechanical shock, vibration", 9, 3, 8),
            ("Loss of oscillation", "Drive level, contamination", 8, 3, 7),
        ],
    }

    def __init__(self, verbose: bool = True):
        self.verbose = verbose
        self.components_analyzed = 0
        self.failure_modes = []

    def identify_component_type(self, component_info: Dict) -> ComponentType:
        """Identify component type from symbol or reference"""
        symbol = component_info.get("symbol", "").lower()
        ref = component_info.get("ref", "").upper()
        value = component_info.get("value", "").lower()

        # Check by symbol name
        if "connector" in symbol or "usb" in symbol or "jack" in symbol:
            return ComponentType.CONNECTOR
        elif "regulator" in symbol or "ldo" in symbol or "dcdc" in symbol:
            return ComponentType.REGULATOR
        elif (
            "mcu" in symbol
            or "micro" in symbol
            or "cpu" in symbol
            or "esp" in symbol
            or "stm" in symbol
        ):
            return ComponentType.MCU
        elif "capacitor" in symbol or symbol.endswith(":c"):
            return ComponentType.CAPACITOR
        elif "resistor" in symbol or symbol.endswith(":r"):
            return ComponentType.RESISTOR
        elif "inductor" in symbol or symbol.endswith(":l"):
            return ComponentType.INDUCTOR
        elif "diode" in symbol or "led" in symbol:
            return ComponentType.LED if "led" in symbol else ComponentType.DIODE
        elif "crystal" in symbol or "xtal" in symbol:
            return ComponentType.CRYSTAL
        elif "transistor" in symbol or "mosfet" in symbol or "bjt" in symbol:
            return ComponentType.TRANSISTOR

        # Check by reference designator
        if ref.startswith("J") or ref.startswith("P"):
            return ComponentType.CONNECTOR
        elif ref.startswith("U"):
            # Could be regulator, MCU, or generic IC
            if "reg" in value or "ldo" in value:
                return ComponentType.REGULATOR
            elif any(x in value for x in ["mcu", "micro", "esp", "stm"]):
                return ComponentType.MCU
            else:
                return ComponentType.IC
        elif ref.startswith("C"):
            return ComponentType.CAPACITOR
        elif ref.startswith("R"):
            return ComponentType.RESISTOR
        elif ref.startswith("L"):
            return ComponentType.INDUCTOR
        elif ref.startswith("D"):
            return ComponentType.LED if "led" in value else ComponentType.DIODE
        elif ref.startswith("Q"):
            return ComponentType.TRANSISTOR
        elif ref.startswith("Y") or ref.startswith("X"):
            return ComponentType.CRYSTAL
        elif ref.startswith("F"):
            return ComponentType.FUSE
        elif ref.startswith("S") or ref.startswith("SW"):
            return ComponentType.SWITCH
        elif ref.startswith("T"):
            return ComponentType.TRANSFORMER

        return ComponentType.UNKNOWN

    def analyze_component(
        self, component_info: Dict, circuit_context: Dict
    ) -> List[FailureMode]:
        """Analyze a single component for failure modes"""
        comp_type = self.identify_component_type(component_info)
        comp_name = f"{component_info.get('ref', 'Unknown')} - {component_info.get('symbol', 'Unknown').split(':')[-1]}"

        failure_modes = []

        # Get standard failure modes for this component type
        standard_modes = self.FAILURE_MODES_DB.get(comp_type, [])

        for mode_data in standard_modes:
            failure_mode, cause, base_severity, base_occurrence, base_detection = (
                mode_data
            )

            # Adjust ratings based on circuit context
            severity = self._adjust_severity(
                base_severity, component_info, circuit_context
            )
            occurrence = self._adjust_occurrence(
                base_occurrence, component_info, circuit_context
            )
            detection = self._adjust_detection(base_detection, circuit_context)

            # Generate effect based on component role
            effect = self._generate_effect(comp_type, failure_mode, circuit_context)

            # Generate recommendation
            recommendation = self._generate_recommendation(
                comp_type, failure_mode, severity
            )

            fm = FailureMode(
                component=comp_name,
                component_type=comp_type,
                failure_mode=failure_mode,
                cause=cause,
                effect=effect,
                severity=severity,
                occurrence=occurrence,
                detection=detection,
                recommendation=recommendation,
            )

            failure_modes.append(fm)

        # Add component-specific failure modes based on connections
        if comp_type == ComponentType.MCU:
            # Check for decoupling capacitors
            if not self._has_nearby_capacitor(component_info, circuit_context):
                fm = FailureMode(
                    component=comp_name,
                    component_type=comp_type,
                    failure_mode="Power supply noise",
                    cause="Inadequate decoupling",
                    effect="Logic errors, system instability",
                    severity=7,
                    occurrence=7,
                    detection=6,
                    recommendation="Add 100nF ceramic capacitor within 5mm of power pins",
                )
                failure_modes.append(fm)

        return failure_modes

    def _adjust_severity(self, base: int, component: Dict, context: Dict) -> int:
        """Adjust severity based on component criticality"""
        # Critical components get higher severity
        if "power" in component.get("symbol", "").lower():
            return min(10, base + 1)
        if "mcu" in component.get("symbol", "").lower():
            return min(10, base + 1)
        return base

    def _adjust_occurrence(self, base: int, component: Dict, context: Dict) -> int:
        """Adjust occurrence based on stress factors"""
        # High current/voltage components have higher occurrence
        if "power" in component.get("symbol", "").lower():
            return min(10, base + 1)
        # Connectors have higher mechanical stress
        if component.get("ref", "").startswith("J"):
            return min(10, base + 1)
        return base

    def _adjust_detection(self, base: int, context: Dict) -> int:
        """Adjust detection based on testability"""
        # Assume moderate detection capability by default
        return base

    def _generate_effect(
        self, comp_type: ComponentType, failure_mode: str, context: Dict
    ) -> str:
        """Generate failure effect description"""
        effects = {
            ComponentType.CONNECTOR: {
                "Solder joint failure": "Complete loss of connection, system failure",
                "Contact oxidation": "Intermittent connection, data errors",
                "Mechanical damage": "Connection loss, physical damage",
            },
            ComponentType.REGULATOR: {
                "Thermal shutdown": "System power loss, unexpected reset",
                "Output voltage drift": "Component malfunction, reduced reliability",
                "Input overvoltage failure": "Cascading component damage",
            },
            ComponentType.MCU: {
                "ESD damage": "Complete MCU failure, system inoperable",
                "Clock failure": "System hang, timing errors",
                "Flash corruption": "Firmware corruption, boot failure",
                "I/O pin failure": "Peripheral communication loss",
            },
            ComponentType.CAPACITOR: {
                "Capacitance degradation": "Increased ripple, filtering ineffective",
                "ESR increase": "Power supply instability, heating",
                "Short circuit": "Power rail short, system damage",
            },
        }

        return effects.get(comp_type, {}).get(failure_mode, "Component malfunction")

    def _generate_recommendation(
        self, comp_type: ComponentType, failure_mode: str, severity: int
    ) -> str:
        """Generate recommendations based on failure mode"""
        if severity >= 8:
            prefix = "CRITICAL: "
        elif severity >= 6:
            prefix = "Important: "
        else:
            prefix = ""

        recommendations = {
            "Solder joint failure": f"{prefix}Add mechanical support, use thicker copper pours, implement strain relief",
            "Thermal shutdown": f"{prefix}Improve heatsinking, add thermal vias, consider higher-rated component",
            "ESD damage": f"{prefix}Add TVS diodes, implement ESD protection circuits, use guard rings",
            "Capacitance degradation": f"{prefix}Use higher-grade capacitors, derate voltage, add redundancy",
            "Clock failure": f"{prefix}Add backup oscillator, use temperature-compensated crystal",
        }

        return recommendations.get(
            failure_mode, f"{prefix}Review design and implement appropriate mitigation"
        )

    def _has_nearby_capacitor(self, component: Dict, context: Dict) -> bool:
        """Check if component has nearby decoupling capacitor"""
        # Simplified check - in real implementation would check actual layout
        return True  # Assume yes for now

    def analyze_circuit_file(self, file_path: str) -> Tuple[Dict, List[Dict]]:
        """Analyze a circuit file (Python or JSON) for FMEA"""
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"Circuit file not found: {file_path}")

        circuit_data = {
            "name": file_path.stem,
            "description": f"Circuit analysis of {file_path.name}",
            "component_count": 0,
            "subsystem_count": 0,
            "subsystems": [],
        }

        components = {}
        nets = {}

        if file_path.suffix == ".json":
            # Parse JSON netlist
            with open(file_path, "r") as f:
                data = json.load(f)
                components = data.get("components", {})
                nets = data.get("nets", {})
                circuit_data["component_count"] = len(components)

        elif file_path.suffix == ".py":
            # Parse Python circuit file using dedicated parser
            try:
                parsed_data = extract_components_from_python(str(file_path))
                components = parsed_data.get("components", {})
                nets = parsed_data.get("nets", {})
                circuit_data["component_count"] = len(components)
                circuit_data["description"] = parsed_data.get(
                    "description", f"Python circuit: {file_path.name}"
                )

                # Extract subcircuits as subsystems
                if parsed_data.get("subcircuits"):
                    circuit_data["subsystem_count"] = len(parsed_data["subcircuits"])
                    circuit_data["subsystems"] = [
                        {"name": name, "description": info.get("docstring", "")}
                        for name, info in parsed_data["subcircuits"].items()
                    ]
            except Exception as e:
                print(f"Warning: Could not parse Python file {file_path}: {e}")
                components = {}
                nets = {}

        # Analyze each component
        self.failure_modes = []
        circuit_context = {
            "total_components": len(components),
            "nets": nets,
            "has_power_regulation": any(
                "reg" in str(c).lower() for c in components.values()
            ),
            "has_mcu": any(
                "mcu" in str(c).lower() or "micro" in str(c).lower()
                for c in components.values()
            ),
        }

        if self.verbose:
            print(f"Analyzing {len(components)} components...")

        for comp_ref, comp_info in components.items():
            if isinstance(comp_info, dict):
                comp_info["ref"] = comp_ref
            else:
                # Handle different component formats
                comp_info = {"ref": comp_ref, "symbol": str(comp_info)}

            comp_failures = self.analyze_component(comp_info, circuit_context)
            self.failure_modes.extend(comp_failures)
            self.components_analyzed += 1

        # Sort by RPN (highest risk first)
        self.failure_modes.sort(key=lambda x: x.rpn, reverse=True)

        # Convert to dict format for report
        failure_modes_dict = [fm.to_dict() for fm in self.failure_modes]

        if self.verbose:
            print(f"Identified {len(self.failure_modes)} failure modes")
            print(
                f"Highest risk: {self.failure_modes[0].component} - {self.failure_modes[0].failure_mode} (RPN: {self.failure_modes[0].rpn})"
                if self.failure_modes
                else "No failure modes identified"
            )

        return circuit_data, failure_modes_dict

    def generate_report(
        self, circuit_data: Dict, failure_modes: List[Dict], output_path: str = None
    ) -> str:
        """Generate PDF FMEA report"""
        generator = FMEAReportGenerator(
            project_name=circuit_data.get("name", "Unknown Circuit"),
            author="Circuit-Synth FMEA Analyzer",
        )

        return generator.generate_fmea_report(
            circuit_data=circuit_data,
            failure_modes=failure_modes,
            output_path=output_path,
        )


def analyze_any_circuit(
    circuit_path: str, output_pdf: str = None, verbose: bool = True
) -> str:
    """
    Main entry point to analyze any circuit for FMEA

    Args:
        circuit_path: Path to circuit file (.py, .json, or directory)
        output_pdf: Optional output path for PDF report
        verbose: Print progress messages

    Returns:
        Path to generated PDF report
    """
    analyzer = UniversalFMEAAnalyzer(verbose=verbose)

    # Check if path is directory or file
    path = Path(circuit_path)

    if path.is_dir():
        # Look for circuit files in directory
        json_files = list(path.glob("*.json"))
        py_files = list(path.glob("*.py"))

        if json_files:
            circuit_file = json_files[0]  # Use first JSON file found
        elif py_files:
            circuit_file = py_files[0]  # Use first Python file found
        else:
            raise ValueError(f"No circuit files found in {circuit_path}")
    else:
        circuit_file = path

    if verbose:
        print(f"Analyzing circuit: {circuit_file}")

    # Analyze the circuit
    circuit_data, failure_modes = analyzer.analyze_circuit_file(str(circuit_file))

    # Generate output filename if not provided
    if output_pdf is None:
        output_pdf = f"{circuit_file.stem}_FMEA_Report.pdf"

    # Generate PDF report
    report_path = analyzer.generate_report(circuit_data, failure_modes, output_pdf)

    if verbose and report_path:
        print(f"✅ FMEA Report generated: {report_path}")

        # Print summary statistics
        total = len(failure_modes)
        critical = sum(1 for fm in failure_modes if fm["rpn"] >= 300)
        high = sum(1 for fm in failure_modes if 125 <= fm["rpn"] < 300)

        print(f"📊 Analysis Summary:")
        print(f"  - Total failure modes: {total}")
        print(f"  - Critical risk (RPN ≥ 300): {critical}")
        print(f"  - High risk (125 ≤ RPN < 300): {high}")

    return report_path


if __name__ == "__main__":
    import sys

    if len(sys.argv) < 2:
        print("Usage: python fmea_analyzer.py <circuit_path> [output_pdf]")
        print("  circuit_path: Path to circuit file or directory")
        print("  output_pdf: Optional output PDF filename")
        sys.exit(1)

    circuit_path = sys.argv[1]
    output_pdf = sys.argv[2] if len(sys.argv) > 2 else None

    try:
        report = analyze_any_circuit(circuit_path, output_pdf)
        print(f"Success! Report saved to: {report}")
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)
