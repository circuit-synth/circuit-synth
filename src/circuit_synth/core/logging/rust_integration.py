"""
Rust Logging Integration for Unified Logging System
==================================================

This module provides integration between Rust components and the Python
unified logging system. It sets up log forwarding from Rust (via pyo3-log)
to the unified logging system with proper context and formatting.
"""

import logging
import threading
from datetime import datetime
from typing import Any, Dict, Optional

from .context_manager import get_context_extras
from .unified_logger import context_logger


class RustLogHandler(logging.Handler):
    """
    Custom logging handler that forwards Rust logs to the unified logging system.

    This handler receives log messages from Rust components (via pyo3-log) and
    forwards them to the unified logging system with proper context and formatting.
    """

    def __init__(self, context_logger_instance=None):
        super().__init__()
        self.context_logger = context_logger_instance or context_logger
        self._lock = threading.Lock()
        self._message_count = 0
        self._error_count = 0

    def emit(self, record: logging.LogRecord):
        """
        Process a log record from Rust and forward to unified logging.

        Args:
            record: The log record from Rust components
        """
        try:
            with self._lock:
                self._message_count += 1

                # Map Python logging levels to our unified system
                level_map = {
                    logging.DEBUG: self.context_logger.debug,
                    logging.INFO: self.context_logger.info,
                    logging.WARNING: self.context_logger.warning,
                    logging.ERROR: self.context_logger.error,
                    logging.CRITICAL: self.context_logger.error,
                }

                log_func = level_map.get(record.levelno, self.context_logger.info)

                # Extract Rust-specific context
                rust_context = {
                    "component": "RUST",
                    "rust_module": record.name,
                    "rust_line": record.lineno,
                    "rust_function": getattr(record, "funcName", "unknown"),
                    "rust_thread": getattr(record, "thread", "unknown"),
                    "rust_process": getattr(record, "process", "unknown"),
                }

                # Parse structured log messages from Rust
                message = record.getMessage()
                parsed_context = self._parse_rust_message(message)
                rust_context.update(parsed_context)

                # Forward to unified logging system
                log_func(parsed_context.get("clean_message", message), **rust_context)

        except Exception as e:
            self._error_count += 1
            # Fallback to stderr to avoid infinite recursion
            import sys

            sys.stderr.write(f"RustLogHandler error: {e}\n")

    def _parse_rust_message(self, message: str) -> Dict[str, Any]:
        """
        Parse structured log messages from Rust components.

        Rust components may send structured messages with prefixes like:
        - PERF_TIMING: operation=... duration_ms=...
        - ERROR_CONTEXT: operation=... error_type=...
        - MEMORY_USAGE: operation=... bytes=...
        - etc.

        Args:
            message: The raw log message from Rust

        Returns:
            Dictionary with parsed context and clean message
        """
        context = {"clean_message": message}

        # Parse performance timing messages
        if message.startswith("PERF_TIMING:"):
            context.update(self._parse_perf_timing(message))

        # Parse error context messages
        elif message.startswith("ERROR_CONTEXT:"):
            context.update(self._parse_error_context(message))

        # Parse memory usage messages
        elif message.startswith("MEMORY_USAGE:"):
            context.update(self._parse_memory_usage(message))

        # Parse cache statistics
        elif message.startswith("CACHE_STATS:"):
            context.update(self._parse_cache_stats(message))

        # Parse file operations
        elif message.startswith("FILE_OP:"):
            context.update(self._parse_file_operation(message))

        # Parse search results
        elif message.startswith("SEARCH_RESULTS:"):
            context.update(self._parse_search_results(message))

        # Parse component lifecycle
        elif message.startswith("COMPONENT_INIT:") or message.startswith(
            "COMPONENT_SHUTDOWN:"
        ):
            context.update(self._parse_component_lifecycle(message))

        return context

    def _parse_perf_timing(self, message: str) -> Dict[str, Any]:
        """Parse performance timing messages from Rust."""
        context = {"log_type": "performance", "rust_perf_timing": True}

        try:
            # Extract key-value pairs from message
            parts = message.split(" ")
            for part in parts[1:]:  # Skip the prefix
                if "=" in part:
                    key, value = part.split("=", 1)
                    if key == "operation":
                        context["operation"] = value
                        context["clean_message"] = f"Rust operation '{value}' timing"
                    elif key == "duration_ms":
                        context["duration_ms"] = float(value)
                    elif key == "metadata":
                        context["rust_metadata"] = value
        except Exception:
            pass  # If parsing fails, just use original message

        return context

    def _parse_error_context(self, message: str) -> Dict[str, Any]:
        """Parse error context messages from Rust."""
        context = {"log_type": "error", "rust_error": True}

        try:
            parts = message.split(" ")
            for part in parts[1:]:
                if "=" in part:
                    key, value = part.split("=", 1)
                    if key == "operation":
                        context["operation"] = value
                    elif key == "error_type":
                        context["error_type"] = value
                    elif key == "error_msg":
                        context["error_message"] = value
                        context["clean_message"] = (
                            f"Rust error in {context.get('operation', 'unknown')}: {value}"
                        )
                    elif key == "context":
                        context["rust_context"] = value
        except Exception:
            pass

        return context

    def _parse_memory_usage(self, message: str) -> Dict[str, Any]:
        """Parse memory usage messages from Rust."""
        context = {"log_type": "performance", "rust_memory": True}

        try:
            parts = message.split(" ")
            for part in parts[1:]:
                if "=" in part:
                    key, value = part.split("=", 1)
                    if key == "operation":
                        context["operation"] = value
                    elif key == "bytes":
                        context["memory_bytes"] = int(value)
                    elif key == "mb":
                        context["memory_mb"] = float(value)
                        context["clean_message"] = (
                            f"Rust memory usage for {context.get('operation', 'unknown')}: {value}MB"
                        )
        except Exception:
            pass

        return context

    def _parse_cache_stats(self, message: str) -> Dict[str, Any]:
        """Parse cache statistics from Rust."""
        context = {"log_type": "performance", "rust_cache_stats": True}

        try:
            parts = message.split(" ")
            for part in parts[1:]:
                if "=" in part:
                    key, value = part.split("=", 1)
                    if key == "cache":
                        context["cache_name"] = value
                    elif key == "hits":
                        context["cache_hits"] = int(value)
                    elif key == "misses":
                        context["cache_misses"] = int(value)
                    elif key == "hit_rate":
                        context["cache_hit_rate"] = float(value)
                        context["clean_message"] = (
                            f"Rust cache '{context.get('cache_name', 'unknown')}' hit rate: {value}"
                        )
        except Exception:
            pass

        return context

    def _parse_file_operation(self, message: str) -> Dict[str, Any]:
        """Parse file operation messages from Rust."""
        context = {"log_type": "performance", "rust_file_op": True}

        try:
            parts = message.split(" ")
            for part in parts[1:]:
                if "=" in part:
                    key, value = part.split("=", 1)
                    if key == "operation":
                        context["file_operation"] = value
                    elif key == "file":
                        context["file_path"] = value
                    elif key == "bytes":
                        context["bytes_processed"] = int(value)
                    elif key == "duration_ms":
                        context["duration_ms"] = float(value)
                    elif key == "throughput_mbps":
                        context["throughput_mbps"] = float(value)
                        context["clean_message"] = (
                            f"Rust file {context.get('file_operation', 'operation')}: {value}MB/s"
                        )
        except Exception:
            pass

        return context

    def _parse_search_results(self, message: str) -> Dict[str, Any]:
        """Parse search results from Rust."""
        context = {"log_type": "performance", "rust_search": True}

        try:
            parts = message.split(" ")
            for part in parts[1:]:
                if "=" in part:
                    key, value = part.split("=", 1)
                    if key == "query":
                        context["search_query"] = value
                    elif key == "total_items":
                        context["total_items"] = int(value)
                    elif key == "results_found":
                        context["results_found"] = int(value)
                    elif key == "hit_rate":
                        context["search_hit_rate"] = float(value)
                    elif key == "duration_ms":
                        context["duration_ms"] = float(value)
                        context["clean_message"] = (
                            f"Rust search found {context.get('results_found', 0)} results in {value}ms"
                        )
        except Exception:
            pass

        return context

    def _parse_component_lifecycle(self, message: str) -> Dict[str, Any]:
        """Parse component lifecycle messages from Rust."""
        context = {"log_type": "system", "rust_lifecycle": True}

        try:
            if message.startswith("COMPONENT_INIT:"):
                context["lifecycle_event"] = "init"
            elif message.startswith("COMPONENT_SHUTDOWN:"):
                context["lifecycle_event"] = "shutdown"

            parts = message.split(" ")
            for part in parts[1:]:
                if "=" in part:
                    key, value = part.split("=", 1)
                    if key == "component":
                        context["rust_component"] = value
                    elif key == "version":
                        context["component_version"] = value
                        context["clean_message"] = (
                            f"Rust component '{context.get('rust_component', 'unknown')}' {context.get('lifecycle_event', 'event')}"
                        )
                    elif key == "uptime_ms":
                        context["uptime_ms"] = float(value)
                        context["clean_message"] = (
                            f"Rust component '{context.get('rust_component', 'unknown')}' shutdown after {value}ms"
                        )
        except Exception:
            pass

        return context

    def get_stats(self) -> Dict[str, Any]:
        """Get statistics about Rust log forwarding."""
        with self._lock:
            return {
                "total_messages": self._message_count,
                "error_count": self._error_count,
                "success_rate": (self._message_count - self._error_count)
                / max(1, self._message_count),
            }


