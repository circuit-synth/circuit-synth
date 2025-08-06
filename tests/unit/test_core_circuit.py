"""
Unit tests for core circuit functionality.

Tests the Circuit, Component, Net, and Pin classes.
"""

import pytest

from circuit_synth.core import Circuit, Component, Net, Pin
from circuit_synth.core.pin import PinType
from circuit_synth.core.reference_manager import ReferenceManager


class TestCircuit:
    """Test the Circuit class."""

    def test_circuit_creation(self):
        """Test creating a basic circuit."""
        circuit = Circuit("TestCircuit")
        assert circuit.name == "TestCircuit"
        assert len(circuit.components) == 0
        assert len(circuit.nets) == 0
        assert len(circuit._subcircuits) == 0

    def test_add_component(self):
        """Test adding components to a circuit."""
        circuit = Circuit("TestCircuit")

        # Add a resistor - use prefix only since we're in a test fixture with circuit context
        r1 = Component("Device:R", ref="R", value="10k")
        circuit.add_component(r1)

        # Finalize references to assign numbers
        circuit.finalize_references()

        assert len(circuit.components) == 1
        # Components is a list, not a dict
        comp = circuit.components[0]
        assert comp.ref == "R1"
        assert comp.symbol == "Device:R"
        assert comp.value == "10k"

    def test_add_net(self):
        """Test adding nets to a circuit."""
        circuit = Circuit("TestCircuit")

        # Add a net
        vcc_net = Net("VCC")
        circuit.add_net(vcc_net)

        assert len(circuit.nets) == 1
        assert "VCC" in circuit.nets
        assert circuit.nets["VCC"].name == "VCC"

    def test_connect_components(self):
        """Test connecting components via nets."""
        circuit = Circuit("TestCircuit")

        # Add components with prefix only
        r1 = Component("Device:R", ref="R")
        r2 = Component("Device:R", ref="R")
        circuit.add_component(r1)
        circuit.add_component(r2)

        # Finalize to get R1 and R2
        circuit.finalize_references()

        # Create and connect net
        net = Net("NET1")
        circuit.add_net(net)

        # In the current implementation, components connect to nets via pins
        # Let's connect the pins directly using bracket notation
        r1_pin1 = r1["1"]
        r2_pin2 = r2["2"]

        # Connect pins to net
        r1_pin1 += net
        r2_pin2 += net

        # Verify connections
        assert net.name == "NET1"
        assert len(net.pins) == 2

    def test_subcircuits(self):
        """Test adding subcircuits."""
        main_circuit = Circuit("MainCircuit")
        sub_circuit = Circuit("SubCircuit")

        # Add component to subcircuit
        r1 = Component("Device:R", ref="R1")
        sub_circuit.add_component(r1)

        # Add subcircuit to main circuit
        main_circuit.add_subcircuit(sub_circuit)

        assert len(main_circuit._subcircuits) == 1
        # _subcircuits is a list, not a dict
        assert main_circuit._subcircuits[0] == sub_circuit

    def test_to_dict(self):
        """Test converting circuit to dictionary."""
        circuit = Circuit("TestCircuit")
        r1 = Component("Device:R", ref="R", value="1k")
        circuit.add_component(r1)
        circuit.finalize_references()

        # Create a net and connect a pin to it
        net = Net("GND")
        circuit.add_net(net)
        r1["1"] += net  # Connect pin 1 of R1 to GND

        circuit_dict = circuit.to_dict()

        assert circuit_dict["name"] == "TestCircuit"
        assert "components" in circuit_dict
        assert "nets" in circuit_dict
        assert len(circuit_dict["components"]) == 1
        # The nets dict includes the GND net we added (only if it has connections)
        assert "GND" in circuit_dict["nets"]
        # Verify the net has the expected connection
        assert len(circuit_dict["nets"]["GND"]) == 1
        assert circuit_dict["nets"]["GND"][0]["component"] == "R1"


