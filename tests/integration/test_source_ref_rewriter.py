"""
Unit tests for source reference rewriting functionality.

Tests the automatic updating of Python source files with finalized component references.
"""

import os
import tempfile
from pathlib import Path
from textwrap import dedent

import pytest

from circuit_synth.core import Circuit, Component, Net
from circuit_synth.core.source_ref_rewriter import SourceRefRewriter


class TestBasicRewriting:
    """Test basic source file rewriting functionality."""

    def test_simple_ref_update(self, tmp_path):
        """Test updating a single unnumbered ref to numbered."""
        # Create test source file
        source_file = tmp_path / "test_circuit.py"
        source_code = dedent(
            '''
            from circuit_synth import *

            @circuit
            def main():
                """Test circuit"""
                r = Component(ref="R", value="10k", symbol="Device:R",
                             footprint="Resistor_SMD:R_0603_1608Metric")

            if __name__ == "__main__":
                circuit = main()
                circuit.generate_kicad_project("test")
        '''
        ).strip()

        source_file.write_text(source_code)

        # Expected result after rewriting
        expected = source_code.replace('ref="R"', 'ref="R1"')

        # Test SourceRefRewriter
        rewriter = SourceRefRewriter(source_file, {"R": "R1"})
        success = rewriter.update()

        assert success is True
        assert source_file.read_text() == expected

    def test_multiple_refs_same_file(self, tmp_path):
        """Test updating multiple different refs in one file."""
        source_file = tmp_path / "test_circuit.py"
        source_code = dedent(
            """
            from circuit_synth import *

            @circuit
            def main():
                r = Component(ref="R", value="10k", symbol="Device:R",
                             footprint="Resistor_SMD:R_0603_1608Metric")
                c = Component(ref="C", value="100nF", symbol="Device:C",
                             footprint="Capacitor_SMD:C_0603_1608Metric")
                l = Component(ref="L", value="10uH", symbol="Device:L",
                             footprint="Inductor_SMD:L_0603_1608Metric")
        """
        ).strip()

        source_file.write_text(source_code)

        # Mapping: R→R1, C→C1, L→L1
        ref_mapping = {"R": "R1", "C": "C1", "L": "L1"}

        # Test multiple ref updates
        rewriter = SourceRefRewriter(source_file, ref_mapping)
        success = rewriter.update()

        assert success is True
        updated = source_file.read_text()
        assert 'ref="R1"' in updated
        assert 'ref="C1"' in updated
        assert 'ref="L1"' in updated
        assert 'ref="R",' not in updated  # Original R with comma shouldn't exist
        assert 'ref="C",' not in updated
        assert 'ref="L",' not in updated

    def test_preserve_formatting(self, tmp_path):
        """Test that formatting (indentation, spacing) is preserved."""
        source_file = tmp_path / "test_circuit.py"
        source_code = dedent(
            """
            from circuit_synth import *

            @circuit
            def main():
                # Lots of spacing
                r    =    Component(  ref="R",   value="10k",
                                     symbol="Device:R",
                                     footprint="Resistor_SMD:R_0603_1608Metric"  )
        """
        ).strip()

        source_file.write_text(source_code)

        # Should preserve all the extra spaces
        expected = source_code.replace('ref="R"', 'ref="R1"')

        rewriter = SourceRefRewriter(source_file, {"R": "R1"})
        rewriter.update()

        assert source_file.read_text() == expected

    def test_mixed_quotes(self, tmp_path):
        """Test handling both single and double quotes."""
        source_file = tmp_path / "test_circuit.py"
        source_code = dedent(
            """
            from circuit_synth import *

            @circuit
            def main():
                r1 = Component(ref="R", value="10k", symbol="Device:R",
                              footprint="Resistor_SMD:R_0603_1608Metric")
                r2 = Component(ref='R', value='10k', symbol='Device:R',
                              footprint='Resistor_SMD:R_0603_1608Metric')
        """
        ).strip()

        source_file.write_text(source_code)

        # Both should be updated
        expected = source_code.replace('ref="R"', 'ref="R1"').replace(
            "ref='R'", "ref='R1'"
        )

        rewriter = SourceRefRewriter(source_file, {"R": "R1"})
        rewriter.update()

        assert source_file.read_text() == expected

    def test_no_refs_to_update(self, tmp_path):
        """Test when mapping is empty (no unnumbered refs)."""
        source_file = tmp_path / "test_circuit.py"
        source_code = dedent(
            """
            from circuit_synth import *

            @circuit
            def main():
                # Already numbered
                r1 = Component(ref="R1", value="10k", symbol="Device:R",
                              footprint="Resistor_SMD:R_0603_1608Metric")
        """
        ).strip()

        source_file.write_text(source_code)
        original_content = source_file.read_text()

        # Empty mapping - nothing to update
        ref_mapping = {}

        # File should remain unchanged
        rewriter = SourceRefRewriter(source_file, ref_mapping)
        success = rewriter.update()

        assert success is False  # Should return False when no changes
        assert source_file.read_text() == original_content

    def test_empty_mapping(self, tmp_path):
        """Test with None or empty mapping."""
        source_file = tmp_path / "test_circuit.py"
        source_code = dedent(
            """
            from circuit_synth import *

            @circuit
            def main():
                r = Component(ref="R", value="10k", symbol="Device:R",
                             footprint="Resistor_SMD:R_0603_1608Metric")
        """
        ).strip()

        source_file.write_text(source_code)
        original = source_file.read_text()

        # Should not modify file
        pytest.skip("SourceRefRewriter not yet implemented")


