"""
Unit tests for circuit debugging functionality
"""

import json
import tempfile
from datetime import datetime
from pathlib import Path

import pytest

from circuit_synth.debugging import (
    CircuitDebugger,
    ComponentFailure,
    DebugCategory,
    DebugKnowledgeBase,
    DebugPattern,
    DebugSession,
    IssueSeverity,
    MeasurementType,
    SymptomAnalyzer,
    TestEquipment,
    TestGuidance,
    TestMeasurement,
    TestStep,
    TroubleshootingTree,
)
from circuit_synth.debugging.symptoms import OscilloscopeTrace


class TestCircuitDebugger:
    """Test CircuitDebugger class"""

    def test_start_session(self):
        """Test starting a debug session"""
        debugger = CircuitDebugger()
        session = debugger.start_session("test_board", "1.0")

        assert session.board_name == "test_board"
        assert session.board_version == "1.0"
        assert session.session_id is not None
        assert len(debugger.active_sessions) == 1

    def test_analyze_power_issue(self):
        """Test power issue analysis"""
        debugger = CircuitDebugger()
        session = debugger.start_session("test_board")

        # Add power-related symptoms
        session.add_symptom("Board not turning on")
        session.add_measurement("3.3V_rail", 2.5, "V")

        issues = debugger.analyze_power_issue(session)

        assert len(issues) > 0
        assert any(issue.category == DebugCategory.POWER for issue in issues)
        # Check that we found power-related issues
        assert any(
            issue.severity == IssueSeverity.CRITICAL
            or issue.severity == IssueSeverity.HIGH
            for issue in issues
        )

    def test_analyze_digital_communication(self):
        """Test digital communication analysis"""
        debugger = CircuitDebugger()
        session = debugger.start_session("test_board")

        # Add I2C symptoms
        session.add_symptom("I2C devices not responding")
        session.add_symptom("No ACK from sensor")

        issues = debugger.analyze_digital_communication(session)

        assert len(issues) > 0
        assert any(issue.category == DebugCategory.DIGITAL for issue in issues)
        assert any("I2C" in issue.title for issue in issues)

    def test_close_session(self):
        """Test closing a debug session"""
        with tempfile.TemporaryDirectory() as tmpdir:
            kb_path = Path(tmpdir) / "debug_kb"
            debugger = CircuitDebugger(knowledge_base_path=kb_path)

            session = debugger.start_session("test_board")
            session.add_symptom("Test symptom")

            debugger.close_session(
                session, "Fixed resistor value", "Wrong resistor installed"
            )

            assert session.resolution == "Fixed resistor value"
            assert session.root_cause == "Wrong resistor installed"
            assert session.ended_at is not None
            assert len(debugger.active_sessions) == 0


class TestDebugSession:
    """Test DebugSession class"""

    def test_add_symptom(self):
        """Test adding symptoms"""
        session = DebugSession(
            session_id="test",
            board_name="test_board",
            board_version="1.0",
            started_at=datetime.now(),
        )

        session.add_symptom("LED not lighting")
        session.add_symptom("No voltage on pin")

        assert len(session.symptoms) == 2
        assert "LED not lighting" in session.symptoms

    def test_add_measurement(self):
        """Test adding measurements"""
        session = DebugSession(
            session_id="test",
            board_name="test_board",
            board_version="1.0",
            started_at=datetime.now(),
        )

        session.add_measurement("VCC", 3.3, "V", "Measured at U1 pin 1")
        session.add_measurement("Current", 150, "mA")

        assert len(session.measurements) == 2
        assert session.measurements["VCC"]["value"] == 3.3
        assert session.measurements["VCC"]["unit"] == "V"

    def test_to_dict(self):
        """Test session serialization"""
        session = DebugSession(
            session_id="test",
            board_name="test_board",
            board_version="1.0",
            started_at=datetime.now(),
        )

        session.add_symptom("Test symptom")
        session.add_measurement("Test", 1.0)

        data = session.to_dict()

        assert data["session_id"] == "test"
        assert data["board_name"] == "test_board"
        assert len(data["symptoms"]) == 1
        assert len(data["measurements"]) == 1


