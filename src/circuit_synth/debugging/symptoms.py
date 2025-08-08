"""
Symptom Analysis and Test Measurement Processing

Provides detailed symptom categorization and measurement interpretation
for circuit debugging.
"""

import re
from dataclasses import dataclass, field
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional, Tuple

import numpy as np


class MeasurementType(Enum):
    """Types of electrical measurements"""

    VOLTAGE_DC = "voltage_dc"
    VOLTAGE_AC = "voltage_ac"
    CURRENT = "current"
    RESISTANCE = "resistance"
    CAPACITANCE = "capacitance"
    INDUCTANCE = "inductance"
    FREQUENCY = "frequency"
    TEMPERATURE = "temperature"
    WAVEFORM = "waveform"
    LOGIC_LEVEL = "logic_level"
    PROTOCOL = "protocol"


@dataclass
class TestMeasurement:
    """Represents a single test measurement with context"""

    measurement_type: MeasurementType
    value: Any
    unit: str
    test_point: str
    reference_point: Optional[str] = "GND"
    timestamp: datetime = field(default_factory=datetime.now)
    conditions: Dict[str, Any] = field(default_factory=dict)
    expected_value: Optional[Any] = None
    tolerance: Optional[float] = None
    pass_fail: Optional[bool] = None
    notes: str = ""

    def evaluate(self) -> bool:
        """Evaluate if measurement is within expected range"""
        if self.expected_value is None:
            return True

        if self.tolerance is None:
            self.tolerance = 0.1  # Default 10% tolerance

        if isinstance(self.value, (int, float)) and isinstance(
            self.expected_value, (int, float)
        ):
            min_val = self.expected_value * (1 - self.tolerance)
            max_val = self.expected_value * (1 + self.tolerance)
            self.pass_fail = min_val <= self.value <= max_val
        else:
            self.pass_fail = self.value == self.expected_value

        return self.pass_fail


@dataclass
class OscilloscopeTrace:
    """Represents oscilloscope waveform data"""

    channel: str
    time_data: List[float]
    voltage_data: List[float]
    timebase: str  # e.g., "1ms/div"
    vertical_scale: str  # e.g., "1V/div"
    trigger_level: float
    trigger_source: str
    coupling: str = "DC"  # AC, DC, GND
    probe_attenuation: int = 1  # 1x, 10x, 100x

    def analyze_waveform(self) -> Dict[str, Any]:
        """Analyze waveform characteristics"""
        v_array = np.array(self.voltage_data)
        t_array = np.array(self.time_data)

        analysis = {
            "min_voltage": float(np.min(v_array)),
            "max_voltage": float(np.max(v_array)),
            "mean_voltage": float(np.mean(v_array)),
            "rms_voltage": float(np.sqrt(np.mean(v_array**2))),
            "peak_to_peak": float(np.max(v_array) - np.min(v_array)),
        }

        # Detect frequency if periodic
        try:
            # Simple zero-crossing detection
            zero_crossings = np.where(np.diff(np.sign(v_array - np.mean(v_array))))[0]
            if len(zero_crossings) > 2:
                periods = np.diff(t_array[zero_crossings[::2]])  # Every other crossing
                if len(periods) > 0:
                    avg_period = np.mean(periods)
                    analysis["frequency"] = 1.0 / avg_period
                    analysis["period"] = avg_period
        except:
            pass

        # Detect rise/fall times
        v_10 = np.min(v_array) + 0.1 * (np.max(v_array) - np.min(v_array))
        v_90 = np.min(v_array) + 0.9 * (np.max(v_array) - np.min(v_array))

        # Find rise time
        rising_edges = []
        for i in range(1, len(v_array)):
            if v_array[i - 1] <= v_10 and v_array[i] >= v_90:
                # Find exact crossing times via interpolation
                t_10 = np.interp(
                    v_10, [v_array[i - 1], v_array[i]], [t_array[i - 1], t_array[i]]
                )
                t_90 = np.interp(
                    v_90, [v_array[i - 1], v_array[i]], [t_array[i - 1], t_array[i]]
                )
                rising_edges.append(t_90 - t_10)

        if rising_edges:
            analysis["rise_time"] = float(np.mean(rising_edges))

        return analysis


