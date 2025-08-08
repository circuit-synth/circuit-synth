"""
SpiceConverter: Converts circuit-synth designs to PySpice format.

This module handles the translation from circuit-synth components and nets
to SPICE netlists that can be simulated with PySpice/ngspice.
"""

import logging
import re
from typing import Any, Dict, List, Optional

logger = logging.getLogger(__name__)

try:
    from PySpice.Spice.Netlist import Circuit as SpiceCircuit
    from PySpice.Unit import *

    PYSPICE_AVAILABLE = True
except ImportError:
    PYSPICE_AVAILABLE = False


class SpiceConverter:
    """Converts circuit-synth circuits to PySpice format."""

    def __init__(self, circuit_synth_circuit):
        self.circuit = circuit_synth_circuit
        self.spice_circuit = None
        self.voltage_sources = []
        self.node_map = {}

    def convert(self) -> "SpiceCircuit":
        """Convert circuit-synth circuit to PySpice circuit."""
        if not PYSPICE_AVAILABLE:
            raise ImportError("PySpice not available")

        # Create PySpice circuit
        circuit_name = getattr(self.circuit, "name", "Circuit")
        self.spice_circuit = SpiceCircuit(circuit_name)

        # Map circuit-synth nets to SPICE nodes
        self._map_nodes()

        # Add components to SPICE circuit
        self._add_components()

        # Add power sources (voltage/current sources)
        self._add_power_sources()

        return self.spice_circuit

    def _map_nodes(self):
        """Create mapping from circuit-synth nets to SPICE node names."""
        self.node_map = {}

        # Handle both dict and list formats for nets
        if hasattr(self.circuit.nets, "values"):
            # Dict format: {name: net_object}
            nets_to_process = self.circuit.nets.values()
        elif hasattr(self.circuit.nets, "__iter__"):
            # List format: [net_object, ...]
            nets_to_process = self.circuit.nets
        else:
            logger.error("Unknown nets format")
            return

        # Map GND net to SPICE ground
        for net in nets_to_process:
            net_name = getattr(net, "name", str(net))
            if net_name.upper() in ["GND", "GROUND", "VSS"]:
                self.node_map[net_name] = self.spice_circuit.gnd
            else:
                self.node_map[net_name] = net_name

    def _add_components(self):
        """Add circuit-synth components to SPICE circuit."""
        for component in self.circuit.components:
            self._add_component(component)

    def _add_component(self, component):
        """Add a single component to the SPICE circuit."""
        symbol = getattr(component, "symbol", "")
        ref = getattr(component, "ref", "X")
        value = getattr(component, "value", None)

        # Determine component type from symbol
        if "Device:R" in symbol:
            self._add_resistor(component, ref, value)
        elif "Device:C" in symbol:
            self._add_capacitor(component, ref, value)
        elif "Device:L" in symbol:
            self._add_inductor(component, ref, value)
        elif "Device:D" in symbol or "Diode:" in symbol:
            self._add_diode(component, ref, value)
        elif any(x in symbol.lower() for x in ["op", "amp", "lm", "tl"]):
            self._add_opamp(component, ref, value)
        elif "Transistor_BJT:" in symbol or "Device:Q" in symbol:
            self._add_bjt_transistor(component, ref, value)
        elif "Transistor_FET:" in symbol or "Device:M" in symbol:
            self._add_mosfet(component, ref, value)
        elif "Reference_Voltage:" in symbol or "Device:V" in symbol:
            self._add_voltage_source(component, ref, value)
        elif "Reference_Current:" in symbol or "Device:I" in symbol:
            self._add_current_source(component, ref, value)
        else:
            logger.warning(f"Unknown component type: {symbol} - skipping")

    def _add_resistor(self, component, ref: str, value: str):
        """Add resistor to SPICE circuit."""
        # Get connected nodes
        nodes = self._get_component_nodes(component)
        if len(nodes) < 2:
            logger.warning(f"Resistor {ref} needs 2 connections, got {len(nodes)}")
            return

        # Convert value to SPICE format
        spice_value = self._convert_value_to_spice(value, "R")

        # Add to SPICE circuit
        self.spice_circuit.R(ref, nodes[0], nodes[1], spice_value)
        logger.debug(f"Added resistor {ref}: {nodes[0]} -> {nodes[1]} = {spice_value}")

    def _add_capacitor(self, component, ref: str, value: str):
        """Add capacitor to SPICE circuit."""
        nodes = self._get_component_nodes(component)
        if len(nodes) < 2:
            logger.warning(f"Capacitor {ref} needs 2 connections, got {len(nodes)}")
            return

        spice_value = self._convert_value_to_spice(value, "C")
        self.spice_circuit.C(ref, nodes[0], nodes[1], spice_value)
        logger.debug(f"Added capacitor {ref}: {nodes[0]} -> {nodes[1]} = {spice_value}")

    def _add_inductor(self, component, ref: str, value: str):
        """Add inductor to SPICE circuit."""
        nodes = self._get_component_nodes(component)
        if len(nodes) < 2:
            logger.warning(f"Inductor {ref} needs 2 connections, got {len(nodes)}")
            return

        spice_value = self._convert_value_to_spice(value, "L")
        self.spice_circuit.L(ref, nodes[0], nodes[1], spice_value)
        logger.debug(f"Added inductor {ref}: {nodes[0]} -> {nodes[1]} = {spice_value}")

    def _add_diode(self, component, ref: str, value: str):
        """Add diode to SPICE circuit."""
        nodes = self._get_component_nodes(component)
        if len(nodes) < 2:
            logger.warning(f"Diode {ref} needs 2 connections, got {len(nodes)}")
            return

        # Use default diode model
        model_name = value or "DefaultDiode"
        self.spice_circuit.D(ref, nodes[0], nodes[1], model=model_name)
        logger.debug(f"Added diode {ref}: {nodes[0]} -> {nodes[1]} model={model_name}")

    def _add_opamp(self, component, ref: str, value: str):
        """Add op-amp to SPICE circuit (simplified model)."""
        nodes = self._get_component_nodes(component)
        if len(nodes) < 3:
            logger.warning(
                f"Op-amp {ref} needs at least 3 connections, got {len(nodes)}"
            )
            return

        # Simplified op-amp as voltage-controlled voltage source
        # Assumes nodes[0] = out, nodes[1] = in+, nodes[2] = in-
        gain = 100000  # High gain approximation
        self.spice_circuit.VCVS(
            ref, nodes[0], self.spice_circuit.gnd, nodes[1], nodes[2], gain
        )
        logger.debug(f"Added op-amp {ref} with gain {gain}")

    def _add_bjt_transistor(self, component, ref: str, value: str):
        """Add BJT transistor to SPICE circuit."""
        nodes = self._get_component_nodes(component)
        if len(nodes) < 3:
            logger.warning(f"BJT {ref} needs 3 connections (C,B,E), got {len(nodes)}")
            return

        # Determine if NPN or PNP from symbol or value
        model_name = value or "DefaultNPN"
        if "pnp" in str(component.symbol).lower() or "pnp" in str(value).lower():
            model_name = value or "DefaultPNP"

        # Add transistor (collector, base, emitter)
        self.spice_circuit.Q(ref, nodes[0], nodes[1], nodes[2], model=model_name)
        logger.debug(
            f"Added BJT {ref}: C={nodes[0]}, B={nodes[1]}, E={nodes[2]}, model={model_name}"
        )

    def _add_mosfet(self, component, ref: str, value: str):
        """Add MOSFET to SPICE circuit."""
        nodes = self._get_component_nodes(component)
        if len(nodes) < 3:
            logger.warning(
                f"MOSFET {ref} needs at least 3 connections (D,G,S), got {len(nodes)}"
            )
            return

        # Determine NMOS or PMOS from symbol or value
        model_name = value or "DefaultNMOS"
        if "pmos" in str(component.symbol).lower() or "pmos" in str(value).lower():
            model_name = value or "DefaultPMOS"

        # Add MOSFET (drain, gate, source, bulk - bulk defaults to source if not provided)
        if len(nodes) >= 4:
            self.spice_circuit.M(
                ref, nodes[0], nodes[1], nodes[2], nodes[3], model=model_name
            )
            logger.debug(
                f"Added MOSFET {ref}: D={nodes[0]}, G={nodes[1]}, S={nodes[2]}, B={nodes[3]}"
            )
        else:
            # Bulk connected to source
            self.spice_circuit.M(
                ref, nodes[0], nodes[1], nodes[2], nodes[2], model=model_name
            )
            logger.debug(
                f"Added MOSFET {ref}: D={nodes[0]}, G={nodes[1]}, S={nodes[2]} (bulk=source)"
            )

    def _add_voltage_source(self, component, ref: str, value: str):
        """Add voltage source to SPICE circuit."""
        nodes = self._get_component_nodes(component)
        if len(nodes) < 2:
            logger.warning(
                f"Voltage source {ref} needs 2 connections, got {len(nodes)}"
            )
            return

        # Parse voltage value
        voltage = self._convert_value_to_spice(value or "5V", "V")

        # Add to list of voltage sources for tracking
        self.voltage_sources.append(ref)

        # Add voltage source (positive, negative, voltage)
        self.spice_circuit.V(ref, nodes[0], nodes[1], voltage)
        logger.debug(
            f"Added voltage source {ref}: {nodes[0]} -> {nodes[1]} = {voltage}V"
        )

    def _add_current_source(self, component, ref: str, value: str):
        """Add current source to SPICE circuit."""
        nodes = self._get_component_nodes(component)
        if len(nodes) < 2:
            logger.warning(
                f"Current source {ref} needs 2 connections, got {len(nodes)}"
            )
            return

        # Parse current value
        current = self._convert_value_to_spice(value or "1mA", "I")

        # Add current source (positive, negative, current)
        self.spice_circuit.I(ref, nodes[0], nodes[1], current)
        logger.debug(
            f"Added current source {ref}: {nodes[0]} -> {nodes[1]} = {current}A"
        )

    def _get_component_nodes(self, component) -> List[str]:
        """Get the SPICE nodes connected to a component."""
        nodes = []

        # Get component connections from the circuit
        # circuit.nets is a dict, iterate over values
        if hasattr(self.circuit.nets, "values"):
            nets_to_check = self.circuit.nets.values()
        else:
            nets_to_check = self.circuit.nets

        for net in nets_to_check:
            net_name = getattr(net, "name", str(net))

            # Check if this net has pins connected to our component
            if hasattr(net, "pins"):
                for pin in net.pins:
                    # Each pin has a reference back to its component
                    # The pin string format is like "Pin(~ of R1, net=VIN)"
                    pin_str = str(pin)
                    component_ref = getattr(component, "ref", "")

                    # Check if this pin belongs to our component
                    if f" of {component_ref}," in pin_str:
                        # Map to SPICE node name
                        spice_node = self.node_map.get(net_name, net_name)
                        if spice_node not in nodes:
                            nodes.append(spice_node)
                        break

        # Sort nodes to ensure consistent pin ordering (important for SPICE)
        # Convert all to strings first to avoid type comparison issues
        nodes.sort(key=str)

        # If we didn't find connections, log for debugging
        if not nodes:
            logger.warning(
                f"No connections found for component {getattr(component, 'ref', 'unknown')}"
            )

        return nodes

    def _convert_value_to_spice(self, value: str, component_type: str) -> float:
        """Convert circuit-synth component value to SPICE format."""
        if not value:
            # Default values
            defaults = {"R": 1000, "C": 1e-6, "L": 1e-3}
            return defaults.get(component_type, 1.0)

        # Parse value string (e.g., "10k", "100nF", "1mH")
        value = str(value).strip().replace(" ", "")

        # Extract numeric part and suffix
        match = re.match(r"^([0-9.]+)([a-zA-Z]*)$", value)
        if not match:
            logger.warning(f"Could not parse value '{value}', using 1.0")
            return 1.0

        numeric_part = float(match.group(1))
        suffix = match.group(2).lower()

        # Convert suffixes to multipliers
        multipliers = {
            # Resistance
            "r": 1,
            "ohm": 1,
            "ohms": 1,
            "k": 1e3,
            "kohm": 1e3,
            "kohms": 1e3,
            "m": 1e6,
            "meg": 1e6,
            "mohm": 1e6,
            "mohms": 1e6,
            # Capacitance
            "f": 1,
            "pf": 1e-12,
            "nf": 1e-9,
            "uf": 1e-6,
            "mf": 1e-3,
            "p": 1e-12,
            "n": 1e-9,
            "u": 1e-6,
            # Inductance
            "h": 1,
            "nh": 1e-9,
            "uh": 1e-6,
            "mh": 1e-3,
            # Voltage
            "v": 1,
            "mv": 1e-3,
            "kv": 1e3,
            # Current
            "a": 1,
            "ma": 1e-3,
            "ua": 1e-6,
            "na": 1e-9,
        }

        multiplier = multipliers.get(suffix, 1.0)
        return numeric_part * multiplier

    def _add_power_sources(self):
        """Add power sources needed for simulation."""
        # Check if we need to add power sources based on net names
        power_nets = []

        # Handle both dict and list formats for nets
        if hasattr(self.circuit.nets, "values"):
            nets_to_process = self.circuit.nets.values()
        elif hasattr(self.circuit.nets, "__iter__"):
            nets_to_process = self.circuit.nets
        else:
            return

        for net in nets_to_process:
            net_name = getattr(net, "name", str(net)).upper()

            # Detect power supply nets
            if any(
                pattern in net_name
                for pattern in ["VCC", "VDD", "V+", "+5V", "+3V3", "+12V"]
            ):
                voltage = self._extract_voltage_from_net_name(net_name)
                if voltage:
                    power_nets.append((getattr(net, "name", str(net)), voltage))
            elif "VIN" in net_name or "VSUPPLY" in net_name:
                # Default supply voltage for VIN
                power_nets.append((getattr(net, "name", str(net)), 5.0))

        # Add voltage sources
        for i, (net_name, voltage) in enumerate(power_nets):
            source_name = f"V_supply_{i+1}"
            spice_node = self.node_map.get(net_name, net_name)
            self.spice_circuit.V(
                source_name, spice_node, self.spice_circuit.gnd, voltage @ u_V
            )
            logger.debug(f"Added voltage source {source_name}: {voltage}V")

    def _extract_voltage_from_net_name(self, net_name: str) -> Optional[float]:
        """Extract voltage value from net name (e.g., '+5V' -> 5.0)."""
        # Look for voltage patterns
        patterns = [
            r"\+?([0-9.]+)V",  # +5V, 3.3V, etc.
            r"VCC_?([0-9.]+)",  # VCC_5, VCC5, etc.
            r"VDD_?([0-9.]+)",  # VDD_3, VDD3, etc.
        ]

        for pattern in patterns:
            match = re.search(pattern, net_name.upper())
            if match:
                try:
                    return float(match.group(1))
                except ValueError:
                    continue

        return None
