"""
Logging decorators for easy integration with Dash callbacks and other functions.
"""

import functools
import time
import traceback
from typing import Any, Callable, Dict, Optional

from .loggers import DashboardLogger


def log_dash_callback(logger: Optional[DashboardLogger] = None):
    """
    Decorator to automatically log Dash callback execution.

    Args:
        logger: Optional DashboardLogger instance. If not provided,
                a default logger will be used.

    Usage:
        @app.callback(...)
        @log_dash_callback(dashboard_logger)
        def my_callback(...):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Get callback context
            from dash import callback_context

            # Extract callback info
            callback_id = func.__name__
            triggered = callback_context.triggered if callback_context.triggered else []
            triggered_by = triggered[0]["prop_id"] if triggered else "unknown"

            # Get inputs and states from context
            inputs = {}
            states = {}

            if callback_context.inputs:
                inputs = callback_context.inputs
            if callback_context.states:
                states = callback_context.states

            # Use provided logger or create a temporary one
            active_logger = logger
            if not active_logger:
                # Try to get username from context or use 'system'
                active_logger = DashboardLogger("system")

            # Log callback start
            start_time = active_logger.log_callback_start(
                callback_id=callback_id,
                inputs=inputs,
                state=states,
                triggered_by=triggered_by,
            )

            error = None
            result = None

            try:
                # Execute the callback
                result = func(*args, **kwargs)
                return result

            except Exception as e:
                # Capture error for logging
                error = f"{type(e).__name__}: {str(e)}"
                # Log the full traceback
                active_logger.log_error(
                    error_type="callback_error",
                    error_message=str(e),
                    traceback=traceback.format_exc(),
                )
                # Re-raise the exception
                raise

            finally:
                # Log callback end
                outputs = {}
                if result is not None:
                    # Try to extract output info
                    if isinstance(result, (list, tuple)):
                        outputs = {"output_count": len(result)}
                    else:
                        outputs = {"output_type": type(result).__name__}

                active_logger.log_callback_end(
                    callback_id=callback_id, outputs=outputs, error=error
                )

        return wrapper

    return decorator


def log_user_action(action_type: str, logger: Optional[DashboardLogger] = None):
    """
    Decorator to log specific user actions.

    Args:
        action_type: Type of action being performed
        logger: Optional DashboardLogger instance

    Usage:
        @log_user_action('button_click', dashboard_logger)
        def handle_button_click(...):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            # Use provided logger or create a temporary one
            active_logger = logger
            if not active_logger:
                active_logger = DashboardLogger("system")

            # Extract details from args/kwargs
            details = {
                "function": func.__name__,
                "args_count": len(args),
                "kwargs_keys": list(kwargs.keys()),
            }

            # Log the action
            active_logger.log_user_action(action=action_type, details=details)

            # Execute the function
            return func(*args, **kwargs)

        return wrapper

    return decorator


def log_performance(operation_name: str, logger: Any = None):
    """
    Decorator to log performance metrics for any operation.

    Args:
        operation_name: Name of the operation being measured
        logger: Logger instance with log_response_time method

    Usage:
        @log_performance('data_processing', performance_logger)
        def process_data(...):
            ...
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            start_time = time.time()

            try:
                result = func(*args, **kwargs)
                return result
            finally:
                duration_ms = (time.time() - start_time) * 1000

                if logger and hasattr(logger, "log_response_time"):
                    logger.log_response_time(
                        operation=operation_name,
                        duration_ms=duration_ms,
                        metadata={"function": func.__name__},
                    )

        return wrapper

    return decorator


class CallbackLogger:
    """
    Context manager for logging callback execution in bulk operations.

    Usage:
        with CallbackLogger(dashboard_logger) as cb_logger:
            cb_logger.log_input('user_text', user_input)
            # ... callback logic ...
            cb_logger.log_output('generated_text', output)
    """

    def __init__(self, logger: DashboardLogger, callback_id: str):
        self.logger = logger
        self.callback_id = callback_id
        self.start_time = None
        self.inputs = {}
        self.outputs = {}
        self.error = None

    def __enter__(self):
        self.start_time = time.time()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        duration_ms = (time.time() - self.start_time) * 1000

        if exc_type:
            self.error = f"{exc_type.__name__}: {exc_val}"

        self.logger.log_dash_callback(
            callback_id=self.callback_id,
            action="complete",
            duration_ms=duration_ms,
            input_state=self.inputs,
            output_state=self.outputs,
        )

        if self.error:
            self.logger.log_error(
                error_type="callback_error",
                error_message=self.error,
                traceback=traceback.format_exc() if exc_tb else None,
            )

    def log_input(self, key: str, value: Any):
        """Log an input value."""
        self.inputs[key] = value

    def log_output(self, key: str, value: Any):
        """Log an output value."""
        self.outputs[key] = value

    def log_state(self, key: str, value: Any):
        """Log a state value."""
        self.inputs[f"state_{key}"] = value
