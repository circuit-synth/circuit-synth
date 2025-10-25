#!/usr/bin/env python3
"""
Comment extraction and preservation for Python code generation.

This module provides utilities to extract comments from Python source files
and re-insert them during code regeneration, preserving user annotations
across KiCad ↔ Python synchronization cycles.
"""

import ast
import logging
import tokenize
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class CommentExtractor:
    """Extract and preserve comments from Python source code."""

    def __init__(self):
        """Initialize the comment extractor."""
        pass

    def extract_comments_from_function(
        self, file_path: Path, function_name: str = "main"
    ) -> Dict[int, List[str]]:
        """
        Extract all user-added content from a specific function.

        This includes comments, inline docstrings, and any other code.
        We extract everything after the first docstring to preserve it.

        Args:
            file_path: Path to Python file
            function_name: Name of function to extract content from

        Returns:
            Dictionary mapping line offset (relative to function start) to list of content lines
            Example: {0: ["# Comment"], 2: ['docstring content']}
        """
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return {}

        try:
            # Parse AST to find function boundaries
            with open(file_path, "r") as f:
                lines = f.readlines()

            tree = ast.parse("".join(lines))
            function_start_line = self._find_function_start_line(tree, function_name)
            function_end_line = self._find_function_end_line(tree, function_name, file_path)

            if function_start_line is None:
                logger.warning(f"Function '{function_name}' not found in {file_path}")
                return {}

            # Find the def line to check for docstring
            def_line_num = self._find_def_line(lines, function_name)

            # Check if there's a docstring on the line after def
            content_start_line = function_start_line
            if def_line_num is not None and (def_line_num + 1) < len(lines):
                # Look at the line after def (def_line_num is 0-indexed)
                line_after_def = lines[def_line_num + 1].strip()
                if line_after_def.startswith('"""') or line_after_def.startswith("'''"):
                    # Skip the docstring line - start extraction from next line
                    content_start_line = function_start_line + 1

            # Extract ALL lines from the function body (after docstring), including blank lines
            # This preserves spacing between comment groups
            content_map = {}
            for line_num in range(content_start_line, function_end_line + 1):
                line_idx = line_num - 1  # Convert to 0-indexed
                if line_idx < len(lines):
                    line = lines[line_idx].rstrip()  # Keep indentation, remove trailing whitespace
                    # Include ALL lines - blank lines preserve spacing
                    offset = line_num - content_start_line
                    if offset not in content_map:
                        content_map[offset] = []
                    content_map[offset].append(line)

            logger.info(
                f"Extracted {len(content_map)} content lines from {function_name}()"
            )
            return content_map

        except Exception as e:
            logger.error(f"Failed to extract content: {e}")
            return {}

    def _find_def_line(self, lines: List[str], function_name: str) -> Optional[int]:
        """
        Find the line index (0-indexed) of the def statement for a function.

        Args:
            lines: List of lines from the file
            function_name: Name of function to find

        Returns:
            Line index (0-indexed) of the def line, or None if not found
        """
        for i, line in enumerate(lines):
            if line.strip().startswith(f"def {function_name}("):
                return i
        return None

    def _find_function_start_line(
        self, tree: ast.AST, function_name: str
    ) -> Optional[int]:
        """
        Find the starting line number of a function in the AST.

        Args:
            tree: Parsed AST tree
            function_name: Name of function to find

        Returns:
            Line number (1-indexed) of function definition, or None if not found
        """
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                # Return the line number of the function body start (after decorator/def line)
                return node.body[0].lineno if node.body else node.lineno
        return None

    def _find_function_end_line(
        self, tree: ast.AST, function_name: str, file_path: Path
    ) -> Optional[int]:
        """
        Find the ending line number of a function by analyzing indentation.

        Since Python's AST doesn't include comments, we need to find where
        the function body ACTUALLY ends by looking at indentation levels.

        Args:
            tree: Parsed AST tree
            function_name: Name of function to find
            file_path: Path to the source file for indentation analysis

        Returns:
            Line number (1-indexed) of last line with function-level indentation
        """
        ast_end_line = None
        function_indent = None

        # First, find the function definition to get AST end line
        for node in ast.walk(tree):
            if isinstance(node, ast.FunctionDef) and node.name == function_name:
                ast_end_line = node.end_lineno
                break

        if ast_end_line is None:
            return None

        # Now scan the file to find actual function end by indentation
        with open(file_path, "r") as f:
            lines = f.readlines()

        # Find the def line and determine function indentation
        def_line_idx = None
        function_indent = None
        for i, line in enumerate(lines):  # 0-indexed
            if line.strip().startswith(f"def {function_name}("):
                # Function indentation is the indentation of the def line
                function_indent = len(line) - len(line.lstrip())
                def_line_idx = i
                break

        if function_indent is None or def_line_idx is None:
            return ast_end_line

        # Scan forward from AFTER the def line to find where function ends
        # The function ends when we find a line with content at or before function indent
        last_function_line = ast_end_line

        for i in range(def_line_idx + 1, len(lines)):  # Start AFTER def line
            line = lines[i]

            # Empty lines are ambiguous - tentatively include them
            if not line.strip():
                last_function_line = i + 1  # Convert to 1-indexed
                continue

            # Get indentation of this line
            line_indent = len(line) - len(line.lstrip())

            # If indentation is greater than function indent, it's part of function
            if line_indent > function_indent:
                last_function_line = i + 1  # Convert to 1-indexed
            else:
                # Found a line at or before function indent level - function ends BEFORE this line
                break

        return last_function_line

    def _extract_comments_with_tokenize(
        self, file_path: Path, function_start_line: int, function_end_line: Optional[int] = None
    ) -> Dict[int, List[str]]:
        """
        Extract comments using the tokenize module.

        Args:
            file_path: Path to Python file
            function_start_line: Line number where function body starts
            function_end_line: Line number where function ends (optional, for bounds checking)

        Returns:
            Dictionary mapping line offset to comments
        """
        comments_map: Dict[int, List[str]] = {}

        try:
            with open(file_path, "rb") as f:
                tokens = tokenize.tokenize(f.readline)

                for tok in tokens:
                    if tok.type == tokenize.COMMENT:
                        line_num = tok.start[0]  # 1-indexed line number
                        comment_text = tok.string  # Includes the '#'

                        # Only include comments within function bounds
                        if line_num < function_start_line:
                            continue
                        if function_end_line is not None and line_num > function_end_line:
                            continue

                        # Calculate offset relative to function start
                        line_offset = line_num - function_start_line

                        if line_offset not in comments_map:
                            comments_map[line_offset] = []
                        comments_map[line_offset].append(comment_text)

        except tokenize.TokenError as e:
            logger.warning(f"Tokenization error: {e}")

        return comments_map

    def reinsert_comments(
        self, generated_lines: List[str], comments_map: Dict[int, List[str]]
    ) -> List[str]:
        """
        Re-insert user content as a block at the start of the function body.

        Simple strategy: Insert ALL user content right at the beginning of the function,
        preserving order and original formatting. This is idempotent.

        Args:
            generated_lines: List of generated code lines (from after docstring)
            comments_map: Dictionary mapping line offsets to content lines

        Returns:
            List of code lines with user content prepended
        """
        if not comments_map:
            return generated_lines

        # Collect all content lines in order, preserving their original formatting
        all_content = []
        for offset in sorted(comments_map.keys()):
            for content_line in comments_map[offset]:
                # Content lines already have their indentation preserved
                all_content.append(content_line)

        # Insert all content at the beginning
        result_lines = all_content

        # Add the rest of the generated lines
        result_lines.extend(generated_lines)

        return result_lines

    def _get_indentation(self, line: str) -> str:
        """
        Get the indentation (leading whitespace) of a line.

        Args:
            line: Line of code

        Returns:
            String of leading whitespace
        """
        return line[: len(line) - len(line.lstrip())]

    def extract_and_reinsert(
        self,
        existing_file: Path,
        generated_code: str,
        function_name: str = "main",
    ) -> str:
        """
        Complete workflow: extract comments from existing file and reinsert into generated code.

        Args:
            existing_file: Path to existing Python file with comments
            generated_code: Newly generated code (without comments)
            function_name: Name of function to extract/reinsert comments for

        Returns:
            Generated code with comments re-inserted
        """
        # Extract comments from existing file
        comments_map = self.extract_comments_from_function(existing_file, function_name)

        if not comments_map:
            return generated_code

        # Find the function in generated code
        generated_lines = generated_code.split("\n")
        function_start_idx = self._find_function_start_index(
            generated_lines, function_name
        )

        if function_start_idx is None:
            return generated_code

        # Split code into: before function body, function body (from after docstring onwards)
        before_function = generated_lines[:function_start_idx]
        function_body = generated_lines[function_start_idx:]

        # Reinsert comments into function body
        function_with_comments = self.reinsert_comments(function_body, comments_map)

        # Combine all parts
        result_lines = before_function + function_with_comments
        return "\n".join(result_lines)

    def _find_function_start_index(
        self, lines: List[str], function_name: str
    ) -> Optional[int]:
        """
        Find the line index where function body starts (right after docstring).

        Args:
            lines: List of code lines
            function_name: Name of function to find

        Returns:
            Line index (0-indexed) right after the docstring, or None if not found
        """
        # Find the def line
        def_idx = None
        for i, line in enumerate(lines):
            if line.strip().startswith(f"def {function_name}("):
                def_idx = i
                break

        if def_idx is None:
            return None

        # Look for docstring on the next line
        docstring_idx = def_idx + 1
        if docstring_idx < len(lines):
            stripped = lines[docstring_idx].strip()
            if stripped.startswith('"""') or stripped.startswith("'''"):
                # Docstring found - return the line after it
                return docstring_idx + 1

        # No docstring - return line after def
        return def_idx + 1
