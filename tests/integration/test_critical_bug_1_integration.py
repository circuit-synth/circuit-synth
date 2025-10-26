"""
Integration test for Critical Bug #1: Multiple components same prefix.

This test demonstrates the complete failure of the round-trip workflow.
"""

import tempfile
from pathlib import Path
from textwrap import dedent

import pytest

from circuit_synth.core import Circuit, Component, Net
from circuit_synth.core.decorators import circuit, set_current_circuit


def test_end_to_end_multiple_capacitors(tmp_path):
    """
    End-to-end test: Multiple capacitors with ref="C" should each get unique refs.

    This test will FAIL with current implementation because:
    1. Three caps start with ref="C"
    2. After finalize: C1, C2, C3
    3. But _ref_mapping only stores {"C": "C3"}
    4. Source rewriter replaces ALL ref="C" with ref="C3"
    5. All three components in source become ref="C3"
    6. Next run will fail with duplicate refs
    """

    # Create a test circuit file
    circuit_file = tmp_path / "test_power_supply.py"
    original_source = dedent(
        '''
        from circuit_synth.core import Circuit, Component, Net
        from circuit_synth.core.decorators import circuit, set_current_circuit

        @circuit(name="power_supply")
        def create_power_supply():
            """Power supply with three capacitors"""

            gnd = Net("GND")
            vcc = Net("VCC_3V3")

            # Three capacitors - all start with ref="C"
            cap_input = Component(
                symbol="Device:C",
                ref="C",
                value="10uF",
                footprint="Capacitor_SMD:C_0805_2012Metric"
            )

            cap_output = Component(
                symbol="Device:C",
                ref="C",
                value="22uF",
                footprint="Capacitor_SMD:C_0805_2012Metric"
            )

            cap_bypass = Component(
                symbol="Device:C",
                ref="C",
                value="100nF",
                footprint="Capacitor_SMD:C_0603_1608Metric"
            )

            # Connect them
            cap_input[1] += vcc
            cap_input[2] += gnd
            cap_output[1] += vcc
            cap_output[2] += gnd
            cap_bypass[1] += vcc
            cap_bypass[2] += gnd

        if __name__ == "__main__":
            c = create_power_supply()
            c.generate_kicad_project(
                "test_project",
                force_regenerate=False,
                update_source_refs=True
            )
    '''
    ).strip()

    circuit_file.write_text(original_source)

    # Import and execute the circuit
    import sys

    sys.path.insert(0, str(tmp_path))

    try:
        # Execute the circuit file (simulating user running it)
        exec_globals = {}
        exec(original_source, exec_globals)

        # Get the circuit
        c = exec_globals["create_power_supply"]()

        # Check components got assigned C1, C2, C3
        components = list(c._components.values())
        refs = sorted(
            [
                comp.ref
                for comp in components
                if hasattr(comp, "ref") and comp.ref.startswith("C")
            ]
        )

        print(f"\nComponent refs after finalize: {refs}")
        print(f"Ref mapping: {c._ref_mapping}")

        assert refs == ["C1", "C2", "C3"], f"Expected C1, C2, C3 but got {refs}"

        # Now check the ref mapping - THIS IS THE BUG
        # Current implementation: _ref_mapping = {"C": "C3"}  ❌
        # This test will PASS the assertion above but show the mapping is broken

        if c._ref_mapping == {"C": "C3"}:
            pytest.fail(
                f"CRITICAL BUG DETECTED!\n"
                f"Component refs are: {refs}\n"
                f"But ref_mapping is: {c._ref_mapping}\n"
                f"This means source rewriter will replace ALL ref='C' with ref='C3'\n"
                f"Causing all three components to become ref='C3' in source code!\n"
                f"The round-trip workflow is completely broken."
            )

        # If we get here, the bug is fixed
        # The mapping should track all three components somehow
        assert len(str(c._ref_mapping)) > 15, (
            f"Ref mapping seems too simple: {c._ref_mapping}. "
            f"It should track all three C->C1, C->C2, C->C3 mappings somehow."
        )

    finally:
        sys.path.remove(str(tmp_path))
        set_current_circuit(None)


if __name__ == "__main__":
    pytest.main([__file__, "-xvs"])
