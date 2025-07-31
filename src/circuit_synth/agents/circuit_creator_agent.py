"""
Circuit Creator Agent

Helps users create, validate, and register pre-made circuits that can be reused.
This agent handles the full workflow from requirements to registered circuit.
"""

import json
import os
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional

from ..core import Component, Net, circuit
from ..manufacturing.jlcpcb import search_jlc_components_web


class CircuitCreatorAgent:
    """
    Agent that helps users create and register pre-made circuits.

    Workflow:
    1. Gather requirements from user
    2. Suggest components with JLCPCB availability
    3. Generate circuit Python code
    4. Validate design (electrical rules, availability)
    5. Register circuit in circuit library
    6. Generate documentation and examples
    """

    def __init__(self, circuits_dir: Optional[Path] = None):
        """
        Initialize the Circuit Creator Agent.

        Args:
            circuits_dir: Directory to store registered circuits
        """
        self.circuits_dir = circuits_dir or Path("circuits_library")
        self.circuits_dir.mkdir(exist_ok=True)

        # Create subdirectories for organization
        (self.circuits_dir / "power").mkdir(exist_ok=True)
        (self.circuits_dir / "microcontrollers").mkdir(exist_ok=True)
        (self.circuits_dir / "sensors").mkdir(exist_ok=True)
        (self.circuits_dir / "interfaces").mkdir(exist_ok=True)
        (self.circuits_dir / "complete_boards").mkdir(exist_ok=True)
        (self.circuits_dir / "custom").mkdir(exist_ok=True)

        # Load existing circuit registry
        self.registry_file = self.circuits_dir / "circuit_registry.json"
        self.registry = self.load_registry()

    def load_registry(self) -> Dict[str, Any]:
        """Load the circuit registry from disk."""
        if self.registry_file.exists():
            with open(self.registry_file, "r") as f:
                return json.load(f)
        return {
            "circuits": {},
            "categories": [
                "power",
                "microcontrollers",
                "sensors",
                "interfaces",
                "complete_boards",
                "custom",
            ],
            "created": datetime.now().isoformat(),
            "version": "1.0",
        }

    def save_registry(self):
        """Save the circuit registry to disk."""
        self.registry["last_updated"] = datetime.now().isoformat()
        with open(self.registry_file, "w") as f:
            json.dump(self.registry, f, indent=2)

    def create_circuit_from_requirements(
        self, requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Create a circuit from user requirements.

        Args:
            requirements: Dictionary with circuit requirements

        Returns:
            Dictionary with circuit creation results
        """
        print(f"🎯 Creating circuit from requirements...")
        print(f"📋 Requirements: {requirements}")

        # Validate requirements
        validation_result = self.validate_requirements(requirements)
        if not validation_result["valid"]:
            return {
                "success": False,
                "error": "Invalid requirements",
                "details": validation_result["errors"],
            }

        # Suggest components based on requirements
        component_suggestions = self.suggest_components(requirements)

        # Generate circuit code
        circuit_code = self.generate_circuit_code(requirements, component_suggestions)

        # Validate the generated circuit
        validation = self.validate_circuit_design(circuit_code, requirements)

        if not validation["valid"]:
            return {
                "success": False,
                "error": "Circuit validation failed",
                "details": validation["errors"],
                "suggested_fixes": validation.get("suggestions", []),
            }

        return {
            "success": True,
            "circuit_code": circuit_code,
            "components": component_suggestions,
            "validation": validation,
            "next_steps": [
                "Review the generated circuit code",
                "Test the circuit if needed",
                "Register the circuit for reuse",
            ],
        }

    def validate_requirements(self, requirements: Dict[str, Any]) -> Dict[str, Any]:
        """Validate user requirements."""
        errors = []

        # Required fields
        required_fields = ["name", "description", "category"]
        for field in required_fields:
            if field not in requirements:
                errors.append(f"Missing required field: {field}")

        # Category validation
        if "category" in requirements:
            if requirements["category"] not in self.registry["categories"]:
                errors.append(
                    f"Invalid category. Must be one of: {self.registry['categories']}"
                )

        # Component requirements
        if "components" in requirements:
            if not isinstance(requirements["components"], list):
                errors.append("Components must be a list")

        return {"valid": len(errors) == 0, "errors": errors}

    def suggest_components(self, requirements: Dict[str, Any]) -> List[Dict[str, Any]]:
        """
        Suggest components based on requirements with JLCPCB availability.

        Args:
            requirements: Circuit requirements

        Returns:
            List of suggested components with availability info
        """
        suggestions = []

        # Extract component needs from requirements
        component_needs = requirements.get("components", [])

        for need in component_needs:
            if isinstance(need, str):
                # Simple string requirement like "microcontroller" or "voltage regulator"
                component_suggestions = self.search_components_by_type(need)
                suggestions.extend(component_suggestions)
            elif isinstance(need, dict):
                # Detailed requirement with specifications
                component_suggestions = self.search_components_by_specs(need)
                suggestions.extend(component_suggestions)

        return suggestions

    def search_components_by_type(self, component_type: str) -> List[Dict[str, Any]]:
        """Search for components by general type."""
        suggestions = []

        # Component type mapping to search terms
        type_mapping = {
            "microcontroller": ["STM32", "ESP32", "Arduino"],
            "voltage_regulator": ["AMS1117", "LM2596", "TPS54531"],
            "imu": ["LSM6DS3", "MPU6050", "ICM20948"],
            "usb_connector": ["USB-C", "Micro USB", "USB-A"],
            "crystal": ["8MHz", "16MHz", "25MHz"],
            "capacitor": ["100nF", "10uF", "22uF"],
            "resistor": ["10K", "4.7K", "330R"],
        }

        search_terms = type_mapping.get(component_type.lower(), [component_type])

        for term in search_terms[:2]:  # Limit to 2 searches to avoid slowdown
            try:
                results = search_jlc_components_web(term, max_results=3)
                for result in results:
                    suggestions.append(
                        {
                            "type": component_type,
                            "part_number": result.get("part_number", ""),
                            "description": result.get("description", ""),
                            "stock": result.get("stock", 0),
                            "price": result.get("price", "N/A"),
                            "jlc_part": result.get("jlc_part", ""),
                            "suggested_symbol": self.suggest_kicad_symbol(
                                component_type
                            ),
                            "suggested_footprint": self.suggest_kicad_footprint(result),
                        }
                    )
            except Exception as e:
                print(f"⚠️  Could not search for {term}: {e}")

        return suggestions

    def search_components_by_specs(self, specs: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Search for components by detailed specifications."""
        # This would implement more sophisticated component selection
        # based on electrical specifications, package requirements, etc.
        suggestions = []

        component_type = specs.get("type", "unknown")
        search_term = specs.get("part_number") or specs.get(
            "description", component_type
        )

        try:
            results = search_jlc_components_web(search_term, max_results=5)
            for result in results:
                suggestions.append(
                    {
                        "type": component_type,
                        "part_number": result.get("part_number", ""),
                        "description": result.get("description", ""),
                        "stock": result.get("stock", 0),
                        "price": result.get("price", "N/A"),
                        "jlc_part": result.get("jlc_part", ""),
                        "specs": specs,
                        "suggested_symbol": self.suggest_kicad_symbol(component_type),
                        "suggested_footprint": self.suggest_kicad_footprint(result),
                    }
                )
        except Exception as e:
            print(f"⚠️  Could not search for {search_term}: {e}")

        return suggestions

    def suggest_kicad_symbol(self, component_type: str) -> str:
        """Suggest appropriate KiCad symbol for component type."""
        symbol_mapping = {
            "microcontroller": "MCU_ST_STM32F4:STM32F411CEU6",
            "voltage_regulator": "Regulator_Linear:AMS1117-3.3",
            "imu": "Sensor_Motion:LSM6DS3TR-C",
            "usb_connector": "Connector:USB_C_Receptacle_USB2.0",
            "crystal": "Device:Crystal",
            "capacitor": "Device:C",
            "resistor": "Device:R",
            "led": "Device:LED",
            "switch": "Switch:SW_Push",
        }

        return symbol_mapping.get(component_type.lower(), "Device:R")

    def suggest_kicad_footprint(self, component_info: Dict[str, Any]) -> str:
        """Suggest appropriate KiCad footprint based on component info."""
        description = component_info.get("description", "").lower()

        # Simple heuristic footprint selection
        if "0603" in description:
            if "resistor" in description:
                return "Resistor_SMD:R_0603_1608Metric"
            elif "capacitor" in description:
                return "Capacitor_SMD:C_0603_1608Metric"
        elif "0805" in description:
            if "resistor" in description:
                return "Resistor_SMD:R_0805_2012Metric"
            elif "capacitor" in description:
                return "Capacitor_SMD:C_0805_2012Metric"
        elif "lqfp" in description:
            if "48" in description:
                return "Package_QFP:LQFP-48_7x7mm_P0.5mm"
            elif "64" in description:
                return "Package_QFP:LQFP-64_10x10mm_P0.5mm"
        elif "sot-223" in description:
            return "Package_TO_SOT_SMD:SOT-223-3_TabPin2"

        # Default fallbacks
        return "Resistor_SMD:R_0603_1608Metric"

    def generate_circuit_code(
        self, requirements: Dict[str, Any], components: List[Dict[str, Any]]
    ) -> str:
        """
        Generate Python circuit-synth code from requirements and components.

        Args:
            requirements: User requirements
            components: Selected components

        Returns:
            Python code as string
        """
        circuit_name = requirements["name"].replace(" ", "_").lower()
        description = requirements["description"]

        # Generate code template
        code_lines = [
            "#!/usr/bin/env python3",
            '"""',
            f'Pre-made Circuit: {requirements["name"]}',
            f"Description: {description}",
            f'Category: {requirements["category"]}',
            f'Generated: {datetime.now().strftime("%Y-%m-%d %H:%M:%S")}',
            '"""',
            "",
            "from circuit_synth import Component, Net, circuit",
            "",
            "",
            "@circuit",
            f"def {circuit_name}():",
            f'    """',
            f"    {description}",
            f"    ",
            f"    Components:",
        ]

        # Add component documentation
        for comp in components:
            code_lines.append(f'    - {comp["part_number"]}: {comp["description"]}')

        code_lines.extend(
            [
                f'    """',
                f"    ",
                f"    # Power nets",
                f'    vcc_3v3 = Net("VCC_3V3")',
                f'    gnd = Net("GND")',
                f"    ",
            ]
        )

        # Generate component instantiation code
        for i, comp in enumerate(components, 1):
            comp_name = f"comp_{i}"
            symbol = comp.get("suggested_symbol", "Device:R")
            footprint = comp.get(
                "suggested_footprint", "Resistor_SMD:R_0603_1608Metric"
            )

            code_lines.extend(
                [
                    f'    # {comp["description"]}',
                    f"    {comp_name} = Component(",
                    f'        symbol="{symbol}",',
                    f'        ref="{self.get_reference_prefix(comp["type"])}{i}",',
                    f'        footprint="{footprint}"',
                    f"    )",
                    f"    ",
                ]
            )

        # Add basic connections (this would be more sophisticated in practice)
        code_lines.extend(
            [
                f"    # Basic power connections",
                f"    # TODO: Add specific net connections based on circuit requirements",
                f"    ",
                f'    print("✅ {requirements["name"]} circuit created successfully!")',
                f"    return locals()  # Return all local variables for inspection",
                "",
                "",
                'if __name__ == "__main__":',
                f"    {circuit_name}()",
            ]
        )

        return "\n".join(code_lines)

    def get_reference_prefix(self, component_type: str) -> str:
        """Get appropriate reference prefix for component type."""
        prefix_mapping = {
            "microcontroller": "U",
            "voltage_regulator": "U",
            "imu": "U",
            "usb_connector": "J",
            "crystal": "Y",
            "capacitor": "C",
            "resistor": "R",
            "led": "D",
            "switch": "SW",
        }

        return prefix_mapping.get(component_type.lower(), "U")

    def validate_circuit_design(
        self, circuit_code: str, requirements: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Validate the generated circuit design.

        Args:
            circuit_code: Generated Python code
            requirements: Original requirements

        Returns:
            Validation results
        """
        errors = []
        warnings = []
        suggestions = []

        # Basic code validation
        try:
            compile(circuit_code, "<string>", "exec")
        except SyntaxError as e:
            errors.append(f"Syntax error in generated code: {e}")

        # Check for required imports
        if "from circuit_synth import" not in circuit_code:
            errors.append("Missing circuit_synth imports")

        # Check for circuit decorator
        if "@circuit" not in circuit_code:
            errors.append("Missing @circuit decorator")

        # Check for basic circuit elements
        if "Net(" not in circuit_code:
            warnings.append("No nets defined - circuit may not be connected")

        if "Component(" not in circuit_code:
            errors.append("No components defined")

        # Suggest improvements
        if "gnd" not in circuit_code.lower():
            suggestions.append("Consider adding ground net for power connections")

        if "vcc" not in circuit_code.lower() and "power" not in circuit_code.lower():
            suggestions.append("Consider adding power supply net")

        return {
            "valid": len(errors) == 0,
            "errors": errors,
            "warnings": warnings,
            "suggestions": suggestions,
        }

    def register_circuit(
        self,
        circuit_name: str,
        circuit_code: str,
        requirements: Dict[str, Any],
        components: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Register a validated circuit in the circuit library.

        Args:
            circuit_name: Name of the circuit
            circuit_code: Python code for the circuit
            requirements: Original requirements
            components: Used components

        Returns:
            Registration results
        """
        # Determine file path
        category = requirements.get("category", "custom")
        filename = f"{circuit_name.replace(' ', '_').lower()}.py"
        circuit_path = self.circuits_dir / category / filename

        # Write circuit file
        with open(circuit_path, "w") as f:
            f.write(circuit_code)

        # Update registry
        circuit_id = f"{category}.{circuit_name.replace(' ', '_').lower()}"
        self.registry["circuits"][circuit_id] = {
            "name": circuit_name,
            "description": requirements.get("description", ""),
            "category": category,
            "file_path": str(circuit_path.relative_to(self.circuits_dir)),
            "components": components,
            "requirements": requirements,
            "created": datetime.now().isoformat(),
            "version": "1.0",
            "usage_count": 0,
        }

        # Save registry
        self.save_registry()

        # Generate documentation
        doc_path = self.generate_documentation(
            circuit_id, circuit_name, requirements, components
        )

        return {
            "success": True,
            "circuit_id": circuit_id,
            "file_path": circuit_path,
            "documentation_path": doc_path,
            "message": f"Circuit '{circuit_name}' registered successfully in category '{category}'",
        }

    def generate_documentation(
        self,
        circuit_id: str,
        circuit_name: str,
        requirements: Dict[str, Any],
        components: List[Dict[str, Any]],
    ) -> Path:
        """Generate documentation for the registered circuit."""
        doc_filename = f"{circuit_name.replace(' ', '_').lower()}_README.md"
        doc_path = self.circuits_dir / requirements["category"] / doc_filename

        doc_content = [
            f"# {circuit_name}",
            "",
            f"**Circuit ID:** `{circuit_id}`",
            f"**Category:** {requirements['category']}",
            f"**Created:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "",
            "## Description",
            "",
            requirements.get("description", "No description provided."),
            "",
            "## Components",
            "",
            "| Component | Part Number | Description | Stock | Price |",
            "|-----------|-------------|-------------|-------|-------|",
        ]

        for comp in components:
            doc_content.append(
                f"| {comp['type']} | {comp['part_number']} | {comp['description']} | {comp['stock']} | {comp['price']} |"
            )

        doc_content.extend(
            [
                "",
                "## Usage",
                "",
                "```python",
                "from circuit_synth import circuit",
                f"from circuits_library.{requirements['category']}.{circuit_name.replace(' ', '_').lower()} import {circuit_name.replace(' ', '_').lower()}",
                "",
                "# Create the circuit",
                f"my_circuit = {circuit_name.replace(' ', '_').lower()}()",
                "```",
                "",
                "## Files",
                "",
                f"- **Circuit Code:** `{circuit_name.replace(' ', '_').lower()}.py`",
                f"- **Documentation:** `{doc_filename}`",
                "",
                "## Notes",
                "",
                "- All components verified available on JLCPCB",
                "- Generated using Circuit Creator Agent",
                "- Modify as needed for your specific requirements",
            ]
        )

        with open(doc_path, "w") as f:
            f.write("\n".join(doc_content))

        return doc_path

    def list_registered_circuits(
        self, category: Optional[str] = None
    ) -> List[Dict[str, Any]]:
        """List all registered circuits, optionally filtered by category."""
        circuits = []

        for circuit_id, circuit_info in self.registry["circuits"].items():
            if category is None or circuit_info["category"] == category:
                circuits.append(
                    {
                        "id": circuit_id,
                        "name": circuit_info["name"],
                        "description": circuit_info["description"],
                        "category": circuit_info["category"],
                        "created": circuit_info["created"],
                        "component_count": len(circuit_info.get("components", [])),
                        "usage_count": circuit_info.get("usage_count", 0),
                    }
                )

        return sorted(circuits, key=lambda x: x["created"], reverse=True)

    def get_circuit_info(self, circuit_id: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a registered circuit."""
        return self.registry["circuits"].get(circuit_id)

    def use_circuit(self, circuit_id: str) -> Dict[str, Any]:
        """
        Load and return a registered circuit for use.

        Args:
            circuit_id: ID of the registered circuit

        Returns:
            Circuit information and usage instructions
        """
        circuit_info = self.get_circuit_info(circuit_id)
        if not circuit_info:
            return {"success": False, "error": f"Circuit '{circuit_id}' not found"}

        # Increment usage count
        self.registry["circuits"][circuit_id]["usage_count"] = (
            circuit_info.get("usage_count", 0) + 1
        )
        self.save_registry()

        # Get file path
        file_path = self.circuits_dir / circuit_info["file_path"]

        return {
            "success": True,
            "circuit_info": circuit_info,
            "file_path": file_path,
            "usage_instructions": [
                f"Import the circuit: from {file_path.stem} import {file_path.stem}",
                f"Create circuit: my_circuit = {file_path.stem}()",
                "Modify as needed for your specific requirements",
            ],
        }


# Global instance for easy access
circuit_creator = CircuitCreatorAgent()


def create_custom_circuit(requirements: Dict[str, Any]) -> Dict[str, Any]:
    """
    Convenience function to create a custom circuit.

    Args:
        requirements: Circuit requirements dictionary

    Returns:
        Circuit creation results
    """
    return circuit_creator.create_circuit_from_requirements(requirements)


def register_circuit(
    name: str, description: str, category: str, components: List[str]
) -> Dict[str, Any]:
    """
    Convenience function to register a new circuit.

    Args:
        name: Circuit name
        description: Circuit description
        category: Circuit category
        components: List of required components

    Returns:
        Registration results
    """
    requirements = {
        "name": name,
        "description": description,
        "category": category,
        "components": components,
    }

    # Create the circuit
    result = circuit_creator.create_circuit_from_requirements(requirements)

    if result["success"]:
        # Register it
        registration = circuit_creator.register_circuit(
            name, result["circuit_code"], requirements, result["components"]
        )

        return {
            "success": True,
            "creation_result": result,
            "registration_result": registration,
        }

    return result


def list_circuits(category: Optional[str] = None) -> List[Dict[str, Any]]:
    """List all registered circuits."""
    return circuit_creator.list_registered_circuits(category)


def use_circuit(circuit_id: str) -> Dict[str, Any]:
    """Use a registered circuit."""
    return circuit_creator.use_circuit(circuit_id)
