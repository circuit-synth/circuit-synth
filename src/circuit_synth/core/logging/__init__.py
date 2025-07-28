"""
Circuit Synth Unified Logging System
====================================

A comprehensive, thread-safe, multi-user logging system built on loguru with:
- User context tracking and session management
- Performance monitoring and metrics collection
- LLM conversation logging with cost tracking
- Rust integration via pyo3-log
- Migration utilities for existing codebases
- Production-ready configuration management

Quick Start:
-----------

Basic usage with user context:
```python
from circuit_synth.core.logging import context_logger, UserContext

with UserContext("john_doe", "session_123"):
    context_logger.info("User started circuit generation", component="CIRCUIT")
    context_logger.error("Validation failed", component="VALIDATION")
```

Performance monitoring:
```python
from circuit_synth.core.logging import performance_logger

with performance_logger.timer("kicad_generation", component="KICAD"):
    generate_kicad_files()
```

LLM conversation logging:
```python
from circuit_synth.core.logging import llm_logger

chat_id = llm_logger.start_conversation("chat_abc123")
request_id = llm_logger.log_request(
    chat_id=chat_id,
    model="gpt-4",
    provider="openai",
    prompt="Design a voltage regulator",
    prompt_tokens=25,
    estimated_cost=0.0015
)
```

Migration from existing logging:
```python
from circuit_synth.core.logging import create_compatibility_logger

# Drop-in replacement for standard logging
logger = create_compatibility_logger("my_module")
logger.info("This works just like standard logging")
```

Initialization:
```python
from circuit_synth.core.logging import initialize_logging

# Initialize the unified logging system
initialize_logging("path/to/logging_config.yaml")
```
"""

# Legacy logging components for backward compatibility
from .circuit_synth_logger import CircuitSynthLogger
from .loggers import DashboardLogger, FileOperationLogger, LLMLogger

# Core logging components
from .unified_logger import (
    ContextLogger,
    LLMConversationLogger,
    PerformanceLogger,
    UserContext,
    context_logger,
    get_llm_logger,
    get_logger,
    get_performance_logger,
    initialize_logging,
    llm_conversation_logger,
    performance_logger,
)

# Compatibility aliases
get_unified_logger = get_logger
setup_logging = initialize_logging


# Legacy function aliases for backward compatibility
def log_info(message: str, **kwargs):
    """Legacy function for logging info messages"""
    context_logger.info(message, **kwargs)


def log_error(message: str, **kwargs):
    """Legacy function for logging error messages"""
    context_logger.error(message, **kwargs)


def log_debug(message: str, **kwargs):
    """Legacy function for logging debug messages"""
    context_logger.debug(message, **kwargs)


def log_warning(message: str, **kwargs):
    """Legacy function for logging warning messages"""
    context_logger.warning(message, **kwargs)


# Configuration management
from .config_manager import (
    ComponentConfig,
    LoggingConfig,
    MultiUserConfig,
    PerformanceConfig,
    SinkConfig,
)

# Context management
from .context_manager import (
    RequestContext,
    SessionManager,
    current_chat,
    current_request,
    current_session,
    current_user,
    get_context_extras,
    get_current_context,
    with_request_context,
    with_user_context,
)

# Utility functions
from .log_utils import generate_chat_id, generate_request_id, generate_session_id

# Migration utilities
from .migration_utils import (
    BackwardCompatibilityLogger,
    LoggingMigrationTool,
    MigrationResult,
    create_compatibility_logger,
    patch_logging_module,
    quick_migrate,
    validate_migration,
)

# Performance monitoring
from .performance_monitor import (
    OperationStats,
    PerformanceMetric,
    SystemMetrics,
    monitor_performance,
    performance_context,
)

# Rust integration - DISABLED for Component subscript compatibility
# from .rust_integration import (
#     RustLogHandler,
#     setup_rust_logging,
#     initialize_rust_module,
#     get_rust_log_stats,
#     ensure_rust_logging_setup
# )

# Version information
__version__ = "2.0.0"
__author__ = "Circuit Synth Team"
__description__ = "Unified logging system for Circuit Synth with multi-user support and performance monitoring"

# Default instances for easy access
logger = context_logger
perf_logger = performance_logger
llm_logger = llm_conversation_logger

# Convenience aliases
log = context_logger
performance = performance_logger
llm = llm_conversation_logger