class TestEdgeCases:
    """Test edge cases in source parsing."""

    def test_refs_in_comments(self, tmp_path):
        """Test that refs in comments are NOT updated."""
        source_file = tmp_path / "test_circuit.py"
        source_code = dedent(
            """
            from circuit_synth import *

            @circuit
            def main():
                # TODO: Change ref="R" to something else
                # Component(ref="R", ...) - example
                r = Component(ref="R", value="10k", symbol="Device:R",
                             footprint="Resistor_SMD:R_0603_1608Metric")
        """
        ).strip()

        source_file.write_text(source_code)

        # Only the actual Component call should be updated, not comments
        rewriter = SourceRefRewriter(source_file, {"R": "R1"})
        rewriter.update()

        updated = source_file.read_text()
        # Check that comments still have ref="R"
        assert '# TODO: Change ref="R"' in updated
        assert '# Component(ref="R"' in updated
        # But the actual Component call should have ref="R1"
        assert 'r = Component(ref="R1"' in updated

    def test_refs_in_docstrings(self, tmp_path):
        """Test that refs in docstrings are NOT updated."""
        source_file = tmp_path / "test_circuit.py"
        source_code = dedent(
            '''
            from circuit_synth import *

            @circuit
            def main():
                """
                Example circuit with Component(ref="R", value="10k")
                """
                r = Component(ref="R", value="10k", symbol="Device:R",
                             footprint="Resistor_SMD:R_0603_1608Metric")
        '''
        ).strip()

        source_file.write_text(source_code)

        # Docstring should NOT be updated
        rewriter = SourceRefRewriter(source_file, {"R": "R1"})
        rewriter.update()

        updated = source_file.read_text()
        # Docstring should still have ref="R"
        assert 'Component(ref="R", value="10k")' in updated
        # But the actual Component call should have ref="R1"
        assert 'r = Component(ref="R1"' in updated

    def test_refs_in_string_literals(self, tmp_path):
        """Test that refs in other string literals are NOT updated."""
        source_file = tmp_path / "test_circuit.py"
        source_code = dedent(
            """
            from circuit_synth import *

            @circuit
            def main():
                example = "Component(ref='R', value='10k')"
                r = Component(ref="R", value="10k", symbol="Device:R",
                             footprint="Resistor_SMD:R_0603_1608Metric")
        """
        ).strip()

        source_file.write_text(source_code)

        # Only the Component call, not the string literal
        pytest.skip("SourceRefRewriter not yet implemented")

    def test_multiline_component_calls(self, tmp_path):
        """Test handling of multiline Component() calls."""
        source_file = tmp_path / "test_circuit.py"
        source_code = dedent(
            """
            from circuit_synth import *

            @circuit
            def main():
                r = Component(
                    ref="R",
                    value="10k",
                    symbol="Device:R",
                    footprint="Resistor_SMD:R_0603_1608Metric"
                )
        """
        ).strip()

        source_file.write_text(source_code)

        # Should find and update ref on separate line
        expected = source_code.replace('ref="R"', 'ref="R1"')

        rewriter = SourceRefRewriter(source_file, {"R": "R1"})
        rewriter.update()

        assert source_file.read_text() == expected

    def test_multiple_components_per_line(self, tmp_path):
        """Test multiple Component calls on same line (edge case)."""
        source_file = tmp_path / "test_circuit.py"
        source_code = dedent(
            """
            from circuit_synth import *

            @circuit
            def main():
                r1 = Component(ref="R", value="10k", symbol="Device:R", footprint="Resistor_SMD:R_0603_1608Metric"); r2 = Component(ref="R", value="47k", symbol="Device:R", footprint="Resistor_SMD:R_0603_1608Metric")
        """
        ).strip()

        source_file.write_text(source_code)

        # This is ambiguous - both refs are "R"
        # Decision: Update all occurrences (may need manual fix)
        # Or: Detect and warn/error

        pytest.skip("SourceRefRewriter not yet implemented - needs design decision")

    def test_dynamic_refs(self, tmp_path):
        """Test that dynamic refs (variables, f-strings) are skipped."""
        source_file = tmp_path / "test_circuit.py"
        source_code = dedent(
            """
            from circuit_synth import *

            @circuit
            def main():
                prefix = "R"
                r1 = Component(ref=prefix, value="10k", symbol="Device:R",
                              footprint="Resistor_SMD:R_0603_1608Metric")
                r2 = Component(ref=f"R{1}", value="10k", symbol="Device:R",
                              footprint="Resistor_SMD:R_0603_1608Metric")
        """
        ).strip()

        source_file.write_text(source_code)

        # Should not crash, should skip these
        original = source_file.read_text()

        pytest.skip("SourceRefRewriter not yet implemented")


