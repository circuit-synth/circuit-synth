"""
Test Plan Generation Agent for Circuit-Synth

This agent generates comprehensive test plans for circuit designs including:
- Functional testing procedures
- Performance validation
- Safety compliance testing
- Manufacturing test procedures
- Equipment specifications and requirements
"""

import json
import logging
from dataclasses import dataclass, field
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

from ..agent_registry import CircuitSubAgent

logger = logging.getLogger(__name__)


@dataclass
class TestEquipment:
    """Test equipment specification"""

    name: str
    type: str
    specifications: Dict[str, Any]
    required: bool = True
    alternatives: List[str] = field(default_factory=list)


@dataclass
class TestProcedure:
    """Individual test procedure"""

    test_id: str
    name: str
    category: str  # functional, performance, safety, manufacturing
    description: str
    equipment: List[str]
    setup: List[str]
    steps: List[str]
    measurements: List[Dict[str, Any]]
    pass_criteria: Dict[str, Any]
    fail_actions: List[str]
    safety_warnings: List[str] = field(default_factory=list)
    duration_minutes: int = 5


@dataclass
class TestPoint:
    """Circuit test point specification"""

    id: str
    net_name: str
    component_ref: Optional[str]
    pin: Optional[str]
    signal_type: str  # power, ground, digital, analog, rf
    nominal_value: Optional[float]
    tolerance_percent: float
    test_equipment: str
    accessibility: str  # probe_point, pad, via, component_pin


