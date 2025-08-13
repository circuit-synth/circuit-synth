"""
KiCad File I/O Layer - Pure file operations.

This module provides clean file read/write operations for KiCad files without any
knowledge of the file format. It handles encoding, paths, backups, and error handling.
"""

import logging
import shutil
from pathlib import Path
from typing import Optional, Union

logger = logging.getLogger(__name__)


class KiCadFileIO:
    """
    Pure file I/O operations for KiCad files.

    This class handles file system operations without any knowledge of KiCad format.
    It provides clean separation between file handling and content manipulation.
    """

    def __init__(self, encoding: str = "utf-8", create_backups: bool = True):
        """
        Initialize file I/O handler.

        Args:
            encoding: Text encoding for file operations (default: utf-8)
            create_backups: Whether to create .bak files when overwriting
        """
        self.encoding = encoding
        self.create_backups = create_backups

    def read(self, file_path: Union[str, Path]) -> str:
        """
        Read file contents as string.

        Args:
            file_path: Path to file to read

        Returns:
            File contents as string

        Raises:
            FileNotFoundError: If file doesn't exist
            IOError: If file can't be read
        """
        file_path = Path(file_path)

        if not file_path.exists():
            raise FileNotFoundError(f"File not found: {file_path}")

        try:
            with open(file_path, "r", encoding=self.encoding) as f:
                content = f.read()

            logger.debug(f"Read {len(content)} characters from {file_path}")
            return content

        except Exception as e:
            logger.error(f"Failed to read file {file_path}: {e}")
            raise IOError(f"Cannot read file {file_path}: {e}") from e

    def write(
        self, content: str, file_path: Union[str, Path], atomic: bool = True
    ) -> None:
        """
        Write string content to file.

        Args:
            content: String content to write
            file_path: Path to write to
            atomic: If True, write to temp file first then rename (safer)

        Raises:
            IOError: If file can't be written
        """
        file_path = Path(file_path)

        # Create parent directories if they don't exist
        file_path.parent.mkdir(parents=True, exist_ok=True)

        # Create backup if file exists and backups enabled
        if self.create_backups and file_path.exists():
            self._create_backup(file_path)

        try:
            if atomic:
                # Atomic write: write to temp file first, then rename
                temp_path = file_path.with_suffix(file_path.suffix + ".tmp")
                with open(temp_path, "w", encoding=self.encoding) as f:
                    f.write(content)

                # Atomic rename
                temp_path.replace(file_path)
                logger.debug(
                    f"Atomically wrote {len(content)} characters to {file_path}"
                )
            else:
                # Direct write
                with open(file_path, "w", encoding=self.encoding) as f:
                    f.write(content)
                logger.debug(f"Wrote {len(content)} characters to {file_path}")

        except Exception as e:
            logger.error(f"Failed to write file {file_path}: {e}")
            raise IOError(f"Cannot write file {file_path}: {e}") from e

    def exists(self, file_path: Union[str, Path]) -> bool:
        """
        Check if file exists.

        Args:
            file_path: Path to check

        Returns:
            True if file exists, False otherwise
        """
        return Path(file_path).exists()

    def backup(
        self, file_path: Union[str, Path], backup_suffix: str = ".bak"
    ) -> Optional[Path]:
        """
        Create backup copy of file.

        Args:
            file_path: Path to file to backup
            backup_suffix: Suffix for backup file

        Returns:
            Path to backup file if successful, None if file doesn't exist

        Raises:
            IOError: If backup can't be created
        """
        file_path = Path(file_path)

        if not file_path.exists():
            return None

        backup_path = file_path.with_suffix(file_path.suffix + backup_suffix)

        try:
            shutil.copy2(file_path, backup_path)
            logger.debug(f"Created backup: {backup_path}")
            return backup_path

        except Exception as e:
            logger.error(f"Failed to create backup of {file_path}: {e}")
            raise IOError(f"Cannot create backup: {e}") from e

    def _create_backup(self, file_path: Path) -> None:
        """Internal method to create backup during write operations."""
        try:
            backup_path = self.backup(file_path)
            if backup_path:
                logger.debug(f"Auto-backup created: {backup_path}")
        except Exception as e:
            # Log but don't fail the write operation
            logger.warning(f"Backup creation failed (continuing with write): {e}")
