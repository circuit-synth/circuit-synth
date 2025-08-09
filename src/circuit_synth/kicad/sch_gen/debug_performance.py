"""
Performance debugging utilities for KiCad generation.
Adds detailed timing and profiling for slow operations.
"""

import functools
import logging
import time
from contextlib import contextmanager
from typing import Any, Callable, Dict, Optional

logger = logging.getLogger(__name__)

# Global performance tracking
PERF_DATA: Dict[str, Any] = {
    "symbol_lookups": {},
    "net_labels": {},
    "component_details": {},
    "slow_operations": [],
}


@contextmanager
def timed_operation(
    name: str, threshold_ms: float = 10.0, details: Optional[Dict] = None
):
    """
    Context manager for timing operations with detailed logging.

    Args:
        name: Operation name
        threshold_ms: Log warning if operation takes longer than this
        details: Additional details to log
    """
    start_time = time.perf_counter()
    logger.debug(f"⏱️  START: {name}")
    if details:
        logger.debug(f"   Details: {details}")

    try:
        yield
    finally:
        elapsed_ms = (time.perf_counter() - start_time) * 1000

        if elapsed_ms > threshold_ms:
            logger.warning(
                f"🐌 SLOW OPERATION: {name} took {elapsed_ms:.2f}ms (threshold: {threshold_ms}ms)"
            )
            if details:
                logger.warning(f"   Context: {details}")

            # Track slow operations
            PERF_DATA["slow_operations"].append(
                {"name": name, "time_ms": elapsed_ms, "details": details or {}}
            )
        else:
            logger.debug(f"⏱️  END: {name} completed in {elapsed_ms:.2f}ms")


def profile_function(threshold_ms: float = 10.0):
    """
    Decorator to profile function execution with detailed logging.
    """

    def decorator(func: Callable) -> Callable:
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            func_name = f"{func.__module__}.{func.__name__}"

            # Extract useful details from args
            details = {}
            if args and hasattr(args[0], "__class__"):
                details["class"] = args[0].__class__.__name__
            if "lib_id" in kwargs:
                details["lib_id"] = kwargs["lib_id"]
            if "symbol" in kwargs:
                details["symbol"] = kwargs["symbol"]

            with timed_operation(func_name, threshold_ms, details):
                return func(*args, **kwargs)

        return wrapper

    return decorator


def log_symbol_lookup(
    lib_id: str, found: bool, time_ms: float, source: str = "unknown"
):
    """Log detailed symbol lookup information."""
    logger.debug(f"📚 Symbol Lookup: {lib_id}")
    logger.debug(f"   Found: {found}, Time: {time_ms:.2f}ms, Source: {source}")

    # Track in performance data
    if lib_id not in PERF_DATA["symbol_lookups"]:
        PERF_DATA["symbol_lookups"][lib_id] = []

    PERF_DATA["symbol_lookups"][lib_id].append(
        {"found": found, "time_ms": time_ms, "source": source}
    )

    # Warn if slow
    if time_ms > 50:
        logger.warning(
            f"🐌 SLOW SYMBOL LOOKUP: {lib_id} took {time_ms:.2f}ms from {source}"
        )


def log_net_label_creation(net_name: str, component_ref: str, pin: str, time_ms: float):
    """Log detailed net label creation information."""
    label_key = f"{net_name}:{component_ref}:{pin}"

    logger.debug(f"🏷️  Net Label: {label_key}")
    logger.debug(f"   Time: {time_ms:.2f}ms")

    # Track in performance data
    if net_name not in PERF_DATA["net_labels"]:
        PERF_DATA["net_labels"][net_name] = []

    PERF_DATA["net_labels"][net_name].append(
        {"component": component_ref, "pin": pin, "time_ms": time_ms}
    )

    # Warn if slow
    if time_ms > 5:
        logger.warning(f"🐌 SLOW NET LABEL: {label_key} took {time_ms:.2f}ms")


