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
        Extract all comments from a specific function with line offsets.

        Args:
            file_path: Path to Python file
            function_name: Name of function to extract comments from

        Returns:
            Dictionary mapping line offset (relative to function start) to list of comments
            Example: {0: ["# Comment on first line"], 2: ["# Comment on third line"]}
        """
        if not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return {}

        try:
            # Parse AST to find function boundaries
            with open(file_path, "r") as f:
                source_code = f.read()

            tree = ast.parse(source_code)
            function_start_line = self._find_function_start_line(tree, function_name)

            if function_start_line is None:
                logger.warning(f"Function '{function_name}' not found in {file_path}")
                return {}

            # Extract comments using tokenize
            comments_map = self._extract_comments_with_tokenize(
                file_path, function_start_line
            )

            logger.info(
                f"Extracted {len(comments_map)} comment locations from {function_name}()"
            )
            return comments_map

        except Exception as e:
            logger.error(f"Failed to extract comments: {e}")
            return {}

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

    def _extract_comments_with_tokenize(
        self, file_path: Path, function_start_line: int
    ) -> Dict[int, List[str]]:
        """
        Extract comments using the tokenize module.

        Args:
            file_path: Path to Python file
            function_start_line: Line number where function body starts

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

                        # Calculate offset relative to function start
                        line_offset = line_num - function_start_line

                        # Only include comments inside or after the function
                        if line_offset >= 0:
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
        Re-insert comments into generated code at their original line offsets.

        Args:
            generated_lines: List of generated code lines (without comments)
            comments_map: Dictionary mapping line offsets to comments

        Returns:
            List of code lines with comments re-inserted
        """
        if not comments_map:
            return generated_lines

        result_lines = []
        max_line_offset = len(generated_lines) - 1

        for line_offset, line in enumerate(generated_lines):
            # Get comments for this line offset
            comments = comments_map.get(line_offset, [])

            # Insert comments before the line content
            for comment in comments:
                # Preserve indentation of the current line
                indent = self._get_indentation(line)
                result_lines.append(f"{indent}{comment}")

            # Add the actual code line
            result_lines.append(line)

        # Handle orphaned comments (line offsets beyond generated code)
        orphaned_offsets = [
            offset for offset in comments_map.keys() if offset > max_line_offset
        ]

        if orphaned_offsets:
            logger.info(
                f"Found {len(orphaned_offsets)} orphaned comments, appending to end"
            )
            result_lines.append("")
            result_lines.append("    # Orphaned comments from previous version:")

            for offset in sorted(orphaned_offsets):
                for comment in comments_map[offset]:
                    result_lines.append(f"    {comment}")

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
            logger.info("No comments found to preserve")
            return generated_code

        # Find the function in generated code
        generated_lines = generated_code.split("\n")
        function_start_idx = self._find_function_start_index(
            generated_lines, function_name
        )

        if function_start_idx is None:
            logger.warning(
                f"Function '{function_name}' not found in generated code, cannot reinsert comments"
            )
            return generated_code

        # Split code into: before function, function body, after function
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
        Find the line index where a function body starts in a list of code lines.

        Args:
            lines: List of code lines
            function_name: Name of function to find

        Returns:
            Line index (0-indexed) where function body starts, or None if not found
        """
        in_function = False
        decorator_or_def_found = False

        for i, line in enumerate(lines):
            stripped = line.strip()

            # Look for @circuit decorator or def function_name
            if stripped.startswith("@circuit") or stripped.startswith(
                f"def {function_name}("
            ):
                decorator_or_def_found = True
                in_function = True
                continue

            # If we're in the function, find the first non-docstring, non-empty line
            if in_function and decorator_or_def_found:
                # Skip docstrings
                if stripped.startswith('"""') or stripped.startswith("'''"):
                    continue

                # Skip empty lines
                if not stripped:
                    continue

                # This is the first real line of the function body
                return i

        return None
