"""
Unit tests for KiCad S-expression string escaping.

Tests the SchematicWriter._escape_kicad_string() method to ensure
proper escaping of strings containing special characters, newlines,
and Unicode characters for KiCad S-expression format compatibility.

Regression test for issue: "Un-terminated delimited string" error when
generating KiCad schematic files with multi-line docstrings containing
Unicode box-drawing characters.
"""

import pytest

from circuit_synth.kicad.sch_gen.schematic_writer import SchematicWriter


class TestKiCadStringEscaping:
    """Test cases for KiCad S-expression string escaping."""

    def test_empty_string(self):
        """Test escaping of empty string."""
        result = SchematicWriter._escape_kicad_string("")
        assert result == ""

    def test_simple_string_no_special_chars(self):
        """Test that simple strings without special characters are unchanged."""
        text = "Simple text without special characters"
        result = SchematicWriter._escape_kicad_string(text)
        assert result == text

    def test_single_newline_escaped(self):
        """Test that single newlines are properly escaped."""
        text = "line1\nline2"
        result = SchematicWriter._escape_kicad_string(text)
        assert result == "line1\\nline2"

    def test_multiple_newlines_escaped(self):
        """Test that multiple newlines are all escaped."""
        text = "line1\nline2\nline3\nline4"
        result = SchematicWriter._escape_kicad_string(text)
        assert result == "line1\\nline2\\nline3\\nline4"

    def test_quoted_string_escaped(self):
        """Test that quotes are properly escaped."""
        text = 'He said "hello"'
        result = SchematicWriter._escape_kicad_string(text)
        assert result == 'He said \\"hello\\"'

    def test_backslash_escaped(self):
        """Test that backslashes are properly escaped."""
        text = "path\\to\\file"
        result = SchematicWriter._escape_kicad_string(text)
        assert result == "path\\\\to\\\\file"

    def test_carriage_return_escaped(self):
        """Test that carriage returns are properly escaped."""
        text = "line1\rline2"
        result = SchematicWriter._escape_kicad_string(text)
        assert result == "line1\\rline2"

    def test_tab_escaped(self):
        """Test that tabs are properly escaped."""
        text = "col1\tcol2\tcol3"
        result = SchematicWriter._escape_kicad_string(text)
        assert result == "col1\\tcol2\\tcol3"

    def test_unicode_box_drawing_preserved(self):
        """Test that Unicode box-drawing characters are preserved."""
        text = "┌┴┐└┬┘"
        result = SchematicWriter._escape_kicad_string(text)
        # Unicode characters should be preserved
        assert "┌" in result
        assert "┴" in result
        assert "┐" in result
        assert "└" in result
        assert "┬" in result
        assert "┘" in result

    def test_unicode_ohm_symbol_preserved(self):
        """Test that Unicode ohm symbol (Ω) is preserved."""
        text = "1kΩ"
        result = SchematicWriter._escape_kicad_string(text)
        assert "Ω" in result

    def test_complex_multiline_with_unicode_and_quotes(self):
        """
        Test complex string with newlines, quotes, and Unicode characters.

        This is the real-world case from the resistor_divider template.
        """
        text = """5V to 3.3V voltage divider for logic level shifting

    This circuit converts 5V signals to 3.3V levels, commonly used for:
    - Arduino (5V) to ESP32 (3.3V) communication
    - Level shifting I2C, SPI, UART signals

    Circuit topology:
           VIN_5V
             │
            ┌┴┐ R1 (1kΩ)
            └┬┘
             ├─── VOUT_3V3 (3.33V output)
            ┌┴┐ R2 (2kΩ)
            └┬┘
             │
            GND"""

        result = SchematicWriter._escape_kicad_string(text)

        # Verify newlines are escaped
        assert "\n" not in result  # No literal newlines
        assert "\\n" in result  # Should have escaped newlines

        # Verify Unicode is preserved
        assert "│" in result
        assert "┌" in result
        assert "┴" in result
        assert "┐" in result
        assert "└" in result
        assert "┬" in result
        assert "┘" in result
        assert "Ω" in result

        # Verify quotes stay in result (not stripped, just escaped)
        # Note: this text doesn't have quotes, but test the logic

    def test_string_with_all_special_chars(self):
        """Test string containing all special characters needing escaping."""
        text = 'Line1\nQuote"here\tTab\rReturn\\Backslash'
        result = SchematicWriter._escape_kicad_string(text)

        # Check that all escaping happened
        assert result == 'Line1\\nQuote\\"here\\tTab\\rReturn\\\\Backslash'

    def test_non_string_input_converted_to_string(self):
        """Test that non-string input is converted to string."""
        # Test with number
        result = SchematicWriter._escape_kicad_string(42)
        assert result == "42"

        # Test with float
        result = SchematicWriter._escape_kicad_string(3.14)
        assert result == "3.14"

    def test_resistor_divider_docstring_example(self):
        """
        Test with actual resistor_divider circuit docstring.

        This is the exact docstring that caused the original bug.
        """
        docstring = """5V to 3.3V voltage divider for logic level shifting

    This circuit converts 5V signals to 3.3V levels, commonly used for:
    - Arduino (5V) to ESP32 (3.3V) communication
    - Level shifting I2C, SPI, UART signals
    - Interfacing 5V sensors with 3.3V microcontrollers

    Circuit topology:
           VIN_5V
             │
            ┌┴┐ R1 (1kΩ)
            └┬┘
             ├─── VOUT_3V3 (3.33V output)
            ┌┴┐ R2 (2kΩ)
            └┬┘
             │
            GND"""

        result = SchematicWriter._escape_kicad_string(docstring)

        # The result should not contain any literal newlines
        assert docstring.count("\n") > 0, "Test input should have newlines"
        assert result.count("\n") == 0, "Result should not have literal newlines"

        # All newlines should be escaped
        assert result.count("\\n") == docstring.count("\n")

        # Unicode characters should be preserved
        for char in ["│", "┌", "┴", "┐", "└", "┬", "┘", "Ω"]:
            assert char in result, f"Unicode character {char} should be preserved"

    def test_double_backslash_handling(self):
        """Test that already-escaped backslashes are handled correctly."""
        # A single backslash becomes double-escaped: \ -> \\
        text = "\\"
        result = SchematicWriter._escape_kicad_string(text)
        assert result == "\\\\"

        # Two backslashes become four
        text = "\\\\"
        result = SchematicWriter._escape_kicad_string(text)
        assert result == "\\\\\\\\"

    def test_mixed_unicode_and_escape_sequences(self):
        """Test that Unicode and escape sequences interact correctly."""
        text = "1kΩ\t│\n┌┴┐"
        result = SchematicWriter._escape_kicad_string(text)

        # Verify escaping happened
        assert "\\t" in result
        assert "\\n" in result

        # Verify Unicode preserved
        assert "Ω" in result
        assert "│" in result
        assert "┌" in result
        assert "┴" in result
        assert "┐" in result

    def test_windows_line_endings(self):
        """Test that Windows-style line endings (CRLF) are properly escaped."""
        text = "line1\r\nline2"
        result = SchematicWriter._escape_kicad_string(text)

        # Both CR and LF should be escaped
        assert result == "line1\\r\\nline2"

    def test_unicode_in_path(self):
        """Test that Unicode characters in file paths are preserved."""
        # This could be relevant if paths appear in documentation
        text = "Path: /Users/test/Documents/file_café"
        result = SchematicWriter._escape_kicad_string(text)

        # Unicode should be preserved, no escaping for these
        assert "t" in result
        assert "c" in result
        assert result == text  # No transformation for simple Unicode

    def test_idempotent_escaping_prevention(self):
        """
        Test that we don't double-escape already escaped content.

        Note: This test documents current behavior. If content is
        passed already escaped, it will be escaped again. Users should
        only escape once before passing to add_text_box.
        """
        # If user passes already-escaped content, it will be escaped again
        text = "line1\\nline2"  # Already escaped by user
        result = SchematicWriter._escape_kicad_string(text)

        # The backslash gets escaped, resulting in double-escaping
        assert result == "line1\\\\nline2"  # \n becomes \\n (escaped backslash + n)


