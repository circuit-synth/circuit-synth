"""
Test Guidance and Troubleshooting Tree Generation

Provides systematic test procedures and decision trees for debugging.
"""

import json
from dataclasses import dataclass, field
from enum import Enum
from typing import Any, Callable, Dict, List, Optional


class TestEquipment(Enum):
    """Types of test equipment"""

    MULTIMETER = "multimeter"
    OSCILLOSCOPE = "oscilloscope"
    LOGIC_ANALYZER = "logic_analyzer"
    SPECTRUM_ANALYZER = "spectrum_analyzer"
    POWER_SUPPLY = "power_supply"
    SIGNAL_GENERATOR = "signal_generator"
    THERMAL_CAMERA = "thermal_camera"
    MICROSCOPE = "microscope"
    LCR_METER = "lcr_meter"
    PROTOCOL_ANALYZER = "protocol_analyzer"


@dataclass
class TestStep:
    """Represents a single test step in troubleshooting"""

    step_id: str
    description: str
    equipment_needed: List[TestEquipment]
    test_points: List[str]
    procedure: List[str]
    expected_results: Dict[str, Any]
    pass_action: Optional[str] = None  # Next step if pass
    fail_action: Optional[str] = None  # Next step if fail
    safety_warnings: List[str] = field(default_factory=list)
    tips: List[str] = field(default_factory=list)
    images: List[str] = field(default_factory=list)

    def to_markdown(self) -> str:
        """Convert test step to markdown format"""
        md = f"## Step {self.step_id}: {self.description}\n\n"

        if self.safety_warnings:
            md += "⚠️ **Safety Warnings:**\n"
            for warning in self.safety_warnings:
                md += f"- {warning}\n"
            md += "\n"

        md += "**Equipment Needed:**\n"
        for equip in self.equipment_needed:
            md += f"- {equip.value}\n"
        md += "\n"

        md += "**Test Points:**\n"
        for point in self.test_points:
            md += f"- {point}\n"
        md += "\n"

        md += "**Procedure:**\n"
        for i, step in enumerate(self.procedure, 1):
            md += f"{i}. {step}\n"
        md += "\n"

        md += "**Expected Results:**\n"
        for key, value in self.expected_results.items():
            md += f"- {key}: {value}\n"
        md += "\n"

        if self.tips:
            md += "💡 **Tips:**\n"
            for tip in self.tips:
                md += f"- {tip}\n"
            md += "\n"

        if self.pass_action:
            md += f"✅ **If Pass:** {self.pass_action}\n"
        if self.fail_action:
            md += f"❌ **If Fail:** {self.fail_action}\n"

        return md


@dataclass
class TroubleshootingTree:
    """Represents a complete troubleshooting decision tree"""

    title: str
    description: str
    initial_step: str
    steps: Dict[str, TestStep]
    equipment_list: List[TestEquipment]
    safety_notes: List[str]

    def get_step(self, step_id: str) -> Optional[TestStep]:
        """Get a specific test step"""
        return self.steps.get(step_id)

    def to_markdown(self) -> str:
        """Convert entire tree to markdown document"""
        md = f"# {self.title}\n\n"
        md += f"{self.description}\n\n"

        if self.safety_notes:
            md += "## ⚠️ General Safety Notes\n"
            for note in self.safety_notes:
                md += f"- {note}\n"
            md += "\n"

        md += "## Required Equipment\n"
        for equip in self.equipment_list:
            md += f"- {equip.value}\n"
        md += "\n"

        md += "## Troubleshooting Steps\n\n"

        # Traverse tree in order
        visited = set()
        to_visit = [self.initial_step]

        while to_visit:
            step_id = to_visit.pop(0)
            if step_id in visited or step_id not in self.steps:
                continue

            visited.add(step_id)
            step = self.steps[step_id]
            md += step.to_markdown()
            md += "\n---\n\n"

            # Add connected steps to visit
            if step.pass_action and step.pass_action.startswith("step_"):
                to_visit.append(step.pass_action.split(":")[0].strip())
            if step.fail_action and step.fail_action.startswith("step_"):
                to_visit.append(step.fail_action.split(":")[0].strip())

        return md

    def to_mermaid(self) -> str:
        """Generate Mermaid diagram of troubleshooting flow"""
        mermaid = "```mermaid\ngraph TD\n"

        for step_id, step in self.steps.items():
            # Create node
            label = step.description.replace('"', "'")
            mermaid += f'    {step_id}["{label}"]\n'

            # Add connections
            if step.pass_action:
                if step.pass_action.startswith("step_"):
                    next_id = step.pass_action.split(":")[0].strip()
                    mermaid += f"    {step_id} -->|Pass| {next_id}\n"
                else:
                    mermaid += f'    {step_id} -->|Pass| solution_{step_id}["{step.pass_action}"]\n'

            if step.fail_action:
                if step.fail_action.startswith("step_"):
                    next_id = step.fail_action.split(":")[0].strip()
                    mermaid += f"    {step_id} -->|Fail| {next_id}\n"
                else:
                    mermaid += f'    {step_id} -->|Fail| issue_{step_id}["{step.fail_action}"]\n'

        mermaid += "```"
        return mermaid