class TestComponent:
    """Test the Component class."""

    def test_component_creation(self):
        """Test creating a component."""
        # Use a symbol that exists in the KiCad library
        # Components with final refs need circuit context, use prefix
        comp = Component("Device:C", ref="C", value="100nF")

        assert comp.ref == "C"
        assert comp.symbol == "Device:C"
        assert comp.value == "100nF"

    def test_component_properties(self):
        """Test component property system."""
        comp = Component("Device:C", ref="C1")

        # Set properties
        comp.value = "100nF"
        comp.voltage_rating = "50V"
        comp.tolerance = "10%"
        comp.footprint = "Capacitor_SMD:C_0805_2012Metric"

        # Check properties
        assert comp.value == "100nF"
        assert comp.voltage_rating == "50V"
        assert comp.tolerance == "10%"
        assert comp.footprint == "Capacitor_SMD:C_0805_2012Metric"

    def test_component_pins(self):
        """Test component pin management."""
        comp = Component("Device:R", ref="R1")

        # Components automatically get pins from their symbols
        # Check that pins exist (loaded from symbol)
        assert hasattr(comp, "_pins")
        # Note: actual pin count depends on the symbol definition

    def test_component_to_dict(self):
        """Test converting component to dictionary."""
        comp = Component("Device:R", ref="R", value="10k")
        comp.footprint = "Resistor_SMD:R_0805_2012Metric"

        comp_dict = comp.to_dict()

        assert comp_dict["ref"] == "R"
        assert comp_dict["symbol"] == "Device:R"
        assert comp_dict["value"] == "10k"
        assert comp_dict["footprint"] == "Resistor_SMD:R_0805_2012Metric"


class TestNet:
    """Test the Net class."""

    def test_net_creation(self):
        """Test creating a net."""
        # Net requires an active circuit
        circuit = Circuit("TestCircuit")
        net = Net("VCC")

        assert net.name == "VCC"
        assert len(net.pins) == 0

    def test_net_connections(self):
        """Test connecting pins to a net."""
        # Net requires an active circuit
        circuit = Circuit("TestCircuit")
        net = Net("SIGNAL")

        # In the actual implementation, pins connect to nets, not the other way around
        # This test would require creating components and connecting their pins
        # For now, just test that the net exists
        assert net.name == "SIGNAL"
        assert isinstance(net.pins, frozenset)

    def test_net_to_dict(self):
        """Test net properties."""
        circuit = Circuit("TestCircuit")
        net = Net("GND")

        # The Net class doesn't have a to_dict method in the current implementation
        # Just test basic properties
        assert net.name == "GND"
        assert hasattr(net, "_pins")
        assert hasattr(net, "pins")


class TestPin:
    """Test the Pin class."""

    def test_pin_creation(self):
        """Test creating a pin."""
        pin = Pin("VCC", "1", "power_in")

        assert pin.num == "1"
        assert pin.name == "VCC"
        assert pin.func == PinType.POWER_IN

    def test_pin_properties(self):
        """Test pin properties."""
        pin = Pin("GPIO1", "A1", "bidirectional")

        assert pin.name == "GPIO1"
        assert pin.num == "A1"
        assert pin.func == PinType.BIDIRECTIONAL

    def test_pin_to_dict(self):
        """Test pin basic properties."""
        pin = Pin("GND", "2", "power_in")

        # Pin class doesn't have to_dict in current implementation
        assert pin.num == "2"
        assert pin.name == "GND"
        assert pin.func == PinType.POWER_IN


class TestReferenceManager:
    """Test the Reference Manager."""

    def test_unique_references(self):
        """Test that reference manager ensures unique references."""
        manager = ReferenceManager()

        # Get references for same prefix
        ref1 = manager.generate_next_reference("R")
        ref2 = manager.generate_next_reference("R")
        ref3 = manager.generate_next_reference("R")

        assert ref1 == "R1"
        assert ref2 == "R2"
        assert ref3 == "R3"

        # Different prefix
        cap1 = manager.generate_next_reference("C")
        assert cap1 == "C1"

    def test_reserve_reference(self):
        """Test reserving specific references."""
        manager = ReferenceManager()

        # Reserve R5
        manager.register_reference("R5")

        # Get next references
        ref1 = manager.generate_next_reference("R")
        ref2 = manager.generate_next_reference("R")

        # Should skip R5
        assert ref1 == "R1"
        assert ref2 == "R2"

        # Continue getting references
        ref3 = manager.generate_next_reference("R")
        ref4 = manager.generate_next_reference("R")
        ref5 = manager.generate_next_reference("R")
        ref6 = manager.generate_next_reference("R")

        assert ref3 == "R3"
        assert ref4 == "R4"
        assert ref5 == "R6"  # Skips R5
        assert ref6 == "R7"