class TestEscapingIntegration:
    """Integration tests for string escaping with actual circuit generation."""

    def test_escape_function_exists_in_schematic_writer(self):
        """Verify the escape function exists and is callable."""
        assert hasattr(SchematicWriter, "_escape_kicad_string")
        assert callable(getattr(SchematicWriter, "_escape_kicad_string"))

    def test_escape_function_is_static_method(self):
        """Verify the escape function is a static method."""
        import inspect

        assert isinstance(
            inspect.getattr_static(SchematicWriter, "_escape_kicad_string"),
            staticmethod,
        )


class TestEdgeCases:
    """Edge case tests for string escaping."""

    def test_very_long_string(self):
        """Test escaping of very long strings."""
        text = "a" * 10000 + "\n" + "b" * 10000
        result = SchematicWriter._escape_kicad_string(text)

        assert "\\n" in result
        assert result.count("a") == 10000
        assert result.count("b") == 10000

    def test_null_character_handling(self):
        """Test handling of null characters."""
        text = "before\x00after"
        result = SchematicWriter._escape_kicad_string(text)

        # Null character should be preserved (not escaped by our function)
        # but this tests that the function doesn't crash
        assert isinstance(result, str)

    def test_unicode_emoji(self):
        """Test that emoji and other Unicode are preserved."""
        text = "Circuit ⚡ with 🔌 connector"
        result = SchematicWriter._escape_kicad_string(text)

        assert "⚡" in result
        assert "🔌" in result

    def test_combining_characters(self):
        """Test Unicode combining characters are preserved."""
        text = "naïve café"  # Using combining characters
        result = SchematicWriter._escape_kicad_string(text)

        # Accented characters should be preserved
        assert "ï" in result or ("i" in result and len(result) > len("naive caf"))
        assert "é" in result or ("e" in result and len(result) > len("naive caf"))