class TestGuidance:
    """Generates test guidance and troubleshooting procedures"""

    @staticmethod
    def create_power_troubleshooting_tree() -> TroubleshootingTree:
        """Create standard power supply troubleshooting tree"""
        steps = {
            "step_1": TestStep(
                step_id="1",
                description="Check Input Power",
                equipment_needed=[TestEquipment.MULTIMETER],
                test_points=["Power input connector", "GND"],
                procedure=[
                    "Set multimeter to DC voltage mode",
                    "Place black probe on GND",
                    "Place red probe on power input positive",
                    "Read voltage value",
                ],
                expected_results={"Input Voltage": "Within ±10% of nominal"},
                pass_action="step_2: Check fuse/protection",
                fail_action="Fix power supply or connection",
                safety_warnings=[
                    "Ensure correct polarity",
                    "Check voltage rating before connecting",
                ],
                tips=["Wiggle connector to check for intermittent connection"],
            ),
            "step_2": TestStep(
                step_id="2",
                description="Check Fuse and Protection Circuits",
                equipment_needed=[TestEquipment.MULTIMETER],
                test_points=["Fuse terminals", "TVS diode", "Reverse polarity diode"],
                procedure=[
                    "Set multimeter to continuity mode",
                    "Check fuse for continuity",
                    "Set to diode mode",
                    "Check protection diodes forward voltage",
                    "Check for shorts across power rails",
                ],
                expected_results={
                    "Fuse": "Continuity (beep)",
                    "TVS diode": "Open circuit in normal direction",
                    "Power to GND": "> 100Ω",
                },
                pass_action="step_3: Check voltage regulator",
                fail_action="Replace fuse or protection components",
                tips=["Visual inspection for blown fuse or burnt components"],
            ),
            "step_3": TestStep(
                step_id="3",
                description="Check Voltage Regulator",
                equipment_needed=[
                    TestEquipment.MULTIMETER,
                    TestEquipment.THERMAL_CAMERA,
                ],
                test_points=[
                    "Regulator input",
                    "Regulator output",
                    "Enable pin",
                    "Feedback pin",
                ],
                procedure=[
                    "Measure regulator input voltage",
                    "Measure regulator output voltage",
                    "Check enable pin state (if present)",
                    "Measure feedback voltage",
                    "Use thermal camera to check temperature",
                ],
                expected_results={
                    "Input": "Present and correct",
                    "Output": "Within specification",
                    "Enable": "Logic high (if used)",
                    "Temperature": "< 70°C",
                },
                pass_action="step_4: Check load and distribution",
                fail_action="Replace regulator or fix enable/feedback circuit",
                safety_warnings=["Regulator may be hot - avoid touching"],
                tips=["Check datasheet for dropout voltage requirements"],
            ),
            "step_4": TestStep(
                step_id="4",
                description="Check Power Distribution and Load",
                equipment_needed=[TestEquipment.MULTIMETER, TestEquipment.OSCILLOSCOPE],
                test_points=[
                    "Various power test points",
                    "Bulk capacitors",
                    "IC power pins",
                ],
                procedure=[
                    "Measure voltage at different points on board",
                    "Check for voltage drop across traces",
                    "Measure current consumption",
                    "Use scope to check for oscillation or ripple",
                    "Disconnect loads one by one to isolate issue",
                ],
                expected_results={
                    "Voltage distribution": "< 100mV drop",
                    "Current": "Within expected range",
                    "Ripple": "< 50mV p-p",
                    "Oscillation": "None",
                },
                pass_action="Power system OK - check other subsystems",
                fail_action="Fix PCB layout, add capacitance, or reduce load",
                tips=[
                    "Check for solder bridges causing shorts",
                    "Verify capacitor polarity",
                ],
            ),
        }

        return TroubleshootingTree(
            title="Power Supply Troubleshooting",
            description="Systematic procedure for debugging power supply issues",
            initial_step="step_1",
            steps=steps,
            equipment_list=[
                TestEquipment.MULTIMETER,
                TestEquipment.OSCILLOSCOPE,
                TestEquipment.THERMAL_CAMERA,
            ],
            safety_notes=[
                "Always check voltage levels before connecting",
                "Use current-limited power supply when possible",
                "Wear ESD protection when handling board",
                "Allow capacitors to discharge before handling",
            ],
        )

    @staticmethod
    def create_i2c_troubleshooting_tree() -> TroubleshootingTree:
        """Create I2C communication troubleshooting tree"""
        steps = {
            "step_1": TestStep(
                step_id="1",
                description="Check I2C Bus Idle State",
                equipment_needed=[TestEquipment.MULTIMETER, TestEquipment.OSCILLOSCOPE],
                test_points=["SDA", "SCL", "GND"],
                procedure=[
                    "Power on the board",
                    "Ensure no I2C communication is active",
                    "Measure DC voltage on SDA and SCL",
                    "Both should be pulled high",
                ],
                expected_results={
                    "SDA voltage": "VDD (3.3V or 5V)",
                    "SCL voltage": "VDD (3.3V or 5V)",
                },
                pass_action="step_2: Check pull-up resistors",
                fail_action="step_5: Check for bus conflict or short",
                tips=["If voltage is 0V, check for shorts or missing pull-ups"],
            ),
            "step_2": TestStep(
                step_id="2",
                description="Verify Pull-up Resistors",
                equipment_needed=[TestEquipment.MULTIMETER],
                test_points=["SDA pull-up", "SCL pull-up"],
                procedure=[
                    "Power off the board",
                    "Measure resistance from SDA to VDD",
                    "Measure resistance from SCL to VDD",
                    "Typical values: 2.2kΩ to 10kΩ",
                ],
                expected_results={
                    "SDA pull-up": "2.2kΩ - 10kΩ",
                    "SCL pull-up": "2.2kΩ - 10kΩ",
                },
                pass_action="step_3: Check I2C signals during communication",
                fail_action="Add or replace pull-up resistors",
                tips=["Lower values for higher speed or longer buses"],
            ),
            "step_3": TestStep(
                step_id="3",
                description="Analyze I2C Communication Signals",
                equipment_needed=[
                    TestEquipment.OSCILLOSCOPE,
                    TestEquipment.LOGIC_ANALYZER,
                ],
                test_points=["SDA", "SCL", "GND"],
                procedure=[
                    "Connect scope/analyzer to SDA, SCL, and GND",
                    "Trigger on falling edge of SDA (START condition)",
                    "Initiate I2C communication",
                    "Capture and analyze waveforms",
                    "Check rise/fall times, voltage levels, clock frequency",
                ],
                expected_results={
                    "START condition": "SDA falls while SCL high",
                    "Clock frequency": "100kHz or 400kHz",
                    "ACK/NACK": "SDA low for ACK",
                    "Rise time": "< 1000ns (standard) or < 300ns (fast)",
                },
                pass_action="step_4: Verify I2C addresses and protocol",
                fail_action="Fix signal integrity issues",
                tips=["Use I2C decoder if available", "Check for clock stretching"],
            ),
            "step_4": TestStep(
                step_id="4",
                description="Verify I2C Device Addresses",
                equipment_needed=[TestEquipment.LOGIC_ANALYZER],
                test_points=["SDA", "SCL"],
                procedure=[
                    "Run I2C scanner/discovery code",
                    "Note all responding addresses",
                    "Compare with expected device addresses",
                    "Check for address conflicts",
                    "Verify 7-bit vs 10-bit addressing",
                ],
                expected_results={
                    "Device addresses": "Match datasheet values",
                    "No conflicts": "Each device unique address",
                    "ACK received": "For all expected devices",
                },
                pass_action="I2C bus functioning correctly",
                fail_action="Check device address configuration pins/jumpers",
                tips=["Some devices have configurable addresses via pins"],
            ),
            "step_5": TestStep(
                step_id="5",
                description="Check for Bus Conflicts and Shorts",
                equipment_needed=[TestEquipment.MULTIMETER],
                test_points=["All I2C devices", "SDA", "SCL"],
                procedure=[
                    "Power off board",
                    "Disconnect I2C devices one by one",
                    "Check resistance between SDA and GND",
                    "Check resistance between SCL and GND",
                    "Check resistance between SDA and SCL",
                ],
                expected_results={
                    "SDA to GND": "> 10kΩ",
                    "SCL to GND": "> 10kΩ",
                    "SDA to SCL": "> 100kΩ",
                },
                pass_action="step_2: Re-check with devices connected",
                fail_action="Fix short circuit or damaged device",
                tips=["Look for solder bridges", "Check for damaged PCB traces"],
            ),
        }

        return TroubleshootingTree(
            title="I2C Communication Troubleshooting",
            description="Systematic debugging of I2C bus issues",
            initial_step="step_1",
            steps=steps,
            equipment_list=[
                TestEquipment.MULTIMETER,
                TestEquipment.OSCILLOSCOPE,
                TestEquipment.LOGIC_ANALYZER,
            ],
            safety_notes=[
                "Ensure voltage levels match between all I2C devices",
                "Use level shifters for mixed voltage systems",
                "Keep I2C traces short and away from noise sources",
            ],
        )

    @staticmethod
    def create_usb_troubleshooting_tree() -> TroubleshootingTree:
        """Create USB troubleshooting tree"""
        steps = {
            "step_1": TestStep(
                step_id="1",
                description="Check USB Power (VBUS)",
                equipment_needed=[TestEquipment.MULTIMETER],
                test_points=["VBUS", "GND", "Shield"],
                procedure=[
                    "Connect USB cable to host",
                    "Measure voltage on VBUS pin",
                    "Check shield connection to GND",
                    "Verify current capability",
                ],
                expected_results={
                    "VBUS": "4.75V - 5.25V",
                    "Shield": "Connected to GND",
                    "Available current": "> 100mA",
                },
                pass_action="step_2: Check USB data lines",
                fail_action="Fix USB power or connector issue",
                safety_warnings=["Do not short VBUS to data lines"],
                tips=["Try different USB ports and cables"],
            ),
            "step_2": TestStep(
                step_id="2",
                description="Check USB Data Lines (D+/D-)",
                equipment_needed=[TestEquipment.OSCILLOSCOPE],
                test_points=["D+", "D-", "GND"],
                procedure=[
                    "Connect scope to D+ and D- (differential mode if available)",
                    "Trigger on enumeration attempt",
                    "Check for proper differential signaling",
                    "Verify signal levels and impedance",
                ],
                expected_results={
                    "D+ idle": "0V (FS) or 3.3V (LS)",
                    "D- idle": "0V",
                    "Differential impedance": "90Ω ±15%",
                    "Signal quality": "Clean edges, no ringing",
                },
                pass_action="step_3: Check USB termination",
                fail_action="Fix D+/D- routing or termination",
                tips=["D+/D- should be matched length differential pair"],
            ),
            "step_3": TestStep(
                step_id="3",
                description="Verify USB Speed Detection",
                equipment_needed=[TestEquipment.OSCILLOSCOPE, TestEquipment.MULTIMETER],
                test_points=["D+", "D- termination resistors"],
                procedure=[
                    "Check for 1.5kΩ pull-up on D+ (Full Speed)",
                    "Or 1.5kΩ pull-up on D- (Low Speed)",
                    "For HS, check 45Ω termination to GND",
                    "Verify pull-up is enabled during enumeration",
                ],
                expected_results={
                    "FS pull-up": "1.5kΩ on D+ to 3.3V",
                    "LS pull-up": "1.5kΩ on D- to 3.3V",
                    "HS termination": "45Ω to GND (both lines)",
                },
                pass_action="step_4: Check crystal/clock",
                fail_action="Fix USB termination resistors",
                tips=["Some MCUs have internal pull-ups"],
            ),
            "step_4": TestStep(
                step_id="4",
                description="Verify USB Clock Source",
                equipment_needed=[TestEquipment.OSCILLOSCOPE],
                test_points=["Crystal", "MCU clock pins"],
                procedure=[
                    "Check crystal oscillation",
                    "Verify frequency (typically 6, 8, 12, 16, 24, 48 MHz)",
                    "Check amplitude and stability",
                    "Verify PLL configuration if used",
                ],
                expected_results={
                    "Crystal frequency": "±50ppm of nominal",
                    "Amplitude": "> 0.5V p-p",
                    "Startup time": "< 10ms",
                    "Jitter": "< 100ps RMS",
                },
                pass_action="USB hardware OK - check firmware",
                fail_action="Fix crystal circuit or load capacitors",
                tips=["USB requires accurate timing (±0.25%)"],
            ),
        }

        return TroubleshootingTree(
            title="USB Communication Troubleshooting",
            description="Debug USB enumeration and communication issues",
            initial_step="step_1",
            steps=steps,
            equipment_list=[
                TestEquipment.MULTIMETER,
                TestEquipment.OSCILLOSCOPE,
                TestEquipment.LOGIC_ANALYZER,
            ],
            safety_notes=[
                "USB can provide up to 500mA - use current limiting",
                "ESD protection required on USB lines",
                "Maintain 90Ω differential impedance for D+/D-",
            ],
        )
