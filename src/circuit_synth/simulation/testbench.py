"""
Automated Test Bench Generator for SPICE Simulations

This module provides automated test bench generation for circuit-synth designs,
creating appropriate stimulus signals and load conditions for various circuit types.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from typing import Dict, List, Optional, Tuple, Union

logger = logging.getLogger(__name__)


class SignalType(Enum):
    """Types of stimulus signals."""

    DC = "dc"
    SINE = "sine"
    SQUARE = "square"
    TRIANGLE = "triangle"
    PULSE = "pulse"
    PWL = "pwl"  # Piece-wise linear
    NOISE = "noise"
    SWEEP = "sweep"


@dataclass
class TestSignal:
    """Definition of a test signal for simulation."""

    signal_type: SignalType
    amplitude: float = 1.0
    frequency: float = 1000.0  # Hz
    dc_offset: float = 0.0
    rise_time: float = 1e-9  # For pulse/square
    fall_time: float = 1e-9
    pulse_width: float = 0.5e-6
    phase: float = 0.0  # Degrees
    points: List[Tuple[float, float]] = None  # For PWL


@dataclass
class LoadCondition:
    """Load configuration for circuit testing."""

    load_type: str  # "resistive", "capacitive", "inductive", "complex"
    resistance: Optional[float] = None
    capacitance: Optional[float] = None
    inductance: Optional[float] = None
    current: Optional[float] = None  # For current load


class TestBenchGenerator:
    """Generates test benches for circuit simulations."""

    def __init__(self, circuit):
        """Initialize with a circuit-synth circuit."""
        self.circuit = circuit
        self.test_signals = {}
        self.load_conditions = {}
        self.power_supplies = {}

    def analyze_circuit_type(self) -> str:
        """Analyze the circuit to determine its type."""
        # Simple heuristic based on components
        components = self.circuit.components

        has_opamp = any("amp" in str(c.symbol).lower() for c in components)
        has_transistor = any(
            any(x in str(c.symbol).lower() for x in ["bjt", "fet", "transistor"])
            for c in components
        )
        has_filter_components = any(
            all(
                any(t in str(c.symbol) for c in components)
                for t in ["Device:R", "Device:C"]
            )
        )

        if has_opamp:
            return "amplifier"
        elif has_transistor:
            return "transistor_circuit"
        elif has_filter_components:
            return "filter"
        else:
            return "general"

    def generate_for_amplifier(self) -> Dict:
        """Generate test bench for amplifier circuits."""
        testbench = {
            "description": "Amplifier circuit test bench",
            "analyses": [],
        }

        # DC operating point
        testbench["analyses"].append(
            {
                "type": "dc_operating_point",
                "description": "Verify DC bias conditions",
            }
        )

        # AC frequency response
        testbench["analyses"].append(
            {
                "type": "ac_analysis",
                "start_frequency": 1,
                "stop_frequency": 10e6,
                "points_per_decade": 20,
                "description": "Frequency response and gain",
            }
        )

        # Input signal for transient
        self.test_signals["input"] = TestSignal(
            signal_type=SignalType.SINE,
            amplitude=0.1,  # 100mV
            frequency=1000,  # 1kHz
            dc_offset=0,
        )

        # Transient analysis
        testbench["analyses"].append(
            {
                "type": "transient",
                "stop_time": 5e-3,  # 5ms (5 periods at 1kHz)
                "step_time": 1e-6,
                "description": "Time domain response",
            }
        )

        # Load condition
        self.load_conditions["output"] = LoadCondition(
            load_type="resistive",
            resistance=10000,  # 10k load
        )

        testbench["signals"] = self.test_signals
        testbench["loads"] = self.load_conditions

        return testbench

    def generate_for_filter(self) -> Dict:
        """Generate test bench for filter circuits."""
        testbench = {
            "description": "Filter circuit test bench",
            "analyses": [],
        }

        # AC analysis for frequency response
        testbench["analyses"].append(
            {
                "type": "ac_analysis",
                "start_frequency": 0.1,
                "stop_frequency": 100e3,
                "points_per_decade": 50,
                "description": "Filter frequency response",
            }
        )

        # Step response
        self.test_signals["step_input"] = TestSignal(
            signal_type=SignalType.PULSE,
            amplitude=1.0,
            rise_time=1e-9,
            pulse_width=100e-3,  # Long pulse for step response
        )

        # Sweep input for filter characterization
        self.test_signals["sweep_input"] = TestSignal(
            signal_type=SignalType.SWEEP,
            amplitude=1.0,
            frequency=1,  # Start frequency
        )

        testbench["analyses"].append(
            {
                "type": "transient",
                "stop_time": 10e-3,
                "step_time": 1e-6,
                "description": "Step response",
            }
        )

        testbench["signals"] = self.test_signals

        return testbench

    def generate_for_power_supply(self) -> Dict:
        """Generate test bench for power supply circuits."""
        testbench = {
            "description": "Power supply test bench",
            "analyses": [],
        }

        # DC sweep for regulation
        testbench["analyses"].append(
            {
                "type": "dc_sweep",
                "source": "VIN",
                "start": 7,
                "stop": 15,
                "step": 0.1,
                "description": "Line regulation test",
            }
        )

        # Load regulation test - varying load current
        self.load_conditions["load_sweep"] = LoadCondition(
            load_type="current",
            current=0.001,  # Start at 1mA
        )

        # Transient with load step
        self.test_signals["load_step"] = TestSignal(
            signal_type=SignalType.PULSE,
            amplitude=0.5,  # 500mA step
            rise_time=1e-6,
            pulse_width=5e-3,
        )

        testbench["analyses"].append(
            {
                "type": "transient",
                "stop_time": 10e-3,
                "step_time": 1e-6,
                "description": "Load transient response",
            }
        )

        # Ripple analysis
        testbench["analyses"].append(
            {
                "type": "ac_analysis",
                "start_frequency": 10,
                "stop_frequency": 100e3,
                "points_per_decade": 20,
                "description": "Output ripple and PSRR",
            }
        )

        testbench["loads"] = self.load_conditions
        testbench["signals"] = self.test_signals

        return testbench

    def generate_for_digital(self) -> Dict:
        """Generate test bench for digital circuits."""
        testbench = {
            "description": "Digital circuit test bench",
            "analyses": [],
        }

        # Digital pulse train
        self.test_signals["clock"] = TestSignal(
            signal_type=SignalType.PULSE,
            amplitude=3.3,  # 3.3V logic
            frequency=1e6,  # 1MHz clock
            rise_time=1e-9,
            fall_time=1e-9,
            pulse_width=0.5e-6,
        )

        # Data pattern (PWL for specific pattern)
        self.test_signals["data"] = TestSignal(
            signal_type=SignalType.PWL,
            points=[
                (0, 0),
                (1e-6, 0),
                (1.01e-6, 3.3),
                (2e-6, 3.3),
                (2.01e-6, 0),
                (3e-6, 0),
                (3.01e-6, 3.3),
                (4e-6, 3.3),
            ],
        )

        testbench["analyses"].append(
            {
                "type": "transient",
                "stop_time": 10e-6,
                "step_time": 1e-9,
                "description": "Digital timing analysis",
            }
        )

        testbench["signals"] = self.test_signals

        return testbench

    def generate_automatic(self) -> Dict:
        """Automatically generate appropriate test bench based on circuit type."""
        circuit_type = self.analyze_circuit_type()

        logger.info(f"Detected circuit type: {circuit_type}")

        if circuit_type == "amplifier":
            return self.generate_for_amplifier()
        elif circuit_type == "filter":
            return self.generate_for_filter()
        elif circuit_type == "power_supply":
            return self.generate_for_power_supply()
        elif circuit_type == "digital":
            return self.generate_for_digital()
        else:
            return self.generate_generic()

    def generate_generic(self) -> Dict:
        """Generate a generic test bench for unknown circuit types."""
        testbench = {
            "description": "Generic circuit test bench",
            "analyses": [],
        }

        # DC operating point - always useful
        testbench["analyses"].append(
            {
                "type": "dc_operating_point",
                "description": "DC operating conditions",
            }
        )

        # AC analysis - check frequency response
        testbench["analyses"].append(
            {
                "type": "ac_analysis",
                "start_frequency": 1,
                "stop_frequency": 1e6,
                "points_per_decade": 10,
                "description": "Frequency response",
            }
        )

        # Basic transient
        self.test_signals["input"] = TestSignal(
            signal_type=SignalType.SINE,
            amplitude=1.0,
            frequency=1000,
        )

        testbench["analyses"].append(
            {
                "type": "transient",
                "stop_time": 5e-3,
                "step_time": 1e-6,
                "description": "Time domain behavior",
            }
        )

        testbench["signals"] = self.test_signals

        return testbench

    def apply_to_spice(self, spice_circuit):
        """Apply the test bench configuration to a PySpice circuit."""
        # Add voltage sources for test signals
        for name, signal in self.test_signals.items():
            self._add_signal_source(spice_circuit, name, signal)

        # Add load conditions
        for name, load in self.load_conditions.items():
            self._add_load(spice_circuit, name, load)

    def _add_signal_source(self, spice_circuit, name: str, signal: TestSignal):
        """Add a signal source to the SPICE circuit."""
        # Implementation would add appropriate SPICE source based on signal type
        pass

    def _add_load(self, spice_circuit, name: str, load: LoadCondition):
        """Add a load condition to the SPICE circuit."""
        # Implementation would add load components
        pass

    def generate_stimulus_code(self) -> str:
        """Generate circuit-synth code for test stimulus."""
        code = []
        code.append("# Test bench stimulus signals")
        code.append("from circuit_synth import Component, Net")
        code.append("")

        for name, signal in self.test_signals.items():
            if signal.signal_type == SignalType.SINE:
                code.append(f"# Sine wave source: {name}")
                code.append(
                    f'{name}_source = Component("Device:V", ref="V", value="{signal.amplitude}V")'
                )
                code.append(
                    f"# Configure as sine: {signal.frequency}Hz, {signal.amplitude}V amplitude"
                )
            elif signal.signal_type == SignalType.PULSE:
                code.append(f"# Pulse source: {name}")
                code.append(
                    f'{name}_source = Component("Device:V", ref="V", value="PULSE")'
                )
                code.append(f"# Pulse: {signal.amplitude}V, {signal.frequency}Hz")

        return "\n".join(code)


def generate_testbench_for_circuit(circuit, auto_detect: bool = True) -> Dict:
    """
    Generate an appropriate test bench for a circuit.

    Args:
        circuit: Circuit-synth circuit object
        auto_detect: Automatically detect circuit type and generate appropriate tests

    Returns:
        Dictionary containing test bench configuration
    """
    generator = TestBenchGenerator(circuit)

    if auto_detect:
        return generator.generate_automatic()
    else:
        return generator.generate_generic()


# Example usage documentation
TESTBENCH_EXAMPLES = """
Test Bench Generator Usage Examples:

