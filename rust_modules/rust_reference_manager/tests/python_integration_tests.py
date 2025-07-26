#!/usr/bin/env python3
"""
Python integration tests for the Rust reference manager.

These tests verify that the Python wrapper works correctly and maintains
API compatibility with the original Python ReferenceManager.
"""

import unittest
import sys
import os
import time
from typing import Dict, Any

# Add the Python package to the path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'python'))

try:
    from rust_reference_manager import (
        RustReferenceManager,
        is_rust_available,
        is_using_rust,
        get_implementation_info,
        benchmark_performance,
        compare_implementations,
    )
    RUST_REFERENCE_MANAGER_AVAILABLE = True
except ImportError as e:
    print(f"Warning: Could not import rust_reference_manager: {e}")
    RUST_REFERENCE_MANAGER_AVAILABLE = False


class TestRustReferenceManagerBasics(unittest.TestCase):
    """Test basic functionality of the Rust reference manager."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not RUST_REFERENCE_MANAGER_AVAILABLE:
            self.skipTest("Rust reference manager not available")
        
        self.manager = RustReferenceManager()
    
    def test_basic_reference_generation(self):
        """Test basic reference generation functionality."""
        # Test sequential generation
        ref1 = self.manager.generate_next_reference("R")
        self.assertEqual(ref1, "R1")
        
        ref2 = self.manager.generate_next_reference("R")
        self.assertEqual(ref2, "R2")
        
        # Test different prefix
        ref3 = self.manager.generate_next_reference("C")
        self.assertEqual(ref3, "C1")
    
    def test_reference_validation(self):
        """Test reference validation functionality."""
        # Initially available
        self.assertTrue(self.manager.validate_reference("R1"))
        
        # Generate and check it's no longer available
        ref1 = self.manager.generate_next_reference("R")
        self.assertEqual(ref1, "R1")
        self.assertFalse(self.manager.validate_reference("R1"))
        
        # Other references should still be available
        self.assertTrue(self.manager.validate_reference("R99"))
        self.assertTrue(self.manager.validate_reference("C1"))
    
    def test_reference_registration(self):
        """Test manual reference registration."""
        # Should be able to register new reference
        self.manager.register_reference("U1")
        
        # Should not be available anymore
        self.assertFalse(self.manager.validate_reference("U1"))
        
        # Should not be able to register again
        with self.assertRaises(Exception):
            self.manager.register_reference("U1")
    
    def test_unnamed_net_generation(self):
        """Test unnamed net generation."""
        net1 = self.manager.generate_next_unnamed_net_name()
        self.assertEqual(net1, "N$1")
        
        net2 = self.manager.generate_next_unnamed_net_name()
        self.assertEqual(net2, "N$2")
        
        net3 = self.manager.generate_next_unnamed_net_name()
        self.assertEqual(net3, "N$3")
    
    def test_initial_counters(self):
        """Test initialization with initial counters."""
        counters = {"R": 10, "C": 5}
        manager = RustReferenceManager(initial_counters=counters)
        
        ref1 = manager.generate_next_reference("R")
        self.assertEqual(ref1, "R10")
        
        ref2 = manager.generate_next_reference("C")
        self.assertEqual(ref2, "C5")
        
        # New prefix should start from 1
        ref3 = manager.generate_next_reference("L")
        self.assertEqual(ref3, "L1")
    
    def test_set_initial_counters(self):
        """Test setting initial counters after creation."""
        # Generate a reference first
        ref1 = self.manager.generate_next_reference("R")
        self.assertEqual(ref1, "R1")
        
        # Set initial counters
        counters = {"R": 10, "C": 5}
        self.manager.set_initial_counters(counters)
        
        # R should continue from 10 (higher than current)
        ref2 = self.manager.generate_next_reference("R")
        self.assertEqual(ref2, "R10")
        
        # C should start from 5
        ref3 = self.manager.generate_next_reference("C")
        self.assertEqual(ref3, "C5")
    
    def test_get_all_used_references(self):
        """Test getting all used references."""
        # Initially empty
        refs = self.manager.get_all_used_references()
        self.assertEqual(len(refs), 0)
        
        # Generate some references
        self.manager.generate_next_reference("R")
        self.manager.generate_next_reference("C")
        self.manager.register_reference("U1")
        
        refs = self.manager.get_all_used_references()
        self.assertEqual(len(refs), 3)
        self.assertIn("R1", refs)
        self.assertIn("C1", refs)
        self.assertIn("U1", refs)
    
    def test_clear_functionality(self):
        """Test clearing all references."""
        # Generate some references
        self.manager.generate_next_reference("R")
        self.manager.generate_next_reference("C")
        self.manager.generate_next_unnamed_net_name()
        
        # Verify they exist
        refs = self.manager.get_all_used_references()
        self.assertGreater(len(refs), 0)
        
        # Clear everything
        self.manager.clear()
        
        # Verify everything is cleared
        refs = self.manager.get_all_used_references()
        self.assertEqual(len(refs), 0)
        
        # Verify counters are reset
        ref1 = self.manager.generate_next_reference("R")
        self.assertEqual(ref1, "R1")
        
        net1 = self.manager.generate_next_unnamed_net_name()
        self.assertEqual(net1, "N$1")


class TestRustReferenceManagerErrorHandling(unittest.TestCase):
    """Test error handling in the Rust reference manager."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not RUST_REFERENCE_MANAGER_AVAILABLE:
            self.skipTest("Rust reference manager not available")
        
        self.manager = RustReferenceManager()
    
    def test_invalid_prefixes(self):
        """Test handling of invalid prefixes."""
        invalid_prefixes = ["", "123", "R-", "@#$", "N$"]
        
        for prefix in invalid_prefixes:
            with self.assertRaises(Exception):
                self.manager.generate_next_reference(prefix)
    
    def test_invalid_references(self):
        """Test handling of invalid references."""
        invalid_references = ["", "123", "R", "GND", "VCC"]
        
        for reference in invalid_references:
            with self.assertRaises(Exception):
                self.manager.register_reference(reference)
    
    def test_duplicate_registration(self):
        """Test handling of duplicate reference registration."""
        # Register a reference
        self.manager.register_reference("R1")
        
        # Try to register the same reference again
        with self.assertRaises(Exception):
            self.manager.register_reference("R1")


