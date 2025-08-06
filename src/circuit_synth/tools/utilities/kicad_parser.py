#!/usr/bin/env python3
"""
KiCad project parser for extracting circuit information.

This module handles parsing of KiCad project files (.kicad_pro) and
associated schematic files to extract circuit structure and components.
"""

import json
import logging
import re
import subprocess
import tempfile
from pathlib import Path
from typing import Dict, List, Optional, Tuple

from circuit_synth.tools.utilities.kicad_netlist_parser import KiCadNetlistParser
from circuit_synth.tools.utilities.models import Circuit, Component, Net

logger = logging.getLogger(__name__)


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
        self.root_schematic = self._find_root_schematic()

    def _find_root_schematic(self) -> Optional[Path]:
        """Parse .kicad_pro file to find the root schematic file"""
        try:
            with open(self.kicad_project, "r") as f:
                project_data = json.load(f)

            # Look for sheets array in the project file
            sheets = project_data.get("sheets", [])
            if not sheets:
                logger.warning("No sheets found in .kicad_pro file")
                # Fallback to assumption that schematic has same name as project
                fallback_sch = self.project_dir / f"{self.kicad_project.stem}.kicad_sch"
                if fallback_sch.exists():
                    logger.info(f"Using fallback root schematic: {fallback_sch}")
                    return fallback_sch
                return None

            # Find the root schematic
            # First try to find a sheet with empty name (traditional root sheet)
            for sheet_info in sheets:
                if isinstance(sheet_info, list) and len(sheet_info) >= 2:
                    schematic_file, sheet_name = sheet_info[0], sheet_info[1]
                    if sheet_name == "":  # Traditional root sheet has empty name
                        root_sch_path = self.project_dir / schematic_file
                        if root_sch_path.exists():
                            logger.info(
                                f"Found traditional root schematic: {root_sch_path}"
                            )
                            return root_sch_path
                        else:
                            logger.error(
                                f"Root schematic file not found: {root_sch_path}"
                            )

            # If no empty-name sheet found, use the first sheet as root (hierarchical projects)
            if sheets and len(sheets) > 0:
                first_sheet = sheets[0]
                if isinstance(first_sheet, list) and len(first_sheet) >= 2:
                    schematic_file, sheet_name = first_sheet[0], first_sheet[1]

                    # Try to construct schematic path from UUID
                    root_sch_path = (
                        self.project_dir / f"{self.kicad_project.stem}.kicad_sch"
                    )
                    if root_sch_path.exists():
                        logger.info(
                            f"Found hierarchical root schematic: {root_sch_path} (sheet: {sheet_name})"
                        )
                        return root_sch_path

                    # Alternative: try schematic_file directly
                    alt_root_sch_path = self.project_dir / schematic_file
                    if alt_root_sch_path.exists():
                        logger.info(
                            f"Found alternative root schematic: {alt_root_sch_path}"
                        )
                        return alt_root_sch_path

            logger.error("Could not find root schematic in .kicad_pro sheets")
            return None

        except (json.JSONDecodeError, FileNotFoundError, KeyError) as e:
            logger.error(f"Error parsing .kicad_pro file: {e}")
            return None

    def generate_netlist(self) -> Optional[Path]:
        """Generate KiCad netlist from schematic using kicad-cli"""
        logger.info("Generating KiCad netlist from schematic")

        if not self.root_schematic:
            logger.error("No root schematic found - cannot generate netlist")
            return None

        try:
            # Create temporary directory for netlist
            temp_dir = Path(tempfile.mkdtemp())
            netlist_path = temp_dir / f"{self.kicad_project.stem}.net"

            # Run kicad-cli to generate netlist from the root schematic file
            cmd = [
                "kicad-cli",
                "sch",
                "export",
                "netlist",
                "--output",
                str(netlist_path),
                str(self.root_schematic),
            ]

            logger.info(f"Running: {' '.join(cmd)}")
            logger.info(f"Target schematic: {self.root_schematic}")
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
                # Clean up the label (remove quotes and leading slash)
                clean_label = label.strip('"')
                if clean_label.startswith("/"):
                    clean_label = clean_label[
                        1:
                    ]  # Remove leading slash from hierarchical labels
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
