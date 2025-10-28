"""
Tests for Python → KiCad generation.

Validates that circuit-synth can generate valid KiCad schematics from Python
circuit definitions.

Manual test equivalents:
- test_01: bidirectional/01_blank_circuit
- test_03: bidirectional/03_python_to_kicad
- test_04: bidirectional/04_roundtrip (generation part)
- test_06: bidirectional/06_add_component
- test_10: bidirectional/10_generate_with_net
- test_15: bidirectional/15_complex_no_overlap
"""

import pytest
import kicad_sch_api as ksa

from fixtures.circuits import (
    blank,
    single_resistor,
    two_resistors,
    two_resistors_connected,
    voltage_regulator_led,
)
from fixtures.assertions import (
    assert_schematic_has_component,
    assert_schematic_component_count,
    assert_net_exists,
)


class TestPythonToKiCadGeneration:
    """Test Python → KiCad schematic generation."""

    def test_01_blank_circuit(self, temp_project_dir, parse_schematic):
        """
        Test: Generate blank circuit with no components.

        Validates:
        - Blank circuit generates valid KiCad schematic
        - Schematic has no components
        - Schematic file is valid and can be opened in KiCad

        Manual equivalent: tests/bidirectional/01_blank_circuit
        """
        # Generate circuit
        circuit_obj = blank()
        output_dir = temp_project_dir / "blank"
        circuit_obj.generate_kicad_project(
            project_name="blank",
            output_dir=str(output_dir)
        )

        # Verify schematic file exists
        sch_path = output_dir / "blank.kicad_sch"
        assert sch_path.exists(), "Schematic file not generated"

        # Parse and validate
        sch = parse_schematic(sch_path)
        assert_schematic_component_count(sch, 0)

        # Verify it's a valid KiCad schematic structure
        assert hasattr(sch, 'components'), "Invalid schematic structure"
        assert hasattr(sch, 'wires'), "Invalid schematic structure"

    def test_03_single_resistor(self, temp_project_dir, parse_schematic):
        """
        Test: Generate circuit with single resistor.

        Validates:
        - Single component generates correctly
        - Component has correct reference (R1)
        - Component has correct value (10k)
        - Component has correct footprint
        - Component has correct symbol

        Manual equivalent: tests/bidirectional/03_python_to_kicad
        """
        # Generate circuit
        circuit_obj = single_resistor()
        output_dir = temp_project_dir / "single_resistor"
        circuit_obj.generate_kicad_project(
            project_name="single_resistor",
            output_dir=str(output_dir)
        )

        # Parse schematic
        sch_path = output_dir / "single_resistor.kicad_sch"
        sch = parse_schematic(sch_path)

        # Validate component
        assert_schematic_component_count(sch, 1)
        assert_schematic_has_component(
            sch,
            ref="R1",
            value="10k",
            footprint="Resistor_SMD:R_0603_1608Metric",
            symbol="Device:R"
        )

    def test_04_two_resistors(self, temp_project_dir, parse_schematic):
        """
        Test: Generate circuit with two resistors.

        Validates:
        - Multiple components generate correctly
        - Each component has distinct reference
        - Component properties preserved
        - Components don't overlap

        Manual equivalent: tests/bidirectional/04_roundtrip (initial generation)
        """
        # Generate circuit
        circuit_obj = two_resistors()
        output_dir = temp_project_dir / "two_resistors"
        circuit_obj.generate_kicad_project(
            project_name="two_resistors",
            output_dir=str(output_dir)
        )

        # Parse schematic
        sch_path = output_dir / "two_resistors.kicad_sch"
        sch = parse_schematic(sch_path)

        # Validate components
        assert_schematic_component_count(sch, 2)
        assert_schematic_has_component(
            sch, ref="R1", value="10k",
            footprint="Resistor_SMD:R_0603_1608Metric"
        )
        assert_schematic_has_component(
            sch, ref="R2", value="4.7k",
            footprint="Resistor_SMD:R_0603_1608Metric"
        )

        # Verify components don't overlap (positions are different)
        r1 = sch.components.get("R1")
        r2 = sch.components.get("R2")
        assert r1.position != r2.position, "Components overlap"

    def test_10_generate_with_net(self, temp_project_dir, parse_schematic):
        """
        Test: Generate circuit with net connections.

        Validates:
        - Net connections generate correctly
        - Wires created between connected pins
        - Labels created for net names
        - Components connected via named net

        Manual equivalent: tests/bidirectional/10_generate_with_net
        """
        # Generate circuit
        circuit_obj = two_resistors_connected()
        output_dir = temp_project_dir / "two_resistors_connected"
        circuit_obj.generate_kicad_project(
            project_name="two_resistors_connected",
            output_dir=str(output_dir)
        )

        # Parse schematic
        sch_path = output_dir / "two_resistors_connected.kicad_sch"
        sch = parse_schematic(sch_path)

        # Validate components
        assert_schematic_component_count(sch, 2)

        # Validate net exists
        assert_net_exists(sch, "NET1")

        # Validate wires exist (at least some connections)
        wires = list(sch.wires)
        assert len(wires) > 0, "No wires generated for net connection"

    def test_15_complex_circuit(self, temp_project_dir, parse_schematic):
        """
        Test: Generate complex circuit with multiple components and nets.

        Validates:
        - Complex circuits generate correctly
        - Multiple component types supported
        - Multiple nets handled correctly
        - Component placement avoids overlaps

        Manual equivalent: tests/bidirectional/15_complex_no_overlap
        """
        # Generate circuit
        circuit_obj = voltage_regulator_led()
        output_dir = temp_project_dir / "voltage_regulator_led"
        circuit_obj.generate_kicad_project(
            project_name="voltage_regulator_led",
            output_dir=str(output_dir)
        )

        # Parse schematic
        sch_path = output_dir / "voltage_regulator_led.kicad_sch"
        sch = parse_schematic(sch_path)

        # Validate components
        assert_schematic_component_count(sch, 5)  # 2 caps, 1 reg, 1 resistor, 1 LED

        # Validate specific components
        assert_schematic_has_component(sch, ref="C1", value="100nF")
        assert_schematic_has_component(sch, ref="C2", value="100nF")
        assert_schematic_has_component(sch, ref="U1", value="LM7805")
        assert_schematic_has_component(sch, ref="R1", value="1k")
        assert_schematic_has_component(sch, ref="D1", value="LED")

        # Validate nets exist
        assert_net_exists(sch, "VIN")
        assert_net_exists(sch, "GND")
        assert_net_exists(sch, "VOUT")
        assert_net_exists(sch, "LED")

    def test_project_files_generated(self, temp_project_dir):
        """
        Test: Verify all KiCad project files are generated.

        Validates:
        - .kicad_pro file created
        - .kicad_sch file created
        - .kicad_pcb file created (if generate_pcb=True)
        - Project structure is valid

        Manual equivalent: All tests
        """
        # Generate circuit
        circuit_obj = single_resistor()
        output_dir = temp_project_dir / "project_test"
        circuit_obj.generate_kicad_project(
            project_name="project_test",
            output_dir=str(output_dir),
            generate_pcb=True
        )

        # Verify project file
        assert (output_dir / "project_test.kicad_pro").exists(), \
            "KiCad project file not generated"

        # Verify schematic file
        assert (output_dir / "project_test.kicad_sch").exists(), \
            "KiCad schematic file not generated"

        # Verify PCB file
        assert (output_dir / "project_test.kicad_pcb").exists(), \
            "KiCad PCB file not generated"

    def test_schematic_opens_in_kicad_api(self, temp_project_dir, parse_schematic):
        """
        Test: Verify generated schematic can be opened with kicad-sch-api.

        Validates:
        - Generated files are valid S-expressions
        - kicad-sch-api can parse generated files
        - No parsing errors

        Manual equivalent: All tests (manual opening in KiCad)
        """
        # Generate circuit
        circuit_obj = single_resistor()
        output_dir = temp_project_dir / "parse_test"
        circuit_obj.generate_kicad_project(
            project_name="parse_test",
            output_dir=str(output_dir)
        )

        # Parse schematic - should not raise exception
        sch_path = output_dir / "parse_test.kicad_sch"
        sch = parse_schematic(sch_path)

        # Verify basic structure
        assert sch is not None
        assert hasattr(sch, 'components')
        assert hasattr(sch, 'wires')
        assert hasattr(sch, 'labels')

    def test_component_properties_preserved(self, temp_project_dir, parse_schematic):
        """
        Test: Verify all component properties are preserved in generation.

        Validates:
        - Reference designator preserved
        - Value preserved
        - Footprint preserved
        - Symbol/lib_id preserved
        - Additional properties preserved

        Manual equivalent: tests/bidirectional/04_roundtrip
        """
        # Generate circuit
        circuit_obj = single_resistor()
        output_dir = temp_project_dir / "properties_test"
        circuit_obj.generate_kicad_project(
            project_name="properties_test",
            output_dir=str(output_dir)
        )

        # Parse and verify
        sch_path = output_dir / "properties_test.kicad_sch"
        sch = parse_schematic(sch_path)

        comp = sch.components.get("R1")
        assert comp is not None, "Component not found"

        # Verify all key properties
        assert comp.reference == "R1"
        assert comp.value == "10k"
        assert comp.footprint == "Resistor_SMD:R_0603_1608Metric"
        assert comp.lib_id == "Device:R"

        # Verify component has standard KiCad properties
        assert hasattr(comp, 'position')
        assert hasattr(comp, 'properties')

    def test_multiple_generation_cycles(self, temp_project_dir, parse_schematic):
        """
        Test: Verify circuit can be generated multiple times without errors.

        Validates:
        - Regeneration works correctly
        - Files can be overwritten
        - No corruption on regeneration

        Manual equivalent: tests/bidirectional/14_incremental_growth
        """
        output_dir = temp_project_dir / "regen_test"

        # First generation
        circuit_obj1 = single_resistor()
        circuit_obj1.generate_kicad_project(
            project_name="regen_test",
            output_dir=str(output_dir)
        )

        sch_path = output_dir / "regen_test.kicad_sch"
        sch1 = parse_schematic(sch_path)
        assert_schematic_component_count(sch1, 1)

        # Second generation (same circuit)
        circuit_obj2 = single_resistor()
        circuit_obj2.generate_kicad_project(
            project_name="regen_test",
            output_dir=str(output_dir)
        )

        sch2 = parse_schematic(sch_path)
        assert_schematic_component_count(sch2, 1)

        # Verify component still correct
        assert_schematic_has_component(
            sch2, ref="R1", value="10k",
            footprint="Resistor_SMD:R_0603_1608Metric"
        )