1. Automatic Test Bench Generation:
```python
from circuit_synth import circuit
from circuit_synth.simulation import TestBenchGenerator

@circuit
def my_amplifier():
    # ... amplifier circuit definition
    pass

# Generate test bench automatically
c = my_amplifier()
testbench_gen = TestBenchGenerator(c)
testbench = testbench_gen.generate_automatic()

# Apply to simulation
sim = c.simulator()
testbench_gen.apply_to_spice(sim.spice_circuit)
```

2. Custom Test Signals:
```python
from circuit_synth.simulation.testbench import TestSignal, SignalType

# Create custom test signal
custom_signal = TestSignal(
    signal_type=SignalType.SINE,
    amplitude=2.5,  # 2.5V
    frequency=10000,  # 10kHz
    dc_offset=1.5,  # 1.5V DC offset
)

testbench_gen.test_signals["custom_input"] = custom_signal
```

3. Circuit Type Detection:
```python
# Detect circuit type for appropriate testing
circuit_type = testbench_gen.analyze_circuit_type()
print(f"Detected circuit type: {circuit_type}")

# Generate type-specific test bench
if circuit_type == "amplifier":
    testbench = testbench_gen.generate_for_amplifier()
elif circuit_type == "filter":
    testbench = testbench_gen.generate_for_filter()
```
"""
