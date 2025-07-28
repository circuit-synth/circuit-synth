"""
Migration Utilities for Unified Logging System
==============================================

This module provides utilities for migrating from existing logging systems
to the unified logging system. It includes:
- Backward compatibility layer for existing logging calls
- Migration helpers for converting standard logging to unified system
- Testing utilities for validation
- Automated migration tools
"""

import ast
import importlib.util
import logging
import re
from dataclasses import dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple, Union

from .context_manager import UserContext, get_context_extras
from .unified_logger import ContextLogger, context_logger


@dataclass
class MigrationResult:
    """Result of a migration operation."""

    file_path: str
    changes_made: List[str]
    warnings: List[str]
    errors: List[str]
    success: bool


class BackwardCompatibilityLogger:
    """
    Backward compatibility layer for existing logging calls.

    This class provides a drop-in replacement for standard Python loggers
    that forwards calls to the unified logging system while maintaining
    the same API.
    """

    def __init__(
        self,
        name: str = "compat",
        context_logger_instance: Optional[ContextLogger] = None,
    ):
        self.name = name
        self.context_logger = context_logger_instance or context_logger
        self._level = logging.INFO
        self._handlers = []
        self._filters = []
        self._disabled = False

    def debug(self, msg, *args, **kwargs):
        """Log debug message with backward compatibility."""
        self._log_with_compat("DEBUG", msg, *args, **kwargs)

    def info(self, msg, *args, **kwargs):
        """Log info message with backward compatibility."""
        self._log_with_compat("INFO", msg, *args, **kwargs)

    def warning(self, msg, *args, **kwargs):
        """Log warning message with backward compatibility."""
        self._log_with_compat("WARNING", msg, *args, **kwargs)

    def warn(self, msg, *args, **kwargs):
        """Alias for warning (deprecated but supported)."""
        self.warning(msg, *args, **kwargs)

    def error(self, msg, *args, **kwargs):
        """Log error message with backward compatibility."""
        self._log_with_compat("ERROR", msg, *args, **kwargs)

    def exception(self, msg, *args, exc_info=True, **kwargs):
        """Log exception with traceback."""
        # Add exception info to kwargs
        kwargs["exc_info"] = exc_info
        self._log_with_compat("ERROR", msg, *args, **kwargs)

    def critical(self, msg, *args, **kwargs):
        """Log critical message with backward compatibility."""
        self._log_with_compat("ERROR", msg, *args, **kwargs)

    def fatal(self, msg, *args, **kwargs):
        """Alias for critical."""
        self.critical(msg, *args, **kwargs)

    def log(self, level, msg, *args, **kwargs):
        """Log with specified level."""
        level_name = self._level_to_name(level)
        self._log_with_compat(level_name, msg, *args, **kwargs)

    def _log_with_compat(self, level: str, msg, *args, **kwargs):
        """Internal method to handle logging with compatibility."""
        if self._disabled:
            return

        # Format message if args provided (standard logging behavior)
        if args:
            try:
                formatted_msg = msg % args
            except (TypeError, ValueError):
                formatted_msg = str(msg)
        else:
            formatted_msg = str(msg)

        # Extract standard logging kwargs
        extra = kwargs.pop("extra", {})
        exc_info = kwargs.pop("exc_info", False)
        stack_info = kwargs.pop("stack_info", False)

        # Build context for unified logger
        context = {
            "component": extra.get("component", "COMPAT"),
            "logger_name": self.name,
            "backward_compat": True,
            **extra,
            **kwargs,
        }

        # Add exception info if provided
        if exc_info:
            import traceback

            context["exception_info"] = traceback.format_exc()

        # Forward to unified logger
        log_method = getattr(
            self.context_logger, level.lower(), self.context_logger.info
        )
        log_method(formatted_msg, **context)

    def _level_to_name(self, level: Union[int, str]) -> str:
        """Convert logging level to name."""
        if isinstance(level, str):
            return level.upper()

        level_map = {
            logging.DEBUG: "DEBUG",
            logging.INFO: "INFO",
            logging.WARNING: "WARNING",
            logging.ERROR: "ERROR",
            logging.CRITICAL: "ERROR",
        }
        return level_map.get(level, "INFO")

    # Standard logger interface methods
    def setLevel(self, level):
        """Set logging level (compatibility)."""
        self._level = level

    def getEffectiveLevel(self):
        """Get effective logging level."""
        return self._level

    def isEnabledFor(self, level):
        """Check if logging is enabled for level."""
        return not self._disabled and level >= self._level

    def addHandler(self, handler):
        """Add handler (compatibility - no-op)."""
        self._handlers.append(handler)

    def removeHandler(self, handler):
        """Remove handler (compatibility - no-op)."""
        if handler in self._handlers:
            self._handlers.remove(handler)

    def addFilter(self, filter_func):
        """Add filter (compatibility - no-op)."""
        self._filters.append(filter_func)

    def removeFilter(self, filter_func):
        """Remove filter (compatibility - no-op)."""
        if filter_func in self._filters:
            self._filters.remove(filter_func)

    def disabled(self, disabled: bool = True):
        """Disable/enable logger."""
        self._disabled = disabled


