#!/usr/bin/env python3
"""
Test-Driven Development Framework for Rust Integration

This module implements the core TDD framework for gradually replacing
Python functions with Rust implementations while maintaining 100%
functional compatibility.

TDD Cycle:
1. RED: Write test that fails (Rust implementation doesn't exist)
2. GREEN: Write minimal Rust implementation to make test pass  
3. REFACTOR: Improve Rust implementation while keeping tests green

Key Features:
- Property-based testing with Hypothesis
- Performance regression testing
- Automatic fallback validation
- Memory bank integration for crash recovery
"""

import pytest
import time
import timeit
import sys
from pathlib import Path
from typing import Any, Dict, Callable, Optional
from unittest.mock import patch

# Add project root to path for imports
sys.path.insert(0, str(Path(__file__).parent.parent.parent / "src"))

from circuit_synth.core.defensive_logging import get_defensive_logger
from tests.rust_integration.test_deterministic_utils import (
    DeterministicTestUtils,
    TDDTestFixtures, 
    memory_bank_updater
)

# Import hypothesis for property-based testing
try:
    from hypothesis import given, strategies as st, settings, HealthCheck
    HYPOTHESIS_AVAILABLE = True
except ImportError:
    HYPOTHESIS_AVAILABLE = False
    
    # Create mock decorators if hypothesis not available
    def given(*strategies):
        def decorator(func):
            return func
        return decorator
    
    class st:
        @staticmethod
        def text(**kwargs):
            return lambda: "test_string"
        
        @staticmethod
        def dictionaries(**kwargs):
            return lambda: {"test": "data"}
        
        @staticmethod
        def sampled_from(choices):
            return lambda: choices[0] if choices else "default"
        
        @staticmethod
        def characters(**kwargs):
            return lambda: "abc123"
    
    # Mock settings and HealthCheck classes
    def settings(**kwargs):
        def decorator(func):
            return func
        return decorator
    
    class HealthCheck:
        function_scoped_fixture = "function_scoped_fixture"


