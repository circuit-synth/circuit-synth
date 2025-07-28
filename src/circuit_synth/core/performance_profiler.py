"""
Performance profiling utility for identifying bottlenecks.

Provides detailed timing information for circuit generation operations.
"""

import time
import functools
from typing import Dict, List, Optional
from contextlib import contextmanager
from ._logger import context_logger

class PerformanceProfiler:
    """Detailed performance profiler for circuit generation."""
    
    def __init__(self):
        self.timings: Dict[str, List[float]] = {}
        self.current_operation: Optional[str] = None
        self.start_time: Optional[float] = None
        
    @contextmanager
    def profile(self, operation_name: str):
        """Context manager for timing operations."""
        start_time = time.perf_counter()
        context_logger.info(f"⏱️  PROFILER: Starting {operation_name}", component="PERFORMANCE")
        
        try:
            yield
        finally:
            end_time = time.perf_counter()
            duration = end_time - start_time
            
            if operation_name not in self.timings:
                self.timings[operation_name] = []
            self.timings[operation_name].append(duration)
            
            context_logger.info(
                f"⏱️  PROFILER: Completed {operation_name} in {duration:.3f}s", 
                component="PERFORMANCE"
            )
    
    def timing_decorator(self, operation_name: str):
        """Decorator for timing function calls."""
        def decorator(func):
            @functools.wraps(func)
            def wrapper(*args, **kwargs):
                with self.profile(f"{operation_name}:{func.__name__}"):
                    return func(*args, **kwargs)
            return wrapper
        return decorator
    
    def get_summary(self) -> Dict[str, Dict[str, float]]:
        """Get timing summary statistics."""
        summary = {}
        for operation, times in self.timings.items():
            summary[operation] = {
                'count': len(times),
                'total': sum(times),
                'average': sum(times) / len(times),
                'min': min(times),
                'max': max(times)
            }
        return summary
    
    def print_summary(self):
        """Print detailed timing summary."""
        summary = self.get_summary()
        
        context_logger.info("📊 PERFORMANCE SUMMARY:", component="PERFORMANCE")
        context_logger.info("=" * 60, component="PERFORMANCE")
        
        total_time = sum(stats['total'] for stats in summary.values())
        context_logger.info(f"🕐 Total Time: {total_time:.3f}s", component="PERFORMANCE")
        context_logger.info("", component="PERFORMANCE")
        
        # Sort by total time descending
        sorted_operations = sorted(
            summary.items(), 
            key=lambda x: x[1]['total'], 
            reverse=True
        )
        
        for operation, stats in sorted_operations:
            percentage = (stats['total'] / total_time) * 100 if total_time > 0 else 0
            context_logger.info(
                f"📈 {operation:30} | "
                f"{stats['total']:6.3f}s ({percentage:5.1f}%) | "
                f"avg: {stats['average']:6.3f}s | "
                f"count: {stats['count']:3d}",
                component="PERFORMANCE"
            )
        
        context_logger.info("=" * 60, component="PERFORMANCE")

# Global profiler instance
_global_profiler = PerformanceProfiler()

def get_profiler() -> PerformanceProfiler:
    """Get the global profiler instance."""
    return _global_profiler

def profile_operation(operation_name: str):
    """Decorator for profiling operations."""
    return _global_profiler.timing_decorator(operation_name)

@contextmanager
def profile(operation_name: str):
    """Context manager for profiling operations."""
    with _global_profiler.profile(operation_name):
        yield

def print_performance_summary():
    """Print performance summary."""
    _global_profiler.print_summary()

# Export timing utilities
__all__ = [
    'PerformanceProfiler',
    'get_profiler', 
    'profile_operation',
    'profile',
    'print_performance_summary'
]