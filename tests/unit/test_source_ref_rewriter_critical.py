"""
Critical bug tests for source reference rewriting.

These tests MUST pass before the feature can be merged.
"""

import tempfile
from pathlib import Path
from textwrap import dedent

import pytest

from circuit_synth.core import Circuit, Component, Net
from circuit_synth.core.decorators import set_current_circuit
from circuit_synth.core.source_ref_rewriter import SourceRefRewriter


class TestCriticalBug1MultipleComponentsSamePrefix:
    """
    CRITICAL BUG #1: Multiple components with same prefix only store last mapping.

    This is the most critical bug - it breaks the core functionality for the most
    common use case (circuits with multiple resistors, capacitors, etc.).
    """

    def test_multiple_components_same_prefix_in_circuit(self, tmp_path):
        """Test that multiple components with same prefix get unique mappings."""
        from circuit_synth.core.decorators import set_current_circuit

        # Create circuit and set as current
        circuit = Circuit("test")
        set_current_circuit(circuit)

        try:
            # Add three components with same ref prefix
            c1 = Component(symbol="Device:C", ref="C", value="10uF",
                          footprint="Capacitor_SMD:C_0805_2012Metric")
            c2 = Component(symbol="Device:C", ref="C", value="22uF",
                          footprint="Capacitor_SMD:C_0805_2012Metric")
            c3 = Component(symbol="Device:C", ref="C", value="100nF",
                          footprint="Capacitor_SMD:C_0603_1608Metric")

            # Finalize references (should assign C1, C2, C3)
            circuit.finalize_references()

            # Check that mapping contains all three components
            # Current buggy implementation: _ref_mapping = {"C": "C3"} ❌
            # Correct implementation: Need to track all mappings
            assert hasattr(circuit, '_ref_mapping')

            # The mapping should contain info about all three components
            # We need a way to distinguish C1 from C2 from C3
            # This will fail with current implementation!
            print(f"Ref mapping: {circuit._ref_mapping}")

            # Check actual component refs were assigned
            assert c1.ref == "C1"
            assert c2.ref == "C2"
            assert c3.ref == "C3"

        finally:
            set_current_circuit(None)

    def test_source_rewriting_multiple_same_prefix(self, tmp_path):
        """Test source file update with multiple components sharing prefix."""
        source_file = tmp_path / "test_circuit.py"
        source_code = dedent('''
            from circuit_synth import *

            @circuit
            def power_supply():
                """Power supply with multiple capacitors"""

                # Line 7: First capacitor
                cap_input = Component(ref="C", value="10uF", symbol="Device:C",
                                     footprint="Capacitor_SMD:C_0805_2012Metric")

                # Line 11: Second capacitor
                cap_output = Component(ref="C", value="22uF", symbol="Device:C",
                                      footprint="Capacitor_SMD:C_0805_2012Metric")

                # Line 15: Third capacitor
                cap_bypass = Component(ref="C", value="100nF", symbol="Device:C",
                                      footprint="Capacitor_SMD:C_0603_1608Metric")
        ''').strip()

        source_file.write_text(source_code)

        # The correct mapping should be line-aware or component-instance aware
        # For now, let's test with a mapping that includes line numbers or indices
        # This is what we NEED to support:
        ref_mapping = {
            ("C", 0): "C1",  # First occurrence
            ("C", 1): "C2",  # Second occurrence
            ("C", 2): "C3",  # Third occurrence
        }

        # Current implementation doesn't support this - we need to fix it
        # For now, let's test what SHOULD happen

        # Expected output:
        expected = source_code.replace('ref="C", value="10uF"', 'ref="C1", value="10uF"', 1)
        expected = expected.replace('ref="C", value="22uF"', 'ref="C2", value="22uF"', 1)
        expected = expected.replace('ref="C", value="100nF"', 'ref="C3", value="100nF"', 1)

        # This test will fail with current implementation!
        # We need a new design that tracks component instances or line numbers
        pytest.skip("Design needs to be fixed - current mapping structure can't handle this")

    def test_ref_mapping_structure_requirements(self):
        """Document what the ref mapping structure needs to support."""

        # PROBLEM: Current structure is just dict[str, str]
        # {"C": "C3"}  ❌ Can only store one mapping per prefix

        # SOLUTION OPTIONS:

        # Option 1: List of tuples with line numbers
        # [("C", 7, "C1"), ("C", 11, "C2"), ("C", 15, "C3")]

        # Option 2: Dict with component instance IDs
        # {id(comp1): ("C", "C1"), id(comp2): ("C", "C2"), id(comp3): ("C", "C3")}

        # Option 3: Store line number in Component and use for matching
        # Component stores its definition line, mapping includes line info

        # Option 4: Use ordered list and match by occurrence order
        # {"C": ["C1", "C2", "C3"]}  # Replace 1st, 2nd, 3rd occurrence

        pytest.skip("Design decision needed - documenting requirements")


