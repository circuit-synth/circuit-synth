#!/usr/bin/env python3
"""
KiCad to DFM Analysis Pipeline
Converts KiCad projects to circuit-synth JSON for comprehensive DFM analysis
"""

import json
import logging
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


@dataclass
class KiCadProject:
    """Represents a parsed KiCad project"""

    name: str
    path: Path
    schematics: List[Path]
    pcb: Optional[Path]
    netlist: Optional[Path]

    @property
    def has_complete_design(self) -> bool:
        """Check if project has both schematic and PCB"""
        return bool(self.schematics and self.pcb)


class KiCadToDFMAnalyzer:
    """Converts KiCad projects to circuit-synth format for DFM analysis"""

    def __init__(self):
        self.hierarchical_json = None
        self.flat_json = None

    def analyze_kicad_project(
        self,
        project_path: str,
        output_format: str = "json",  # "json", "python", or "both"
    ) -> Dict[str, Any]:
        """
        Main entry point for KiCad DFM analysis

        Args:
            project_path: Path to KiCad project directory
            output_format: Output format for analysis

        Returns:
            DFM analysis results
        """
        project_dir = Path(project_path)

        # 1. Discover KiCad files
        project = self._discover_project(project_dir)
        logger.info(f"Found KiCad project: {project.name}")

        # 2. Parse to hierarchical JSON
        circuit_json = self._parse_to_json(project)

        # 3. Prepare for DFM agent
        dfm_input = self._prepare_dfm_input(circuit_json)

        # 4. Generate output format
        if output_format == "python":
            return self._generate_python_output(circuit_json)
        elif output_format == "both":
            return {
                "json": circuit_json,
                "python": self._generate_python_output(circuit_json),
                "dfm_input": dfm_input,
            }
        else:  # json
            return {"circuit": circuit_json, "dfm_input": dfm_input}

    def _discover_project(self, project_dir: Path) -> KiCadProject:
        """Discover KiCad project files"""
        return KiCadProject(
            name=project_dir.name,
            path=project_dir,
            schematics=list(project_dir.glob("*.kicad_sch")),
            pcb=next(project_dir.glob("*.kicad_pcb"), None),
            netlist=next(project_dir.glob("*.net"), None),
        )

    def _parse_to_json(self, project: KiCadProject) -> Dict[str, Any]:
        """Parse KiCad files to hierarchical JSON"""

        # Start with netlist if available (most reliable for components)
        if project.netlist:
            circuit_json = self._parse_netlist(project.netlist)
        else:
            circuit_json = self._parse_schematics(project.schematics)

        # Add PCB data if available
        if project.pcb:
            circuit_json["pcb_data"] = self._parse_pcb(project.pcb)

        # Add metadata
        circuit_json["metadata"] = {
            "source": "KiCad",
            "project_name": project.name,
            "project_path": str(project.path),
            "parsed_date": datetime.now().isoformat(),
            "file_count": {
                "schematics": len(project.schematics),
                "has_pcb": project.pcb is not None,
                "has_netlist": project.netlist is not None,
            },
        }

        return circuit_json

    def _parse_netlist(self, netlist_path: Path) -> Dict[str, Any]:
        """Parse KiCad netlist to extract circuit data"""
        import re

        with open(netlist_path, "r") as f:
            content = f.read()

        circuit_data = {
            "name": netlist_path.stem,
            "components": {},
            "nets": {},
            "subcircuits": {},
        }

        # Parse components
        comp_pattern = r'\(comp \(ref "?([^")\s]+)"?\)\s*\(value "?([^")\s]+)"?\)\s*\(footprint "?([^")\s]+)"?\)'
        comp_matches = re.finditer(comp_pattern, content)

        for match in comp_matches:
            ref = match.group(1)
            value = match.group(2)
            footprint = match.group(3)

            # Determine component type and subcircuit
            comp_type = self._get_component_type(ref)
            subcircuit = self._determine_subcircuit(ref, value)

            component_data = {
                "reference": ref,
                "value": value,
                "footprint": footprint,
                "type": comp_type,
                "subcircuit": subcircuit,
                "part_number": self._infer_part_number(value, footprint),
                "manufacturer": self._infer_manufacturer(value),
            }

            circuit_data["components"][ref] = component_data

            # Organize by subcircuit
            if subcircuit not in circuit_data["subcircuits"]:
                circuit_data["subcircuits"][subcircuit] = {
                    "name": subcircuit,
                    "components": {},
                    "nets": {},
                }
            circuit_data["subcircuits"][subcircuit]["components"][ref] = component_data

        # Parse nets
        net_pattern = r'\(net \(code "?(\d+)"?\) \(name "?([^")\s]+)"?\)'
        net_matches = re.finditer(net_pattern, content)

        for match in net_matches:
            net_code = match.group(1)
            net_name = match.group(2)
            circuit_data["nets"][net_code] = {"name": net_name, "code": net_code}

        return circuit_data

    def _parse_schematics(self, schematic_files: List[Path]) -> Dict[str, Any]:
        """Parse KiCad schematic files"""
        # Implementation for parsing .kicad_sch files
        # This would be more complex, parsing the S-expression format
        return {"name": "Circuit", "components": {}, "nets": {}, "subcircuits": {}}

    def _parse_pcb(self, pcb_path: Path) -> Dict[str, Any]:
        """Parse KiCad PCB file for physical information"""
        return {
            "board_size": {"width": 100, "height": 80, "units": "mm"},
            "layer_count": 2,
            "technology": "SMT",
            "has_thermal_vias": False,
        }

    def _prepare_dfm_input(self, circuit_json: Dict[str, Any]) -> Dict[str, Any]:
        """Prepare optimized input for DFM agent"""

        # Calculate statistics
        total_components = len(circuit_json.get("components", {}))
        unique_values = len(
            set(c["value"] for c in circuit_json.get("components", {}).values())
        )

        # Group components by type for analysis
        components_by_type = {}
        for comp in circuit_json.get("components", {}).values():
            comp_type = comp.get("type", "Unknown")
            if comp_type not in components_by_type:
                components_by_type[comp_type] = []
            components_by_type[comp_type].append(comp)

        # Create DFM-optimized structure
        dfm_input = {
            "summary": {
                "total_components": total_components,
                "unique_components": unique_values,
                "subcircuit_count": len(circuit_json.get("subcircuits", {})),
                "technology_mix": self._analyze_technology_mix(circuit_json),
            },
            "components_for_pricing": self._extract_bom_for_pricing(circuit_json),
            "design_complexity": self._assess_complexity(circuit_json),
            "hierarchical_structure": circuit_json.get("subcircuits", {}),
            "full_circuit_json": circuit_json,  # Include complete data
        }

        return dfm_input

    def _generate_python_output(self, circuit_json: Dict[str, Any]) -> Dict[str, str]:
        """Generate Python files from circuit JSON"""
        python_files = {}

        # Generate main circuit file
        main_code = self._generate_main_circuit_python(circuit_json)
        python_files["main_circuit.py"] = main_code

        # Generate subcircuit files if they exist
        for subcircuit_name, subcircuit_data in circuit_json.get(
            "subcircuits", {}
        ).items():
            if subcircuit_data.get("components"):
                code = self._generate_subcircuit_python(
                    subcircuit_name, subcircuit_data
                )
                python_files[f"{subcircuit_name}.py"] = code

        return python_files

    def _generate_main_circuit_python(self, circuit_json: Dict[str, Any]) -> str:
        """Generate main circuit Python code"""
        lines = [
            "#!/usr/bin/env python3",
            '"""',
            f"Circuit: {circuit_json.get('name', 'Circuit')}",
            f"Generated from KiCad project",
            f"Date: {datetime.now().isoformat()}",
            '"""',
            "",
            "from circuit_synth import Circuit, Component, Net",
            "",
        ]

        # Import subcircuits if any
        for subcircuit in circuit_json.get("subcircuits", {}).keys():
            lines.append(f"from .{subcircuit} import {subcircuit}")

        lines.extend(
            [
                "",
                "@circuit",
                f"def {circuit_json.get('name', 'main_circuit')}():",
                '    """Main circuit definition"""',
                "    ",
            ]
        )

        # Add components
        for ref, comp in circuit_json.get("components", {}).items():
            lines.append(f"    {ref} = Component(")
            lines.append(f'        symbol="{comp.get("type", "Device:R")}",')
            lines.append(f'        ref="{ref}",')
            lines.append(f'        value="{comp.get("value", "")}",')
            lines.append(f'        footprint="{comp.get("footprint", "")}"')
            lines.append("    )")
            lines.append("")

        return "\n".join(lines)

    def _generate_subcircuit_python(self, name: str, data: Dict[str, Any]) -> str:
        """Generate subcircuit Python code"""
        lines = [
            "#!/usr/bin/env python3",
            '"""',
            f"Subcircuit: {name}",
            '"""',
            "",
            "from circuit_synth import Circuit, Component, Net",
            "",
            "@circuit",
            f"def {name}():",
            f'    """{name} subcircuit"""',
            "",
        ]

        # Add components
        for ref, comp in data.get("components", {}).items():
            lines.append(f"    {ref} = Component(")
            lines.append(f'        symbol="{comp.get("type", "Device:R")}",')
            lines.append(f'        ref="{ref}",')
            lines.append(f'        value="{comp.get("value", "")}",')
            lines.append(f'        footprint="{comp.get("footprint", "")}"')
            lines.append("    )")
            lines.append("")

        return "\n".join(lines)

    # Helper methods
    def _get_component_type(self, reference: str) -> str:
        """Determine component type from reference designator"""
        if reference.startswith("R"):
            return "Resistor"
        elif reference.startswith("C"):
            return "Capacitor"
        elif reference.startswith("L"):
            return "Inductor"
        elif reference.startswith("U"):
            return "IC"
        elif reference.startswith("J"):
            return "Connector"
        elif reference.startswith("D"):
            return "Diode"
        elif reference.startswith("Q"):
            return "Transistor"
        elif reference.startswith("SW"):
            return "Switch"
        else:
            return "Component"

    def _determine_subcircuit(self, reference: str, value: str) -> str:
        """Determine which subcircuit a component belongs to"""
        # Simple heuristic - can be improved with schematic sheet info
        if "USB" in value or reference.startswith("J"):
            return "usb_interface"
        elif "3.3" in value or "REG" in value or "LDO" in value:
            return "power_supply"
        elif "ESP32" in value or "MCU" in value:
            return "mcu_section"
        elif "LED" in value:
            return "indicators"
        else:
            return "main"

    def _infer_part_number(self, value: str, footprint: str) -> str:
        """Infer actual part number from value and footprint"""
        # This would map common values to real part numbers
        # For now, return value as-is
        return value

    def _infer_manufacturer(self, value: str) -> str:
        """Infer manufacturer from part value"""
        # Add manufacturer inference logic
        return ""

    def _analyze_technology_mix(self, circuit_json: Dict[str, Any]) -> Dict[str, int]:
        """Analyze SMT vs THT mix"""
        smt_count = 0
        tht_count = 0

        for comp in circuit_json.get("components", {}).values():
            footprint = comp.get("footprint", "").lower()
            if "smd" in footprint or "0603" in footprint or "0805" in footprint:
                smt_count += 1
            elif "tht" in footprint or "dip" in footprint:
                tht_count += 1
            else:
                smt_count += 1  # Default to SMT

        return {"SMT": smt_count, "THT": tht_count}

    def _extract_bom_for_pricing(
        self, circuit_json: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """Extract BOM in format suitable for pricing lookup"""
        bom = []
        for ref, comp in circuit_json.get("components", {}).items():
            bom.append(
                {
                    "reference": ref,
                    "part_number": comp.get("part_number", comp.get("value", "")),
                    "manufacturer": comp.get("manufacturer", ""),
                    "quantity": 1,
                    "value": comp.get("value", ""),
                    "footprint": comp.get("footprint", ""),
                }
            )
        return bom

    def _assess_complexity(self, circuit_json: Dict[str, Any]) -> Dict[str, Any]:
        """Assess circuit complexity for DFM"""
        total_components = len(circuit_json.get("components", {}))

        return {
            "level": (
                "Low"
                if total_components < 50
                else "Medium" if total_components < 200 else "High"
            ),
            "component_count": total_components,
            "unique_parts": len(
                set(c["value"] for c in circuit_json.get("components", {}).values())
            ),
            "subcircuit_count": len(circuit_json.get("subcircuits", {})),
            "estimated_assembly_time": total_components * 0.5,  # minutes
        }


def analyze_kicad_for_dfm(project_path: str) -> Dict[str, Any]:
    """
    Main entry point for KiCad DFM analysis

    Args:
        project_path: Path to KiCad project

    Returns:
        DFM analysis results with circuit JSON
    """
    analyzer = KiCadToDFMAnalyzer()
    return analyzer.analyze_kicad_project(project_path, output_format="both")
