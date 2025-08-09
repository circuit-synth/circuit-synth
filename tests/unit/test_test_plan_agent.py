"""
Unit tests for the Test Plan Agent
"""

import json
from pathlib import Path

import pytest

from circuit_synth.ai_integration.claude.agents.test_plan_agent import (
    TestEquipment,
    TestPlanGenerator,
    TestPoint,
    TestProcedure,
    create_test_plan_from_circuit,
)


class TestTestPlanGenerator:
    """Test the TestPlanGenerator class"""

    def setup_method(self):
        """Set up test fixtures"""
        self.generator = TestPlanGenerator()

        # Sample circuit data
        self.simple_circuit = {
            "name": "TestCircuit",
            "components": [
                {
                    "ref": "U1",
                    "symbol": "MCU_ST_STM32F4:STM32F407VETx",
                    "value": "STM32F407VET6",
                },
                {"ref": "J1", "symbol": "Connector:USB_C_Receptacle", "value": "USB_C"},
                {
                    "ref": "U2",
                    "symbol": "Regulator_Linear:AMS1117-3.3",
                    "value": "AMS1117-3.3",
                },
            ],
            "nets": [
                {"name": "VCC_3V3", "connections": []},
                {"name": "GND", "connections": []},
                {"name": "USB_DP", "connections": []},
                {"name": "USB_DM", "connections": []},
            ],
        }

        # Hierarchical circuit data
        self.hierarchical_circuit = {
            "name": "MainBoard",
            "components": {},
            "nets": {},
            "subcircuits": [
                {
                    "name": "PowerSupply",
                    "components": {
                        "U1": {
                            "symbol": "Regulator_Linear:AMS1117-3.3",
                            "value": "3.3V",
                        }
                    },
                    "nets": {"VCC_3V3": {}, "GND": {}},
                },
                {
                    "name": "USBInterface",
                    "components": {
                        "J1": {"symbol": "Connector:USB_C_Receptacle", "value": "USB-C"}
                    },
                    "nets": {"VBUS": {}, "USB_DP": {}, "USB_DM": {}, "GND": {}},
                },
            ],
        }

    def test_equipment_database_initialization(self):
        """Test that equipment database is properly initialized"""
        assert "multimeter" in self.generator.equipment_db
        assert "oscilloscope" in self.generator.equipment_db
        assert "power_supply" in self.generator.equipment_db

        multimeter = self.generator.equipment_db["multimeter"]
        assert multimeter.name == "Digital Multimeter"
        assert multimeter.type == "multimeter"
        assert "voltage_range" in multimeter.specifications

    def test_analyze_circuit_simple(self):
        """Test circuit analysis with simple circuit"""
        analysis = self.generator.analyze_circuit(self.simple_circuit)

        # Check power rails detection
        assert len(analysis["power_rails"]) == 2
        rail_names = [r["name"] for r in analysis["power_rails"]]
        assert "VCC_3V3" in rail_names
        assert "GND" in rail_names

        # Check component type detection
        assert "microcontroller" in analysis["component_types"]
        assert "usb_interface" in analysis["component_types"]
        assert "power_regulator" in analysis["component_types"]

        # Check interface detection
        interfaces = analysis["interfaces"]
        assert any(i["type"] == "mcu" for i in interfaces)
        assert any(i["type"] == "usb" for i in interfaces)

    def test_analyze_circuit_hierarchical(self):
        """Test circuit analysis with hierarchical circuit"""
        analysis = self.generator.analyze_circuit(self.hierarchical_circuit)

        # Should find power rails in subcircuits
        rail_names = [r["name"] for r in analysis["power_rails"]]
        assert "PowerSupply/VCC_3V3" in rail_names or "VCC_3V3" in rail_names
        assert "PowerSupply/GND" in rail_names or "GND" in rail_names

        # Should find components in subcircuits
        assert "power_regulator" in analysis["component_types"]
        assert "usb_interface" in analysis["component_types"]

    def test_identify_test_points(self):
        """Test test point identification"""
        analysis = self.generator.analyze_circuit(self.simple_circuit)
        test_points = self.generator.identify_test_points(analysis)

        # Should create test points for power rails
        tp_names = [tp.net_name for tp in test_points]
        assert "VCC_3V3" in tp_names
        assert "GND" in tp_names

        # Should create test points for USB interface
        assert any(tp.net_name == "USB_DP" for tp in test_points)
        assert any(tp.net_name == "USB_DM" for tp in test_points)

        # Check test point properties
        vcc_tp = next(tp for tp in test_points if "VCC_3V3" in tp.net_name)
        assert vcc_tp.nominal_value == 3.3
        assert vcc_tp.tolerance_percent == 5.0
        assert vcc_tp.test_equipment == "multimeter"

    def test_generate_test_procedures(self):
        """Test test procedure generation"""
        analysis = self.generator.analyze_circuit(self.simple_circuit)
        test_points = self.generator.identify_test_points(analysis)
        procedures = self.generator.generate_test_procedures(
            analysis, test_points, ["functional", "safety"]
        )

        # Should generate procedures for requested categories
        categories = set(p.category for p in procedures)
        assert "functional" in categories
        assert "safety" in categories

        # Should have power-on test
        power_tests = [p for p in procedures if "power" in p.name.lower()]
        assert len(power_tests) > 0

        # Check procedure structure
        power_test = power_tests[0]
        assert power_test.test_id
        assert len(power_test.equipment) > 0
        assert len(power_test.steps) > 0
        assert len(power_test.pass_criteria) > 0

    def test_generate_markdown_report(self):
        """Test markdown report generation"""
        analysis = self.generator.analyze_circuit(self.simple_circuit)
        test_points = self.generator.identify_test_points(analysis)
        procedures = self.generator.generate_test_procedures(analysis, test_points)

        report = self.generator.generate_test_report(
            "TestCircuit", analysis, test_points, procedures, "markdown"
        )

        # Check report contains key sections
        assert "# Test Plan: TestCircuit" in report
        assert "## Executive Summary" in report
        assert "## Required Test Equipment" in report
        assert "## Test Points" in report
        assert "## Test Procedures" in report
        assert "## Test Execution Summary" in report
        assert "## Sign-off" in report

        # Check test points table
        assert "| ID | Net | Component | Signal Type |" in report
        assert "TP_VCC_3V3" in report
        assert "TP_GND" in report

    def test_generate_json_report(self):
        """Test JSON report generation"""
        analysis = self.generator.analyze_circuit(self.simple_circuit)
        test_points = self.generator.identify_test_points(analysis)
        procedures = self.generator.generate_test_procedures(analysis, test_points)

        report_str = self.generator.generate_test_report(
            "TestCircuit", analysis, test_points, procedures, "json"
        )

        # Should be valid JSON
        report = json.loads(report_str)

        # Check structure
        assert report["circuit_name"] == "TestCircuit"
        assert "summary" in report
        assert "test_points" in report
        assert "procedures" in report
        assert "equipment_required" in report

        # Check summary
        assert report["summary"]["total_test_points"] == len(test_points)
        assert report["summary"]["total_procedures"] == len(procedures)

        # Check test points
        assert len(report["test_points"]) == len(test_points)
        if len(report["test_points"]) > 0:
            tp = report["test_points"][0]
            assert "id" in tp
            assert "net_name" in tp
            assert "signal_type" in tp

    def test_get_nominal_voltage(self):
        """Test nominal voltage detection from net names"""
        test_cases = [
            ("VCC_3V3", 3.3),
            ("3V3", 3.3),
            ("3.3V", 3.3),
            ("VCC_5V", 5.0),
            ("5V", 5.0),
            ("12V", 12.0),
            ("VCC_1V8", 1.8),
            ("1.8V", 1.8),
            ("GND", 0.0),
            ("VSS", 0.0),
            ("UNKNOWN", None),
        ]

        for net_name, expected in test_cases:
            result = self.generator._get_nominal_voltage(net_name)
            assert (
                result == expected
            ), f"Failed for {net_name}: got {result}, expected {expected}"

    def test_esp32_detection(self):
        """Test ESP32 microcontroller detection"""
        esp32_circuit = {
            "components": [
                {
                    "ref": "U1",
                    "symbol": "RF_Module:ESP32-C6-MINI-1",
                    "value": "ESP32-C6",
                }
            ],
            "nets": [],
        }

        analysis = self.generator.analyze_circuit(esp32_circuit)
        assert "microcontroller" in analysis["component_types"]

        # Also test value-based detection
        esp32_circuit2 = {
            "components": [
                {"ref": "U1", "symbol": "SomeOtherSymbol", "value": "ESP32-C6-WROOM"}
            ],
            "nets": [],
        }

        analysis2 = self.generator.analyze_circuit(esp32_circuit2)
        assert "microcontroller" in analysis2["component_types"]


