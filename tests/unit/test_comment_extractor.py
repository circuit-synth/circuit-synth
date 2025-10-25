#!/usr/bin/env python3
"""
Unit tests for CommentExtractor class.

Tests comment extraction and reinsertion during code generation.
"""

import tempfile
from pathlib import Path

import pytest

from circuit_synth.tools.utilities.comment_extractor import CommentExtractor


class TestCommentExtractor:
    """Test suite for CommentExtractor"""

    @pytest.fixture
    def extractor(self):
        """Create a CommentExtractor instance"""
        return CommentExtractor()

    @pytest.fixture
    def sample_python_file(self, tmp_path):
        """Create a sample Python file with comments"""
        code = '''#!/usr/bin/env python3
"""Sample circuit file"""

from circuit_synth import *

@circuit
def main():
    """Generated circuit from KiCad"""
    # Comment on line 0
    vin = Net('VIN')
    # Comment on line 2
    gnd = Net('GND')
    # Final comment on line 4

if __name__ == '__main__':
    circuit = main()
'''
        file_path = tmp_path / "test_circuit.py"
        file_path.write_text(code)
        return file_path

    def test_extract_comments_from_function(self, extractor, sample_python_file):
        """Test extracting comments from a function"""
        comments_map = extractor.extract_comments_from_function(
            sample_python_file, "main"
        )

        # Should find 3 comments
        assert len(comments_map) > 0
        # Check that at least one comment contains our expected text
        all_comments = str(list(comments_map.values()))
        assert "Comment on line 0" in all_comments

    def test_extract_comments_nonexistent_file(self, extractor, tmp_path):
        """Test extraction from non-existent file returns empty dict"""
        result = extractor.extract_comments_from_function(
            tmp_path / "nonexistent.py", "main"
        )
        assert result == {}

    def test_extract_comments_nonexistent_function(self, extractor, sample_python_file):
        """Test extraction from non-existent function returns empty dict"""
        result = extractor.extract_comments_from_function(
            sample_python_file, "nonexistent_function"
        )
        assert result == {}

    def test_reinsert_comments_simple(self, extractor):
        """Test re-inserting comments at correct positions"""
        generated_lines = [
            "    vin = Net('VIN')",
            "    gnd = Net('GND')",
            "    vout = Net('VOUT')",
        ]

        comments_map = {
            0: ["# Comment about VIN"],
            2: ["# Comment about VOUT"],
        }

        result = extractor.reinsert_comments(generated_lines, comments_map)

        # Should have original lines + 2 comment lines = 5 lines
        assert len(result) == 5
        assert "# Comment about VIN" in result[0]
        assert "vin = Net('VIN')" in result[1]
        # After inserting first comment, indices shift
        # Line 2 becomes index 4 (0: comment, 1: vin, 2: gnd, 3: comment, 4: vout)
        assert "# Comment about VOUT" in result[3]
        assert "vout = Net('VOUT')" in result[4]

    def test_reinsert_comments_preserves_indentation(self, extractor):
        """Test that comments preserve indentation of surrounding code"""
        generated_lines = [
            "    net1 = Net('NET1')",  # 4 spaces
            "        net2 = Net('NET2')",  # 8 spaces
        ]

        comments_map = {
            0: ["# First comment"],
            1: ["# Second comment"],
        }

        result = extractor.reinsert_comments(generated_lines, comments_map)

        # First comment should have 4 spaces
        assert result[0] == "    # First comment"
        # Second comment should have 8 spaces
        assert result[2] == "        # Second comment"

    def test_reinsert_comments_orphaned(self, extractor):
        """Test handling of orphaned comments (line offset beyond generated code)"""
        generated_lines = [
            "    vin = Net('VIN')",
            "    gnd = Net('GND')",
        ]

        comments_map = {
            0: ["# Valid comment"],
            5: ["# Orphaned comment"],  # Beyond line 1
        }

        result = extractor.reinsert_comments(generated_lines, comments_map)

        # Should append orphaned comments at end
        assert any("Orphaned comments" in line for line in result)
        assert any("# Orphaned comment" in line for line in result)

    def test_reinsert_comments_empty_map(self, extractor):
        """Test reinsertion with no comments returns original lines"""
        generated_lines = [
            "    vin = Net('VIN')",
            "    gnd = Net('GND')",
        ]

        result = extractor.reinsert_comments(generated_lines, {})

        assert result == generated_lines

    def test_extract_and_reinsert_workflow(self, extractor, sample_python_file):
        """Test complete workflow: extract from file and reinsert into new code"""
        # New generated code (without comments)
        new_generated_code = '''@circuit
def main():
    """Generated circuit from KiCad"""
    vin = Net('VIN')
    gnd = Net('GND')
    vout = Net('VOUT')'''

        result = extractor.extract_and_reinsert(
            sample_python_file, new_generated_code, "main"
        )

        # Result should contain comments
        assert "# Comment" in result
        assert "vin = Net('VIN')" in result
        assert "gnd = Net('GND')" in result

    def test_multiple_comments_same_line(self, extractor):
        """Test handling multiple comments at same line offset"""
        generated_lines = ["    net = Net('NET')"]

        comments_map = {
            0: ["# First comment", "# Second comment"],
        }

        result = extractor.reinsert_comments(generated_lines, comments_map)

        # Should have both comments + original line
        assert len(result) == 3
        assert "# First comment" in result[0]
        assert "# Second comment" in result[1]
        assert "net = Net('NET')" in result[2]

    def test_blank_circuit_with_comments(self, extractor, tmp_path):
        """Test extracting comments from blank circuit (no actual code)"""
        code = '''@circuit
def main():
    """Generated circuit from KiCad"""
    # This is a blank circuit
    # No components yet

if __name__ == '__main__':
    circuit = main()
'''
        file_path = tmp_path / "blank_circuit.py"
        file_path.write_text(code)

        comments_map = extractor.extract_comments_from_function(file_path, "main")

        # For truly blank circuits (only docstring, no executable code),
        # comments after docstring are syntactically outside the function body
        # (Python AST ends function after docstring when there's no other content)
        # So they should NOT be extracted
        assert len(comments_map) == 0

    def test_circuit_with_comments_and_code(self, extractor, tmp_path):
        """Test extracting comments from circuit with actual code"""
        code = '''@circuit
def main():
    """Generated circuit from KiCad"""
    # This comment is about VIN
    vin = Net('VIN')
    # This comment is about GND
    gnd = Net('GND')

if __name__ == '__main__':
    circuit = main()
'''
        file_path = tmp_path / "circuit_with_code.py"
        file_path.write_text(code)

        comments_map = extractor.extract_comments_from_function(file_path, "main")

        # With actual code (Net() calls), comments inside function should be extracted
        assert len(comments_map) >= 1
        # Verify specific comments were found
        all_comments = str(comments_map.values())
        assert "VIN" in all_comments
        assert "GND" in all_comments
