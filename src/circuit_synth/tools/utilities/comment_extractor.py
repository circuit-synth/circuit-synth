#!/usr/bin/env python3
"""
Comment extraction and preservation for Python code generation.

This module provides utilities to extract comments from Python source files
and re-insert them during code regeneration, preserving user annotations
across KiCad ↔ Python synchronization cycles.
"""

import ast
import logging
import subprocess
import tokenize
from pathlib import Path
from typing import Dict, List, Optional, Tuple

logger = logging.getLogger(__name__)


class CommentExtractor:
    """Extract and preserve comments from Python source code."""

    def __init__(self):
        """Initialize the comment extractor."""
        pass

    def _format_code_with_black(self, code: str, line_length: int = 88) -> str:
        """
        Format Python code using Black formatter.

        Args:
            code: Python code to format
            line_length: Maximum line length (default 88, use 200+ to force single-line)

        Returns:
            Formatted code, or original code if Black fails
        """
        try:
            import black

            # Format the code using Black
            mode = black.Mode(
                line_length=line_length,
                string_normalization=True,
                is_pyi=False,
            )
            formatted = black.format_str(code, mode=mode)
            logger.debug(f"Successfully formatted code with Black (line_length={line_length})")
            return formatted
        except Exception as e:
            logger.warning(f"Failed to format code with Black: {e}, using original code")
            return code

    def extract_comments_from_function(
        self, file_path: Path, function_name: str = "main", content: Optional[str] = None
    ) -> Dict[int, List[str]]:
        """
        Extract all user-added content from a specific function.

        This includes comments, inline docstrings, and any other code.
        We extract everything after the first docstring to preserve it.

        Args:
            file_path: Path to Python file
            function_name: Name of function to extract content from
            content: Optional pre-formatted content to use instead of reading file

        Returns:
            Dictionary mapping line offset (relative to function start) to list of content lines
            Example: {0: ["# Comment"], 2: ['docstring content']}
        """
        if content is None and not file_path.exists():
            logger.warning(f"File not found: {file_path}")
            return {}

        try:
            # Parse AST to find function boundaries
            if content is not None:
                lines = content.splitlines(keepends=True)
            else:
                with open(file_path, "r") as f:
                    lines = f.readlines()

            tree = ast.parse("".join(lines))
            function_start_line = self._find_function_start_line(tree, function_name)
            # Pass content if available, otherwise reads from file
            lines_str = "".join(lines) if content else None
            function_end_line = self._find_function_end_line(tree, function_name, file_path, content=lines_str)

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
        self, tree: ast.AST, function_name: str, file_path: Path, content: Optional[str] = None
    ) -> Optional[int]:
        """
        Find the ending line number of a function by analyzing indentation.

        Since Python's AST doesn't include comments, we need to find where
        the function body ACTUALLY ends by looking at indentation levels.

        Args:
            tree: Parsed AST tree
            function_name: Name of function to find
            file_path: Path to the source file for indentation analysis
            content: Optional pre-formatted content to use instead of reading file

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
        if content is not None:
            lines = content.splitlines(keepends=True)
        else:
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

        # Limit trailing blank lines to max 2 (preserve user spacing, but prevent accumulation)
        # Count trailing blanks
        trailing_blank_count = 0
        for line in reversed(all_content):
            if line.strip() == '':
                trailing_blank_count += 1
            else:
                break

        # Remove excess trailing blanks (keep max 2)
        max_trailing_blanks = 2
        if trailing_blank_count > max_trailing_blanks:
            for _ in range(trailing_blank_count - max_trailing_blanks):
                all_content.pop()

        # Also limit trailing blank lines from generated content
        generated_lines_copy = list(generated_lines)  # Don't modify original
        trailing_gen_blank_count = 0
        for line in reversed(generated_lines_copy):
            if line.strip() == '':
                trailing_gen_blank_count += 1
            else:
                break

        # Remove excess trailing blanks from generated (keep max 2)
        if trailing_gen_blank_count > max_trailing_blanks:
            for _ in range(trailing_gen_blank_count - max_trailing_blanks):
                generated_lines_copy.pop()

        # Insert all content at the beginning
        result_lines = all_content

        # Add the rest of the generated lines (without trailing blanks)
        result_lines.extend(generated_lines_copy)

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

    def extract_after_function_content(self, file_path: Path, function_name: str = "main") -> List[str]:
        """
        Extract content that appears AFTER the function ends but BEFORE if __name__.

        This captures user-added content between the function definition and the
        boilerplate code at the end of the file.

        Args:
            file_path: Path to Python file
            function_name: Name of function to find

        Returns:
            List of lines that appear after the function
        """
        if not file_path.exists():
            return []

        try:
            with open(file_path, "r") as f:
                lines = f.readlines()

            tree = ast.parse("".join(lines))
            function_end_line = self._find_function_end_line(tree, function_name, file_path)

            if function_end_line is None:
                return []

            # Find where "if __name__" starts
            if_name_line = None
            for i, line in enumerate(lines):
                if line.strip().startswith("if __name__"):
                    if_name_line = i + 1  # Convert to 1-indexed
                    break

            if if_name_line is None:
                # No if __name__ block, extract everything after function
                if_name_line = len(lines) + 1

            # Extract lines between function end and if __name__
            after_function_content = []
            for line_num in range(function_end_line + 1, if_name_line):
                line_idx = line_num - 1  # Convert to 0-indexed
                if line_idx < len(lines):
                    line = lines[line_idx].rstrip()
                    after_function_content.append(line)

            # Strip leading and trailing blank lines
            while after_function_content and after_function_content[0].strip() == '':
                after_function_content.pop(0)
            while after_function_content and after_function_content[-1].strip() == '':
                after_function_content.pop()

            return after_function_content

        except Exception as e:
            logger.error(f"Failed to extract after-function content: {e}")
            return []

    def find_circuit_function_name(self, file_path: Path) -> Optional[str]:
        """
        Find the name of the @circuit decorated function in a file.

        Args:
            file_path: Path to Python file

        Returns:
            Name of the circuit function, or None if not found
        """
        if not file_path.exists():
            return None

        try:
            with open(file_path, "r") as f:
                content = f.read()

            tree = ast.parse(content)

            # Look for function with @circuit decorator
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    # Check if it has @circuit decorator
                    for decorator in node.decorator_list:
                        # Handle both @circuit and @circuit(...)
                        if isinstance(decorator, ast.Name) and decorator.id == "circuit":
                            return node.name
                        elif isinstance(decorator, ast.Call):
                            if isinstance(decorator.func, ast.Name) and decorator.func.id == "circuit":
                                return node.name

            # Fallback: if no @circuit found, look for any function
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    return node.name

            return None

        except Exception as e:
            logger.warning(f"Failed to find circuit function name: {e}")
            return None

    def merge_preserving_user_content(
        self,
        existing_file: Path,
        generated_template: str,
        function_name: Optional[str] = None,
    ) -> str:
        """
        Merge generated code with existing file, preserving ALL user content.

        Strategy: Read existing file, extract generated component code from template,
        replace ONLY that section, keep everything else untouched.

        Args:
            existing_file: Path to existing Python file with user content
            generated_template: Newly generated template (full file)
            function_name: Name of function to update (if None, auto-detect)

        Returns:
            Merged code with user content preserved and generated code updated
        """
        if not existing_file.exists():
            # No existing file, return generated template formatted
            return self._format_code_with_black(generated_template)

        # Auto-detect function name if not provided
        if function_name is None:
            function_name = self.find_circuit_function_name(existing_file)
            if function_name is None:
                logger.warning("Could not find circuit function, using 'main' as fallback")
                function_name = "main"
            else:
                logger.info(f"Auto-detected circuit function: {function_name}")

        try:
            # Read existing file and normalize formatting with Black
            with open(existing_file, "r") as f:
                existing_content_raw = f.read()

            # Format existing file with Black using VERY LONG line length (200)
            # This forces multi-line Component() calls to be single-line,
            # making them easier to detect and remove during merge
            existing_content = self._format_code_with_black(existing_content_raw, line_length=200)
            existing_lines = existing_content.split("\n")
            # Add back newlines for compatibility
            existing_lines = [line + "\n" if i < len(existing_lines) - 1 else line
                            for i, line in enumerate(existing_lines)]

            # Parse both existing and generated code
            generated_lines = generated_template.split("\n")

            # Find function boundaries in EXISTING file
            existing_tree = ast.parse(existing_content)
            existing_func_start = self._find_function_start_line(existing_tree, function_name)
            # IMPORTANT: Pass formatted content so indentation analysis uses formatted version
            existing_func_end = self._find_function_end_line(existing_tree, function_name, existing_file, content=existing_content)

            if existing_func_start is None:
                # Function doesn't exist in old file, return template
                return generated_template

            # Find function body content in GENERATED template (the new component code)
            # Try the detected function name first, then try "main" as fallback
            generated_func_start_idx = self._find_function_start_index(generated_lines, function_name)
            if generated_func_start_idx is None and function_name != "main":
                # Function not found, try "main" (the template default)
                logger.info(f"Function '{function_name}' not in generated code, trying 'main' fallback")
                generated_func_start_idx = self._find_function_start_index(generated_lines, "main")

            if generated_func_start_idx is None:
                # Can't find any function in generated code, return existing
                logger.warning(f"Could not find function in generated code (searched for '{function_name}')")
                return existing_content

            # Extract the NEW generated component code (everything after docstring in generated file)
            generated_func_body = []
            for i in range(generated_func_start_idx, len(generated_lines)):
                line = generated_lines[i]
                # Stop at "# Generate the circuit" or end of function indicators
                if line.strip().startswith("# Generate the circuit") or \
                   line.strip().startswith("if __name__"):
                    break
                generated_func_body.append(line)

            # Strip trailing blank lines from generated body
            while generated_func_body and generated_func_body[-1].strip() == '':
                generated_func_body.pop()

            # Now build the result: existing file with function body replaced
            result_lines = []

            # Part 1: Everything BEFORE the function body (header, imports, decorator, def line, docstring)
            for i in range(existing_func_start):
                # Preserve line as-is but remove trailing newline
                line = existing_lines[i]
                if line.endswith('\n'):
                    line = line[:-1]
                result_lines.append(line.rstrip())

            # Part 2: User content from INSIDE old function + NEW generated code
            # Extract user comments from inside the existing function
            # IMPORTANT: Pass the formatted content so we process the single-line version
            user_comments_map = self.extract_comments_from_function(
                existing_file, function_name, content=existing_content
            )

            # Filter out generated patterns and standalone 'pass' statements
            # These should not be preserved as "user content"
            if user_comments_map and generated_func_body:
                # Check if any generated line has actual component code (not just whitespace/comments)
                has_real_code = any(
                    line.strip() and
                    not line.strip().startswith('#') and
                    not line.strip().startswith('"""') and
                    not line.strip().startswith("'''")
                    for line in generated_func_body
                )

                if has_real_code:
                    # Known generated comment patterns that should not be preserved
                    generated_patterns = [
                        'pass',  # Standalone pass statement
                        '# Create components',  # Generated section marker
                        '# Create nets',  # Generated section marker
                        '# Create subcircuits',  # Generated section marker
                    ]

                    # Remove generated patterns and component code lines
                    # Parse the content to identify component assignments using AST
                    component_line_ranges = set()
                    try:
                        # Parse the formatted existing content to find Component/Net assignments
                        tree = ast.parse(existing_content)
                        for node in ast.walk(tree):
                            if isinstance(node, ast.Assign):
                                # Check if RHS is a Call to Component or Net
                                if isinstance(node.value, ast.Call):
                                    if isinstance(node.value.func, ast.Name):
                                        if node.value.func.id in ('Component', 'Net'):
                                            # Add all lines from this assignment to the exclusion set
                                            # Convert to 0-indexed and account for function start
                                            start_line = node.lineno - 1  # AST is 1-indexed
                                            end_line = node.end_lineno - 1 if node.end_lineno else start_line
                                            for line_num in range(start_line, end_line + 1):
                                                component_line_ranges.add(line_num)
                    except Exception as e:
                        logger.warning(f"Failed to parse AST for component detection: {e}")

                    filtered_comments = {}
                    for offset, lines in user_comments_map.items():
                        filtered_lines = []
                        for i, line in enumerate(lines):
                            stripped = line.strip()
                            # Skip if it's a generated pattern
                            if stripped in generated_patterns:
                                continue

                            # Calculate absolute line number in the file
                            # offset is relative to function start, so add existing_func_start
                            abs_line_num = existing_func_start + offset + i

                            # Skip if this line is part of a Component/Net assignment
                            if abs_line_num in component_line_ranges:
                                continue

                            filtered_lines.append(line)

                        if filtered_lines:  # Only keep if there's content after filtering
                            filtered_comments[offset] = filtered_lines

                    # Now remove leading blank-only entries, but keep blank lines between content
                    if filtered_comments:
                        # Find first and last non-blank entries
                        sorted_offsets = sorted(filtered_comments.keys())
                        first_non_blank = None
                        last_non_blank = None

                        for offset in sorted_offsets:
                            has_content = any(line.strip() for line in filtered_comments[offset])
                            if has_content:
                                if first_non_blank is None:
                                    first_non_blank = offset
                                last_non_blank = offset

                        # Keep only entries between first and last non-blank (inclusive)
                        if first_non_blank is not None:
                            user_comments_map = {
                                offset: lines
                                for offset, lines in filtered_comments.items()
                                if first_non_blank <= offset <= last_non_blank
                            }
                        else:
                            # All blank lines - discard
                            user_comments_map = {}
                    else:
                        user_comments_map = {}

            # Merge: user comments first, then generated code
            if user_comments_map:
                # Reinsert user comments with generated code
                merged_body = self.reinsert_comments(generated_func_body, user_comments_map)
                result_lines.extend(merged_body)
            else:
                # No user comments, just use generated code
                result_lines.extend(generated_func_body)


            # Part 3: Everything AFTER the function body (preserve user content after function)
            # existing_func_end is 1-indexed, so existing_lines[existing_func_end] is the line AFTER function end
            if existing_func_end is not None and existing_func_end < len(existing_lines):
                after_lines_count = len(existing_lines) - existing_func_end
                for i in range(existing_func_end, len(existing_lines)):
                    # Preserve line as-is but remove trailing newline
                    line = existing_lines[i]
                    if line.endswith('\n'):
                        line = line[:-1]
                    result_lines.append(line.rstrip())

            # Format the final result with Black before returning
            merged_code = "\n".join(result_lines)
            return self._format_code_with_black(merged_code)

        except Exception as e:
            logger.error(f"Failed to merge preserving user content: {e}")
            # On error, return generated template (safe fallback)
            return generated_template

    def extract_and_reinsert(
        self,
        existing_file: Path,
        generated_code: str,
        function_name: str = "main",
    ) -> str:
        """
        Complete workflow: extract comments from existing file and reinsert into generated code.

        DEPRECATED: Use merge_preserving_user_content() instead for comprehensive preservation.

        Args:
            existing_file: Path to existing Python file with comments
            generated_code: Newly generated code (without comments)
            function_name: Name of function to extract/reinsert comments for

        Returns:
            Generated code with comments re-inserted
        """
        # Extract comments from existing file
        comments_map = self.extract_comments_from_function(existing_file, function_name)

        # Extract content after function (between function and if __name__)
        after_function_content = self.extract_after_function_content(existing_file, function_name)

        if not comments_map and not after_function_content:
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

        # Find where to insert after-function content (before "# Generate the circuit" or "if __name__")
        result_lines = before_function + function_with_comments

        # Insert after-function content before the boilerplate
        if after_function_content:
            # Find the "# Generate the circuit" or "if __name__" line
            insert_idx = None
            for i, line in enumerate(result_lines):
                if line.strip().startswith("# Generate the circuit") or \
                   line.strip().startswith("if __name__"):
                    insert_idx = i
                    break

            if insert_idx is not None:
                # Insert after-function content before the boilerplate
                result_lines = result_lines[:insert_idx] + [''] + after_function_content + [''] + result_lines[insert_idx:]
            else:
                # No boilerplate found, append at end
                result_lines.extend([''] + after_function_content)

        # Format the final result with Black before returning
        merged_code = "\n".join(result_lines)
        return self._format_code_with_black(merged_code)

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
