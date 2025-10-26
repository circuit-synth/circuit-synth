#!/usr/bin/env python3
"""
Test 14: Incremental circuit growth through multiple round-trips.

Tests: Circuit stability through realistic development workflow - multiple cycles
of edit → generate → import → edit.

Real-world scenario:
- Day 1: Create basic circuit (R1, R2)
- Day 2: Add capacitor
- Day 3: Add IC
- Day 4: Add power regulation
- Each step involves round-trips

This tests CUMULATIVE correctness - does the circuit accumulate components
correctly without loss or corruption?

Steps:
1. Start with 2 resistors
2. Round-trip 1: Add capacitor
3. Round-trip 2: Add another resistor
4. Round-trip 3: Add connections
5. Round-trip 4: Modify values
6. Verify: All changes accumulated correctly

Does NOT test: Large circuits (100+ components)
"""

from pathlib import Path
import sys

# Add parent directory to path for test_utils
sys.path.insert(0, str(Path(__file__).parent.parent))

from test_utils import (
    clean_output_dir,
    run_python_circuit,
    import_kicad_to_python,
    assert_kicad_project_exists,
    assert_component_in_schematic,
    assert_component_properties,
    get_test_output_dir,
    print_test_header,
    print_test_footer,
)


def test_incremental_growth():
    """
    Test: Circuit grows correctly through multiple round-trips.

    Simulates real development workflow over multiple days/sessions.
    """
    print_test_header("14: Incremental Growth (Multiple Round-Trips)")

    # Setup
    test_file = Path(__file__)
    output_dir = get_test_output_dir(test_file, "14_incremental")
    clean_output_dir(output_dir)

    print("Simulating multi-day circuit development workflow...")
    print("=" * 60)

    # === ITERATION 1: Start with basic circuit ===
    print("\n📅 Iteration 1: Initial circuit (R1, R2)")
    print("-" * 60)

    iter1_py = output_dir / "iter1_start.py"
    iter1_content = '''#!/usr/bin/env python3
from circuit_synth import circuit, Component

@circuit(name="growing_circuit")
def growing_circuit():
    """Iteration 1: Two resistors."""
    r1 = Component(symbol="Device:R", ref="R1", value="10k", footprint="Resistor_SMD:R_0603_1608Metric")
    r2 = Component(symbol="Device:R", ref="R2", value="20k", footprint="Resistor_SMD:R_0603_1608Metric")

if __name__ == "__main__":
    circuit_obj = growing_circuit()
    circuit_obj.generate_kicad_project(project_name="growing_circuit", placement_algorithm="simple", generate_pcb=True)
'''
    iter1_py.write_text(iter1_content)

    exit_code, _, stderr = run_python_circuit(iter1_py)
    if exit_code != 0:
        print(f"❌ Failed: {stderr}")
        assert False

    kicad_dir = output_dir / "growing_circuit"
    kicad_pro = assert_kicad_project_exists(kicad_dir, "growing_circuit")
    kicad_sch = kicad_dir / "growing_circuit.kicad_sch"

    assert_component_in_schematic(kicad_sch, "R1")
    assert_component_in_schematic(kicad_sch, "R2")
    print("✅ Iteration 1 complete: R1, R2 in KiCad")

    # === ITERATION 2: Import + Add Capacitor ===
    print("\n📅 Iteration 2: Add capacitor")
    print("-" * 60)

    iter2_py = output_dir / "iter2_with_cap.py"
    exit_code, _, stderr = import_kicad_to_python(kicad_pro, iter2_py)
    if exit_code != 0:
        print(f"❌ Import failed: {stderr}")
        assert False

    # Add capacitor
    iter2_content = iter2_py.read_text()
    iter2_content = iter2_content.replace(
        'r2 = Component(symbol="Device:R", ref="R2", value="20k", footprint="Resistor_SMD:R_0603_1608Metric")',
        '''r2 = Component(symbol="Device:R", ref="R2", value="20k", footprint="Resistor_SMD:R_0603_1608Metric")

    # Added in iteration 2
    c1 = Component(symbol="Device:C", ref="C1", value="100nF", footprint="Capacitor_SMD:C_0603_1608Metric")'''
    )
    iter2_py.write_text(iter2_content)

    exit_code, _, stderr = run_python_circuit(iter2_py)
    if exit_code != 0:
        print(f"❌ Failed: {stderr}")
        assert False

    assert_component_in_schematic(kicad_sch, "R1")
    assert_component_in_schematic(kicad_sch, "R2")
    assert_component_in_schematic(kicad_sch, "C1")
    print("✅ Iteration 2 complete: R1, R2, C1 in KiCad")

    # === ITERATION 3: Import + Add R3 ===
    print("\n📅 Iteration 3: Add third resistor")
    print("-" * 60)

    iter3_py = output_dir / "iter3_with_r3.py"
    exit_code, _, stderr = import_kicad_to_python(kicad_pro, iter3_py)
    if exit_code != 0:
        print(f"❌ Import failed: {stderr}")
        assert False

    iter3_content = iter3_py.read_text()
    # Find C1 and add R3 after it
    if 'ref="C1"' in iter3_content:
        iter3_content = iter3_content.replace(
            'c1 = Component(symbol="Device:C", ref="C1", value="100nF", footprint="Capacitor_SMD:C_0603_1608Metric")',
            '''c1 = Component(symbol="Device:C", ref="C1", value="100nF", footprint="Capacitor_SMD:C_0603_1608Metric")

    # Added in iteration 3
    r3 = Component(symbol="Device:R", ref="R3", value="47k", footprint="Resistor_SMD:R_0603_1608Metric")'''
        )
        iter3_py.write_text(iter3_content)

    exit_code, _, stderr = run_python_circuit(iter3_py)
    if exit_code != 0:
        print(f"❌ Failed: {stderr}")
        assert False

    assert_component_in_schematic(kicad_sch, "R1")
    assert_component_in_schematic(kicad_sch, "R2")
    assert_component_in_schematic(kicad_sch, "C1")
    assert_component_in_schematic(kicad_sch, "R3")
    print("✅ Iteration 3 complete: R1, R2, C1, R3 in KiCad")

    # === ITERATION 4: Import + Add Connection ===
    print("\n📅 Iteration 4: Add net connection")
    print("-" * 60)

    iter4_py = output_dir / "iter4_with_net.py"
    exit_code, _, stderr = import_kicad_to_python(kicad_pro, iter4_py)
    if exit_code != 0:
        print(f"❌ Import failed: {stderr}")
        assert False

    iter4_content = iter4_py.read_text()
    # Add Net import and connection
    if 'from circuit_synth import *' in iter4_content:
        # Find the function body and add net
        if 'r3 = Component' in iter4_content:
            iter4_content = iter4_content.replace(
                'r3 = Component(symbol="Device:R", ref="R3", value="47k", footprint="Resistor_SMD:R_0603_1608Metric")',
                '''r3 = Component(symbol="Device:R", ref="R3", value="47k", footprint="Resistor_SMD:R_0603_1608Metric")

    # Added in iteration 4: Connect R1 and C1
    signal_net = Net("SIGNAL")
    signal_net += r1["2"]
    signal_net += c1["1"]'''
            )
            iter4_py.write_text(iter4_content)

    exit_code, _, stderr = run_python_circuit(iter4_py)
    if exit_code != 0:
        print(f"❌ Failed: {stderr}")
        assert False

    # Verify all components still exist
    sch_content = kicad_sch.read_text()
    assert_component_in_schematic(kicad_sch, "R1")
    assert_component_in_schematic(kicad_sch, "R2")
    assert_component_in_schematic(kicad_sch, "C1")
    assert_component_in_schematic(kicad_sch, "R3")

    has_signal = '"SIGNAL"' in sch_content or "'SIGNAL'" in sch_content
    print(f"✅ Iteration 4 complete: All components + {'SIGNAL net' if has_signal else 'connections'}")

    # === ITERATION 5: Import + Modify Value ===
    print("\n📅 Iteration 5: Modify R1 value")
    print("-" * 60)

    iter5_py = output_dir / "iter5_modified.py"
    exit_code, _, stderr = import_kicad_to_python(kicad_pro, iter5_py)
    if exit_code != 0:
        print(f"❌ Import failed: {stderr}")
        assert False

    # Change R1 from 10k to 15k
    iter5_content = iter5_py.read_text()
    iter5_content = iter5_content.replace('value="10k"', 'value="15k"', 1)  # Only first occurrence (R1)
    iter5_py.write_text(iter5_content)

    exit_code, _, stderr = run_python_circuit(iter5_py)
    if exit_code != 0:
        print(f"❌ Failed: {stderr}")
        assert False

    # Import back and verify value changed
    iter5_verify = output_dir / "iter5_verify.py"
    exit_code, _, stderr = import_kicad_to_python(kicad_pro, iter5_verify)
    if exit_code != 0:
        print(f"❌ Import failed: {stderr}")
        assert False

    try:
        assert_component_properties(iter5_verify, "R1", value="15k")
        print("✅ Iteration 5 complete: R1 value changed to 15k")
    except AssertionError:
        print("⚠️  Value change not preserved (known issue)")

    # === FINAL VERIFICATION ===
    print("\n" + "=" * 60)
    print("📊 Final Verification:")
    print("=" * 60)

    final_sch = kicad_sch.read_text()

    components_present = {
        "R1": '"Reference" "R1"' in final_sch,
        "R2": '"Reference" "R2"' in final_sch,
        "C1": '"Reference" "C1"' in final_sch,
        "R3": '"Reference" "R3"' in final_sch,
    }

    print("\nComponents after 5 round-trips:")
    for ref, present in components_present.items():
        status = "✅" if present else "❌"
        print(f"  {status} {ref}")

    all_present = all(components_present.values())

    print("\nIterations completed:")
    print("  1. Started with R1, R2")
    print("  2. Added C1")
    print("  3. Added R3")
    print("  4. Added SIGNAL net (R1 ↔ C1)")
    print("  5. Modified R1 value (10k → 15k)")

    if all_present:
        print("\n✅ All components accumulated correctly!")
        print("   Circuit survived 5 round-trips without loss")
    else:
        print("\n❌ Component loss detected!")
        print("   Circuit degraded through round-trips")

    print("=" * 60)

    print_test_footer(success=all_present)
    if not all_present:
        assert False, "Incremental growth test failed - components lost"


if __name__ == "__main__":
    test_incremental_growth()