class SymptomAnalyzer:
    """Analyzes symptoms and measurements to identify issues"""

    # Symptom patterns for different failure modes
    POWER_SYMPTOMS = [
        "not turning on",
        "no power",
        "dead",
        "won't start",
        "no voltage",
        "burning smell",
        "hot",
        "overheating",
        "smoke",
        "melted",
        "regulator hot",
        "fuse blown",
        "short circuit",
        "overcurrent",
    ]

    DIGITAL_SYMPTOMS = [
        "i2c",
        "spi",
        "uart",
        "usb",
        "can",
        "communication",
        "no ack",
        "nack",
        "timeout",
        "bus error",
        "not responding",
        "enumeration",
        "not detected",
        "unknown device",
    ]

    ANALOG_SYMPTOMS = [
        "noise",
        "distortion",
        "offset",
        "drift",
        "unstable",
        "oscillating",
        "saturated",
        "clipping",
        "no output",
    ]

    RF_SYMPTOMS = [
        "no signal",
        "weak signal",
        "interference",
        "poor range",
        "antenna",
        "vswr",
        "reflection",
        "impedance mismatch",
    ]

    THERMAL_SYMPTOMS = [
        "overheating",
        "thermal shutdown",
        "hot",
        "cold",
        "temperature",
        "thermal cycling",
        "condensation",
    ]

    MECHANICAL_SYMPTOMS = [
        "broken",
        "cracked",
        "loose",
        "vibration",
        "shock",
        "bent",
        "physical damage",
        "connector",
        "intermittent",
    ]

    def __init__(self):
        self.symptom_categories = {
            "power": self.POWER_SYMPTOMS,
            "digital": self.DIGITAL_SYMPTOMS,
            "analog": self.ANALOG_SYMPTOMS,
            "rf": self.RF_SYMPTOMS,
            "thermal": self.THERMAL_SYMPTOMS,
            "mechanical": self.MECHANICAL_SYMPTOMS,
        }

    def categorize_symptoms(self, symptoms: List[str]) -> Dict[str, List[str]]:
        """Categorize symptoms by failure domain"""
        categorized = {category: [] for category in self.symptom_categories}

        for symptom in symptoms:
            symptom_lower = symptom.lower()
            for category, patterns in self.symptom_categories.items():
                if any(pattern in symptom_lower for pattern in patterns):
                    categorized[category].append(symptom)

        # Remove empty categories
        return {k: v for k, v in categorized.items() if v}

    def analyze_voltage_measurement(
        self, measurement: TestMeasurement
    ) -> Dict[str, Any]:
        """Analyze a voltage measurement for issues"""
        analysis = {"status": "unknown", "issues": [], "recommendations": []}

        if measurement.expected_value is None:
            return analysis

        expected = float(measurement.expected_value)
        actual = float(measurement.value)
        deviation = abs(actual - expected) / expected if expected != 0 else float("inf")

        if deviation < 0.05:  # Within 5%
            analysis["status"] = "nominal"
        elif deviation < 0.1:  # Within 10%
            analysis["status"] = "marginal"
            analysis["issues"].append(
                f"Voltage slightly out of spec: {actual}V vs {expected}V expected"
            )
            analysis["recommendations"].append(
                "Check load conditions and regulator feedback"
            )
        else:  # More than 10% deviation
            analysis["status"] = "failed"

            if actual < expected * 0.9:  # More than 10% low
                analysis["issues"].append(
                    f"Voltage too low: {actual}V (expected {expected}V)"
                )
                analysis["recommendations"].extend(
                    [
                        "Check for short circuits or overload",
                        "Verify input voltage to regulator",
                        "Measure current draw",
                        "Check regulator enable signal",
                    ]
                )
            elif actual > expected * 1.1:  # More than 10% high
                analysis["issues"].append(
                    f"Voltage too high: {actual}V (expected {expected}V)"
                )
                analysis["recommendations"].extend(
                    [
                        "Check feedback network resistors",
                        "Verify regulator is correct part",
                        "Look for open circuit in feedback path",
                        "Check for oscillation with oscilloscope",
                    ]
                )

        return analysis

    def analyze_i2c_signals(
        self, sda_trace: OscilloscopeTrace, scl_trace: OscilloscopeTrace
    ) -> Dict[str, Any]:
        """Analyze I2C signal quality and timing"""
        analysis = {
            "bus_health": "unknown",
            "issues": [],
            "measurements": {},
            "recommendations": [],
        }

        # Analyze SDA line
        sda_analysis = sda_trace.analyze_waveform()
        scl_analysis = scl_trace.analyze_waveform()

        # Check voltage levels
        voh = sda_analysis["max_voltage"]  # High level
        vol = sda_analysis["min_voltage"]  # Low level

        analysis["measurements"]["sda_high"] = voh
        analysis["measurements"]["sda_low"] = vol
        analysis["measurements"]["scl_frequency"] = scl_analysis.get("frequency", 0)

        # Check for proper I2C levels (assuming 3.3V I2C)
        if voh < 2.97:  # 90% of 3.3V
            analysis["issues"].append(f"SDA high level too low: {voh}V")
            analysis["recommendations"].append(
                "Check pull-up resistor value (try 2.2kΩ - 4.7kΩ)"
            )

        if vol > 0.4:
            analysis["issues"].append(f"SDA low level too high: {vol}V")
            analysis["recommendations"].append(
                "Check for weak driver or bus contention"
            )

        # Check rise time
        if "rise_time" in sda_analysis:
            rise_time_us = sda_analysis["rise_time"] * 1e6
            analysis["measurements"]["sda_rise_time_us"] = rise_time_us

            # I2C spec: max 1000ns for standard, 300ns for fast mode
            if rise_time_us > 1.0:
                analysis["issues"].append(
                    f"SDA rise time too slow: {rise_time_us:.2f}μs"
                )
                analysis["recommendations"].extend(
                    [
                        "Reduce pull-up resistor value",
                        "Reduce bus capacitance (shorter traces)",
                        "Add I2C buffer/repeater for long buses",
                    ]
                )

        # Check clock frequency
        if "frequency" in scl_analysis:
            freq_khz = scl_analysis["frequency"] / 1000
            analysis["measurements"]["scl_frequency_khz"] = freq_khz

            if freq_khz > 400:
                analysis["recommendations"].append(
                    f"Clock frequency {freq_khz:.1f}kHz exceeds I2C Fast Mode"
                )

        # Overall health assessment
        if not analysis["issues"]:
            analysis["bus_health"] = "healthy"
        elif len(analysis["issues"]) <= 2:
            analysis["bus_health"] = "marginal"
        else:
            analysis["bus_health"] = "failed"

        return analysis

    def analyze_power_rail_stability(
        self, rail_trace: OscilloscopeTrace, load_current: Optional[float] = None
    ) -> Dict[str, Any]:
        """Analyze power rail for noise, ripple, and stability"""
        analysis = {
            "stability": "unknown",
            "issues": [],
            "measurements": {},
            "recommendations": [],
        }

        waveform = rail_trace.analyze_waveform()

        # Calculate ripple
        ripple_vpp = waveform["peak_to_peak"]
        mean_voltage = waveform["mean_voltage"]
        ripple_percent = (ripple_vpp / mean_voltage * 100) if mean_voltage != 0 else 0

        analysis["measurements"]["mean_voltage"] = mean_voltage
        analysis["measurements"]["ripple_vpp"] = ripple_vpp
        analysis["measurements"]["ripple_percent"] = ripple_percent

        # Check ripple levels
        if ripple_percent > 5:
            analysis["issues"].append(f"Excessive ripple: {ripple_percent:.1f}%")
            analysis["recommendations"].extend(
                [
                    "Add more output capacitance",
                    "Use low-ESR capacitors",
                    "Add ferrite bead for high-frequency filtering",
                ]
            )
        elif ripple_percent > 2:
            analysis["issues"].append(f"Moderate ripple: {ripple_percent:.1f}%")
            analysis["recommendations"].append(
                "Consider adding ceramic bypass capacitors"
            )

        # Check for oscillation
        if "frequency" in waveform and waveform["frequency"] > 1000:
            analysis["issues"].append(
                f"Possible oscillation detected at {waveform['frequency']:.1f}Hz"
            )
            analysis["recommendations"].extend(
                [
                    "Check regulator compensation",
                    "Verify feedback loop stability",
                    "Add output capacitance with correct ESR range",
                ]
            )

        # Load regulation analysis if current provided
        if load_current is not None:
            analysis["measurements"]["load_current_a"] = load_current
            # Estimate based on typical regulators
            if ripple_percent > 1 and load_current > 0.5:
                analysis["recommendations"].append(
                    "High ripple under load - check thermal derating"
                )

        # Overall assessment
        if not analysis["issues"]:
            analysis["stability"] = "stable"
        elif len(analysis["issues"]) == 1 and "Moderate" in analysis["issues"][0]:
            analysis["stability"] = "acceptable"
        else:
            analysis["stability"] = "unstable"

        return analysis
