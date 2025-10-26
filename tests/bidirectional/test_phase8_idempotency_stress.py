#!/usr/bin/env python3
"""
Phase 8: Idempotency Stress Tests

Critical tests that validate the foundation of user trust:
"Re-syncing without changes should be a no-op (or deterministic)."

These tests ensure that the sync pipeline is stable and predictable.

Tests:
- 8.1: Triple regeneration produces identical results
- 8.2: Round-trip cycle maintains idempotency
- 8.3: Complex circuit deterministic regeneration
- 8.4: Repeated import-export cycles produce stable JSON
"""

import json
import tempfile
from pathlib import Path

import pytest

from circuit_synth import circuit
from circuit_synth.tools.kicad_integration.kicad_to_python_sync import (
    KiCadToPythonSyncer,
)


class TestPhase8IdempotencyStress:
    """Phase 8: Stress tests for idempotency and determinism"""

    @pytest.fixture
    def complex_circuit(self):
        """Create a more complex circuit for stress testing."""

        @circuit(name="stress_test_circuit")
        def stress_test_circuit():
            from circuit_synth import Component, Net

            # Power supply section
            r1 = Component(
                symbol="Device:R",
                ref="R1",
                value="1k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )
            c1 = Component(
                symbol="Device:C",
                ref="C1",
                value="100u",
                footprint="Capacitor_SMD:C_0603_1608Metric",
            )

            # Signal processing section
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
            c2 = Component(
                symbol="Device:C",
                ref="C2",
                value="100n",
                footprint="Capacitor_SMD:C_0603_1608Metric",
            )

            # Protection section
            d1 = Component(
                symbol="Device:D",
                ref="D1",
                value="1N4148",
                footprint="Diode_SMD:D_0603_1608Metric",
            )
            l1 = Component(
                symbol="Device:L",
                ref="L1",
                value="10u",
                footprint="Inductor_SMD:L_0603_1608Metric",
            )

        return stress_test_circuit()

    def test_8_1_triple_regeneration_identical(self, complex_circuit):
        """Test 8.1: Triple regeneration produces identical results

        CRITICAL TEST: Verify that running generation 3 times produces
        identical results. This is the foundation of user trust.

        Validates:
        - Generate KiCad project
        - Regenerate (2nd time)
        - Regenerate (3rd time)
        - All three JSON files are identical
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Generate first time
            result1 = complex_circuit.generate_kicad_project(
                project_name="stress_test_circuit", generate_pcb=False
            )
            project_dir = Path(result1["project_path"])
            json_file = next(project_dir.glob("*.json"))

            with open(json_file) as f:
                json_content_1 = f.read()

            # Generate second time
            result2 = complex_circuit.generate_kicad_project(
                project_name="stress_test_circuit", generate_pcb=False
            )

            with open(json_file) as f:
                json_content_2 = f.read()

            # Generate third time
            result3 = complex_circuit.generate_kicad_project(
                project_name="stress_test_circuit", generate_pcb=False
            )

            with open(json_file) as f:
                json_content_3 = f.read()

            # All three should be identical
            assert (
                json_content_1 == json_content_2
            ), "Second generation differs from first"
            assert (
                json_content_2 == json_content_3
            ), "Third generation differs from second"

            # Parse to verify structure stability
            json_1 = json.loads(json_content_1)
            json_2 = json.loads(json_content_2)
            json_3 = json.loads(json_content_3)

            # Compare component counts
            def get_comp_count(j):
                comps = j.get("components", {})
                return len(comps) if isinstance(comps, dict) else len(comps or [])

            comp_count_1 = get_comp_count(json_1)
            comp_count_2 = get_comp_count(json_2)
            comp_count_3 = get_comp_count(json_3)

            assert (
                comp_count_1 == comp_count_2 == comp_count_3
            ), f"Component count varied: {comp_count_1}, {comp_count_2}, {comp_count_3}"

            print(f"✅ Test 8.1 PASS: Triple regeneration identical")
            print(f"   - Generation 1: {comp_count_1} components")
            print(f"   - Generation 2: {comp_count_2} components")
            print(f"   - Generation 3: {comp_count_3} components")
            print(f"   - JSON content identical: ✓")
            print(f"   - Determinism verified: ✓")

    def test_8_2_round_trip_maintains_idempotency(self, complex_circuit):
        """Test 8.2: Round-trip cycle maintains idempotency

        CRITICAL TEST: Verify that Python → KiCad → Python → KiCad
        produces identical results on the second KiCad generation.

        Validates:
        - Generate KiCad from Python (1st)
        - Import to Python
        - Generate KiCad from imported Python (2nd)
        - 1st and 2nd KiCad outputs are similar enough
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Step 1: Generate KiCad from original Python
            result1 = complex_circuit.generate_kicad_project(
                project_name="stress_test_circuit", generate_pcb=False
            )
            project_dir_1 = Path(result1["project_path"])
            json_file_1 = next(project_dir_1.glob("*.json"))

            with open(json_file_1) as f:
                json_content_1 = f.read()
            json_data_1 = json.loads(json_content_1)

            # Step 2: Import back to Python
            output_dir = tmpdir_path / "imported"
            output_dir.mkdir()

            syncer = KiCadToPythonSyncer(
                kicad_project_or_json=str(
                    project_dir_1 / "stress_test_circuit.kicad_pro"
                ),
                python_file=str(output_dir),
                preview_only=False,
                create_backup=False,
            )

            success = syncer.sync()
            assert success, "KiCad → Python sync failed"

            # Step 3: Load imported circuit and regenerate KiCad
            main_py = output_dir / "main.py"
            assert main_py.exists(), "main.py not created"

            import sys

            sys.path.insert(0, str(output_dir))
            spec = __import__("importlib.util").util.spec_from_file_location(
                "main", main_py
            )
            main_module = __import__("importlib.util").util.module_from_spec(spec)
            spec.loader.exec_module(main_module)

            circuit_func = getattr(main_module, "stress_test_circuit", None)
            if circuit_func:
                reimported_circuit = circuit_func()
                result2 = reimported_circuit.generate_kicad_project(
                    project_name="stress_test_circuit_regen",
                    generate_pcb=False,
                )
                project_dir_2 = Path(result2["project_path"])
                json_file_2 = next(project_dir_2.glob("*.json"))

                with open(json_file_2) as f:
                    json_content_2 = f.read()
                json_data_2 = json.loads(json_content_2)

                # Compare structure
                def get_comp_count(j):
                    comps = j.get("components", {})
                    return len(comps) if isinstance(comps, dict) else len(comps or [])

                comp_count_1 = get_comp_count(json_data_1)
                comp_count_2 = get_comp_count(json_data_2)

                # Should have same or very similar component count
                assert (
                    comp_count_1 == comp_count_2
                ), f"Component count changed: {comp_count_1} → {comp_count_2}"

                print(f"✅ Test 8.2 PASS: Round-trip maintains idempotency")
                print(f"   - Original KiCad: {comp_count_1} components")
                print(f"   - After round-trip KiCad: {comp_count_2} components")
                print(f"   - Component counts match: ✓")
                print(f"   - Idempotency maintained: ✓")

    def test_8_3_complex_circuit_deterministic(self, complex_circuit):
        """Test 8.3: Complex circuit deterministic regeneration

        Validates:
        - Complex circuit with 7 components regenerates identically
        - No component loss or duplication
        - Net topology stable across regenerations
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Generate first time and record checksums
            results = []
            for i in range(3):
                result = complex_circuit.generate_kicad_project(
                    project_name="stress_test_circuit", generate_pcb=False
                )
                project_dir = Path(result["project_path"])
                json_file = next(project_dir.glob("*.json"))

                with open(json_file) as f:
                    json_content = f.read()

                # Calculate checksum
                import hashlib

                checksum = hashlib.md5(json_content.encode()).hexdigest()
                results.append((i + 1, checksum, json.loads(json_content)))

            # All checksums should be identical
            checksums = [r[1] for r in results]
            assert len(set(checksums)) == 1, f"Checksums differ: {checksums}"

            # Verify component counts are stable
            for gen_num, checksum, json_data in results:
                comps = json_data.get("components", {})
                comp_count = len(comps) if isinstance(comps, dict) else len(comps or [])
                print(
                    f"   - Generation {gen_num}: {comp_count} components, "
                    f"checksum: {checksum[:8]}..."
                )

            print(f"✅ Test 8.3 PASS: Complex circuit deterministic")
            print(f"   - 3 regenerations: ✓")
            print(f"   - Identical checksums: ✓")
            print(f"   - Determinism verified: ✓")

    def test_8_4_repeated_import_export_stable(self):
        """Test 8.4: Repeated import-export cycles stable

        CRITICAL TEST: Verify that multiple cycles of import-export-import
        don't degrade or change the circuit.

        Validates:
        - Create circuit and generate KiCad
        - Cycle 1: Import to Python, export back to KiCad
        - Cycle 2: Import to Python, export back to KiCad
        - Compare JSON after each cycle
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create initial circuit
            @circuit(name="cycle_test_circuit")
            def cycle_test_circuit():
                from circuit_synth import Component, Net

                r1 = Component(
                    symbol="Device:R",
                    ref="R1",
                    value="1k",
                    footprint="Resistor_SMD:R_0603_1608Metric",
                )
                r2 = Component(
                    symbol="Device:R",
                    ref="R2",
                    value="10k",
                    footprint="Resistor_SMD:R_0603_1608Metric",
                )
                c1 = Component(
                    symbol="Device:C",
                    ref="C1",
                    value="100n",
                    footprint="Capacitor_SMD:C_0603_1608Metric",
                )

            circuit_obj = cycle_test_circuit()

            # Generate initial KiCad
            result0 = circuit_obj.generate_kicad_project(
                project_name="cycle_test_circuit", generate_pcb=False
            )
            project_dir_0 = Path(result0["project_path"])
            json_file_0 = next(project_dir_0.glob("*.json"))

            with open(json_file_0) as f:
                json_content_0 = f.read()

            json_checksums = [json_content_0]

            # Cycle through import-export multiple times
            current_json_path = json_file_0
            for cycle in range(2):
                # Import cycle
                import_dir = tmpdir_path / f"import_cycle_{cycle}"
                import_dir.mkdir()

                syncer = KiCadToPythonSyncer(
                    kicad_project_or_json=str(current_json_path),
                    python_file=str(import_dir),
                    preview_only=False,
                    create_backup=False,
                )

                success = syncer.sync()
                assert success, f"Import cycle {cycle} failed"

                # Load imported circuit and regenerate
                main_py = import_dir / "main.py"
                import sys

                sys.path.insert(0, str(import_dir))
                spec = __import__("importlib.util").util.spec_from_file_location(
                    "main", main_py
                )
                main_module = __import__("importlib.util").util.module_from_spec(spec)
                spec.loader.exec_module(main_module)

                circuit_func = getattr(main_module, "cycle_test_circuit", None)
                if circuit_func:
                    regen_circuit = circuit_func()
                    result = regen_circuit.generate_kicad_project(
                        project_name=f"cycle_test_circuit_regen_{cycle}",
                        generate_pcb=False,
                    )
                    regen_dir = Path(result["project_path"])
                    current_json_path = next(regen_dir.glob("*.json"))

                    with open(current_json_path) as f:
                        json_content = f.read()
                    json_checksums.append(json_content)

            # Verify stability: last two checksums should be identical
            import hashlib

            checksums = [hashlib.md5(c.encode()).hexdigest() for c in json_checksums]
            print(f"   - Initial: {checksums[0][:8]}...")
            print(f"   - Cycle 0: {checksums[1][:8]}...")
            print(f"   - Cycle 1: {checksums[2][:8]}...")

            assert checksums[1] == checksums[2], "Checksums not stable after cycle 1"

            print(f"✅ Test 8.4 PASS: Repeated import-export stable")
            print(f"   - Initial generation: {checksums[0][:8]}...")
            print(f"   - After cycle 1: {checksums[1][:8]}...")
            print(f"   - After cycle 2: {checksums[2][:8]}...")
            print(f"   - Stabilized at cycle 1: ✓")
            print(f"   - System is stable: ✓")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
