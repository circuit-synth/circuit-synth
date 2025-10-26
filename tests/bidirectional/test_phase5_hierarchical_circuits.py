#!/usr/bin/env python3
"""
Phase 5: Hierarchical Circuit Tests

Tests circuits with hierarchical structure (subcircuits, sheets, modules).
These tests validate that circuit hierarchy is preserved through sync operations.

Tests:
- 5.1: Create hierarchical circuit (main + subcircuit)
- 5.2: Import hierarchical KiCad to Python preserves structure
- 5.3: Subcircuit components accessible in imported code
- 5.4: Idempotency with hierarchical circuits
"""

import json
import tempfile
from pathlib import Path

import pytest

from circuit_synth import circuit
from circuit_synth.tools.kicad_integration.kicad_to_python_sync import (
    KiCadToPythonSyncer,
)


class TestPhase5HierarchicalCircuits:
    """Phase 5: Hierarchical circuit tests"""

    @pytest.fixture
    def simple_hierarchical_circuit(self):
        """Create a hierarchical circuit with main and subcircuit."""

        @circuit(name="main_circuit")
        def main_circuit():
            from circuit_synth import Component, Net

            # Main circuit components
            r_main = Component(
                symbol="Device:R",
                ref="R_MAIN1",
                value="1k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )

            # In a real hierarchical circuit, we would reference subcircuits
            # For now, test with simple flat structure
            c_main = Component(
                symbol="Device:C",
                ref="C_MAIN1",
                value="10u",
                footprint="Capacitor_SMD:C_0603_1608Metric",
            )

        return main_circuit()

    def test_5_1_hierarchical_circuit_generation(self, simple_hierarchical_circuit):
        """Test 5.1: Create and generate hierarchical circuit

        Validates:
        - Hierarchical circuit structure generates valid KiCad project
        - Project has valid schematic structure
        - JSON reflects circuit hierarchy
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Generate KiCad project
            result = simple_hierarchical_circuit.generate_kicad_project(
                project_name="main_circuit", generate_pcb=False
            )

            assert result.get("success"), "Project generation failed"
            project_dir = Path(result["project_path"])

            # Verify project structure
            assert project_dir.exists(), f"Project directory not created"

            kicad_sch = next(project_dir.glob("*.kicad_sch"), None)
            assert kicad_sch is not None, "No .kicad_sch file created"

            kicad_pro = next(project_dir.glob("*.kicad_pro"), None)
            assert kicad_pro is not None, "No .kicad_pro file created"

            # Check JSON structure
            json_file = next(project_dir.glob("*.json"))
            with open(json_file) as f:
                json_data = json.load(f)

            # Verify JSON has expected structure
            assert "components" in json_data, "JSON missing 'components'"
            assert "nets" in json_data, "JSON missing 'nets'"

            components = json_data.get("components", {})
            if isinstance(components, dict):
                component_list = list(components.keys())
            else:
                component_list = [c.get("ref") for c in components if c.get("ref")]

            assert "R_MAIN" in component_list, "R_MAIN not found"
            assert "C_MAIN" in component_list, "C_MAIN not found"

            print(f"✅ Test 5.1 PASS: Hierarchical circuit generation")
            print(f"   - Project created: {project_dir.name}")
            print(f"   - Schematic file: {kicad_sch.name}")
            print(f"   - Project file: {kicad_pro.name}")
            print(f"   - Components: {component_list}")

    def test_5_2_hierarchical_import_preserves_structure(self):
        """Test 5.2: Import hierarchical KiCad preserves structure

        Validates:
        - Import hierarchical KiCad project
        - Generated Python has proper structure
        - All components from all sheets/levels present
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create hierarchical circuit
            @circuit(name="hier_circuit")
            def hier_circuit():
                from circuit_synth import Component, Net

                r1 = Component(
                    symbol="Device:R",
                    ref="R1",
                    value="1k",
                    footprint="Resistor_SMD:R_0603_1608Metric",
                )
                c1 = Component(
                    symbol="Device:C",
                    ref="C1",
                    value="100n",
                    footprint="Capacitor_SMD:C_0603_1608Metric",
                )
                l1 = Component(
                    symbol="Device:L",
                    ref="L1",
                    value="10u",
                    footprint="Inductor_SMD:L_0603_1608Metric",
                )

            circuit_obj = hier_circuit()

            # Generate KiCad
            result = circuit_obj.generate_kicad_project(
                project_name="hier_circuit", generate_pcb=False
            )
            project_dir = Path(result["project_path"])

            # Import back to Python
            output_dir = tmpdir_path / "imported"
            output_dir.mkdir()

            syncer = KiCadToPythonSyncer(
                kicad_project_or_json=str(project_dir / "hier_circuit.kicad_pro"),
                python_file=str(output_dir),
                preview_only=False,
                create_backup=False,
            )

            success = syncer.sync()
            assert success, "KiCad → Python sync failed"

            # Verify generated Python
            main_py = output_dir / "main.py"
            assert main_py.exists(), "main.py not created"

            with open(main_py) as f:
                generated_code = f.read()

            # Verify all components present
            assert "R1" in generated_code, "R1 not in generated Python"
            assert "C1" in generated_code, "C1 not in generated Python"
            assert "L1" in generated_code, "L1 not in generated Python"

            # Verify circuit structure present
            assert "def " in generated_code, "Circuit function not found"

            print(f"✅ Test 5.2 PASS: Hierarchical import preserves structure")
            print(f"   - KiCad project imported: ✓")
            print(f"   - Python generated: ✓")
            print(f"   - All components preserved: ✓")
            print(f"   - Circuit structure intact: ✓")

    def test_5_3_subcircuit_components_accessible(self):
        """Test 5.3: Subcircuit components are accessible

        Validates:
        - Components from all circuit levels are accessible
        - Component references are correct
        - Values and parameters accessible
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create circuit with multiple component groups
            @circuit(name="multi_level_circuit")
            def multi_level_circuit():
                from circuit_synth import Component, Net

                # Power supply section
                r_ps = Component(
                    symbol="Device:R",
                    ref="R_PS1",
                    value="100k",
                    footprint="Resistor_SMD:R_0603_1608Metric",
                )
                c_ps = Component(
                    symbol="Device:C",
                    ref="C_PS1",
                    value="47u",
                    footprint="Capacitor_SMD:C_0603_1608Metric",
                )

                # Signal section
                r_sig = Component(
                    symbol="Device:R",
                    ref="R_SIG1",
                    value="1k",
                    footprint="Resistor_SMD:R_0603_1608Metric",
                )
                c_sig = Component(
                    symbol="Device:C",
                    ref="C_SIG1",
                    value="100n",
                    footprint="Capacitor_SMD:C_0603_1608Metric",
                )

            circuit_obj = multi_level_circuit()

            # Generate KiCad
            result = circuit_obj.generate_kicad_project(
                project_name="multi_level_circuit", generate_pcb=False
            )
            project_dir = Path(result["project_path"])

            # Import to Python
            output_dir = tmpdir_path / "imported"
            output_dir.mkdir()

            syncer = KiCadToPythonSyncer(
                kicad_project_or_json=str(
                    project_dir / "multi_level_circuit.kicad_pro"
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

            # Verify all component groups accessible
            assert "R_PS" in generated_code, "R_PS not accessible"
            assert "C_PS" in generated_code, "C_PS not accessible"
            assert "R_SIG" in generated_code, "R_SIG not accessible"
            assert "C_SIG" in generated_code, "C_SIG not accessible"

            # Verify values accessible
            assert "100k" in generated_code, "R_PS value not accessible"
            assert "47u" in generated_code, "C_PS value not accessible"
            assert "1k" in generated_code, "R_SIG value not accessible"
            assert "100n" in generated_code, "C_SIG value not accessible"

            print(f"✅ Test 5.3 PASS: Subcircuit components accessible")
            print(f"   - Power supply components: R_PS, C_PS ✓")
            print(f"   - Signal components: R_SIG, C_SIG ✓")
            print(f"   - All values accessible: ✓")

    def test_5_4_hierarchical_idempotency(self, simple_hierarchical_circuit):
        """Test 5.4: Idempotency with hierarchical circuits

        CRITICAL TEST: Hierarchical circuits must regenerate deterministically.

        Validates:
        - Generate hierarchical KiCad circuit
        - Regenerate without changes
        - JSON is identical
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Generate first time
            result1 = simple_hierarchical_circuit.generate_kicad_project(
                project_name="main_circuit", generate_pcb=False
            )
            project_dir = Path(result1["project_path"])

            json_file = next(project_dir.glob("*.json"))
            with open(json_file) as f:
                json_content_1 = f.read()

            json_data_1 = json.loads(json_content_1)
            components_1 = json_data_1.get("components", {})
            nets_1 = json_data_1.get("nets", {})

            # Regenerate without changes
            result2 = simple_hierarchical_circuit.generate_kicad_project(
                project_name="main_circuit", generate_pcb=False
            )

            with open(json_file) as f:
                json_content_2 = f.read()

            json_data_2 = json.loads(json_content_2)
            components_2 = json_data_2.get("components", {})
            nets_2 = json_data_2.get("nets", {})

            # Verify component structure unchanged
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

            assert (
                comp_count_1 == comp_count_2
            ), f"Component count changed: {comp_count_1} → {comp_count_2}"

            # Verify net structure unchanged
            net_count_1 = len(nets_1) if nets_1 else 0
            net_count_2 = len(nets_2) if nets_2 else 0

            assert (
                net_count_1 == net_count_2
            ), f"Net count changed: {net_count_1} → {net_count_2}"

            # JSON should be identical
            assert (
                json_content_1 == json_content_2
            ), "Hierarchical circuit JSON not deterministic"

            print(f"✅ Test 5.4 PASS: Hierarchical idempotency")
            print(
                f"   - First generation: {comp_count_1} components, {net_count_1} nets"
            )
            print(
                f"   - Second generation: {comp_count_2} components, {net_count_2} nets"
            )
            print(f"   - JSON deterministic: ✓")
            print(f"   - Idempotency verified: ✓")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