class TestDataClasses:
    """Test the data classes"""

    def test_test_equipment(self):
        """Test TestEquipment dataclass"""
        equipment = TestEquipment(
            name="Test Scope",
            type="oscilloscope",
            specifications={"bandwidth": "100MHz"},
            required=True,
            alternatives=["Rigol", "Keysight"],
        )

        assert equipment.name == "Test Scope"
        assert equipment.type == "oscilloscope"
        assert equipment.specifications["bandwidth"] == "100MHz"
        assert equipment.required is True
        assert len(equipment.alternatives) == 2

    def test_test_procedure(self):
        """Test TestProcedure dataclass"""
        procedure = TestProcedure(
            test_id="TEST-001",
            name="Power Test",
            category="functional",
            description="Test power supply",
            equipment=["multimeter"],
            setup=["Connect power"],
            steps=["Measure voltage"],
            measurements=[{"param": "VCC", "value": 3.3}],
            pass_criteria={"voltage_ok": True},
            fail_actions=["Check connections"],
        )

        assert procedure.test_id == "TEST-001"
        assert procedure.category == "functional"
        assert procedure.duration_minutes == 5  # Default value
        assert len(procedure.safety_warnings) == 0  # Default empty list

    def test_test_point(self):
        """Test TestPoint dataclass"""
        test_point = TestPoint(
            id="TP1",
            net_name="VCC_3V3",
            component_ref="U1",
            pin="14",
            signal_type="power",
            nominal_value=3.3,
            tolerance_percent=5.0,
            test_equipment="multimeter",
            accessibility="probe_point",
        )

        assert test_point.id == "TP1"
        assert test_point.net_name == "VCC_3V3"
        assert test_point.nominal_value == 3.3
        assert test_point.tolerance_percent == 5.0


