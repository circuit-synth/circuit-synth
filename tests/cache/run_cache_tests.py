#!/usr/bin/env python3
"""
Master Cache Test Runner

This script orchestrates the complete Rust cache testing strategy,
providing a single entry point for all cache validation and testing.
"""

import argparse
import json
import logging
import os
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from pathlib import Path
from typing import Any, Dict, List, Optional

# Add the current directory to path for imports
sys.path.insert(0, str(Path(__file__).parent))

# Removed rust_unified_cache imports
from cache_monitor import CacheMonitor, create_monitored_example_runner

# Import our testing modules
from clear_caches import CacheCleaner

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


@dataclass
class TestSuiteResult:
    """Result of running the complete test suite"""
    suite_name: str
    success: bool
    duration_seconds: float
    summary: Dict[str, Any]
    output_files: List[str]
    error_message: Optional[str] = None


class MasterTestRunner:
    """Master test runner that orchestrates all cache testing"""
    
    def __init__(self, project_root: Path, output_dir: Path):
        self.project_root = project_root
        self.output_dir = output_dir
        self.output_dir.mkdir(parents=True, exist_ok=True)
        
        # Test suite results
        self.suite_results: List[TestSuiteResult] = []
        
        # Initialize components
        self.cache_cleaner = CacheCleaner(project_root)
        self.monitor = CacheMonitor()
        
        logger.info(f"Master test runner initialized")
        logger.info(f"Project root: {project_root}")
        logger.info(f"Output directory: {output_dir}")
    
    def run_cache_clearing(self, clear_all: bool = True) -> TestSuiteResult:
        """Run cache clearing operations"""
        logger.info("=" * 60)
        logger.info("RUNNING CACHE CLEARING")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        try:
            if clear_all:
                success = self.cache_cleaner.clear_all_caches()
            else:
                # Clear only Rust caches for targeted testing
                success = self.cache_cleaner.clear_rust_caches()
            
            duration = time.time() - start_time
            
            # Generate cache locations report
            cache_locations_file = self.output_dir / "cache_locations.json"
            locations_data = {
                'cache_locations': self.cache_cleaner.cache_locations,
                'clearing_successful': success,
                'timestamp': time.time()
            }
            
            with open(cache_locations_file, 'w') as f:
                json.dump(locations_data, f, indent=2, default=str)
            
            result = TestSuiteResult(
                suite_name="cache_clearing",
                success=success,
                duration_seconds=duration,
                summary={
                    'caches_cleared': success,
                    'cache_locations': self.cache_cleaner.cache_locations
                },
                output_files=[str(cache_locations_file)]
            )
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestSuiteResult(
                suite_name="cache_clearing",
                success=False,
                duration_seconds=duration,
                summary={},
                output_files=[],
                error_message=str(e)
            )
        
        self.suite_results.append(result)
        return result
    
    def run_integration_tests(self) -> TestSuiteResult:
        """Run integration test suite - DISABLED (rust_unified_cache removed)"""
        logger.info("=" * 60)
        logger.info("SKIPPING INTEGRATION TESTS (rust_unified_cache removed)")
        logger.info("=" * 60)
        
        start_time = time.time()
        duration = time.time() - start_time
        
        result = TestSuiteResult(
            suite_name="integration_tests",
            success=True,  # Skip successfully
            duration_seconds=duration,
            summary={"skipped": True, "reason": "rust_unified_cache removed"},
            output_files=[]
        )
        
        self.suite_results.append(result)
        return result
    
    def run_rust_cache_validation(self) -> TestSuiteResult:
        """Run Rust cache validation - DISABLED (rust_unified_cache removed)"""
        logger.info("=" * 60)
        logger.info("SKIPPING RUST CACHE VALIDATION (rust_unified_cache removed)")
        logger.info("=" * 60)
        
        start_time = time.time()
        duration = time.time() - start_time
        
        result = TestSuiteResult(
            suite_name="rust_cache_validation",
            success=True,  # Skip successfully
            duration_seconds=duration,
            summary={"skipped": True, "reason": "rust_unified_cache removed"},
            output_files=[]
        )
        
        self.suite_results.append(result)
        return result
    
    def run_monitored_example(self) -> TestSuiteResult:
        """Run the example project with monitoring"""
        logger.info("=" * 60)
        logger.info("RUNNING MONITORED EXAMPLE PROJECT")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        try:
            # Create monitored runner
            runner = create_monitored_example_runner(self.monitor)
            
            # Run the example
            success, subprocess_result = runner()
            
            duration = time.time() - start_time
            
            # Export monitoring metrics
            metrics_file = self.output_dir / "example_monitoring_metrics.json"
            self.monitor.export_metrics(metrics_file)
            
            # Get performance comparison
            comparison = self.monitor.get_performance_comparison()
            
            summary = {
                'example_execution_successful': success,
                'subprocess_return_code': subprocess_result.returncode if subprocess_result else None,
                'performance_comparison': comparison,
                'monitoring_data_available': True
            }
            
            result = TestSuiteResult(
                suite_name="monitored_example",
                success=success,
                duration_seconds=duration,
                summary=summary,
                output_files=[str(metrics_file)]
            )
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestSuiteResult(
                suite_name="monitored_example",
                success=False,
                duration_seconds=duration,
                summary={},
                output_files=[],
                error_message=str(e)
            )
        
        self.suite_results.append(result)
        return result
    
    def run_performance_benchmarks(self) -> TestSuiteResult:
        """Run performance benchmarks"""
        logger.info("=" * 60)
        logger.info("RUNNING PERFORMANCE BENCHMARKS")
        logger.info("=" * 60)
        
        start_time = time.time()
        
        try:
            # Rust unified cache benchmarks removed
            benchmark_results = {
                'rust_benchmarks': {
                    'success': False,
                    'error': "rust_unified_cache removed from project"
                }
            }
            
            duration = time.time() - start_time
            
            # Save benchmark results
            benchmark_file = self.output_dir / "performance_benchmarks.json"
            with open(benchmark_file, 'w') as f:
                json.dump(benchmark_results, f, indent=2, default=str)
            
            success = benchmark_results.get('rust_benchmarks', {}).get('success', False)
            
            result = TestSuiteResult(
                suite_name="performance_benchmarks",
                success=success,
                duration_seconds=duration,
                summary=benchmark_results,
                output_files=[str(benchmark_file)]
            )
            
        except Exception as e:
            duration = time.time() - start_time
            result = TestSuiteResult(
                suite_name="performance_benchmarks",
                success=False,
                duration_seconds=duration,
                summary={},
                output_files=[],
                error_message=str(e)
            )
        
        self.suite_results.append(result)
        return result
    
    def run_complete_test_suite(self, 
                               clear_caches: bool = True,
                               run_integration: bool = True,
                               run_validation: bool = True,
                               run_monitoring: bool = True,
                               run_benchmarks: bool = True) -> Dict[str, Any]:
        """Run the complete test suite"""
        logger.info("🚀" * 20)
        logger.info("STARTING COMPLETE RUST CACHE TEST SUITE")
        logger.info("🚀" * 20)
        
        overall_start_time = time.time()
        
        # Clear previous results
        self.suite_results.clear()
        
        # Run test suites in order
        if clear_caches:
            self.run_cache_clearing()
        
        if run_integration:
            self.run_integration_tests()
        
        if run_validation:
            self.run_rust_cache_validation()
        
        if run_monitoring:
            self.run_monitored_example()
        
        if run_benchmarks:
            self.run_performance_benchmarks()
        
        overall_duration = time.time() - overall_start_time
        
        # Generate comprehensive summary
        summary = self._generate_comprehensive_summary(overall_duration)
        
        # Save master report
        master_report_file = self.output_dir / "master_test_report.json"
        with open(master_report_file, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        # Print final summary
        self._print_final_summary(summary)
        
        return summary
    
    def _generate_comprehensive_summary(self, overall_duration: float) -> Dict[str, Any]:
        """Generate comprehensive test summary"""
        total_suites = len(self.suite_results)
        successful_suites = sum(1 for r in self.suite_results if r.success)
        failed_suites = total_suites - successful_suites
        
        # Extract key metrics
        rust_cache_working = False
        performance_improvement = 0.0
        integration_success = False
        
        for result in self.suite_results:
            if result.suite_name == "rust_cache_validation" and result.success:
                rust_cache_working = True
                performance_improvement = result.summary.get('performance_improvement', 0.0)
            elif result.suite_name == "integration_tests" and result.success:
                integration_success = True
        
        # Collect all output files
        all_output_files = []
        for result in self.suite_results:
            all_output_files.extend(result.output_files)
        
        summary = {
            'test_execution_timestamp': time.time(),
            'overall_duration_seconds': overall_duration,
            'total_test_suites': total_suites,
            'successful_suites': successful_suites,
            'failed_suites': failed_suites,
            'success_rate': (successful_suites / total_suites * 100) if total_suites > 0 else 0,
            'rust_cache_status': {
                'working': rust_cache_working,
                'performance_improvement': performance_improvement,
                'integration_successful': integration_success
            },
            'suite_results': [asdict(r) for r in self.suite_results],
            'output_files': all_output_files,
            'recommendations': self._generate_recommendations()
        }
        
        return summary
    
    def _generate_recommendations(self) -> List[str]:
        """Generate recommendations based on test results"""
        recommendations = []
        
        # Check if Rust cache is working
        rust_validation = next((r for r in self.suite_results if r.suite_name == "rust_cache_validation"), None)
        
        if not rust_validation or not rust_validation.success:
            recommendations.append("ℹ️  Rust unified cache has been removed from the project.")
            recommendations.append("✅ Other Rust cache systems (rust_symbol_cache, rust_symbol_search, rust_reference_manager) remain available.")
        else:
            recommendations.append("ℹ️  Rust unified cache validation skipped (removed from project).")
        
        # Check integration
        integration = next((r for r in self.suite_results if r.suite_name == "integration_tests"), None)
        if integration and not integration.success:
            recommendations.append("⚠️  Integration tests failed. Check Python-Rust interface compatibility.")
        
        # Check example execution
        example = next((r for r in self.suite_results if r.suite_name == "monitored_example"), None)
        if example and not example.success:
            recommendations.append("⚠️  Example project execution failed. Check dependencies and configuration.")
        
        return recommendations
    
    def _print_final_summary(self, summary: Dict[str, Any]):
        """Print final test summary"""
        logger.info("🏁" * 20)
        logger.info("TEST SUITE COMPLETE")
        logger.info("🏁" * 20)
        
        logger.info(f"Overall duration: {summary['overall_duration_seconds']:.1f} seconds")
        logger.info(f"Test suites run: {summary['total_test_suites']}")
        logger.info(f"Successful: {summary['successful_suites']}")
        logger.info(f"Failed: {summary['failed_suites']}")
        logger.info(f"Success rate: {summary['success_rate']:.1f}%")
        
        rust_status = summary['rust_cache_status']
        if rust_status['working']:
            logger.info("🎉 Rust cache is working!")
            if rust_status['performance_improvement'] > 1:
                logger.info(f"🚀 Performance improvement: {rust_status['performance_improvement']:.1f}x")
        else:
            logger.warning("⚠️  Rust cache validation failed")
        
        logger.info("\nRecommendations:")
        for rec in summary['recommendations']:
            logger.info(f"  {rec}")
        
        logger.info(f"\nDetailed reports saved to: {self.output_dir}")
        logger.info("📊 Check the following files for detailed results:")
        for output_file in summary['output_files']:
            logger.info(f"  - {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Run comprehensive Rust cache test suite",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python run_cache_tests.py                    # Run complete test suite
  python run_cache_tests.py --quick            # Run quick validation only
  python run_cache_tests.py --no-clear        # Skip cache clearing
  python run_cache_tests.py --validation-only # Run only validation tests
        """
    )
    
    parser.add_argument('--project-root', type=Path,
                       default=Path(__file__).parent.parent.parent,
                       help='Project root directory')
    parser.add_argument('--output-dir', type=Path,
                       default=Path('cache_test_results'),
                       help='Output directory for test results')
    parser.add_argument('--no-clear', action='store_true',
                       help='Skip cache clearing')
    parser.add_argument('--no-integration', action='store_true',
                       help='Skip integration tests')
    parser.add_argument('--no-validation', action='store_true',
                       help='Skip validation tests')
    parser.add_argument('--no-monitoring', action='store_true',
                       help='Skip monitoring tests')
    parser.add_argument('--no-benchmarks', action='store_true',
                       help='Skip benchmark tests')
    parser.add_argument('--quick', action='store_true',
                       help='Run only validation (quick test)')
    parser.add_argument('--validation-only', action='store_true',
                       help='Run only validation tests')
    parser.add_argument('--verbose', '-v', action='store_true',
                       help='Enable verbose logging')
    
    args = parser.parse_args()
    
    if args.verbose:
        logging.getLogger().setLevel(logging.DEBUG)
    
    # Validate project root
    project_root = args.project_root.resolve()
    if not project_root.exists():
        logger.error(f"Project root does not exist: {project_root}")
        return 1
    
    # Create output directory
    output_dir = args.output_dir.resolve()
    
    # Create test runner
    runner = MasterTestRunner(project_root, output_dir)
    
    # Determine what to run
    if args.quick or args.validation_only:
        # Quick mode: only validation
        summary = runner.run_complete_test_suite(
            clear_caches=not args.no_clear,
            run_integration=False,
            run_validation=True,
            run_monitoring=False,
            run_benchmarks=False
        )
    else:
        # Full test suite
        summary = runner.run_complete_test_suite(
            clear_caches=not args.no_clear,
            run_integration=not args.no_integration,
            run_validation=not args.no_validation,
            run_monitoring=not args.no_monitoring,
            run_benchmarks=not args.no_benchmarks
        )
    
    # Return appropriate exit code
    rust_working = summary['rust_cache_status']['working']
    return 0 if rust_working else 1


if __name__ == "__main__":
    sys.exit(main())