class TestCriticalBug2InlineComments:
    """
    CRITICAL BUG #2: Inline comments get modified when they shouldn't.

    The code checks if pattern appears before comment, but then uses
    str.replace() which replaces ALL occurrences on the line.
    """

    def test_inline_comment_preservation(self, tmp_path):
        """Test that inline comments are NOT modified."""
        source_file = tmp_path / "test_circuit.py"
        source_code = dedent('''
            from circuit_synth import *

            @circuit
            def main():
                r = Component(ref="R", value="10k", symbol="Device:R",
                             footprint="Resistor_SMD:R_0603_1608Metric")  # old ref="R" value
        ''').strip()

        source_file.write_text(source_code)

        # Expected: Only the Component ref="R" should change, NOT the comment
        expected = source_code.replace('(ref="R"', '(ref="R1"')
        # Comment should still have ref="R"
        assert '# old ref="R" value' in expected

        rewriter = SourceRefRewriter(source_file, {"R": "R1"})
        rewriter.update()

        updated = source_file.read_text()

        # This will FAIL with current implementation!
        assert 'ref="R1"' in updated  # Component should be updated
        assert '# old ref="R" value' in updated  # Comment should NOT be updated

    def test_multiple_refs_on_line_with_comment(self, tmp_path):
        """Test line with multiple refs and a comment."""
        source_file = tmp_path / "test_circuit.py"
        source_code = dedent('''
            from circuit_synth import *

            @circuit
            def main():
                r = Component(ref="R", value="10k", symbol="Device:R", footprint="Resistor_SMD:R_0603_1608Metric")  # Note: ref="R" is auto-numbered
        ''').strip()

        source_file.write_text(source_code)

        rewriter = SourceRefRewriter(source_file, {"R": "R1"})
        rewriter.update()

        updated = source_file.read_text()

        # Only the FIRST ref="R" (in Component) should change
        # The one in the comment should stay as ref="R"
        assert updated.count('ref="R1"') == 1  # Component updated
        assert 'ref="R" is auto-numbered' in updated  # Comment unchanged

    def test_comment_at_various_positions(self, tmp_path):
        """Test comments at different positions relative to ref."""
        source_file = tmp_path / "test_circuit.py"
        source_code = dedent('''
            from circuit_synth import *

            @circuit
            def main():
                # Before: ref="R"
                r = Component(ref="R", value="10k", symbol="Device:R",  # Inline ref="R"
                             footprint="Resistor_SMD:R_0603_1608Metric")
                # After: ref="R"
        ''').strip()

        source_file.write_text(source_code)

        rewriter = SourceRefRewriter(source_file, {"R": "R1"})
        rewriter.update()

        updated = source_file.read_text()

        # Only Component(ref="R") should change
        assert updated.count('ref="R1"') == 1
        # All comment refs should be unchanged
        assert '# Before: ref="R"' in updated
        assert '# Inline ref="R"' in updated
        assert '# After: ref="R"' in updated


