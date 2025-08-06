"""
Real-time Circuit Design Validation

Called by Claude Code hooks to provide immediate feedback on circuit design
quality, component availability, and manufacturing readiness.
"""

import ast
import re
import sys
from pathlib import Path
from typing import Dict, List, Optional, Tuple


def extract_components_from_file(file_path: str) -> List[Dict[str, str]]:
    """Extract Component definitions from circuit-synth Python file"""

    try:
        with open(file_path, "r") as f:
            content = f.read()

        components = []

        # Parse with AST for robust extraction
        try:
            tree = ast.parse(content)

            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    # Look for Component() calls
                    if (
                        isinstance(node.func, ast.Name) and node.func.id == "Component"
                    ) or (
                        isinstance(node.func, ast.Attribute)
                        and node.func.attr == "Component"
                    ):

                        component = {}

                        # Extract keyword arguments
                        for keyword in node.keywords:
                            if keyword.arg in ["symbol", "ref", "footprint", "value"]:
                                if isinstance(keyword.value, ast.Constant):
                                    component[keyword.arg] = keyword.value.value

                        if component:
                            components.append(component)

        except SyntaxError:
            # Fallback to regex if AST parsing fails
            component_patterns = [
                r'Component\s*\([^)]*symbol\s*=\s*["\']([^"\']*)["\'][^)]*\)',
                r'Component\s*\([^)]*ref\s*=\s*["\']([^"\']*)["\'][^)]*\)',
                r'Component\s*\([^)]*footprint\s*=\s*["\']([^"\']*)["\'][^)]*\)',
            ]

            for pattern in component_patterns:
                matches = re.findall(pattern, content)
                for match in matches:
                    components.append({"symbol": match})

        return components

    except Exception as e:
        print(f"⚠️  Error extracting components: {e}")
        return []


def validate_component_symbols(components: List[Dict[str, str]]) -> List[str]:
    """Validate that component symbols follow KiCad conventions"""

    issues = []

    for comp in components:
        symbol = comp.get("symbol", "")
        if not symbol:
            continue

        # Check symbol format (Library:Symbol)
        if ":" not in symbol:
            issues.append(
                f"Invalid symbol format '{symbol}' - should be 'Library:Symbol'"
            )
            continue

        library, symbol_name = symbol.split(":", 1)

        # Check for common library names
        common_libraries = [
            "Device",
            "Connector",
            "Connector_Generic",
            "MCU_ST_STM32G4",
            "MCU_ST_STM32F4",
            "RF_Module",
            "Regulator_Linear",
            "Amplifier_Operational",
        ]

        if library not in common_libraries:
            # Not necessarily an error, but worth noting
            pass

        # Check reference designator conventions
        ref = comp.get("ref", "")
        if ref:
            if library.startswith("MCU") and not ref.startswith("U"):
                issues.append(f"MCU component should use 'U' reference, not '{ref}'")
            elif "Connector" in library and not ref.startswith("J"):
                issues.append(f"Connector should use 'J' reference, not '{ref}'")

    return issues


def check_net_connectivity(file_path: str) -> List[str]:
    """Check for potential net connectivity issues"""

    issues = []

    try:
        with open(file_path, "r") as f:
            content = f.read()

        # Look for net assignments (component["pin"] += net)
        net_assignments = re.findall(r"(\w+)\[\"([^\"]*)\"\]\s*\+=\s*(\w+)", content)
        net_assignments += re.findall(r"(\w+)\['([^']*)'\]\s*\+=\s*(\w+)", content)

        # Look for Net() definitions
        net_definitions = re.findall(r"(\w+)\s*=\s*Net\s*\(\"([^\"]*)\"\)", content)
        net_definitions += re.findall(r"(\w+)\s*=\s*Net\s*\('([^']*)'\)", content)

        defined_nets = {net_name for net_name, _ in net_definitions}
        used_nets = {net_name for _, _, net_name in net_assignments}

        # Check for undefined nets
        undefined_nets = used_nets - defined_nets
        if undefined_nets:
            issues.append(f"Undefined nets used: {', '.join(undefined_nets)}")

        # Check for unused nets
        unused_nets = defined_nets - used_nets
        if unused_nets:
            issues.append(f"Defined but unused nets: {', '.join(unused_nets)}")

        # Check for common power nets
        power_nets = ["VCC", "VDD", "GND", "VBAT", "3V3", "5V"]
        found_power_nets = [
            net for net in defined_nets if any(pwr in net.upper() for pwr in power_nets)
        ]

        if not found_power_nets:
            issues.append("No power/ground nets detected - verify power connections")

    except Exception as e:
        issues.append(f"Error checking net connectivity: {e}")

    return issues