class LoggingMigrationTool:
    """
    Automated tool for migrating logging statements to unified system.

    This tool can analyze Python files and automatically convert standard
    logging calls to use the unified logging system.
    """

    def __init__(self):
        self.conversion_patterns = [
            # Standard logging to unified logger
            (
                r"import logging\s*\n",
                "from circuit_synth.core.logging.unified import context_logger\n",
            ),
            (r"logger = logging\.getLogger\([^)]*\)", "logger = context_logger"),
            (r"logging\.getLogger\([^)]*\)", "context_logger"),
            # Direct logging calls
            (r"logging\.info\((.*?)\)", r'context_logger.info(\1, component="INFO")'),
            (
                r"logging\.debug\((.*?)\)",
                r'context_logger.debug(\1, component="DEBUG")',
            ),
            (
                r"logging\.warning\((.*?)\)",
                r'context_logger.warning(\1, component="WARNING")',
            ),
            (
                r"logging\.error\((.*?)\)",
                r'context_logger.error(\1, component="ERROR")',
            ),
            (
                r"logging\.critical\((.*?)\)",
                r'context_logger.error(\1, component="CRITICAL")',
            ),
            # Logger instance calls
            (r"logger\.info\((.*?)\)", r'context_logger.info(\1, component="INFO")'),
            (r"logger\.debug\((.*?)\)", r'context_logger.debug(\1, component="DEBUG")'),
            (
                r"logger\.warning\((.*?)\)",
                r'context_logger.warning(\1, component="WARNING")',
            ),
            (r"logger\.error\((.*?)\)", r'context_logger.error(\1, component="ERROR")'),
            (
                r"logger\.critical\((.*?)\)",
                r'context_logger.error(\1, component="CRITICAL")',
            ),
            (
                r"logger\.exception\((.*?)\)",
                r'context_logger.error(\1, component="EXCEPTION", exc_info=True)',
            ),
            # Print statements to logging
            (
                r'print\(f?"([^"]*)".*?\)',
                r'context_logger.info("\1", component="PRINT")',
            ),
            (
                r"print\(f?'([^']*)'.*?\)",
                r'context_logger.info("\1", component="PRINT")',
            ),
        ]

        self.import_patterns = [
            "from circuit_synth.core.logging.unified import context_logger",
            "from circuit_synth.core.logging.context_manager import UserContext",
        ]

    def migrate_file(self, file_path: Path) -> MigrationResult:
        """
        Migrate a single Python file to use unified logging.

        Args:
            file_path: Path to the Python file to migrate

        Returns:
            MigrationResult with details of the migration
        """
        if not file_path.suffix == ".py":
            return MigrationResult(
                file_path=str(file_path),
                changes_made=[],
                warnings=[f"Skipping non-Python file: {file_path}"],
                errors=[],
                success=False,
            )

        try:
            with open(file_path, "r", encoding="utf-8") as f:
                original_content = f.read()
        except Exception as e:
            return MigrationResult(
                file_path=str(file_path),
                changes_made=[],
                warnings=[],
                errors=[f"Failed to read file: {e}"],
                success=False,
            )

        content = original_content
        changes = []
        warnings = []
        errors = []

        try:
            # Apply conversion patterns
            for pattern, replacement in self.conversion_patterns:
                matches = re.findall(pattern, content)
                if matches:
                    content = re.sub(pattern, replacement, content)
                    changes.extend(
                        [f"Converted {pattern} -> {replacement}" for _ in matches]
                    )

            # Add imports if logging calls were converted
            needs_import = any("context_logger" in change for change in changes)
            if (
                needs_import
                and "from circuit_synth.core.logging.unified import context_logger"
                not in content
            ):
                # Find the best place to add import
                import_line = (
                    "from circuit_synth.core.logging.unified import context_logger\n"
                )

                # Try to add after existing imports
                lines = content.split("\n")
                import_index = 0
                for i, line in enumerate(lines):
                    if line.strip().startswith("import ") or line.strip().startswith(
                        "from "
                    ):
                        import_index = i + 1

                lines.insert(import_index, import_line.strip())
                content = "\n".join(lines)
                changes.append("Added unified logger import")

            # Validate syntax
            try:
                ast.parse(content)
            except SyntaxError as e:
                errors.append(f"Syntax error after migration: {e}")
                content = original_content  # Revert changes
                changes = []

            # Write back if changes were made and no errors
            if content != original_content and not errors:
                with open(file_path, "w", encoding="utf-8") as f:
                    f.write(content)

            return MigrationResult(
                file_path=str(file_path),
                changes_made=changes,
                warnings=warnings,
                errors=errors,
                success=len(changes) > 0 and len(errors) == 0,
            )

        except Exception as e:
            return MigrationResult(
                file_path=str(file_path),
                changes_made=[],
                warnings=[],
                errors=[f"Migration failed: {e}"],
                success=False,
            )

    def migrate_directory(
        self, directory: Path, recursive: bool = True
    ) -> Dict[str, MigrationResult]:
        """
        Migrate all Python files in a directory.

        Args:
            directory: Directory to migrate
            recursive: Whether to migrate subdirectories

        Returns:
            Dictionary mapping file paths to migration results
        """
        results = {}

        if recursive:
            pattern = "**/*.py"
        else:
            pattern = "*.py"

        for py_file in directory.glob(pattern):
            if py_file.is_file():
                result = self.migrate_file(py_file)
                results[str(py_file)] = result

        return results

    def generate_migration_report(self, results: Dict[str, MigrationResult]) -> str:
        """Generate a human-readable migration report."""
        total_files = len(results)
        successful_migrations = sum(1 for r in results.values() if r.success)
        total_changes = sum(len(r.changes_made) for r in results.values())
        total_warnings = sum(len(r.warnings) for r in results.values())
        total_errors = sum(len(r.errors) for r in results.values())

        report = f"""
Unified Logging Migration Report
===============================

Summary:
- Total files processed: {total_files}
- Successful migrations: {successful_migrations}
- Total changes made: {total_changes}
- Total warnings: {total_warnings}
- Total errors: {total_errors}

Detailed Results:
"""

        for file_path, result in results.items():
            report += f"\n{file_path}:\n"
            if result.success:
                report += (
                    f"  ✓ Successfully migrated ({len(result.changes_made)} changes)\n"
                )
                for change in result.changes_made:
                    report += f"    - {change}\n"
            else:
                report += f"  ✗ Migration failed\n"

            for warning in result.warnings:
                report += f"  ⚠ Warning: {warning}\n"

            for error in result.errors:
                report += f"  ✗ Error: {error}\n"

        return report


