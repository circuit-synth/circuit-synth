#!/usr/bin/env python3
"""
Cache Performance Monitor

This module provides real-time monitoring and logging of cache usage,
comparing Python vs Rust cache performance and tracking metrics.
"""

import os
import sys
import time
import json
import logging
import threading
from pathlib import Path
from typing import Dict, List, Any, Optional, Callable
from dataclasses import dataclass, asdict
from contextlib import contextmanager
from collections import defaultdict, deque
import psutil

# Add the src directory to the path
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class CacheOperation:
    """Represents a single cache operation"""
    timestamp: float
    operation_type: str  # 'search', 'get', 'set', 'invalidate'
    cache_type: str     # 'symbol', 'footprint', 'component', 'knowledge'
    implementation: str  # 'python', 'rust'
    duration_ms: float
    query: Optional[str] = None
    result_count: Optional[int] = None
    cache_hit: Optional[bool] = None
    memory_usage_mb: Optional[float] = None
    error: Optional[str] = None


@dataclass
class CacheStats:
    """Aggregated cache statistics"""
    total_operations: int = 0
    total_duration_ms: float = 0.0
    avg_duration_ms: float = 0.0
    min_duration_ms: float = float('inf')
    max_duration_ms: float = 0.0
    cache_hits: int = 0
    cache_misses: int = 0
    hit_rate: float = 0.0
    errors: int = 0
    memory_peak_mb: float = 0.0


