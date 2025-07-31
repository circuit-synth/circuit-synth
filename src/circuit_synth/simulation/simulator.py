"""
Main CircuitSimulator class for circuit-synth SPICE integration.

This module provides the primary interface for running SPICE simulations
on circuit-synth designs.
"""

import logging
import os
import platform
from typing import Dict, List, Optional, Tuple, Union

# Configure logging
logger = logging.getLogger(__name__)

try:
    import PySpice
    from PySpice.Spice.Netlist import Circuit as SpiceCircuit
    from PySpice.Spice.NgSpice.Shared import NgSpiceShared
    from PySpice.Unit import *

    PYSPICE_AVAILABLE = True

    # Auto-configure ngspice library path for macOS
    if platform.system() == "Darwin":  # macOS
        possible_paths = [
            "/opt/homebrew/lib/libngspice.dylib",  # Apple Silicon
            "/usr/local/lib/libngspice.dylib",  # Intel Mac
        ]
        for path in possible_paths:
            if os.path.exists(path):
                NgSpiceShared.LIBRARY_PATH = path
                logger.debug(f"Set ngspice library path: {path}")
                break

except ImportError as e:
    PYSPICE_AVAILABLE = False
    logger.warning(f"PySpice not available: {e}")


class SimulationResult:
    """Container for SPICE simulation results with analysis capabilities."""

    def __init__(self, analysis_result, analysis_type: str):
        self.analysis = analysis_result
        self.analysis_type = analysis_type
        self._voltages = {}
        self._currents = {}

        # Extract voltages and currents from analysis
        if hasattr(analysis_result, "nodes"):
            for node in analysis_result.nodes:
                if hasattr(analysis_result, node):
                    self._voltages[node] = analysis_result[node]

    def get_voltage(self, node: str) -> Union[float, List[float]]:
        """Get voltage at a specific node."""
        if node in self._voltages:
            voltage = self._voltages[node]
            # Handle scalar or array results
            if hasattr(voltage, "__len__") and len(voltage) == 1:
                return float(voltage[0])
            elif hasattr(voltage, "__len__"):
                return [float(v) for v in voltage]
            else:
                return float(voltage)
        else:
            # Try direct access
            try:
                voltage = self.analysis[node]
                if hasattr(voltage, "__len__") and len(voltage) == 1:
                    return float(voltage[0])
                elif hasattr(voltage, "__len__"):
                    return [float(v) for v in voltage]
                else:
                    return float(voltage)
            except:
                raise KeyError(f"Node '{node}' not found in simulation results")

    def get_current(self, component: str) -> Union[float, List[float]]:
        """Get current through a specific component."""
        # PySpice current notation: I(Vcomponent) for voltage sources
        current_name = f"I({component})"
        try:
            current = self.analysis[current_name]
            if hasattr(current, "__len__") and len(current) == 1:
                return float(current[0])
            elif hasattr(current, "__len__"):
                return [float(i) for i in current]
            else:
                return float(current)
        except:
            raise KeyError(f"Current for component '{component}' not found")

    def list_nodes(self) -> List[str]:
        """List all available voltage nodes."""
        nodes = []
        if hasattr(self.analysis, "nodes"):
            nodes.extend(self.analysis.nodes)
        # Also check for direct access
        for attr in dir(self.analysis):
            if not attr.startswith("_") and attr not in ["nodes", "branches"]:
                try:
                    val = getattr(self.analysis, attr)
                    if hasattr(val, "__len__") or isinstance(val, (int, float)):
                        nodes.append(attr)
                except:
                    pass
        return list(set(nodes))

    def plot(self, *nodes, title: Optional[str] = None):
        """Plot voltage results (requires matplotlib)."""
        try:
            import matplotlib.pyplot as plt
        except ImportError:
            logger.error("matplotlib required for plotting")
            return

        plt.figure(figsize=(10, 6))

        for node in nodes:
            try:
                voltage = self.get_voltage(node)
                if isinstance(voltage, list):
                    plt.plot(voltage, label=f"V({node})")
                else:
                    plt.axhline(y=voltage, label=f"V({node}) = {voltage:.3f}V")
            except KeyError as e:
                logger.warning(f"Could not plot {node}: {e}")

        plt.xlabel("Time/Frequency/Sweep")
        plt.ylabel("Voltage (V)")
        plt.title(title or f"{self.analysis_type.upper()} Analysis Results")
        plt.legend()
        plt.grid(True)
        plt.show()


class CircuitSimulator:
    """Main interface for SPICE simulation of circuit-synth designs."""

    def __init__(self, circuit_synth_circuit):
        if not PYSPICE_AVAILABLE:
            raise ImportError(
                "PySpice not available. Install with: pip install PySpice\n"
                "Also ensure ngspice is installed on your system."
            )

        self.circuit_synth_circuit = circuit_synth_circuit
        self.spice_circuit = None
        self._convert_to_spice()

    def _convert_to_spice(self):
        """Convert circuit-synth circuit to PySpice format."""
        from .converter import SpiceConverter

        converter = SpiceConverter(self.circuit_synth_circuit)
        self.spice_circuit = converter.convert()

    def operating_point(self) -> SimulationResult:
        """Run DC operating point analysis."""
        if not self.spice_circuit:
            raise RuntimeError("SPICE circuit not initialized")

        simulator = self.spice_circuit.simulator(temperature=25, nominal_temperature=25)
        analysis = simulator.operating_point()

        return SimulationResult(analysis, "dc_op")

    def dc_analysis(
        self, source: str, start: float, stop: float, step: float
    ) -> SimulationResult:
        """Run DC sweep analysis."""
        if not self.spice_circuit:
            raise RuntimeError("SPICE circuit not initialized")

        simulator = self.spice_circuit.simulator(temperature=25, nominal_temperature=25)
        analysis = simulator.dc(**{source: slice(start, stop, step)})

        return SimulationResult(analysis, "dc_sweep")

    def ac_analysis(
        self, start_freq: float, stop_freq: float, points: int = 100
    ) -> SimulationResult:
        """Run AC analysis."""
        if not self.spice_circuit:
            raise RuntimeError("SPICE circuit not initialized")

        simulator = self.spice_circuit.simulator(temperature=25, nominal_temperature=25)
        analysis = simulator.ac(
            start_frequency=start_freq @ u_Hz,
            stop_frequency=stop_freq @ u_Hz,
            number_of_points=points,
            variation="dec",
        )

        return SimulationResult(analysis, "ac")

    def transient_analysis(self, step_time: float, end_time: float) -> SimulationResult:
        """Run transient analysis."""
        if not self.spice_circuit:
            raise RuntimeError("SPICE circuit not initialized")

        simulator = self.spice_circuit.simulator(temperature=25, nominal_temperature=25)
        analysis = simulator.transient(
            step_time=step_time @ u_s, end_time=end_time @ u_s
        )

        return SimulationResult(analysis, "transient")

    def list_components(self) -> List[str]:
        """List all components in the SPICE circuit."""
        if not self.spice_circuit:
            return []

        components = []
        for element in self.spice_circuit.elements:
            components.append(str(element.name))
        return components

    def list_nodes(self) -> List[str]:
        """List all nodes in the SPICE circuit."""
        if not self.spice_circuit:
            return []

        nodes = []
        for node in self.spice_circuit.node_names:
            nodes.append(str(node))
        return nodes

    def get_netlist(self) -> str:
        """Get the SPICE netlist as string."""
        if not self.spice_circuit:
            return ""

        return str(self.spice_circuit)
