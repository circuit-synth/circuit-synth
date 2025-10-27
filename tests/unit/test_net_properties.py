#!/usr/bin/env python3
"""
Unit tests for Net class with power net, differential pair,
and physical constraint properties.
"""

import pytest
from circuit_synth import circuit, Component, Net
from circuit_synth.core.exception import CircuitSynthError


class TestPowerNetAutoDetection:
    """Test automatic power net detection."""

    @circuit(name="test_gnd_auto")
    def test_gnd_auto_detected(self):
        """GND should auto-detect as power net."""
        gnd = Net(name="GND")
        assert gnd.is_power is True
        assert gnd.power_symbol == "power:GND"
        assert gnd.name == "GND"

    @circuit(name="test_vcc_auto")
    def test_vcc_auto_detected(self):
        """VCC should auto-detect as power net."""
        vcc = Net(name="VCC")
        assert vcc.is_power is True
        assert vcc.power_symbol == "power:VCC"

    @circuit(name="test_3v3_auto")
    def test_3v3_auto_detected(self):
        """+3V3 should auto-detect as power net."""
        vcc = Net(name="+3V3")
        assert vcc.is_power is True
        assert vcc.power_symbol == "power:+3V3"

    @circuit(name="test_5v_auto")
    def test_5v_auto_detected(self):
        """+5V should auto-detect as power net."""
        vcc = Net(name="+5V")
        assert vcc.is_power is True
        assert vcc.power_symbol == "power:+5V"

    @circuit(name="test_signal_not_auto")
    def test_signal_not_auto_detected(self):
        """Regular signal net should not auto-detect."""
        signal = Net(name="DATA_OUT")
        assert signal.is_power is False
        assert signal.power_symbol is None

    @circuit(name="test_usb_not_auto")
    def test_usb_not_auto_detected(self):
        """USB nets should not auto-detect as power."""
        usb_dp = Net(name="USB_DP")
        usb_dn = Net(name="USB_DN")
        assert usb_dp.is_power is False
        assert usb_dn.is_power is False


class TestPowerNetExplicitOverride:
    """Test explicit override of auto-detection."""

    @circuit(name="test_prevent_auto")
    def test_explicit_false_prevents_auto_detection(self):
        """is_power=False should prevent auto-detection."""
        gnd_sense = Net(name="GND_SENSE", is_power=False)
        assert gnd_sense.is_power is False
        assert gnd_sense.power_symbol is None

    @circuit(name="test_explicit_power")
    def test_explicit_power_net_with_symbol(self):
        """Explicit power net should work."""
        pwr = Net(name="PWR", is_power=True, power_symbol="power:VCC")
        assert pwr.is_power is True
        assert pwr.power_symbol == "power:VCC"

    @circuit(name="test_explicit_gnd_override")
    def test_explicit_override_even_for_gnd(self):
        """Can explicitly override even for GND."""
        gnd_signal = Net(name="GND", is_power=False)
        assert gnd_signal.is_power is False
        assert gnd_signal.power_symbol is None


class TestPowerNetValidation:
    """Test power net validation rules."""

    @circuit(name="test_power_needs_symbol")
    def test_power_net_requires_symbol(self):
        """Power net without symbol should raise error."""
        with pytest.raises(CircuitSynthError, match="requires power_symbol"):
            Net(name="CUSTOM_PWR", is_power=True)

    @circuit(name="test_power_with_symbol_ok")
    def test_power_net_with_symbol_valid(self):
        """Power net with symbol should be valid."""
        pwr = Net(name="CUSTOM_PWR", is_power=True, power_symbol="power:VCC")
        assert pwr.is_power is True
        assert pwr.power_symbol == "power:VCC"


class TestDifferentialPairNaming:
    """Test differential pair naming conventions (KiCad auto-detection)."""

    @circuit(name="test_diff_naming")
    def test_differential_pair_naming_convention(self):
        """Differential pairs use KiCad naming conventions."""
        # KiCad detects these as differential pairs by name
        usb_dp = Net(name="USB_DP", impedance=90)
        usb_dn = Net(name="USB_DN", impedance=90)

        # Just regular nets with impedance constraint
        assert usb_dp.impedance == 90
        assert usb_dn.impedance == 90

    @circuit(name="test_diff_plus_minus")
    def test_differential_pair_plus_minus_naming(self):
        """Test +/- naming convention."""
        eth_tx_p = Net(name="ETH_TX+", impedance=100)
        eth_tx_n = Net(name="ETH_TX-", impedance=100)

        assert eth_tx_p.name == "ETH_TX+"
        assert eth_tx_n.name == "ETH_TX-"


