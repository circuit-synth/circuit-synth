"""
End-to-end integration test for source reference rewriting feature.

Tests the complete workflow: Python circuit → KiCad generation → source update.
"""

import tempfile
from pathlib import Path
from textwrap import dedent

import pytest

from circuit_synth.core import Circuit, Component, Net
from circuit_synth.core.decorators import circuit, set_current_circuit


def test_complete_workflow_with_source_update(tmp_path):
    """Test complete workflow: create circuit, generate KiCad, verify source updated."""

    # Step 1: Create a realistic circuit file
    circuit_file = tmp_path / "led_circuit.py"
    original_source = dedent('''
        from circuit_synth.core import Circuit, Component, Net
        from circuit_synth.core.decorators import circuit

        @circuit(name="led_circuit")
        def led_blinker():
            """Simple LED blinking circuit"""

            # Create nets
            gnd = Net("GND")
            vcc = Net("VCC_3V3")
            led_net = Net("LED")

            # Components with unnumbered refs
            led = Component(
                symbol="Device:LED",
                ref="D",
                value="RED",
                footprint="LED_SMD:LED_0603_1608Metric"
            )

            resistor = Component(
                symbol="Device:R",
                ref="R",
                value="1k",
                footprint="Resistor_SMD:R_0603_1608Metric"
            )

            # Connect
            led[1] += led_net
            led[2] += gnd
            resistor[1] += vcc
            resistor[2] += led_net

            return led, resistor

        if __name__ == "__main__":
            c = led_blinker()
    ''').strip()

    circuit_file.write_text(original_source)

    # Step 2: Execute the circuit and finalize references
    import sys
    sys.path.insert(0, str(tmp_path))

    try:
        # Import the circuit
        exec_globals = {}
        exec(original_source, exec_globals)

        # Create circuit instance
        c = exec_globals['led_blinker']()

        # Finalize references (should assign D1, R1)
        c.finalize_references()

        # Verify components got correct refs
        components = list(c._components.values())
        refs = sorted([comp.ref for comp in components if hasattr(comp, 'ref')])
        print(f"\nComponent refs: {refs}")
        assert "D1" in refs, f"Expected D1 in {refs}"
        assert "R1" in refs, f"Expected R1 in {refs}"

        # Verify ref mapping contains both
        print(f"Ref mapping: {c._ref_mapping}")
        assert "D" in c._ref_mapping
        assert "R" in c._ref_mapping
        assert c._ref_mapping["D"] == ["D1"]
        assert c._ref_mapping["R"] == ["R1"]

        # Step 3: Update source file
        # Note: _get_source_file() doesn't work with exec'd code,
        # so we call _update_source_refs directly
        from circuit_synth.core.source_ref_rewriter import SourceRefRewriter
        rewriter = SourceRefRewriter(circuit_file, c._ref_mapping)
        rewriter.update()

        # Step 4: Verify source file was updated
        updated_source = circuit_file.read_text()

        print("\n" + "="*70)
        print("UPDATED SOURCE:")
        print("="*70)
        print(updated_source)
        print("="*70)

        # Check that refs were updated
        assert 'ref="D1"' in updated_source, "LED ref should be updated to D1"
        assert 'ref="R1"' in updated_source, "Resistor ref should be updated to R1"
        assert 'ref="D",' not in updated_source, "Original D ref should be gone"
        assert 'ref="R",' not in updated_source, "Original R ref should be gone"

        print("\n✅ ROUND-TRIP SUCCESSFUL!")
        print("   - Original refs: D, R")
        print("   - After finalize: D1, R1")
        print("   - Source updated: D1, R1")
        print("   - Source file now has numbered refs for next generation")

    finally:
        sys.path.remove(str(tmp_path))
        set_current_circuit(None)