def log_component_processing(
    component_ref: str,
    lib_id: str,
    operation: str,
    time_ms: float,
    details: Optional[Dict] = None,
):
    """Log detailed component processing information."""
    logger.debug(f"🔧 Component Processing: {component_ref} ({lib_id})")
    logger.debug(f"   Operation: {operation}, Time: {time_ms:.2f}ms")
    if details:
        logger.debug(f"   Details: {details}")

    # Track in performance data
    if component_ref not in PERF_DATA["component_details"]:
        PERF_DATA["component_details"][component_ref] = {}

    if operation not in PERF_DATA["component_details"][component_ref]:
        PERF_DATA["component_details"][component_ref][operation] = []

    PERF_DATA["component_details"][component_ref][operation].append(
        {"lib_id": lib_id, "time_ms": time_ms, "details": details or {}}
    )

    # Warn if slow
    if time_ms > 20:
        logger.warning(
            f"🐌 SLOW COMPONENT OPERATION: {component_ref} - {operation} took {time_ms:.2f}ms"
        )


def print_performance_summary():
    """Print a summary of performance data collected."""
    print("\n" + "=" * 80)
    print("📊 PERFORMANCE DEBUGGING SUMMARY")
    print("=" * 80)

    # Slow operations
    if PERF_DATA["slow_operations"]:
        print("\n🐌 SLOW OPERATIONS (>10ms):")
        print("-" * 60)
        sorted_ops = sorted(
            PERF_DATA["slow_operations"], key=lambda x: x["time_ms"], reverse=True
        )
        for op in sorted_ops[:20]:  # Top 20
            print(f"  {op['name']:50s}: {op['time_ms']:8.2f}ms")
            if op["details"]:
                for key, value in op["details"].items():
                    print(f"    {key}: {value}")

    # Symbol lookup analysis
    if PERF_DATA["symbol_lookups"]:
        print("\n📚 SYMBOL LOOKUP ANALYSIS:")
        print("-" * 60)
        total_time = 0
        slow_symbols = []

        for lib_id, lookups in PERF_DATA["symbol_lookups"].items():
            total_lookup_time = sum(l["time_ms"] for l in lookups)
            total_time += total_lookup_time

            if total_lookup_time > 50:
                slow_symbols.append((lib_id, total_lookup_time, len(lookups)))

        if slow_symbols:
            print("  Slow symbol lookups (>50ms total):")
            for lib_id, time_ms, count in sorted(
                slow_symbols, key=lambda x: x[1], reverse=True
            ):
                avg_time = time_ms / count
                print(
                    f"    {lib_id:50s}: {time_ms:8.2f}ms total ({count} lookups, {avg_time:.2f}ms avg)"
                )

        print(f"\n  Total symbol lookup time: {total_time:.2f}ms")

    # Net label analysis
    if PERF_DATA["net_labels"]:
        print("\n🏷️  NET LABEL ANALYSIS:")
        print("-" * 60)
        total_time = 0
        label_count = 0

        for net_name, labels in PERF_DATA["net_labels"].items():
            net_time = sum(l["time_ms"] for l in labels)
            total_time += net_time
            label_count += len(labels)

            if net_time > 10:
                print(f"  {net_name:30s}: {net_time:8.2f}ms ({len(labels)} labels)")

        if label_count > 0:
            print(f"\n  Total net label time: {total_time:.2f}ms")
            print(f"  Total labels created: {label_count}")
            print(f"  Average per label: {total_time/label_count:.2f}ms")

    # Component processing analysis
    if PERF_DATA["component_details"]:
        print("\n🔧 COMPONENT PROCESSING ANALYSIS:")
        print("-" * 60)

        component_totals = {}
        for comp_ref, operations in PERF_DATA["component_details"].items():
            total_time = 0
            for op_name, op_list in operations.items():
                op_time = sum(o["time_ms"] for o in op_list)
                total_time += op_time
            component_totals[comp_ref] = total_time

        # Sort by total time
        sorted_comps = sorted(
            component_totals.items(), key=lambda x: x[1], reverse=True
        )

        print("  Slowest components:")
        for comp_ref, total_time in sorted_comps[:10]:  # Top 10
            if total_time > 10:
                print(f"    {comp_ref:30s}: {total_time:8.2f}ms")

                # Show operation breakdown
                if comp_ref in PERF_DATA["component_details"]:
                    for op_name, op_list in PERF_DATA["component_details"][
                        comp_ref
                    ].items():
                        op_time = sum(o["time_ms"] for o in op_list)
                        if op_time > 5:
                            print(f"      - {op_name}: {op_time:.2f}ms")

    return PERF_DATA


def reset_performance_data():
    """Reset performance tracking data."""
    global PERF_DATA
    PERF_DATA = {
        "symbol_lookups": {},
        "net_labels": {},
        "component_details": {},
        "slow_operations": [],
    }
