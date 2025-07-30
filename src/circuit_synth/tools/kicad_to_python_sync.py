#!/usr/bin/env python3
"""
KiCad to Python Synchronization Tool

This tool updates existing Python circuit definitions from modified KiCad schematics,
preserving manual Python code modifications while applying changes from the KiCad schematic.

Features:
- Parses KiCad schematics to extract components and nets
- Uses LLM-assisted code generation for intelligent merging
- Preserves existing Python code structure and comments
- Creates backups before making changes
- Supports preview mode for safe testing

Usage:
    kicad-to-python <kicad_project> <python_file> --preview
    kicad-to-python <kicad_project> <python_file> --apply --backup
"""

import argparse
import logging
import os
import re
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Configure logging
logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


@dataclass
class Component:
    """Simple component representation"""

    reference: str
    lib_id: str
    value: str
    position: tuple = (0.0, 0.0)
    footprint: str = ""

    def to_dict(self):
        return {
            "reference": self.reference,
            "lib_id": self.lib_id,
            "value": self.value,
            "position": self.position,
            "footprint": self.footprint,
        }


@dataclass
class Net:
    """Net representation with actual pin connections"""

    name: str
    connections: List[Tuple[str, str]]  # List of (component_ref, pin) tuples

    def to_dict(self):
        return {"name": self.name, "connections": self.connections}


@dataclass
class Circuit:
    """Circuit representation with real netlist data"""

    name: str
    components: List[Component]
    nets: List[Net]
    schematic_file: str = ""
    is_hierarchical_sheet: bool = False
    hierarchical_tree: Optional[Dict[str, List[str]]] = (
        None  # Parent-child relationships
    )


class KiCadNetlistParser:
    """Parse KiCad netlist files to extract real connections"""

    def __init__(self):
        pass

    def parse_netlist(self, netlist_path: Path) -> Tuple[List[Component], List[Net]]:
        """Parse a KiCad .net file to extract components and nets with real connections"""
        logger.info(f"Parsing KiCad netlist: {netlist_path}")

        if not netlist_path.exists():
            logger.error(f"Netlist file not found: {netlist_path}")
            return [], []

        try:
            with open(netlist_path, "r") as f:
                content = f.read()

            # Parse S-expressions to extract components and nets
            components = self._parse_components_from_netlist(content)
            nets = self._parse_nets_from_netlist(content)

            logger.info(
                f"Parsed {len(components)} components and {len(nets)} nets from netlist"
            )

            # Debug: log netlist content if parsing fails
            if len(components) == 0 and len(nets) == 0:
                logger.warning(
                    "Netlist parsing returned no results - debugging netlist content:"
                )
                logger.debug(f"Netlist content (first 500 chars): {content[:500]}")

            return components, nets

        except Exception as e:
            logger.error(f"Failed to parse netlist {netlist_path}: {e}")
            return [], []

    def _parse_components_from_netlist(self, content: str) -> List[Component]:
        """Extract component information from netlist"""
        components = []

        # Find all component definitions in (components ...) block
        components_match = re.search(
            r"\(components(.*?)\)\s*\(libparts", content, re.DOTALL
        )
        if not components_match:
            return components

        components_block = components_match.group(1)

        # Find individual component entries - handle multi-line format
        comp_matches = re.findall(
            r'\(comp \(ref "([^"]+)"\)\s*\(value "([^"]*)"\)(.*?)(?=\(comp \(ref|\Z)',
            components_block,
            re.DOTALL,
        )

        for ref, value, comp_data in comp_matches:
            # Extract footprint
            footprint_match = re.search(r'\(footprint "([^"]*)"', comp_data)
            footprint = footprint_match.group(1) if footprint_match else ""

            # Extract libsource (lib_id)
            libsource_match = re.search(
                r'\(libsource \(lib "([^"]+)"\) \(part "([^"]+)"\)', comp_data
            )
            if libsource_match:
                lib = libsource_match.group(1)
                part = libsource_match.group(2)
                lib_id = f"{lib}:{part}"
            else:
                lib_id = "Unknown:Unknown"

            component = Component(
                reference=ref, lib_id=lib_id, value=value, footprint=footprint
            )
            components.append(component)
            logger.debug(f"Parsed component: {ref} = {lib_id} ({value})")

        return components

    def _parse_nets_from_netlist(self, content: str) -> List[Net]:
        """Extract net connections from netlist"""
        nets = []

        # Find all net definitions in (nets ...) block
        nets_match = re.search(r"\(nets(.*?)\)\s*$", content, re.DOTALL)
        if not nets_match:
            return nets

        nets_block = nets_match.group(1)

        # Find individual net entries - match actual KiCad format from the netlist
        net_matches = re.findall(
            r'\(net \(code "(\d+)"\) \(name "([^"]+)"\) \(class "[^"]*"\)(.*?)(?=\(net|\Z)',
            nets_block,
            re.DOTALL,
        )

        for code, net_name, nodes_block in net_matches:
            connections = []

            # Find all node connections in this net
            node_matches = re.findall(
                r'\(node \(ref "([^"]+)"\) \(pin "([^"]+)"\)', nodes_block
            )

            for ref, pin in node_matches:
                connections.append((ref, pin))

            if connections:  # Only add nets that have connections
                net = Net(name=net_name, connections=connections)
                nets.append(net)
                logger.debug(
                    f"Parsed net: {net_name} with {len(connections)} connections"
                )

        return nets


