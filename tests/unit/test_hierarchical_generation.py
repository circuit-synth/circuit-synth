"""
Unit tests for hierarchical circuit generation (Issue #539).

Tests that hierarchical circuits properly generate:
- Main schematic file
- All subcircuit .kicad_sch files
- Components in correct subcircuit files
- Proper hierarchical structure and UUIDs
"""

import shutil
import tempfile
from pathlib import Path

import pytest

from circuit_synth import Component, Net, circuit


class TestHierarchicalGeneration:
    """Test hierarchical circuit file generation."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test projects."""
        test_dir = tempfile.mkdtemp()
        yield Path(test_dir)
        shutil.rmtree(test_dir)

    def test_basic_hierarchical_files_created(self, temp_dir):
        """Test that basic hierarchical circuit creates all expected files.

        This is the core regression test for Issue #539.
        """
        @circuit(name="power_supply")
        def power_supply(vin, vout, gnd):
            """Simple power supply subcircuit."""
            C1 = Component("Device:C", ref="C", value="10uF")
            C2 = Component("Device:C", ref="C", value="100nF")
            C1[1] += vin
            C1[2] += gnd
            C2[1] += vout
            C2[2] += gnd

        @circuit(name="main_circuit")
        def main_circuit():
            """Main circuit with one subcircuit."""
            VIN = Net("VIN")
            VOUT = Net("VOUT")
            GND = Net("GND")
            power_supply(VIN, VOUT, GND)

        # Generate KiCad project
        project_path = temp_dir / "test_basic_hierarchical"
        circuit_instance = main_circuit()
        circuit_instance.generate_kicad_project(
            str(project_path),
            force_regenerate=True
        )

        # Verify all files were created
        main_sch = project_path / "main_circuit.kicad_sch"
        power_sch = project_path / "power_supply.kicad_sch"

        assert main_sch.exists(), "Main schematic file should be created"
        assert power_sch.exists(), "Subcircuit schematic file should be created (Issue #539)"

        # Verify files have content
        assert main_sch.stat().st_size > 0, "Main schematic should have content"
        assert power_sch.stat().st_size > 0, "Subcircuit schematic should have content"

    def test_multiple_subcircuits(self, temp_dir):
        """Test circuit with multiple different subcircuits."""
        @circuit(name="power")
        def power(vin, vout, gnd):
            C = Component("Device:C", ref="C", value="10uF")
            C[1] += vin
            C[2] += gnd

        @circuit(name="led_driver")
        def led_driver(vcc, gnd):
            R = Component("Device:R", ref="R", value="330")
            R[1] += vcc
            R[2] += gnd

        @circuit(name="top")
        def top():
            VCC = Net("VCC")
            GND = Net("GND")
            power(VCC, VCC, GND)
            led_driver(VCC, GND)

        project_path = temp_dir / "test_multiple"
        top().generate_kicad_project(str(project_path), force_regenerate=True)

        # All three schematic files should exist
        assert (project_path / "top.kicad_sch").exists()
        assert (project_path / "power.kicad_sch").exists()
        assert (project_path / "led_driver.kicad_sch").exists()

    def test_subcircuit_components_included(self, temp_dir):
        """Test that subcircuit components are actually in the subcircuit file."""
        @circuit(name="subcircuit")
        def subcircuit(a, b):
            R1 = Component("Device:R", ref="R", value="1k")
            R2 = Component("Device:R", ref="R", value="2k")
            R3 = Component("Device:R", ref="R", value="3k")
            R1[1] += a
            R1[2] += R2[1]
            R2[2] += R3[1]
            R3[2] += b

        @circuit(name="top")
        def top():
            A = Net("A")
            B = Net("B")
            subcircuit(A, B)

        project_path = temp_dir / "test_components"
        top().generate_kicad_project(str(project_path), force_regenerate=True)

        # Read subcircuit file and verify components
        sub_file = project_path / "subcircuit.kicad_sch"
        content = sub_file.read_text()

        # Should contain all three resistor symbols
        assert content.count('(lib_id "Device:R")') == 3, \
            "Subcircuit should contain all 3 resistors"
        assert '"R1"' in content, "R1 should be in subcircuit"
        assert '"R2"' in content, "R2 should be in subcircuit"
        assert '"R3"' in content, "R3 should be in subcircuit"

    def test_nested_hierarchy(self, temp_dir):
        """Test 3-level deep hierarchy."""
        @circuit(name="leaf")
        def leaf(inp, out):
            R = Component("Device:R", ref="R", value="1k")
            R[1] += inp
            R[2] += out

        @circuit(name="branch")
        def branch(vcc, gnd):
            MID = Net("MID")
            leaf(vcc, MID)
            leaf(MID, gnd)

        @circuit(name="root")
        def root():
            VCC = Net("VCC")
            GND = Net("GND")
            branch(VCC, GND)

        project_path = temp_dir / "test_nested"
        root().generate_kicad_project(str(project_path), force_regenerate=True)

        # All three levels should have files
        assert (project_path / "root.kicad_sch").exists()
        assert (project_path / "branch.kicad_sch").exists()
        assert (project_path / "leaf.kicad_sch").exists()

    def test_empty_subcircuit(self, temp_dir):
        """Test subcircuit with no components (edge case)."""
        @circuit(name="empty_sub")
        def empty_sub(a, b):
            # No components, just pass-through
            pass

        @circuit(name="main")
        def main():
            A = Net("A")
            B = Net("B")
            empty_sub(A, B)

        project_path = temp_dir / "test_empty"
        main().generate_kicad_project(str(project_path), force_regenerate=True)

        # Even empty subcircuit should create a file
        sub_file = project_path / "empty_sub.kicad_sch"
        assert sub_file.exists(), "Empty subcircuit should still create .kicad_sch file"

        # Should be valid KiCad format with no symbols
        content = sub_file.read_text()
        assert "(kicad_sch" in content
        assert content.count("(symbol") == 0  # No component symbols

    def test_hierarchical_sheet_uuids(self, temp_dir):
        """Test that hierarchical sheets have proper UUIDs."""
        @circuit(name="sub")
        def sub(a, b):
            R = Component("Device:R", ref="R", value="1k")
            R[1] += a
            R[2] += b

        @circuit(name="main")
        def main():
            A = Net("A")
            B = Net("B")
            sub(A, B)

        project_path = temp_dir / "test_uuids"
        main().generate_kicad_project(str(project_path), force_regenerate=True)

        # Read main file and check for sheet reference
        main_file = project_path / "main.kicad_sch"
        main_content = main_file.read_text()

        # Should have a sheet element with uuid
        assert "(sheet" in main_content, "Main schematic should have sheet element"
        assert "(uuid" in main_content, "Sheet should have UUID"

        # Read subcircuit and check it has its own uuid
        sub_file = project_path / "sub.kicad_sch"
        sub_content = sub_file.read_text()
        assert "(uuid" in sub_content, "Subcircuit should have UUID"

    def test_multiple_instances_same_subcircuit(self, temp_dir):
        """Test using the same subcircuit multiple times."""
        @circuit(name="resistor_pair")
        def resistor_pair(a, b):
            R1 = Component("Device:R", ref="R", value="1k")
            R2 = Component("Device:R", ref="R", value="2k")
            R1[1] += a
            R1[2] += R2[1]
            R2[2] += b

        @circuit(name="main")
        def main():
            VCC = Net("VCC")
            MID = Net("MID")
            GND = Net("GND")
            # Use same subcircuit twice
            resistor_pair(VCC, MID)
            resistor_pair(MID, GND)

        project_path = temp_dir / "test_instances"
        main().generate_kicad_project(str(project_path), force_regenerate=True)

        # Should only create ONE subcircuit file (shared)
        sub_file = project_path / "resistor_pair.kicad_sch"
        assert sub_file.exists(), "Subcircuit file should exist"

        # Main file should reference it twice
        main_content = (project_path / "main.kicad_sch").read_text()
        sheet_count = main_content.count('(sheet')
        assert sheet_count >= 2, "Main should reference subcircuit at least twice"

    def test_hierarchical_with_different_components(self, temp_dir):
        """Test subcircuits with different component types."""
        @circuit(name="analog")
        def analog(inp, out, gnd):
            R = Component("Device:R", ref="R", value="10k")
            C = Component("Device:C", ref="C", value="100nF")
            R[1] += inp
            R[2] += C[1]
            C[1] += out
            C[2] += gnd

        @circuit(name="digital")
        def digital(data, clk):
            # Using different component types
            IC = Component("Device:R", ref="U", value="74HC74")  # Placeholder
            IC[1] += data
            IC[2] += clk

        @circuit(name="mixed")
        def mixed():
            IN = Net("IN")
            OUT = Net("OUT")
            GND = Net("GND")
            DATA = Net("DATA")
            CLK = Net("CLK")
            analog(IN, OUT, GND)
            digital(DATA, CLK)

        project_path = temp_dir / "test_mixed"
        mixed().generate_kicad_project(str(project_path), force_regenerate=True)

        # Verify both subcircuits created
        analog_file = project_path / "analog.kicad_sch"
        digital_file = project_path / "digital.kicad_sch"

        assert analog_file.exists()
        assert digital_file.exists()

        # Verify correct components in each
        analog_content = analog_file.read_text()
        assert '"R' in analog_content  # Resistor reference
        assert '"C' in analog_content  # Capacitor reference

        digital_content = digital_file.read_text()
        assert '"U' in digital_content  # IC reference