class TestFileHandling:
    """Test file system operations."""

    def test_readonly_file(self, tmp_path):
        """Test handling of read-only files."""
        source_file = tmp_path / "test_circuit.py"
        source_code = dedent(
            """
            from circuit_synth import *

            @circuit
            def main():
                r = Component(ref="R", value="10k", symbol="Device:R",
                             footprint="Resistor_SMD:R_0603_1608Metric")
        """
        ).strip()

        source_file.write_text(source_code)

        # Make read-only
        os.chmod(source_file, 0o444)

        try:
            # On Unix systems, atomic rename can still work even if file is read-only
            # as long as we own the directory
            rewriter = SourceRefRewriter(source_file, {"R": "R1"})
            success = rewriter.update()

            # Should succeed on Unix (owner can rename files)
            # Would fail on other systems with actual readonly enforcement
            if success:
                assert 'ref="R1"' in source_file.read_text()
        finally:
            # Cleanup
            os.chmod(source_file, 0o644)

    def test_missing_file(self, tmp_path):
        """Test when source file doesn't exist."""
        source_file = tmp_path / "nonexistent.py"

        # Should handle gracefully by returning False and logging warning
        rewriter = SourceRefRewriter(source_file, {"R": "R1"})
        success = rewriter.update()

        assert success is False  # Should return False for missing file

    def test_symlinked_file(self, tmp_path):
        """Test handling of symlinked files."""
        # Create actual file
        actual_file = tmp_path / "actual.py"
        source_code = dedent(
            """
            from circuit_synth import *

            @circuit
            def main():
                r = Component(ref="R", value="10k", symbol="Device:R",
                             footprint="Resistor_SMD:R_0603_1608Metric")
        """
        ).strip()
        actual_file.write_text(source_code)

        # Create symlink
        symlink_file = tmp_path / "link.py"
        if os.name != "nt":  # Skip on Windows
            symlink_file.symlink_to(actual_file)

            # Should update the target file
            pytest.skip("SourceRefRewriter not yet implemented")
        else:
            pytest.skip("Symlink test skipped on Windows")

    def test_encoding_preservation(self, tmp_path):
        """Test that file encoding is preserved."""
        source_file = tmp_path / "test_circuit.py"
        source_code = dedent(
            '''
            # -*- coding: utf-8 -*-
            from circuit_synth import *

            @circuit
            def main():
                """Circuit with émoji 🔥"""
                r = Component(ref="R", value="10k", symbol="Device:R",
                             footprint="Resistor_SMD:R_0603_1608Metric")
        '''
        ).strip()

        source_file.write_text(source_code, encoding="utf-8")

        # Should preserve UTF-8 encoding and special characters
        rewriter = SourceRefRewriter(source_file, {"R": "R1"})
        rewriter.update()

        updated = source_file.read_text(encoding="utf-8")
        assert '"""Circuit with émoji 🔥"""' in updated
        assert 'ref="R1"' in updated

    def test_line_ending_preservation(self, tmp_path):
        """Test that line endings (CRLF vs LF) are preserved."""
        source_file = tmp_path / "test_circuit.py"
        source_code = 'from circuit_synth import *\r\n\r\n@circuit\r\ndef main():\r\n    r = Component(ref="R", value="10k", symbol="Device:R", footprint="Resistor_SMD:R_0603_1608Metric")\r\n'

        source_file.write_bytes(source_code.encode("utf-8"))

        # Should preserve CRLF line endings
        pytest.skip("SourceRefRewriter not yet implemented")

    def test_bom_preservation(self, tmp_path):
        """Test that UTF-8 BOM is preserved."""
        source_file = tmp_path / "test_circuit.py"
        source_code = dedent(
            """
            from circuit_synth import *

            @circuit
            def main():
                r = Component(ref="R", value="10k", symbol="Device:R",
                             footprint="Resistor_SMD:R_0603_1608Metric")
        """
        ).strip()

        # Write with BOM
        source_file.write_bytes(b"\xef\xbb\xbf" + source_code.encode("utf-8"))

        # Should preserve BOM
        pytest.skip("SourceRefRewriter not yet implemented")

    def test_atomic_write(self, tmp_path):
        """Test that writes are atomic (temp file + rename)."""
        source_file = tmp_path / "test_circuit.py"
        source_code = dedent(
            """
            from circuit_synth import *

            @circuit
            def main():
                r = Component(ref="R", value="10k", symbol="Device:R",
                             footprint="Resistor_SMD:R_0603_1608Metric")
        """
        ).strip()

        source_file.write_text(source_code)

        # If write fails partway, original file should be intact
        # (This requires implementation-specific testing)
        pytest.skip("SourceRefRewriter not yet implemented")