class TestPhysicalConstraints:
    """Test physical constraint properties."""

    @circuit(name="test_trace_current_valid")
    def test_trace_current_valid(self):
        """Valid trace current should be stored."""
        net = Net(name="POWER", trace_current=2000)
        assert net.trace_current == 2000

    @circuit(name="test_trace_current_negative")
    def test_trace_current_must_be_positive(self):
        """Trace current must be positive."""
        with pytest.raises(CircuitSynthError, match="trace_current must be positive"):
            Net(name="POWER", trace_current=-100)

    @circuit(name="test_trace_current_zero")
    def test_trace_current_cannot_be_zero(self):
        """Trace current cannot be zero."""
        with pytest.raises(CircuitSynthError, match="trace_current must be positive"):
            Net(name="POWER", trace_current=0)

    @circuit(name="test_impedance_valid")
    def test_impedance_valid(self):
        """Valid impedance should be stored."""
        net = Net(name="RF", impedance=50)
        assert net.impedance == 50

    @circuit(name="test_impedance_negative")
    def test_impedance_must_be_positive(self):
        """Impedance must be positive."""
        with pytest.raises(CircuitSynthError, match="impedance must be positive"):
            Net(name="RF", impedance=-50)

    @circuit(name="test_impedance_zero")
    def test_impedance_cannot_be_zero(self):
        """Impedance cannot be zero."""
        with pytest.raises(CircuitSynthError, match="impedance must be positive"):
            Net(name="RF", impedance=0)

    @circuit(name="test_both_constraints")
    def test_both_constraints_valid(self):
        """Both constraints can be set together."""
        net = Net(name="POWER", trace_current=2000, impedance=50)
        assert net.trace_current == 2000
        assert net.impedance == 50


class TestCustomProperties:
    """Test custom properties extension."""

    @circuit(name="test_custom_props")
    def test_custom_properties_stored(self):
        """Custom properties should be stored in properties dict."""
        net = Net(
            name="RF",
            impedance=50,
            substrate_height=1.6,
            dielectric_constant=4.5,
            is_test_point_required=True
        )
        assert net.impedance == 50  # Regular parameter
        assert net.properties["substrate_height"] == 1.6
        assert net.properties["dielectric_constant"] == 4.5
        assert net.properties["is_test_point_required"] is True

    @circuit(name="test_multiple_custom")
    def test_multiple_custom_properties(self):
        """Multiple custom properties should work."""
        net = Net(
            name="SIGNAL",
            prop1="value1",
            prop2=42,
            prop3=True,
            prop4=[1, 2, 3]
        )
        assert net.properties["prop1"] == "value1"
        assert net.properties["prop2"] == 42
        assert net.properties["prop3"] is True
        assert net.properties["prop4"] == [1, 2, 3]


class TestBackwardCompatibility:
    """Test backward compatibility with existing code."""

    @circuit(name="test_old_style")
    def test_old_net_creation_still_works(self):
        """Old Net(name="signal") usage should still work."""
        signal = Net(name="CLK")
        assert signal.name == "CLK"
        assert signal.is_power is False
        assert signal.trace_current is None
        assert signal.impedance is None
        assert signal.properties == {}

    @circuit(name="test_unnamed_net")
    def test_unnamed_net_works(self):
        """Net without name should work (auto-generated name)."""
        net = Net()
        # Net name is auto-generated (e.g., N$1)
        assert net.name is not None
        assert net.name.startswith("N$")
        assert net.is_power is False


class TestNetRepr:
    """Test Net string representation."""

    @circuit(name="test_repr_simple")
    def test_simple_net_repr(self):
        """Simple net should have simple repr."""
        net = Net(name="DATA")
        repr_str = repr(net)
        assert "DATA" in repr_str

    @circuit(name="test_repr_power")
    def test_power_net_repr(self):
        """Power net should show power flag in repr."""
        gnd = Net(name="GND")
        repr_str = repr(gnd)
        assert "GND" in repr_str
        assert "power" in repr_str

    @circuit(name="test_repr_impedance")
    def test_impedance_net_repr(self):
        """Net with impedance should show it in repr."""
        dp = Net(name="USB_DP", impedance=90)
        repr_str = repr(dp)
        assert "USB_DP" in repr_str
        assert "90Ω" in repr_str


class TestCombinedFeatures:
    """Test combinations of features."""

    @circuit(name="test_power_with_current")
    def test_power_net_with_trace_current(self):
        """Power net can have trace current."""
        vcc = Net(name="+5V", trace_current=3000)
        assert vcc.is_power is True
        assert vcc.power_symbol == "power:+5V"
        assert vcc.trace_current == 3000

    @circuit(name="test_diff_with_impedance")
    def test_differential_with_impedance(self):
        """Differential pair nets with impedance."""
        # KiCad will detect these as diff pair by name
        dp = Net(name="USB_DP", impedance=90)
        dn = Net(name="USB_DN", impedance=90)

        assert dp.impedance == 90
        assert dn.impedance == 90

    @circuit(name="test_all_features")
    def test_all_features_together(self):
        """Can use impedance, current, and custom properties together."""
        net = Net(
            name="RF_OUT",
            impedance=50,
            trace_current=100,
            substrate_height=1.6,
            dielectric_constant=4.5
        )
        assert net.impedance == 50
        assert net.trace_current == 100
        assert net.properties["substrate_height"] == 1.6


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