class TestSymptomAnalyzer:
    """Test SymptomAnalyzer class"""

    def test_categorize_symptoms(self):
        """Test symptom categorization"""
        analyzer = SymptomAnalyzer()

        symptoms = [
            "Board not turning on",
            "I2C communication failing",
            "USB not detected",
            "Regulator overheating",
            "Connector loose",
        ]

        categories = analyzer.categorize_symptoms(symptoms)

        assert "power" in categories
        assert "digital" in categories
        assert "thermal" in categories
        assert "mechanical" in categories

    def test_analyze_voltage_measurement(self):
        """Test voltage measurement analysis"""
        analyzer = SymptomAnalyzer()

        measurement = TestMeasurement(
            measurement_type=MeasurementType.VOLTAGE_DC,
            value=2.0,  # Changed to be significantly off
            unit="V",
            test_point="3.3V_rail",
            expected_value=3.3,
            tolerance=0.05,
        )

        analysis = analyzer.analyze_voltage_measurement(measurement)

        assert analysis["status"] == "failed"
        assert len(analysis["issues"]) > 0
        assert len(analysis["recommendations"]) > 0

    def test_analyze_i2c_signals(self):
        """Test I2C signal analysis"""
        analyzer = SymptomAnalyzer()

        # Create mock I2C traces
        sda_trace = OscilloscopeTrace(
            channel="CH1",
            time_data=[0, 1, 2, 3, 4],
            voltage_data=[0, 3.3, 0, 3.3, 0],
            timebase="1us/div",
            vertical_scale="1V/div",
            trigger_level=1.5,
            trigger_source="CH1",
        )

        scl_trace = OscilloscopeTrace(
            channel="CH2",
            time_data=[0, 1, 2, 3, 4],
            voltage_data=[3.3, 3.3, 0, 0, 3.3],
            timebase="1us/div",
            vertical_scale="1V/div",
            trigger_level=1.5,
            trigger_source="CH2",
        )

        analysis = analyzer.analyze_i2c_signals(sda_trace, scl_trace)

        assert "bus_health" in analysis
        assert "measurements" in analysis
        assert "sda_high" in analysis["measurements"]


class TestDebugKnowledgeBase:
    """Test DebugKnowledgeBase class"""

    def test_add_and_search_pattern(self):
        """Test adding and searching patterns"""
        with tempfile.TemporaryDirectory() as tmpdir:
            kb = DebugKnowledgeBase(db_path=Path(tmpdir) / "test.db")

            pattern = DebugPattern(
                pattern_id="test_pattern",
                category="power",
                symptoms=["No power", "Board dead"],
                root_cause="Blown fuse",
                solutions=["Replace fuse", "Check input voltage"],
                component_types=["Fuse"],
                occurrence_count=1,
                success_rate=0.9,
            )

            assert kb.add_pattern(pattern)

            # Search for pattern
            results = kb.search_patterns(["Board dead"])
            assert len(results) > 0
            assert results[0][0].pattern_id == "test_pattern"

    def test_component_failures(self):
        """Test component failure tracking"""
        with tempfile.TemporaryDirectory() as tmpdir:
            kb = DebugKnowledgeBase(db_path=Path(tmpdir) / "test.db")

            failure = ComponentFailure(
                component_type="AMS1117-3.3",
                manufacturer="AMS",
                failure_mode="Thermal shutdown",
                failure_rate=50.0,
                symptoms=["Output drops to 0V", "Regulator very hot"],
                root_causes=["Overcurrent", "Inadequate cooling"],
                environmental_factors=["High ambient temperature"],
                mitigation=["Add heatsink", "Reduce load current"],
            )

            assert kb.add_component_failure(failure)

            # Search for failures
            failures = kb.get_component_failures("AMS1117")
            assert len(failures) > 0
            assert failures[0].failure_mode == "Thermal shutdown"

    def test_record_debug_session(self):
        """Test recording debug session"""
        with tempfile.TemporaryDirectory() as tmpdir:
            kb = DebugKnowledgeBase(db_path=Path(tmpdir) / "test.db")

            session_data = {
                "session_id": "test_session",
                "board_name": "test_board",
                "board_version": "1.0",
                "symptoms": ["No power"],
                "measurements": {"VCC": 0},
                "root_cause": "Blown fuse",
                "resolution": "Replaced fuse",
                "duration_minutes": 30,
                "success": True,
            }

            assert kb.record_debug_session(session_data)

            # Search for similar sessions
            similar = kb.get_similar_sessions("test_board", ["No power"])
            assert len(similar) > 0


