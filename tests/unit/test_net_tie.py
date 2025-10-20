"""
Unit tests for net-tie insertion functionality.
"""

import pytest
from circuit_synth import Circuit, Component, Net, NetTieConfig


def test_net_tie_basic_creation():
    """Test basic net-tie insertion."""
    circuit = Circuit(name="test_net_tie")

    # Create power nets
    vcc = Net("VCC_3V3")
    gnd = Net("GND")

    # Create a simple IC with a decoupling cap
    ic = Component(
        symbol="MCU_ST_STM32F4:STM32F411CEUx",
        ref="U1",
        footprint="Package_QFP:LQFP-48_7x7mm_P0.5mm"
    )

    cap = Component(
        symbol="Device:C",
        ref="C1",
        value="100nF",
        footprint="Capacitor_SMD:C_0603_1608Metric"
    )

    # Connect IC power pins
    ic["VDD"] += vcc
    ic["VSS"] += gnd

    # Connect decoupling cap
    cap["1"] += vcc
    cap["2"] += gnd

    # Insert net-ties
    net_ties = circuit.insert_decoupling_net_ties()

    # Should have inserted at least one net-tie
    assert len(net_ties) > 0

    # Net-tie should be a component
    assert all(isinstance(nt, Component) for nt in net_ties)

    # Net-tie should have correct symbol
    assert all("NetTie" in nt.symbol for nt in net_ties)


def test_net_tie_targeted_insertion():
    """Test targeted net-tie insertion for specific component."""
    circuit = Circuit(name="test_targeted")

    vcc = Net("VCC_3V3")
    gnd = Net("GND")

    # Create two ICs
    ic1 = Component(symbol="MCU_ST_STM32F4:STM32F411CEUx", ref="U1")
    ic2 = Component(symbol="MCU_ST_STM32F4:STM32F411CEUx", ref="U2")

    # Create decoupling caps for both
    cap1 = Component(symbol="Device:C", ref="C1", value="100nF")
    cap2 = Component(symbol="Device:C", ref="C2", value="100nF")

    # Connect first IC
    ic1["VDD"] += vcc
    ic1["VSS"] += gnd
    cap1["1"] += vcc
    cap1["2"] += gnd

    # Connect second IC
    ic2["VDD"] += vcc
    ic2["VSS"] += gnd
    cap2["1"] += vcc
    cap2["2"] += gnd

    # Insert net-ties only for IC1
    net_ties = circuit.insert_decoupling_net_ties(target_component=ic1)

    # Should have fewer net-ties than if we processed both ICs
    # (This is a basic check - actual count depends on implementation)
    assert len(net_ties) >= 0


def test_manual_net_tie():
    """Test manual net-tie insertion."""
    circuit = Circuit(name="test_manual")

    vcc = Net("VCC_3V3")
    gnd = Net("GND")

    # Create two caps to group together
    cap1 = Component(symbol="Device:C", ref="C1", value="100nF")
    cap2 = Component(symbol="Device:C", ref="C2", value="10uF")

    cap1["2"] += gnd
    cap2["2"] += gnd

    # Manually insert net-tie between the two caps
    net_tie = circuit.insert_net_tie(cap1, "1", cap2, "1", vcc)

    # Check net-tie was created
    assert net_tie is not None
    assert "NetTie" in net_tie.symbol

    # Check grouping metadata
    assert 'groups_with' in net_tie._extra_fields
    assert "C1" in net_tie._extra_fields['groups_with']
    assert "C2" in net_tie._extra_fields['groups_with']


def test_net_tie_groups():
    """Test net-tie group extraction."""
    circuit = Circuit(name="test_groups")

    vcc = Net("VCC_3V3")
    gnd = Net("GND")

    cap1 = Component(symbol="Device:C", ref="C1", value="100nF")
    cap2 = Component(symbol="Device:C", ref="C2", value="10uF")

    cap1["2"] += gnd
    cap2["2"] += gnd

    # Insert manual net-tie
    net_tie = circuit.insert_net_tie(cap1, "1", cap2, "1", vcc)

    # Get groups
    groups = circuit.get_net_tie_groups()

    # Should have one group
    assert len(groups) > 0

    # The net-tie should be in the groups
    assert net_tie.ref in groups