class TestPlanGenerator:
    """Generate comprehensive test plans for circuits"""

    def __init__(self):
        self.equipment_db = self._initialize_equipment_db()
        self.test_templates = self._initialize_test_templates()

    def _initialize_equipment_db(self) -> Dict[str, TestEquipment]:
        """Initialize database of test equipment specifications"""
        return {
            "multimeter": TestEquipment(
                name="Digital Multimeter",
                type="multimeter",
                specifications={
                    "voltage_range": "0-1000V DC/AC",
                    "current_range": "0-10A",
                    "resistance_range": "0-100MΩ",
                    "accuracy": "0.5%",
                    "resolution": "6.5 digits",
                },
                alternatives=["Fluke 87V", "Keysight 34461A", "Rigol DM3068"],
            ),
            "oscilloscope": TestEquipment(
                name="Digital Oscilloscope",
                type="oscilloscope",
                specifications={
                    "bandwidth": "100MHz minimum",
                    "channels": "4",
                    "sample_rate": "1GSa/s",
                    "memory_depth": "10Mpts",
                    "probes": "10:1 passive probes",
                },
                alternatives=[
                    "Rigol DS1054Z",
                    "Keysight DSOX1204A",
                    "Tektronix TBS1104",
                ],
            ),
            "power_supply": TestEquipment(
                name="Programmable Power Supply",
                type="power_supply",
                specifications={
                    "channels": "2-3",
                    "voltage_range": "0-30V",
                    "current_range": "0-5A",
                    "resolution": "1mV/1mA",
                    "ripple": "<5mVpp",
                },
                alternatives=["Rigol DP832", "Keysight E36313A", "Siglent SPD3303X"],
            ),
            "logic_analyzer": TestEquipment(
                name="Logic Analyzer",
                type="logic_analyzer",
                specifications={
                    "channels": "16 minimum",
                    "sample_rate": "100MSa/s",
                    "memory": "1M samples/channel",
                    "protocol_decode": "I2C, SPI, UART, CAN",
                },
                alternatives=[
                    "Saleae Logic Pro 16",
                    "Keysight 16850A",
                    "Digilent Digital Discovery",
                ],
            ),
            "spectrum_analyzer": TestEquipment(
                name="Spectrum Analyzer",
                type="spectrum_analyzer",
                specifications={
                    "frequency_range": "9kHz-3GHz",
                    "rbw": "1Hz-3MHz",
                    "phase_noise": "-95dBc/Hz @ 10kHz",
                    "danl": "-161dBm/Hz",
                },
                required=False,
                alternatives=["Rigol DSA815", "Keysight N9320B", "Siglent SSA3032X"],
            ),
            "esd_gun": TestEquipment(
                name="ESD Simulator",
                type="esd_gun",
                specifications={
                    "voltage_range": "±30kV",
                    "discharge_modes": "Contact and Air",
                    "standards": "IEC 61000-4-2",
                    "discharge_network": "150pF/330Ω",
                },
                required=False,
                alternatives=["Teseq NSG 435", "EM Test Dito", "NoiseKen ESS-2000"],
            ),
            "thermal_chamber": TestEquipment(
                name="Temperature Chamber",
                type="thermal_chamber",
                specifications={
                    "temperature_range": "-40°C to +125°C",
                    "humidity_range": "10-95% RH",
                    "stability": "±0.5°C",
                    "ramp_rate": "5°C/min",
                },
                required=False,
                alternatives=["ESPEC BTL-433", "Thermotron S-1.2", "Weiss WK3-180/40"],
            ),
        }

    def _initialize_test_templates(self) -> Dict[str, List[str]]:
        """Initialize test procedure templates"""
        return {
            "power_on": [
                "Verify input voltage range",
                "Check inrush current",
                "Measure power rail sequencing",
                "Verify voltage regulation",
                "Check ripple and noise",
            ],
            "functional": [
                "Verify reset functionality",
                "Test GPIO functionality",
                "Validate communication interfaces",
                "Check interrupt handling",
                "Verify peripheral operation",
            ],
            "performance": [
                "Measure power consumption",
                "Check frequency accuracy",
                "Verify timing margins",
                "Test signal integrity",
                "Measure thermal performance",
            ],
            "safety": [
                "ESD testing per IEC 61000-4-2",
                "Overvoltage protection test",
                "Short circuit protection",
                "Thermal shutdown verification",
                "Isolation testing",
            ],
            "manufacturing": [
                "In-circuit test (ICT)",
                "Boundary scan (JTAG)",
                "Flying probe test",
                "Functional test fixture",
                "Burn-in testing",
            ],
        }

    def analyze_circuit(self, circuit_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Analyze circuit to identify test requirements

        Args:
            circuit_data: Circuit JSON or parsed circuit data

        Returns:
            Analysis results with test points and requirements
        """
        analysis = {
            "power_rails": [],
            "interfaces": [],
            "test_points": [],
            "critical_signals": [],
            "component_types": set(),
        }

        # Function to analyze components and nets recursively
        def analyze_circuit_level(data: Dict[str, Any], prefix: str = ""):
            # Extract power rails from nets
            if "nets" in data and isinstance(data["nets"], dict):
                for net_name, net_data in data.get("nets", {}).items():
                    net_upper = net_name.upper()
                    if any(
                        pwr in net_upper
                        for pwr in ["VCC", "VDD", "VSS", "GND", "3V3", "5V", "12V"]
                    ):
                        analysis["power_rails"].append(
                            {
                                "name": f"{prefix}{net_name}" if prefix else net_name,
                                "type": "power" if "V" in net_upper else "ground",
                            }
                        )
            elif "nets" in data and isinstance(data["nets"], list):
                for net in data.get("nets", []):
                    net_name = net.get("name", "").upper()
                    if any(
                        pwr in net_name
                        for pwr in ["VCC", "VDD", "VSS", "GND", "3V3", "5V", "12V"]
                    ):
                        analysis["power_rails"].append(
                            {
                                "name": net_name,
                                "type": "power" if "V" in net_name else "ground",
                            }
                        )

            # Identify interfaces from components
            if "components" in data:
                components = data["components"]
                # Handle both dict and list formats
                if isinstance(components, dict):
                    for ref, comp in components.items():
                        self._analyze_component(comp, ref, analysis, prefix)
                elif isinstance(components, list):
                    for comp in components:
                        self._analyze_component(
                            comp, comp.get("ref", ""), analysis, prefix
                        )

            # Process subcircuits recursively
            if "subcircuits" in data:
                for subcircuit in data.get("subcircuits", []):
                    subcircuit_name = subcircuit.get("name", "")
                    analyze_circuit_level(subcircuit, f"{subcircuit_name}/")

        # Start analysis from top level
        analyze_circuit_level(circuit_data)

        # Convert set to list for JSON serialization
        analysis["component_types"] = list(analysis["component_types"])

        return analysis

    def _analyze_component(
        self, comp: Dict[str, Any], ref: str, analysis: Dict, prefix: str = ""
    ):
        """Analyze individual component and categorize it"""
        symbol = comp.get("symbol", "").lower()
        full_ref = f"{prefix}{ref}" if prefix else ref

        # Categorize component types
        if (
            "mcu" in symbol
            or "stm32" in symbol
            or "esp32" in symbol
            or "esp32" in comp.get("value", "").lower()
        ):
            analysis["component_types"].add("microcontroller")
            analysis["interfaces"].append({"type": "mcu", "ref": full_ref})
        elif "usb" in symbol:
            analysis["component_types"].add("usb_interface")
            analysis["interfaces"].append({"type": "usb", "ref": full_ref})
        elif "connector" in symbol:
            analysis["component_types"].add("connector")
        elif "regulator" in symbol or "ams1117" in symbol.lower() or "ldo" in symbol:
            analysis["component_types"].add("power_regulator")
        elif "crystal" in symbol or "oscillator" in symbol:
            analysis["component_types"].add("timing")
        elif "esd" in symbol or "tpd" in symbol or "protection" in symbol:
            analysis["component_types"].add("protection")
        elif "ft231" in symbol or "ch340" in symbol or "cp210" in symbol:
            analysis["component_types"].add("usb_uart_bridge")

    def identify_test_points(self, circuit_analysis: Dict[str, Any]) -> List[TestPoint]:
        """
        Identify critical test points in the circuit

        Args:
            circuit_analysis: Results from analyze_circuit

        Returns:
            List of test points with specifications
        """
        test_points = []

        # Add power rail test points
        for rail in circuit_analysis.get("power_rails", []):
            test_points.append(
                TestPoint(
                    id=f"TP_{rail['name']}",
                    net_name=rail["name"],
                    component_ref=None,
                    pin=None,
                    signal_type="power" if rail["type"] == "power" else "ground",
                    nominal_value=self._get_nominal_voltage(rail["name"]),
                    tolerance_percent=5.0,
                    test_equipment="multimeter",
                    accessibility="probe_point",
                )
            )

        # Add interface test points
        for interface in circuit_analysis.get("interfaces", []):
            if interface["type"] == "usb":
                test_points.extend(
                    [
                        TestPoint(
                            id="TP_USB_VBUS",
                            net_name="VBUS",
                            component_ref=interface["ref"],
                            pin="VBUS",
                            signal_type="power",
                            nominal_value=5.0,
                            tolerance_percent=5.0,
                            test_equipment="multimeter",
                            accessibility="component_pin",
                        ),
                        TestPoint(
                            id="TP_USB_DP",
                            net_name="USB_DP",
                            component_ref=interface["ref"],
                            pin="D+",
                            signal_type="digital",
                            nominal_value=None,
                            tolerance_percent=10.0,
                            test_equipment="oscilloscope",
                            accessibility="component_pin",
                        ),
                        TestPoint(
                            id="TP_USB_DM",
                            net_name="USB_DM",
                            component_ref=interface["ref"],
                            pin="D-",
                            signal_type="digital",
                            nominal_value=None,
                            tolerance_percent=10.0,
                            test_equipment="oscilloscope",
                            accessibility="component_pin",
                        ),
                    ]
                )
            elif interface["type"] == "mcu":
                test_points.extend(
                    [
                        TestPoint(
                            id="TP_MCU_RESET",
                            net_name="NRST",
                            component_ref=interface["ref"],
                            pin="NRST",
                            signal_type="digital",
                            nominal_value=3.3,
                            tolerance_percent=10.0,
                            test_equipment="oscilloscope",
                            accessibility="component_pin",
                        ),
                        TestPoint(
                            id="TP_MCU_CLOCK",
                            net_name="HSE_IN",
                            component_ref=interface["ref"],
                            pin="OSC_IN",
                            signal_type="analog",
                            nominal_value=None,
                            tolerance_percent=2.0,
                            test_equipment="oscilloscope",
                            accessibility="component_pin",
                        ),
                    ]
                )

        return test_points

    def _get_nominal_voltage(self, net_name: str) -> Optional[float]:
        """Get nominal voltage from net name"""
        net_upper = net_name.upper()
        if "3V3" in net_upper or "3.3V" in net_upper:
            return 3.3
        elif "5V" in net_upper:
            return 5.0
        elif "12V" in net_upper:
            return 12.0
        elif "1V8" in net_upper or "1.8V" in net_upper:
            return 1.8
        elif "2V5" in net_upper or "2.5V" in net_upper:
            return 2.5
        elif "GND" in net_upper or "VSS" in net_upper:
            return 0.0
        return None

    def generate_test_procedures(
        self,
        circuit_analysis: Dict[str, Any],
        test_points: List[TestPoint],
        test_categories: List[str] = None,
    ) -> List[TestProcedure]:
        """
        Generate comprehensive test procedures

        Args:
            circuit_analysis: Circuit analysis results
            test_points: List of identified test points
            test_categories: Categories to include (default: all)

        Returns:
            List of test procedures
        """
        if test_categories is None:
            test_categories = ["functional", "performance", "safety", "manufacturing"]

        procedures = []

        # Power-on test (always included)
        if "functional" in test_categories:
            procedures.append(
                self._generate_power_on_test(circuit_analysis, test_points)
            )
            procedures.extend(
                self._generate_functional_tests(circuit_analysis, test_points)
            )

        if "performance" in test_categories:
            procedures.extend(
                self._generate_performance_tests(circuit_analysis, test_points)
            )

        if "safety" in test_categories:
            procedures.extend(
                self._generate_safety_tests(circuit_analysis, test_points)
            )

        if "manufacturing" in test_categories:
            procedures.extend(
                self._generate_manufacturing_tests(circuit_analysis, test_points)
            )

        return procedures

    def _generate_power_on_test(
        self, circuit_analysis: Dict[str, Any], test_points: List[TestPoint]
    ) -> TestProcedure:
        """Generate power-on test procedure"""
        power_rails = [tp for tp in test_points if tp.signal_type == "power"]

        return TestProcedure(
            test_id="PWR-001",
            name="Power-On Sequence Test",
            category="functional",
            description="Verify proper power-on sequence and voltage levels",
            equipment=["multimeter", "oscilloscope", "power_supply"],
            setup=[
                "Connect power supply to input connector",
                "Set current limit to 500mA initially",
                "Connect oscilloscope to power rail test points",
                "Connect multimeter for DC measurements",
            ],
            steps=[
                "Apply input voltage slowly from 0V to nominal",
                "Monitor inrush current (should be < 2A peak)",
                "Verify power rail sequencing timing",
                f"Measure each power rail voltage: {', '.join([tp.net_name for tp in power_rails])}",
                "Check for oscillation or instability",
                "Measure ripple voltage on each rail",
            ],
            measurements=[
                {
                    "parameter": tp.net_name,
                    "nominal": tp.nominal_value,
                    "tolerance": f"±{tp.tolerance_percent}%",
                    "equipment": "multimeter",
                }
                for tp in power_rails
            ],
            pass_criteria={
                "voltages_in_spec": True,
                "ripple_max_mv": 50,
                "sequencing_correct": True,
                "no_oscillation": True,
            },
            fail_actions=[
                "Check power supply connections",
                "Verify input voltage and current limit",
                "Inspect voltage regulator components",
                "Check decoupling capacitors",
            ],
            safety_warnings=[
                "Ensure current limit is set before power-on",
                "Check for hot components during test",
            ],
            duration_minutes=10,
        )

    def _generate_functional_tests(
        self, circuit_analysis: Dict[str, Any], test_points: List[TestPoint]
    ) -> List[TestProcedure]:
        """Generate functional test procedures"""
        procedures = []

        # MCU functional test
        if "microcontroller" in circuit_analysis.get("component_types", []):
            procedures.append(
                TestProcedure(
                    test_id="FUNC-001",
                    name="Microcontroller Functional Test",
                    category="functional",
                    description="Verify microcontroller basic functionality",
                    equipment=["oscilloscope", "logic_analyzer"],
                    setup=[
                        "Power on the circuit",
                        "Connect programmer/debugger",
                        "Load test firmware",
                    ],
                    steps=[
                        "Verify reset functionality (pull NRST low, then release)",
                        "Check crystal oscillator frequency",
                        "Test GPIO toggle on all available pins",
                        "Verify UART communication at 115200 baud",
                        "Test I2C/SPI interfaces if present",
                    ],
                    measurements=[
                        {
                            "parameter": "Crystal frequency",
                            "nominal": "8MHz/16MHz/25MHz",
                            "tolerance": "±50ppm",
                            "equipment": "oscilloscope",
                        },
                        {
                            "parameter": "GPIO high level",
                            "nominal": 3.3,
                            "tolerance": "±10%",
                            "equipment": "multimeter",
                        },
                    ],
                    pass_criteria={
                        "reset_works": True,
                        "clock_stable": True,
                        "gpio_functional": True,
                        "communication_works": True,
                    },
                    fail_actions=[
                        "Check crystal and loading capacitors",
                        "Verify power supply to MCU",
                        "Check reset circuit components",
                        "Verify programmer connections",
                    ],
                    duration_minutes=15,
                )
            )

        # USB interface test
        if "usb_interface" in circuit_analysis.get("component_types", []):
            procedures.append(
                TestProcedure(
                    test_id="FUNC-002",
                    name="USB Interface Test",
                    category="functional",
                    description="Verify USB communication and compliance",
                    equipment=["oscilloscope", "multimeter"],
                    setup=[
                        "Connect USB cable to host computer",
                        "Install USB protocol analyzer software",
                        "Connect oscilloscope to D+ and D- lines",
                    ],
                    steps=[
                        "Measure VBUS voltage (should be 5V ±5%)",
                        "Verify device enumeration on host",
                        "Check D+ pull-up resistor (1.5kΩ for full-speed)",
                        "Measure differential signal quality",
                        "Test data transfer at maximum speed",
                    ],
                    measurements=[
                        {
                            "parameter": "VBUS voltage",
                            "nominal": 5.0,
                            "tolerance": "±5%",
                            "equipment": "multimeter",
                        },
                        {
                            "parameter": "D+/D- differential",
                            "nominal": "400mV",
                            "tolerance": "±10%",
                            "equipment": "oscilloscope",
                        },
                    ],
                    pass_criteria={
                        "enumeration_success": True,
                        "vbus_in_spec": True,
                        "signal_quality_good": True,
                        "data_transfer_works": True,
                    },
                    fail_actions=[
                        "Check USB connector soldering",
                        "Verify series resistors on data lines",
                        "Check ESD protection components",
                        "Verify firmware USB stack",
                    ],
                    duration_minutes=10,
                )
            )

        return procedures

    def _generate_performance_tests(
        self, circuit_analysis: Dict[str, Any], test_points: List[TestPoint]
    ) -> List[TestProcedure]:
        """Generate performance test procedures"""
        procedures = []

        procedures.append(
            TestProcedure(
                test_id="PERF-001",
                name="Power Consumption Test",
                category="performance",
                description="Measure power consumption in various operating modes",
                equipment=["multimeter", "power_supply"],
                setup=[
                    "Connect ammeter in series with power input",
                    "Set up automated test sequence if available",
                    "Prepare thermal imaging camera if available",
                ],
                steps=[
                    "Measure idle current consumption",
                    "Measure active mode current (all peripherals on)",
                    "Measure sleep/low-power mode current",
                    "Calculate total power consumption",
                    "Check for thermal hotspots",
                ],
                measurements=[
                    {
                        "parameter": "Idle current",
                        "nominal": "50mA",
                        "tolerance": "±20%",
                        "equipment": "multimeter",
                    },
                    {
                        "parameter": "Active current",
                        "nominal": "200mA",
                        "tolerance": "±20%",
                        "equipment": "multimeter",
                    },
                    {
                        "parameter": "Sleep current",
                        "nominal": "1mA",
                        "tolerance": "±50%",
                        "equipment": "multimeter",
                    },
                ],
                pass_criteria={
                    "current_within_spec": True,
                    "no_thermal_issues": True,
                    "efficiency_acceptable": True,
                },
                fail_actions=[
                    "Check for shorts or leakage paths",
                    "Verify component values",
                    "Check firmware power management",
                    "Inspect thermal design",
                ],
                duration_minutes=20,
            )
        )

        return procedures

    def _generate_safety_tests(
        self, circuit_analysis: Dict[str, Any], test_points: List[TestPoint]
    ) -> List[TestProcedure]:
        """Generate safety test procedures"""
        procedures = []

        procedures.append(
            TestProcedure(
                test_id="SAFE-001",
                name="ESD Protection Test",
                category="safety",
                description="Verify ESD protection per IEC 61000-4-2",
                equipment=["esd_gun", "oscilloscope"],
                setup=[
                    "Configure ESD gun for contact discharge",
                    "Set initial voltage to ±2kV",
                    "Connect oscilloscope to monitor critical signals",
                    "Ensure proper grounding of test setup",
                ],
                steps=[
                    "Apply ±2kV contact discharge to exposed connectors",
                    "Apply ±4kV contact discharge to ground planes",
                    "Apply ±8kV air discharge to plastic enclosure",
                    "Verify circuit functionality after each discharge",
                    "Check for latch-up conditions",
                ],
                measurements=[
                    {
                        "parameter": "Recovery time",
                        "nominal": "<1s",
                        "tolerance": "N/A",
                        "equipment": "oscilloscope",
                    },
                    {
                        "parameter": "Functionality",
                        "nominal": "Normal operation",
                        "tolerance": "No permanent damage",
                        "equipment": "functional_test",
                    },
                ],
                pass_criteria={
                    "no_permanent_damage": True,
                    "auto_recovery": True,
                    "data_integrity": True,
                },
                fail_actions=[
                    "Add TVS diodes on exposed signals",
                    "Improve PCB grounding",
                    "Add ferrite beads on cables",
                    "Review ESD protection components",
                ],
                safety_warnings=[
                    "ESD testing can damage unprotected circuits",
                    "Ensure proper PPE when using ESD gun",
                    "Keep sensitive equipment away from test area",
                ],
                duration_minutes=30,
            )
        )

        procedures.append(
            TestProcedure(
                test_id="SAFE-002",
                name="Overvoltage Protection Test",
                category="safety",
                description="Verify circuit protection against overvoltage",
                equipment=["power_supply", "multimeter", "oscilloscope"],
                setup=[
                    "Connect variable power supply",
                    "Set current limit to safe value",
                    "Monitor critical component voltages",
                ],
                steps=[
                    "Gradually increase input voltage to 110% of maximum",
                    "Monitor protection circuit activation",
                    "Verify no damage to downstream components",
                    "Test auto-recovery when voltage returns to normal",
                    "Check protection response time",
                ],
                measurements=[
                    {
                        "parameter": "Protection threshold",
                        "nominal": "110% of Vmax",
                        "tolerance": "±5%",
                        "equipment": "multimeter",
                    },
                    {
                        "parameter": "Response time",
                        "nominal": "<100µs",
                        "tolerance": "N/A",
                        "equipment": "oscilloscope",
                    },
                ],
                pass_criteria={
                    "protection_activates": True,
                    "no_component_damage": True,
                    "auto_recovery_works": True,
                },
                fail_actions=[
                    "Check TVS diode specifications",
                    "Verify crowbar circuit operation",
                    "Review input protection design",
                    "Add redundant protection",
                ],
                safety_warnings=[
                    "Overvoltage testing may damage components",
                    "Use current limiting for safety",
                    "Have replacement components ready",
                ],
                duration_minutes=15,
            )
        )

        return procedures

    def _generate_manufacturing_tests(
        self, circuit_analysis: Dict[str, Any], test_points: List[TestPoint]
    ) -> List[TestProcedure]:
        """Generate manufacturing test procedures"""
        procedures = []

        procedures.append(
            TestProcedure(
                test_id="MFG-001",
                name="In-Circuit Test (ICT)",
                category="manufacturing",
                description="Automated bed-of-nails testing for production",
                equipment=["ICT_fixture", "multimeter"],
                setup=[
                    "Load board into ICT fixture",
                    "Ensure all test points make contact",
                    "Load test program into ICT system",
                ],
                steps=[
                    "Test continuity of all nets",
                    "Verify component presence and orientation",
                    "Measure passive component values (R, C, L)",
                    "Check for shorts between adjacent nets",
                    "Verify power supply isolation",
                ],
                measurements=[
                    {
                        "parameter": "Net continuity",
                        "nominal": "<1Ω",
                        "tolerance": "N/A",
                        "equipment": "ICT_system",
                    },
                    {
                        "parameter": "Component values",
                        "nominal": "Per BOM",
                        "tolerance": "±5%",
                        "equipment": "ICT_system",
                    },
                ],
                pass_criteria={
                    "all_nets_connected": True,
                    "no_shorts": True,
                    "components_correct": True,
                    "values_in_tolerance": True,
                },
                fail_actions=[
                    "Inspect solder joints",
                    "Check component placement",
                    "Verify PCB fabrication",
                    "Review assembly process",
                ],
                duration_minutes=2,
            )
        )

        if "microcontroller" in circuit_analysis.get("component_types", []):
            procedures.append(
                TestProcedure(
                    test_id="MFG-002",
                    name="Boundary Scan Test (JTAG)",
                    category="manufacturing",
                    description="JTAG boundary scan for digital connectivity",
                    equipment=["JTAG_programmer", "boundary_scan_software"],
                    setup=[
                        "Connect JTAG adapter to test points",
                        "Load boundary scan description files",
                        "Configure scan chain",
                    ],
                    steps=[
                        "Verify JTAG chain integrity",
                        "Run interconnect test",
                        "Test pull-up/pull-down resistors",
                        "Verify crystal connections",
                        "Program device ID for traceability",
                    ],
                    measurements=[
                        {
                            "parameter": "Chain integrity",
                            "nominal": "Complete",
                            "tolerance": "N/A",
                            "equipment": "JTAG_tester",
                        },
                        {
                            "parameter": "Interconnect test",
                            "nominal": "100% pass",
                            "tolerance": "N/A",
                            "equipment": "JTAG_tester",
                        },
                    ],
                    pass_criteria={
                        "chain_complete": True,
                        "interconnect_pass": True,
                        "device_id_programmed": True,
                    },
                    fail_actions=[
                        "Check JTAG connector soldering",
                        "Verify MCU power and ground",
                        "Inspect BGA balls if applicable",
                        "Review JTAG signal integrity",
                    ],
                    duration_minutes=5,
                )
            )

        return procedures

    def generate_test_report(
        self,
        circuit_name: str,
        circuit_analysis: Dict[str, Any],
        test_points: List[TestPoint],
        procedures: List[TestProcedure],
        output_format: str = "markdown",
    ) -> str:
        """
        Generate comprehensive test plan report

        Args:
            circuit_name: Name of the circuit
            circuit_analysis: Circuit analysis results
            test_points: List of test points
            procedures: List of test procedures
            output_format: Output format (markdown, json, csv)

        Returns:
            Formatted test plan report
        """
        if output_format == "markdown":
            return self._generate_markdown_report(
                circuit_name, circuit_analysis, test_points, procedures
            )
        elif output_format == "json":
            return self._generate_json_report(
                circuit_name, circuit_analysis, test_points, procedures
            )
        else:
            raise ValueError(f"Unsupported output format: {output_format}")

    def _generate_markdown_report(
        self,
        circuit_name: str,
        circuit_analysis: Dict[str, Any],
        test_points: List[TestPoint],
        procedures: List[TestProcedure],
    ) -> str:
        """Generate markdown format test report"""
        report = []

        # Header
        report.append(f"# Test Plan: {circuit_name}")
        report.append(f"\n## Executive Summary\n")
        report.append(f"- **Total Test Points**: {len(test_points)}")
        report.append(f"- **Test Procedures**: {len(procedures)}")
        report.append(
            f"- **Estimated Duration**: {sum(p.duration_minutes for p in procedures)} minutes"
        )
        report.append(
            f"- **Component Types**: {', '.join(circuit_analysis.get('component_types', []))}"
        )

        # Required Equipment
        report.append(f"\n## Required Test Equipment\n")
        equipment_used = set()
        for proc in procedures:
            equipment_used.update(proc.equipment)

        for eq_id in equipment_used:
            if eq_id in self.equipment_db:
                eq = self.equipment_db[eq_id]
                report.append(f"\n### {eq.name}")
                report.append(f"- **Type**: {eq.type}")
                for spec, value in eq.specifications.items():
                    report.append(f"- **{spec.replace('_', ' ').title()}**: {value}")
                if eq.alternatives:
                    report.append(
                        f"- **Recommended Models**: {', '.join(eq.alternatives)}"
                    )

        # Test Points
        report.append(f"\n## Test Points\n")
        report.append(
            "| ID | Net | Component | Signal Type | Nominal | Tolerance | Equipment |"
        )
        report.append("|---|---|---|---|---|---|---|")
        for tp in test_points:
            nominal = f"{tp.nominal_value}V" if tp.nominal_value is not None else "N/A"
            report.append(
                f"| {tp.id} | {tp.net_name} | {tp.component_ref or 'N/A'} | "
                f"{tp.signal_type} | {nominal} | ±{tp.tolerance_percent}% | {tp.test_equipment} |"
            )

        # Test Procedures
        report.append(f"\n## Test Procedures\n")

        # Group by category
        categories = {}
        for proc in procedures:
            if proc.category not in categories:
                categories[proc.category] = []
            categories[proc.category].append(proc)

        for category, procs in categories.items():
            report.append(f"\n### {category.title()} Tests\n")

            for proc in procs:
                report.append(f"\n#### {proc.test_id}: {proc.name}")
                report.append(f"\n**Description**: {proc.description}")
                report.append(f"\n**Duration**: {proc.duration_minutes} minutes")
                report.append(f"\n**Required Equipment**: {', '.join(proc.equipment)}")

                if proc.safety_warnings:
                    report.append(f"\n**⚠️ Safety Warnings**:")
                    for warning in proc.safety_warnings:
                        report.append(f"- {warning}")

                report.append(f"\n**Setup**:")
                for i, step in enumerate(proc.setup, 1):
                    report.append(f"{i}. {step}")

                report.append(f"\n**Test Steps**:")
                for i, step in enumerate(proc.steps, 1):
                    report.append(f"{i}. {step}")

                if proc.measurements:
                    report.append(f"\n**Measurements**:")
                    report.append("| Parameter | Nominal | Tolerance | Equipment |")
                    report.append("|---|---|---|---|")
                    for meas in proc.measurements:
                        report.append(
                            f"| {meas['parameter']} | {meas['nominal']} | "
                            f"{meas['tolerance']} | {meas['equipment']} |"
                        )

                report.append(f"\n**Pass Criteria**:")
                for criteria, value in proc.pass_criteria.items():
                    report.append(f"- {criteria.replace('_', ' ').title()}: {value}")

                report.append(f"\n**If Test Fails**:")
                for action in proc.fail_actions:
                    report.append(f"- {action}")

        # Test Summary
        report.append(f"\n## Test Execution Summary\n")
        report.append("| Test ID | Test Name | Category | Duration | Status | Notes |")
        report.append("|---|---|---|---|---|---|")
        for proc in procedures:
            report.append(
                f"| {proc.test_id} | {proc.name} | {proc.category} | "
                f"{proc.duration_minutes} min | [ ] Pass [ ] Fail | |"
            )

        report.append(f"\n## Sign-off\n")
        report.append("- **Tested By**: _________________________ Date: _____________")
        report.append("- **Reviewed By**: _______________________ Date: _____________")
        report.append("- **Approved By**: _______________________ Date: _____________")

        return "\n".join(report)

    def _generate_json_report(
        self,
        circuit_name: str,
        circuit_analysis: Dict[str, Any],
        test_points: List[TestPoint],
        procedures: List[TestProcedure],
    ) -> str:
        """Generate JSON format test report"""
        report = {
            "circuit_name": circuit_name,
            "summary": {
                "total_test_points": len(test_points),
                "total_procedures": len(procedures),
                "estimated_duration_minutes": sum(
                    p.duration_minutes for p in procedures
                ),
                "component_types": circuit_analysis.get("component_types", []),
            },
            "test_points": [
                {
                    "id": tp.id,
                    "net_name": tp.net_name,
                    "component_ref": tp.component_ref,
                    "pin": tp.pin,
                    "signal_type": tp.signal_type,
                    "nominal_value": tp.nominal_value,
                    "tolerance_percent": tp.tolerance_percent,
                    "test_equipment": tp.test_equipment,
                    "accessibility": tp.accessibility,
                }
                for tp in test_points
            ],
            "procedures": [
                {
                    "test_id": proc.test_id,
                    "name": proc.name,
                    "category": proc.category,
                    "description": proc.description,
                    "equipment": proc.equipment,
                    "setup": proc.setup,
                    "steps": proc.steps,
                    "measurements": proc.measurements,
                    "pass_criteria": proc.pass_criteria,
                    "fail_actions": proc.fail_actions,
                    "safety_warnings": proc.safety_warnings,
                    "duration_minutes": proc.duration_minutes,
                }
                for proc in procedures
            ],
            "equipment_required": {
                eq_id: {
                    "name": eq.name,
                    "type": eq.type,
                    "specifications": eq.specifications,
                    "required": eq.required,
                    "alternatives": eq.alternatives,
                }
                for eq_id, eq in self.equipment_db.items()
                if any(eq_id in proc.equipment for proc in procedures)
            },
        }

        return json.dumps(report, indent=2)


def create_test_plan_from_circuit(
    circuit_path: str,
    output_format: str = "markdown",
    test_categories: List[str] = None,
) -> str:
    """
    Create comprehensive test plan from circuit file

    Args:
        circuit_path: Path to circuit JSON or Python file
        output_format: Output format (markdown, json)
        test_categories: Test categories to include

    Returns:
        Formatted test plan
    """
    generator = TestPlanGenerator()

    # Load circuit data
    circuit_data = {}
    if circuit_path.endswith(".json"):
        with open(circuit_path, "r") as f:
            circuit_data = json.load(f)
    else:
        # For Python files, would need to execute and extract circuit
        logger.warning("Python circuit file parsing not implemented yet")
        return "Error: Python circuit file parsing not implemented"

    # Analyze circuit
    analysis = generator.analyze_circuit(circuit_data)

    # Identify test points
    test_points = generator.identify_test_points(analysis)

    # Generate procedures
    procedures = generator.generate_test_procedures(
        analysis, test_points, test_categories
    )

    # Generate report
    circuit_name = Path(circuit_path).stem
    return generator.generate_test_report(
        circuit_name, analysis, test_points, procedures, output_format
    )


# Agent interface for Claude integration
def handle_test_plan_request(request: str, context: Dict[str, Any] = None) -> str:
    """
    Handle test plan generation request from Claude agent

    Args:
        request: User request string
        context: Additional context (circuit data, preferences)

    Returns:
        Generated test plan or instructions
    """
    if context and "circuit_file" in context:
        return create_test_plan_from_circuit(
            context["circuit_file"],
            context.get("format", "markdown"),
            context.get("categories", None),
        )
    else:
        return """
# Test Plan Generator Ready

To generate a test plan, please provide:
1. Circuit file path (JSON or Python)
2. Desired output format (markdown or json)
3. Test categories to include (optional)

Example usage:
```python
from circuit_synth.ai_integration.claude.agents.test_plan_agent import create_test_plan_from_circuit

test_plan = create_test_plan_from_circuit(
    "my_circuit.json",
    output_format="markdown",
    test_categories=["functional", "safety"]
)
```

The generator will analyze your circuit and create comprehensive test procedures including:
- Functional testing
- Performance validation
- Safety compliance
- Manufacturing tests
"""
