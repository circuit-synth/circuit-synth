"""
Source Reference Rewriter

Automatically updates component reference values in Python source files
when KiCad auto-numbers them during project generation.

This solves the back-annotation problem where Python has ref="R" but
KiCad generates R1, making round-trip synchronization difficult.
"""

import logging
import re
import tempfile
from pathlib import Path
from typing import Dict, Optional

logger = logging.getLogger(__name__)


class SourceRefRewriter:
    """Updates component reference values in Python source files.

    This class performs line-based replacement of component refs,
    preserving formatting, comments, and code structure.

    Example:
        >>> rewriter = SourceRefRewriter(
        ...     source_file=Path("main.py"),
        ...     ref_mapping={"R": "R1", "C": "C1"}
        ... )
        >>> rewriter.update()  # Updates main.py in-place
    """

    def __init__(self, source_file: Path, ref_mapping: Dict[str, str]):
        """Initialize the source rewriter.

        Args:
            source_file: Path to Python source file to update
            ref_mapping: Dict mapping old refs to new refs
                        Can be either:
                        - {"R": "R1"} for single mapping
                        - {"C": ["C1", "C2", "C3"]} for multiple components
        """
        self.source_file = Path(source_file)
        self.ref_mapping = ref_mapping

    def update(self) -> bool:
        """Update component refs in the source file.

        Uses atomic file operations (write to temp, then rename) to prevent
        corruption. Preserves file encoding, line endings, and permissions.

        Returns:
            bool: True if update succeeded, False if skipped or failed

        Raises:
            PermissionError: If file is read-only
            UnicodeDecodeError: If file encoding cannot be detected
            OSError: For other file system errors
        """
        if not self.ref_mapping:
            logger.debug("No ref mapping to apply, skipping source update")
            return False

        if not self.source_file.exists():
            logger.warning(f"Source file not found: {self.source_file}")
            return False

        try:
            # Read original file
            content, encoding, newline = self._read_file()

            # Apply ref updates
            updated_content = self._apply_ref_updates(content)

            # Check if anything changed
            if updated_content == content:
                logger.debug("No changes needed in source file")
                return False

            # Write atomically
            self._write_file_atomic(updated_content, encoding, newline)

            logger.info(f"Updated source refs in {self.source_file}: {self.ref_mapping}")
            return True

        except PermissionError:
            logger.error(f"Permission denied writing to {self.source_file}")
            raise
        except UnicodeDecodeError as e:
            logger.error(f"Encoding error reading {self.source_file}: {e}")
            raise
        except OSError as e:
            logger.error(f"File system error updating {self.source_file}: {e}")
            raise

    def _read_file(self) -> tuple[str, str, Optional[str]]:
        """Read file and detect encoding and line endings.

        Returns:
            tuple: (content, encoding, newline_type)
                   newline_type can be None (universal), '\\n', '\\r\\n', or '\\r'
        """
        # Detect encoding (try UTF-8 first, then detect)
        encoding = self._detect_encoding()

        # Read with newline=None to preserve line endings
        with open(self.source_file, 'r', encoding=encoding, newline='') as f:
            content = f.read()

        # Detect line ending type
        newline = self._detect_newline(content)

        return content, encoding, newline

    def _detect_encoding(self) -> str:
        """Detect file encoding.

        Tries UTF-8 first, then looks for encoding declaration in first two lines.
        Falls back to system default if needed.

        Returns:
            str: Encoding name (e.g., 'utf-8', 'latin-1')
        """
        # Try UTF-8 first (most common)
        try:
            with open(self.source_file, 'r', encoding='utf-8') as f:
                f.read()
            return 'utf-8'
        except UnicodeDecodeError:
            pass

        # Look for encoding declaration in first two lines
        # Format: # -*- coding: <encoding> -*-
        encoding_pattern = re.compile(
            rb'coding[=:]\s*([-\w.]+)', re.IGNORECASE
        )

        with open(self.source_file, 'rb') as f:
            for _ in range(2):
                line = f.readline()
                match = encoding_pattern.search(line)
                if match:
                    return match.group(1).decode('ascii')

        # Fall back to UTF-8 (will raise error if not compatible)
        return 'utf-8'

    def _detect_newline(self, content: str) -> Optional[str]:
        """Detect line ending type in content.

        Args:
            content: File content string

        Returns:
            str or None: '\\r\\n' (Windows), '\\n' (Unix), '\\r' (Mac), or None (mixed/unknown)
        """
        # Count different line ending types
        crlf_count = content.count('\r\n')
        lf_count = content.count('\n') - crlf_count
        cr_count = content.count('\r') - crlf_count

        # Return most common type
        if crlf_count > lf_count and crlf_count > cr_count:
            return '\r\n'
        elif lf_count > crlf_count and lf_count > cr_count:
            return '\n'
        elif cr_count > 0:
            return '\r'

        return None  # Use universal newlines

    def _apply_ref_updates(self, content: str) -> str:
        """Apply ref updates to file content.

        Uses line-based replacement with regex to handle:
        - ref="R" and ref='R' (both quote styles)
        - Multiline Component() calls
        - Comments (skips updates in comments)
        - Docstrings (skips updates in docstrings)
        - Multiple components with same prefix (ordered replacement)

        Args:
            content: Original file content

        Returns:
            str: Updated file content
        """
        lines = content.splitlines(keepends=True)
        updated_lines = []
        in_docstring = False
        docstring_delimiter = None

        # Track occurrence count for each prefix (for list-based mappings)
        occurrence_count = {prefix: 0 for prefix in self.ref_mapping.keys()}

        for line in lines:
            # Track docstring state
            if '"""' in line or "'''" in line:
                # Simple docstring detection (doesn't handle all edge cases)
                if '"""' in line:
                    delimiter = '"""'
                else:
                    delimiter = "'''"

                count = line.count(delimiter)
                if count == 1:
                    if in_docstring and delimiter == docstring_delimiter:
                        in_docstring = False
                        docstring_delimiter = None
                    else:
                        in_docstring = True
                        docstring_delimiter = delimiter
                # count == 2 means single-line docstring, no state change

            # Skip updates in docstrings
            if in_docstring:
                updated_lines.append(line)
                continue

            # Check if line is a comment
            stripped = line.lstrip()
            if stripped.startswith('#'):
                # Skip updates in comment lines
                updated_lines.append(line)
                continue

            # Apply ref updates
            updated_line = line
            for old_ref, new_refs in self.ref_mapping.items():
                # Normalize to list (handles both string and list values)
                if isinstance(new_refs, str):
                    ref_list = [new_refs]
                else:
                    ref_list = new_refs

                # Match ref="R" or ref='R'
                patterns = [
                    f'ref="{re.escape(old_ref)}"',
                    f"ref='{re.escape(old_ref)}'",
                ]

                for pattern in patterns:
                    # Find all occurrences of this pattern in the line
                    while pattern in updated_line:
                        # Find position of pattern
                        pattern_pos = updated_line.find(pattern)

                        # Check if it's in a comment
                        comment_pos = updated_line.find('#')
                        if comment_pos != -1 and pattern_pos > comment_pos:
                            # Pattern is inside a comment, skip it
                            break

                        # Get the appropriate replacement based on occurrence count
                        idx = occurrence_count[old_ref]
                        if idx < len(ref_list):
                            new_ref = ref_list[idx]
                        else:
                            # More occurrences than mappings - use last mapping
                            new_ref = ref_list[-1]
                            logger.warning(
                                f"More occurrences of ref='{old_ref}' than mappings. "
                                f"Using {new_ref} for occurrence {idx + 1}"
                            )

                        # Determine quote style
                        if pattern.startswith('ref="'):
                            replacement = f'ref="{new_ref}"'
                        else:
                            replacement = f"ref='{new_ref}'"

                        # Replace only the first occurrence (before comment)
                        updated_line = updated_line.replace(pattern, replacement, 1)

                        # Increment occurrence count
                        occurrence_count[old_ref] += 1

                        # Break to avoid infinite loop (we already replaced this one)
                        break

            updated_lines.append(updated_line)

        return ''.join(updated_lines)

    def _write_file_atomic(self, content: str, encoding: str, newline: Optional[str]):
        """Write file atomically using temp file + rename.

        This prevents corruption if the process is interrupted.

        Args:
            content: File content to write
            encoding: Encoding to use (e.g., 'utf-8')
            newline: Line ending type to preserve
        """
        # Get original file permissions
        try:
            original_mode = self.source_file.stat().st_mode
        except OSError:
            original_mode = None

        # Write to temporary file in same directory
        # (ensures atomic rename works on same filesystem)
        temp_fd, temp_path = tempfile.mkstemp(
            dir=self.source_file.parent,
            prefix=f'.{self.source_file.name}.',
            suffix='.tmp'
        )

        try:
            # Write content
            with open(temp_fd, 'w', encoding=encoding, newline=newline) as f:
                f.write(content)

            # Restore original permissions
            if original_mode:
                Path(temp_path).chmod(original_mode & 0o777)

            # Atomic rename
            Path(temp_path).replace(self.source_file)

        except Exception:
            # Clean up temp file on error
            try:
                Path(temp_path).unlink()
            except OSError:
                pass
            raise