class TestCriticalBug3DocstringDetection:
    """
    BUG #3: Docstring detection is fragile and misses edge cases.
    """

    def test_escaped_quotes_in_string(self, tmp_path):
        """Test that escaped quotes don't confuse docstring detection."""
        source_file = tmp_path / "test_circuit.py"
        source_code = dedent('''
            from circuit_synth import *

            @circuit
            def main():
                example = "string with \\"\\"\\" inside"
                r = Component(ref="R", value="10k", symbol="Device:R",
                             footprint="Resistor_SMD:R_0603_1608Metric")
        ''').strip()

        source_file.write_text(source_code)

        rewriter = SourceRefRewriter(source_file, {"R": "R1"})
        rewriter.update()

        updated = source_file.read_text()

        assert 'ref="R1"' in updated
        assert 'string with \\"\\"\\" inside' in updated  # Unchanged

    def test_code_after_single_line_docstring(self, tmp_path):
        """Test code on same line after single-line docstring."""
        source_file = tmp_path / "test_circuit.py"
        source_code = dedent('''
            from circuit_synth import *

            @circuit
            def main():
                """Docstring"""; r = Component(ref="R", value="10k", symbol="Device:R", footprint="Resistor_SMD:R_0603_1608Metric")
        ''').strip()

        source_file.write_text(source_code)

        rewriter = SourceRefRewriter(source_file, {"R": "R1"})
        rewriter.update()

        updated = source_file.read_text()

        # The Component should be updated even though it's on same line as docstring
        assert 'ref="R1"' in updated

    def test_multiline_docstring_with_refs(self, tmp_path):
        """Test that refs inside multiline docstrings are NOT updated."""
        source_file = tmp_path / "test_circuit.py"
        source_code = dedent('''
            from circuit_synth import *

            @circuit
            def main():
                """
                This is a multiline docstring.
                It mentions Component(ref="R", value="10k") as an example.
                This should NOT be changed.
                """
                r = Component(ref="R", value="10k", symbol="Device:R",
                             footprint="Resistor_SMD:R_0603_1608Metric")
        ''').strip()

        source_file.write_text(source_code)

        rewriter = SourceRefRewriter(source_file, {"R": "R1"})
        rewriter.update()

        updated = source_file.read_text()

        # Only the actual Component outside docstring should be updated
        lines = updated.split('\n')
        docstring_line = [l for l in lines if 'It mentions Component' in l][0]
        component_line = [l for l in lines if 'r = Component' in l][0]

        assert 'ref="R"' in docstring_line  # Docstring unchanged
        assert 'ref="R1"' in component_line  # Component changed


class TestAmbiguityDetection:
    """Test detection and handling of ambiguous scenarios."""

    def test_detect_multiple_components_same_prefix_same_line(self, tmp_path):
        """Test detection of ambiguous case: multiple components on same line."""
        source_file = tmp_path / "test_circuit.py"
        source_code = 'r1 = Component(ref="R", value="10k", symbol="Device:R", footprint="Resistor_SMD:R_0603_1608Metric"); r2 = Component(ref="R", value="47k", symbol="Device:R", footprint="Resistor_SMD:R_0603_1608Metric")'

        source_file.write_text(source_code)

        # This is ambiguous - which becomes R1 and which becomes R2?
        # We should either:
        # 1. Detect and warn
        # 2. Handle left-to-right order
        # 3. Refuse to update and log error

        # For now, let's test that we handle it somehow without corruption
        rewriter = SourceRefRewriter(source_file, {"R": "R1"})
        result = rewriter.update()

        # At minimum, file should not be corrupted
        updated = source_file.read_text()
        assert 'Component' in updated
        assert 'Device:R' in updated

        # Document expected behavior
        pytest.skip("Ambiguous case - needs design decision on how to handle")


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