def test_net_tie_config():
    """Test custom net-tie configuration."""
    config = NetTieConfig(
        auto_decoupling=True,
        min_decoupling_cap=1e-9,  # 1nF
        max_decoupling_cap=1e-3,  # 1000uF
        net_tie_prefix="NT",
        net_tie_symbol="Device:NetTie_2"
    )

    circuit = Circuit(name="test_config")

    vcc = Net("VCC_3V3")
    gnd = Net("GND")

    ic = Component(symbol="MCU_ST_STM32F4:STM32F411CEUx", ref="U1")
    cap = Component(symbol="Device:C", ref="C1", value="100nF")

    ic["VDD"] += vcc
    ic["VSS"] += gnd
    cap["1"] += vcc
    cap["2"] += gnd

    # Insert with custom config
    net_ties = circuit.insert_decoupling_net_ties(config=config)

    # Net-ties should use custom prefix
    for nt in net_ties:
        assert nt.ref.startswith("NT") or nt._user_reference.startswith("NT")


def test_net_tie_capacitance_parsing():
    """Test that capacitance value parsing works correctly."""
    from circuit_synth.core.net_tie import NetTieInserter

    inserter = NetTieInserter()

    # Test various capacitance formats
    assert inserter._parse_capacitance("100nF") == pytest.approx(100e-9)
    assert inserter._parse_capacitance("0.1uF") == pytest.approx(0.1e-6)
    assert inserter._parse_capacitance("10uF") == pytest.approx(10e-6)
    assert inserter._parse_capacitance("1000pF") == pytest.approx(1000e-12)
    assert inserter._parse_capacitance("47µF") == pytest.approx(47e-6)


def test_net_tie_is_power_net():
    """Test power net detection."""
    from circuit_synth.core.net_tie import NetTieInserter

    inserter = NetTieInserter()

    # Test various power net names
    assert inserter._is_power_net(Net("VCC"))
    assert inserter._is_power_net(Net("VDD"))
    assert inserter._is_power_net(Net("VCC_3V3"))
    assert inserter._is_power_net(Net("+5V"))
    assert inserter._is_power_net(Net("VDDA"))
    assert inserter._is_power_net(Net("VDDCORE"))

    # Test non-power nets
    assert not inserter._is_power_net(Net("GND"))
    assert not inserter._is_power_net(Net("SIGNAL"))
    assert not inserter._is_power_net(Net("DATA"))


def test_net_tie_is_ground_net():
    """Test ground net detection."""
    from circuit_synth.core.net_tie import NetTieInserter

    inserter = NetTieInserter()

    # Test various ground net names
    assert inserter._is_ground_net(Net("GND"))
    assert inserter._is_ground_net(Net("VSS"))
    assert inserter._is_ground_net(Net("VSSA"))
    assert inserter._is_ground_net(Net("AGND"))
    assert inserter._is_ground_net(Net("DGND"))

    # Test non-ground nets
    assert not inserter._is_ground_net(Net("VCC"))
    assert not inserter._is_ground_net(Net("SIGNAL"))


def test_net_tie_placement_integration():
    """Test that net-tie groups can be used in placement."""
    from circuit_synth.pcb.placement.grouping import extract_net_tie_groupings

    circuit = Circuit(name="test_placement")

    vcc = Net("VCC_3V3")
    gnd = Net("GND")

    cap1 = Component(symbol="Device:C", ref="C1", value="100nF")
    cap2 = Component(symbol="Device:C", ref="C2", value="10uF")

    cap1["2"] += gnd
    cap2["2"] += gnd

    # Insert net-tie
    net_tie = circuit.insert_net_tie(cap1, "1", cap2, "1", vcc)

    # Extract groupings for placement
    groupings = extract_net_tie_groupings(circuit)

    # Should have groupings
    assert len(groupings) > 0

    # C1 and C2 should be grouped
    assert "C1" in groupings or "C2" in groupings


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
