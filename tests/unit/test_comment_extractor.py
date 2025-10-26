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
        """Test re-inserting comments as a block at the start"""
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

        # Comments inserted as a block at the beginning
        assert len(result) == 5  # 2 comments + 3 lines
        assert "# Comment about VIN" in result[0]
        assert "# Comment about VOUT" in result[1]
        assert "vin = Net('VIN')" in result[2]
        assert "gnd = Net('GND')" in result[3]
        assert "vout = Net('VOUT')" in result[4]

    def test_reinsert_comments_preserves_indentation(self, extractor):
        """Test that content preserves its original indentation"""
        generated_lines = [
            "    net1 = Net('NET1')",  # 4 spaces
            "        net2 = Net('NET2')",  # 8 spaces
        ]

        # Content map now has full lines with indentation (as extracted)
        comments_map = {
            0: ["    # First comment"],  # With indentation
            1: ["    # Second comment"],  # With indentation
        }

        result = extractor.reinsert_comments(generated_lines, comments_map)

        # Content preserves its original indentation
        assert result[0] == "    # First comment"
        assert result[1] == "    # Second comment"
        assert result[2] == "    net1 = Net('NET1')"
        assert result[3] == "        net2 = Net('NET2')"

    def test_reinsert_comments_orphaned(self, extractor):
        """Test that all comments are inserted regardless of offset"""
        generated_lines = [
            "    vin = Net('VIN')",
            "    gnd = Net('GND')",
        ]

        comments_map = {
            0: ["# Valid comment"],
            5: ["# Comment with high offset"],  # Beyond generated lines
        }

        result = extractor.reinsert_comments(generated_lines, comments_map)

        # All comments inserted at the beginning in order
        assert len(result) == 4  # 2 comments + 2 lines
        assert "# Valid comment" in result[0]
        assert "# Comment with high offset" in result[1]
        assert "vin = Net('VIN')" in result[2]
        assert "gnd = Net('GND')" in result[3]

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

        # With improved indentation-based boundary detection, comments inside
        # the function (even if no executable code) should be extracted
        assert len(comments_map) >= 1
        # Verify specific comments were found
        all_comments = str(comments_map.values())
        assert "blank circuit" in all_comments
        assert "No components" in all_comments

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

    def test_preserves_inline_docstrings(self, extractor, tmp_path):
        """Test that inline docstrings inside function body are preserved"""
        code = '''@circuit
def main():
    """Generated circuit from KiCad"""
    # USER COMMENT: This is my first comment
    # USER COMMENT: This is my second comment
    #

    """
    This is an inline docstring that should be preserved!
    """

if __name__ == '__main__':
    circuit = main()
'''
        file_path = tmp_path / "circuit_with_docstring.py"
        file_path.write_text(code)

        # Test extraction
        comments_map = extractor.extract_comments_from_function(file_path, "main")

        # Should find regular comments
        assert len(comments_map) >= 1
        all_comments = str(comments_map.values())
        assert "USER COMMENT" in all_comments

        # Test round-trip preservation
        generated_code = '''@circuit
def main():
    """Generated circuit from KiCad"""


'''
        result = extractor.extract_and_reinsert(file_path, generated_code, "main")

        # The inline docstring should be preserved in the result
        assert '"""' in result or "'''" in result
        # Look for the inline docstring content (may be reformatted)
        assert "inline docstring" in result.lower() or "preserved" in result.lower()

    def test_does_not_duplicate_function_docstring(self, extractor, tmp_path):
        """Test that function's own docstring is not duplicated during round-trip"""
        code = '''@circuit
def main():
    """Generated circuit from KiCad"""
    # USER COMMENT: This is my first preserved comment!
    # USER COMMENT: This is my second preserved comment!
    #
    #
    #
    """
    look at these!"""

if __name__ == '__main__':
    circuit = main()
'''
        file_path = tmp_path / "circuit_with_comments.py"
        file_path.write_text(code)

        # Generate new code with same docstring
        generated_code = '''@circuit
def main():
    """Generated circuit from KiCad"""


'''
        result = extractor.extract_and_reinsert(file_path, generated_code, "main")

        # Count occurrences of the function docstring
        docstring_count = result.count('"""Generated circuit from KiCad"""')

        # Should only appear ONCE (not duplicated)
        assert (
            docstring_count == 1
        ), f"Expected 1 occurrence of function docstring, found {docstring_count}"

        # User comments should still be preserved
        assert "USER COMMENT" in result
        assert "look at these!" in result

    def test_preserves_blank_lines_between_comments(self, extractor, tmp_path):
        """Test that blank lines between comment groups are preserved"""
        code = '''@circuit
def main():
    """Generated circuit from KiCad"""
    # USER COMMENT: This is my first preserved comment!
    # USER COMMENT: This is my second preserved comment!
    #
    #
    #
    """
    look at these!"""

    # another one!
    # another one!
    # another one!

    # another one!
    # another one!
    # another one!
    """ more comments"""
    """ more comments"""
    """ more comments"""

if __name__ == '__main__':
    circuit = main()
'''
        file_path = tmp_path / "circuit_with_blank_lines.py"
        file_path.write_text(code)

        # Generate new code
        generated_code = '''@circuit
def main():
    """Generated circuit from KiCad"""


'''
        result = extractor.extract_and_reinsert(file_path, generated_code, "main")

        # Should preserve blank lines between comment groups
        # The blank line after "look at these!""" should be preserved
        assert (
            'look at these!"""\n\n    # another one!' in result
            or 'look at these!"""\n    \n    # another one!' in result
        ), "Blank line after inline docstring should be preserved"

        # The blank line between the two "another one!" groups should be preserved
        lines = result.split("\n")

        # Find the lines with "another one!" comments
        another_one_indices = [
            i for i, line in enumerate(lines) if "another one!" in line
        ]

        # Should have 6 occurrences
        assert (
            len(another_one_indices) == 6
        ), f"Expected 6 'another one!' comments, found {len(another_one_indices)}"

        # There should be a blank line in the middle (between index 2 and 3 of the another_one group)
        # Check if there's a gap in the indices
        has_blank_between = (another_one_indices[3] - another_one_indices[2]) > 1
        assert has_blank_between, "Should preserve blank line between comment groups"

    def test_strips_trailing_blank_lines(self, extractor, tmp_path):
        """Test that trailing blank lines at end of function are limited to max 2"""
        code = '''@circuit
def main():
    """Generated circuit from KiCad"""
    # USER COMMENT: This is my first preserved comment!
    """
    look at these!"""

    # another one!
    # another one!
    # another one!

    # another one!
    # another one!
    # another one!
    """ more comments"""
    """ more comments"""
    """ more comments"""

    # suhp?


if __name__ == '__main__':
    circuit = main()
'''
        file_path = tmp_path / "circuit_with_trailing_blanks.py"
        file_path.write_text(code)

        # Generate new code
        generated_code = '''@circuit
def main():
    """Generated circuit from KiCad"""


'''
        result = extractor.merge_preserving_user_content(
            file_path, generated_code, "main"
        )

        # Find where function ends (before the generated circuit comment)
        lines = result.split("\n")

        # Find the last user content line (should be "# suhp?")
        suhp_index = None
        for i, line in enumerate(lines):
            if "suhp?" in line:
                suhp_index = i
                break

        assert suhp_index is not None, "Should find '# suhp?' comment"

        # Check lines after "# suhp?" - should not have excessive blank lines
        # Allow max 2 blank lines after last content
        blank_count = 0
        for i in range(suhp_index + 1, len(lines)):
            line = lines[i]
            if line.strip() == "":
                blank_count += 1
            else:
                break  # Hit non-blank line

        assert (
            blank_count <= 2
        ), f"Should not have more than 2 trailing blank lines, found {blank_count}"

    def test_preserves_all_user_content_comprehensive(self, extractor, tmp_path):
        """Test that ALL user content is preserved across the entire file

        This is CRITICAL - users document design decisions, datasheets, test results, etc.
        We must preserve EVERYTHING except the generated component/net code.
        """
        code = '''#!/usr/bin/env python3
"""
Circuit Generated from KiCad
"""

from circuit_synth import *

# MODULE-LEVEL COMMENT: Design decision - using 0603 resistors for space constraints
# See: https://example.com/datasheet.pdf

VOLTAGE_RAIL = 3.3  # Global constant - main supply voltage

@circuit
def main():
    """Generated circuit from KiCad"""
    # DESIGN NOTE: Power supply section
    # Tested with 10k pull-up, works reliably
    # See lab notebook 2024-10-25 page 42

    """
    CRITICAL: This inline docstring contains test results
    - Measured current: 3.2mA
    - Temperature rise: 2.1°C
    """

    # Signal processing section

"""
POST-FUNCTION NOTE: Additional context about the design
This should be preserved exactly where it is
"""

def helper_function():
    """User added this helper"""
    pass

# Generate the circuit
if __name__ == '__main__':
    circuit = main()
    # USER NOTE: Using specific project name for CI/CD pipeline
    circuit.generate_kicad_project(project_name="main_generated")
    circuit.generate_kicad_netlist("main_generated/main_generated.net")
    # POST-GENERATION NOTE: This runs after generation

# FINAL NOTE: File-level documentation at the end
'''
        file_path = tmp_path / "comprehensive_comments.py"
        file_path.write_text(code)

        # Simulate regeneration - only the main() body changes
        generated_code = '''@circuit
def main():
    """Generated circuit from KiCad"""
    # NEW GENERATED COMPONENT
    r1 = Component("R1")


# Generate the circuit
if __name__ == '__main__':
    circuit = main()
'''

        result = extractor.merge_preserving_user_content(
            file_path, generated_code, "main"
        )

        # Verify ALL user content is preserved
        critical_content = [
            "MODULE-LEVEL COMMENT",
            "0603 resistors",
            "https://example.com/datasheet.pdf",
            "VOLTAGE_RAIL = 3.3",
            "DESIGN NOTE: Power supply section",
            "lab notebook 2024-10-25 page 42",
            "CRITICAL: This inline docstring",
            "Measured current: 3.2mA",
            "Signal processing section",
            "POST-FUNCTION NOTE",
            "helper_function",
            "USER NOTE: Using specific project name",
            "POST-GENERATION NOTE",
            "FINAL NOTE: File-level documentation",
        ]

        for content in critical_content:
            assert content in result, f"LOST USER CONTENT: '{content}'"

        print("✅ All user content preserved:")
        for content in critical_content:
            print(f"   ✓ {content[:50]}...")

    def test_preserves_content_outside_function(self, extractor, tmp_path):
        """Test that content OUTSIDE the function (after function, before if __name__) is preserved"""
        code = '''@circuit
def main():
    """Generated circuit from KiCad"""
    # Inside function comment

"""
one time!
"""

if __name__ == '__main__':
    circuit = main()
'''
        file_path = tmp_path / "circuit_with_outside_content.py"
        file_path.write_text(code)

        # Test the after-function content extraction
        after_function_content = extractor.extract_after_function_content(
            file_path, "main"
        )

        # Should find the docstring between function and if __name__
        assert len(after_function_content) > 0, "Should extract content after function"
        after_function_str = "\n".join(after_function_content)
        assert (
            "one time!" in after_function_str
        ), "Should preserve 'one time!' docstring"

        # Test full round-trip with extract_and_reinsert
        generated_code = '''@circuit
def main():
    """Generated circuit from KiCad"""


# Generate the circuit
if __name__ == '__main__':
    circuit = main()
'''
        result = extractor.extract_and_reinsert(file_path, generated_code, "main")

        # Verify the after-function content is preserved in the result
        assert "one time!" in result, "After-function content should be preserved"
        assert (
            "# Inside function comment" in result
        ), "Inside function comment should be preserved"

        # Verify it's inserted BEFORE "# Generate the circuit"
        lines = result.split("\n")
        one_time_idx = None
        generate_idx = None
        for i, line in enumerate(lines):
            if "one time!" in line:
                one_time_idx = i
            if "# Generate the circuit" in line:
                generate_idx = i

        assert one_time_idx is not None, "Should find 'one time!' in result"
        assert (
            generate_idx is not None
        ), "Should find '# Generate the circuit' in result"
        assert (
            one_time_idx < generate_idx
        ), "After-function content should appear BEFORE boilerplate"