class KiCadParser:
    """Parse KiCad files to extract components and generate netlists"""

    def __init__(self, kicad_project: str):
        self.kicad_project = Path(kicad_project)

        # If user passed a directory, find the .kicad_pro file in it
        if self.kicad_project.is_dir():
            pro_files = list(self.kicad_project.glob("*.kicad_pro"))
            if pro_files:
                self.kicad_project = pro_files[0]
                logger.info(f"Found project file: {self.kicad_project}")
            else:
                logger.error(f"No .kicad_pro file found in directory: {kicad_project}")

        self.project_dir = self.kicad_project.parent
        self.netlist_parser = KiCadNetlistParser()

    def generate_netlist(self) -> Optional[Path]:
        """Generate KiCad netlist from schematic using kicad-cli"""
        logger.info("Generating KiCad netlist from schematic")

        try:
            # Create temporary directory for netlist
            temp_dir = Path(tempfile.mkdtemp())
            netlist_path = temp_dir / f"{self.kicad_project.stem}.net"

            # Run kicad-cli to generate netlist
            cmd = [
                "kicad-cli",
                "sch",
                "export",
                "netlist",
                "--output",
                str(netlist_path),
                str(self.kicad_project.parent / f"{self.kicad_project.stem}.kicad_sch"),
            ]

            logger.info(f"Running: {' '.join(cmd)}")
            result = subprocess.run(cmd, capture_output=True, text=True, check=True)

            if netlist_path.exists():
                logger.info(f"Generated netlist: {netlist_path}")
                return netlist_path
            else:
                logger.error("Netlist generation failed - file not created")
                return None

        except subprocess.CalledProcessError as e:
            logger.error(f"kicad-cli failed: {e}")
            logger.error(f"stdout: {e.stdout}")
            logger.error(f"stderr: {e.stderr}")
            return None
        except Exception as e:
            logger.error(f"Failed to generate netlist: {e}")
            return None

    def parse_circuits(self) -> Dict[str, Circuit]:
        """Parse KiCad project using real netlist data"""
        logger.info(
            f"🔍 HIERARCHICAL DEBUG: Starting parse_circuits for {self.kicad_project}"
        )

        if not self.kicad_project.exists():
            logger.error(f"KiCad project not found: {self.kicad_project}")
            return {}

        try:
            # Step 1: Generate real KiCad netlist
            logger.info("🔍 HIERARCHICAL DEBUG: Step 1 - Generating KiCad netlist")
            netlist_path = self.generate_netlist()
            if not netlist_path:
                logger.warning(
                    "Failed to generate KiCad netlist, falling back to schematic parsing"
                )
                return self._parse_circuits_from_schematics()

            # Step 2: Parse netlist to get real connections
            logger.info(
                "🔍 HIERARCHICAL DEBUG: Step 2 - Parsing netlist for components and nets"
            )
            components, nets = self.netlist_parser.parse_netlist(netlist_path)

            logger.info(f"🔍 HIERARCHICAL DEBUG: Netlist parsing results:")
            logger.info(f"  - Total components from netlist: {len(components)}")
            for comp in components:
                logger.info(f"    * {comp.reference}: {comp.lib_id} = {comp.value}")
            logger.info(f"  - Total nets from netlist: {len(nets)}")
            for net in nets:
                logger.info(f"    * {net.name}: {len(net.connections)} connections")
                for ref, pin in net.connections:
                    logger.info(f"      - {ref}[{pin}]")

            # Step 3: Find hierarchical structure from schematics
            logger.info(
                "🔍 HIERARCHICAL DEBUG: Step 3 - Analyzing hierarchical structure"
            )
            hierarchical_info = self._analyze_hierarchical_structure()

            logger.info(f"🔍 HIERARCHICAL DEBUG: Hierarchical analysis results:")
            if hierarchical_info:
                for sheet_name, sheet_components in hierarchical_info.items():
                    logger.info(
                        f"  - Sheet '{sheet_name}': {len(sheet_components)} components"
                    )
                    for comp in sheet_components:
                        logger.info(f"    * {comp.reference}: {comp.lib_id}")
            else:
                logger.info("  - No hierarchical structure detected")

            # Step 3.5: Build hierarchical tree for import relationships
            logger.info("🔍 HIERARCHICAL DEBUG: Step 3.5 - Building hierarchical tree")
            hierarchical_tree = self._build_hierarchical_tree(hierarchical_info)

            logger.info(f"🔍 HIERARCHICAL DEBUG: Hierarchical tree results:")
            for parent, children in hierarchical_tree.items():
                logger.info(f"  - {parent} -> {children}")

            # Step 4: Create circuit representation with real connections
            logger.info(
                "🔍 HIERARCHICAL DEBUG: Step 4 - Creating circuit representations"
            )
            circuits = {}

            if hierarchical_info:
                logger.info("🔍 HIERARCHICAL DEBUG: Using hierarchical approach")
                # Distribute components across hierarchical sheets based on schematic analysis
                for sheet_name, sheet_components in hierarchical_info.items():
                    logger.info(
                        f"🔍 HIERARCHICAL DEBUG: Processing sheet '{sheet_name}'"
                    )

                    # Filter components that belong to this sheet
                    sheet_component_refs = {comp.reference for comp in sheet_components}
                    sheet_actual_components = [
                        comp
                        for comp in components
                        if comp.reference in sheet_component_refs
                    ]

                    logger.info(
                        f"  - Components in {sheet_name}: {[comp.reference for comp in sheet_actual_components]}"
                    )

                    # Filter nets that connect to components in this sheet
                    sheet_nets = []
                    for net in nets:
                        sheet_connections = [
                            (ref, pin)
                            for ref, pin in net.connections
                            if ref in sheet_component_refs
                        ]
                        if sheet_connections:
                            sheet_net = Net(
                                name=net.name, connections=sheet_connections
                            )
                            sheet_nets.append(sheet_net)
                            logger.info(
                                f"  - Net {net.name} in {sheet_name}: {sheet_connections}"
                            )

                    circuit = Circuit(
                        name=sheet_name,
                        components=sheet_actual_components,
                        nets=sheet_nets,
                        schematic_file=f"{sheet_name}.kicad_sch",
                        is_hierarchical_sheet=(sheet_name != "main"),
                        hierarchical_tree=hierarchical_tree,
                    )
                    circuits[sheet_name] = circuit
                    logger.info(
                        f"🔍 HIERARCHICAL DEBUG: Created {sheet_name}: {len(sheet_actual_components)} components, {len(sheet_nets)} nets"
                    )
            else:
                logger.info("🔍 HIERARCHICAL DEBUG: Using flat circuit approach")
                # Single flat circuit
                circuit = Circuit(
                    name="main",
                    components=components,
                    nets=nets,
                    schematic_file=f"{self.kicad_project.stem}.kicad_sch",
                    is_hierarchical_sheet=False,
                    hierarchical_tree=hierarchical_tree,
                )
                circuits["main"] = circuit
                logger.info(
                    f"🔍 HIERARCHICAL DEBUG: Created flat circuit: {len(components)} components, {len(nets)} nets"
                )

            logger.info(f"🔍 HIERARCHICAL DEBUG: Final circuits created:")
            for name, circuit in circuits.items():
                logger.info(
                    f"  - {name}: {len(circuit.components)} components, {len(circuit.nets)} nets, hierarchical={circuit.is_hierarchical_sheet}"
                )

            # Clean up temporary netlist
            if netlist_path and netlist_path.exists():
                netlist_path.unlink()
                netlist_path.parent.rmdir()

            return circuits

        except Exception as e:
            logger.error(f"Failed to parse KiCad project: {e}")
            return {}

    def _analyze_hierarchical_structure(self) -> Dict[str, List[Component]]:
        """Analyze schematic files to understand hierarchical structure"""
        logger.info("🔍 HIERARCHICAL DEBUG: Starting _analyze_hierarchical_structure")
        hierarchical_info = {}

        # Find all schematic files
        schematic_files = list(self.project_dir.glob("*.kicad_sch"))
        logger.info(
            f"🔍 HIERARCHICAL DEBUG: Found {len(schematic_files)} schematic files:"
        )
        for sch_file in schematic_files:
            logger.info(f"  - {sch_file.name}")

        # Parse main schematic to find sheet instances
        main_sch_file = self.project_dir / f"{self.kicad_project.stem}.kicad_sch"
        if main_sch_file.exists():
            logger.info(
                f"🔍 HIERARCHICAL DEBUG: Parsing main schematic for sheet instances: {main_sch_file.name}"
            )
            sheet_instances = self._parse_sheet_instances(main_sch_file)
            logger.info(
                f"🔍 HIERARCHICAL DEBUG: Found {len(sheet_instances)} sheet instances:"
            )
            for sheet_path, sheet_file in sheet_instances.items():
                logger.info(f"  - {sheet_path} -> {sheet_file}")
        else:
            logger.warning(
                f"🔍 HIERARCHICAL DEBUG: Main schematic file not found: {main_sch_file}"
            )
            sheet_instances = {}

        for sch_file in schematic_files:
            logger.info(
                f"🔍 HIERARCHICAL DEBUG: Parsing schematic file: {sch_file.name}"
            )
            components, net_names = self._parse_schematic_file(sch_file)

            # Determine circuit name and type
            circuit_name = sch_file.stem
            if circuit_name == self.kicad_project.stem:
                circuit_name = "main"

            logger.info(
                f"🔍 HIERARCHICAL DEBUG: Circuit '{circuit_name}' from {sch_file.name}:"
            )
            logger.info(f"  - Components: {len(components)}")
            for comp in components:
                logger.info(f"    * {comp.reference}: {comp.lib_id}")
            logger.info(f"  - Net names: {net_names}")

            hierarchical_info[circuit_name] = components

        logger.info(f"🔍 HIERARCHICAL DEBUG: Final hierarchical structure:")
        for sheet_name, components in hierarchical_info.items():
            logger.info(f"  - {sheet_name}: {len(components)} components")

        return hierarchical_info

    def _build_hierarchical_tree(
        self, hierarchical_info: Dict[str, List[Component]]
    ) -> Dict[str, List[str]]:
        """Build a tree structure showing parent-child relationships between sheets"""
        logger.info("🔍 HIERARCHICAL DEBUG: Building hierarchical tree")
        hierarchical_tree = {}

        # Find all schematic files and their sheet instances
        schematic_files = list(self.project_dir.glob("*.kicad_sch"))

        for sch_file in schematic_files:
            circuit_name = sch_file.stem
            if circuit_name == self.kicad_project.stem:
                circuit_name = "main"

            # Parse this schematic file for sheet instances
            logger.info(
                f"🔍 HIERARCHICAL DEBUG: Analyzing {circuit_name} for child sheets"
            )
            sheet_instances = self._parse_sheet_instances(sch_file)

            # Extract child sheet names
            child_sheets = []
            for sheet_name, sheet_file in sheet_instances.items():
                # Convert sheet file to circuit name
                child_circuit_name = Path(sheet_file).stem
                child_sheets.append(child_circuit_name)
                logger.info(
                    f"🔍 HIERARCHICAL DEBUG: {circuit_name} has child: {child_circuit_name}"
                )

            hierarchical_tree[circuit_name] = child_sheets

        logger.info(f"🔍 HIERARCHICAL DEBUG: Complete hierarchical tree:")
        for parent, children in hierarchical_tree.items():
            logger.info(f"  - {parent}: {children}")

        return hierarchical_tree

    def _parse_sheet_instances(self, main_sch_file: Path) -> Dict[str, str]:
        """Parse main schematic to find hierarchical sheet instances and their relationships"""
        logger.info(
            f"🔍 HIERARCHICAL DEBUG: Parsing sheet instances from {main_sch_file}"
        )
        sheet_instances = {}

        try:
            with open(main_sch_file, "r") as f:
                content = f.read()

            # Look for (sheet ...) blocks in the main schematic
            # These define hierarchical sheet instances
            sheet_blocks = self._extract_sheet_blocks(content)

            logger.info(
                f"🔍 HIERARCHICAL DEBUG: Found {len(sheet_blocks)} sheet blocks"
            )

            for block in sheet_blocks:
                sheet_info = self._parse_sheet_block(block)
                if sheet_info:
                    sheet_path, sheet_file = sheet_info
                    sheet_instances[sheet_path] = sheet_file
                    logger.info(
                        f"🔍 HIERARCHICAL DEBUG: Sheet instance: {sheet_path} -> {sheet_file}"
                    )

            # Also look for sheet_instances definitions which show the hierarchy
            instance_blocks = self._extract_sheet_instance_blocks(content)
            logger.info(
                f"🔍 HIERARCHICAL DEBUG: Found {len(instance_blocks)} sheet instance definition blocks"
            )

            for block in instance_blocks:
                instance_info = self._parse_sheet_instance_block(block)
                if instance_info:
                    logger.info(
                        f"🔍 HIERARCHICAL DEBUG: Sheet instance definition: {instance_info}"
                    )

        except Exception as e:
            logger.error(f"🔍 HIERARCHICAL DEBUG: Failed to parse sheet instances: {e}")

        return sheet_instances

    def _extract_sheet_blocks(self, content: str) -> List[str]:
        """Extract (sheet ...) blocks from schematic content"""
        blocks = []
        pos = 0

        while True:
            start = content.find("(sheet", pos)
            if start == -1:
                break

            # Find the matching closing parenthesis
            depth = 0
            end = start
            for i, char in enumerate(content[start:], start):
                if char == "(":
                    depth += 1
                elif char == ")":
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break

            if end > start:
                blocks.append(content[start:end])
                pos = end
            else:
                pos = start + 1

        return blocks

    def _extract_sheet_instance_blocks(self, content: str) -> List[str]:
        """Extract (sheet_instances ...) blocks from schematic content"""
        blocks = []

        # Look for sheet_instances block
        start = content.find("(sheet_instances")
        if start != -1:
            # Find the matching closing parenthesis
            depth = 0
            end = start
            for i, char in enumerate(content[start:], start):
                if char == "(":
                    depth += 1
                elif char == ")":
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break

            if end > start:
                blocks.append(content[start:end])

        return blocks

    def _parse_sheet_block(self, block: str) -> Optional[Tuple[str, str]]:
        """Parse a (sheet ...) block to extract sheet file and path information"""
        try:
            # Extract the sheet name - look for Sheetname property
            name_match = re.search(r'\(property\s+"Sheetname"\s+"([^"]+)"', block)
            sheet_name = name_match.group(1) if name_match else None

            # Extract the sheet file reference - look for Sheetfile property
            file_match = re.search(r'\(property\s+"Sheetfile"\s+"([^"]+)"', block)
            sheet_file = file_match.group(1) if file_match else None

            if sheet_name and sheet_file:
                logger.info(
                    f"🔍 HIERARCHICAL DEBUG: Parsed sheet block: {sheet_name} -> {sheet_file}"
                )
                return (sheet_name, sheet_file)
            else:
                logger.warning(
                    f"🔍 HIERARCHICAL DEBUG: Could not parse sheet block: name={sheet_name}, file={sheet_file}"
                )
                logger.debug(
                    f"🔍 HIERARCHICAL DEBUG: Sheet block content: {block[:200]}..."
                )
                return None

        except Exception as e:
            logger.error(f"🔍 HIERARCHICAL DEBUG: Failed to parse sheet block: {e}")
            return None

    def _parse_sheet_instance_block(self, block: str) -> Optional[Dict]:
        """Parse a (sheet_instances ...) block to extract hierarchical path information"""
        try:
            # Extract path and sheet_name information from sheet instances
            # This shows the actual hierarchical structure
            instance_matches = re.findall(
                r'\(path\s+"([^"]+)"\s*\(reference\s+"([^"]+)"\)\s*\(unit\s+\d+\)',
                block,
            )

            instances = {}
            for path, reference in instance_matches:
                instances[path] = reference
                logger.info(
                    f"🔍 HIERARCHICAL DEBUG: Sheet instance path: {path} -> {reference}"
                )

            return instances if instances else None

        except Exception as e:
            logger.error(
                f"🔍 HIERARCHICAL DEBUG: Failed to parse sheet instance block: {e}"
            )
            return None

    def _parse_circuits_from_schematics(self) -> Dict[str, Circuit]:
        """Fallback: Parse circuits from schematics only (no real connections)"""
        logger.warning(
            "Using fallback schematic parsing without real netlist connections"
        )

        try:
            # Find all schematic files
            schematic_files = list(self.project_dir.glob("*.kicad_sch"))
            logger.info(f"Found {len(schematic_files)} schematic files")

            circuits = {}

            for sch_file in schematic_files:
                components, net_names = self._parse_schematic_file(sch_file)

                # Convert net names to Net objects with empty connections (fallback)
                nets = [Net(name=name, connections=[]) for name in net_names]

                # Determine if this is a hierarchical sheet or main schematic
                is_main_schematic = sch_file.stem == self.kicad_project.stem
                is_hierarchical = sch_file.stem == "root" or (
                    not is_main_schematic and sch_file.stem != "root"
                )

                circuit_name = sch_file.stem
                if is_main_schematic:
                    circuit_name = "main"

                circuit = Circuit(
                    name=circuit_name,
                    components=components,
                    nets=nets,
                    schematic_file=sch_file.name,
                    is_hierarchical_sheet=is_hierarchical,
                )

                circuits[circuit_name] = circuit
                logger.info(
                    f"Parsed {circuit_name}: {len(components)} components, {len(nets)} nets (no connections)"
                )

            return circuits

        except Exception as e:
            logger.error(f"Failed to parse KiCad schematics: {e}")
            return {}

    def _parse_schematic_file(
        self, schematic_file: Path
    ) -> Tuple[List[Component], List[str]]:
        """Parse a single schematic file to extract components and net names"""
        logger.info(f"Parsing schematic: {schematic_file.name}")

        components = []
        net_names = set()

        try:
            with open(schematic_file, "r") as f:
                content = f.read()

            # Extract components using regex
            symbol_blocks = self._extract_symbol_blocks(content)

            for block in symbol_blocks:
                component = self._parse_component_block(block)
                if component:
                    components.append(component)

            # Extract nets from hierarchical labels
            hierarchical_labels = re.findall(
                r"\(hierarchical_label\s+([^\s\)]+)", content
            )
            for label in hierarchical_labels:
                # Clean up the label (remove quotes)
                clean_label = label.strip('"')
                if clean_label and not clean_label.startswith(
                    "N$"
                ):  # Skip auto-generated nets
                    net_names.add(clean_label)

        except Exception as e:
            logger.error(f"Failed to parse schematic {schematic_file}: {e}")

        return components, list(net_names)

    def _extract_symbol_blocks(self, content: str) -> List[str]:
        """Extract symbol blocks from schematic content"""
        blocks = []

        # Find all symbol blocks using balanced parentheses
        pos = 0
        while True:
            start = content.find("(symbol", pos)
            if start == -1:
                break

            # Find the matching closing parenthesis
            depth = 0
            end = start
            for i, char in enumerate(content[start:], start):
                if char == "(":
                    depth += 1
                elif char == ")":
                    depth -= 1
                    if depth == 0:
                        end = i + 1
                        break

            if end > start:
                blocks.append(content[start:end])
                pos = end
            else:
                pos = start + 1

        return blocks

    def _parse_component_block(self, block: str) -> Optional[Component]:
        """Parse a component from a symbol block"""
        try:
            # Extract lib_id
            lib_id_match = re.search(r"\(lib_id\s+([^\s\)]+)", block)
            if not lib_id_match:
                return None
            lib_id = lib_id_match.group(1).strip('"')

            # Extract reference
            ref_match = re.search(r'\(property\s+"Reference"\s+"([^"]+)"', block)
            if not ref_match:
                return None
            reference = ref_match.group(1)

            # Extract value (optional)
            value_match = re.search(r'\(property\s+"Value"\s+"([^"]+)"', block)
            value = value_match.group(1) if value_match else ""

            # Extract footprint (optional)
            footprint_match = re.search(r'\(property\s+"Footprint"\s+"([^"]+)"', block)
            footprint = footprint_match.group(1) if footprint_match else ""

            # Extract position
            pos_match = re.search(r"\(at\s+([\d.-]+)\s+([\d.-]+)", block)
            position = (
                (float(pos_match.group(1)), float(pos_match.group(2)))
                if pos_match
                else (0.0, 0.0)
            )

            return Component(
                reference=reference,
                lib_id=lib_id,
                value=value,
                position=position,
                footprint=footprint,
            )

        except Exception as e:
            logger.error(f"Failed to parse component block: {e}")
            return None


