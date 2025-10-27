#!/usr/bin/env python3
"""
Unit tests for power symbol generation in KiCad schematics.

Tests that power nets (GND, VCC, +3V3, etc.) generate power symbols
instead of hierarchical labels in the generated KiCad schematic files.
"""

import json
import re
from pathlib import Path
from tempfile import TemporaryDirectory

import pytest

from circuit_synth import Component, Net, circuit


class TestPowerSymbolGeneration:
    """Test power symbol generation for power nets."""

    def test_gnd_generates_power_symbol(self):
        """GND net should generate power:GND symbols, not hierarchical labels."""

        @circuit(name="test_gnd")
        def test_gnd():
            r1 = Component(
                symbol="Device:R",
                ref="R1",
                value="10k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            gnd = Net(name="GND")
            gnd += r1[2]

        circ = test_gnd()

        with TemporaryDirectory() as tmpdir:
            result = circ.generate_kicad_project(
                project_name=f"{tmpdir}/test_gnd",
                placement_algorithm="simple",
                generate_pcb=False,
            )

            assert result["success"]

            # Check schematic file
            sch_file = Path(tmpdir) / "test_gnd" / "test_gnd.kicad_sch"
            assert sch_file.exists()

            content = sch_file.read_text()

            # Should have power:GND lib_id
            assert 'lib_id "power:GND"' in content

            # Should have #PWR reference
            assert re.search(r'reference "#PWR\d+"', content)

            # Should NOT have hierarchical_label for GND
            assert 'hierarchical_label "GND"' not in content

    def test_vcc_generates_power_symbol(self):
        """VCC net should generate power:VCC symbols."""

        @circuit(name="test_vcc")
        def test_vcc():
            r1 = Component(
                symbol="Device:R",
                ref="R1",
                value="10k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            vcc = Net(name="VCC")
            vcc += r1[1]

        circ = test_vcc()

        with TemporaryDirectory() as tmpdir:
            result = circ.generate_kicad_project(
                project_name=f"{tmpdir}/test_vcc",
                placement_algorithm="simple",
                generate_pcb=False,
            )

            assert result["success"]

            sch_file = Path(tmpdir) / "test_vcc" / "test_vcc.kicad_sch"
            content = sch_file.read_text()

            # Should have power:VCC lib_id
            assert 'lib_id "power:VCC"' in content

            # Should have #PWR reference
            assert re.search(r'reference "#PWR\d+"', content)

            # Should NOT have hierarchical_label for VCC
            assert 'hierarchical_label "VCC"' not in content

    def test_multiple_power_nets(self):
        """Multiple power nets should all generate power symbols."""

        @circuit(name="test_multi_power")
        def test_multi_power():
            r1 = Component(
                symbol="Device:R",
                ref="R1",
                value="10k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            r2 = Component(
                symbol="Device:R",
                ref="R2",
                value="10k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )

            gnd = Net(name="GND")
            vcc = Net(name="VCC")
            v3_3 = Net(name="+3V3")

            gnd += r1[2]
            gnd += r2[2]
            vcc += r1[1]
            v3_3 += r2[1]

        circ = test_multi_power()

        with TemporaryDirectory() as tmpdir:
            result = circ.generate_kicad_project(
                project_name=f"{tmpdir}/test_multi",
                placement_algorithm="simple",
                generate_pcb=False,
            )

            assert result["success"]

            sch_file = Path(tmpdir) / "test_multi" / "test_multi.kicad_sch"
            content = sch_file.read_text()

            # Should have all three power symbols
            assert 'lib_id "power:GND"' in content
            assert 'lib_id "power:VCC"' in content
            assert 'lib_id "power:+3V3"' in content

            # Should have multiple #PWR references
            pwr_refs = re.findall(r'reference "#PWR\d+"', content)
            assert len(pwr_refs) >= 4  # At least 4 power connections

            # Should NOT have hierarchical labels for any power net
            assert 'hierarchical_label "GND"' not in content
            assert 'hierarchical_label "VCC"' not in content
            assert 'hierarchical_label "+3V3"' not in content

    def test_regular_nets_still_use_hierarchical_labels(self):
        """Non-power nets should still use hierarchical labels."""

        @circuit(name="test_mixed")
        def test_mixed():
            r1 = Component(
                symbol="Device:R",
                ref="R1",
                value="10k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            r2 = Component(
                symbol="Device:R",
                ref="R2",
                value="10k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )

            gnd = Net(name="GND")  # Power net
            signal = Net(name="DATA")  # Regular signal net

            gnd += r1[2]
            signal += r1[1]
            signal += r2[1]
            gnd += r2[2]

        circ = test_mixed()

        with TemporaryDirectory() as tmpdir:
            result = circ.generate_kicad_project(
                project_name=f"{tmpdir}/test_mixed",
                placement_algorithm="simple",
                generate_pcb=False,
            )

            assert result["success"]

            sch_file = Path(tmpdir) / "test_mixed" / "test_mixed.kicad_sch"
            content = sch_file.read_text()

            # GND should use power symbol
            assert 'lib_id "power:GND"' in content
            assert 'hierarchical_label "GND"' not in content

            # DATA should use hierarchical label
            assert 'hierarchical_label "DATA"' in content


class TestNetJSONSerialization:
    """Test that Net metadata is preserved through JSON serialization."""

    def test_power_net_serialization(self):
        """Power net attributes should be preserved in JSON."""

        @circuit(name="test_json")
        def test_json():
            r1 = Component(
                symbol="Device:R",
                ref="R1",
                value="10k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            gnd = Net(name="GND")
            gnd += r1[2]

        circ = test_json()

        with TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "test.json"
            circ.generate_json_netlist(str(json_path))

            assert json_path.exists()

            with open(json_path) as f:
                data = json.load(f)

            # Check that GND net has metadata
            assert "GND" in data["nets"]
            gnd_net = data["nets"]["GND"]

            # Should be a dict with connections and metadata
            assert isinstance(gnd_net, dict)
            assert "connections" in gnd_net
            assert "is_power" in gnd_net
            assert "power_symbol" in gnd_net

            # Verify values
            assert gnd_net["is_power"] is True
            assert gnd_net["power_symbol"] == "power:GND"

    def test_regular_net_serialization(self):
        """Regular net should serialize with is_power=False."""

        @circuit(name="test_json_signal")
        def test_json_signal():
            r1 = Component(
                symbol="Device:R",
                ref="R1",
                value="10k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            signal = Net(name="DATA")
            signal += r1[1]

        circ = test_json_signal()

        with TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "test.json"
            circ.generate_json_netlist(str(json_path))

            with open(json_path) as f:
                data = json.load(f)

            data_net = data["nets"]["DATA"]
            assert data_net["is_power"] is False
            assert data_net["power_symbol"] is None

    def test_net_with_trace_current(self):
        """Net with trace_current should serialize correctly."""

        @circuit(name="test_json_current")
        def test_json_current():
            r1 = Component(
                symbol="Device:R",
                ref="R1",
                value="10k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            power = Net(name="+5V", trace_current=2000)  # 2A
            power += r1[1]

        circ = test_json_current()

        with TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "test.json"
            circ.generate_json_netlist(str(json_path))

            with open(json_path) as f:
                data = json.load(f)

            power_net = data["nets"]["+5V"]
            assert power_net["is_power"] is True
            assert power_net["power_symbol"] == "power:+5V"
            assert power_net["trace_current"] == 2000

    def test_net_with_impedance(self):
        """Net with impedance should serialize correctly."""

        @circuit(name="test_json_impedance")
        def test_json_impedance():
            r1 = Component(
                symbol="Device:R",
                ref="R1",
                value="10k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            signal = Net(name="USB_DP", impedance=90)
            signal += r1[1]

        circ = test_json_impedance()

        with TemporaryDirectory() as tmpdir:
            json_path = Path(tmpdir) / "test.json"
            circ.generate_json_netlist(str(json_path))

            with open(json_path) as f:
                data = json.load(f)

            usb_net = data["nets"]["USB_DP"]
            assert usb_net["impedance"] == 90


class TestPowerSymbolReferences:
    """Test that power symbols get unique #PWR references."""

    def test_power_symbol_unique_references(self):
        """Each power symbol should have a unique #PWR reference."""

        @circuit(name="test_pwr_refs")
        def test_pwr_refs():
            r1 = Component(
                symbol="Device:R",
                ref="R1",
                value="10k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            r2 = Component(
                symbol="Device:R",
                ref="R2",
                value="10k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            r3 = Component(
                symbol="Device:R",
                ref="R3",
                value="10k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )

            gnd = Net(name="GND")
            gnd += r1[2]
            gnd += r2[2]
            gnd += r3[2]

        circ = test_pwr_refs()

        with TemporaryDirectory() as tmpdir:
            result = circ.generate_kicad_project(
                project_name=f"{tmpdir}/test_refs",
                placement_algorithm="simple",
                generate_pcb=False,
            )

            assert result["success"]

            sch_file = Path(tmpdir) / "test_refs" / "test_refs.kicad_sch"
            content = sch_file.read_text()

            # Extract all #PWR references
            pwr_refs = re.findall(r'reference "#PWR(\d+)"', content)

            # Should have at least 3 power symbols
            assert len(pwr_refs) >= 3

            # All references should be unique
            assert len(pwr_refs) == len(set(pwr_refs))

            # References should be sequential
            pwr_nums = sorted([int(n) for n in pwr_refs])
            assert pwr_nums == list(range(1, len(pwr_nums) + 1))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