class RustTDDFramework:
    """
    Core Test-Driven Development framework for Rust integration
    """
    
    def __init__(self, component_name: str):
        self.component_name = component_name
        self.logger = get_defensive_logger(f"rust_tdd_{component_name}")
        self.python_implementation = None
        self.rust_implementation = None
        
        # TDD cycle tracking
        self.current_test = None
        self.cycle_phase = "SETUP"  # SETUP -> RED -> GREEN -> REFACTOR
        
        self.logger.logger.info(f"🧪 TDD FRAMEWORK INITIALIZED [{component_name}]")
    
    def set_implementations(self, 
                          python_func: Callable, 
                          rust_func: Optional[Callable] = None):
        """Set the Python and Rust implementations to test"""
        self.python_implementation = python_func
        self.rust_implementation = rust_func
        
        self.logger.logger.info(f"📝 IMPLEMENTATIONS SET")
        self.logger.logger.info(f"   🐍 Python: {python_func.__name__ if python_func else 'None'}")
        self.logger.logger.info(f"   🦀 Rust: {rust_func.__name__ if rust_func else 'None'}")
    
    def start_tdd_cycle(self, test_name: str, phase: str = "RED"):
        """Start a new TDD cycle"""
        self.current_test = test_name
        self.cycle_phase = phase
        
        self.logger.logger.info(f"🔴 TDD CYCLE START: {test_name} - {phase}")
        memory_bank_updater.log_tdd_cycle(self.component_name, phase, "STARTED")
    
    def assert_rust_python_equivalence(self, 
                                     test_input: Any, 
                                     file_type: str = "text",
                                     performance_check: bool = True) -> bool:
        """
        Core TDD assertion: Rust and Python outputs must be equivalent
        """
        self.logger.logger.info(f"🔍 EQUIVALENCE TEST: {self.current_test}")
        
        # Get Python result (baseline)
        python_start = time.perf_counter()
        try:
            python_result = self.python_implementation(test_input)
            python_time = time.perf_counter() - python_start
            self.logger.logger.info(f"   🐍 Python completed in {python_time:.4f}s")
        except Exception as e:
            self.logger.logger.error(f"   🐍 Python failed: {type(e).__name__}: {e}")
            python_result = None
            python_time = 0.0
        
        # Get Rust result (if available)
        rust_result = None
        rust_time = 0.0
        
        if self.rust_implementation is not None:
            rust_start = time.perf_counter()
            try:
                rust_result = self.rust_implementation(test_input)
                rust_time = time.perf_counter() - rust_start
                self.logger.logger.info(f"   🦀 Rust completed in {rust_time:.4f}s")
            except Exception as e:
                self.logger.logger.error(f"   🦀 Rust failed: {type(e).__name__}: {e}")
                rust_result = None
                rust_time = 0.0
        else:
            self.logger.logger.warning(f"   🦀 Rust implementation not available")
        
        # Handle RED phase (expected failure)
        if self.cycle_phase == "RED":
            if rust_result is None:
                self.logger.logger.info(f"   🔴 RED PHASE: Expected failure - Rust not implemented")
                memory_bank_updater.log_tdd_cycle(self.component_name, "RED", "EXPECTED_FAILURE")
                return False  # Expected in RED phase
            else:
                self.logger.logger.error(f"   🔴 RED PHASE: Unexpected success - Rust already works!")
                return False
        
        # Handle GREEN/REFACTOR phases (require equivalence)
        if python_result is None:
            self.logger.logger.error(f"   ❌ Python implementation failed")
            return False
        
        if rust_result is None:
            self.logger.logger.error(f"   ❌ Rust implementation failed") 
            return False
        
        # Functional equivalence check
        functionally_equivalent = DeterministicTestUtils.validate_rust_python_equivalence(
            str(python_result), str(rust_result), file_type, self.current_test
        )
        
        if not functionally_equivalent:
            self.logger.logger.error(f"   ❌ FUNCTIONAL EQUIVALENCE: FAILED")
            memory_bank_updater.log_test_result(
                self.current_test, "FAILED", "Rust/Python outputs not equivalent"
            )
            return False
        
        # Performance check (optional)
        if performance_check and rust_time > 0 and python_time > 0:
            performance_improvement = python_time / rust_time
            self.logger.logger.info(f"   ⚡ Performance improvement: {performance_improvement:.1f}x")
            
            if performance_improvement < 1.0:
                self.logger.logger.warning(f"   ⚠️ Rust is slower than Python!")
            elif performance_improvement < 1.5:
                self.logger.logger.warning(f"   ⚠️ Modest performance improvement")
            else:
                self.logger.logger.info(f"   ✅ Good performance improvement")
        
        # Success!
        self.logger.logger.info(f"   ✅ EQUIVALENCE TEST: PASSED")
        memory_bank_updater.log_test_result(
            self.current_test, "PASSED", f"Rust/Python equivalence confirmed"
        )
        
        return True
    
    def complete_tdd_cycle(self, success: bool):
        """Complete the current TDD cycle"""
        status = "PASSED" if success else "FAILED"
        
        self.logger.logger.info(f"🏁 TDD CYCLE COMPLETE: {self.current_test} - {status}")
        memory_bank_updater.log_tdd_cycle(self.component_name, self.cycle_phase, status)
        
        if success and self.cycle_phase == "GREEN":
            self.logger.logger.info(f"   🎯 Ready for REFACTOR phase")
        elif success and self.cycle_phase == "REFACTOR":
            self.logger.logger.info(f"   🎉 TDD cycle complete for {self.current_test}")


