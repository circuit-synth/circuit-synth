#!/usr/bin/env python3
"""
LLM-assisted code updating for KiCad to Python synchronization.

This module handles the intelligent updating of Python circuit code
using LLM assistance when available, with fallback to simpler updates.
"""

import logging
import os
import re
from pathlib import Path
from typing import Any, Dict, List, Optional

from circuit_synth.tools.utilities.models import Circuit, Component, Net

logger = logging.getLogger(__name__)


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
        var_name = re.sub(r"[^a-zA-Z0-9_]", "_", var_name)

        # Prefix with underscore if starts with a digit
        if var_name and var_name[0].isdigit():
            var_name = "_" + var_name

        # Handle empty names
        if not var_name or var_name == "_":
            var_name = "net"

        return var_name

    def _check_llm_availability(self) -> bool:
        """Check if LLM services are available"""
        logger.info("🔍 LLM_AVAILABILITY_CHECK: Starting LLM availability check")

        try:
            # Try different LLM import methods
            llm = None

            # Method 1: LLM features not currently available
            # Note: Advanced AI features are not implemented in this version
            pass

            # Method 2: Try direct litellm approach
            if llm is None:
                try:
                    import litellm

                    logger.info(
                        "🔍 LLM_AVAILABILITY_CHECK: Found litellm, testing connection"
                    )

                    # Try a simple test with Claude Sonnet
                    test_response = litellm.completion(
                        model="claude-3-sonnet-20240229",
                        messages=[{"role": "user", "content": "Hello, testing..."}],
                        max_tokens=10,
                    )

                    if test_response and test_response.choices:
                        logger.info(
                            "🔍 LLM_AVAILABILITY_CHECK: ✅ Direct litellm connection successful"
                        )
                        return True
                    else:
                        logger.warning(
                            "🔍 LLM_AVAILABILITY_CHECK: ❌ litellm test failed - no response"
                        )

                except ImportError:
                    logger.info(
                        "🔍 LLM_AVAILABILITY_CHECK: litellm not available (ImportError)"
                    )
                except Exception as e:
                    logger.warning(
                        f"🔍 LLM_AVAILABILITY_CHECK: litellm test failed: {str(e)[:100]}..."
                    )

            # Method 3: Check for OpenAI compatibility
            if llm is None:
                try:
                    import openai

                    logger.info(
                        "🔍 LLM_AVAILABILITY_CHECK: Found openai, checking for API key"
                    )

                    # Check if API key is available
                    api_key = openai.api_key or os.environ.get("OPENAI_API_KEY") or None

                    if api_key:
                        logger.info(
                            "🔍 LLM_AVAILABILITY_CHECK: ✅ OpenAI API key found"
                        )
                        return True
                    else:
                        logger.info(
                            "🔍 LLM_AVAILABILITY_CHECK: ❌ OpenAI API key not found"
                        )

                except ImportError:
                    logger.info(
                        "🔍 LLM_AVAILABILITY_CHECK: openai not available (ImportError)"
                    )
                except Exception as e:
                    logger.warning(
                        f"🔍 LLM_AVAILABILITY_CHECK: openai check failed: {str(e)[:100]}..."
                    )

            logger.info(
                "🔍 LLM_AVAILABILITY_CHECK: ❌ No LLM services available - using fallback code generation"
            )
            return False

        except Exception as e:
            logger.error(f"🔍 LLM_AVAILABILITY_CHECK: Unexpected error: {e}")
            return False

    def update_python_file(
        self, python_file: Path, circuits: Dict[str, Circuit], preview_only: bool = True
    ) -> Optional[str]:
        """Update Python file with circuit data"""
        logger.info(f"🔄 CODE_UPDATE: Starting update of {python_file}")
        logger.info(f"🔄 CODE_UPDATE: Preview mode: {preview_only}")
        logger.info(f"🔄 CODE_UPDATE: Circuits to update: {list(circuits.keys())}")

        try:
            # Read existing Python file or create empty one if it doesn't exist
            if python_file.exists():
                logger.info("🔄 CODE_UPDATE: Reading existing Python file")
                with open(python_file, "r") as f:
                    original_code = f.read()
                logger.info(
                    f"🔄 CODE_UPDATE: Original file size: {len(original_code)} chars"
                )
            else:
                logger.info(
                    "🔄 CODE_UPDATE: Python file doesn't exist, creating new one"
                )
                original_code = ""

            # Determine update strategy based on LLM availability
            if self.llm_available:
                logger.info("🔄 CODE_UPDATE: Using LLM-assisted update strategy")
                updated_code = self._llm_assisted_update(original_code, circuits)
            else:
                logger.info("🔄 CODE_UPDATE: Using fallback update strategy")
                updated_code = self._fallback_update(original_code, circuits)

            if updated_code:
                logger.info(
                    f"🔄 CODE_UPDATE: Generated updated code: {len(updated_code)} chars"
                )

                if preview_only:
                    logger.info("🔄 CODE_UPDATE: Preview mode - not writing to file")
                    return updated_code
                else:
                    logger.info("🔄 CODE_UPDATE: Writing updated code to file")
                    with open(python_file, "w") as f:
                        f.write(updated_code)
                    logger.info("🔄 CODE_UPDATE: ✅ File update completed")
                    return updated_code
            else:
                logger.error("🔄 CODE_UPDATE: ❌ Failed to generate updated code")
                return None

        except Exception as e:
            logger.error(f"🔄 CODE_UPDATE: Failed to update Python file: {e}")
            return None

    def _llm_assisted_update(
        self, original_code: str, circuits: Dict[str, Circuit]
    ) -> Optional[str]:
        """Use LLM to intelligently update the Python code"""
        logger.info("🤖 LLM_UPDATE: Starting LLM-assisted code update")

        try:
            # Prepare context for LLM
            context = self._prepare_llm_context(original_code, circuits)

            # For now, fall back to the simpler update since LLM integration is complex
            logger.info("🤖 LLM_UPDATE: Using simplified update for now")
            return self._fallback_update(original_code, circuits)

        except Exception as e:
            logger.error(f"🤖 LLM_UPDATE: LLM update failed: {e}")
            logger.info("🤖 LLM_UPDATE: Falling back to simple update")
            return self._fallback_update(original_code, circuits)

    def _prepare_llm_context(
        self, original_code: str, circuits: Dict[str, Circuit]
    ) -> str:
        """Prepare context information for LLM"""
        context_parts = []

        context_parts.append("=== ORIGINAL PYTHON CODE ===")
        context_parts.append(original_code)
        context_parts.append("")

        context_parts.append("=== CIRCUIT INFORMATION FROM KICAD ===")
        for circuit_name, circuit in circuits.items():
            context_parts.append(f"Circuit: {circuit_name}")
            context_parts.append(f"Components ({len(circuit.components)}):")
            for comp in circuit.components:
                context_parts.append(
                    f"  - {comp.reference}: {comp.lib_id} = {comp.value}"
                )

            context_parts.append(f"Nets ({len(circuit.nets)}):")
            for net in circuit.nets:
                connections = ", ".join(
                    [f"{ref}[{pin}]" for ref, pin in net.connections]
                )
                context_parts.append(f"  - {net.name}: {connections}")
            context_parts.append("")

        return "\n".join(context_parts)

    def _fallback_update(
        self, original_code: str, circuits: Dict[str, Circuit]
    ) -> Optional[str]:
        """Simple fallback update without LLM"""
        logger.info("📝 FALLBACK_UPDATE: Starting fallback code update")

        try:
            # Check if this is a hierarchical design
            is_hierarchical = len(circuits) > 1 or any(
                circuit.is_hierarchical_sheet for circuit in circuits.values()
            )

            logger.info(f"📝 FALLBACK_UPDATE: Hierarchical design: {is_hierarchical}")

            if is_hierarchical:
                logger.info("📝 FALLBACK_UPDATE: Generating hierarchical circuit code")
                return self._generate_hierarchical_code(circuits)
            else:
                logger.info("📝 FALLBACK_UPDATE: Generating flat circuit code")
                main_circuit = list(circuits.values())[0]
                return self._generate_flat_code(main_circuit)

        except Exception as e:
            logger.error(f"📝 FALLBACK_UPDATE: Fallback update failed: {e}")
            return None

    def _generate_hierarchical_code(self, circuits: Dict[str, Circuit]) -> str:
        """Generate hierarchical Python code"""
        logger.info("🏗️ HIERARCHICAL_CODE: Generating hierarchical circuit code")

        code_parts = []

        # Add imports
        code_parts.append("#!/usr/bin/env python3")
        code_parts.append('"""')
        code_parts.append("Hierarchical Circuit Generated from KiCad")
        code_parts.append('"""')
        code_parts.append("")
        code_parts.append("from circuit_synth import *")
        code_parts.append("")

        # Generate subcircuit functions for hierarchical sheets
        main_circuit = None
        hierarchical_tree = {}

        for circuit_name, circuit in circuits.items():
            if circuit.is_hierarchical_sheet:
                logger.info(
                    f"🏗️ HIERARCHICAL_CODE: Generating subcircuit: {circuit_name}"
                )
                subcircuit_code = self._generate_subcircuit_function(circuit)
                code_parts.extend(subcircuit_code)
                code_parts.append("")
            else:
                main_circuit = circuit
                if circuit.hierarchical_tree:
                    hierarchical_tree = circuit.hierarchical_tree

        # Generate main circuit function
        if main_circuit:
            logger.info("🏗️ HIERARCHICAL_CODE: Generating main circuit")
            main_code = self._generate_main_circuit_function(
                main_circuit, hierarchical_tree
            )
            code_parts.extend(main_code)
        else:
            logger.warning("🏗️ HIERARCHICAL_CODE: No main circuit found")

        # Add generation code
        code_parts.extend(
            [
                "",
                "# Generate the circuit",
                "if __name__ == '__main__':",
                "    circuit = main()",
                "    circuit.generate_kicad_project()",
            ]
        )

        result = "\n".join(code_parts)
        logger.info(
            f"🏗️ HIERARCHICAL_CODE: Generated {len(result)} characters of hierarchical code"
        )
        return result

    def _generate_subcircuit_function(self, circuit: Circuit) -> List[str]:
        """Generate code for a hierarchical subcircuit"""
        logger.info(f"🔧 SUBCIRCUIT: Generating subcircuit function for {circuit.name}")

        function_name = self._sanitize_variable_name(circuit.name)
        code_lines = []

        # Function definition with docstring
        code_lines.append(f"@circuit(name='{circuit.name}')")
        code_lines.append(f"def {function_name}():")
        code_lines.append(f'    """')
        code_lines.append(f"    {circuit.name} subcircuit")
        code_lines.append(f'    """')

        # Create nets
        if circuit.nets:
            code_lines.append("    # Create nets")
            for net in circuit.nets:
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

        # Add connections
        if circuit.nets:
            code_lines.append("    # Connections")
            for net in circuit.nets:
                if net.connections:
                    net_var = self._sanitize_variable_name(net.name)
                    for ref, pin in net.connections:
                        comp_var = self._sanitize_variable_name(ref)
                        if pin.isdigit():
                            code_lines.append(f"    {comp_var}[{pin}] += {net_var}")
                        else:
                            code_lines.append(f"    {comp_var}['{pin}'] += {net_var}")

        logger.info(
            f"🔧 SUBCIRCUIT: Generated {len(code_lines)} lines for {circuit.name}"
        )
        return code_lines

    def _generate_main_circuit_function(
        self, circuit: Circuit, hierarchical_tree: Dict[str, List[str]]
    ) -> List[str]:
        """Generate the main circuit function"""
        logger.info("🎯 MAIN_CIRCUIT: Generating main circuit function")

        code_lines = []

        # Function definition
        code_lines.append("@circuit(name='main')")
        code_lines.append("def main():")
        code_lines.append('    """')
        code_lines.append("    Main circuit with hierarchical subcircuits")
        code_lines.append('    """')

        # Create nets for main circuit
        if circuit.nets:
            code_lines.append("    # Main circuit nets")
            for net in circuit.nets:
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
                child_var = self._sanitize_variable_name(child_circuit)
                child_func = self._sanitize_variable_name(child_circuit)
                code_lines.append(f"    {child_var} = {child_func}()")

        code_lines.append("")

        # Add main circuit connections
        if circuit.nets:
            code_lines.append("    # Main circuit connections")
            for net in circuit.nets:
                if net.connections:
                    net_var = self._sanitize_variable_name(net.name)
                    for ref, pin in net.connections:
                        comp_var = self._sanitize_variable_name(ref)
                        if pin.isdigit():
                            code_lines.append(f"    {comp_var}[{pin}] += {net_var}")
                        else:
                            code_lines.append(f"    {comp_var}['{pin}'] += {net_var}")

        logger.info(
            f"🎯 MAIN_CIRCUIT: Generated {len(code_lines)} lines for main circuit"
        )
        return code_lines

    def _generate_flat_code(self, circuit: Circuit) -> str:
        """Generate flat (non-hierarchical) Python code"""
        logger.info("📄 FLAT_CODE: Generating flat circuit code")

        code_parts = []

        # Add imports
        code_parts.append("#!/usr/bin/env python3")
        code_parts.append('"""')
        code_parts.append("Circuit Generated from KiCad")
        code_parts.append('"""')
        code_parts.append("")
        code_parts.append("from circuit_synth import *")
        code_parts.append("")

        # Generate main function
        code_parts.append("@circuit")
        code_parts.append("def main():")
        code_parts.append('    """Generated circuit from KiCad"""')

        # Create nets
        if circuit.nets:
            code_parts.append("    # Create nets")
            for net in circuit.nets:
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

        # Add connections
        if circuit.nets:
            code_parts.append("    # Connections")
            for net in circuit.nets:
                if net.connections:
                    net_var = self._sanitize_variable_name(net.name)
                    for ref, pin in net.connections:
                        comp_var = self._sanitize_variable_name(ref)
                        if pin.isdigit():
                            code_parts.append(f"    {comp_var}[{pin}] += {net_var}")
                        else:
                            code_parts.append(f"    {comp_var}['{pin}'] += {net_var}")

        # Add generation code
        code_parts.extend(
            [
                "",
                "# Generate the circuit",
                "if __name__ == '__main__':",
                "    circuit = main()",
                "    circuit.generate_kicad_project()",
            ]
        )

        result = "\n".join(code_parts)
        logger.info(f"📄 FLAT_CODE: Generated {len(result)} characters of flat code")
        return result

    def _generate_component_code(
        self, component: Component, indent: str = ""
    ) -> List[str]:
        """Generate Python code for a component"""
        comp_var = self._sanitize_variable_name(component.reference)

        code_lines = []

        # Build component creation line
        parts = [
            f'symbol="{component.lib_id}"',
            f'ref="{component.reference[0]}"',  # Get the letter part (R, C, U, etc.)
        ]

        if component.value:
            parts.append(f'value="{component.value}"')
        if component.footprint:
            parts.append(f'footprint="{component.footprint}"')

        component_args = ", ".join(parts)
        code_lines.append(f"{indent}{comp_var} = Component({component_args})")

        return code_lines
