#!/usr/bin/env python3
"""
Phase 9: Performance and Regression Tests

Tests that ensure sync operations maintain acceptable performance
and detect regressions.

Tests:
- 9.1: Simple circuit generation < 1 second
- 9.2: Medium circuit (20 components) < 2 seconds
- 9.3: Import operation < 3 seconds
- 9.4: JSON file size reasonable (not growing unnecessarily)
"""

import json
import tempfile
import time
from pathlib import Path

import pytest

from circuit_synth import circuit
from circuit_synth.tools.kicad_integration.kicad_to_python_sync import (
    KiCadToPythonSyncer,
)


class TestPhase9Performance:
    """Phase 9: Performance and regression tests"""

    def test_9_1_simple_generation_performance(self):
        """Test 9.1: Simple circuit generation performance

        Validates:
        - Blank circuit generates in < 1 second
        - No performance regressions
        """
        @circuit(name="perf_simple")
        def perf_simple():
            from circuit_synth import Component, Net

            r1 = Component(
                symbol="Device:R",
                ref="R1",
                value="1k",
                footprint="Resistor_SMD:R_0603_1608Metric"
            )

        circuit_obj = perf_simple()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Measure generation time
            start = time.time()
            result = circuit_obj.generate_kicad_project(
                project_name="perf_simple", generate_pcb=False
            )
            elapsed = time.time() - start

            assert result.get("success"), "Generation failed"

            # Performance assertion: should be very fast
            assert elapsed < 1.0, f"Simple generation took {elapsed:.2f}s (target: <1s)"

            project_dir = Path(result["project_path"])
            assert project_dir.exists(), "Project directory not created"

            print(f"✅ Test 9.1 PASS: Simple generation performance")
            print(f"   - Time: {elapsed:.3f}s (target: <1s)")
            print(f"   - Performance: ✓")

    def test_9_2_medium_circuit_performance(self):
        """Test 9.2: Medium circuit (20 components) generation

        Validates:
        - Circuit with ~20 components generates in < 2 seconds
        - No performance regressions with larger circuits
        """
        @circuit(name="perf_medium")
        def perf_medium():
            from circuit_synth import Component, Net

            # Create 20 components (various types)
            for i in range(1, 9):
                r = Resistor(f"R{i}", value="1k")

            for i in range(1, 7):
                c = Capacitor(f"C{i}", value="100n")

            for i in range(1, 6):
                l = Inductor(f"L{i}", value="10u")

        circuit_obj = perf_medium()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Measure generation time
            start = time.time()
            result = circuit_obj.generate_kicad_project(
                project_name="perf_medium", generate_pcb=False
            )
            elapsed = time.time() - start

            assert result.get("success"), "Generation failed"

            # Performance assertion: larger circuit should still be reasonably fast
            assert elapsed < 2.0, f"Medium generation took {elapsed:.2f}s (target: <2s)"

            project_dir = Path(result["project_path"])
            json_file = next(project_dir.glob("*.json"))

            # Verify components present
            with open(json_file) as f:
                json_data = json.load(f)

            components = json_data.get("components", {})
            comp_count = (
                len(components) if isinstance(components, dict) else len(components or [])
            )
            assert comp_count >= 18, f"Expected ~20 components, got {comp_count}"

            print(f"✅ Test 9.2 PASS: Medium circuit performance")
            print(f"   - Components: {comp_count}")
            print(f"   - Time: {elapsed:.3f}s (target: <2s)")
            print(f"   - Performance: ✓")

    def test_9_3_import_operation_performance(self):
        """Test 9.3: Import operation performance

        Validates:
        - Importing KiCad project to Python < 3 seconds
        - No performance regressions with larger imports
        """
        # Create a circuit with multiple components
        @circuit(name="perf_import")
        def perf_import():
            from circuit_synth import Component, Net

            for i in range(1, 6):
                r = Resistor(f"R{i}", value="1k")
                c = Capacitor(f"C{i}", value="100n")

        circuit_obj = perf_import()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # First generate KiCad
            result = circuit_obj.generate_kicad_project(
                project_name="perf_import", generate_pcb=False
            )
            project_dir = Path(result["project_path"])

            # Now measure import time
            output_dir = tmpdir_path / "imported"
            output_dir.mkdir()

            start = time.time()
            syncer = KiCadToPythonSyncer(
                kicad_project_or_json=str(project_dir / "perf_import.kicad_pro"),
                python_file=str(output_dir),
                preview_only=False,
                create_backup=False,
            )
            success = syncer.sync()
            elapsed = time.time() - start

            assert success, "Import failed"

            # Performance assertion
            assert elapsed < 3.0, f"Import took {elapsed:.2f}s (target: <3s)"

            # Verify output
            main_py = output_dir / "main.py"
            assert main_py.exists(), "main.py not created"

            print(f"✅ Test 9.3 PASS: Import operation performance")
            print(f"   - Time: {elapsed:.3f}s (target: <3s)")
            print(f"   - Performance: ✓")

    def test_9_4_json_file_size_reasonable(self):
        """Test 9.4: JSON file size doesn't grow unnecessarily

        Validates:
        - JSON file for simple circuit is reasonably small
        - No bloat from repeated generations
        - File size doesn't grow across cycles
        """
        @circuit(name="perf_size")
        def perf_size():
            from circuit_synth import Component, Net

            r1 = Component(
                symbol="Device:R",
                ref="R1",
                value="1k",
                footprint="Resistor_SMD:R_0603_1608Metric"
            )
            r2 = Component(
                symbol="Device:R",
                ref="R2",
                value="10k",
                footprint="Resistor_SMD:R_0603_1608Metric"
            )
            c1 = Component(
                symbol="Device:C",
                ref="C1",
                value="100n",
                footprint="Capacitor_SMD:C_0603_1608Metric"
            )

        circuit_obj = perf_size()

        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Generate multiple times and track file sizes
            sizes = []

            for i in range(3):
                result = circuit_obj.generate_kicad_project(
                    project_name="perf_size", generate_pcb=False
                )
                project_dir = Path(result["project_path"])
                json_file = next(project_dir.glob("*.json"))

                file_size = json_file.stat().st_size
                sizes.append((i + 1, file_size))

            # Verify file sizes are reasonable and don't grow
            for gen_num, size in sizes:
                print(f"   - Generation {gen_num}: {size} bytes")

                # Should be relatively small for just 3 components
                assert (
                    size < 5000
                ), f"JSON file too large: {size} bytes (target: <5KB)"

            # Verify sizes are stable (shouldn't grow)
            size_growth = sizes[-1][1] - sizes[0][1]
            assert (
                size_growth <= 10
            ), f"File size grew too much: {size_growth} bytes"

            print(f"✅ Test 9.4 PASS: JSON file size reasonable")
            print(f"   - Initial size: {sizes[0][1]} bytes")
            print(f"   - Final size: {sizes[-1][1]} bytes")
            print(f"   - Growth: {size_growth} bytes")
            print(f"   - Size reasonable: ✓")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