class TestRustReferenceManagerPerformance(unittest.TestCase):
    """Test performance characteristics of the Rust reference manager."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not RUST_REFERENCE_MANAGER_AVAILABLE:
            self.skipTest("Rust reference manager not available")
        
        self.manager = RustReferenceManager()
    
    def test_generation_performance(self):
        """Test reference generation performance."""
        start_time = time.perf_counter()
        
        # Generate many references
        for i in range(10000):
            prefix = ["R", "C", "L"][i % 3]
            self.manager.generate_next_reference(prefix)
        
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        print(f"Generated 10,000 references in {duration:.3f} seconds")
        print(f"Average time per reference: {duration * 1000000 / 10000:.1f} microseconds")
        
        # Should be much faster than Python implementation
        self.assertLess(duration, 0.1)  # Should be under 100ms
    
    def test_validation_performance(self):
        """Test reference validation performance."""
        # Pre-populate with references
        for i in range(1000):
            prefix = ["R", "C", "L"][i % 3]
            self.manager.generate_next_reference(prefix)
        
        start_time = time.perf_counter()
        
        # Validate many references
        for i in range(1000):
            reference = f"R{i + 1}"
            self.manager.validate_reference(reference)
        
        end_time = time.perf_counter()
        duration = end_time - start_time
        
        print(f"Validated 1,000 references in {duration:.3f} seconds")
        print(f"Average time per validation: {duration * 1000000 / 1000:.1f} microseconds")
        
        # Should be very fast
        self.assertLess(duration, 0.01)  # Should be under 10ms
    
    def test_large_scale_operations(self):
        """Test operations with large numbers of references."""
        # Generate a large number of references
        start_time = time.perf_counter()
        
        for i in range(50000):
            prefix = ["R", "C", "L", "U", "D"][i % 5]
            self.manager.generate_next_reference(prefix)
        
        generation_time = time.perf_counter() - start_time
        
        # Test getting all references
        start_time = time.perf_counter()
        all_refs = self.manager.get_all_used_references()
        retrieval_time = time.perf_counter() - start_time
        
        print(f"Generated 50,000 references in {generation_time:.3f} seconds")
        print(f"Retrieved {len(all_refs)} references in {retrieval_time:.3f} seconds")
        
        self.assertEqual(len(all_refs), 50000)
        self.assertLess(generation_time, 1.0)  # Should be under 1 second
        self.assertLess(retrieval_time, 0.1)   # Should be under 100ms


class TestRustReferenceManagerCompatibility(unittest.TestCase):
    """Test API compatibility with the original Python implementation."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not RUST_REFERENCE_MANAGER_AVAILABLE:
            self.skipTest("Rust reference manager not available")
    
    def test_api_compatibility(self):
        """Test that the API matches the original Python implementation."""
        manager = RustReferenceManager()
        
        # Test method signatures and return types
        
        # generate_next_reference should return str
        ref1 = manager.generate_next_reference("R")
        self.assertIsInstance(ref1, str)
        self.assertEqual(ref1, "R1")
        
        # validate_reference should return bool
        is_valid = manager.validate_reference("R2")
        self.assertIsInstance(is_valid, bool)
        self.assertTrue(is_valid)
        
        # generate_next_unnamed_net_name should return str
        net = manager.generate_next_unnamed_net_name()
        self.assertIsInstance(net, str)
        self.assertEqual(net, "N$1")
        
        # get_all_used_references should return set-like object
        refs = manager.get_all_used_references()
        self.assertTrue(hasattr(refs, '__contains__'))  # Should be set-like
        self.assertIn("R1", refs)
        
        # register_reference should not return anything (or None)
        result = manager.register_reference("C1")
        self.assertIsNone(result)
        
        # clear should not return anything (or None)
        result = manager.clear()
        self.assertIsNone(result)
    
    def test_implementation_info(self):
        """Test implementation information functions."""
        # Test module-level functions
        rust_available = is_rust_available()
        self.assertIsInstance(rust_available, bool)
        
        using_rust = is_using_rust()
        self.assertIsInstance(using_rust, bool)
        
        info = get_implementation_info()
        self.assertIsInstance(info, dict)
        self.assertIn("rust_available", info)
        self.assertIn("using_rust", info)
        self.assertIn("version", info)
        
        # Test instance methods
        manager = RustReferenceManager()
        
        using_rust_impl = manager.is_using_rust_implementation()
        self.assertIsInstance(using_rust_impl, bool)
        
        impl_details = manager.get_implementation_details()
        self.assertIsInstance(impl_details, dict)
        self.assertIn("using_rust", impl_details)
        self.assertIn("manager_id", impl_details)
    
    def test_stats_functionality(self):
        """Test statistics functionality."""
        manager = RustReferenceManager()
        
        # Generate some references to populate stats
        for _ in range(100):
            manager.generate_next_reference("R")
        
        stats = manager.get_stats()
        self.assertIsInstance(stats, dict)
        
        if manager.is_using_rust_implementation():
            # Rust implementation should have detailed stats
            self.assertIn("performance", stats)
            self.assertIn("manager_id", stats)
        else:
            # Python fallback should have basic info
            self.assertIn("implementation", stats)


