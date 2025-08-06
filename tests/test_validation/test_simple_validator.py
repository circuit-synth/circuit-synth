"""
Test suite for simple circuit validator.

Tests both validation logic and context generation functionality.
"""

import pytest

from circuit_synth.ai_integration.validation import (
    get_circuit_design_context,
    validate_and_improve_circuit,
)


class TestCircuitValidation:
    """Test circuit validation functionality."""

    def test_valid_circuit_passes(self):
        """Test that valid circuit code passes validation."""
        valid_code = """
from circuit_synth import Component, Net, circuit

@circuit
def simple_circuit():
    VCC = Net("VCC")
    GND = Net("GND")
    
    resistor = Component("Device:R", "R", value="1k")
    VCC += resistor[1]
    GND += resistor[2]
"""

        result_code, is_valid, status = validate_and_improve_circuit(valid_code)
        assert is_valid
        assert "✅" in status

    def test_syntax_error_detected(self):
        """Test that syntax errors are caught."""
        invalid_code = """
from circuit_synth import Component
# Missing closing parenthesis
resistor = Component("Device:R", "R"
"""

        result_code, is_valid, status = validate_and_improve_circuit(invalid_code)
        assert not is_valid
        assert "issues after" in status  # Check for our standard failure message format

    def test_missing_import_fixed(self):
        """Test that missing imports are automatically fixed."""
        code_without_import = """
@circuit
def simple_circuit():
    resistor = Component("Device:R", "R")
"""

        result_code, is_valid, status = validate_and_improve_circuit(
            code_without_import
        )
        assert "from circuit_synth import" in result_code

    def test_context_generation(self):
        """Test context generation for different circuit types."""

        # Test general context
        general_context = get_circuit_design_context("general")
        assert "from circuit_synth import" in general_context
        assert "Best Practices" in general_context

        # Test power supply context
        power_context = get_circuit_design_context("power")
        assert "Power Supply Design" in power_context
        assert "AMS1117" in power_context

        # Test microcontroller context
        mcu_context = get_circuit_design_context("mcu")
        assert "Microcontroller Design" in mcu_context
        assert "crystal" in mcu_context.lower()


class TestValidatedCircuitGenerator:
    """Test the integrated circuit generator."""

    def test_generator_integration(self):
        """Test that the generator integrates validation properly."""
        # This would test the full integration
        # Implementation depends on how we mock the base agent
        # For now, just verify the validation functions are importable and callable

        # Test that we can import and call the validation functions
        from circuit_synth.ai_integration.validation import (
            get_circuit_design_context,
            validate_and_improve_circuit,
        )

        # Test basic functionality
        simple_code = """
from circuit_synth import Component
resistor = Component("Device:R", "R")
"""
        result_code, is_valid, status = validate_and_improve_circuit(simple_code)
        assert isinstance(result_code, str)
        assert isinstance(is_valid, bool)
        assert isinstance(status, str)

        # Test context generation
        context = get_circuit_design_context("general")
        assert isinstance(context, str)
        assert len(context) > 0