class CacheMonitor:
    """Real-time cache performance monitor"""
    
    def __init__(self, max_operations: int = 10000):
        self.max_operations = max_operations
        self.operations: deque = deque(maxlen=max_operations)
        self.stats_by_implementation: Dict[str, CacheStats] = defaultdict(CacheStats)
        self.stats_by_cache_type: Dict[str, CacheStats] = defaultdict(CacheStats)
        self.monitoring_active = False
        self.monitor_thread: Optional[threading.Thread] = None
        self.lock = threading.Lock()
        
        # Performance tracking
        self.start_time = time.time()
        self.last_stats_update = time.time()
        
        # Memory monitoring
        self.process = psutil.Process()
        self.baseline_memory_mb = self.process.memory_info().rss / 1024 / 1024
    
    def start_monitoring(self):
        """Start background monitoring"""
        if self.monitoring_active:
            return
        
        self.monitoring_active = True
        self.monitor_thread = threading.Thread(target=self._monitor_loop, daemon=True)
        self.monitor_thread.start()
        logger.info("Cache monitoring started")
    
    def stop_monitoring(self):
        """Stop background monitoring"""
        self.monitoring_active = False
        if self.monitor_thread:
            self.monitor_thread.join(timeout=1.0)
        logger.info("Cache monitoring stopped")
    
    def _monitor_loop(self):
        """Background monitoring loop"""
        while self.monitoring_active:
            try:
                # Update memory usage
                current_memory = self.process.memory_info().rss / 1024 / 1024
                memory_delta = current_memory - self.baseline_memory_mb
                
                # Update peak memory for all implementations
                for stats in self.stats_by_implementation.values():
                    stats.memory_peak_mb = max(stats.memory_peak_mb, memory_delta)
                
                time.sleep(1.0)  # Monitor every second
            except Exception as e:
                logger.warning(f"Monitoring error: {e}")
    
    @contextmanager
    def monitor_operation(self, 
                         operation_type: str,
                         cache_type: str,
                         implementation: str,
                         query: Optional[str] = None):
        """Context manager to monitor a cache operation"""
        start_time = time.perf_counter()
        start_memory = self.process.memory_info().rss / 1024 / 1024
        
        operation = CacheOperation(
            timestamp=time.time(),
            operation_type=operation_type,
            cache_type=cache_type,
            implementation=implementation,
            duration_ms=0.0,
            query=query,
            memory_usage_mb=start_memory - self.baseline_memory_mb
        )
        
        try:
            yield operation
            success = True
        except Exception as e:
            operation.error = str(e)
            success = False
            raise
        finally:
            end_time = time.perf_counter()
            end_memory = self.process.memory_info().rss / 1024 / 1024
            
            operation.duration_ms = (end_time - start_time) * 1000
            operation.memory_usage_mb = end_memory - self.baseline_memory_mb
            
            # Record the operation
            self.record_operation(operation)
    
    def record_operation(self, operation: CacheOperation):
        """Record a cache operation"""
        with self.lock:
            self.operations.append(operation)
            self._update_stats(operation)
    
    def _update_stats(self, operation: CacheOperation):
        """Update aggregated statistics"""
        # Update implementation stats
        impl_stats = self.stats_by_implementation[operation.implementation]
        self._update_single_stats(impl_stats, operation)
        
        # Update cache type stats
        cache_stats = self.stats_by_cache_type[operation.cache_type]
        self._update_single_stats(cache_stats, operation)
    
    def _update_single_stats(self, stats: CacheStats, operation: CacheOperation):
        """Update a single stats object"""
        stats.total_operations += 1
        stats.total_duration_ms += operation.duration_ms
        stats.avg_duration_ms = stats.total_duration_ms / stats.total_operations
        stats.min_duration_ms = min(stats.min_duration_ms, operation.duration_ms)
        stats.max_duration_ms = max(stats.max_duration_ms, operation.duration_ms)
        
        if operation.cache_hit is not None:
            if operation.cache_hit:
                stats.cache_hits += 1
            else:
                stats.cache_misses += 1
            
            total_cache_ops = stats.cache_hits + stats.cache_misses
            if total_cache_ops > 0:
                stats.hit_rate = stats.cache_hits / total_cache_ops
        
        if operation.error:
            stats.errors += 1
        
        if operation.memory_usage_mb:
            stats.memory_peak_mb = max(stats.memory_peak_mb, operation.memory_usage_mb)
    
    def get_performance_comparison(self) -> Dict[str, Any]:
        """Get performance comparison between implementations"""
        python_stats = self.stats_by_implementation.get('python', CacheStats())
        rust_stats = self.stats_by_implementation.get('rust', CacheStats())
        
        comparison = {
            'python': asdict(python_stats),
            'rust': asdict(rust_stats),
            'improvement_factor': 0.0,
            'memory_improvement': 0.0,
            'reliability_comparison': {
                'python_error_rate': 0.0,
                'rust_error_rate': 0.0
            }
        }
        
        # Calculate performance improvement
        if rust_stats.avg_duration_ms > 0 and python_stats.avg_duration_ms > 0:
            comparison['improvement_factor'] = python_stats.avg_duration_ms / rust_stats.avg_duration_ms
        
        # Calculate memory improvement
        if rust_stats.memory_peak_mb > 0 and python_stats.memory_peak_mb > 0:
            comparison['memory_improvement'] = python_stats.memory_peak_mb / rust_stats.memory_peak_mb
        
        # Calculate error rates
        if python_stats.total_operations > 0:
            comparison['reliability_comparison']['python_error_rate'] = python_stats.errors / python_stats.total_operations
        
        if rust_stats.total_operations > 0:
            comparison['reliability_comparison']['rust_error_rate'] = rust_stats.errors / rust_stats.total_operations
        
        return comparison
    
    def get_recent_operations(self, count: int = 100) -> List[Dict[str, Any]]:
        """Get recent operations"""
        with self.lock:
            recent = list(self.operations)[-count:]
            return [asdict(op) for op in recent]
    
    def export_metrics(self, output_file: Path):
        """Export all metrics to JSON file"""
        metrics = {
            'monitoring_duration_seconds': time.time() - self.start_time,
            'total_operations': len(self.operations),
            'stats_by_implementation': {k: asdict(v) for k, v in self.stats_by_implementation.items()},
            'stats_by_cache_type': {k: asdict(v) for k, v in self.stats_by_cache_type.items()},
            'performance_comparison': self.get_performance_comparison(),
            'recent_operations': self.get_recent_operations(1000),
            'baseline_memory_mb': self.baseline_memory_mb
        }
        
        with open(output_file, 'w') as f:
            json.dump(metrics, f, indent=2, default=str)
        
        logger.info(f"Metrics exported to: {output_file}")
    
    def print_summary(self):
        """Print a summary of current metrics"""
        comparison = self.get_performance_comparison()
        
        print("\n" + "=" * 60)
        print("CACHE PERFORMANCE SUMMARY")
        print("=" * 60)
        
        print(f"Monitoring duration: {time.time() - self.start_time:.1f} seconds")
        print(f"Total operations recorded: {len(self.operations)}")
        
        print("\nImplementation Comparison:")
        for impl, stats in self.stats_by_implementation.items():
            print(f"\n{impl.upper()} Cache:")
            print(f"  Operations: {stats.total_operations}")
            print(f"  Avg duration: {stats.avg_duration_ms:.2f}ms")
            print(f"  Hit rate: {stats.hit_rate:.1%}")
            print(f"  Error rate: {stats.errors/max(stats.total_operations, 1):.1%}")
            print(f"  Peak memory: {stats.memory_peak_mb:.1f}MB")
        
        if comparison['improvement_factor'] > 1:
            print(f"\n🚀 Rust is {comparison['improvement_factor']:.1f}x faster than Python!")
        elif comparison['improvement_factor'] > 0:
            print(f"\n⚠️  Python is {1/comparison['improvement_factor']:.1f}x faster than Rust")
        
        print("\nCache Type Breakdown:")
        for cache_type, stats in self.stats_by_cache_type.items():
            print(f"  {cache_type}: {stats.total_operations} ops, {stats.avg_duration_ms:.2f}ms avg")


