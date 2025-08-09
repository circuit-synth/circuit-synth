"""
AI-Powered Circuit Debugging Agent for Claude Code

This agent provides comprehensive PCB debugging assistance with:
1. KiCad to Python conversion for LLM understanding
2. Real-world debugging knowledge from extensive knowledge base
3. Systematic fault-finding methodologies
4. Web search capability for additional insights
"""

import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class CircuitDebuggingAgent:
    """
    Advanced debugging agent with comprehensive knowledge base integration
    and KiCad-to-Python conversion capability
    """

    def __init__(self):
        """Initialize the debugging agent with knowledge bases"""
        self.knowledge_base_path = (
            Path(__file__).parent.parent.parent.parent.parent
            / "knowledge_base"
            / "debugging"
        )
        self.component_failures = self._load_knowledge("component_failure_modes.json")
        self.debugging_techniques = self._load_knowledge("debugging_techniques.json")
        self.common_problems = self._load_knowledge("common_problems_solutions.json")
        self.test_equipment = self._load_knowledge("test_equipment_guide.json")
        self.current_session = None
        self.converted_circuits = {}

    def _load_knowledge(self, filename: str) -> Dict:
        """Load a knowledge base file"""
        file_path = self.knowledge_base_path / filename
        if file_path.exists():
            with open(file_path, "r") as f:
                return json.load(f)
        return {}

    def convert_kicad_to_python(self, kicad_project_path: str) -> Dict[str, str]:
        """
        Convert KiCad project to Python circuit-synth code for analysis

        Args:
            kicad_project_path: Path to KiCad project directory

        Returns:
            Dictionary mapping subcircuit names to Python code
        """
        from circuit_synth.kicad_to_python import kicad_to_python_project

        logger.info(f"Converting KiCad project at {kicad_project_path} to Python...")

        try:
            # Convert the KiCad project to Python
            project_path = Path(kicad_project_path)

            # Find the .kicad_pro file
            kicad_pro_files = list(project_path.glob("*.kicad_pro"))
            if not kicad_pro_files:
                raise ValueError(f"No .kicad_pro file found in {project_path}")

            # Convert to Python - this generates multiple files for subcircuits
            output_dir = project_path / "debug_python_conversion"
            output_dir.mkdir(exist_ok=True)

            result = kicad_to_python_project(
                str(kicad_pro_files[0]),
                str(output_dir),
                split_subcircuits=True,  # Generate separate files for each subcircuit
            )

            # Load the generated Python files
            python_circuits = {}
            for py_file in output_dir.glob("*.py"):
                with open(py_file, "r") as f:
                    circuit_name = py_file.stem
                    python_circuits[circuit_name] = f.read()
                    logger.info(f"Loaded subcircuit: {circuit_name}")

            self.converted_circuits = python_circuits
            return python_circuits

        except Exception as e:
            logger.error(f"Failed to convert KiCad to Python: {e}")
            raise

    def analyze_circuit_code(
        self, circuit_code: str, symptoms: List[str]
    ) -> Dict[str, Any]:
        """
        Analyze Python circuit code for potential issues based on symptoms

        Args:
            circuit_code: Python circuit-synth code
            symptoms: List of observed symptoms

        Returns:
            Analysis results with potential issues and recommendations
        """
        analysis = {
            "circuit_components": [],
            "potential_issues": [],
            "recommendations": [],
            "relevant_knowledge": [],
        }

        # Parse circuit code to identify components
        import ast

        try:
            tree = ast.parse(circuit_code)

            # Extract component information
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if hasattr(node.func, "id") and node.func.id == "Component":
                        # Extract component details
                        component_info = self._extract_component_info(node)
                        analysis["circuit_components"].append(component_info)
        except:
            logger.warning("Could not parse circuit code as Python")

        # Match symptoms to knowledge base
        for symptom in symptoms:
            symptom_lower = symptom.lower()

            # Check component failure modes
            if self.component_failures:
                relevant_failures = self._find_relevant_failures(symptom_lower)
                for failure in relevant_failures:
                    analysis["potential_issues"].append(failure)

            # Check common problems
            if self.common_problems:
                relevant_problems = self._find_relevant_problems(symptom_lower)
                for problem in relevant_problems:
                    analysis["relevant_knowledge"].append(problem)

            # Get debugging techniques
            if self.debugging_techniques:
                techniques = self._get_debugging_techniques(symptom_lower)
                analysis["recommendations"].extend(techniques)

        return analysis

    def _extract_component_info(self, node: Any) -> Dict[str, str]:
        """Extract component information from AST node"""
        info = {"type": "Component"}

        for keyword in node.keywords:
            if keyword.arg == "symbol":
                if hasattr(keyword.value, "s"):
                    info["symbol"] = keyword.value.s
            elif keyword.arg == "ref":
                if hasattr(keyword.value, "s"):
                    info["reference"] = keyword.value.s
            elif keyword.arg == "value":
                if hasattr(keyword.value, "s"):
                    info["value"] = keyword.value.s

        return info

    def _find_relevant_failures(self, symptom: str) -> List[Dict]:
        """Find component failures relevant to symptom"""
        relevant = []

        if not self.component_failures.get("component_failure_modes"):
            return relevant

        for component_type, data in self.component_failures[
            "component_failure_modes"
        ].items():
            if "failure_modes" in data:
                for failure in data["failure_modes"]:
                    # Check if symptom matches
                    if any(s.lower() in symptom for s in failure.get("symptoms", [])):
                        relevant.append(
                            {
                                "component_type": component_type,
                                "failure_mode": failure.get("mode"),
                                "symptoms": failure.get("symptoms"),
                                "causes": failure.get("causes"),
                                "detection": failure.get("detection"),
                                "prevention": failure.get("prevention"),
                            }
                        )

            # Check subcategories (like ceramic, electrolytic for capacitors)
            for subtype, subdata in data.items():
                if isinstance(subdata, dict) and "failure_modes" in subdata:
                    for failure in subdata["failure_modes"]:
                        if any(
                            s.lower() in symptom for s in failure.get("symptoms", [])
                        ):
                            relevant.append(
                                {
                                    "component_type": f"{component_type}/{subtype}",
                                    "failure_mode": failure.get("mode"),
                                    "symptoms": failure.get("symptoms"),
                                    "causes": failure.get("causes"),
                                    "detection": failure.get("detection"),
                                    "prevention": failure.get("prevention"),
                                }
                            )

        return relevant

    def _find_relevant_problems(self, symptom: str) -> List[Dict]:
        """Find common PCB problems relevant to symptom"""
        relevant = []

        if not self.common_problems.get("common_pcb_problems"):
            return relevant

        problems = self.common_problems["common_pcb_problems"]

        # Search through all problem categories
        for category, issues in problems.items():
            if isinstance(issues, dict):
                for issue_name, issue_data in issues.items():
                    if isinstance(issue_data, dict):
                        # Check if symptom matches
                        issue_symptoms = issue_data.get("symptoms", [])
                        if isinstance(issue_symptoms, list):
                            if any(s.lower() in symptom for s in issue_symptoms):
                                relevant.append(
                                    {
                                        "category": category,
                                        "issue": issue_name,
                                        "description": issue_data.get("description"),
                                        "symptoms": issue_symptoms,
                                        "causes": issue_data.get("causes"),
                                        "detection": issue_data.get("detection"),
                                        "fixes": issue_data.get("fixes")
                                        or issue_data.get("repair"),
                                        "prevention": issue_data.get("prevention"),
                                    }
                                )

        return relevant

    def _get_debugging_techniques(self, symptom: str) -> List[str]:
        """Get relevant debugging techniques for symptom"""
        techniques = []

        if not self.debugging_techniques.get("debugging_techniques"):
            return techniques

        debug_tech = self.debugging_techniques["debugging_techniques"]

        # Map symptoms to debugging categories
        if "power" in symptom or "voltage" in symptom:
            if "power_supply_debugging" in debug_tech:
                power_debug = debug_tech["power_supply_debugging"]
                if "no_output" in power_debug:
                    steps = power_debug["no_output"].get("systematic_approach", [])
                    for step in steps:
                        if isinstance(step, dict):
                            techniques.append(
                                f"Step {step.get('step')}: {step.get('action')} - {step.get('details')}"
                            )

        if "i2c" in symptom:
            if "digital_communication_debugging" in debug_tech:
                i2c_debug = debug_tech["digital_communication_debugging"].get("i2c", {})
                if "no_ack" in i2c_debug:
                    checks = i2c_debug["no_ack"].get("systematic_check", [])
                    for check in checks:
                        if isinstance(check, dict):
                            techniques.append(
                                f"{check.get('test')}: {check.get('method')}"
                            )

        if "usb" in symptom:
            if "digital_communication_debugging" in debug_tech:
                usb_debug = debug_tech["digital_communication_debugging"].get("usb", {})
                if "enumeration_failure" in usb_debug:
                    steps = usb_debug["enumeration_failure"].get("systematic_debug", [])
                    for step in steps:
                        if isinstance(step, dict):
                            techniques.append(f"{step.get('step')}: {step.get('test')}")

        return techniques

    def generate_test_plan(
        self, symptoms: List[str], measurements: Dict[str, Any]
    ) -> List[Dict]:
        """
        Generate a systematic test plan based on symptoms and measurements

        Args:
            symptoms: List of observed symptoms
            measurements: Dictionary of measurements already taken

        Returns:
            List of test steps with equipment and expected results
        """
        test_plan = []

        # Determine test equipment needed
        equipment_needed = set()

        for symptom in symptoms:
            symptom_lower = symptom.lower()

            # Power-related tests
            if "power" in symptom_lower or "voltage" in symptom_lower:
                equipment_needed.add("multimeter")
                equipment_needed.add("oscilloscope")

                test_plan.append(
                    {
                        "step": len(test_plan) + 1,
                        "test": "Verify Input Power",
                        "equipment": "Multimeter",
                        "procedure": "Measure voltage at power input connector",
                        "expected": "Within specified input range (e.g., 5V ±5%)",
                        "if_fail": "Check power supply, cable, and connector",
                    }
                )

                test_plan.append(
                    {
                        "step": len(test_plan) + 1,
                        "test": "Check Power Rail Voltages",
                        "equipment": "Multimeter",
                        "procedure": "Measure all power rails (3.3V, 5V, etc.)",
                        "expected": "Within ±5% of nominal",
                        "if_fail": "Check voltage regulators and load conditions",
                    }
                )

                test_plan.append(
                    {
                        "step": len(test_plan) + 1,
                        "test": "Measure Ripple and Noise",
                        "equipment": "Oscilloscope",
                        "procedure": "AC couple scope, measure peak-to-peak ripple",
                        "expected": "<50mV p-p for digital, <10mV for analog",
                        "if_fail": "Check capacitors, add filtering",
                    }
                )

            # Digital communication tests
            if any(proto in symptom_lower for proto in ["i2c", "spi", "uart", "usb"]):
                equipment_needed.add("oscilloscope")
                equipment_needed.add("logic_analyzer")

                if "i2c" in symptom_lower:
                    test_plan.append(
                        {
                            "step": len(test_plan) + 1,
                            "test": "I2C Pull-up Resistors",
                            "equipment": "Multimeter",
                            "procedure": "Measure resistance from SDA/SCL to VDD (power off)",
                            "expected": "2.2kΩ to 10kΩ",
                            "if_fail": "Add or adjust pull-up resistors",
                        }
                    )

                    test_plan.append(
                        {
                            "step": len(test_plan) + 1,
                            "test": "I2C Bus Voltage",
                            "equipment": "Oscilloscope",
                            "procedure": "Check SDA/SCL idle voltage and signal levels",
                            "expected": "Idle high at VDD, proper logic levels",
                            "if_fail": "Check for stuck device or shorts",
                        }
                    )

            # Thermal tests
            if "hot" in symptom_lower or "thermal" in symptom_lower:
                equipment_needed.add("thermal_camera")

                test_plan.append(
                    {
                        "step": len(test_plan) + 1,
                        "test": "Thermal Imaging",
                        "equipment": "Thermal Camera",
                        "procedure": "Image board under normal operation",
                        "expected": "No components >70°C, even heat distribution",
                        "if_fail": "Identify hot spots for investigation",
                    }
                )

        # Add equipment summary
        test_plan.insert(
            0,
            {
                "equipment_required": list(equipment_needed),
                "preparation": "Ensure all test equipment is calibrated and ESD precautions are in place",
            },
        )

        return test_plan

    def search_web_for_solution(
        self, symptoms: List[str], board_info: Dict[str, str]
    ) -> str:
        """
        Search web for additional debugging information

        Args:
            symptoms: List of symptoms
            board_info: Dictionary with board details (name, version, components)

        Returns:
            Web search guidance prompt
        """
        # Build search query
        search_terms = []

        # Add board-specific terms if available
        if board_info.get("mcu"):
            search_terms.append(board_info["mcu"])

        # Add symptom-specific terms
        for symptom in symptoms:
            if "i2c" in symptom.lower():
                search_terms.extend(
                    ["I2C debugging", "I2C no ACK", "I2C troubleshooting"]
                )
            elif "power" in symptom.lower():
                search_terms.extend(
                    ["power supply debugging", "voltage regulator troubleshooting"]
                )
            elif "usb" in symptom.lower():
                search_terms.extend(["USB enumeration failure", "USB debugging"])

        # Create search guidance
        search_guidance = f"""
        To find additional solutions, search for:
        
        Primary searches:
        - {' '.join(search_terms[:3])}
        
        Specific forums and resources:
        - EEVblog Forum: Electronics debugging discussions
        - Stack Exchange Electrical Engineering
        - Manufacturer application notes for key components
        - Reference designs for similar circuits
        
        Look for:
        1. Similar symptoms reported by others
        2. Manufacturer errata or known issues
        3. Application notes with debugging sections
        4. Reference design troubleshooting guides
        """

        return search_guidance

    def generate_debug_report(
        self,
        kicad_path: str,
        symptoms: List[str],
        measurements: Dict[str, Any],
        observations: List[str],
    ) -> Dict[str, Any]:
        """
        Generate comprehensive debugging report

        Args:
            kicad_path: Path to KiCad project
            symptoms: List of observed symptoms
            measurements: Test measurements taken
            observations: Additional observations

        Returns:
            Complete debugging analysis report
        """
        report = {
            "timestamp": datetime.now().isoformat(),
            "project": kicad_path,
            "symptoms": symptoms,
            "measurements": measurements,
            "observations": observations,
        }

        # Convert KiCad to Python for analysis
        try:
            python_circuits = self.convert_kicad_to_python(kicad_path)
            report["circuits_analyzed"] = list(python_circuits.keys())

            # Analyze each circuit
            circuit_analyses = {}
            for circuit_name, circuit_code in python_circuits.items():
                analysis = self.analyze_circuit_code(circuit_code, symptoms)
                circuit_analyses[circuit_name] = analysis

            report["circuit_analysis"] = circuit_analyses
        except Exception as e:
            report["conversion_error"] = str(e)
            logger.error(f"Failed to convert/analyze circuits: {e}")

        # Generate test plan
        test_plan = self.generate_test_plan(symptoms, measurements)
        report["test_plan"] = test_plan

        # Find relevant knowledge
        all_failures = []
        all_problems = []
        all_techniques = []

        for symptom in symptoms:
            symptom_lower = symptom.lower()
            all_failures.extend(self._find_relevant_failures(symptom_lower))
            all_problems.extend(self._find_relevant_problems(symptom_lower))
            all_techniques.extend(self._get_debugging_techniques(symptom_lower))

        report["relevant_failure_modes"] = all_failures
        report["known_problems"] = all_problems
        report["debugging_techniques"] = all_techniques

        # Generate web search guidance
        board_info = {
            "mcu": "extracted_from_circuit"
        }  # Would extract from circuit analysis
        report["web_search_guidance"] = self.search_web_for_solution(
            symptoms, board_info
        )

        # Priority recommendations
        report["priority_actions"] = self._generate_priority_actions(
            symptoms, measurements, all_problems
        )

        return report

    def _generate_priority_actions(
        self, symptoms: List[str], measurements: Dict, problems: List
    ) -> List[str]:
        """Generate prioritized action items"""
        actions = []

        # Critical actions first
        if any(
            "not turning on" in s.lower() or "no power" in s.lower() for s in symptoms
        ):
            actions.append(
                "CRITICAL: Verify input power and check for shorts on power rails"
            )
            actions.append("CRITICAL: Test continuity from input to regulators")

        # High priority based on symptoms
        if any("i2c" in s.lower() for s in symptoms):
            actions.append("HIGH: Verify I2C pull-up resistors (2.2k-10k)")
            actions.append("HIGH: Check I2C addressing and voltage levels")

        if any("usb" in s.lower() for s in symptoms):
            actions.append("HIGH: Verify USB D+/D- routing and termination")
            actions.append("HIGH: Check crystal oscillation and frequency")

        # Medium priority - general checks
        actions.append("MEDIUM: Visual inspection for solder bridges and cold joints")
        actions.append("MEDIUM: Thermal imaging to identify hot spots")

        # Low priority - optimization
        actions.append("LOW: Review PCB layout for signal integrity improvements")
        actions.append("LOW: Check component date codes and authenticity")

        return actions[:7]  # Return top 7 actions


# Agent function for Claude Code
def debug_circuit(task_description: str) -> str:
    """
    Main entry point for Claude Code debugging agent

    Args:
        task_description: Description of debugging task

    Returns:
        Debugging analysis and recommendations
    """
    agent = CircuitDebuggingAgent()

    # Parse task description for key information
    # This would be enhanced with actual parsing logic

    result = """
    🔍 Circuit Debugging Agent Activated
    =====================================
    
    This agent will:
    1. Convert your KiCad project to Python for analysis
    2. Analyze symptoms against comprehensive knowledge base
    3. Generate systematic test plans
    4. Provide web search guidance for additional solutions
    
    To start debugging, provide:
    - Path to KiCad project
    - List of symptoms observed
    - Any measurements already taken
    - Additional observations
    
    The agent incorporates extensive real-world knowledge including:
    - Component failure modes database
    - Common PCB problems and solutions
    - Professional debugging techniques
    - Test equipment usage guides
    
    Ready to assist with systematic fault-finding!
    """

    return result
