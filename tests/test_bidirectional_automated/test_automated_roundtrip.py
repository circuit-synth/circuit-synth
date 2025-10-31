"""
Tests for round-trip consistency (Python → KiCad → Python).

Validates that circuit data is preserved through full round-trip cycles.

Manual test equivalents:
- test_04: bidirectional/04_roundtrip
- test_14: bidirectional/14_incremental_growth
"""

import pytest
import kicad_sch_api as ksa

from circuit_synth.kicad.importer import import_kicad_project
from fixtures.circuits import single_resistor, two_resistors, two_resistors_connected
from fixtures.assertions import assert_roundtrip_preserves_components


class TestRoundTripConsistency:
    """Test Python → KiCad → Python round-trip consistency."""

    def test_04_simple_roundtrip(self, temp_project_dir):
        """
        Test: Single resistor round-trip preserves all properties.

        Workflow:
        1. Create circuit in Python
        2. Generate KiCad project
        3. Import KiCad project back to Python
        4. Verify all properties preserved

        Validates:
        - Component count preserved
        - Component references preserved
        - Component values preserved
        - Component footprints preserved
        - Component symbols preserved

        Manual equivalent: tests/bidirectional/04_roundtrip
        """
        # Step 1: Create original circuit
        original_circuit = single_resistor()

        # Step 2: Generate KiCad
        output_dir = temp_project_dir / "roundtrip_test"
        original_circuit.generate_kicad_project(
            project_name=str(output_dir)
        )

        # Step 3: Import back to Python
        project_file = output_dir / "roundtrip_test.kicad_pro"
        imported_circuit = import_kicad_project(str(project_file))

        # Step 4: Verify properties preserved
        assert_roundtrip_preserves_components(original_circuit, imported_circuit)

    def test_04_two_resistors_roundtrip(self, temp_project_dir):
        """
        Test: Multiple component round-trip.

        Validates:
        - Multiple components preserved
        - Each component's properties preserved
        - Component order doesn't matter

        Manual equivalent: tests/bidirectional/04_roundtrip (extended)
        """
        # Original circuit
        original_circuit = two_resistors()

        # Generate KiCad
        output_dir = temp_project_dir / "two_resistors_roundtrip"
        original_circuit.generate_kicad_project(
            project_name=str(output_dir)
        )

        # Import back
        project_file = output_dir / "two_resistors_roundtrip.kicad_pro"
        imported_circuit = import_kicad_project(str(project_file))

        # Verify
        assert_roundtrip_preserves_components(original_circuit, imported_circuit)

        # Additional checks for multiple components
        assert "R1" in imported_circuit.components
        assert "R2" in imported_circuit.components
        assert imported_circuit.components["R1"].value == "10k"
        assert imported_circuit.components["R2"].value == "4.7k"

    def test_04_roundtrip_with_nets(self, temp_project_dir):
        """
        Test: Round-trip with net connections.

        Validates:
        - Net connections preserved
        - Component connections maintained
        - Net names preserved

        Manual equivalent: tests/bidirectional/10_generate_with_net + roundtrip
        """
        # Original circuit with nets
        original_circuit = two_resistors_connected()

        # Generate KiCad
        output_dir = temp_project_dir / "nets_roundtrip"
        original_circuit.generate_kicad_project(
            project_name=str(output_dir)
        )

        # Import back
        project_file = output_dir / "nets_roundtrip.kicad_pro"
        imported_circuit = import_kicad_project(str(project_file))

        # Verify components preserved
        assert_roundtrip_preserves_components(original_circuit, imported_circuit)

        # Verify nets exist (if importer supports nets)
        if hasattr(imported_circuit, 'nets'):
            net_names = [net.name for net in imported_circuit.nets]
            assert "NET1" in net_names, "Net name not preserved in round-trip"

    def test_14_incremental_growth_roundtrip(self, temp_project_dir):
        """
        Test: Multiple iteration cycles preserve all data.

        Workflow:
        1. Generate circuit with R1
        2. Add R2 in KiCad
        3. Import → verify both present
        4. Add R3 in Python
        5. Generate → verify all three present

        Validates:
        - Incremental additions work
        - Previous components preserved
        - Multiple iteration cycles stable

        Manual equivalent: tests/bidirectional/14_incremental_growth
        """
        output_dir = temp_project_dir / "incremental_test"

        # Iteration 1: Start with R1
        circuit1 = single_resistor()
        circuit1.generate_kicad_project(
            project_name=str(output_dir)
        )

        # Iteration 2: Add R2 in KiCad
        sch_path = output_dir / "incremental_test.kicad_sch"
        sch = ksa.Schematic.load(str(sch_path))
        sch.components.add(
            lib_id="Device:R",
            reference="R2",
            value="4.7k",
            footprint="Resistor_SMD:R_0603_1608Metric",
            position=(150, 100)
        )
        sch.save()

        # Import after R2 added
        project_file = output_dir / "incremental_test.kicad_pro"
        circuit2 = import_kicad_project(str(project_file))

        assert len(circuit2.components) == 2, "R2 not imported"
        assert "R1" in circuit2.components
        assert "R2" in circuit2.components

        # Iteration 3: Add R3 in KiCad
        sch = ksa.Schematic.load(str(sch_path))
        sch.components.add(
            lib_id="Device:R",
            reference="R3",
            value="1k",
            footprint="Resistor_SMD:R_0603_1608Metric",
            position=(200, 100)
        )
        sch.save()

        # Import after R3 added
        circuit3 = import_kicad_project(str(project_file))

        assert len(circuit3.components) == 3, "R3 not imported"
        assert "R1" in circuit3.components, "R1 lost after R3 added"
        assert "R2" in circuit3.components, "R2 lost after R3 added"
        assert "R3" in circuit3.components, "R3 not imported"

        # Verify all values correct
        assert circuit3.components["R1"].value == "10k"
        assert circuit3.components["R2"].value == "4.7k"
        assert circuit3.components["R3"].value == "1k"

    def test_multiple_roundtrip_cycles(self, temp_project_dir):
        """
        Test: Multiple round-trip cycles maintain data integrity.

        Workflow:
        1. Python → KiCad → Python (cycle 1)
        2. Python → KiCad → Python (cycle 2)
        3. Python → KiCad → Python (cycle 3)

        Validates:
        - Data doesn't degrade over multiple cycles
        - No accumulation of errors
        - Stable representation

        Manual equivalent: Extension of tests/bidirectional/04_roundtrip
        """
        output_dir = temp_project_dir / "multi_roundtrip"

        # Original
        original_circuit = single_resistor()

        # Cycle 1
        original_circuit.generate_kicad_project(
            project_name=str(output_dir)
        )
        project_file = output_dir / "multi_roundtrip.kicad_pro"
        cycle1 = import_kicad_project(str(project_file))

        assert_roundtrip_preserves_components(original_circuit, cycle1)

        # Cycle 2: Re-generate from imported circuit
        cycle1.generate_kicad_project(
            project_name=str(output_dir)
        )
        cycle2 = import_kicad_project(str(project_file))

        assert_roundtrip_preserves_components(original_circuit, cycle2)
        assert_roundtrip_preserves_components(cycle1, cycle2)

        # Cycle 3: One more time
        cycle2.generate_kicad_project(
            project_name=str(output_dir)
        )
        cycle3 = import_kicad_project(str(project_file))

        assert_roundtrip_preserves_components(original_circuit, cycle3)
        assert_roundtrip_preserves_components(cycle2, cycle3)

        # Final verification: component still intact
        assert "R1" in cycle3.components
        assert cycle3.components["R1"].value == "10k"
        assert cycle3.components["R1"].footprint == "Resistor_SMD:R_0603_1608Metric"