def count_symbol_instances(content: str) -> int:
    """
    Count symbol instances in KiCad schematic content.

    Excludes symbol definitions in lib_symbols section.
    Only counts actual component instances.
    """
    lines = content.split('\n')
    in_lib_symbols = False
    instance_count = 0
    depth = 0

    for line in lines:
        stripped = line.strip()

        # Track when we enter lib_symbols section
        if '(lib_symbols' in line:
            in_lib_symbols = True
            depth = line.count('\t')

        # Count opening symbol tags outside lib_symbols
        if '(symbol' in line and not in_lib_symbols:
            instance_count += 1

        # Track when we exit lib_symbols (when we hit closing paren at same depth)
        if in_lib_symbols and stripped == ')' and line.count('\t') == depth:
            in_lib_symbols = False

    return instance_count


class TestHierarchicalRegressions:
    """Regression tests to prevent Issue #539 from recurring."""

    @pytest.fixture
    def temp_dir(self):
        """Create temporary directory for test projects."""
        test_dir = tempfile.mkdtemp()
        yield Path(test_dir)
        shutil.rmtree(test_dir)

    def test_issue_539_subcircuit_files_generated(self, temp_dir):
        """
        Regression test for Issue #539: Hierarchical sheet .kicad_sch files not generated.

        Before fix: Only main schematic was created, subcircuits were missing.
        After fix: All subcircuit files should be created.
        """
        @circuit(name="power_supply")
        def power_supply(vin, vout, gnd):
            C1 = Component("Device:C", ref="C", value="10uF")
            C2 = Component("Device:C", ref="C", value="100nF")
            R1 = Component("Device:R", ref="R", value="10k")
            C1[1] += vin
            C1[2] += gnd
            C2[1] += vout
            C2[2] += gnd
            R1[1] += vout
            R1[2] += gnd

        @circuit(name="esp32_module")
        def esp32_module(vcc, gnd):
            C1 = Component("Device:C", ref="C", value="100nF")
            C2 = Component("Device:C", ref="C", value="10uF")
            R1 = Component("Device:R", ref="R", value="10k")
            C1[1] += vcc
            C1[2] += gnd
            C2[1] += vcc
            C2[2] += gnd
            R1[1] += vcc
            R1[2] += gnd

        @circuit(name="led_controller")
        def led_controller():
            """Main circuit with two subcircuits."""
            VIN = Net('VIN')
            VOUT_5V = Net('VOUT_5V')
            GND = Net('GND')

            # Call both subcircuits
            power_supply(VIN, VOUT_5V, GND)
            esp32_module(VOUT_5V, GND)

        # Generate project
        project_path = temp_dir / "led_controller"
        led_controller().generate_kicad_project(
            str(project_path),
            force_regenerate=True
        )

        # CRITICAL: All three files MUST exist (this was the bug)
        main_file = project_path / "led_controller.kicad_sch"
        power_file = project_path / "power_supply.kicad_sch"
        esp32_file = project_path / "esp32_module.kicad_sch"

        assert main_file.exists(), \
            "Main schematic must exist"
        assert power_file.exists(), \
            "Issue #539: power_supply.kicad_sch MUST be created"
        assert esp32_file.exists(), \
            "Issue #539: esp32_module.kicad_sch MUST be created"

        # Verify subcircuits have components (not just empty files)
        power_content = power_file.read_text()
        esp32_content = esp32_file.read_text()

        # Each subcircuit should have 3 components (count instances, not definitions)
        power_instance_count = count_symbol_instances(power_content)
        esp32_instance_count = count_symbol_instances(esp32_content)

        assert power_instance_count == 3, \
            f"power_supply should have 3 components, found {power_instance_count}"
        assert esp32_instance_count == 3, \
            f"esp32_module should have 3 components, found {esp32_instance_count}"

        # Verify valid KiCad format
        for file in [main_file, power_file, esp32_file]:
            content = file.read_text()
            assert content.startswith("(kicad_sch"), \
                f"{file.name} should be valid KiCad schematic format"
            assert "(uuid" in content, \
                f"{file.name} should have UUID"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