def validate_circuit_functions(file_path: str) -> List[str]:
    """Validate circuit function definitions and decorators"""

    issues = []

    try:
        with open(file_path, "r") as f:
            content = f.read()

        # Parse AST to find functions with @circuit decorator
        tree = ast.parse(content)
        circuit_functions = []

        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef):
                has_circuit_decorator = False

                for decorator in node.decorator_list:
                    if (
                        isinstance(decorator, ast.Name) and decorator.id == "circuit"
                    ) or (
                        isinstance(decorator, ast.Call)
                        and isinstance(decorator.func, ast.Name)
                        and decorator.func.id == "circuit"
                    ):
                        has_circuit_decorator = True
                        break

                if has_circuit_decorator:
                    circuit_functions.append(node.name)

        if not circuit_functions:
            # Check if there are Component definitions without @circuit
            if "Component(" in content:
                issues.append(
                    "Found Component definitions but no @circuit decorated functions"
                )

        # Check for docstrings in circuit functions
        for func_name in circuit_functions:
            func_pattern = rf"def\s+{func_name}\s*\([^)]*\)\s*:"
            match = re.search(func_pattern, content)
            if match:
                # Look for docstring after function definition
                after_func = content[match.end() :]
                if not re.match(r'\s*""".*?"""', after_func, re.DOTALL):
                    issues.append(
                        f"Function '{func_name}' missing docstring (used for schematic annotations)"
                    )

    except SyntaxError as e:
        issues.append(f"Python syntax error: {e}")
    except Exception as e:
        issues.append(f"Error validating circuit functions: {e}")

    return issues


def validate_circuit_file(file_path: str) -> None:
    """Main validation function called by Claude Code hooks"""

    if not file_path or not Path(file_path).exists():
        print("⚠️  File not found for validation")
        return

    print(f"🔍 Validating circuit design: {Path(file_path).name}")

    all_issues = []

    # Extract and validate components
    components = extract_components_from_file(file_path)
    if components:
        print(f"📦 Found {len(components)} components")

        symbol_issues = validate_component_symbols(components)
        all_issues.extend(symbol_issues)

    # Check net connectivity
    net_issues = check_net_connectivity(file_path)
    all_issues.extend(net_issues)

    # Validate circuit functions
    function_issues = validate_circuit_functions(file_path)
    all_issues.extend(function_issues)

    # Report results
    if not all_issues:
        print("✅ Circuit validation passed - no issues found")
    else:
        print(f"⚠️  Found {len(all_issues)} design issues:")
        for i, issue in enumerate(all_issues, 1):
            print(f"   {i}. {issue}")

    # Provide helpful suggestions
    if components:
        print("💡 Suggestions:")
        print("   - Use /check-manufacturing to verify component availability")
        print("   - Use /analyze-power for power supply recommendations")
        print("   - Use /optimize-routing for signal integrity analysis")


def main():
    """CLI entry point for validation"""
    if len(sys.argv) != 2:
        print(
            "Usage: python -m circuit_synth.ai_integration.validation.real_time_check <file_path>"
        )
        sys.exit(1)

    validate_circuit_file(sys.argv[1])


if __name__ == "__main__":
    main()