def create_compatibility_logger(name: str = "compat") -> BackwardCompatibilityLogger:
    """
    Create a backward compatibility logger.

    This function creates a logger that provides the same interface as
    standard Python logging but forwards to the unified system.

    Args:
        name: Name for the compatibility logger

    Returns:
        BackwardCompatibilityLogger instance
    """
    return BackwardCompatibilityLogger(name)


def patch_logging_module():
    """
    Monkey-patch the standard logging module to use unified logging.

    This function replaces key functions in the logging module to
    redirect to the unified logging system. Use with caution as it
    affects global state.
    """
    import logging

    # Store original functions
    original_getLogger = logging.getLogger
    original_basicConfig = logging.basicConfig

    # Create a registry of compatibility loggers
    _compat_loggers = {}

    def unified_getLogger(name=None):
        """Replacement for logging.getLogger that returns compatibility logger."""
        if name is None:
            name = "root"

        if name not in _compat_loggers:
            _compat_loggers[name] = BackwardCompatibilityLogger(name)

        return _compat_loggers[name]

    def unified_basicConfig(**kwargs):
        """Replacement for logging.basicConfig (no-op for compatibility)."""
        # Log that basicConfig was called but ignored
        context_logger.debug(
            "logging.basicConfig called but ignored (using unified logging)",
            component="COMPAT",
            config_kwargs=kwargs,
        )

    # Apply patches
    logging.getLogger = unified_getLogger
    logging.basicConfig = unified_basicConfig

    # Patch module-level logging functions
    logging.debug = lambda msg, *args, **kwargs: context_logger.debug(
        str(msg), component="LOGGING", **kwargs
    )
    logging.info = lambda msg, *args, **kwargs: context_logger.info(
        str(msg), component="LOGGING", **kwargs
    )
    logging.warning = lambda msg, *args, **kwargs: context_logger.warning(
        str(msg), component="LOGGING", **kwargs
    )
    logging.error = lambda msg, *args, **kwargs: context_logger.error(
        str(msg), component="LOGGING", **kwargs
    )
    logging.critical = lambda msg, *args, **kwargs: context_logger.error(
        str(msg), component="CRITICAL", **kwargs
    )
    logging.exception = lambda msg, *args, **kwargs: context_logger.error(
        str(msg), component="EXCEPTION", exc_info=True, **kwargs
    )

    context_logger.info(
        "Standard logging module patched for unified logging", component="COMPAT"
    )