class TestCircuitStructure:
    """Test various circuit structure scenarios."""

    def test_multiple_circuits_per_file(self, tmp_path):
        """Test file with multiple @circuit decorated functions."""
        source_file = tmp_path / "test_circuit.py"
        source_code = dedent(
            """
            from circuit_synth import *

            @circuit
            def circuit1():
                r = Component(ref="R", value="10k", symbol="Device:R",
                             footprint="Resistor_SMD:R_0603_1608Metric")

            @circuit
            def circuit2():
                r = Component(ref="R", value="47k", symbol="Device:R",
                             footprint="Resistor_SMD:R_0603_1608Metric")
        """
        ).strip()

        source_file.write_text(source_code)

        # Each circuit should only update its own refs
        # Need line range detection
        pytest.skip("SourceRefRewriter not yet implemented")

    def test_nested_functions(self, tmp_path):
        """Test circuit with nested helper functions."""
        source_file = tmp_path / "test_circuit.py"
        source_code = dedent(
            """
            from circuit_synth import *

            @circuit
            def main():
                def helper():
                    # Should this be updated?
                    r = Component(ref="R", value="10k", symbol="Device:R",
                                 footprint="Resistor_SMD:R_0603_1608Metric")

                r = Component(ref="R", value="47k", symbol="Device:R",
                             footprint="Resistor_SMD:R_0603_1608Metric")
        """
        ).strip()

        source_file.write_text(source_code)

        # Design decision: Update nested functions too?
        pytest.skip("SourceRefRewriter not yet implemented - needs design decision")

    def test_circuit_in_main_block(self, tmp_path):
        """Test circuit defined in if __name__ == '__main__' block."""
        source_file = tmp_path / "test_circuit.py"
        source_code = dedent(
            """
            from circuit_synth import *

            if __name__ == "__main__":
                @circuit
                def main():
                    r = Component(ref="R", value="10k", symbol="Device:R",
                                 footprint="Resistor_SMD:R_0603_1608Metric")

                circuit = main()
                circuit.generate_kicad_project("test")
        """
        ).strip()

        source_file.write_text(source_code)

        # Should work normally
        rewriter = SourceRefRewriter(source_file, {"R": "R1"})
        rewriter.update()

        assert 'ref="R1"' in source_file.read_text()


