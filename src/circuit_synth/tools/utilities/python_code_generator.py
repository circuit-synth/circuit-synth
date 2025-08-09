#!/usr/bin/env python3
"""
Python code generation for KiCad to Python synchronization.

This module handles the generation of Python circuit code from parsed KiCad schematics.
It converts circuit data structures into executable Python code with proper formatting
and hierarchical support.
"""

import logging
import re
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from circuit_synth.tools.utilities.models import Circuit, Component, Net

logger = logging.getLogger(__name__)


class PythonCodeGenerator:
    """Generate Python circuit code from parsed KiCad data"""

    def __init__(self, project_name: Optional[str] = None):
        """Initialize the Python code generator"""
        self.project_name = project_name

    def _generate_project_call(self) -> str:
        """Generate the circuit.generate_kicad_netlist() and circuit.generate_kicad_project() calls"""
        if self.project_name:
            project_name = f"{self.project_name}_generated"
            return f'    # Generate KiCad project (creates directory)\n    circuit.generate_kicad_project(project_name="{project_name}")\n    # Generate KiCad netlist (required for ratsnest display)\n    circuit.generate_kicad_netlist("{project_name}/{project_name}.net")'
        else:
            return "    # Generate KiCad project\n    circuit.generate_kicad_project()\n    # Generate KiCad netlist (required for ratsnest display)\n    circuit.generate_kicad_netlist()"

    def _sanitize_variable_name(self, name: str) -> str:
        """
        Convert a net or signal name to a valid Python variable name.

        Rules:
        - Remove hierarchical path prefixes (/path/to/NET → NET)
        - Replace invalid characters with underscores
        - Prefix with underscore if starts with a digit
        - Handle common power net naming conventions
        """
        # Remove hierarchical path prefixes
        # Convert "/resistor_divider/GND" to "GND"
        if "/" in name:
            # Take the last part after the final slash
            name = name.split("/")[-1]
            logger.debug(f"Cleaned hierarchical name to: {name}")

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
        var_name = re.sub(r"[^a-zA-Z0-9_]", "_", var_name)

        # Prefix with underscore if starts with a digit
        if var_name and var_name[0].isdigit():
            var_name = "_" + var_name

        # Handle empty names
        if not var_name or var_name == "_":
            var_name = "net"

        return var_name

    def _generate_component_code(self, comp: Component, indent: str = "") -> List[str]:
        """Generate code lines for a single component"""
        lines = []

        # Generate the component creation line
        # Use 'ref' attribute which is the actual field name in Component
        comp_ref = getattr(comp, "ref", None) or getattr(comp, "reference", None) or ""
        comp_var = self._sanitize_variable_name(comp_ref)
        comp_line = f"{indent}{comp_var} = Component("

        # Add parameters
        params = []
        # Check for both lib_id and symbol (different attributes used in different contexts)
        comp_symbol = getattr(comp, "lib_id", None) or getattr(comp, "symbol", None)
        if comp_symbol:
            params.append(f'symbol="{comp_symbol}"')
        if comp_ref:
            params.append(f'ref="{comp_ref}"')
        if comp.value:
            params.append(f'value="{comp.value}"')
        if comp.footprint:
            params.append(f'footprint="{comp.footprint}"')

        comp_line += ", ".join(params) + ")"
        lines.append(comp_line)

        return lines

    def _format_net_summary(self, net: Net) -> str:
        """Format a one-line summary of a net and its connections"""
        if not net.connections:
            return f"{net.name}: No connections"

        connection_strs = []
        for ref, pin in net.connections:
            connection_strs.append(f"{ref}[{pin}]")

        return f"{net.name}: {' + '.join(connection_strs)}"

    def generate_hierarchical_code(
        self,
        main_circuit: Circuit,
        subcircuits: List[Circuit],
        hierarchical_tree: Optional[Dict] = None,
    ) -> str:
        """Generate hierarchical Python code with main circuit and subcircuits"""
        logger.info("🏗️ HIERARCHICAL_CODE: Starting hierarchical code generation")

        code_lines = []

        # Header
        code_lines.extend(
            [
                "#!/usr/bin/env python3",
                '"""',
                "Hierarchical Circuit Generated from KiCad",
                '"""',
                "",
                "from circuit_synth import *",
                "",
            ]
        )

        # Generate subcircuits first
        for circuit in subcircuits:
            code_lines.extend(self._generate_subcircuit_code(circuit))
            code_lines.append("")

        # Generate main circuit
        code_lines.extend(
            self._generate_main_circuit_code(main_circuit, hierarchical_tree)
        )

        # Add generation code
        code_lines.extend(
            [
                "",
                "# Generate the circuit",
                "if __name__ == '__main__':",
                "    circuit = main()",
                self._generate_project_call(),
            ]
        )

        result = "\n".join(code_lines)
        logger.info(f"🏗️ HIERARCHICAL_CODE: Generated {len(code_lines)} lines of code")
        return result

    def _generate_subcircuit_code(self, circuit: Circuit) -> List[str]:
        """Generate code for a subcircuit function"""
        logger.info(f"🔧 SUBCIRCUIT: Generating code for {circuit.name}")

        code_lines = []

        # Function declaration
        code_lines.append(f"@circuit(name='{circuit.name}')")
        code_lines.append(f"def {circuit.name}():")
        code_lines.append(f'    """')
        code_lines.append(f"    {circuit.name} subcircuit")
        code_lines.append(f'    """')

        # Create nets (filter out unconnected nets)
        if circuit.nets:
            connected_nets = [
                net for net in circuit.nets if not net.name.startswith("unconnected-")
            ]
            if connected_nets:
                code_lines.append("    # Create nets")
                for net in connected_nets:
                    net_var = self._sanitize_variable_name(net.name)
                    code_lines.append(f"    {net_var} = Net('{net.name}')")

        code_lines.append("")

        # Create components
        if circuit.components:
            code_lines.append("    # Create components")
            for comp in circuit.components:
                comp_code = self._generate_component_code(comp, indent="    ")
                code_lines.extend(comp_code)

        code_lines.append("")

        # Add connections (skip unconnected nets)
        if circuit.nets:
            connected_nets = [
                net for net in circuit.nets if not net.name.startswith("unconnected-")
            ]
            if any(net.connections for net in connected_nets):
                code_lines.append("    # Connections")
                for net in connected_nets:
                    if net.connections:
                        net_var = self._sanitize_variable_name(net.name)
                        for ref, pin in net.connections:
                            comp_var = self._sanitize_variable_name(ref)
                            if pin.isdigit():
                                code_lines.append(f"    {comp_var}[{pin}] += {net_var}")
                            else:
                                code_lines.append(
                                    f"    {comp_var}['{pin}'] += {net_var}"
                                )

        logger.info(
            f"🔧 SUBCIRCUIT: Generated {len(code_lines)} lines for {circuit.name}"
        )
        return code_lines

    def _generate_main_circuit_code(
        self, circuit: Circuit, hierarchical_tree: Optional[Dict] = None
    ) -> List[str]:
        """Generate code for the main circuit function"""
        logger.info("🎯 MAIN_CIRCUIT: Generating main circuit code")

        code_lines = []

        # Function declaration
        code_lines.append("@circuit(name='main')")
        code_lines.append("def main():")
        code_lines.append('    """')
        code_lines.append("    Main circuit with hierarchical subcircuits")
        code_lines.append('    """')

        # Create nets for main circuit (filter out unconnected nets)
        if circuit.nets:
            connected_nets = [
                net for net in circuit.nets if not net.name.startswith("unconnected-")
            ]
            if connected_nets:
                code_lines.append("    # Main circuit nets")
                for net in connected_nets:
                    net_var = self._sanitize_variable_name(net.name)
                    code_lines.append(f"    {net_var} = Net('{net.name}')")

        code_lines.append("")

        # Create main circuit components
        if circuit.components:
            code_lines.append("    # Main circuit components")
            for comp in circuit.components:
                comp_code = self._generate_component_code(comp, indent="    ")
                code_lines.extend(comp_code)

        code_lines.append("")

        # Instantiate subcircuits based on hierarchical tree
        if hierarchical_tree and "main" in hierarchical_tree:
            code_lines.append("    # Instantiate subcircuits")
            for child_circuit in hierarchical_tree["main"]:
                child_var = f"{self._sanitize_variable_name(child_circuit)}_instance"
                child_func = self._sanitize_variable_name(child_circuit)
                code_lines.append(f"    {child_var} = {child_func}()")

        code_lines.append("")

        # Add main circuit connections (skip unconnected nets)
        if circuit.nets:
            connected_nets = [
                net for net in circuit.nets if not net.name.startswith("unconnected-")
            ]
            if any(net.connections for net in connected_nets):
                code_lines.append("    # Main circuit connections")
                for net in connected_nets:
                    if net.connections:
                        net_var = self._sanitize_variable_name(net.name)
                        for ref, pin in net.connections:
                            comp_var = self._sanitize_variable_name(ref)
                            if pin.isdigit():
                                code_lines.append(f"    {comp_var}[{pin}] += {net_var}")
                            else:
                                code_lines.append(
                                    f"    {comp_var}['{pin}'] += {net_var}"
                                )

        logger.info(
            f"🎯 MAIN_CIRCUIT: Generated {len(code_lines)} lines for main circuit"
        )
        return code_lines

    def _generate_flat_code(self, circuit: Circuit) -> str:
        """Generate flat (non-hierarchical) Python code"""
        logger.info("📄 FLAT_CODE: Generating flat circuit code")

        code_parts = []

        # Header
        code_parts.extend(
            [
                "#!/usr/bin/env python3",
                '"""',
                "Circuit Generated from KiCad",
                '"""',
                "",
                "from circuit_synth import *",
                "",
            ]
        )

        # Generate main function
        code_parts.append("@circuit")
        code_parts.append("def main():")
        code_parts.append('    """Generated circuit from KiCad"""')

        # Create nets (filter out unconnected nets)
        if circuit.nets:
            connected_nets = [
                net for net in circuit.nets if not net.name.startswith("unconnected-")
            ]
            if connected_nets:
                code_parts.append("    # Create nets")
                for net in connected_nets:
                    net_var = self._sanitize_variable_name(net.name)
                    code_parts.append(f"    {net_var} = Net('{net.name}')")

        code_parts.append("")

        # Create components
        if circuit.components:
            code_parts.append("    # Create components")
            for comp in circuit.components:
                comp_code = self._generate_component_code(comp, indent="    ")
                code_parts.extend(comp_code)

        code_parts.append("")

        # Add connections (skip unconnected nets)
        if circuit.nets:
            connected_nets = [
                net for net in circuit.nets if not net.name.startswith("unconnected-")
            ]
            if any(net.connections for net in connected_nets):
                code_parts.append("    # Connections")
                for net in connected_nets:
                    if net.connections:
                        net_var = self._sanitize_variable_name(net.name)
                        for ref, pin in net.connections:
                            comp_var = self._sanitize_variable_name(ref)
                            if pin.isdigit():
                                code_parts.append(f"    {comp_var}[{pin}] += {net_var}")
                            else:
                                code_parts.append(
                                    f"    {comp_var}['{pin}'] += {net_var}"
                                )

        # Add generation code
        code_parts.extend(
            [
                "",
                "# Generate the circuit",
                "if __name__ == '__main__':",
                "    circuit = main()",
                self._generate_project_call(),
            ]
        )

        result = "\n".join(code_parts)
        logger.info(f"📄 FLAT_CODE: Generated {len(code_parts)} lines of flat code")
        return result

    def update_or_create_file(
        self,
        target_path: Path,
        main_circuit: Circuit,
        subcircuits: List[Circuit] = None,
        hierarchical_tree: Optional[Dict] = None,
        backup: bool = True,
    ) -> bool:
        """
        Update or create a Python file with circuit code.

        Args:
            target_path: Path to the target Python file
            main_circuit: Main circuit data
            subcircuits: List of subcircuit data (for hierarchical circuits)
            hierarchical_tree: Hierarchical structure mapping
            backup: Whether to create backup files

        Returns:
            bool: True if successful, False otherwise
        """
        try:
            logger.info(f"📝 CODE_UPDATE: Updating file {target_path}")

            # Create backup if requested and file exists
            if backup and target_path.exists():
                backup_path = target_path.with_suffix(target_path.suffix + ".backup")
                backup_path.write_text(target_path.read_text())
                logger.info(f"📋 BACKUP: Created backup at {backup_path}")

            # Determine if this is hierarchical or flat
            if subcircuits and len(subcircuits) > 0:
                logger.info("🏗️ CODE_UPDATE: Generating hierarchical code")
                content = self.generate_hierarchical_code(
                    main_circuit, subcircuits, hierarchical_tree
                )
            else:
                logger.info("📄 CODE_UPDATE: Generating flat code")
                content = self._generate_flat_code(main_circuit)

            # Write the file
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(content)

            logger.info(
                f"✅ CODE_UPDATE: Successfully wrote {len(content)} characters to {target_path}"
            )
            return True

        except Exception as e:
            logger.error(f"❌ CODE_UPDATE: Failed to update {target_path}: {e}")
            return False

    def _get_ancestors(
        self, circuit_name: str, child_to_parent: Dict[str, str]
    ) -> List[str]:
        """
        Get all ancestors of a circuit in the hierarchy tree.

        Args:
            circuit_name: Name of the circuit
            child_to_parent: Mapping from child circuit to parent circuit

        Returns:
            List of ancestor circuit names, from immediate parent to root
        """
        ancestors = []
        current = circuit_name

        while current in child_to_parent:
            parent = child_to_parent[current]
            ancestors.append(parent)
            current = parent

        return ancestors

    def _get_depth(
        self, circuit_name: str, hierarchy_tree: Dict[str, List[str]]
    ) -> int:
        """
        Get the depth of a circuit in the hierarchy tree (0 = root).

        Args:
            circuit_name: Name of the circuit
            hierarchy_tree: Parent -> children mapping

        Returns:
            Depth level (0 for root, 1 for direct children, etc.)
        """
        if circuit_name == "main":
            return 0

        # Build reverse mapping: child -> parent
        child_to_parent = {}
        for parent, children in hierarchy_tree.items():
            for child in children:
                child_to_parent[child] = parent

        depth = 0
        current = circuit_name

        while current in child_to_parent:
            depth += 1
            current = child_to_parent[current]

        return depth

    def _find_lowest_common_ancestor(
        self, net_users: List[str], hierarchy_tree: Dict[str, List[str]]
    ) -> str:
        """
        Find the lowest common ancestor for a set of net users in the hierarchy tree.

        Args:
            net_users: List of circuit names that use the net
            hierarchy_tree: Dict mapping parent -> list of children

        Returns:
            Circuit name where the net should be created
        """
        if len(net_users) == 1:
            return net_users[0]

        # Build reverse mapping: child -> parent
        child_to_parent = {}
        for parent, children in hierarchy_tree.items():
            for child in children:
                child_to_parent[child] = parent

        # Find all ancestors for each net user
        all_ancestors = []
        for user in net_users:
            ancestors = self._get_ancestors(user, child_to_parent)
            # Include the user itself in its ancestor path
            ancestors_set = set([user] + ancestors)
            all_ancestors.append(ancestors_set)

        # Find common ancestors
        if not all_ancestors:
            return "main"  # Fallback to root

        common_ancestors = set.intersection(*all_ancestors)

        if not common_ancestors:
            return "main"  # Fallback to root

        # Return the deepest (lowest) common ancestor
        # The deepest ancestor has the highest depth value in the tree
        deepest_ancestor = max(
            common_ancestors, key=lambda x: self._get_depth(x, hierarchy_tree)
        )
        return deepest_ancestor

    def _determine_net_scope(
        self, net_name: str, net_users: List[str], hierarchy_tree: Dict[str, List[str]]
    ) -> str:
        """
        Determine the correct scope (circuit) where a net should be created.

        This implements the "lowest common ancestor" rule for hierarchical nets.
        """
        # Special cases for global nets
        global_nets = [
            "GND",
            "GROUND",
            "VSS",
            "VSSA",
            "VCC",
            "VDD",
            "VDDA",
            "VBUS",
            "VIN",
        ]
        if (
            net_name in global_nets
            or net_name.startswith("VCC_")
            or net_name.startswith("VDD_")
        ):
            return "main"

        # For local nets (used by single circuit), create locally
        if len(net_users) == 1:
            return net_users[0]

        # For shared nets, find lowest common ancestor
        return self._find_lowest_common_ancestor(net_users, hierarchy_tree)

    def _analyze_hierarchical_nets(
        self, circuits: Dict[str, Circuit], hierarchical_tree: Optional[Dict] = None
    ) -> Tuple[Dict[str, Dict[str, Net]], Dict[str, List[str]]]:
        """
        Analyze hierarchical circuit structure to determine proper net creation levels.

        Args:
            circuits: Dictionary of circuit objects
            hierarchical_tree: Optional hierarchical tree structure from KiCad parser

        Returns:
            hierarchical_nets: Dict mapping circuit names to nets that should be created at that level
            shared_nets_per_subcircuit: Dict mapping subcircuit names to nets they should receive as parameters
        """
        logger.info(
            "🔍 NET_ANALYSIS: Starting hierarchical net analysis with LCA algorithm"
        )

        # Use provided hierarchical tree or build a fallback structure
        if hierarchical_tree:
            hierarchy_tree = hierarchical_tree
            logger.info(
                f"🔍 NET_ANALYSIS: Using provided hierarchy tree: {hierarchy_tree}"
            )
        else:
            # Fallback: Build simple 2-level hierarchy structure
            hierarchy_tree = {}
            main_circuit = circuits.get("main")
            if main_circuit:
                hierarchy_tree["main"] = [
                    name for name in circuits.keys() if name != "main"
                ]
                for subcircuit_name in hierarchy_tree["main"]:
                    hierarchy_tree[subcircuit_name] = []
            else:
                # If no main, treat as flat structure
                hierarchy_tree = {name: [] for name in circuits.keys()}

            logger.info(
                f"🔍 NET_ANALYSIS: Built fallback hierarchy tree: {hierarchy_tree}"
            )

        # Collect all nets and their usage across circuits
        net_usage = {}  # net_name -> set of circuit names that use it

        for circuit_name, circuit in circuits.items():
            for net in circuit.nets:
                if net.name not in net_usage:
                    net_usage[net.name] = set()
                net_usage[net.name].add(circuit_name)

        logger.info(f"🔍 NET_ANALYSIS: Net usage analysis:")
        for net_name, using_circuits in net_usage.items():
            logger.info(f"  - {net_name}: used by {list(using_circuits)}")

        # Determine where each net should be created using LCA algorithm
        hierarchical_nets = {}  # circuit_name -> {net_name: Net object}
        shared_nets_per_subcircuit = {}  # subcircuit_name -> [shared_net_names]

        for circuit_name in circuits.keys():
            hierarchical_nets[circuit_name] = {}
            if circuit_name != "main":
                shared_nets_per_subcircuit[circuit_name] = []

        for net_name, using_circuits in net_usage.items():
            # Determine optimal scope using LCA algorithm
            net_scope = self._determine_net_scope(
                net_name, list(using_circuits), hierarchy_tree
            )

            # Get net object from one of the using circuits
            net_obj = next(
                net
                for net in circuits[list(using_circuits)[0]].nets
                if net.name == net_name
            )
            hierarchical_nets[net_scope][net_name] = net_obj

            # All circuits that use this net (except the scope circuit) should receive it as parameter
            for circuit_name in using_circuits:
                if circuit_name != net_scope and circuit_name != "main":
                    shared_nets_per_subcircuit[circuit_name].append(net_name)

            logger.info(
                f"🔍 NET_ANALYSIS: {net_name} -> created at {net_scope}, shared with {[c for c in using_circuits if c != net_scope]}"
            )

        logger.info(
            "🔍 NET_ANALYSIS: Hierarchical net analysis complete using LCA algorithm"
        )
        return hierarchical_nets, shared_nets_per_subcircuit

    def _generate_multiple_files(
        self,
        main_python_file: Path,
        circuits: Dict[str, Circuit],
        preview_only: bool = True,
        hierarchical_tree: Optional[Dict] = None,
    ) -> Optional[str]:
        """Generate separate Python files for each circuit"""
        logger.info(f"🗂️ MULTI_FILE: Generating {len(circuits)} separate circuit files")

        try:
            # Determine output directory (where main.py will go)
            output_dir = main_python_file.parent
            logger.info(f"🗂️ MULTI_FILE: Output directory: {output_dir}")

            # Find main circuit and subcircuits
            main_circuit = circuits.get("main")
            if not main_circuit:
                # If no explicit 'main', pick the first non-hierarchical circuit
                for name, circuit in circuits.items():
                    if not (
                        hasattr(circuit, "is_hierarchical_sheet")
                        and circuit.is_hierarchical_sheet
                    ):
                        main_circuit = circuit
                        break
                if not main_circuit:
                    main_circuit = list(circuits.values())[0]

            subcircuits = {
                name: circuit
                for name, circuit in circuits.items()
                if circuit != main_circuit
            }

            logger.info(f"🗂️ MULTI_FILE: Main circuit: {main_circuit.name}")
            logger.info(f"🗂️ MULTI_FILE: Subcircuits: {list(subcircuits.keys())}")

            # Perform hierarchical net analysis to determine proper net creation levels
            hierarchical_nets, shared_nets_per_subcircuit = (
                self._analyze_hierarchical_nets(circuits, hierarchical_tree)
            )

            logger.info(f"🗂️ MULTI_FILE: Hierarchical net analysis results:")
            for level, nets in hierarchical_nets.items():
                logger.info(f"  - {level}: {list(nets.keys())}")

            for name, shared_nets in shared_nets_per_subcircuit.items():
                logger.info(f"🗂️ MULTI_FILE: Shared nets with {name}: {shared_nets}")

            # Identify only top-level circuits (direct children of main)
            top_level_circuits = self._identify_top_level_circuits(
                hierarchical_tree or {}
            )
            logger.info(
                f"🗂️ MULTI_FILE: Top-level circuits (direct children of main): {top_level_circuits}"
            )

            # Generate subcircuit files for ALL circuits (not just top-level)
            subcircuit_files_created = []
            for name, circuit in subcircuits.items():
                subcircuit_file = output_dir / f"{name}.py"
                logger.info(f"🗂️ MULTI_FILE: Generating {subcircuit_file}")

                # Generate subcircuit code with shared nets as parameters
                shared_nets = shared_nets_per_subcircuit.get(name, [])
                local_nets = hierarchical_nets.get(name, {})
                subcircuit_code = self._generate_standalone_subcircuit_file(
                    circuit,
                    shared_nets,
                    local_nets,
                    circuits,
                    hierarchical_tree,
                    shared_nets_per_subcircuit,
                )

                if preview_only:
                    logger.info(
                        f"🗂️ MULTI_FILE: [PREVIEW] Would create {subcircuit_file}"
                    )
                    logger.info(
                        f"🗂️ MULTI_FILE: [PREVIEW] Content preview:\n{subcircuit_code[:200]}..."
                    )
                else:
                    # Write subcircuit file
                    with open(subcircuit_file, "w") as f:
                        f.write(subcircuit_code)
                    logger.info(f"🗂️ MULTI_FILE: ✅ Created {subcircuit_file}")

                subcircuit_files_created.append(name)

            # Generate main.py file with ONLY top-level circuits instantiated
            main_nets = hierarchical_nets.get("main", {})
            main_code = self._generate_main_file_with_imports(
                main_circuit, top_level_circuits, shared_nets_per_subcircuit, main_nets
            )

            if preview_only:
                logger.info(f"🗂️ MULTI_FILE: [PREVIEW] Would create {main_python_file}")
                logger.info("🗂️ MULTI_FILE: [PREVIEW] Main file content:")
                return main_code
            else:
                # Write main file
                with open(main_python_file, "w") as f:
                    f.write(main_code)
                logger.info(f"🗂️ MULTI_FILE: ✅ Created {main_python_file}")
                return main_code

        except Exception as e:
            logger.error(f"🗂️ MULTI_FILE: Failed to generate multiple files: {e}")
            return None

    def _generate_standalone_subcircuit_file(
        self,
        circuit: Circuit,
        shared_nets: List[str] = None,
        local_nets: Dict[str, Net] = None,
        circuits: Dict[str, Circuit] = None,
        hierarchy_tree: Dict[str, List[str]] = None,
        shared_nets_per_subcircuit: Dict[str, List[str]] = None,
    ) -> str:
        """Generate a complete Python file for a single subcircuit"""
        logger.info(
            f"📄 SUBCIRCUIT_FILE: Generating standalone file for {circuit.name}"
        )

        code_lines = []

        # File header
        code_lines.extend(
            [
                "#!/usr/bin/env python3",
                '"""',
                f"{circuit.name} subcircuit generated from KiCad",
                '"""',
                "",
                "from circuit_synth import *",
            ]
        )

        # Add imports for child circuits if this circuit has children
        if hierarchy_tree and circuit.name in hierarchy_tree:
            children = hierarchy_tree[circuit.name]
            if children:
                code_lines.append("")
                code_lines.append("# Import child circuits")
                for child_name in children:
                    code_lines.append(f"from {child_name} import {child_name.lower()}")

        code_lines.append("")

        # Generate the subcircuit function with net parameters
        code_lines.extend(
            self._generate_subcircuit_code_with_params(
                circuit,
                shared_nets or [],
                local_nets or {},
                circuits,
                hierarchy_tree,
                shared_nets_per_subcircuit,
            )
        )

        result = "\n".join(code_lines)
        logger.info(
            f"📄 SUBCIRCUIT_FILE: Generated {len(code_lines)} lines for {circuit.name}"
        )
        return result

    def _generate_subcircuit_code_with_params(
        self,
        circuit: Circuit,
        shared_nets: List[str],
        local_nets: Dict[str, Net] = None,
        circuits: Dict[str, Circuit] = None,
        hierarchy_tree: Dict[str, List[str]] = None,
        shared_nets_per_subcircuit: Dict[str, List[str]] = None,
    ) -> List[str]:
        """Generate code for a subcircuit function with net parameters and internal hierarchy"""
        logger.info(
            f"🔧 SUBCIRCUIT_PARAMS: Generating parameterized code for {circuit.name}"
        )

        code_lines = []

        # Function declaration with net parameters
        net_params = []
        for net_name in shared_nets:
            net_var = self._sanitize_variable_name(net_name)
            net_params.append(net_var)

        param_str = ", ".join(net_params) if net_params else ""
        code_lines.append(f"@circuit(name='{circuit.name}')")
        code_lines.append(f"def {circuit.name.lower()}({param_str}):")
        code_lines.append(f'    """')
        code_lines.append(f"    {circuit.name} subcircuit")
        if shared_nets:
            code_lines.append(f"    Parameters: {', '.join(shared_nets)}")
        code_lines.append(f'    """')

        # Create only local nets (not shared ones) using hierarchical analysis
        if local_nets:
            code_lines.append("    # Create local nets")
            for net_name, net_obj in local_nets.items():
                net_var = self._sanitize_variable_name(net_name)
                code_lines.append(f"    {net_var} = Net('{net_name}')")
        elif circuit.nets:
            # Fallback: create local nets by excluding shared ones
            local_circuit_nets = [
                net for net in circuit.nets if net.name not in shared_nets
            ]
            if local_circuit_nets:
                code_lines.append("    # Create local nets (fallback)")
                for net in local_circuit_nets:
                    net_var = self._sanitize_variable_name(net.name)
                    code_lines.append(f"    {net_var} = Net('{net.name}')")

        code_lines.append("")

        # Create components
        if circuit.components:
            code_lines.append("    # Create components")
            for comp in circuit.components:
                comp_code = self._generate_component_code(comp, indent="    ")
                code_lines.extend(comp_code)

        code_lines.append("")

        # Instantiate child circuits if this circuit has children
        if hierarchy_tree and circuit.name in hierarchy_tree:
            children = hierarchy_tree[circuit.name]
            if children and circuits:
                code_lines.append("    # Instantiate child circuits")
                for child_name in children:
                    if child_name in circuits:
                        # Get shared nets for this child circuit
                        child_shared_nets = (
                            shared_nets_per_subcircuit.get(child_name, [])
                            if shared_nets_per_subcircuit
                            else []
                        )
                        if child_shared_nets:
                            # Pass shared nets as parameters
                            net_args = []
                            for net_name in child_shared_nets:
                                net_var = self._sanitize_variable_name(net_name)
                                net_args.append(net_var)
                            args_str = ", ".join(net_args)
                            code_lines.append(
                                f"    {child_name.lower()}_circuit = {child_name.lower()}({args_str})"
                            )
                        else:
                            # No shared nets
                            code_lines.append(
                                f"    {child_name.lower()}_circuit = {child_name.lower()}()"
                            )
                code_lines.append("")

        # Add connections (all nets, both shared and local)
        if circuit.nets:
            connected_nets = [
                net for net in circuit.nets if not net.name.startswith("unconnected-")
            ]
            if any(net.connections for net in connected_nets):
                code_lines.append("    # Connections")
                for net in connected_nets:
                    if net.connections:
                        net_var = self._sanitize_variable_name(net.name)
                        for ref, pin in net.connections:
                            comp_var = self._sanitize_variable_name(ref)
                            if pin.isdigit():
                                code_lines.append(f"    {comp_var}[{pin}] += {net_var}")
                            else:
                                code_lines.append(
                                    f"    {comp_var}['{pin}'] += {net_var}"
                                )

        logger.info(
            f"🔧 SUBCIRCUIT_PARAMS: Generated {len(code_lines)} lines for {circuit.name}"
        )
        return code_lines

    def _generate_main_file_with_imports(
        self,
        main_circuit: Circuit,
        subcircuit_names: List[str],
        shared_nets_per_subcircuit: Dict[str, List[str]] = None,
        main_nets: Dict[str, Net] = None,
    ) -> str:
        """Generate the main.py file that imports subcircuits from separate files"""
        logger.info(
            f"📄 MAIN_FILE: Generating main file with imports for {len(subcircuit_names)} subcircuits"
        )

        code_lines = []

        # File header
        code_lines.extend(
            [
                "#!/usr/bin/env python3",
                '"""',
                "Main circuit generated from KiCad",
                '"""',
                "",
                "from circuit_synth import *",
            ]
        )

        # Import subcircuit functions from separate files
        if subcircuit_names:
            code_lines.append("")
            code_lines.append("# Import subcircuit functions")
            for subcircuit_name in subcircuit_names:
                code_lines.append(
                    f"from {subcircuit_name} import {subcircuit_name.lower()}"
                )

        code_lines.append("")

        # Generate main circuit function with proper subcircuit instantiation
        code_lines.extend(
            self._generate_main_circuit_code_with_params(
                main_circuit,
                subcircuit_names,
                shared_nets_per_subcircuit or {},
                main_nets or {},
            )
        )

        # Add generation code
        code_lines.extend(
            [
                "",
                "# Generate the circuit",
                "if __name__ == '__main__':",
                "    circuit = main()",
                self._generate_project_call(),
            ]
        )

        result = "\n".join(code_lines)
        logger.info(f"📄 MAIN_FILE: Generated {len(code_lines)} lines for main circuit")
        return result

    def _identify_top_level_circuits(
        self, hierarchy_tree: Dict[str, List[str]]
    ) -> List[str]:
        """
        Identify circuits that should be instantiated at the main level.

        Args:
            hierarchy_tree: Parent -> children mapping

        Returns:
            List of circuit names that are direct children of main
        """
        return hierarchy_tree.get("main", [])

    def _get_child_interface_nets(
        self,
        child_circuit: str,
        circuits: Dict[str, Circuit],
        net_assignments: Dict[str, str],
    ) -> List[str]:
        """
        Determine which nets should be passed as parameters to a child circuit.

        Args:
            child_circuit: Name of the child circuit
            circuits: Dictionary of all circuits
            net_assignments: Net name -> scope circuit mapping

        Returns:
            List of net variable names to pass as parameters
        """
        interface_nets = []

        # Find all nets used by the child circuit
        if child_circuit not in circuits:
            return interface_nets

        child_circuit_obj = circuits[child_circuit]
        child_nets = {net.name for net in child_circuit_obj.nets}

        # For each net used by child, check if it's defined in a parent scope
        for net_name in child_nets:
            net_scope = net_assignments.get(net_name)

            # If net is defined in parent scope, it's an interface net
            if net_scope and net_scope != child_circuit:
                interface_nets.append(net_name)

        return sorted(interface_nets)  # Sort for consistency

    def _generate_hierarchical_circuit_recursive(
        self,
        circuit_name: str,
        circuits: Dict[str, Circuit],
        hierarchy_tree: Dict[str, List[str]],
        net_assignments: Dict[str, str],
        indent: str = "    ",
    ) -> List[str]:
        """
        Generate Python code for a circuit and its children recursively.

        Args:
            circuit_name: Name of circuit to generate
            circuits: Dictionary of all circuits
            hierarchy_tree: Parent -> children mapping
            net_assignments: Net name -> scope circuit mapping
            indent: Indentation string for this level

        Returns:
            Generated Python code lines
        """
        code_lines = []

        # Skip if circuit doesn't exist
        if circuit_name not in circuits:
            logger.warning(
                f"🔧 RECURSIVE_GEN: Circuit {circuit_name} not found in circuits"
            )
            return code_lines

        circuit = circuits[circuit_name]

        # Generate nets that belong to this circuit scope
        local_nets = [
            (net_name, net_obj)
            for net_name, scope in net_assignments.items()
            if scope == circuit_name
        ]

        if local_nets:
            if circuit_name == "main":
                code_lines.append(f"{indent}# Main circuit nets")
            else:
                code_lines.append(f"{indent}# Local nets")
            for net_name, net_obj in local_nets:
                net_var = self._sanitize_variable_name(net_name)
                code_lines.append(f"{indent}{net_var} = Net('{net_name}')")
            code_lines.append("")  # Blank line after nets

        # Generate components for this circuit
        if circuit.components:
            code_lines.append(f"{indent}# Components")
            for component in circuit.components:
                comp_code = self._generate_component_code(component, indent=indent)
                code_lines.extend(comp_code)
            code_lines.append("")  # Blank line after components

        # Generate child circuit instantiations
        children = hierarchy_tree.get(circuit_name, [])
        if children:
            code_lines.append(f"{indent}# Instantiate subcircuits")
            for child_name in children:
                # Determine nets to pass to child
                child_interface_nets = self._get_child_interface_nets(
                    child_name, circuits, net_assignments
                )

                if child_interface_nets:
                    net_vars = [
                        self._sanitize_variable_name(net_name)
                        for net_name in child_interface_nets
                    ]
                    params = ", ".join(net_vars)
                    code_lines.append(
                        f"{indent}{child_name.lower()}_circuit = {child_name.lower()}({params})"
                    )
                else:
                    code_lines.append(
                        f"{indent}{child_name.lower()}_circuit = {child_name.lower()}()"
                    )
            code_lines.append("")  # Blank line after instantiations

        # Generate connections for this circuit level
        if circuit.nets:
            connected_nets = [
                net for net in circuit.nets if not net.name.startswith("unconnected-")
            ]
            net_connections_at_this_level = []

            for net in connected_nets:
                if net.connections and net.name in [
                    name
                    for name, scope in net_assignments.items()
                    if scope == circuit_name
                ]:
                    net_connections_at_this_level.append(net)

            if net_connections_at_this_level:
                code_lines.append(f"{indent}# Connections")
                for net in net_connections_at_this_level:
                    net_var = self._sanitize_variable_name(net.name)
                    for ref, pin in net.connections:
                        comp_var = self._sanitize_variable_name(ref)
                        if pin.isdigit():
                            code_lines.append(f"{indent}{comp_var}[{pin}] += {net_var}")
                        else:
                            code_lines.append(
                                f"{indent}{comp_var}['{pin}'] += {net_var}"
                            )
                code_lines.append("")  # Blank line after connections

        return code_lines

    def _generate_main_circuit_code_with_params(
        self,
        circuit: Circuit,
        subcircuit_names: List[str],
        shared_nets_per_subcircuit: Dict[str, List[str]],
        main_nets: Dict[str, Net] = None,
    ) -> List[str]:
        """Generate code for the main circuit function with proper hierarchical structure"""
        logger.info(
            "🎯 MAIN_CIRCUIT_PARAMS: Generating main circuit code with hierarchical structure"
        )

        code_lines = []

        # Function declaration
        code_lines.append("@circuit(name='main')")
        code_lines.append("def main():")
        code_lines.append('    """')
        code_lines.append("    Main circuit with hierarchical subcircuits")
        code_lines.append('    """')

        # Create main circuit nets (using hierarchical analysis)
        if main_nets:
            code_lines.append("    # Main circuit nets")
            for net_name, net_obj in main_nets.items():
                net_var = self._sanitize_variable_name(net_name)
                code_lines.append(f"    {net_var} = Net('{net_name}')")
        elif circuit.nets:
            # Fallback to circuit's own nets if no hierarchical analysis
            connected_nets = [
                net for net in circuit.nets if not net.name.startswith("unconnected-")
            ]
            if connected_nets:
                code_lines.append("    # Main circuit nets (fallback)")
                for net in connected_nets:
                    net_var = self._sanitize_variable_name(net.name)
                    code_lines.append(f"    {net_var} = Net('{net.name}')")

        code_lines.append("")

        # Create main circuit components
        if circuit.components:
            code_lines.append("    # Main circuit components")
            for comp in circuit.components:
                comp_code = self._generate_component_code(comp, indent="    ")
                code_lines.extend(comp_code)

        code_lines.append("")

        # Instantiate ONLY top-level subcircuits (not all subcircuits)
        # This is the key fix - only instantiate direct children of main
        if subcircuit_names:
            code_lines.append("    # Instantiate top-level subcircuits")
            for subcircuit_name in subcircuit_names:
                shared_nets = shared_nets_per_subcircuit.get(subcircuit_name, [])
                if shared_nets:
                    # Pass shared nets as parameters
                    net_args = []
                    for net_name in shared_nets:
                        net_var = self._sanitize_variable_name(net_name)
                        net_args.append(net_var)
                    args_str = ", ".join(net_args)
                    code_lines.append(
                        f"    {subcircuit_name.lower()}_circuit = {subcircuit_name.lower()}({args_str})"
                    )
                else:
                    # No shared nets
                    code_lines.append(
                        f"    {subcircuit_name.lower()}_circuit = {subcircuit_name.lower()}()"
                    )

        code_lines.append("")

        # Add main circuit connections
        if circuit.nets:
            connected_nets = [
                net for net in circuit.nets if not net.name.startswith("unconnected-")
            ]
            if any(net.connections for net in connected_nets):
                code_lines.append("    # Main circuit connections")
                for net in connected_nets:
                    if net.connections:
                        net_var = self._sanitize_variable_name(net.name)
                        for ref, pin in net.connections:
                            comp_var = self._sanitize_variable_name(ref)
                            if pin.isdigit():
                                code_lines.append(f"    {comp_var}[{pin}] += {net_var}")
                            else:
                                code_lines.append(
                                    f"    {comp_var}['{pin}'] += {net_var}"
                                )

        logger.info(
            f"🎯 MAIN_CIRCUIT_PARAMS: Generated {len(code_lines)} lines for main circuit"
        )
        return code_lines

    def update_python_file(
        self,
        python_file: Path,
        circuits: Dict[str, Circuit],
        preview_only: bool = True,
        hierarchical_tree: Optional[Dict] = None,
    ) -> Optional[str]:
        """Update Python file with circuit data - creates separate files for each circuit"""
        logger.info(f"🔄 CODE_UPDATE: Starting update of {python_file}")
        logger.info(f"🔄 CODE_UPDATE: Preview mode: {preview_only}")
        logger.info(f"🔄 CODE_UPDATE: Circuits to update: {list(circuits.keys())}")

        # Debug hierarchical tree
        if hierarchical_tree:
            logger.info(
                f"🔧 CODE_UPDATE_DEBUG: Using hierarchical tree: {hierarchical_tree}"
            )
        else:
            logger.warning(
                "🔧 CODE_UPDATE_DEBUG: No hierarchical tree provided, will use fallback"
            )

        try:
            # Check if this is a hierarchical design
            is_hierarchical = len(circuits) > 1 or any(
                hasattr(circuit, "is_hierarchical_sheet")
                and circuit.is_hierarchical_sheet
                for circuit in circuits.values()
            )
            logger.info(f"📝 CODE_UPDATE: Hierarchical design: {is_hierarchical}")

            if is_hierarchical:
                logger.info(
                    "📝 CODE_UPDATE: Generating separate files for hierarchical circuits"
                )
                return self._generate_multiple_files(
                    python_file, circuits, preview_only, hierarchical_tree
                )
            else:
                # For non-hierarchical (flat) circuits, still use the old single-file approach
                logger.info("📝 CODE_UPDATE: Generating single file for flat circuit")
                main_circuit = list(circuits.values())[0]
                updated_code = self._generate_flat_code(main_circuit)

            if updated_code:
                logger.info(
                    f"🔄 CODE_UPDATE: Generated updated code: {len(updated_code)} chars"
                )
                if preview_only:
                    logger.info("🔄 CODE_UPDATE: Preview mode - not writing to file")
                    return updated_code
                else:
                    logger.info("🔄 CODE_UPDATE: Writing updated code to file")
                    python_file.parent.mkdir(parents=True, exist_ok=True)
                    python_file.write_text(updated_code)
                    logger.info("🔄 CODE_UPDATE: ✅ File update completed")
                    return updated_code
            else:
                logger.error("🔄 CODE_UPDATE: ❌ Failed to generate updated code")
                return None

        except Exception as e:
            logger.error(f"🔄 CODE_UPDATE: Failed to update Python file: {e}")
            return None
