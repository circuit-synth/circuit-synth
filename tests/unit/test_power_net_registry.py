#!/usr/bin/env python3
"""
Unit tests for power net registry.

Tests automatic power net detection and symbol mapping.
"""

import pytest
from circuit_synth.core.power_net_registry import (
    PowerNetRegistry,
    is_power_net,
    get_power_symbol,
    get_all_power_nets,
)


class TestPowerNetRegistry:
    """Test PowerNetRegistry singleton functionality."""

    def test_singleton_instance(self):
        """Registry should be singleton."""
        reg1 = PowerNetRegistry()
        reg2 = PowerNetRegistry()
        assert reg1 is reg2

    def test_registry_initialized(self):
        """Registry should initialize power symbols."""
        registry = PowerNetRegistry()
        power_nets = registry.get_all_power_nets()
        assert len(power_nets) > 0
        assert "GND" in power_nets
        assert "VCC" in power_nets


class TestCommonPowerNets:
    """Test detection of common power net names."""

    def test_gnd_is_power_net(self):
        """GND should be detected as power net."""
        assert is_power_net("GND") is True
        assert get_power_symbol("GND") == "power:GND"

    def test_vcc_is_power_net(self):
        """VCC should be detected as power net."""
        assert is_power_net("VCC") is True
        assert get_power_symbol("VCC") == "power:VCC"

    def test_vdd_is_power_net(self):
        """VDD should be detected as power net."""
        assert is_power_net("VDD") is True
        assert get_power_symbol("VDD") == "power:VDD"

    def test_3v3_variants(self):
        """Test all 3.3V variants."""
        variants = ["+3V3", "3V3", "+3.3V", "3.3V"]
        for variant in variants:
            assert is_power_net(variant) is True, f"{variant} should be detected"
            assert get_power_symbol(variant) == "power:+3V3"

    def test_5v_variants(self):
        """Test all 5V variants."""
        variants = ["+5V", "5V"]
        for variant in variants:
            assert is_power_net(variant) is True
            assert get_power_symbol(variant) == "power:+5V"

    def test_12v_variants(self):
        """Test 12V variants."""
        assert is_power_net("+12V") is True
        assert is_power_net("12V") is True
        assert get_power_symbol("+12V") == "power:+12V"

    def test_negative_voltages(self):
        """Test negative voltage detection."""
        assert is_power_net("-5V") is True
        assert is_power_net("-12V") is True
        assert get_power_symbol("-12V") == "power:-12V"

    def test_special_power_nets(self):
        """Test special power nets."""
        # Only test nets that actually exist in KiCad power library
        # VBUS might not be in all versions
        special = ["VCC", "VDD"]
        for net in special:
            assert is_power_net(net) is True
            assert get_power_symbol(net) == f"power:{net}"

    def test_ground_variants(self):
        """Test ground variants."""
        grounds = ["GND", "GNDA", "GNDD", "GNDPWR", "GNDREF"]
        for gnd in grounds:
            assert is_power_net(gnd) is True
            assert get_power_symbol(gnd).startswith("power:GND")


class TestNonPowerNets:
    """Test that signal nets are NOT detected as power nets."""

    def test_signal_not_power(self):
        """Regular signal net should not be power net."""
        assert is_power_net("DATA") is False
        assert get_power_symbol("DATA") is None

    def test_usb_not_power(self):
        """USB signals should not be power nets."""
        assert is_power_net("USB_DP") is False
        assert is_power_net("USB_DN") is False

    def test_clock_not_power(self):
        """Clock signals should not be power nets."""
        assert is_power_net("CLK") is False
        assert is_power_net("XTAL1") is False

    def test_partial_match_not_power(self):
        """Partial matches should not be detected."""
        # These contain power net names but aren't power nets
        assert is_power_net("GND_SENSE") is False
        assert is_power_net("VCC_EN") is False
        assert is_power_net("VDD_GOOD") is False

    def test_similar_names_not_power(self):
        """Similar but different names should not match."""
        assert is_power_net("GRD") is False  # Not GND
        assert is_power_net("VCD") is False  # Not VCC
        assert is_power_net("3V4") is False  # Not 3V3


class TestEdgeCases:
    """Test edge cases and special conditions."""

    def test_empty_string(self):
        """Empty string should not be power net."""
        assert is_power_net("") is False
        assert get_power_symbol("") is None

    def test_case_sensitive(self):
        """Power net detection should be case-sensitive."""
        # Lowercase should NOT match (KiCad uses uppercase)
        assert is_power_net("gnd") is False
        assert is_power_net("vcc") is False

    def test_whitespace(self):
        """Whitespace should not match."""
        assert is_power_net(" GND") is False
        assert is_power_net("GND ") is False
        assert is_power_net(" GND ") is False

    def test_get_all_power_nets_returns_set(self):
        """get_all_power_nets should return a set."""
        all_nets = get_all_power_nets()
        assert isinstance(all_nets, set)
        assert len(all_nets) > 0

    def test_get_all_power_nets_contains_common(self):
        """get_all_power_nets should contain common power nets."""
        all_nets = get_all_power_nets()
        common = ["GND", "VCC", "VDD", "+3V3", "+5V"]
        for net in common:
            assert net in all_nets


class TestLowVoltagePowerNets:
    """Test low voltage power nets (1V0, 1V2, 1V8, 2V5)."""

    def test_1v0_variants(self):
        """Test 1.0V variants."""
        assert is_power_net("+1V0") is True
        assert is_power_net("1V0") is True
        assert get_power_symbol("1V0") == "power:+1V0"

    def test_1v2_variants(self):
        """Test 1.2V variants."""
        assert is_power_net("+1V2") is True
        assert is_power_net("1V2") is True

    def test_1v8_variants(self):
        """Test 1.8V variants."""
        assert is_power_net("+1V8") is True
        assert is_power_net("1V8") is True

    def test_2v5_variants(self):
        """Test 2.5V variants."""
        assert is_power_net("+2V5") is True
        assert is_power_net("2V5") is True


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
