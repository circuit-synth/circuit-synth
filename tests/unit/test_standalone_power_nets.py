#!/usr/bin/env python3
"""
Unit tests for standalone power nets (Issue #458).

Tests that power nets without any component connections still generate
power symbols in the KiCad schematic.

Issue: https://github.com/circuit-synth/circuit-synth/issues/458
"""

import json
import re
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from circuit_synth import Net, circuit


class TestStandalonePowerNets:
    """Test that standalone power nets (no connections) still generate symbols."""

    def test_standalone_power_nets_export_to_json(self):
        """
        Standalone power nets should be exported to JSON even without connections.

        This is the first step - ensure power nets appear in the JSON intermediate format.
        """

        @circuit(name="standalone_power")
        def standalone_power():
            # Create power nets without connecting them to any components
            _3v3 = Net("3V3")
            _5v = Net("5V")
            gnd = Net("GND")
            _vdc = Net("+VDC")
            _m9v = Net("-9V")

        circ = standalone_power()

        with TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "test.json"
            circ.generate_json_netlist(str(json_path))

            assert json_path.exists()

            with open(json_path) as f:
                data = json.load(f)

            # All power nets should be in the JSON
            assert "3V3" in data["nets"], "3V3 net missing from JSON"
            assert "5V" in data["nets"], "5V net missing from JSON"
            assert "GND" in data["nets"], "GND net missing from JSON"
            assert "+VDC" in data["nets"], "+VDC net missing from JSON"
            assert "-9V" in data["nets"], "-9V net missing from JSON"

            # Each should have power net metadata
            for net_name in ["3V3", "5V", "GND", "+VDC", "-9V"]:
                net_data = data["nets"][net_name]
                assert isinstance(net_data, dict), f"{net_name} should be a dict"
                assert net_data["is_power"] is True, f"{net_name} should be power net"
                assert net_data["power_symbol"] is not None, f"{net_name} missing power_symbol"

                # Should have nodes list (even if empty)
                assert "nodes" in net_data, f"{net_name} missing nodes list"
                assert isinstance(net_data["nodes"], list), f"{net_name} nodes should be list"

    def test_standalone_power_nets_generate_symbols(self):
        """
        Standalone power nets should generate power symbols in KiCad schematic.

        Even without component connections, power nets should create visible
        power symbols in the schematic.
        """

        @circuit(name="standalone_power")
        def standalone_power():
            # Create power nets without connecting them to any components
            _3v3 = Net("3V3")
            _5v = Net("5V")
            gnd = Net("GND")
            _vdc = Net("+VDC")
            _m9v = Net("-9V")

        circ = standalone_power()

        with TemporaryDirectory() as tmpdir:
            result = circ.generate_kicad_project(
                project_name=f"{tmpdir}/standalone",
                placement_algorithm="simple",
                generate_pcb=False,
            )

            assert result["success"], f"Generation failed: {result.get('error', 'Unknown error')}"

            # Check schematic file
            sch_file = Path(tmpdir) / "standalone" / "standalone_power.kicad_sch"
            assert sch_file.exists(), f"Schematic file not found at {sch_file}"

            content = sch_file.read_text()

            # Should NOT be empty (issue #458 - was generating empty schematic)
            assert len(content) > 500, "Schematic appears to be empty or minimal"

            # Should have power symbol lib_ids
            assert 'lib_id "power:+3V3"' in content or 'lib_id "power:3V3"' in content, "Missing +3V3 power symbol"
            assert 'lib_id "power:+5V"' in content or 'lib_id "power:5V"' in content, "Missing +5V power symbol"
            assert 'lib_id "power:GND"' in content, "Missing GND power symbol"
            assert 'lib_id "power:+VDC"' in content, "Missing +VDC power symbol"
            assert 'lib_id "power:-9V"' in content, "Missing -9V power symbol"

            # Should have #PWR references
            pwr_refs = re.findall(r'reference "#PWR\d+"', content)
            assert len(pwr_refs) >= 5, f"Expected at least 5 power symbols, found {len(pwr_refs)}"

    def test_mixed_standalone_and_connected_power_nets(self):
        """
        Test that standalone power nets work alongside connected ones.

        Some power nets connected to components, some standalone.
        All should generate power symbols.
        """
        from circuit_synth import Component

        @circuit(name="mixed_power")
        def mixed_power():
            r1 = Component(
                symbol="Device:R",
                ref="R1",
                value="10k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )

            # Connected power net
            gnd = Net("GND")
            gnd += r1[2]

            # Standalone power nets
            _3v3 = Net("3V3")
            _5v = Net("5V")

        circ = mixed_power()

        with TemporaryDirectory() as tmpdir:
            result = circ.generate_kicad_project(
                project_name=f"{tmpdir}/mixed",
                placement_algorithm="simple",
                generate_pcb=False,
            )

            assert result["success"]

            sch_file = Path(tmpdir) / "mixed" / "mixed_power.kicad_sch"
            content = sch_file.read_text()

            # All three power symbols should be present
            assert 'lib_id "power:GND"' in content
            assert 'lib_id "power:+3V3"' in content or 'lib_id "power:3V3"' in content
            assert 'lib_id "power:+5V"' in content or 'lib_id "power:5V"' in content

            # Should have at least 3 power symbols (could be more if R1 connects to multiple nets)
            pwr_refs = re.findall(r'reference "#PWR\d+"', content)
            assert len(pwr_refs) >= 3


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