class TestBenchmarkingFunctions(unittest.TestCase):
    """Test benchmarking and comparison functions."""
    
    def setUp(self):
        """Set up test fixtures."""
        if not RUST_REFERENCE_MANAGER_AVAILABLE:
            self.skipTest("Rust reference manager not available")
        
        if not is_rust_available():
            self.skipTest("Rust implementation not available")
    
    def test_benchmark_performance(self):
        """Test the benchmark_performance function."""
        prefixes = ["R", "C", "L"]
        results = benchmark_performance(prefixes, iterations=100)
        
        self.assertIsInstance(results, dict)
        self.assertIn("total_generation_time_ms", results)
        self.assertIn("total_generated", results)
        self.assertIn("avg_generation_time_ns", results)
        self.assertIn("generations_per_second", results)
        
        # Verify reasonable performance
        avg_time_ns = results["avg_generation_time_ns"]
        self.assertLess(avg_time_ns, 1000000)  # Should be under 1ms per reference
    
    def test_compare_implementations(self):
        """Test the compare_implementations function."""
        prefixes = ["R", "C", "L"]
        results = compare_implementations(prefixes, iterations=50)
        
        self.assertIsInstance(results, dict)
        self.assertIn("prefixes", results)
        self.assertIn("iterations", results)
        self.assertIn("rust_available", results)
        
        if results["rust_available"]:
            self.assertIn("rust", results)
            rust_results = results["rust"]
            self.assertIn("total_generation_time_ms", rust_results)
            self.assertIn("generations_per_second", rust_results)