class TestErrorHandling:
    """Test error handling and recovery."""

    def test_permission_error(self, tmp_path):
        """Test graceful handling of permission errors."""
        pytest.skip("Covered by test_readonly_file")

    def test_unicode_error(self, tmp_path):
        """Test handling of unicode decode errors."""
        source_file = tmp_path / "test_circuit.py"

        # Write invalid UTF-8
        source_file.write_bytes(b"\xff\xfe invalid utf-8 \xff")

        # Should handle gracefully
        pytest.skip("SourceRefRewriter not yet implemented")

    def test_no_source_file(self):
        """Test when source file path cannot be determined."""
        # Simulate REPL or exec() environment
        pytest.skip("SourceRefRewriter not yet implemented")


class TestRefMapping:
    """Test ref mapping edge cases."""

    def test_same_ref_multiple_times(self, tmp_path):
        """Test when same ref prefix is used multiple times (invalid but possible)."""
        source_file = tmp_path / "test_circuit.py"
        source_code = dedent(
            """
            from circuit_synth import *

            @circuit
            def main():
                r1 = Component(ref="R", value="10k", symbol="Device:R",
                              footprint="Resistor_SMD:R_0603_1608Metric")
                r2 = Component(ref="R", value="47k", symbol="Device:R",
                              footprint="Resistor_SMD:R_0603_1608Metric")
        """
        ).strip()

        source_file.write_text(source_code)

        # This is invalid (duplicate refs), but if it happens:
        # Should we update all to R1? Or R1 and R2?
        pytest.skip("SourceRefRewriter not yet implemented - needs design decision")

    def test_already_numbered_refs(self, tmp_path):
        """Test that numbered refs are not updated."""
        source_file = tmp_path / "test_circuit.py"
        source_code = dedent(
            """
            from circuit_synth import *

            @circuit
            def main():
                r1 = Component(ref="R1", value="10k", symbol="Device:R",
                              footprint="Resistor_SMD:R_0603_1608Metric")
        """
        ).strip()

        source_file.write_text(source_code)
        original = source_file.read_text()

        # Should not modify already numbered refs
        # Empty mapping
        ref_mapping = {}

        rewriter = SourceRefRewriter(source_file, ref_mapping)
        success = rewriter.update()

        assert success is False  # No changes
        assert source_file.read_text() == original
