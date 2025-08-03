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
from typing import Any, Dict, List, Optional

from circuit_synth.tools.models import Circuit, Component, Net

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
            return f'    # Generate KiCad netlist (required for ratsnest display)\n    circuit.generate_kicad_netlist("{project_name}/{project_name}.net")\n    circuit.generate_kicad_project(project_name="{project_name}")'
        else:
            return "    # Generate KiCad netlist (required for ratsnest display)\n    circuit.generate_kicad_netlist()\n    circuit.generate_kicad_project()"

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
        comp_var = self._sanitize_variable_name(comp.reference)
        comp_line = f'{indent}{comp_var} = Component('
        
        # Add parameters
        params = []
        if comp.lib_id:
            params.append(f'symbol="{comp.lib_id}"')
        if comp.reference:
            params.append(f'ref="{comp.reference}"')
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
        self, main_circuit: Circuit, subcircuits: List[Circuit], hierarchical_tree: Optional[Dict] = None
    ) -> str:
        """Generate hierarchical Python code with main circuit and subcircuits"""
        logger.info("🏗️ HIERARCHICAL_CODE: Starting hierarchical code generation")
        
        code_lines = []
        
        # Header
        code_lines.extend([
            '#!/usr/bin/env python3',
            '"""',
            'Hierarchical Circuit Generated from KiCad',
            '"""',
            '',
            'from circuit_synth import *',
            ''
        ])
        
        # Generate subcircuits first
        for circuit in subcircuits:
            code_lines.extend(self._generate_subcircuit_code(circuit))
            code_lines.append("")
        
        # Generate main circuit
        code_lines.extend(self._generate_main_circuit_code(main_circuit, hierarchical_tree))
        
        # Add generation code
        code_lines.extend([
            '',
            '# Generate the circuit',
            'if __name__ == \'__main__\':',
            '    circuit = main()',
            self._generate_project_call()
        ])
        
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
            connected_nets = [net for net in circuit.nets if not net.name.startswith('unconnected-')]
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
            connected_nets = [net for net in circuit.nets if not net.name.startswith('unconnected-')]
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
                                code_lines.append(f"    {comp_var}['{pin}'] += {net_var}")

        logger.info(f"🔧 SUBCIRCUIT: Generated {len(code_lines)} lines for {circuit.name}")
        return code_lines

    def _generate_main_circuit_code(self, circuit: Circuit, hierarchical_tree: Optional[Dict] = None) -> List[str]:
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
            connected_nets = [net for net in circuit.nets if not net.name.startswith('unconnected-')]
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
            connected_nets = [net for net in circuit.nets if not net.name.startswith('unconnected-')]
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
                                code_lines.append(f"    {comp_var}['{pin}'] += {net_var}")

        logger.info(f"🎯 MAIN_CIRCUIT: Generated {len(code_lines)} lines for main circuit")
        return code_lines

    def _generate_flat_code(self, circuit: Circuit) -> str:
        """Generate flat (non-hierarchical) Python code"""
        logger.info("📄 FLAT_CODE: Generating flat circuit code")
        
        code_parts = []

        # Header
        code_parts.extend([
            '#!/usr/bin/env python3',
            '"""',
            'Circuit Generated from KiCad',
            '"""',
            '',
            'from circuit_synth import *',
            ''
        ])

        # Generate main function
        code_parts.append("@circuit")
        code_parts.append("def main():")
        code_parts.append('    """Generated circuit from KiCad"""')

        # Create nets (filter out unconnected nets)
        if circuit.nets:
            connected_nets = [net for net in circuit.nets if not net.name.startswith('unconnected-')]
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
            connected_nets = [net for net in circuit.nets if not net.name.startswith('unconnected-')]
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
                                code_parts.append(f"    {comp_var}['{pin}'] += {net_var}")

        # Add generation code
        code_parts.extend([
            "",
            "# Generate the circuit",
            "if __name__ == '__main__':",
            "    circuit = main()",
            self._generate_project_call()
        ])

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
                content = self.generate_hierarchical_code(main_circuit, subcircuits, hierarchical_tree)
            else:
                logger.info("📄 CODE_UPDATE: Generating flat code")
                content = self._generate_flat_code(main_circuit)

            # Write the file
            target_path.parent.mkdir(parents=True, exist_ok=True)
            target_path.write_text(content)
            
            logger.info(f"✅ CODE_UPDATE: Successfully wrote {len(content)} characters to {target_path}")
            return True
            
        except Exception as e:
            logger.error(f"❌ CODE_UPDATE: Failed to update {target_path}: {e}")
            return False

    def _generate_multiple_files(
        self, main_python_file: Path, circuits: Dict[str, Circuit], preview_only: bool = True
    ) -> Optional[str]:
        """Generate separate Python files for each circuit"""
        logger.info(f"🗂️ MULTI_FILE: Generating {len(circuits)} separate circuit files")
        
        try:
            # Determine output directory (where main.py will go)
            output_dir = main_python_file.parent
            logger.info(f"🗂️ MULTI_FILE: Output directory: {output_dir}")
            
            # Find main circuit and subcircuits
            main_circuit = circuits.get('main')
            if not main_circuit:
                # If no explicit 'main', pick the first non-hierarchical circuit
                for name, circuit in circuits.items():
                    if not (hasattr(circuit, 'is_hierarchical_sheet') and circuit.is_hierarchical_sheet):
                        main_circuit = circuit
                        break
                if not main_circuit:
                    main_circuit = list(circuits.values())[0]
            
            subcircuits = {name: circuit for name, circuit in circuits.items() 
                          if circuit != main_circuit}
            
            logger.info(f"🗂️ MULTI_FILE: Main circuit: {main_circuit.name}")
            logger.info(f"🗂️ MULTI_FILE: Subcircuits: {list(subcircuits.keys())}")
            
            # Identify shared nets between main and subcircuits
            main_net_names = {net.name for net in main_circuit.nets}
            shared_nets_per_subcircuit = {}
            
            for name, circuit in subcircuits.items():
                subcircuit_net_names = {net.name for net in circuit.nets}
                shared_nets = list(main_net_names.intersection(subcircuit_net_names))
                shared_nets_per_subcircuit[name] = shared_nets
                logger.info(f"🗂️ MULTI_FILE: Shared nets with {name}: {shared_nets}")
            
            # Generate subcircuit files
            subcircuit_files_created = []
            for name, circuit in subcircuits.items():
                subcircuit_file = output_dir / f"{name}.py"
                logger.info(f"🗂️ MULTI_FILE: Generating {subcircuit_file}")
                
                # Generate subcircuit code with shared nets as parameters
                shared_nets = shared_nets_per_subcircuit[name]
                subcircuit_code = self._generate_standalone_subcircuit_file(circuit, shared_nets)
                
                if preview_only:
                    logger.info(f"🗂️ MULTI_FILE: [PREVIEW] Would create {subcircuit_file}")
                    logger.info(f"🗂️ MULTI_FILE: [PREVIEW] Content preview:\n{subcircuit_code[:200]}...")
                else:
                    # Write subcircuit file
                    with open(subcircuit_file, 'w') as f:
                        f.write(subcircuit_code)
                    logger.info(f"🗂️ MULTI_FILE: ✅ Created {subcircuit_file}")
                
                subcircuit_files_created.append(name)
            
            # Generate main.py file
            main_code = self._generate_main_file_with_imports(main_circuit, subcircuit_files_created, shared_nets_per_subcircuit)
            
            if preview_only:
                logger.info(f"🗂️ MULTI_FILE: [PREVIEW] Would create {main_python_file}")
                logger.info("🗂️ MULTI_FILE: [PREVIEW] Main file content:")
                return main_code
            else:
                # Write main file
                with open(main_python_file, 'w') as f:
                    f.write(main_code)
                logger.info(f"🗂️ MULTI_FILE: ✅ Created {main_python_file}")
                return main_code
                
        except Exception as e:
            logger.error(f"🗂️ MULTI_FILE: Failed to generate multiple files: {e}")
            return None

    def _generate_standalone_subcircuit_file(self, circuit: Circuit, shared_nets: List[str] = None) -> str:
        """Generate a complete Python file for a single subcircuit"""
        logger.info(f"📄 SUBCIRCUIT_FILE: Generating standalone file for {circuit.name}")
        
        code_lines = []
        
        # File header
        code_lines.extend([
            '#!/usr/bin/env python3',
            '"""',
            f'{circuit.name} subcircuit generated from KiCad',
            '"""',
            '',
            'from circuit_synth import *',
            ''
        ])
        
        # Generate the subcircuit function with net parameters
        code_lines.extend(self._generate_subcircuit_code_with_params(circuit, shared_nets or []))
        
        result = "\n".join(code_lines)
        logger.info(f"📄 SUBCIRCUIT_FILE: Generated {len(code_lines)} lines for {circuit.name}")
        return result

    def _generate_subcircuit_code_with_params(self, circuit: Circuit, shared_nets: List[str]) -> List[str]:
        """Generate code for a subcircuit function with net parameters"""
        logger.info(f"🔧 SUBCIRCUIT_PARAMS: Generating parameterized code for {circuit.name}")
        
        code_lines = []
        
        # Function declaration with net parameters
        net_params = []
        for net_name in shared_nets:
            net_var = self._sanitize_variable_name(net_name)
            net_params.append(net_var)
        
        param_str = ", ".join(net_params) if net_params else ""
        code_lines.append(f"@circuit(name='{circuit.name}')")
        code_lines.append(f"def {circuit.name}({param_str}):")
        code_lines.append(f'    """')
        code_lines.append(f"    {circuit.name} subcircuit")
        if shared_nets:
            code_lines.append(f"    Parameters: {', '.join(shared_nets)}")
        code_lines.append(f'    """')

        # Create only local nets (not shared ones)
        if circuit.nets:
            local_nets = [net for net in circuit.nets if net.name not in shared_nets]
            if local_nets:
                code_lines.append("    # Create local nets")
                for net in local_nets:
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

        # Add connections (all nets, both shared and local)
        if circuit.nets:
            connected_nets = [net for net in circuit.nets if not net.name.startswith('unconnected-')]
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
                                code_lines.append(f"    {comp_var}['{pin}'] += {net_var}")

        logger.info(f"🔧 SUBCIRCUIT_PARAMS: Generated {len(code_lines)} lines for {circuit.name}")
        return code_lines

    def _generate_main_file_with_imports(self, main_circuit: Circuit, subcircuit_names: List[str], shared_nets_per_subcircuit: Dict[str, List[str]] = None) -> str:
        """Generate the main.py file that imports subcircuits from separate files"""
        logger.info(f"📄 MAIN_FILE: Generating main file with imports for {len(subcircuit_names)} subcircuits")
        
        code_lines = []
        
        # File header
        code_lines.extend([
            '#!/usr/bin/env python3',
            '"""',
            'Main circuit generated from KiCad',
            '"""',
            '',
            'from circuit_synth import *'
        ])
        
        # Import subcircuit functions from separate files
        if subcircuit_names:
            code_lines.append('')
            code_lines.append('# Import subcircuit functions')
            for subcircuit_name in subcircuit_names:
                code_lines.append(f'from {subcircuit_name} import {subcircuit_name}')
        
        code_lines.append('')
        
        # Generate main circuit function with proper subcircuit instantiation
        code_lines.extend(self._generate_main_circuit_code_with_params(main_circuit, subcircuit_names, shared_nets_per_subcircuit or {}))
        
        # Add generation code
        code_lines.extend([
            '',
            '# Generate the circuit',
            'if __name__ == \'__main__\':',
            '    circuit = main()',
            self._generate_project_call()
        ])
        
        result = "\n".join(code_lines)
        logger.info(f"📄 MAIN_FILE: Generated {len(code_lines)} lines for main circuit")
        return result

    def _generate_main_circuit_code_with_params(self, circuit: Circuit, subcircuit_names: List[str], shared_nets_per_subcircuit: Dict[str, List[str]]) -> List[str]:
        """Generate code for the main circuit function with proper subcircuit instantiation"""
        logger.info("🎯 MAIN_CIRCUIT_PARAMS: Generating main circuit code with net passing")
        
        code_lines = []
        
        # Function declaration  
        code_lines.append("@circuit(name='main')")
        code_lines.append("def main():")
        code_lines.append('    """')
        code_lines.append("    Main circuit with hierarchical subcircuits")
        code_lines.append('    """')

        # Create main circuit nets
        if circuit.nets:
            connected_nets = [net for net in circuit.nets if not net.name.startswith('unconnected-')]
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

        # Instantiate subcircuits with shared nets passed as parameters
        if subcircuit_names:
            code_lines.append("    # Instantiate subcircuits")
            for subcircuit_name in subcircuit_names:
                shared_nets = shared_nets_per_subcircuit.get(subcircuit_name, [])
                if shared_nets:
                    # Pass shared nets as parameters
                    net_args = []
                    for net_name in shared_nets:
                        net_var = self._sanitize_variable_name(net_name)
                        net_args.append(net_var)
                    args_str = ", ".join(net_args)
                    code_lines.append(f"    {subcircuit_name}_instance = {subcircuit_name}({args_str})")
                else:
                    # No shared nets
                    code_lines.append(f"    {subcircuit_name}_instance = {subcircuit_name}()")

        code_lines.append("")

        # Add main circuit connections
        if circuit.nets:
            connected_nets = [net for net in circuit.nets if not net.name.startswith('unconnected-')]
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
                                code_lines.append(f"    {comp_var}['{pin}'] += {net_var}")

        logger.info(f"🎯 MAIN_CIRCUIT_PARAMS: Generated {len(code_lines)} lines for main circuit")
        return code_lines

    def update_python_file(
        self, python_file: Path, circuits: Dict[str, Circuit], preview_only: bool = True
    ) -> Optional[str]:
        """Update Python file with circuit data - creates separate files for each circuit"""
        logger.info(f"🔄 CODE_UPDATE: Starting update of {python_file}")
        logger.info(f"🔄 CODE_UPDATE: Preview mode: {preview_only}")
        logger.info(f"🔄 CODE_UPDATE: Circuits to update: {list(circuits.keys())}")
        
        try:
            # Check if this is a hierarchical design
            is_hierarchical = len(circuits) > 1 or any(
                hasattr(circuit, 'is_hierarchical_sheet') and circuit.is_hierarchical_sheet 
                for circuit in circuits.values()
            )
            logger.info(f"📝 CODE_UPDATE: Hierarchical design: {is_hierarchical}")
            
            if is_hierarchical:
                logger.info("📝 CODE_UPDATE: Generating separate files for hierarchical circuits")
                return self._generate_multiple_files(python_file, circuits, preview_only)
            else:
                # For non-hierarchical (flat) circuits, still use the old single-file approach
                logger.info("📝 CODE_UPDATE: Generating single file for flat circuit")
                main_circuit = list(circuits.values())[0]
                updated_code = self._generate_flat_code(main_circuit)

            if updated_code:
                logger.info(f"🔄 CODE_UPDATE: Generated updated code: {len(updated_code)} chars")
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