def validate_migration(file_path: Path) -> List[str]:
    """
    Validate that a migrated file works correctly.

    Args:
        file_path: Path to the migrated Python file

    Returns:
        List of validation issues (empty if valid)
    """
    issues = []

    try:
        # Check syntax
        with open(file_path, "r", encoding="utf-8") as f:
            content = f.read()

        try:
            ast.parse(content)
        except SyntaxError as e:
            issues.append(f"Syntax error: {e}")
            return issues

        # Check for required imports
        if (
            "context_logger" in content
            and "from circuit_synth.core.logging.unified import context_logger"
            not in content
        ):
            issues.append("Missing unified logger import")

        # Check for remaining standard logging calls
        problematic_patterns = [
            r"logging\.getLogger",
            r"logging\.basicConfig",
            r"import logging(?!\s*#)",  # Allow commented imports
        ]

        for pattern in problematic_patterns:
            if re.search(pattern, content):
                issues.append(f"Found unconverted logging pattern: {pattern}")

        # Try to import the module (if it's importable)
        try:
            spec = importlib.util.spec_from_file_location("test_module", file_path)
            if spec and spec.loader:
                module = importlib.util.module_from_spec(spec)
                # Don't actually execute, just check if it can be loaded
        except Exception as e:
            issues.append(f"Module import test failed: {e}")

    except Exception as e:
        issues.append(f"Validation failed: {e}")

    return issues


# Convenience function for quick migration
def quick_migrate(path: Union[str, Path], recursive: bool = True) -> str:
    """
    Quickly migrate a file or directory and return a report.

    Args:
        path: File or directory path to migrate
        recursive: Whether to migrate subdirectories (if path is a directory)

    Returns:
        Migration report as string
    """
    path = Path(path)
    migrator = LoggingMigrationTool()

    if path.is_file():
        result = migrator.migrate_file(path)
        results = {str(path): result}
    elif path.is_dir():
        results = migrator.migrate_directory(path, recursive)
    else:
        return f"Error: Path {path} does not exist"

    return migrator.generate_migration_report(results)
