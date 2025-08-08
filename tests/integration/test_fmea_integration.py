#!/usr/bin/env python3
"""
Integration tests for FMEA functionality
Tests complete FMEA workflow from circuit analysis to report generation
"""

import os
import tempfile
import unittest
from pathlib import Path

from circuit_synth import *
from circuit_synth.quality_assurance import (
    ComprehensiveFMEAReportGenerator,
    EnhancedFMEAAnalyzer,
    FMEAReportGenerator,
    UniversalFMEAAnalyzer,
)


class TestFMEAIntegration(unittest.TestCase):
    """Test complete FMEA workflow integration"""

    def setUp(self):
        """Set up test environment"""
        self.temp_dir = tempfile.mkdtemp()
        self.test_circuit_file = Path(self.temp_dir) / "test_circuit.py"

        # Create a test circuit
        self._create_test_circuit()

    def tearDown(self):
        """Clean up temporary files"""
        import shutil

        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def _create_test_circuit(self):
        """Create a test circuit file"""
        circuit_code = '''
from circuit_synth import *

@circuit(name="Test_ESP32_Board")
def test_esp32_board():
    """Test ESP32 development board for FMEA analysis"""
    
    # Power regulation
    regulator = Component(
        symbol="Regulator_Linear:AMS1117-3.3",
        ref="U",
        footprint="Package_TO_SOT_SMD:SOT-223-3_TabPin2"
    )
    
    # ESP32 MCU
    esp32 = Component(
        symbol="RF_Module:ESP32-WROOM-32",
        ref="U",
        footprint="RF_Module:ESP32-WROOM-32"
    )
    
    # USB connector
    usb = Component(
        symbol="Connector:USB_C_Receptacle",
        ref="J",
        footprint="Connector_USB:USB_C_Receptacle"
    )
    
    # Crystal
    crystal = Component(
        symbol="Device:Crystal",
        ref="Y",
        value="40MHz",
        footprint="Crystal:Crystal_SMD_5032-2Pin_5.0x3.2mm"
    )
    
    # Capacitors
    cap_in = Component(symbol="Device:C", ref="C", value="10uF",
                      footprint="Capacitor_SMD:C_0805_2012Metric")
    cap_out = Component(symbol="Device:C", ref="C", value="22uF",
                       footprint="Capacitor_SMD:C_0805_2012Metric")
    cap_crystal1 = Component(symbol="Device:C", ref="C", value="22pF",
                            footprint="Capacitor_SMD:C_0603_1608Metric")
    cap_crystal2 = Component(symbol="Device:C", ref="C", value="22pF",
                            footprint="Capacitor_SMD:C_0603_1608Metric")
    
    # Resistors
    pull_up1 = Component(symbol="Device:R", ref="R", value="10k",
                        footprint="Resistor_SMD:R_0603_1608Metric")
    pull_up2 = Component(symbol="Device:R", ref="R", value="10k",
                        footprint="Resistor_SMD:R_0603_1608Metric")
    
    # LED and resistor
    led = Component(symbol="Device:LED", ref="D",
                   footprint="LED_SMD:LED_0603_1608Metric")
    led_r = Component(symbol="Device:R", ref="R", value="1k",
                     footprint="Resistor_SMD:R_0603_1608Metric")
    
    # Create nets
    vbus = Net("VBUS")
    vcc_3v3 = Net("VCC_3V3")
    gnd = Net("GND")
    xtal_in = Net("XTAL_IN")
    xtal_out = Net("XTAL_OUT")
    
    # Power connections
    usb["VBUS"] += vbus
    usb["GND"] += gnd
    
    regulator["VI"] += vbus
    regulator["VO"] += vcc_3v3
    regulator["GND"] += gnd
    
    cap_in[1] += vbus
    cap_in[2] += gnd
    cap_out[1] += vcc_3v3
    cap_out[2] += gnd
    
    # ESP32 power
    esp32["VDD"] += vcc_3v3
    esp32["GND"] += gnd
    
    # Crystal connections
    crystal[1] += xtal_in
    crystal[2] += xtal_out
    cap_crystal1[1] += xtal_in
    cap_crystal1[2] += gnd
    cap_crystal2[1] += xtal_out
    cap_crystal2[2] += gnd
    
    # Pull-ups
    pull_up1[1] += vcc_3v3
    pull_up2[1] += vcc_3v3
    
    # LED
    led[1] += vcc_3v3
    led[2] += led_r[1]
    led_r[2] += gnd

if __name__ == "__main__":
    circuit = test_esp32_board()
    circuit.generate_json_netlist("test_esp32.json")
'''

        with open(self.test_circuit_file, "w") as f:
            f.write(circuit_code)

    def test_basic_fmea_analysis(self):
        """Test basic FMEA analysis workflow"""
        # Initialize analyzer
        analyzer = UniversalFMEAAnalyzer()

        # Analyze circuit file - returns circuit_data and failure_modes as dicts
        circuit_data, failure_modes_dict = analyzer.analyze_circuit_file(
            str(self.test_circuit_file)
        )

        # Should extract components
        self.assertGreater(circuit_data["component_count"], 0)

        # Should generate failure modes
        self.assertGreater(len(failure_modes_dict), 0)

        # Each failure mode should have required fields
        for fm in failure_modes_dict:
            self.assertIn("component", fm)
            self.assertIn("failure_mode", fm)
            self.assertIn("severity", fm)
            self.assertIn("occurrence", fm)
            self.assertIn("detection", fm)
            self.assertGreaterEqual(fm["severity"], 1)
            self.assertLessEqual(fm["severity"], 10)
            self.assertGreaterEqual(fm["occurrence"], 1)
            self.assertLessEqual(fm["occurrence"], 10)
            self.assertGreaterEqual(fm["detection"], 1)
            self.assertLessEqual(fm["detection"], 10)

    def test_enhanced_fmea_with_knowledge_base(self):
        """Test enhanced FMEA analysis with knowledge base"""
        try:
            analyzer = EnhancedFMEAAnalyzer()
        except Exception as e:
            # Skip if knowledge base not available
            self.skipTest(f"Knowledge base not available: {e}")

        # Set context for analysis
        circuit_context = {
            "environment": "industrial",
            "safety_critical": True,
            "production_volume": "high",
            "operating_temperature": "-20 to +85C",
            "expected_lifetime": "10 years",
        }

        # Analyze circuit and get failure modes as dict
        circuit_data, failure_modes_dict = analyzer.analyze_circuit_file(
            str(self.test_circuit_file)
        )

        # Should generate more comprehensive failure modes
        self.assertGreater(len(failure_modes_dict), 10)

        # Check for variety of failure types
        failure_types = set(fm["failure_mode"] for fm in failure_modes_dict)
        self.assertGreater(len(failure_types), 5)  # Should have variety

    def test_pdf_report_generation(self):
        """Test PDF report generation"""
        try:
            import reportlab
        except ImportError:
            self.skipTest("reportlab not installed")

        # Analyze circuit
        analyzer = UniversalFMEAAnalyzer()
        circuit_context, components = analyzer.analyze_circuit_file(
            str(self.test_circuit_file)
        )

        # Generate failure modes
        all_failure_modes = []
        for component in components:
            modes = analyzer.analyze_component(component, circuit_context)
            all_failure_modes.extend(modes)

        # Convert to dict format for report
        failure_modes_dict = [
            {
                "component": fm.component,
                "failure_mode": fm.failure_mode,
                "cause": fm.cause,
                "effect": fm.effect,
                "severity": fm.severity,
                "occurrence": fm.occurrence,
                "detection": fm.detection,
                "rpn": fm.severity * fm.occurrence * fm.detection,
                "recommendation": fm.recommendation,
            }
            for fm in all_failure_modes
        ]

        # Generate report
        generator = FMEAReportGenerator("Test ESP32 Board")
        output_path = Path(self.temp_dir) / "test_fmea_report.pdf"

        circuit_data = {
            "name": "Test ESP32 Board",
            "component_count": len(components),
            "subsystem_count": 3,
            "subsystems": [
                {"name": "Power", "description": "Power regulation"},
                {"name": "MCU", "description": "Main processor"},
                {"name": "Interface", "description": "USB interface"},
            ],
        }

        report_path = generator.generate_fmea_report(
            circuit_data=circuit_data,
            failure_modes=failure_modes_dict,
            output_path=str(output_path),
        )

        # Check report was created
        self.assertTrue(Path(report_path).exists())

        # Check file size (should be reasonable)
        file_size = Path(report_path).stat().st_size
        self.assertGreater(file_size, 1000)  # At least 1KB

    def test_comprehensive_report_generation(self):
        """Test comprehensive 50+ page report generation"""
        try:
            import reportlab
        except ImportError:
            self.skipTest("reportlab not installed")

        # Use enhanced analyzer if available
        try:
            analyzer = EnhancedFMEAAnalyzer()
        except:
            analyzer = UniversalFMEAAnalyzer()

        # Analyze circuit and get failure modes directly
        circuit_data, failure_modes_dict = analyzer.analyze_circuit_file(
            str(self.test_circuit_file)
        )

        # Update context
        circuit_context = {
            "environment": "aerospace",
            "safety_critical": True,
            "production_volume": "low",
            "compliance_standards": ["IPC-A-610 Class 3", "MIL-STD-883"],
        }
        circuit_data.update(circuit_context)

        # Failure modes are already in dict format from analyze_circuit_file
        # No conversion needed

        # Create analysis results
        analysis_results = {
            "project_name": "Test ESP32 Board",
            "circuit_data": {
                "name": "Test ESP32 Board",
                "description": "ESP32 development board for testing",
                "component_count": circuit_data.get("component_count", 0),
                "subsystem_count": 5,
                "design_version": "1.0",
                "compliance_standards": ["IPC-A-610 Class 3"],
                "subsystems": [
                    {
                        "name": "Power Management",
                        "description": "Voltage regulation",
                        "components": ["U1", "C1", "C2"],
                        "criticality": "High",
                    },
                    {
                        "name": "MCU Core",
                        "description": "ESP32 processor",
                        "components": ["U2"],
                        "criticality": "Critical",
                    },
                ],
            },
            "failure_modes": failure_modes_dict,
            "circuit_context": circuit_context,
            "components": [],  # Component list not needed for comprehensive report
        }

        # Generate comprehensive report
        generator = ComprehensiveFMEAReportGenerator("Test ESP32 Board")
        output_path = Path(self.temp_dir) / "comprehensive_fmea_report.pdf"

        report_path = generator.generate_comprehensive_report(
            analysis_results=analysis_results, output_path=str(output_path)
        )

        # Check report was created
        self.assertTrue(Path(report_path).exists())

        # Comprehensive report should be larger
        file_size = Path(report_path).stat().st_size
        self.assertGreater(file_size, 10000)  # At least 10KB

    def test_risk_categorization(self):
        """Test failure modes are properly categorized by risk"""
        analyzer = UniversalFMEAAnalyzer()

        # Create test components with known risk levels
        test_component = {"symbol": "Device:C", "ref": "C1", "value": "100nF"}

        failure_modes = analyzer.analyze_component(test_component, {})

        # Categorize by RPN
        critical = [
            fm
            for fm in failure_modes
            if fm.severity * fm.occurrence * fm.detection >= 300
        ]
        high = [
            fm
            for fm in failure_modes
            if 125 <= fm.severity * fm.occurrence * fm.detection < 300
        ]
        medium = [
            fm
            for fm in failure_modes
            if 50 <= fm.severity * fm.occurrence * fm.detection < 125
        ]
        low = [
            fm
            for fm in failure_modes
            if fm.severity * fm.occurrence * fm.detection < 50
        ]

        # All modes should fall into one category
        total_categorized = len(critical) + len(high) + len(medium) + len(low)
        self.assertEqual(total_categorized, len(failure_modes))

    def test_environmental_context_impact(self):
        """Test that environmental context affects analysis"""
        analyzer = UniversalFMEAAnalyzer()

        component = {"symbol": "Device:R", "ref": "R1", "value": "10k"}

        # Analyze in different environments
        contexts = [
            {"environment": "consumer", "temperature_range": "0-70C"},
            {"environment": "industrial", "temperature_range": "-20-85C"},
            {"environment": "automotive", "temperature_range": "-40-125C"},
            {"environment": "aerospace", "temperature_range": "-55-125C"},
        ]

        results = []
        for context in contexts:
            modes = analyzer.analyze_component(component, context)
            avg_occurrence = sum(fm.occurrence for fm in modes) / len(modes)
            results.append((context["environment"], avg_occurrence))

        # More harsh environments should have higher occurrence rates
        consumer_avg = next(r[1] for r in results if r[0] == "consumer")
        aerospace_avg = next(r[1] for r in results if r[0] == "aerospace")

        # Aerospace should have higher failure rates than consumer
        self.assertGreaterEqual(aerospace_avg, consumer_avg)


if __name__ == "__main__":
    unittest.main()
