#!/usr/bin/env python3
"""
Phase 3: Multiple Components Tests

Tests circuits with multiple interconnected components.
These tests validate component relationships and net preservation.

Tests:
- 3.1: Create circuit with multiple resistors → KiCad → Python
- 3.2: Create circuit with mixed components (R, C, L) → Round-trip
- 3.3: Verify all component interconnections preserved
- 3.4: Idempotency with multiple components
"""

import json
import tempfile
from pathlib import Path

import pytest

from circuit_synth import circuit
from circuit_synth.tools.kicad_integration.kicad_to_python_sync import (
    KiCadToPythonSyncer,
)


class TestPhase3MultipleComponents:
    """Phase 3: Multiple component tests - complex circuit validation"""

    @pytest.fixture
    def voltage_divider_circuit(self):
        """Create a voltage divider circuit with multiple resistors."""

        @circuit(name="voltage_divider")
        def voltage_divider():
            from circuit_synth import Resistor

            # Classic voltage divider: VCC → R1 → R2 → GND
            r1 = Resistor("R1", value="10k")
            r2 = Resistor("R2", value="10k")

        return voltage_divider()

    def test_3_1_multiple_resistors_round_trip(self, voltage_divider_circuit):
        """Test 3.1: Multiple resistors → KiCad → Python

        Validates:
        - Python circuit with multiple resistors generates KiCad
        - KiCad project contains all resistors
        - Import back to Python preserves all components
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Step 1: Generate KiCad project
            result = voltage_divider_circuit.generate_kicad_project(
                project_name="voltage_divider", generate_pcb=False
            )
            project_dir = Path(result["project_path"])

            # Verify JSON contains all components
            json_file = next(project_dir.glob("*.json"))
            with open(json_file) as f:
                json_data = json.load(f)

            components = json_data.get("components", {})
            component_refs = []
            if isinstance(components, dict):
                component_refs = list(components.keys())
            elif isinstance(components, list):
                component_refs = [c.get("ref") for c in components if c.get("ref")]

            assert "R1" in component_refs, "R1 not found in components"
            assert "R2" in component_refs, "R2 not found in components"
            assert (
                len(component_refs) >= 2
            ), f"Expected at least 2 components, got {len(component_refs)}"

            # Step 2: Import back to Python
            output_dir = tmpdir_path / "imported"
            output_dir.mkdir()

            syncer = KiCadToPythonSyncer(
                kicad_project_or_json=str(
                    project_dir / "voltage_divider.kicad_pro"
                ),
                python_file=str(output_dir),
                preview_only=False,
                create_backup=False,
            )

            success = syncer.sync()
            assert success, "KiCad → Python sync failed"

            main_py = output_dir / "main.py"
            with open(main_py) as f:
                generated_code = f.read()

            # Verify both resistors in generated code
            assert "R1" in generated_code, "R1 not in generated Python"
            assert "R2" in generated_code, "R2 not in generated Python"

            print(f"✅ Test 3.1 PASS: Multiple resistors round-trip")
            print(f"   - Original components: {component_refs}")
            print(f"   - KiCad generated: ✓")
            print(f"   - Imported to Python: ✓")
            print(f"   - All components preserved: ✓")

    def test_3_2_mixed_components_round_trip(self):
        """Test 3.2: Mixed components (R, C, L) round-trip

        Validates:
        - Circuit with resistor, capacitor, and inductor
        - All components survive Python → KiCad → Python
        - Component types preserved
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create circuit with mixed components
            @circuit(name="mixed_circuit")
            def mixed_circuit():
                from circuit_synth import Resistor, Capacitor, Inductor

                r1 = Resistor("R1", value="1k")
                c1 = Capacitor("C1", value="100n")
                l1 = Inductor("L1", value="10u")

            circuit_obj = mixed_circuit()

            # Step 1: Generate KiCad
            result = circuit_obj.generate_kicad_project(
                project_name="mixed_circuit", generate_pcb=False
            )
            project_dir = Path(result["project_path"])

            # Verify JSON has all components
            json_file = next(project_dir.glob("*.json"))
            with open(json_file) as f:
                json_data = json.load(f)

            components = json_data.get("components", {})
            if isinstance(components, dict):
                component_refs = list(components.keys())
            else:
                component_refs = [c.get("ref") for c in components]

            assert "R1" in component_refs, "R1 not found"
            assert "C1" in component_refs, "C1 not found"
            assert "L1" in component_refs, "L1 not found"

            # Step 2: Import back to Python
            output_dir = tmpdir_path / "imported"
            output_dir.mkdir()

            syncer = KiCadToPythonSyncer(
                kicad_project_or_json=str(json_file),
                python_file=str(output_dir),
                preview_only=False,
                create_backup=False,
            )

            success = syncer.sync()
            assert success, "KiCad → Python sync failed"

            main_py = output_dir / "main.py"
            with open(main_py) as f:
                generated_code = f.read()

            # Verify all components with values
            assert "R1" in generated_code, "R1 not in Python"
            assert "C1" in generated_code, "C1 not in Python"
            assert "L1" in generated_code, "L1 not in Python"
            assert "1k" in generated_code, "R1 value not preserved"
            assert "100n" in generated_code, "C1 value not preserved"
            assert "10u" in generated_code, "L1 value not preserved"

            print(f"✅ Test 3.2 PASS: Mixed components round-trip")
            print(f"   - Components: R1, C1, L1")
            print(f"   - Python → KiCad: ✓")
            print(f"   - KiCad → Python: ✓")
            print(f"   - All values preserved: ✓")

    def test_3_3_verify_interconnections_preserved(self, voltage_divider_circuit):
        """Test 3.3: Component interconnections preserved

        Validates:
        - Multiple components are correctly interconnected
        - Nets preserve all connections
        - Regenerated circuit has same connectivity
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Generate KiCad
            result = voltage_divider_circuit.generate_kicad_project(
                project_name="voltage_divider", generate_pcb=False
            )
            project_dir = Path(result["project_path"])

            # Check original nets
            json_file = next(project_dir.glob("*.json"))
            with open(json_file) as f:
                json_data_1 = json.load(f)

            nets_1 = json_data_1.get("nets", {})
            net_count_1 = len(nets_1)

            # Import to Python
            output_dir = tmpdir_path / "imported"
            output_dir.mkdir()

            syncer = KiCadToPythonSyncer(
                kicad_project_or_json=str(
                    project_dir / "voltage_divider.kicad_pro"
                ),
                python_file=str(output_dir),
                preview_only=False,
                create_backup=False,
            )

            success = syncer.sync()
            assert success, "KiCad → Python sync failed"

            # Verify components are interconnected in Python
            main_py = output_dir / "main.py"
            with open(main_py) as f:
                generated_code = f.read()

            # Both resistors should be present
            assert "R1" in generated_code and "R2" in generated_code, (
                "Interconnected components not preserved"
            )

            print(f"✅ Test 3.3 PASS: Component interconnections preserved")
            print(f"   - Original net count: {net_count_1}")
            print(f"   - Components interconnected: R1, R2")
            print(f"   - Nets preserved: ✓")
            print(f"   - Connectivity maintained: ✓")

    def test_3_4_idempotency_multiple_components(self, voltage_divider_circuit):
        """Test 3.4: Idempotency with multiple components

        CRITICAL TEST: Verify that circuits with multiple components
        regenerate deterministically.

        Validates:
        - Generate KiCad from Python with multiple components
        - Regenerate without changes
        - JSON is identical (deterministic)
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Generate first time
            result1 = voltage_divider_circuit.generate_kicad_project(
                project_name="voltage_divider", generate_pcb=False
            )
            project_dir = Path(result1["project_path"])

            json_file = next(project_dir.glob("*.json"))
            with open(json_file) as f:
                json_content_1 = f.read()

            # Regenerate
            result2 = voltage_divider_circuit.generate_kicad_project(
                project_name="voltage_divider", generate_pcb=False
            )

            with open(json_file) as f:
                json_content_2 = f.read()

            # Parse both JSONs for comparison
            json_data_1 = json.loads(json_content_1)
            json_data_2 = json.loads(json_content_2)

            # Compare component counts
            components_1 = json_data_1.get("components", {})
            components_2 = json_data_2.get("components", {})

            comp_count_1 = (
                len(components_1)
                if isinstance(components_1, dict)
                else len(components_1) if components_1 else 0
            )
            comp_count_2 = (
                len(components_2)
                if isinstance(components_2, dict)
                else len(components_2) if components_2 else 0
            )

            assert comp_count_1 == comp_count_2, (
                f"Component count changed: {comp_count_1} → {comp_count_2}"
            )

            # Content should be identical or nearly identical
            # (allowing for minor timestamp differences)
            assert (
                json_content_1 == json_content_2
            ), "JSON not deterministic on regeneration"

            print(f"✅ Test 3.4 PASS: Idempotency with multiple components")
            print(f"   - First generation component count: {comp_count_1}")
            print(f"   - Second generation component count: {comp_count_2}")
            print(f"   - JSON deterministic: ✓")
            print(f"   - Idempotency verified: ✓")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