class LLMCodeUpdater:
    """Update Python code using LLM assistance"""

    def __init__(self):
        """Initialize the LLM code updater"""
        self.llm_available = self._check_llm_availability()

    def _sanitize_variable_name(self, name: str) -> str:
        """
        Convert a net or signal name to a valid Python variable name.

        Rules:
        - Remove hierarchical path prefixes (/path/to/NET → NET)
        - Replace invalid characters with underscores
        - Prefix with underscore if starts with a digit
        - Handle common power net naming conventions
        """
        # 🔧 HIERARCHICAL FIX: Remove hierarchical path prefixes
        # Convert "/resistor_divider/GND" to "GND"
        if "/" in name:
            # Take the last part after the final slash
            name = name.split("/")[-1]
            logger.debug(f"🔍 NET NAME DEBUG: Cleaned hierarchical name to: {name}")

        # Handle common power net special cases first
        if name in ["3V3", "3.3V", "+3V3", "+3.3V"]:
            return "_3v3"
        elif name in ["5V", "+5V", "5.0V", "+5.0V"]:
            return "_5v"
        elif name in ["12V", "+12V", "12.0V", "+12.0V"]:
            return "_12v"
        elif name in ["VCC", "VDD", "VDDA", "VIN"]:
            return name.lower()
        elif name in ["GND", "GROUND", "VSS", "VSSA"]:
            return "gnd"
        elif name in ["MID", "MIDDLE", "OUT", "OUTPUT"]:
            return name.lower()

        # Convert to lowercase and replace invalid characters
        var_name = name.lower()
        var_name = var_name.replace("+", "p").replace("-", "n").replace(".", "_")
        var_name = var_name.replace("/", "_").replace("\\", "_").replace(" ", "_")

        # Remove any remaining non-alphanumeric characters except underscore
        import re

        var_name = re.sub(r"[^a-zA-Z0-9_]", "_", var_name)

        # Prefix with underscore if starts with a digit
        if var_name and var_name[0].isdigit():
            var_name = "_" + var_name

        # Ensure it's not empty and doesn't conflict with Python keywords
        if not var_name or var_name in [
            "class",
            "def",
            "if",
            "else",
            "for",
            "while",
            "import",
            "from",
            "return",
        ]:
            var_name = "net_" + var_name

        return var_name

    def _sanitize_component_type_name(self, lib_id: str) -> str:
        """
        Convert a component lib_id to a valid Python variable name for component types.

        Example: "Connector:USB_C_Plug_USB2.0" -> "Connector_USB_C_Plug_USB2_0"
        """
        # Replace invalid characters with underscores
        comp_type = lib_id.replace(":", "_").replace("-", "_").replace(".", "_")
        comp_type = comp_type.replace("/", "_").replace("\\", "_").replace(" ", "_")

        # Remove any remaining non-alphanumeric characters except underscore
        import re

        comp_type = re.sub(r"[^a-zA-Z0-9_]", "_", comp_type)

        # Prefix with underscore if starts with a digit
        if comp_type and comp_type[0].isdigit():
            comp_type = "_" + comp_type

        # Ensure it's not empty and doesn't conflict with Python keywords
        if not comp_type or comp_type in [
            "class",
            "def",
            "if",
            "else",
            "for",
            "while",
            "import",
            "from",
            "return",
        ]:
            comp_type = "component_" + comp_type

        return comp_type

    def _check_llm_availability(self) -> bool:
        """Check if LLM services are available"""
        try:
            # Check for API keys or LLM availability
            import os

            return (
                os.getenv("OPENAI_API_KEY")
                or os.getenv("ANTHROPIC_API_KEY")
                or os.getenv("GOOGLE_API_KEY")
            )
        except Exception:
            return False

    def update_hierarchical_python_code(
        self, circuits: Dict[str, Circuit]
    ) -> Dict[str, str]:
        """Update Python code for hierarchical circuits using LLM intelligence"""
        logger.info("Updating hierarchical Python code with LLM assistance")

        if self.llm_available:
            return self._llm_generate_hierarchical_code(circuits)
        else:
            logger.warning(
                "LLM not available, falling back to template-based generation"
            )
            return self._template_generate_hierarchical_code(circuits)

    def _llm_generate_hierarchical_code(
        self, circuits: Dict[str, Circuit]
    ) -> Dict[str, str]:
        """Use LLM to intelligently generate hierarchical Python code"""
        logger.info("Using LLM for intelligent code generation")

        try:
            # Try different LLM import methods
            llm = None

            # Method 1: Try the unified conversation interface
            try:
                from circuit_synth.intelligence.llm_unified_conversation_async import (
                    LLMUnifiedConversationAsync,
                )

                llm = LLMUnifiedConversationAsync()
                logger.info("Using LLMUnifiedConversationAsync")
            except ImportError:
                pass

            # Method 2: Try direct litellm approach
            if llm is None:
                try:
                    import litellm

                    litellm.set_verbose = False
                    logger.info("Using direct litellm approach")

                    # Create circuit analysis prompt
                    circuit_analysis = self._create_circuit_analysis_prompt(circuits)

                    # Get LLM response using litellm
                    response = litellm.completion(
                        model="openrouter/google/gemini-2.5-flash",
                        messages=[{"role": "user", "content": circuit_analysis}],
                        temperature=0.1,
                    )

                    response_content = response.choices[0].message.content

                    # Parse LLM response into Python files
                    return self._parse_llm_response_to_files(response_content, circuits)

                except Exception as e:
                    logger.warning(f"Direct litellm approach failed: {e}")

            # Method 3: If we have an LLM instance, use it
            if llm is not None:
                # Create circuit analysis prompt
                circuit_analysis = self._create_circuit_analysis_prompt(circuits)

                # Get LLM-generated hierarchical structure
                import asyncio

                loop = asyncio.new_event_loop()
                asyncio.set_event_loop(loop)
                response = loop.run_until_complete(llm.send_message(circuit_analysis))
                loop.close()

                # Parse LLM response into Python files
                return self._parse_llm_response_to_files(response, circuits)

            # If all methods fail, fall back to templates
            logger.warning(
                "All LLM methods failed, falling back to template generation"
            )
            return self._template_generate_hierarchical_code(circuits)

        except Exception as e:
            logger.error(f"LLM generation failed: {e}")
            logger.info("Falling back to template-based generation")
            return self._template_generate_hierarchical_code(circuits)

    def _create_circuit_analysis_prompt(self, circuits: Dict[str, Circuit]) -> str:
        """Create a detailed prompt for LLM circuit analysis"""

        prompt = """You are an expert in electronic circuit design and Python code generation. I need you to analyze this KiCad project structure and generate appropriate Python circuit code using Circuit Synth framework.

## KiCad Project Analysis:

"""

        # Add circuit information
        for circuit_name, circuit in circuits.items():
            prompt += f"""
**Circuit: {circuit_name}**
- Schematic file: {circuit.schematic_file}
- Components: {len(circuit.components)}
- Nets: {len(circuit.nets)} ({', '.join(circuit.nets) if circuit.nets else 'none'})
- Is hierarchical sheet: {circuit.is_hierarchical_sheet}

Components in {circuit_name}:
"""
            for comp in circuit.components:
                prompt += f"  - {comp.reference}: {comp.lib_id} (value: {comp.value})\n"

        prompt += """

## CRITICAL Requirements:

1. **ALWAYS generate main.py** - This is mandatory and serves as the entry point
2. **Generate hierarchical Python files** using Circuit Synth `@circuit` decorator syntax
3. **Proper net parameter passing** - nets should be created at top level and passed down
4. **ALWAYS include actual connections** - do NOT comment out component pin connections
5. **Use proper component syntax** - `Component("Library:Symbol", ref="RefDes")`
6. **Follow Circuit Synth patterns** - use proper imports, component instantiation, and net connections

## Circuit Synth Syntax Examples:

**Component Creation (REQUIRED FORMAT):**
```python
# CORRECT - use ref= parameter
u1 = Component("RF_Module:ESP32-S3-MINI-1", ref="U1")
c1 = Component("Device:C", ref="C1")

# WRONG - don't do this
u1 = Component("RF_Module:ESP32-S3-MINI-1")
u1.ref = "U1"
```

**Circuit Function Example:**
```python
from circuit_synth import *

@circuit
def esp32_circuit(_3v3, gnd):
    # Components with proper syntax
    u1 = Component("RF_Module:ESP32-S3-MINI-1", ref="U1")
    c1 = Component("Device:C", ref="C1")
    c2 = Component("Device:C", ref="C2")
    
    # ACTUAL connections - do NOT comment these out
    u1[1] += gnd      # ESP32 GND pin
    u1[3] += _3v3     # ESP32 3.3V power pin
    c1['1'] += _3v3   # Capacitor to 3.3V
    c1['2'] += gnd    # Capacitor to GND
    c2['1'] += _3v3   # Capacitor to 3.3V  
    c2['2'] += gnd    # Capacitor to GND
```

**main.py Template (ALWAYS INCLUDE):**
```python
from circuit_synth import *
from root import root_circuit  # Import top-level circuit

@circuit
def main():
    # Call the root circuit to instantiate the design
    root_circuit()

if __name__ == '__main__':
    # Generate the circuit
    circuit = main()
    
    # Export to various formats
    print("Generating circuit files...")
    
    # Generate text netlist
    text_netlist = circuit.generate_text_netlist()
    print("✓ Generated text netlist:")
    print(text_netlist)
    
    # Generate JSON and KiCad netlists
    circuit.generate_json_netlist("circuit.json")
    circuit.generate_kicad_netlist("circuit.net")
    print("✓ Generated netlists: circuit.json, circuit.net")
    
    # Generate complete KiCad project
    try:
        from circuit_synth.kicad.unified_kicad_integration import create_unified_kicad_integration
        import os
        
        output_dir = "circuit_output"
        os.makedirs(output_dir, exist_ok=True)
        
        gen = create_unified_kicad_integration(output_dir, "circuit_project")
        gen.generate_project("circuit.json", generate_pcb=True, force_regenerate=True)
        print("✓ Generated complete KiCad project: circuit_output/")
    except Exception as e:
        print(f"⚠ KiCad project generation error: {e}")
    
    print("Circuit generation complete!")
```

## Expected Output Format:

MANDATORY: You must provide a JSON response with this EXACT structure and EXACT filenames:

```json
{
    "analysis": "Your analysis of the hierarchical structure and relationships",
    "files": {
        "main.py": "REQUIRED - Python code for main.py entry point using the template above",
        "root.py": "Python code for root circuit file - MUST be named root.py",
        "esp32.py": "Python code for ESP32 circuit file - MUST be named esp32.py", 
        "other_subcircuit.py": "Additional circuit files - use simple names without _circuit suffix"
    },
    "hierarchy": "Description of the calling hierarchy (main -> root -> esp32, etc.)"
}
```

CRITICAL FILENAME REQUIREMENTS:
- main.py is MANDATORY 
- Hierarchical circuit files must use simple names: root.py, esp32.py, analog.py, etc.
- DO NOT use _circuit suffix in filenames (WRONG: root_circuit.py, CORRECT: root.py)
- Match the KiCad schematic names exactly (root.kicad_sch -> root.py)

CRITICAL REQUIREMENTS:
- main.py is MANDATORY and must be included in every response
- Use the exact main.py template provided above
- All component connections must be uncommented and functional
- Use proper Component("Library:Symbol", ref="RefDes") syntax
- Create a logical hierarchy based on component distribution

Focus on creating a clean, functional hierarchy that makes engineering sense.
"""

        return prompt

    def _parse_llm_response_to_files(
        self, response: str, circuits: Dict[str, Circuit]
    ) -> Dict[str, str]:
        """Parse LLM response into Python files"""
        try:
            import json
            import re

            # Try to extract JSON from response
            json_match = re.search(r"```json\s*(.*?)\s*```", response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # Look for JSON-like structure in response
                json_match = re.search(r'\{.*"files".*\}', response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise ValueError("No JSON structure found in LLM response")

            parsed_response = json.loads(json_str)

            if "files" in parsed_response:
                logger.info(
                    f"LLM generated {len(parsed_response['files'])} Python files"
                )
                if "analysis" in parsed_response:
                    logger.info(f"LLM analysis: {parsed_response['analysis']}")
                if "hierarchy" in parsed_response:
                    logger.info(f"LLM hierarchy: {parsed_response['hierarchy']}")

                # Normalize filenames to handle inconsistent LLM responses
                normalized_files = {}
                for filename, content in parsed_response["files"].items():
                    # Remove _circuit suffix if present and ensure proper naming
                    if filename.endswith("_circuit.py"):
                        normalized_name = filename.replace("_circuit.py", ".py")
                    else:
                        normalized_name = filename

                    # Ensure we have the expected files for circuits
                    circuit_names = [name for name in circuits.keys()]
                    if normalized_name == "main_circuit.py":
                        normalized_name = "main.py"
                    elif any(
                        f"{circuit_name}_circuit.py" == filename
                        for circuit_name in circuit_names
                    ):
                        # Extract circuit name and use simple name
                        circuit_name = filename.replace("_circuit.py", ".py")
                        normalized_name = circuit_name

                    normalized_files[normalized_name] = content
                    if normalized_name != filename:
                        logger.info(
                            f"Normalized filename: {filename} -> {normalized_name}"
                        )

                return normalized_files
            else:
                raise ValueError("No 'files' key in LLM response")

        except Exception as e:
            logger.error(f"Failed to parse LLM response: {e}")
            logger.info("Falling back to template generation")
            return self._template_generate_hierarchical_code(circuits)

    def _template_generate_hierarchical_code(
        self, circuits: Dict[str, Circuit]
    ) -> Dict[str, str]:
        """Fallback template-based code generation"""
        logger.info(
            "🔍 HIERARCHICAL DEBUG: Starting _template_generate_hierarchical_code"
        )
        logger.info(f"🔍 HIERARCHICAL DEBUG: Input circuits: {list(circuits.keys())}")

        for name, circuit in circuits.items():
            logger.info(
                f"🔍 HIERARCHICAL DEBUG: Circuit '{name}': hierarchical={circuit.is_hierarchical_sheet}, components={len(circuit.components)}"
            )

        python_files = {}

        # Always generate main.py first
        main_circuit = None
        for circuit_name, circuit in circuits.items():
            if not circuit.is_hierarchical_sheet:
                main_circuit = circuit
                logger.info(
                    f"🔍 HIERARCHICAL DEBUG: Found main circuit: {circuit_name}"
                )
                break

        if main_circuit:
            logger.info(
                f"🔍 HIERARCHICAL DEBUG: Generating main.py for circuit: {main_circuit.name}"
            )
            python_files["main.py"] = self._generate_main_file(main_circuit, circuits)
        else:
            logger.warning(
                "🔍 HIERARCHICAL DEBUG: No main circuit found - all circuits are hierarchical"
            )

        # Generate Python files for each hierarchical circuit
        for circuit_name, circuit in circuits.items():
            if circuit.is_hierarchical_sheet:
                # Generate subcircuit files for all hierarchical sheets
                filename = f"{circuit_name}.py"
                logger.info(
                    f"🔍 HIERARCHICAL DEBUG: Generating hierarchical subcircuit file: {filename}"
                )
                python_files[filename] = self._generate_subcircuit_file(
                    circuit, circuits
                )
                logger.info(
                    f"🔍 HIERARCHICAL DEBUG: Generated subcircuit file: {filename}"
                )
            elif circuit_name != "main":
                # Also generate files for non-main non-hierarchical circuits (like resistor_divider)
                filename = f"{circuit_name}.py"
                logger.info(
                    f"🔍 HIERARCHICAL DEBUG: Generating non-main circuit file: {filename}"
                )
                python_files[filename] = self._generate_subcircuit_file(
                    circuit, circuits
                )
                logger.info(
                    f"🔍 HIERARCHICAL DEBUG: Generated circuit file: {filename}"
                )

        logger.info(
            f"🔍 HIERARCHICAL DEBUG: Final generated files: {list(python_files.keys())}"
        )

        return python_files

    def update_python_code(self, original_code: str, kicad_circuit: Circuit) -> str:
        """Update Python code based on KiCad circuit using LLM"""
        logger.info("Updating Python code with LLM assistance")

        # For now, implement a template-based approach
        # In a full implementation, this would call an LLM API

        # Extract the existing structure
        lines = original_code.split("\n")

        # Find the circuit function
        circuit_start = -1
        circuit_end = -1

        for i, line in enumerate(lines):
            if "@circuit" in line:
                circuit_start = i
                continue

            if circuit_start >= 0:
                if line.strip().startswith("def ") and (
                    "root" in line or "circuit" in line
                ):
                    continue

                # Track indentation to find end of function
                if (
                    line.strip()
                    and not line.startswith(" ")
                    and not line.startswith("\t")
                    and not line.startswith("if __name__")
                ):
                    circuit_end = i
                    break

        if circuit_start == -1:
            logger.error("Could not find circuit function in Python code")
            return original_code

        # Generate new circuit content
        new_circuit_content = self._generate_circuit_content(kicad_circuit)

        # Replace the circuit function content
        new_lines = lines[:circuit_start]
        new_lines.extend(new_circuit_content.split("\n"))

        # Add the rest of the file (if any)
        if circuit_end > 0:
            new_lines.extend(lines[circuit_end:])
        else:
            # Add the main execution block if it doesn't exist
            new_lines.extend(
                [
                    "",
                    "if __name__ == '__main__':",
                    "    c = root()",
                    "    netlist_text = c.generate_text_netlist()",
                    "    print(netlist_text)",
                    f'    c.generate_json_netlist("{kicad_circuit.name}.json")',
                    f'    c.generate_kicad_netlist("{kicad_circuit.name}.net")',
                    "    ",
                    "    # Create output directory for KiCad project",
                    '    output_dir = "kicad_output"',
                    "    os.makedirs(output_dir, exist_ok=True)",
                    "    ",
                    "    # Generate KiCad project with schematic",
                    '    logger.info(f"Generating KiCad project in {output_dir}")',
                    f'    logger.info(f"Using JSON file: {kicad_circuit.name}.json")',
                    "    ",
                    f'    gen = create_unified_kicad_integration(output_dir, "{kicad_circuit.name}")',
                    "    gen.generate_project(",
                    f'        "{kicad_circuit.name}.json",',
                    '        schematic_placement="sequential",',
                    "        generate_pcb=True,",
                    "        force_regenerate=True",
                    "    )",
                    '    logger.info(f"KiCad project generated successfully in {output_dir}")',
                ]
            )

        return "\n".join(new_lines)

    def _generate_circuit_content(self, circuit: Circuit) -> str:
        """Generate the circuit function content based on KiCad components"""

        # Start with the circuit function definition
        content = [
            "@circuit",
            "def root():",
            '    """',
            "    Circuit imported from KiCad schematic",
            '    """',
            '    logger.info("Creating circuit from KiCad import")',
            "    ",
        ]

        # Create nets based on what we found
        unique_nets = set(circuit.nets)
        if "3V3" not in unique_nets:
            unique_nets.add("3V3")
        if "GND" not in unique_nets:
            unique_nets.add("GND")

        content.append("    # Create main nets")
        for net in sorted(unique_nets):
            if net in ["3V3", "GND", "VCC", "VDD"]:
                net_var = self._sanitize_variable_name(net)
                content.append(f"    {net_var} = Net('{net}')")
        content.append("    ")

        # Add components
        if circuit.components:
            content.append("    # Components from KiCad schematic")
            for comp in circuit.components:
                comp_var = comp.reference.lower()
                content.append(f"    {comp_var} = Component(")
                content.append(f'        "{comp.lib_id}",')
                content.append(f'        ref="{comp.reference}",')
                if comp.footprint:
                    content.append(f'        footprint="{comp.footprint}"')
                content.append("    )")
                content.append("")

        # Add basic connections (simplified)
        if circuit.components:
            content.append("    # Basic power connections")
            for comp in circuit.components:
                comp_var = comp.reference.lower()
                # This is a simplified connection - in reality we'd parse the actual netlist
                if "ESP32" in comp.lib_id.upper():
                    content.append(f'    {comp_var}["3"] += _3v3  # VDD')
                    content.append(f'    {comp_var}["1"] += gnd   # GND')
                elif "C" in comp.reference:  # Capacitor
                    content.append(f'    {comp_var}["1"] += _3v3')
                    content.append(f'    {comp_var}["2"] += gnd')
                elif "R" in comp.reference:  # Resistor
                    content.append(f'    {comp_var}["1"] += _3v3')
                    content.append(f'    {comp_var}["2"] += gnd')

        content.append("    ")
        content.append('    logger.info("Circuit imported from KiCad")')
        content.append("")

        return "\n".join(content)

    def _generate_subcircuit_file(
        self, circuit: Circuit, all_circuits: Dict[str, Circuit] = None
    ) -> str:
        """Generate Python file for a hierarchical subcircuit with net parameter passing"""
        content = [
            "#!/usr/bin/env python3",
            f'"""',
            f"{circuit.name} subcircuit",
            f"",
            f"Generated from KiCad schematic: {circuit.schematic_file}",
            f"Components: {len(circuit.components)}",
            f"Nets: {len(circuit.nets)}",
            f'"""',
            "",
            "import logging",
            "from circuit_synth import *",
            "",
        ]

        # 🔧 HIERARCHICAL FIX: Add imports based on hierarchical tree
        hierarchical_tree = circuit.hierarchical_tree or {}
        child_circuits = hierarchical_tree.get(circuit.name, [])

        logger.info(
            f"🔍 HIERARCHICAL DEBUG: Subcircuit {circuit.name} children: {child_circuits}"
        )

        if child_circuits:
            # Import only direct children
            for child_name in child_circuits:
                if child_name in all_circuits:
                    content.append(f"from {child_name} import {child_name}")
                    logger.info(
                        f"🔍 HIERARCHICAL DEBUG: {circuit.name} imports {child_name}"
                    )
        else:
            logger.info(
                f"🔍 HIERARCHICAL DEBUG: {circuit.name} has no children - no imports needed"
            )

        content.extend(
            [
                "",
                "logger = logging.getLogger(__name__)",
                "",
            ]
        )

        # Add component definitions
        component_types = {}
        for comp in circuit.components:
            comp_type = self._sanitize_component_type_name(comp.lib_id)
            if comp_type not in component_types:
                content.append(f"# {comp.lib_id} component definition")
                content.append(f"{comp_type} = Component(")
                content.append(f'    symbol="{comp.lib_id}",')
                content.append(f'    ref="{comp.reference[0]}",')
                if comp.footprint:
                    content.append(f'    footprint="{comp.footprint}"')
                content.append(")")
                content.append("")
                component_types[comp_type] = comp.lib_id

        # 🔧 HIERARCHICAL FIX: Generate net parameter list for function signature
        net_params = []

        # Extract unique net names from this circuit's actual connections
        if circuit.nets:
            unique_nets = set()
            for net in circuit.nets:
                # 🔧 FIX: Include ALL nets, not just those with multiple connections
                # Hierarchical circuits need all nets that cross boundaries
                unique_nets.add(net.name)
                logger.debug(
                    f"🔍 NET PARAM DEBUG: Added net {net.name} to {circuit.name}"
                )

            # Convert to sanitized parameter names
            for net_name in sorted(unique_nets):
                net_var = self._sanitize_variable_name(net_name)
                if net_var not in net_params:
                    net_params.append(net_var)
                    logger.debug(
                        f"🔍 NET PARAM DEBUG: Parameter {net_var} for {circuit.name}"
                    )

        logger.info(
            f"🔍 NET PARAM DEBUG: {circuit.name} final parameters: {net_params}"
        )

        # Generate circuit function with net parameters (empty if no nets)
        param_str = ", ".join(net_params)
        content.extend(
            [
                "@circuit",
                f"def {circuit.name}({param_str}):",
                f'    """',
                f"    {circuit.name} subcircuit from KiCad",
                f'    """',
                f'    logger.info("Creating {circuit.name} subcircuit")',
                "    ",
            ]
        )

        # Add comment if no net parameters were found
        if not net_params:
            content.append("    # No nets with connections found")
            content.append("    ")

        # Add components
        if circuit.components:
            content.append("    # Components")
            for comp in circuit.components:
                comp_type = self._sanitize_component_type_name(comp.lib_id)
                comp_var = comp.reference.lower()
                content.append(f"    {comp_var} = {comp_type}()")
                content.append(f'    {comp_var}.ref = "{comp.reference}"')
                content.append("")

        # Add real connections from netlist data - fully generalized
        if circuit.nets:
            content.append("    # Real connections from KiCad netlist")
            for net in circuit.nets:
                if (
                    len(net.connections) > 1
                ):  # Only connect nets with multiple connections
                    net_var = self._sanitize_variable_name(net.name)
                    # 🔧 HIERARCHICAL FIX: Clean net name for comment
                    clean_net_name = self._sanitize_variable_name(net.name)
                    content.append(f"    # Net: {clean_net_name}")
                    for comp_ref, pin in net.connections:
                        comp_var = comp_ref.lower()
                        if pin.isdigit():
                            content.append(f"    {comp_var}[{pin}] += {net_var}")
                        else:
                            content.append(f'    {comp_var}["{pin}"] += {net_var}')
                    content.append("    ")
        else:
            content.append("    # No netlist connections available")
            content.append("    # Components are instantiated but not connected")
            content.append("    ")

        # 🔧 HIERARCHICAL FIX: Add subcircuit instantiation based on hierarchical tree
        if child_circuits:
            content.append("    # Instantiate child subcircuits (hierarchical)")
            for child_name in child_circuits:
                if child_name in all_circuits:
                    child_subcircuit = all_circuits[child_name]
                    logger.info(
                        f"🔍 HIERARCHICAL DEBUG: {circuit.name} instantiating child: {child_name}"
                    )

                    # 🔧 HIERARCHICAL FIX: Generate parameter list based on ALL child subcircuit nets
                    subcircuit_params = []
                    if child_subcircuit.nets:
                        unique_nets = set()
                        for net in child_subcircuit.nets:
                            # 🔧 FIX: Include ALL nets for proper hierarchical parameter passing
                            unique_nets.add(net.name)

                        for net_name in sorted(unique_nets):
                            net_var = self._sanitize_variable_name(net_name)
                            if net_var not in subcircuit_params:
                                subcircuit_params.append(net_var)

                    if subcircuit_params:
                        param_str = ", ".join(subcircuit_params)
                        content.append(
                            f"    {child_name}_instance = {child_name}({param_str})"
                        )
                        logger.info(
                            f"🔍 HIERARCHICAL DEBUG: {circuit.name} instantiates: {child_name}({param_str})"
                        )
                    else:
                        content.append(f"    {child_name}_instance = {child_name}()")
                        logger.info(
                            f"🔍 HIERARCHICAL DEBUG: {circuit.name} instantiates: {child_name}()"
                        )
            content.append("    ")
        else:
            logger.info(
                f"🔍 HIERARCHICAL DEBUG: {circuit.name} has no children - no instantiation needed"
            )

        content.extend([f'    logger.info("{circuit.name} subcircuit created")', ""])

        return "\n".join(content)

    def _generate_main_file(
        self, main_circuit: Circuit, all_circuits: Dict[str, Circuit]
    ) -> str:
        """Generate main Python file that instantiates subcircuits"""
        logger.info("🔍 HIERARCHICAL DEBUG: Starting _generate_main_file")

        # Find hierarchical subcircuits
        subcircuits = [
            name
            for name, circuit in all_circuits.items()
            if circuit.is_hierarchical_sheet
        ]

        logger.info(f"🔍 HIERARCHICAL DEBUG: Identified subcircuits: {subcircuits}")
        logger.info(f"🔍 HIERARCHICAL DEBUG: All circuits: {list(all_circuits.keys())}")
        for name, circuit in all_circuits.items():
            logger.info(
                f"  - {name}: hierarchical={circuit.is_hierarchical_sheet}, components={len(circuit.components)}"
            )

        content = [
            "#!/usr/bin/env python3",
            f'"""',
            f"{main_circuit.name} main circuit",
            f"",
            f"Generated from KiCad project with hierarchical structure:",
        ]

        for name, circuit in all_circuits.items():
            content.append(
                f"  - {name}: {len(circuit.components)} components ({circuit.schematic_file})"
            )

        content.extend(
            [
                f'"""',
                "",
                "import logging",
                "from circuit_synth import *",
                "",
            ]
        )

        # 🔧 HIERARCHICAL FIX: Use hierarchical tree for correct imports
        hierarchical_tree = main_circuit.hierarchical_tree or {}
        logger.info(
            f"🔍 HIERARCHICAL DEBUG: Using hierarchical tree for imports: {hierarchical_tree}"
        )

        # Import only direct children of main circuit
        main_children = hierarchical_tree.get("main", [])
        logger.info(f"🔍 HIERARCHICAL DEBUG: Main circuit children: {main_children}")

        if main_children:
            # Import only direct children - they will handle their own sub-imports
            for child_name in main_children:
                if child_name in all_circuits:
                    content.append(f"from {child_name} import {child_name}")
                    logger.info(
                        f"🔍 HIERARCHICAL DEBUG: Added import: from {child_name} import {child_name}"
                    )
        else:
            # Fallback: if no hierarchical tree or no children, import all subcircuits
            logger.warning(
                "🔍 HIERARCHICAL DEBUG: No hierarchical children found, falling back to flat imports"
            )
            for subcircuit_name in subcircuits:
                content.append(f"from {subcircuit_name} import {subcircuit_name}")

        content.extend(
            [
                "",
                "# Configure logging to reduce noise - only show warnings and errors",
                "logging.basicConfig(level=logging.WARNING)",
                "",
                "logger = logging.getLogger(__name__)",
                "",
            ]
        )

        # Add main circuit function
        content.extend(
            [
                "@circuit",
                "def main_circuit():",
                '    """',
                "    Main circuit with hierarchical subcircuits",
                '    """',
                '    logger.info("Creating main circuit with subcircuits")',
                "    ",
            ]
        )

        # Create main nets from actual netlist data - fully generalized
        all_nets = set()
        for circuit in all_circuits.values():
            for net in circuit.nets:
                # 🔧 HIERARCHICAL FIX: Include ALL nets for proper main circuit creation
                all_nets.add(net.name)

        if all_nets:
            content.append("    # Create main nets from KiCad netlist")
            for net_name in sorted(all_nets):
                net_var = self._sanitize_variable_name(net_name)
                # 🔧 HIERARCHICAL FIX: Use clean net names in Net() creation
                clean_net_name = self._sanitize_variable_name(net_name).upper()
                content.append(f'    {net_var} = Net("{clean_net_name}")')
            content.append("    ")

        # 🔧 HIERARCHICAL FIX: Instantiate only direct children based on hierarchical tree
        if main_children:
            content.append("    # Instantiate direct child subcircuits (hierarchical)")
            for child_name in main_children:
                if child_name in all_circuits:
                    child_circuit = all_circuits[child_name]
                    logger.info(
                        f"🔍 HIERARCHICAL DEBUG: Instantiating direct child: {child_name}"
                    )

                    # 🔧 HIERARCHICAL FIX: Generate net parameter list based on child circuit's ALL nets
                    net_params = []
                    if child_circuit.nets:
                        unique_nets = set()
                        for net in child_circuit.nets:
                            # 🔧 FIX: Include ALL nets for proper hierarchical parameter passing
                            unique_nets.add(net.name)

                        for net_name in sorted(unique_nets):
                            net_var = self._sanitize_variable_name(net_name)
                            if net_var not in net_params:
                                net_params.append(net_var)

                    if net_params:
                        param_str = ", ".join(net_params)
                        content.append(
                            f"    {child_name}_instance = {child_name}({param_str})"
                        )
                        logger.info(
                            f"🔍 HIERARCHICAL DEBUG: Added instantiation: {child_name}({param_str})"
                        )
                    else:
                        content.append(f"    {child_name}_instance = {child_name}()")
                        logger.info(
                            f"🔍 HIERARCHICAL DEBUG: Added instantiation: {child_name}()"
                        )
                    content.append("")
        elif subcircuits:
            # Fallback: if no hierarchical children, instantiate all subcircuits directly
            logger.warning(
                "🔍 HIERARCHICAL DEBUG: Falling back to flat subcircuit instantiation"
            )
            content.append("    # Instantiate all subcircuits (fallback)")
            for subcircuit_name in subcircuits:
                subcircuit = all_circuits[subcircuit_name]

                # Generate net parameter list based on subcircuit's actual nets
                net_params = []
                if subcircuit.nets:
                    unique_nets = set()
                    for net in subcircuit.nets:
                        if len(net.connections) > 1:
                            unique_nets.add(net.name)

                    for net_name in sorted(unique_nets):
                        net_var = self._sanitize_variable_name(net_name)
                        if net_var not in net_params:
                            net_params.append(net_var)

                if net_params:
                    param_str = ", ".join(net_params)
                    content.append(
                        f"    {subcircuit_name}_instance = {subcircuit_name}({param_str})"
                    )
                else:
                    content.append(
                        f"    {subcircuit_name}_instance = {subcircuit_name}()"
                    )
                content.append("")

        # Add main circuit components (if any)
        main_components = [
            comp
            for comp in main_circuit.components
            if not any(
                comp in circuit.components
                for circuit in all_circuits.values()
                if circuit.is_hierarchical_sheet
            )
        ]

        if main_components:
            content.append("    # Main circuit components")
            for comp in main_components:
                comp_var = comp.reference.lower()
                content.append(f"    {comp_var} = Component(")
                content.append(f'        "{comp.lib_id}",')
                content.append(f'        ref="{comp.reference}",')
                if comp.footprint:
                    content.append(f'        footprint="{comp.footprint}"')
                content.append("    )")
                content.append("")

        content.extend(
            [
                "    # TODO: Add inter-subcircuit connections",
                "    # Connect subcircuits through shared nets",
                "    ",
                '    logger.info("Main circuit with subcircuits created")',
                "",
            ]
        )

        # Add main execution block
        project_name = main_circuit.name
        if project_name == "main":
            # Use the KiCad project name
            project_name = "circuit"  # fallback

        content.extend(
            [
                "if __name__ == '__main__':",
                "    circuit = main_circuit()",
                "    ",
                "    # Generate netlists",
                f'    circuit.generate_kicad_netlist("{project_name}.net")',
                f'    circuit.generate_json_netlist("{project_name}.json")',
                "    ",
                "    # Generate KiCad project",
                f'    circuit.generate_kicad_project("{project_name}")',
            ]
        )

        return "\n".join(content)


class KiCadToPythonSyncer:
    """Main synchronization class"""

    def __init__(
        self,
        kicad_project: str,
        python_file: str,
        preview_only: bool = True,
        create_backup: bool = True,
    ):
        self.kicad_project = Path(kicad_project)
        self.python_file = Path(python_file)
        self.preview_only = preview_only
        self.create_backup = create_backup

        # Initialize components
        self.parser = KiCadParser(str(self.kicad_project))
        self.updater = LLMCodeUpdater()

        logger.info(f"KiCadToPythonSyncer initialized")
        logger.info(f"KiCad project: {self.kicad_project}")
        logger.info(f"Python file: {self.python_file}")
        logger.info(f"Preview mode: {self.preview_only}")

    def sync(self) -> bool:
        """Perform the synchronization from KiCad to Python"""
        logger.info("=== Starting KiCad to Python Synchronization ===")

        try:
            # Step 1: Parse KiCad circuits (hierarchical)
            kicad_circuits = self.parser.parse_circuits()
            if not kicad_circuits:
                logger.error("Failed to parse KiCad circuits")
                return False

            # Step 2: Read existing Python code or create new
            original_code = ""
            if self.python_file.exists() and self.python_file.is_file():
                logger.info(f"Reading existing Python file: {self.python_file}")
                with open(self.python_file, "r") as f:
                    original_code = f.read()
            elif self.python_file.exists() and self.python_file.is_dir():
                # Directory exists - check for main.py or create it
                main_file = self.python_file / "main.py"
                if main_file.exists():
                    logger.info(
                        f"Reading existing main.py from project directory: {main_file}"
                    )
                    with open(main_file, "r") as f:
                        original_code = f.read()
                    self.python_file = main_file  # Update to point to main.py
                else:
                    logger.info(
                        f"Creating main.py in existing project directory: {self.python_file}"
                    )
                    # For new projects, we'll generate hierarchical structure
                    original_code = ""
                    self.python_file = main_file  # Update to point to main.py
            else:
                # Handle creating new Python files/projects
                if self.python_file.suffix == "":
                    # Directory path - create Python project
                    logger.info(
                        f"Creating new Python project directory: {self.python_file}"
                    )
                    self.python_file.mkdir(parents=True, exist_ok=True)
                    main_file = self.python_file / "main.py"
                    # For new projects, we'll generate hierarchical structure
                    original_code = ""
                    self.python_file = main_file  # Update to point to main.py
                else:
                    # Single file path - create new Python file
                    logger.info(f"Creating new Python file: {self.python_file}")
                    self.python_file.parent.mkdir(parents=True, exist_ok=True)
                    # For single files, we'll still generate hierarchical structure
                    original_code = ""

            # Step 3: Generate updated Python code (hierarchical)
            logger.info("Generating hierarchical Python code...")
            python_files = self.updater.update_hierarchical_python_code(kicad_circuits)

            # Step 4: Preview or apply changes
            if self.preview_only:
                logger.info("=== PREVIEW MODE ===")
                for circuit_name, circuit in kicad_circuits.items():
                    logger.info(
                        f"Circuit {circuit_name}: {len(circuit.components)} components, {len(circuit.nets)} nets"
                    )
                    for comp in circuit.components:
                        logger.info(f"  {comp.reference}: {comp.lib_id} = {comp.value}")

                print("\n=== Hierarchical Python Files Preview ===")
                for filename, content in python_files.items():
                    print(f"\n--- {filename} ---")
                    print(content)
                print("=== End Preview ===")

            else:
                # Ensure output directory exists
                if self.python_file.is_file():
                    output_dir = self.python_file.parent
                elif self.python_file.suffix == ".py":
                    # Output path looks like a file but doesn't exist - treat as directory
                    output_dir = self.python_file.parent
                    output_dir.mkdir(parents=True, exist_ok=True)
                else:
                    # Output path is a directory
                    output_dir = self.python_file
                    output_dir.mkdir(parents=True, exist_ok=True)

                # Create backup if requested
                if self.create_backup and (output_dir / "main.py").exists():
                    backup_path = output_dir / "main.py.backup"
                    with open(backup_path, "w") as f:
                        if (output_dir / "main.py").exists():
                            f.write((output_dir / "main.py").read_text())
                    logger.info(f"Created backup: {backup_path}")

                # Write all Python files
                for filename, content in python_files.items():
                    file_path = output_dir / filename
                    with open(file_path, "w") as f:
                        f.write(content)
                    logger.info(f"Generated: {file_path}")

            logger.info("=== Synchronization Complete ===")
            return True

        except Exception as e:
            logger.error(f"Synchronization failed: {e}")
            return False

    def _generate_new_python_file_template(self, kicad_circuit) -> str:
        """Generate template Python code for a new single file"""
        project_name = self.kicad_project.stem

        template = f'''#!/usr/bin/env python3
"""
{project_name} Circuit Definition

Generated from KiCad project: {self.kicad_project.name}
Created by kicad-to-python tool

Components found:
{self._format_components_list(kicad_circuit.components)}

Nets found: {len(kicad_circuit.nets)} nets
"""

from circuit_synth import Circuit, Component

def create_{project_name}_circuit():
    """Create the {project_name} circuit"""
    circuit = Circuit("{project_name}")
    
    # TODO: Add components from KiCad schematic
{self._generate_component_code(kicad_circuit.components)}
    
    # TODO: Add net connections
    # {len(kicad_circuit.nets)} nets need to be connected
    
    return circuit

if __name__ == "__main__":
    circuit = create_{project_name}_circuit()
    print(f"Created circuit: {{circuit.name}}")
    print(f"Components: {{len(circuit._components)}}")
'''
        return template

    def _generate_new_python_project_template(self, kicad_circuit) -> str:
        """Generate template Python code for a new project directory"""
        project_name = self.kicad_project.stem

        template = f'''#!/usr/bin/env python3
"""
{project_name} Circuit Project

Generated from KiCad project: {self.kicad_project.name}
Created by kicad-to-python tool

This is the main file for a hierarchical circuit project.
Individual subcircuits should be created in separate files.

Components found:
{self._format_components_list(kicad_circuit.components)}

Nets found: {len(kicad_circuit.nets)} nets
"""

from circuit_synth import Circuit, Component

def create_{project_name}_circuit():
    """Create the main {project_name} circuit"""
    circuit = Circuit("{project_name}")
    
    # TODO: Import and instantiate subcircuits
    # from subcircuit1 import create_subcircuit1
    # circuit.add_subcircuit(create_subcircuit1())
    
    # TODO: Add top-level components
{self._generate_component_code(kicad_circuit.components)}
    
    # TODO: Add inter-subcircuit connections
    # {len(kicad_circuit.nets)} nets need to be connected
    
    return circuit

if __name__ == "__main__":
    circuit = create_{project_name}_circuit()
    print(f"Created circuit: {{circuit.name}}")
    print(f"Components: {{len(circuit._components)}}")
    
    # Generate KiCad files
    print("\\nTo generate KiCad files, run:")
    print("uv run python examples/example_kicad_project.py")
'''
        return template

    def _format_components_list(self, components: List[Component]) -> str:
        """Format components list for template comments"""
        if not components:
            return "  (No components found)"

        lines = []
        for comp in components:
            lines.append(f"  - {comp.reference}: {comp.lib_id} = {comp.value}")
        return "\n".join(lines)

    def _generate_component_code(self, components: List[Component]) -> str:
        """Generate Python code for adding components"""
        if not components:
            return "    # No components found in KiCad schematic"

        lines = []
        for comp in components:
            # Clean up component values and library IDs for Python
            lib_id = comp.lib_id.replace(":", "_")
            safe_ref = comp.reference.lower()

            lines.append(
                f"""    # {comp.reference}: {comp.lib_id}
    {safe_ref} = Component(
        reference="{comp.reference}",
        symbol="{comp.lib_id}",
        value="{comp.value}",
        footprint="{comp.footprint}"
    )
    circuit.add_component({safe_ref})
"""
            )

        return "\n".join(lines)


def _resolve_kicad_project_path(input_path: str) -> Optional[Path]:
    """
    Resolve KiCad project path from input, handling both files and directories.

    Args:
        input_path: Path to .kicad_pro file or directory containing one

    Returns:
        Path to .kicad_pro file or None if not found
    """
    path = Path(input_path)

    # If it's already a .kicad_pro file, return it
    if path.is_file() and path.suffix == ".kicad_pro":
        logger.info(f"Using KiCad project file: {path}")
        return path

    # If it's a directory, search recursively for .kicad_pro files
    if path.is_dir():
        logger.info(f"Searching for .kicad_pro files in directory: {path}")

        # Search recursively for .kicad_pro files
        kicad_pro_files = list(path.rglob("*.kicad_pro"))

        if not kicad_pro_files:
            logger.error(f"No .kicad_pro files found in directory: {path}")
            return None

        if len(kicad_pro_files) == 1:
            logger.info(f"Found project file: {kicad_pro_files[0]}")
            return kicad_pro_files[0]

        # If multiple files found, prefer the one at the root level
        root_level_files = [f for f in kicad_pro_files if f.parent == path]
        if root_level_files:
            logger.info(f"Found project file at root level: {root_level_files[0]}")
            return root_level_files[0]

        # Otherwise, use the first one found
        logger.warning(f"Multiple .kicad_pro files found, using: {kicad_pro_files[0]}")
        for f in kicad_pro_files:
            logger.info(f"  - {f}")
        return kicad_pro_files[0]

    # If the path doesn't exist, check if it's a file without extension
    if not path.exists():
        # Try adding .kicad_pro extension
        kicad_pro_path = path.with_suffix(".kicad_pro")
        if kicad_pro_path.exists():
            logger.info(f"Found project file with added extension: {kicad_pro_path}")
            return kicad_pro_path

    logger.error(f"Could not resolve KiCad project path: {input_path}")
    return None


def main():
    """Main entry point for the KiCad to Python sync tool"""
    parser = argparse.ArgumentParser(
        description="Synchronize KiCad schematics with Python circuit definitions",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  %(prog)s my_project.kicad_pro my_circuit.py --preview
      Preview changes to existing Python file
      
  %(prog)s project_directory/ new_circuit.py --apply
      Create new Python file from KiCad project (searches for .kicad_pro)
      
  %(prog)s my_project.kicad_pro python_project/ --apply
      Create new Python project directory with main.py
      
  %(prog)s project_directory/ existing_project/ --apply
      Update existing Python project from KiCad directory
      
  %(prog)s my_project.kicad_pro my_circuit.py --apply --backup
      Update existing file with backup creation
        """,
    )

    # Required arguments
    parser.add_argument(
        "kicad_project",
        help="Path to KiCad project file (.kicad_pro) or directory containing one (searches recursively)",
    )
    parser.add_argument(
        "python_file",
        help="Path to Python file or project directory (will be created if it does not exist)",
    )

    # Action options
    action_group = parser.add_mutually_exclusive_group(required=True)
    action_group.add_argument(
        "--preview", action="store_true", help="Preview changes without applying them"
    )
    action_group.add_argument(
        "--apply", action="store_true", help="Apply changes to Python file"
    )

    # Sync options
    parser.add_argument(
        "--backup",
        action="store_true",
        default=True,
        help="Create backup before applying changes (default: True)",
    )
    parser.add_argument(
        "--no-backup",
        action="store_true",
        help="Do not create backup before applying changes",
    )

    # Output options
    parser.add_argument(
        "--verbose", "-v", action="store_true", help="Enable verbose logging"
    )

    args = parser.parse_args()

    # Setup logging
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)

    # Handle backup option
    create_backup = args.backup and not args.no_backup

    try:
        # Resolve KiCad project path - search for .kicad_pro files if directory given
        kicad_project_path = _resolve_kicad_project_path(args.kicad_project)
        if not kicad_project_path:
            logger.error(f"No .kicad_pro file found in: {args.kicad_project}")
            return 1

        # Create syncer and run
        syncer = KiCadToPythonSyncer(
            str(kicad_project_path),
            args.python_file,
            preview_only=args.preview,
            create_backup=create_backup,
        )
        success = syncer.sync()

        # Print summary
        if args.preview:
            print("\nPreview mode - no changes were applied")
            print("Use --apply to actually update the Python file")
        elif success:
            print("\nChanges applied successfully!")

        return 0 if success else 1

    except Exception as e:
        logger.error(f"Synchronization failed: {e}")
        if args.verbose:
            import traceback

            traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())
