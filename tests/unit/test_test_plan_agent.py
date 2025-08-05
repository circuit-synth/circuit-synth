"""
Unit tests for the Test Plan Creation Agent
"""

import pytest
from unittest.mock import Mock, patch

from circuit_synth.claude_integration.agents.test_plan_agent import (
    TestPlanCreatorAgent,
    CircuitTestPoint,
    CircuitTestProcedure
)


class TestTestPlanCreatorAgent:
    """Test suite for TestPlanCreatorAgent"""
    
    def test_agent_initialization(self):
        """Test agent initializes with correct properties"""
        agent = TestPlanCreatorAgent()
        
        assert agent.name == "test-plan-creator"
        assert agent.description == "Circuit test plan generation and validation specialist"
        assert agent.version == "1.0.0"
        assert agent.expertise_area == "Test Plan Creation & Circuit Validation"
        
    def test_agent_capabilities(self):
        """Test agent reports correct capabilities"""
        agent = TestPlanCreatorAgent()
        capabilities = agent.get_capabilities()
        
        expected_capabilities = [
            "test_plan_generation",
            "test_point_identification",
            "performance_test_design",
            "safety_test_procedures",
            "manufacturing_test_creation",
            "equipment_recommendations",
            "pass_fail_criteria_definition",
            "test_coverage_analysis",
            "validation_checklist_creation",
            "integration_test_planning"
        ]
        
        assert capabilities == expected_capabilities
        
    def test_system_prompt_content(self):
        """Test system prompt contains key information"""
        agent = TestPlanCreatorAgent()
        prompt = agent.get_system_prompt()
        
        # Check for key sections in the prompt
        assert "test plan creation agent" in prompt
        assert "Functional Testing" in prompt
        assert "Performance Testing" in prompt
        assert "Safety and Compliance" in prompt
        assert "Manufacturing Testing" in prompt
        assert "Equipment Recommendations" in prompt
        
    def test_tool_definitions(self):
        """Test agent defines correct tools"""
        agent = TestPlanCreatorAgent()
        tools = agent.get_tools()
        
        expected_tools = [
            "analyze_circuit",
            "generate_test_procedure", 
            "recommend_equipment",
            "create_validation_checklist",
            "export_test_plan"
        ]
        
        assert list(tools.keys()) == expected_tools
        
        # Check tool parameters
        assert "circuit_file" in tools["analyze_circuit"]["parameters"]
        assert "test_type" in tools["generate_test_procedure"]["parameters"]
        assert "measurement_type" in tools["recommend_equipment"]["parameters"]
        
    def test_analyze_circuit_tool(self):
        """Test circuit analysis tool execution"""
        agent = TestPlanCreatorAgent()
        
        result = agent.execute_tool(
            "analyze_circuit",
            {"circuit_file": "test_circuit.py", "analysis_type": "test_points"}
        )
        
        assert result["circuit_file"] == "test_circuit.py"
        assert result["analysis_type"] == "test_points"
        assert "analysis_info" in result
        assert "suggestion" in result
        
    def test_generate_test_procedure_tool(self):
        """Test test procedure generation tool"""
        agent = TestPlanCreatorAgent()
        
        result = agent.execute_tool(
            "generate_test_procedure",
            {"test_type": "functional", "circuit_info": {"name": "ESP32 Board"}}
        )
        
        assert result["test_type"] == "functional"
        assert "procedure_template" in result
        assert result["procedure_template"]["name"] == "Functional Test Procedure"
        assert "Power-on sequence verification" in result["procedure_template"]["sections"]
        
    def test_recommend_equipment_tool(self):
        """Test equipment recommendation tool"""
        agent = TestPlanCreatorAgent()
        
        result = agent.execute_tool(
            "recommend_equipment",
            {"measurement_type": "voltage", "specifications": {"range": "0-5V"}}
        )
        
        assert result["measurement_type"] == "voltage"
        assert "recommended_equipment" in result
        assert "basic" in result["recommended_equipment"]
        
    def test_create_validation_checklist_tool(self):
        """Test validation checklist creation"""
        agent = TestPlanCreatorAgent()
        
        result = agent.execute_tool(
            "create_validation_checklist",
            {"circuit_type": "power", "requirements": ["Output stable"]}
        )
        
        assert result["circuit_type"] == "power"
        assert "base_checklist" in result
        assert len(result["base_checklist"]) > 0
        assert "Input voltage range verified" in result["base_checklist"]
        
    def test_export_test_plan_tool(self):
        """Test test plan export functionality"""
        agent = TestPlanCreatorAgent()
        
        test_procedures = [
            {"name": "Power Test", "steps": ["Apply power", "Measure voltage"]},
            {"name": "Function Test", "steps": ["Test GPIO", "Test comms"]}
        ]
        
        result = agent.execute_tool(
            "export_test_plan",
            {"format": "markdown", "test_procedures": test_procedures}
        )
        
        assert result["format"] == "markdown"
        assert result["procedures_count"] == 2
        assert result["format_info"]["extension"] == ".md"
        
    def test_unknown_tool_handling(self):
        """Test handling of unknown tool requests"""
        agent = TestPlanCreatorAgent()
        
        result = agent.execute_tool("unknown_tool", {})
        
        assert "error" in result
        assert "Unknown tool" in result["error"]
        
    def test_metadata(self):
        """Test agent metadata generation"""
        agent = TestPlanCreatorAgent()
        metadata = agent.get_metadata()
        
        assert metadata["name"] == "test-plan-creator"
        assert metadata["version"] == "1.0.0"
        assert metadata["priority"] == "medium"
        assert metadata["usage_context"] == "test_plan_creation"
        assert len(metadata["capabilities"]) == 10
        assert len(metadata["output_formats"]) == 4
        
    def test_test_point_dataclass(self):
        """Test CircuitTestPoint dataclass functionality"""
        test_point = CircuitTestPoint(
            net_name="VCC_3V3",
            position=(10.5, 20.3),
            expected_value="3.3V",
            test_type="voltage",
            tolerance="±5%"
        )
        
        assert test_point.net_name == "VCC_3V3"
        assert test_point.position == (10.5, 20.3)
        assert test_point.expected_value == "3.3V"
        assert test_point.test_type == "voltage"
        assert test_point.tolerance == "±5%"
        
    def test_test_procedure_dataclass(self):
        """Test CircuitTestProcedure dataclass functionality"""
        test_points = [
            CircuitTestPoint("VCC", (0, 0), "5V"),
            CircuitTestPoint("GND", (0, 10), "0V")
        ]
        
        procedure = CircuitTestProcedure(
            name="Power Test",
            category="functional",
            test_points=test_points,
            equipment=["Multimeter", "Power Supply"],
            steps=["Apply power", "Measure voltages"],
            pass_criteria=["All voltages within spec"],
            fail_criteria=["Any voltage out of spec"],
            notes="Check power-on sequence"
        )
        
        assert procedure.name == "Power Test"
        assert procedure.category == "functional"
        assert len(procedure.test_points) == 2
        assert len(procedure.equipment) == 2
        assert procedure.notes == "Check power-on sequence"