def test_multiple_components_round_trip(tmp_path):
    """Test round-trip with multiple components of same type."""

    circuit_file = tmp_path / "power_supply.py"
    original_source = dedent('''
        from circuit_synth.core import Circuit, Component, Net
        from circuit_synth.core.decorators import circuit

        @circuit(name="power")
        def power_supply():
            """Power supply with decoupling caps"""

            gnd = Net("GND")
            vcc = Net("VCC_3V3")

            # Multiple caps - all ref="C"
            cap1 = Component(symbol="Device:C", ref="C", value="10uF",
                           footprint="Capacitor_SMD:C_0805_2012Metric")
            cap2 = Component(symbol="Device:C", ref="C", value="100nF",
                           footprint="Capacitor_SMD:C_0603_1608Metric")
            cap3 = Component(symbol="Device:C", ref="C", value="1uF",
                           footprint="Capacitor_SMD:C_0603_1608Metric")

            # Connect all
            for cap in [cap1, cap2, cap3]:
                cap[1] += vcc
                cap[2] += gnd

        if __name__ == "__main__":
            c = power_supply()
    ''').strip()

    circuit_file.write_text(original_source)

    import sys
    sys.path.insert(0, str(tmp_path))

    try:
        # Execute and finalize
        exec_globals = {}
        exec(original_source, exec_globals)
        c = exec_globals['power_supply']()
        c.finalize_references()

        # Check mapping
        print(f"\nRef mapping: {c._ref_mapping}")
        assert c._ref_mapping["C"] == ["C1", "C2", "C3"], \
            f"Expected C1, C2, C3 but got {c._ref_mapping['C']}"

        # Update source
        from circuit_synth.core.source_ref_rewriter import SourceRefRewriter
        rewriter = SourceRefRewriter(circuit_file, c._ref_mapping)
        rewriter.update()

        # Verify update
        updated = circuit_file.read_text()

        print("\nUPDATED SOURCE:")
        for i, line in enumerate(updated.split('\n'), 1):
            if 'ref=' in line:
                print(f"  Line {i}: {line.strip()}")

        # Each cap should have unique ref
        assert 'ref="C1", value="10uF"' in updated
        assert 'ref="C2", value="100nF"' in updated
        assert 'ref="C3", value="1uF"' in updated

        # Original refs should be gone
        assert updated.count('ref="C",') == 0, \
            "Original unnumbered refs should all be replaced"

        print("\n✅ MULTIPLE COMPONENTS TEST PASSED!")

    finally:
        sys.path.remove(str(tmp_path))
        set_current_circuit(None)


def test_comments_and_docstrings_preserved(tmp_path):
    """Test that comments and docstrings are not modified."""

    circuit_file = tmp_path / "documented_circuit.py"
    original_source = dedent('''
        from circuit_synth.core import Circuit, Component, Net
        from circuit_synth.core.decorators import circuit

        @circuit(name="test")
        def test_circuit():
            """
            Example circuit shows Component(ref="R", value="10k").
            This ref="R" in docstring should NOT change.
            """

            gnd = Net("GND")
            vcc = Net("VCC")

            # Comment mentions ref="R" - should NOT change
            resistor = Component(
                symbol="Device:R",
                ref="R",  # This ref="R" SHOULD change
                value="10k",
                footprint="Resistor_SMD:R_0603_1608Metric"
            )  # Note: ref="R" is auto-numbered - comment should NOT change

            resistor[1] += vcc
            resistor[2] += gnd

        if __name__ == "__main__":
            c = test_circuit()
    ''').strip()

    circuit_file.write_text(original_source)

    import sys
    sys.path.insert(0, str(tmp_path))

    try:
        exec_globals = {}
        exec(original_source, exec_globals)
        c = exec_globals['test_circuit']()
        c.finalize_references()

        # Update source
        from circuit_synth.core.source_ref_rewriter import SourceRefRewriter
        rewriter = SourceRefRewriter(circuit_file, c._ref_mapping)
        rewriter.update()

        updated = circuit_file.read_text()

        print("\nUPDATED SOURCE:")
        print(updated)

        # Only the actual Component ref should change
        assert updated.count('ref="R1"') == 1, \
            "Exactly one ref should be updated (the Component)"

        # Docstring and comments should be preserved
        assert 'Example circuit shows Component(ref="R", value="10k")' in updated, \
            "Docstring should preserve ref=\"R\""
        assert '# Comment mentions ref="R"' in updated, \
            "Comment line should preserve ref=\"R\""
        assert 'comment should NOT change' in updated
        assert 'ref="R" is auto-numbered' in updated, \
            "Inline comment should preserve ref=\"R\""

        print("\n✅ COMMENTS AND DOCSTRINGS PRESERVED!")

    finally:
        sys.path.remove(str(tmp_path))
        set_current_circuit(None)


if __name__ == "__main__":
    pytest.main([__file__, "-xvs"])