class CacheInstrumentor:
    """Instruments cache classes to automatically monitor operations"""
    
    def __init__(self, monitor: CacheMonitor):
        self.monitor = monitor
        self.original_methods: Dict[str, Callable] = {}
    
    def instrument_python_cache(self, cache_obj, cache_type: str):
        """Instrument a Python cache object"""
        methods_to_monitor = ['search', 'get', 'search_symbols', 'get_symbol', 'get_footprint']
        
        for method_name in methods_to_monitor:
            if hasattr(cache_obj, method_name):
                original_method = getattr(cache_obj, method_name)
                instrumented_method = self._create_instrumented_method(
                    original_method, method_name, cache_type, 'python'
                )
                setattr(cache_obj, method_name, instrumented_method)
                self.original_methods[f"python_{cache_type}_{method_name}"] = original_method
    
    def instrument_rust_cache(self, cache_obj, cache_type: str):
        """Instrument a Rust cache object"""
        methods_to_monitor = ['search_symbols', 'search_footprints', 'search_components', 'search_all']
        
        for method_name in methods_to_monitor:
            if hasattr(cache_obj, method_name):
                original_method = getattr(cache_obj, method_name)
                instrumented_method = self._create_instrumented_method(
                    original_method, method_name, cache_type, 'rust'
                )
                setattr(cache_obj, method_name, instrumented_method)
                self.original_methods[f"rust_{cache_type}_{method_name}"] = original_method
    
    def _create_instrumented_method(self, original_method, method_name, cache_type, implementation):
        """Create an instrumented version of a method"""
        def instrumented_method(*args, **kwargs):
            # Extract query if possible
            query = None
            if args and isinstance(args[0], str):
                query = args[0]
            elif 'query' in kwargs:
                query = kwargs['query']
            
            with self.monitor.monitor_operation(method_name, cache_type, implementation, query) as operation:
                result = original_method(*args, **kwargs)
                
                # Try to extract result information
                if hasattr(result, '__len__'):
                    operation.result_count = len(result)
                elif result is not None:
                    operation.result_count = 1
                else:
                    operation.result_count = 0
                
                # Assume cache hit if we got results (simplified)
                operation.cache_hit = operation.result_count > 0
                
                return result
        
        return instrumented_method
    
    def restore_original_methods(self, cache_obj, cache_type: str, implementation: str):
        """Restore original methods"""
        for key, original_method in self.original_methods.items():
            if key.startswith(f"{implementation}_{cache_type}_"):
                method_name = key.split('_', 2)[2]
                if hasattr(cache_obj, method_name):
                    setattr(cache_obj, method_name, original_method)


def create_monitored_example_runner(monitor: CacheMonitor) -> Callable:
    """Create a function that runs the example with monitoring"""
    
    def run_monitored_example():
        """Run the example project with cache monitoring"""
        import subprocess
        import sys
        from pathlib import Path
        
        project_root = Path(__file__).parent.parent.parent
        example_script = project_root / "examples" / "example_kicad_project.py"
        
        logger.info("Running example project with cache monitoring...")
        
        # Start monitoring
        monitor.start_monitoring()
        
        try:
            # Run the example script
            with monitor.monitor_operation("example_execution", "integrated", "python"):
                result = subprocess.run(
                    [sys.executable, str(example_script)],
                    cwd=str(project_root),
                    capture_output=True,
                    text=True,
                    timeout=300
                )
            
            success = result.returncode == 0
            
            if success:
                logger.info("✅ Example project completed successfully")
            else:
                logger.error(f"❌ Example project failed: {result.stderr[:200]}")
            
            return success, result
            
        finally:
            monitor.stop_monitoring()
    
    return run_monitored_example


def main():
    """Main function for standalone monitoring"""
    import argparse
    
    parser = argparse.ArgumentParser(description="Monitor cache performance")
    parser.add_argument('--duration', type=int, default=60,
                       help='Monitoring duration in seconds')
    parser.add_argument('--output', type=Path, default=Path('cache_metrics.json'),
                       help='Output file for metrics')
    parser.add_argument('--run-example', action='store_true',
                       help='Run the example project with monitoring')
    
    args = parser.parse_args()
    
    # Create monitor
    monitor = CacheMonitor()
    
    if args.run_example:
        # Run example with monitoring
        runner = create_monitored_example_runner(monitor)
        success, result = runner()
        
        # Print summary
        monitor.print_summary()
        
        # Export metrics
        monitor.export_metrics(args.output)
        
        return 0 if success else 1
    else:
        # Just monitor for the specified duration
        monitor.start_monitoring()
        
        try:
            logger.info(f"Monitoring for {args.duration} seconds...")
            time.sleep(args.duration)
        except KeyboardInterrupt:
            logger.info("Monitoring interrupted by user")
        finally:
            monitor.stop_monitoring()
            monitor.print_summary()
            monitor.export_metrics(args.output)
        
        return 0


if __name__ == "__main__":
    sys.exit(main())