def setup_unified_logging(
    config_path: str = "src/circuit_synth/core/logging/logging_config.yaml",
    enable_rust: bool = True,
    enable_migration_compat: bool = False,
) -> None:
    """
    Complete setup of the unified logging system.

    This function initializes all components of the unified logging system
    including configuration, Rust integration, and optional backward compatibility.

    Args:
        config_path: Path to the logging configuration YAML file
        enable_rust: Whether to enable Rust logging integration
        enable_migration_compat: Whether to patch standard logging for compatibility
    """
    try:
        # Initialize core logging system
        initialize_logging(config_path)

        # Set up Rust integration if enabled
        if enable_rust:
            try:
                ensure_rust_logging_setup()
                context_logger.info(
                    "Rust logging integration enabled", component="SYSTEM"
                )
            except Exception as e:
                context_logger.warning(
                    f"Rust logging integration failed: {e}",
                    component="SYSTEM",
                    error_type=type(e).__name__,
                )

        # Set up backward compatibility if enabled
        if enable_migration_compat:
            try:
                patch_logging_module()
                context_logger.info(
                    "Backward compatibility patching enabled", component="SYSTEM"
                )
            except Exception as e:
                context_logger.warning(
                    f"Backward compatibility patching failed: {e}",
                    component="SYSTEM",
                    error_type=type(e).__name__,
                )

        context_logger.info(
            "Unified logging system setup completed successfully",
            component="SYSTEM",
            config_path=config_path,
            rust_enabled=enable_rust,
            compat_enabled=enable_migration_compat,
        )

    except Exception as e:
        # Fallback to stderr if logging setup fails
        import sys

        sys.stderr.write(f"CRITICAL: Failed to setup unified logging: {e}\n")
        raise


def get_system_status() -> dict:
    """
    Get comprehensive status of the unified logging system.

    Returns:
        Dictionary with system status information
    """
    try:
        # Get session statistics
        session_manager = SessionManager.get_instance()
        session_stats = session_manager.get_session_stats()

        # Get performance statistics
        perf_stats = performance_logger.get_all_operation_stats(hours=1)
        system_metrics = performance_logger.get_system_metrics_summary(hours=1)

        # Get Rust integration status
        rust_stats = get_rust_log_stats()

        return {
            "system": {
                "version": __version__,
                "status": "operational",
                "uptime_info": "Available via system metrics",
            },
            "sessions": session_stats,
            "performance": {
                "operations_tracked": len(perf_stats),
                "system_metrics": system_metrics,
            },
            "rust_integration": rust_stats,
            "timestamp": get_current_context()["timestamp"],
        }

    except Exception as e:
        return {
            "system": {"version": __version__, "status": "error", "error": str(e)},
            "timestamp": get_current_context()["timestamp"],
        }


# Auto-initialize with default settings if not already initialized
def _auto_initialize():
    """Auto-initialize the logging system with default settings."""
    try:
        # Check if already initialized by trying to log
        context_logger.debug("Testing logging system", component="INIT")
    except Exception:
        # Not initialized, set up with defaults
        try:
            setup_unified_logging(enable_rust=False, enable_migration_compat=False)
        except Exception as e:
            # Fallback to basic setup
            import sys

            sys.stderr.write(f"Warning: Auto-initialization failed: {e}\n")


# Perform auto-initialization when module is imported
_auto_initialize()

# Export all public components
__all__ = [
    # Core components
    "ContextLogger",
    "PerformanceLogger",
    "LLMConversationLogger",
    "UserContext",
    "initialize_logging",
    "context_logger",
    "performance_logger",
    "llm_conversation_logger",
    "get_logger",
    "get_performance_logger",
    "get_llm_logger",
    # Legacy components for backward compatibility
    "CircuitSynthLogger",
    "DashboardLogger",
    "LLMLogger",
    "FileOperationLogger",
    "get_unified_logger",
    "setup_logging",
    "log_info",
    "log_error",
    "log_debug",
    "log_warning",
    # Context management
    "SessionManager",
    "RequestContext",
    "get_current_context",
    "get_context_extras",
    "with_user_context",
    "with_request_context",
    "current_user",
    "current_session",
    "current_request",
    "current_chat",
    # Performance monitoring
    "PerformanceMetric",
    "SystemMetrics",
    "OperationStats",
    "monitor_performance",
    "performance_context",
    # Configuration
    "LoggingConfig",
    "SinkConfig",
    "ComponentConfig",
    "MultiUserConfig",
    "PerformanceConfig",
    # Utility functions
    "generate_session_id",
    "generate_chat_id",
    "generate_request_id",
    # Migration utilities
    "BackwardCompatibilityLogger",
    "LoggingMigrationTool",
    "MigrationResult",
    "create_compatibility_logger",
    "patch_logging_module",
    "validate_migration",
    "quick_migrate",
    # Rust integration
    "RustLogHandler",
    "setup_rust_logging",
    "initialize_rust_module",
    "get_rust_log_stats",
    "ensure_rust_logging_setup",
    # Convenience aliases
    "logger",
    "perf_logger",
    "llm_logger",
    "log",
    "performance",
    "llm",
    # Setup functions
    "setup_unified_logging",
    "get_system_status",
    # Version info
    "__version__",
    "__author__",
    "__description__",
]