class TestTestGuidance:
    """Test TestGuidance class"""

    def test_create_power_troubleshooting_tree(self):
        """Test power troubleshooting tree generation"""
        tree = TestGuidance.create_power_troubleshooting_tree()

        assert tree.title == "Power Supply Troubleshooting"
        assert tree.initial_step == "step_1"
        assert len(tree.steps) > 0
        assert TestEquipment.MULTIMETER in tree.equipment_list

        # Test step navigation
        step1 = tree.get_step("step_1")
        assert step1 is not None
        assert "Check Input Power" in step1.description

    def test_create_i2c_troubleshooting_tree(self):
        """Test I2C troubleshooting tree generation"""
        tree = TestGuidance.create_i2c_troubleshooting_tree()

        assert tree.title == "I2C Communication Troubleshooting"
        assert len(tree.steps) > 0
        assert TestEquipment.OSCILLOSCOPE in tree.equipment_list

    def test_troubleshooting_tree_to_markdown(self):
        """Test markdown generation from tree"""
        tree = TestGuidance.create_power_troubleshooting_tree()
        markdown = tree.to_markdown()

        assert "# Power Supply Troubleshooting" in markdown
        assert "## Required Equipment" in markdown
        assert "## Step 1:" in markdown

    def test_troubleshooting_tree_to_mermaid(self):
        """Test Mermaid diagram generation"""
        tree = TestGuidance.create_power_troubleshooting_tree()
        mermaid = tree.to_mermaid()

        assert "```mermaid" in mermaid
        assert "graph TD" in mermaid
        assert "step_1" in mermaid


class TestTestMeasurement:
    """Test TestMeasurement class"""

    def test_measurement_evaluation(self):
        """Test measurement pass/fail evaluation"""
        measurement = TestMeasurement(
            measurement_type=MeasurementType.VOLTAGE_DC,
            value=3.25,
            unit="V",
            test_point="VCC",
            expected_value=3.3,
            tolerance=0.05,  # 5%
        )

        assert measurement.evaluate() == True
        assert measurement.pass_fail == True

        # Test failing measurement
        measurement.value = 2.5
        assert measurement.evaluate() == False
        assert measurement.pass_fail == False


class TestOscilloscopeTrace:
    """Test OscilloscopeTrace class"""

    def test_waveform_analysis(self):
        """Test waveform analysis"""
        import numpy as np

        # Create a simple square wave
        t = np.linspace(0, 0.001, 100)  # 1ms, 100 points
        v = np.where(np.sin(2 * np.pi * 1000 * t) > 0, 3.3, 0)  # 1kHz square wave

        trace = OscilloscopeTrace(
            channel="CH1",
            time_data=t.tolist(),
            voltage_data=v.tolist(),
            timebase="100us/div",
            vertical_scale="1V/div",
            trigger_level=1.65,
            trigger_source="CH1",
        )

        analysis = trace.analyze_waveform()

        assert "min_voltage" in analysis
        assert "max_voltage" in analysis
        assert "peak_to_peak" in analysis
        assert analysis["min_voltage"] < 0.5
        assert analysis["max_voltage"] > 3.0
        assert analysis["peak_to_peak"] > 3.0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