class TestFallbackBehavior(unittest.TestCase):
    """Test fallback behavior when Rust is not available."""
    
    def test_fallback_info(self):
        """Test that implementation info is available even without Rust."""
        info = get_implementation_info()
        self.assertIsInstance(info, dict)
        self.assertIn("rust_available", info)
        self.assertIn("python_fallback_available", info)
        self.assertIn("using_rust", info)
    
    def test_manager_creation_with_fallback(self):
        """Test that manager can be created even if Rust is not preferred."""
        # This test would need to mock the Rust availability
        # For now, we just verify the manager can be created
        manager = RustReferenceManager()
        self.assertIsNotNone(manager)
        
        # Basic functionality should work regardless of implementation
        ref1 = manager.generate_next_reference("R")
        self.assertEqual(ref1, "R1")


def run_performance_comparison():
    """Run a comprehensive performance comparison."""
    if not RUST_REFERENCE_MANAGER_AVAILABLE or not is_rust_available():
        print("Rust implementation not available for performance comparison")
        return
    
    print("\n" + "="*60)
    print("RUST REFERENCE MANAGER PERFORMANCE COMPARISON")
    print("="*60)
    
    prefixes = ["R", "C", "L", "U", "D"]
    iterations = 1000
    
    print(f"\nTesting with prefixes: {prefixes}")
    print(f"Iterations: {iterations}")
    
    try:
        results = compare_implementations(prefixes, iterations)
        
        print(f"\nRust available: {results['rust_available']}")
        print(f"Python fallback available: {results['python_available']}")
        
        if "rust" in results:
            rust = results["rust"]
            print(f"\nRust Performance:")
            print(f"  Total time: {rust['total_generation_time_ms']:.2f} ms")
            print(f"  Average per reference: {rust['avg_generation_time_ns']:.0f} ns")
            print(f"  References per second: {rust['generations_per_second']:.0f}")
        
        if "python" in results:
            python = results["python"]
            print(f"\nPython Performance:")
            print(f"  Total time: {python['total_generation_time_ms']:.2f} ms")
            print(f"  Average per reference: {python['avg_generation_time_ns']:.0f} ns")
            print(f"  References per second: {python['generations_per_second']:.0f}")
        
        if "performance_improvement" in results:
            improvement = results["performance_improvement"]
            print(f"\nPerformance Improvement:")
            print(f"  Speedup factor: {improvement['speedup_factor']:.1f}x")
            print(f"  Improvement: {improvement['improvement_percentage']:.1f}%")
        
    except Exception as e:
        print(f"Error running performance comparison: {e}")


if __name__ == "__main__":
    # Run the performance comparison first
    run_performance_comparison()
    
    # Then run the unit tests
    print("\n" + "="*60)
    print("RUNNING UNIT TESTS")
    print("="*60)
    
    unittest.main(verbosity=2)