class TestIntegration:
    """Integration tests"""

    def test_create_test_plan_from_circuit(self, tmp_path):
        """Test the main entry point function"""
        # Create a test circuit JSON file
        circuit_data = {
            "name": "TestBoard",
            "components": [
                {
                    "ref": "U1",
                    "symbol": "MCU_ST_STM32F4:STM32F407VETx",
                    "value": "STM32F407",
                }
            ],
            "nets": [{"name": "VCC_3V3"}, {"name": "GND"}],
        }

        circuit_file = tmp_path / "test_circuit.json"
        with open(circuit_file, "w") as f:
            json.dump(circuit_data, f)

        # Generate markdown test plan
        markdown_plan = create_test_plan_from_circuit(
            str(circuit_file), output_format="markdown", test_categories=["functional"]
        )

        assert "# Test Plan: test_circuit" in markdown_plan
        assert "functional" in markdown_plan.lower()

        # Generate JSON test plan
        json_plan = create_test_plan_from_circuit(
            str(circuit_file), output_format="json", test_categories=["safety"]
        )

        plan_data = json.loads(json_plan)
        assert plan_data["circuit_name"] == "test_circuit"
        assert any(p["category"] == "safety" for p in plan_data["procedures"])

    def test_python_file_handling(self):
        """Test handling of Python circuit files"""
        # Currently not implemented, should return error message
        result = create_test_plan_from_circuit(
            "test_circuit.py", output_format="markdown"
        )

        assert "not implemented" in result.lower()


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