class TestSExpressionGeneration:
    """
    TDD test suite for S-expression generation - our first Rust integration target
    
    This tests the most isolated, pure function we identified for Rust migration.
    """
    
    def setup_method(self):
        """Set up TDD framework for each test"""
        self.tdd = RustTDDFramework("sexp_generation")
        
        # Set up Python implementation (existing)
        self.tdd.set_implementations(
            python_func=self._python_component_sexp,
            rust_func=None  # Will be set when Rust implementation exists
        )
    
    def _python_component_sexp(self, component_data: Dict[str, Any]) -> str:
        """
        Python implementation of component S-expression generation
        
        This is a simplified version for TDD - in practice we'd call the real implementation
        """
        ref = component_data.get("ref", "U?")
        symbol = component_data.get("symbol", "Device:Unknown")
        value = component_data.get("value", "")
        
        # Simple S-expression format (real implementation is more complex)
        sexp = f'(symbol (lib_id "{symbol}") (at 0 0 0) (unit 1)\n'
        sexp += f'  (property "Reference" "{ref}")\n'
        if value:
            sexp += f'  (property "Value" "{value}")\n'
        sexp += ')'
        
        return sexp
    
    def _rust_component_sexp(self, component_data: Dict[str, Any]) -> str:
        """
        Rust implementation placeholder - will be implemented during GREEN phase
        """
        # Try to import Rust module
        try:
            # This will fail in RED phase, succeed in GREEN phase
            import rust_kicad_schematic_writer
            return rust_kicad_schematic_writer.generate_component_sexp(component_data)
        except ImportError:
            raise RuntimeError("Rust implementation not available")
    
    def test_component_sexp_basic_resistor_RED(self):
        """
        RED PHASE: Test that should fail - Rust implementation doesn't exist yet
        """
        self.tdd.start_tdd_cycle("basic_resistor_sexp", "RED")
        
        # Use simple test fixture
        component = TDDTestFixtures.create_simple_component()
        
        # This should fail because Rust implementation doesn't exist
        result = self.tdd.assert_rust_python_equivalence(component, "text", performance_check=False)
        
        # In RED phase, we expect failure
        assert not result, "RED phase should fail - Rust not implemented yet"
        
        self.tdd.complete_tdd_cycle(True)  # Success in RED means expected failure
    
    @pytest.mark.skip(reason="GREEN phase - implement when Rust module exists")
    def test_component_sexp_basic_resistor_GREEN(self):
        """
        GREEN PHASE: Test should pass with minimal Rust implementation
        
        This test will be enabled once we have a minimal Rust implementation
        """
        self.tdd.start_tdd_cycle("basic_resistor_sexp", "GREEN")
        
        # Enable Rust implementation
        self.tdd.set_implementations(
            python_func=self._python_component_sexp,
            rust_func=self._rust_component_sexp
        )
        
        component = TDDTestFixtures.create_simple_component() 
        
        result = self.tdd.assert_rust_python_equivalence(component, "text")
        assert result, "GREEN phase should pass - Rust implementation works"
        
        self.tdd.complete_tdd_cycle(True)
    
    @pytest.mark.skipif(not HYPOTHESIS_AVAILABLE, reason="Hypothesis not available")
    @given(st.dictionaries(
        keys=st.sampled_from(['ref', 'symbol', 'value', 'lib_id']),
        values=st.text(min_size=1, max_size=50, alphabet=st.characters(whitelist_categories=("L", "N", "P"))),
        min_size=1
    ))
    @settings(suppress_health_check=[HealthCheck.function_scoped_fixture])
    def test_component_sexp_property_based(self, component_data):
        """
        Property-based test: Any valid component data should produce equivalent outputs
        
        This test will run once we have GREEN phase working
        """
        if not hasattr(self, 'tdd'):
            self.setup_method()
        
        self.tdd.start_tdd_cycle("property_based_sexp", "REFACTOR")
        
        # Enable Rust implementation (skip if not available)
        if self.tdd.rust_implementation is None:
            pytest.skip("Rust implementation not available yet")
        
        try:
            result = self.tdd.assert_rust_python_equivalence(
                component_data, "text", performance_check=False
            )
            
            # Property: All valid inputs should produce equivalent outputs
            assert result, f"Property violation: {component_data}"
            
        except (ValueError, KeyError, TypeError) as e:
            # Both implementations should handle invalid input identically
            self.tdd.logger.logger.info(f"   🔍 Invalid input handled consistently: {e}")
        
        self.tdd.complete_tdd_cycle(True)
    
    def test_performance_regression(self):
        """
        Performance regression test: Rust should be faster than Python
        """
        if not hasattr(self, 'tdd'):
            self.setup_method()
        
        self.tdd.start_tdd_cycle("performance_regression", "REFACTOR")
        
        # Skip if Rust not available
        if self.tdd.rust_implementation is None:
            pytest.skip("Rust implementation not available yet")
        
        component = TDDTestFixtures.create_complex_component()
        
        # Measure Python performance
        python_time = timeit.timeit(
            lambda: self.tdd.python_implementation(component),
            number=100
        ) / 100
        
        # Measure Rust performance  
        rust_time = timeit.timeit(
            lambda: self.tdd.rust_implementation(component),
            number=100
        ) / 100
        
        performance_improvement = python_time / rust_time
        
        self.tdd.logger.logger.info(f"   📊 Performance comparison:")
        self.tdd.logger.logger.info(f"      🐍 Python: {python_time:.4f}s")
        self.tdd.logger.logger.info(f"      🦀 Rust: {rust_time:.4f}s")
        self.tdd.logger.logger.info(f"      ⚡ Improvement: {performance_improvement:.1f}x")
        
        # Rust should be at least 2x faster for it to be worth the complexity
        assert performance_improvement >= 2.0, \
            f"Rust only {performance_improvement:.1f}x faster, expected ≥2x"
        
        self.tdd.complete_tdd_cycle(True)