def setup_rust_logging(context_logger_instance=None) -> RustLogHandler:
    """
    Configure Rust logging to integrate with unified system.

    This function sets up the bridge between Rust components (via pyo3-log)
    and the Python unified logging system.

    Args:
        context_logger_instance: Optional context logger instance to use

    Returns:
        The configured RustLogHandler instance
    """

    # Get the Rust logger (this is where pyo3-log forwards messages)
    rust_logger = logging.getLogger("rust_symbol_search")
    rust_logger.setLevel(logging.DEBUG)

    # Remove any existing handlers to avoid duplication
    rust_logger.handlers.clear()

    # Create and configure our custom handler
    rust_handler = RustLogHandler(context_logger_instance)
    rust_handler.setLevel(logging.DEBUG)

    # Add our handler to the Rust logger
    rust_logger.addHandler(rust_handler)
    rust_logger.propagate = False  # Don't propagate to root logger

    # Log successful setup
    logger_instance = context_logger_instance or context_logger
    logger_instance.info(
        "Rust logging integration configured successfully", component="SYSTEM"
    )

    return rust_handler


def initialize_rust_module():
    """
    Initialize the Rust module with logging support.

    This function imports the Rust module and initializes its logging
    system to forward messages to Python.
    """
    try:
        # Import the Rust module (this will trigger pyo3-log initialization)
        # import rust_symbol_search  # DISABLED: Rust integration removed for Component subscript compatibility

        # The Rust module should call pyo3_log::init() during import
        # which will set up the logging bridge

        context_logger.info(
            "Rust symbol search module imported successfully",
            component="RUST",
            module="rust_symbol_search",
        )

        return rust_symbol_search

    except ImportError as e:
        context_logger.error(
            f"Failed to import Rust module: {e}",
            component="RUST",
            error_type="ImportError",
        )
        raise
    except Exception as e:
        context_logger.error(
            f"Error initializing Rust module: {e}",
            component="RUST",
            error_type=type(e).__name__,
        )
        raise


def get_rust_log_stats() -> Dict[str, Any]:
    """
    Get statistics about Rust logging integration.

    Returns:
        Dictionary with statistics about Rust log forwarding
    """
    rust_logger = logging.getLogger("rust_symbol_search")

    stats = {
        "rust_logger_level": rust_logger.level,
        "rust_logger_handlers": len(rust_logger.handlers),
        "rust_logger_propagate": rust_logger.propagate,
    }

    # Get stats from our custom handler if it exists
    for handler in rust_logger.handlers:
        if isinstance(handler, RustLogHandler):
            stats.update(handler.get_stats())
            break

    return stats


# Initialize Rust logging when this module is imported
_rust_handler = None


def ensure_rust_logging_setup():
    """Ensure Rust logging is set up (idempotent)."""
    global _rust_handler
    if _rust_handler is None:
        _rust_handler = setup_rust_logging()
    return _rust_handler
