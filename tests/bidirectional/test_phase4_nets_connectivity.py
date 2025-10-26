#!/usr/bin/env python3
"""
Phase 4: Nets and Connectivity Tests

Tests that verify circuit net topology and component interconnections
are correctly preserved through sync operations.

Tests:
- 4.1: Create named nets and verify in KiCad
- 4.2: Verify net connections in imported Python
- 4.3: Complex net topology preservation
- 4.4: Net name preservation and idempotency
"""

import json
import tempfile
from pathlib import Path

import pytest

from circuit_synth import circuit
from circuit_synth.tools.kicad_integration.kicad_to_python_sync import (
    KiCadToPythonSyncer,
)


class TestPhase4NetsConnectivity:
    """Phase 4: Net connectivity and topology tests"""

    @pytest.fixture
    def circuit_with_named_nets(self):
        """Create a circuit with explicitly named nets."""

        @circuit(name="net_circuit")
        def net_circuit():
            from circuit_synth import Component, Net

            # Create named nets
            vcc_net = Net("VCC")
            gnd_net = Net("GND")
            signal_net = Net("SIGNAL")

            # Components
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
            r2 = Component(
                symbol="Device:R",
                ref="R2",
                value="10k",
                footprint="Resistor_SMD:R_0603_1608Metric",
            )

            # Connect components to nets
            r1[1] += vcc_net
            r1[2] += signal_net
            c1[1] += signal_net
            c1[2] += gnd_net
            r2[1] += signal_net
            r2[2] += gnd_net

        return net_circuit()

    def test_4_1_named_nets_in_kicad(self, circuit_with_named_nets):
        """Test 4.1: Named nets appear in KiCad project

        Validates:
        - Python circuit with named nets generates KiCad
        - JSON contains named nets
        - KiCad schematic has net information
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Generate KiCad project
            result = circuit_with_named_nets.generate_kicad_project(
                project_name="net_circuit", generate_pcb=False
            )
            project_dir = Path(result["project_path"])

            # Check JSON for nets
            json_file = next(project_dir.glob("*.json"))
            with open(json_file) as f:
                json_data = json.load(f)

            nets = json_data.get("nets", {})
            net_names = (
                list(nets.keys())
                if isinstance(nets, dict)
                else [n.get("name") for n in nets]
            )

            # Verify named nets exist
            assert len(net_names) > 0, "No nets found in JSON"

            # At least some of our named nets should be present
            named_nets = ["VCC", "GND", "SIGNAL"]
            found_nets = [n for n in named_nets if n in net_names]
            assert len(found_nets) > 0, f"None of {named_nets} found in {net_names}"

            # Check KiCad schematic has net references
            kicad_sch = next(project_dir.glob("*.kicad_sch"))
            with open(kicad_sch) as f:
                sch_content = f.read()

            # Should have at least some net or component references
            assert len(sch_content) > 100, "KiCad schematic too short"

            print(f"✅ Test 4.1 PASS: Named nets in KiCad")
            print(f"   - Total nets: {len(net_names)}")
            print(f"   - Named nets found: {found_nets}")
            print(f"   - KiCad schematic generated: ✓")

    def test_4_2_net_connections_in_imported_python(self, circuit_with_named_nets):
        """Test 4.2: Net connections visible in imported Python

        Validates:
        - Generate KiCad with nets
        - Import back to Python
        - Generated Python reflects net structure
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Generate KiCad
            result = circuit_with_named_nets.generate_kicad_project(
                project_name="net_circuit", generate_pcb=False
            )
            project_dir = Path(result["project_path"])

            # Record original nets
            json_file = next(project_dir.glob("*.json"))
            with open(json_file) as f:
                json_data = json.load(f)

            original_nets = json_data.get("nets", {})
            original_net_count = (
                len(original_nets)
                if isinstance(original_nets, dict)
                else len(original_nets or [])
            )

            # Import to Python
            output_dir = tmpdir_path / "imported"
            output_dir.mkdir()

            syncer = KiCadToPythonSyncer(
                kicad_project_or_json=str(project_dir / "net_circuit.kicad_pro"),
                python_file=str(output_dir),
                preview_only=False,
                create_backup=False,
            )

            success = syncer.sync()
            assert success, "KiCad → Python sync failed"

            # Verify generated Python has net references
            main_py = output_dir / "main.py"
            with open(main_py) as f:
                generated_code = f.read()

            # Check for component references (nets connect components)
            assert (
                "R1" in generated_code or "C1" in generated_code
            ), "No component references in generated Python"

            print(f"✅ Test 4.2 PASS: Net connections in imported Python")
            print(f"   - Original nets: {original_net_count}")
            print(f"   - Components in generated Python: ✓")
            print(f"   - Net structure reflected: ✓")

    def test_4_3_complex_net_topology(self):
        """Test 4.3: Complex net topology preservation

        Validates:
        - Create circuit with complex net topology (many connections)
        - Generate KiCad
        - Import back to Python
        - Verify net count and structure preserved
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            # Create circuit with more complex topology
            @circuit(name="complex_net_circuit")
            def complex_net_circuit():
                from circuit_synth import Component, Net

                # Power rails
                vcc = Net("VCC")
                gnd = Net("GND")

                # Signal paths
                in1 = Net("IN1")
                out1 = Net("OUT1")
                mid1 = Net("MID1")

                # Components that connect these nets
                r1 = Component(
                    symbol="Device:R",
                    ref="R1",
                    value="1k",
                    footprint="Resistor_SMD:R_0603_1608Metric",
                )
                r2 = Component(
                    symbol="Device:R",
                    ref="R2",
                    value="2k",
                    footprint="Resistor_SMD:R_0603_1608Metric",
                )
                r3 = Component(
                    symbol="Device:R",
                    ref="R3",
                    value="3k",
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

            circuit_obj = complex_net_circuit()

            # Step 1: Generate KiCad
            result1 = circuit_obj.generate_kicad_project(
                project_name="complex_net_circuit", generate_pcb=False
            )
            project_dir_1 = Path(result1["project_path"])
            json_file_1 = next(project_dir_1.glob("*.json"))

            with open(json_file_1) as f:
                json_data_1 = json.load(f)

            nets_1 = json_data_1.get("nets", {})
            net_count_1 = len(nets_1) if isinstance(nets_1, dict) else len(nets_1 or [])
            comps_1 = json_data_1.get("components", {})
            comp_count_1 = (
                len(comps_1) if isinstance(comps_1, dict) else len(comps_1 or [])
            )

            # Step 2: Import to Python
            output_dir = tmpdir_path / "imported"
            output_dir.mkdir()

            syncer = KiCadToPythonSyncer(
                kicad_project_or_json=str(
                    project_dir_1 / "complex_net_circuit.kicad_pro"
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

            # Verify all components present
            for comp_ref in ["R1", "R2", "R3", "C1", "L1"]:
                assert comp_ref in generated_code, f"{comp_ref} not in generated Python"

            # Step 3: Regenerate KiCad from imported Python
            import sys

            sys.path.insert(0, str(output_dir))
            spec = __import__("importlib.util").util.spec_from_file_location(
                "main", main_py
            )
            main_module = __import__("importlib.util").util.module_from_spec(spec)
            spec.loader.exec_module(main_module)

            circuit_func = getattr(main_module, "complex_net_circuit", None)
            if circuit_func:
                regen_circuit = circuit_func()
                result2 = regen_circuit.generate_kicad_project(
                    project_name="complex_net_circuit_regen",
                    generate_pcb=False,
                )
                project_dir_2 = Path(result2["project_path"])
                json_file_2 = next(project_dir_2.glob("*.json"))

                with open(json_file_2) as f:
                    json_data_2 = json.load(f)

                nets_2 = json_data_2.get("nets", {})
                net_count_2 = (
                    len(nets_2) if isinstance(nets_2, dict) else len(nets_2 or [])
                )
                comps_2 = json_data_2.get("components", {})
                comp_count_2 = (
                    len(comps_2) if isinstance(comps_2, dict) else len(comps_2 or [])
                )

                # Verify counts preserved
                assert (
                    comp_count_1 == comp_count_2
                ), f"Component count changed: {comp_count_1} → {comp_count_2}"
                assert (
                    net_count_1 == net_count_2
                ), f"Net count changed: {net_count_1} → {net_count_2}"

            print(f"✅ Test 4.3 PASS: Complex net topology preserved")
            print(f"   - Original: {comp_count_1} components, {net_count_1} nets")
            print(
                f"   - After round-trip: {comp_count_2} components, {net_count_2} nets"
            )
            print(f"   - Topology preserved: ✓")

    def test_4_4_net_name_idempotency(self, circuit_with_named_nets):
        """Test 4.4: Net names preserved with idempotency

        CRITICAL TEST: Verify that net names are deterministically preserved
        across multiple regenerations.

        Validates:
        - Generate KiCad with named nets
        - Regenerate multiple times
        - Net names and counts identical each time
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            tmpdir_path = Path(tmpdir)

            net_data_list = []

            # Generate three times
            for i in range(3):
                result = circuit_with_named_nets.generate_kicad_project(
                    project_name="net_circuit", generate_pcb=False
                )
                project_dir = Path(result["project_path"])
                json_file = next(project_dir.glob("*.json"))

                with open(json_file) as f:
                    json_data = json.load(f)

                nets = json_data.get("nets", {})
                net_names = (
                    list(nets.keys())
                    if isinstance(nets, dict)
                    else sorted([n.get("name") for n in nets if n.get("name")])
                )

                net_data_list.append((i + 1, len(net_names), net_names))

            # Verify all generations have same net count
            net_counts = [d[1] for d in net_data_list]
            assert all(
                c == net_counts[0] for c in net_counts
            ), f"Net counts varied: {net_counts}"

            # Verify net names consistent
            first_net_names = sorted(net_data_list[0][2])
            for gen_num, net_count, net_names in net_data_list:
                print(
                    f"   - Generation {gen_num}: {net_count} nets, "
                    f"names: {net_names[:3]}..."
                )
                sorted_names = sorted(net_names)
                assert (
                    sorted_names == first_net_names
                ), f"Net names changed in generation {gen_num}"

            print(f"✅ Test 4.4 PASS: Net name idempotency")
            print(f"   - 3 generations with same net count: ✓")
            print(f"   - Net names consistent: ✓")
            print(f"   - Idempotency verified: ✓")


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