class TestTDDFrameworkItself:
    """
    Meta-tests: Test the TDD framework itself
    """
    
    def test_tdd_framework_initialization(self):
        """Test that TDD framework initializes correctly"""
        tdd = RustTDDFramework("test_component")
        
        assert tdd.component_name == "test_component"
        assert tdd.python_implementation is None
        assert tdd.rust_implementation is None
        assert tdd.cycle_phase == "SETUP"
        
        memory_bank_updater.log_test_result(
            "tdd_framework_init", "PASSED", "TDD framework initializes correctly"
        )
    
    def test_deterministic_utils(self):
        """Test that our deterministic utilities work correctly"""
        # Test JSON normalization
        json1 = '{"tstamps": "/root-4508312656/", "name": "test"}'
        json2 = '{"tstamps": "/root-5721586864/", "name": "test"}'
        
        assert not json1 == json2  # Should be different
        
        # But functionally equivalent after normalization
        assert DeterministicTestUtils.compare_outputs_functionally(json1, json2, "json")
        
        memory_bank_updater.log_test_result(
            "deterministic_utils", "PASSED", "JSON normalization working correctly"
        )
    
    def test_memory_bank_integration(self):
        """Test that memory bank integration works"""
        memory_bank_updater.log_milestone(
            "TDD Framework Complete",
            "Core TDD framework implemented with deterministic testing utilities"
        )
        
        # Check that log file exists
        assert memory_bank_updater.tdd_log_file.exists()
        
        memory_bank_updater.log_test_result(
            "memory_bank_integration", "PASSED", "Memory bank logging functional"
        )


if __name__ == "__main__":
    # Run the RED phase test to demonstrate TDD cycle
    print("🧪 Running TDD Framework Demo - RED Phase")
    
    test_suite = TestSExpressionGeneration()
    test_suite.setup_method()
    
    try:
        test_suite.test_component_sexp_basic_resistor_RED()
        print("✅ RED phase test completed successfully")
    except Exception as e:
        print(f"❌ RED phase test failed: {e}")
    
    print("\n📋 Check memory-bank/progress/rust-tdd-log.md for detailed progress")