"""
Enhanced circuit generation agent with built-in validation.

This agent extends the existing circuit-synth capabilities with automatic
validation and context-aware generation.
"""

import logging
from typing import Optional

from ..validation import get_circuit_design_context, validate_and_improve_circuit

logger = logging.getLogger(__name__)


class ValidatedCircuitGenerator:
    """Circuit generator with integrated validation and context awareness."""

    def __init__(self):
        # Note: This would integrate with existing circuit-synth agent system
        # For now, we'll create a simple implementation
        pass

    async def generate_validated_circuit(
        self, prompt: str, circuit_type: str = "general"
    ) -> str:
        """
        Generate circuit code with automatic validation and context.

        Args:
            prompt: User's circuit description
            circuit_type: Type of circuit for context (general, power, mcu, etc.)

        Returns:
            Validated circuit code with status report
        """

        logger.info(f"Generating validated circuit for: {prompt}")

        # Phase 1: Get relevant context
        context = get_circuit_design_context(circuit_type)
        logger.debug("Retrieved design context")

        # Phase 2: Generate initial circuit with context
        enhanced_prompt = f"""
{context}

Based on the above context and best practices, generate circuit code for:
{prompt}

Requirements:
- Use proper circuit_synth imports and patterns
- Follow the component and net naming conventions
- Include appropriate decoupling and protection
- Ensure all components are commonly available
"""

        # For now, generate a simple example circuit
        # This would integrate with the actual circuit-synth agent
        initial_code = self._generate_simple_example(prompt, circuit_type)
        logger.debug("Generated initial circuit code")

        # Phase 3: Validate and improve
        final_code, is_valid, status = validate_and_improve_circuit(initial_code)
        logger.info(f"Validation complete: {status}")

        # Phase 4: Create comprehensive response
        response = self._create_response(final_code, is_valid, status, prompt)

        return response

    def _generate_simple_example(self, prompt: str, circuit_type: str) -> str:
        """Generate a simple example circuit based on the prompt."""
        # This is a placeholder - would integrate with actual circuit-synth logic
        if any(keyword in prompt.lower() for keyword in ["led", "blink"]):
            return """from circuit_synth import Component, Net, circuit

@circuit
def led_circuit():
    VCC_3V3 = Net("VCC_3V3")
    GND = Net("GND")
    
    led = Component("Device:LED", "D")
    resistor = Component("Device:R", "R", value="330")
    
    VCC_3V3 += resistor[1]
    resistor[2] += led[1]
    GND += led[2]"""

        elif any(keyword in prompt.lower() for keyword in ["esp32", "microcontroller"]):
            return """from circuit_synth import Component, Net, circuit

@circuit
def esp32_circuit():
    VCC_3V3 = Net("VCC_3V3")
    GND = Net("GND")
    
    esp32 = Component("RF_Module:ESP32-S3-MINI-1", "U")
    cap = Component("Device:C", "C", value="100nF")
    
    VCC_3V3 += esp32["VDD"], cap[1]
    GND += esp32["GND"], cap[2]"""

        else:
            return """from circuit_synth import Component, Net, circuit

@circuit
def basic_circuit():
    VCC_3V3 = Net("VCC_3V3")
    GND = Net("GND")
    
    resistor = Component("Device:R", "R", value="1k")
    VCC_3V3 += resistor[1]
    GND += resistor[2]"""

    def _create_response(
        self, code: str, is_valid: bool, status: str, original_prompt: str
    ) -> str:
        """Create comprehensive response with code and status."""

        # Create header comment
        header = f"""# Circuit generated for: {original_prompt}
# Validation status: {"PASSED" if is_valid else "NEEDS ATTENTION"}
# {status}

"""

        # Add validation badge to code
        validation_badge = "# ✅ VALIDATED" if is_valid else "# ⚠️ VALIDATION ISSUES"

        return f"""{header}{validation_badge}

{code}

# Generation Summary:
# {status}
# Generated with Circuit-Synth Quality Assurance"""

    async def quick_validate(self, code: str) -> str:
        """Quick validation service for existing code."""

        final_code, is_valid, status = validate_and_improve_circuit(code)

        return f"""# Validation Results
{status}

{final_code}"""
